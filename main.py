import asyncio
import urllib
import os
from concurrent.futures import ProcessPoolExecutor
from time import sleep
from typing import List

import requests
from pdfminer.high_level import extract_text

import s3
from nagivation import get_urls_for_date_range
from log_utils import setup_logging
from settings import (
    NAME_LOOKUPS,
    INITIAL_DATE,
    DAYS_AHEAD,
)


logger = setup_logging(__name__)


async def perform_request(url):
    logger.info(url)
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, requests.get, url)


def filename_from_url(url):
    return urllib.parse.quote(url['url'].split("/")[-1], '')


def download(initial_date: str, days_ahead: int = 1):
    urls = get_urls_for_date_range(initial_date, days_ahead)
    logger.info(f'Found {len(urls)} lists. Checking existence and downloading...')

    filenames = [filename_from_url(url) for url in urls]

    to_download = [url for url in urls if not os.path.isfile(filename_from_url(url))]
    asyncio.run(_download(to_download))
    logger.info(f'{len(to_download)} files downloaded.')

    filenames_to_upload = [name for name in filenames if not s3.file_exists(name)]

    logger.info(f'Uploading {len(filenames_to_upload)} new files to S3 bucket...')
    for name in filenames_to_upload:
        s3.upload(name)

    return filenames


async def _download(urls):
    filenames: List[str] = []
    future_responses = await asyncio.gather(
        *[perform_request(url['url']) for url in urls]
    )

    for resp in asyncio.as_completed(future_responses):
        response = await resp
        filename = urllib.parse.quote(response.url.split("/")[-1], '')
        logger.info(f'Downloading: {filename}')
        with open(filename, 'wb') as file:
            file.write(response.content)
            filenames.append(file.name)

    return filenames


def write_and_upload_results(results_filename, results: str) -> None:
    logger.info(f"Results file '{results_filename}'.")

    with open(results_filename, "w+") as results_file:
        results_file.write(results)

    logger.info("Wrote results file.")
    s3.upload(results_filename)


def match_text(results):
    logger.info("Searching for name in results...")
    return [name for name in NAME_LOOKUPS if name.lower() in results]


def _read(filename):
    base_filename = filename.split(".")[0]
    results_filename = base_filename + "_results.txt"
    is_result_in_s3 = s3.file_exists(results_filename)

    if is_result_in_s3:
        logger.info(f"Result already in S3: '{results_filename}'...")
        results = str(s3.pull(results_filename))
    else:
        logger.info(f"Starting text extraction on '{filename}'...")
        raw_results = extract_text(filename)
        results = raw_results.lower()
        logger.info("Uploading results file...")
        write_and_upload_results(results_filename, results)

    found = match_text(results)
    logger.info(
        f'{filename.split("/")[-1]}: '
        f'{found if found else "No results in this file."}'
    )


def read(filenames):
    with ProcessPoolExecutor() as pool:
        pool.map(_read, filenames)


if __name__ == '__main__':
    logger.info("Downloading...")
    filenames = download(INITIAL_DATE, DAYS_AHEAD)

    logger.info("Reading...")
    read(filenames=filenames)

    logger.info("Finished.")

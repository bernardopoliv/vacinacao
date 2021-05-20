import asyncio
import urllib
from concurrent.futures import ProcessPoolExecutor
from typing import List

import boto3
import requests
from pdfminer.high_level import extract_text

import s3
from log_utils import setup_logging
from navigation import get_urls_for_files
from settings import (
    NAME_LOOKUPS,
    S3_FILES_BUCKET,
    VAC_PUBLIC_LIST_URL
)

logger = setup_logging(__name__)


async def perform_request(url):
    logger.info(url)
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, requests.get, url)


def filename_from_url(url):
    return urllib.parse.quote(url['url'].split("/")[-1], '')


def download(initial_url: str, existing_files: list = None):
    urls = get_urls_for_files(initial_url)
    logger.info(f'Found {len(urls)} lists. Checking existence and downloading...')

    to_download = [url for url in urls if filename_from_url(url) not in existing_files]
    logger.info(f'Found {len(to_download)} new lists. Downloading...')
    filenames_to_upload = asyncio.run(_download(to_download, existing_files))
    logger.info(f'Uploading {len(filenames_to_upload)} new files to S3 bucket...')
    for name in filenames_to_upload:
        s3.upload(name)

    return filenames_to_upload


async def _download(urls, existing_files):
    filenames = []
    future_responses = await asyncio.gather(
        *[perform_request(url['url']) for url in urls]
    )

    for resp in asyncio.as_completed(future_responses):
        response = await resp
        filename = urllib.parse.quote(response.url.split("/")[-1], '')
        if filename not in existing_files:
            logger.info(f'Downloading: {filename}')
            filenames.append((filename, response.content))

    return filenames


def upload_result(results_filename: str, results: str) -> None:
    logger.info(f"Results file '{results_filename}'.")

    with open(results_filename, "w+") as results_file:
        results_file.write(results)

    logger.info("Uploaded results file.")
    s3.upload(results_filename)


def match_text(results):
    return [name for name in NAME_LOOKUPS if name.lower() in results]


async def _read(s3_keys):
    future_results = await asyncio.gather(
        *[s3.async_pull(key) for key in s3_keys]
    )

    results = []
    for r in asyncio.as_completed(future_results):
        result = await r
        results.append(
            (result['Body'].read())
        )
    return results


def find_text(filenames):
    with ProcessPoolExecutor() as pool:
        pool.map(_read, filenames)


def read(existing_files):
    existing_results = [f for f in existing_files if f.endswith('_results.txt')]

    results = asyncio.run(_read(existing_results))

    for result in results:
        found = match_text(str(result))
        logger.info(
            # TODO: Add the file name to this log.
            # TODO: We need to identify which thread went with which file.
            f'{found if found else "No results in this file."}'
        )


def extract_result(filename):
    logger.info(f"Starting text extraction on '{filename}'...")
    boto3.client('s3').download_file(S3_FILES_BUCKET, filename, filename)
    with open(filename, 'rb') as f:
        raw_result = extract_text(f)
    return raw_result.lower()


def generate_results(existing_files: List[str]):
    missing_results = [
        f for f
        in existing_files
        if f.replace('.pdf', '_results.txt') not in existing_files
    ]
    logger.info(f'Processing {len(missing_results)} new pdfs. Generating results...')

    for filename in missing_results:
        try:
            # Result is the PDF content represented as string
            result: str = extract_result(filename)
        except Exception as e:
            logger.exception(e)
        else:
            logger.info("Uploading results file...")
            upload_result(filename.replace('.pdf', "_results.txt"), result)
            existing_files.append(filename)


if __name__ == '__main__':
    logger.info('Starting...')
    # Get list of file names that are in the bucket (S3) already
    existing_files = s3.get_existing_files(S3_FILES_BUCKET)
    download(VAC_PUBLIC_LIST_URL, existing_files)

    logger.info("Generating results...")
    generate_results(existing_files)

    logger.info("Reading...")
    read(existing_files)

    logger.info("Finished.")

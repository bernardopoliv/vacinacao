import asyncio
import urllib
from typing import List

import boto3
import requests
from pdfminer.high_level import extract_text

from vacinacao import s3, settings, indexer
from vacinacao.log_utils import setup_logging
from vacinacao.navigation import get_file_urls


logger = setup_logging(__name__)


async def perform_request(url):
    logger.info(url)
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, requests.get, url)


def filename_from_url(url):
    return urllib.parse.quote(url['url'].split("/")[-1], '')


def download(existing_files: list = None):
    urls = get_file_urls()
    logger.info(f'Found {len(urls)} lists. Checking existence and downloading...')

    to_download = [
        url for url
        in urls if filename_from_url(url).lower()
        not in [f.lower() for f in existing_files]
    ]
    logger.info(f'Found {len(to_download)} new lists. Downloading...')

    new_files: List[dict] = asyncio.run(_download(to_download, existing_files))
    logger.info(f'Uploading {len(new_files)} new files to S3 bucket...')

    for file in new_files:
        s3.upload(filename=file['filename'], file_in_memory=file['file_content'])

    return new_files


async def _download(urls: List[str], existing_files: List[str]) -> dict:
    new_files = []
    future_responses = await asyncio.gather(
        *[perform_request(url['url']) for url in urls]
    )

    for resp in asyncio.as_completed(future_responses):
        response = await resp
        # URL passed with the async call for this thread
        filename = response.__dict__['url'].split("/")[-1].lower()
        if filename not in existing_files:
            logger.info(f'Downloading: {filename}')
            new_files.append({
                'url': response.url,
                'filename': filename,
                'content': response.content
            })

    return new_files


def upload_result(results_filename: str, results: str) -> None:
    logger.info(f"Results file '{results_filename}'.")

    with open("/tmp/" + results_filename, "w+") as results_file:
        results_file.write(results)

    logger.info("Uploaded results file.")
    s3.upload(results_filename)


def match_text(result_text, searched_name=None):
    names = [searched_name] if searched_name else settings.NAME_LOOKUPS
    names_found = [name for name in names if name.lower() in result_text]
    # Make user friendly to show in the result page
    return names_found[0] if len(names_found) == 1 else names_found


def read(searched_name):
    logger.info("Started `read` method.")

    in_memory_files = indexer.pull_index()
    logger.info("Got index into memory.")

    found_list = []
    for result, content in in_memory_files.items():
        found = match_text(str(content), searched_name)
        if found:
            found_list.append({"names": found, "file_key": result})
        logger.info(
            f'{result}: {found if found else "No results in this file."}'
        )

    return found_list


def extract_result(filename):
    logger.info(f"Starting text extraction on '{filename}'...")
    boto3.client('s3').download_file(settings.S3_FILES_BUCKET, filename, "/tmp/" + filename)
    with open("/tmp/" + filename, 'rb') as f:
        raw_result = extract_text(f)
    return raw_result.lower()


def generate_results(existing_files: List[str]):
    missing_results = [
        f for f
        in existing_files
        if f.replace('.pdf', '_results.txt') not in existing_files
    ]
    logger.info(f'Processing {len(missing_results)} new pdfs. Generating results...')

    new_results = []
    for filename in missing_results:
        try:
            # Result is the PDF content represented as string
            result: str = extract_result(filename)
        except Exception as e:
            logger.exception("Could not extract result.")
        else:
            logger.info("Uploading results file...")
            upload_result(filename.replace('.pdf', "_results.txt"), result)
            new_results.append(filename)

    return new_results

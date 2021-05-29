import json
import gzip
import asyncio
import urllib
from datetime import date
from typing import List

import boto3
import requests
from pdfminer.high_level import extract_text

from vacinacao import settings
from vacinacao.log_utils import setup_logging
from vacinacao.service_layer import s3, navigation


logger = setup_logging(__name__)


class IndexUnavailable(Exception):
    pass


async def perform_request(url):
    logger.info(url)
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, requests.get, url)


def filename_from_url(url):
    return urllib.parse.quote(url['url'].split("/")[-1], '')


def download_from_prefeitura(existing_files: list = None) -> List[dict]:
    urls = navigation.get_file_urls()
    logger.info(f'Found {len(urls)} lists. Checking existence and downloading...')

    to_download = [
        url for url
        in urls if filename_from_url(url).lower()
        not in [f.lower() for f in existing_files]
    ]
    logger.info(f'Found {len(to_download)} new lists. Downloading...')

    new_files: List[dict] = asyncio.run(_download(to_download))
    logger.info(f'Uploading {len(new_files)} new files to S3 bucket...')

    for file in new_files:
        s3.upload(filename=file['filename'], file_in_memory=file['content'])

    return new_files


async def _download(urls: List[str]) -> List[dict]:
    new_files = []
    future_responses = await asyncio.gather(
        *[perform_request(url['url']) for url in urls]
    )

    for resp in asyncio.as_completed(future_responses):
        response = await resp
        # URL passed with the async call for this thread
        filename = response.__dict__['url'].split("/")[-1].lower()
        logger.info(f'Downloading: {filename}')
        new_files.append({
            'url': response.url,
            'filename': filename,
            'content': response.content
        })

    return new_files


def compile_index(new_pdfs) -> None:
    """
    Checks for result files in S3 and compare against the index.
    Adds those to the index and update in S3.
    """
    existing_results = s3.fetch_file_names("_results.txt")
    logger.info("Got results s3 keys.")

    try:
        current_index = pull_index()
    except IndexUnavailable:
        current_index = {}

    missing_in_index = set(existing_results).difference(current_index)

    new_index = s3.pull_files(missing_in_index)
    logger.info("Pulled results files into memory.")
    new_index.update(current_index)

    for pdf_meta in new_pdfs:
        for result_name, result_content in new_index.items():
            if result_name.replace('_results.txt', '.pdf').lower() == pdf_meta['filename'].lower():
                new_index[result_name] = {
                    'url': pdf_meta['url'],
                    'content': result_content,
                }

    index_json = json.dumps(new_index)
    logger.info("Dumped index into JSON string.")

    index_filename = _get_todays_index()
    s3.upload(index_filename, gzip.compress(bytes(index_json, encoding="utf8")))

    logger.info(f"Successfully wrote index file '{index_filename}'.")


def pull_index() -> dict:
    index_filename = _get_todays_index()
    logger.info(f"Looking for index '{index_filename}'.")
    if s3.file_exists(index_filename):
        index_json = gzip.decompress(s3.pull(index_filename)).decode()
        index = json.loads(index_json)
        logger.info(f"Index contains '{len(index)}' files.")
        return index
    else:
        raise IndexUnavailable()


def _get_todays_index():
    return f"temp_index_{date.today().isoformat()}.json.gzip"


def extract_result(filename):
    logger.info(f"Starting text extraction on '{filename}'...")
    boto3.client('s3').download_file(settings.S3_FILES_BUCKET, filename, "/tmp/" + filename)
    with open("/tmp/" + filename, 'rb') as f:
        raw_result = extract_text(f)
    return raw_result.lower()


def _upload_result(results_filename: str, results: str) -> None:
    logger.info(f"Results file '{results_filename}'.")

    with open("/tmp/" + results_filename, "w+") as results_file:
        results_file.write(results)

    logger.info("Uploaded results file.")
    s3.upload(results_filename)


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
            _upload_result(filename.replace('.pdf', "_results.txt"), result)
            new_results.append(filename)

    return new_results


def download_and_reindex():
    logger.info('Starting reindex...')
    existing_files = s3.get_existing_files(settings.S3_FILES_BUCKET)
    new_pdfs: List[dict] = download_from_prefeitura(existing_files)

    logger.info("Generating results...")
    new_results: List[str] = generate_results(existing_files)
    existing_files.extend(new_results)

    logger.info("Compiling index...")
    compile_index(new_pdfs)

    logger.info("Finished reindex.")


if __name__ == "__main__":
    download_and_reindex()

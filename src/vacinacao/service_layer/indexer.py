import hashlib
import io
import json
import gzip
import asyncio
import urllib
from datetime import date, timedelta
from typing import List

import requests
from pdfminer.high_level import extract_text

from vacinacao.log_utils import setup_logging
from vacinacao.service_layer import s3, navigation
from vacinacao.service_layer.utils import hash_content

logger = setup_logging(__name__)


class IndexUnavailable(Exception):
    pass


async def perform_request(url):
    logger.info(url)
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, requests.get, url)


def filename_from_url(url):
    return urllib.parse.quote(url['url'].split("/")[-1], '')


def is_url_in_index(url, index):
    if not index:
        return []
    indexed_urls = [entry.get("url", '').lower() for entry in index.values()]
    return url['url'].lower() in indexed_urls


def download_from_prefeitura(to_download: List[str]) -> dict:
    new_files: dict = asyncio.run(_download(to_download))

    logger.info(f'Adding {len(new_files)} new files to the index...')
    for file_meta in new_files.values():
        s3.upload(
            filename=file_meta['pdf_file_key'],
            file_in_memory=file_meta['content']
        )
    return new_files


async def _download(urls: List[str]) -> dict:
    new_files = {}
    future_responses = await asyncio.gather(
        *[perform_request(url['url']) for url in urls]
    )

    for resp in asyncio.as_completed(future_responses):
        response = await resp
        # URL passed with the async call for this thread
        content_hash = hash_content(response.content)
        filename = f'{content_hash}.pdf'
        logger.info(f'Downloading: {content_hash}.pdf')
        new_files[content_hash] = {
            'url': response.request.url,
            'content': response.content,
            'pdf_file_key': filename
        }
    return new_files


def compile_index(new_entries: dict, current_index: dict) -> None:
    """
    Checks for result files in S3 and compare against the index.
    Adds those to the index and update in S3.
    """

    new_entries = {
        k: v for k, v
        in new_entries.items()
        if k not in current_index
    }

    new_index = {**new_entries, **current_index}
    index_json = json.dumps(new_index)
    logger.info("Dumped index into JSON string.")

    index_filename = get_index_filename_for_date(date.today())
    s3.upload(index_filename, gzip.compress(bytes(index_json, encoding="utf8")))

    logger.info(f"Successfully wrote index file '{index_filename}'.")


def pull_index(index_date=None) -> dict:
    if index_date is None:
        index_date = date.today()
    index_filename = get_index_filename_for_date(index_date)

    logger.info(f"Looking for index '{index_filename}'.")
    if s3.file_exists(index_filename):
        index_json = gzip.decompress(s3.pull(index_filename)).decode()
        index = json.loads(index_json)
        logger.info(f"Index contains '{len(index)}' files.")
        return index
    else:
        raise IndexUnavailable()


def get_index_filename_for_date(index_date: date):
    return f"temp_index_{index_date.isoformat()}.json.gzip"


def extract_result(file_entry: dict) -> str:
    logger.info(f"Starting text extraction on '{file_entry['pdf_file_key']}'...")
    text_result = extract_text(io.BytesIO(file_entry['content']))
    return text_result.lower()


def _upload_result(results_filename: str, results: str) -> None:
    logger.info(f"Uploading results file {results_filename}...")

    with open("/tmp/" + results_filename, "w+") as results_file:
        results_file.write(results)

    logger.info("Uploaded results file.")
    s3.upload(results_filename)


def generate_results(new_entries: dict):
    logger.info(f'Processing {len(new_entries)} new pdfs. Generating results...')
    for content_hash, file_meta in new_entries.items():
        result: str = extract_result(file_meta)
        results_file_key = f'{content_hash}_results.txt'
        new_entries[content_hash].update({
            'content': result,
            'results_file_key': results_file_key,
        })
        _upload_result(results_file_key, result)


def get_current_index() -> dict:
    try:
        current_index = pull_index()
    except IndexUnavailable:
        logger.info("Unable to get today's index")
        yesterday = date.today() - timedelta(days=1)
        current_index = pull_index(yesterday)

    return current_index


def get_existing_pdfs(current_index):
    return [f.get('pdf_file_key') for f in current_index]


def download_and_reindex():
    logger.info('Starting reindex...')
    current_index: dict = get_current_index()
    urls = navigation.get_file_urls()

    to_download = [
        url
        for url in urls
        if not is_url_in_index(url, current_index)
    ]

    logger.info(f'Found {len(to_download)} new lists. Downloading...')
    new_entries = download_from_prefeitura(to_download)

    logger.info("Generating results...")
    generate_results(new_entries)

    logger.info("Compiling and uploading new index...")
    compile_index(new_entries, current_index)
    logger.info("Finished reindex.")


if __name__ == "__main__":
    download_and_reindex()

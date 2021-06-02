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
    return urllib.parse.quote(url["url"].split("/")[-1], "")


def is_url_in_index(url, index):
    if not index:
        return []
    indexed_urls = [entry.get("url", "").lower() for entry in index.values()]
    return url["url"].lower() in indexed_urls


def download_from_prefeitura(to_download: List[str]):
    index = get_current_index()
    new_entries: dict = asyncio.run(_download(to_download))

    for content_hash, file_meta in new_entries.items():
        s3.upload(
            filename=file_meta["pdf_file_key"], file_in_memory=file_meta["content"]
        )
        index[content_hash] = {
            "url": file_meta["url"],
            "pdf_file_key": file_meta["pdf_file_key"],
        }

    if new_entries:
        logger.info(f"Adding {len(new_entries)} new files to the index...")
        dump_and_upload_index(index)


async def _download(urls: List[str]) -> dict:
    new_files = {}
    future_responses = await asyncio.gather(
        *[perform_request(url["url"]) for url in urls]
    )

    for resp in asyncio.as_completed(future_responses):
        response = await resp
        # URL passed with the async call for this thread
        content_hash = hash_content(response.content)
        filename = f"{content_hash}.pdf"
        logger.info(f"Downloading: {content_hash}.pdf")
        new_files[content_hash] = {
            "url": response.request.url,
            "content": response.content,
            "pdf_file_key": filename,
        }
    return new_files


def dump_and_upload_index(new_index: dict) -> None:
    """
    Checks for result files in S3 and compare against the index.
    Adds those to the index and update in S3.
    """
    logger.info("Compiling and uploading new index...")
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


def extract_result(pdf_file_key: dict, pdf_content: bytes) -> str:
    logger.info(f"Starting text extraction on '{pdf_file_key}'...")
    text_result = extract_text(io.BytesIO(pdf_content))
    return text_result.lower()


def upload_result(results_filename: str, results: str) -> None:
    logger.info(f"Uploading results file {results_filename}...")

    with open("/tmp/" + results_filename, "w+") as results_file:
        results_file.write(results)

    logger.info("Uploaded results file.")
    s3.upload(results_filename)


def generate_and_upload_results():
    index = get_current_index()
    for content_hash, file_meta in index.items():
        if file_meta.get("content") and file_meta.get("results_file_key"):
            continue
        pdf_filename = file_meta["pdf_file_key"]
        logger.info(f"Generating results for {pdf_filename}")
        pdf_content = s3.pull(pdf_filename)
        result: str = extract_result(pdf_filename, pdf_content)
        results_file_key = f"{content_hash}_results.txt"
        upload_result(results_file_key, result)
        index[content_hash].update(
            {
                "content": result,
                "results_file_key": results_file_key,
            }
        )
    dump_and_upload_index(index)


def get_current_index() -> dict:
    try:
        current_index = pull_index()
    except IndexUnavailable:
        logger.info("Unable to get today's index")
        yesterday = date.today() - timedelta(days=1)
        current_index = pull_index(yesterday)

    return current_index


def download_and_reindex():
    logger.info("Starting reindex...")
    current_index: dict = get_current_index()
    urls = navigation.get_file_urls()

    to_download = [url for url in urls if not is_url_in_index(url, current_index)]

    logger.info(f"Found {len(to_download)} new lists. Downloading...")
    download_from_prefeitura(to_download)

    logger.info("Generating results...")
    generate_and_upload_results()

    logger.info("Finished reindex.")


if __name__ == "__main__":
    download_and_reindex()

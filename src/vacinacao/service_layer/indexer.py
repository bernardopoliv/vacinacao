import os
import io
import json
import gzip
import asyncio
import urllib
from datetime import date, timedelta
from typing import List

import requests
from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError

from vacinacao.log_utils import setup_logging
from vacinacao.service_layer import s3, navigation
from vacinacao.service_layer.utils import hash_content, SingletonMeta


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
    index = get_most_recent_index()
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


class AbstractIndex:
    # TODO: make this inherit from abc.ABC? Need to resolve metaclass conflict on InMemoryIndex.

    index: dict

    def __init__(self, for_date: date):
        self.for_date = for_date

    def is_available(self):
        return self._is_available()

    def pull(self):
        return self._pull()

    def push(self, index):
        return self._push(index)

    def _is_available(self):
        raise NotImplementedError

    def _pull(self):
        raise NotImplementedError

    def _push(self):
        raise NotImplementedError


class InMemoryIndex(AbstractIndex, metaclass=SingletonMeta):
    _indexes: dict = {}  # can hold multiple index, by date as key

    def _is_available(self):
        return bool(self.for_date in self._indexes)

    def _pull(self):
        return self._indexes[self.for_date]

    def _push(self, index):
        self._indexes[self.for_date] = index


class LocalFileIndex(AbstractIndex):
    def _pull(self):
        if not self.is_available():
            raise IndexUnavailable
        index = open(self.__get_filename()).read()
        return json.loads(index)

    def __get_filename(self):
        return "/tmp/" + get_index_filename_for_date(self.for_date)

    def _is_available(self):
        return os.path.isfile(self.__get_filename())

    def _push(self, index):
        with open(self.__get_filename(), "w") as file:
            file.write(json.dumps(index))


class S3FileIndex(AbstractIndex):
    def _is_available(self):
        return s3.file_exists(get_index_filename_for_date(self.for_date))

    def _pull(self):
        gzip_content = s3.pull(get_index_filename_for_date(self.for_date))
        index_json = gzip.decompress(gzip_content).decode()
        return json.loads(index_json)


def pull_index(index_date=None) -> dict:
    """
    Orchestrates the search among the different index strategies (in-memory, local file, S3).
    Fill up the missed indexes to improve performance of the next searches.
    """
    if index_date is None:
        index_date = date.today()

    # This should be in order of performance (best comes first)
    index_types = [
        InMemoryIndex,
        LocalFileIndex,
        S3FileIndex,
    ]

    logger.info(f"Looking for index for date '{index_date}'.")
    index = None
    missed_indexes = []
    for index_type in index_types:
        logger.info(f"Looking in index type '{index_type}'")
        this_index = index_type(index_date)

        if not this_index.is_available():
            missed_indexes.append(this_index)
            continue

        logger.info(f"Found index in type '{index_type}'")
        index = this_index.pull()
        logger.info(f"Index contains '{len(index)}' files.")
        break

    if index is None:
        raise IndexUnavailable

    for missed_index in missed_indexes:
        logger.info(f"Pushing towards index '{missed_index}'.")
        missed_index.push(index)

    return index


def get_index_filename_for_date(index_date: date):
    return f"temp_index_{index_date.isoformat()}.json.gzip"


def upload_result(results_filename: str, results: str) -> None:
    logger.info(f"Uploading results file {results_filename}...")

    with open("/tmp/" + results_filename, "w+") as results_file:
        results_file.write(results)

    logger.info("Uploaded results file.")
    s3.upload(results_filename)


def extract_result(file_meta, pdf_content) -> str:
    pdf_filename = file_meta["pdf_file_key"]
    logger.info(f"Starting text extraction on '{pdf_filename}'...")

    try:
        return extract_text(io.BytesIO(pdf_content)).lower()
    except PDFSyntaxError:
        logger.warning(
            "PDF content is not valid. This file will be ignored.",
            extra={"url": file_meta["url"], "s3_key": pdf_filename},
        )
        return ""


def generate_and_upload_results():
    index = get_most_recent_index()
    for content_hash, file_meta in index.items():
        if file_meta.get("content") and file_meta.get("results_file_key"):
            continue
        pdf_filename = file_meta["pdf_file_key"]
        logger.info(f"Generating results for {pdf_filename}")

        pdf_content = s3.pull(pdf_filename)
        result = extract_result(file_meta, pdf_content)

        results_file_key = f"{content_hash}_results.txt"
        upload_result(results_file_key, result)
        index[content_hash].update(
            {"content": result, "results_file_key": results_file_key}
        )
    dump_and_upload_index(index)


def get_most_recent_index() -> dict:
    index = None
    index_date = date.today()
    while index is None:
        try:
            index = pull_index(index_date)
        except IndexUnavailable:
            logger.info(f"Unable to get index for date '{index_date}'.")
            index_date -= timedelta(days=1)
    return index


def download_and_reindex():
    logger.info("Starting reindex...")
    current_index: dict = get_most_recent_index()
    urls = navigation.get_file_urls()

    to_download = [url for url in urls if not is_url_in_index(url, current_index)]

    logger.info(f"Found {len(to_download)} new lists. Downloading...")
    download_from_prefeitura(to_download)

    logger.info("Generating results...")
    generate_and_upload_results()

    logger.info("Finished reindex.")


if __name__ == "__main__":
    download_and_reindex()

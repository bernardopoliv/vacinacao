import json
import gzip
import sys
from datetime import date
from typing import List

from vacinacao import s3, settings
from vacinacao.log_utils import setup_logging


logger = setup_logging(__name__)


class IndexUnavailable(Exception):
    pass


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

    for pdf_name, pdf_meta in new_pdfs.items():
        for result_name, result_content in new_index.items():
            if result_name == pdf_meta['filename'].replace('_result.txt', '.pdf'):
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
    return f"index_{date.today().isoformat()}.json.gzip"


def download_and_reindex():
    from vacinacao.main import download, generate_results

    logger.info('Starting reindex...')
    existing_files = s3.get_existing_files(settings.S3_FILES_BUCKET)
    new_pdfs: List[dict] = download(existing_files)

    logger.info("Generating results...")
    new_results: List[str] = generate_results(existing_files)
    existing_files.extend(new_results)

    logger.info("Compiling index...")
    compile_index(new_pdfs)

    logger.info("Finished reindex.")

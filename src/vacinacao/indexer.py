import json
import gzip
from datetime import date

from vacinacao import s3, settings
from vacinacao.log_utils import setup_logging


logger = setup_logging(__name__)


class IndexUnavailable(Exception):
    pass


def compile_index() -> None:
    from vacinacao.main import pull_files
    existing_results = s3.fetch_file_names("_results.txt")
    logger.info("Got results s3 keys.")

    current_index = pull_index()
    missing_in_index = set(existing_results).difference(current_index)

    new_index = pull_files(missing_in_index)
    logger.info("Pulled results files into memory.")
    new_index.update(current_index)

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


if __name__ == "__main__":
    from vacinacao.main import download, generate_results

    logger.info('Starting reindex...')
    existing_files = s3.get_existing_files(settings.S3_FILES_BUCKET)
    download(existing_files)

    logger.info("Generating results...")
    generate_results(existing_files)

    logger.info("Compiling index...")
    compile_index()

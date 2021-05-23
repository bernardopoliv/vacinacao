from datetime import date
import json

from vacinacao import s3
from vacinacao.log_utils import setup_logging


logger = setup_logging(__name__)


class IndexUnavailable(Exception):
    pass


def compile_index():
    from vacinacao.main import fetch_file_names, pull_files
    existing_results = fetch_file_names("_results.txt")
    logger.info("Got results s3 keys.")

    in_memory_files = pull_files(existing_results)
    logger.info("Pulled results files into memory.")

    index_json = json.dumps(in_memory_files)
    logger.info("Dumped index into JSON string.")

    index_filename = _get_todays_index()
    s3.upload(index_filename, bytes(index_json, encoding="utf8"))

    logger.info(f"Successfully wrote index file '{index_filename}'.")


def pull_index():
    index_filename = _get_todays_index()
    if s3.file_exists(index_filename):
        index_json = s3.pull(index_filename).decode()
        return json.loads(index_json)
    else:
        raise IndexUnavailable()


def _get_todays_index():
    return f"index_{date.today().isoformat()}.json"


if __name__ == "__main__":
    compile_index()

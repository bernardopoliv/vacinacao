from typing import List

from vacinacao import settings
from vacinacao.service_layer import indexer
from vacinacao.log_utils import setup_logging


logger = setup_logging(__name__)


def match_text(result_text, searched_name=None):
    names = [searched_name] if searched_name else settings.NAME_LOOKUPS
    names_found = [name for name in names if name.lower() in result_text]
    # Make user friendly to show in the result page
    return names_found[0] if len(names_found) == 1 else names_found


def search_name(searched_name):
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

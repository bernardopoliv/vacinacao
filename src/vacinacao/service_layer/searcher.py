from vacinacao.log_utils import setup_logging
from vacinacao.service_layer import indexer, utils

logger = setup_logging(__name__)


def match_text(result_text, searched_name: str):
    return searched_name if searched_name.lower() in result_text else ""


def search_name(searched_name):
    logger.info("Started `read` method for name: %s." % searched_name)
    index = indexer.get_most_recent_index()
    logger.info("Got index into memory.")

    searched_names = {searched_name.strip()}
    searched_names.add(utils.sanitize(searched_name))

    found_list = []
    for content_hash, file_meta in index.items():
        if not file_meta.get("content"):
            logger.warning(f"File {content_hash} without content.")
            continue

        for name in searched_names:
            found = match_text(str(file_meta["content"]), name)
            if found:
                found_list.append({"names": found, "url": file_meta["url"]})
            logger.debug(
                f'{content_hash}: {found if found else "No results in this file."}'
            )

    return found_list

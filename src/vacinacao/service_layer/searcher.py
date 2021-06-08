from vacinacao import settings
from vacinacao.log_utils import setup_logging
from vacinacao.service_layer import indexer

logger = setup_logging(__name__)


def match_text(result_text, searched_name=None):
    names = [searched_name] if searched_name else settings.NAME_LOOKUPS
    names_found = [name for name in names if name.lower() in result_text]
    # Make user friendly to show in the result page
    return names_found[0] if len(names_found) == 1 else names_found


def search_name(searched_name):
    logger.info("Started `read` method.")

    index = indexer.get_current_index()
    logger.info("Got index into memory.")

    found_list = []
    for content_hash, file_meta in index.items():
        if not file_meta.get("content"):
            logger.warning(f"File {content_hash} without content.")
            continue
        found = match_text(str(file_meta["content"]), searched_name)
        if found:
            found_list.append({"names": found, "url": file_meta["url"]})
        logger.info(f'{content_hash}: {found if found else "No results in this file."}')

    return found_list

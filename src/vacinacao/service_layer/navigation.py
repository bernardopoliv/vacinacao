import json

import requests

from vacinacao import settings
from vacinacao.log_utils import setup_logging

logger = setup_logging(__name__)


def get_file_urls():
    logger.info("Getting file URLs from direct XML parse...")
    response = requests.get(settings.VAC_PUBLIC_LIST_URL)
    # This is actually a javascript file.
    # The json object we need starts at char 47 and ends at -2
    # TODO: Improve this parsing. Using this as a quick hack to get the index back in shape.
    content_str = response.content.decode("utf8")
    content_fixed_urls = content_str.replace(
        "./pdfs/", "https://coronavirus.fortaleza.ce.gov.br/pdfs/"
    )
    response_json = json.loads(content_fixed_urls[47:-2])
    return __urls_from_json(response_json)


def __urls_from_json(obj: dict):
    rows = obj["table"]["rows"][1:]
    return [{"url": r["c"][2]["v"], "date": "dummy"} for r in rows]

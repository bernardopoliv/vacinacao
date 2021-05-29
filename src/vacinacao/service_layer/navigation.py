import requests
from lxml import etree

from vacinacao import settings
from vacinacao.log_utils import setup_logging

logger = setup_logging(__name__)


def get_file_urls():
    logger.info("Getting file URLs from direct XML parse...")
    response = requests.get(settings.VAC_PUBLIC_LIST_URL)
    tree = etree.fromstring(response.content)
    return __urls_from_response(tree)


def __urls_from_response(tree):
    urls = []
    for element in tree.iterchildren():
        for subelement in element:
            txt = subelement.text
            if txt and "pdf" in txt and txt.startswith("https:"):
                urls.append({"url": subelement.text, "date": "dummy"})
    logger.info("Created list of file URLs to return.")
    return urls

from datetime import datetime, timedelta
from time import sleep
from typing import List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from log_utils import setup_logging

logger = setup_logging(__name__)


def get_urls_for_files(url) -> List[str]:
    options = Options()
    options.add_argument("--headless")
    browser = webdriver.Firefox(options=options)
    browser.get(url)
    logger.info(f'Started navigating at {url}')
    sleep(3)

    return __find_urls(browser.page_source)


def __find_urls(html_content):
    urls = []
    html = html_content
    soup = BeautifulSoup(html, 'lxml')

    # TODO: Think in a better solution for this
    # Arbitrarily from beginning of current year until late next year
    date_range = [datetime(2021, 1, 1) + timedelta(days=x) for x in range(500)]

    for i in soup.find(id='boletinsAnteriores').find_all('a'):
        for day in date_range:
            is_searched_date = day.strftime('%d/%m/%Y') or day.strftime('%d.%m.%Y')
            url = i['href']
            if is_searched_date in i.text:
                if 'http' in url:
                    urls.append({'url': url, 'date': day.strftime('%d_%m_%Y')})
                else:
                    logger.info(f'ignoring bad url: {url}')
    return urls

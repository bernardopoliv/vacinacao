from time import sleep
from datetime import datetime, timedelta
from typing import List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from log_utils import setup_logging
from settings import VAC_PUBLIC_LIST_URL


logger = setup_logging(__name__)


def get_urls_for_date_range(initial_date: str, days_ahead: int = 1) -> List[str]:
    if initial_date is None:
        # Default: current day
        initial_date = datetime.today().strftime('%d/%m/%Y')

    options = Options()
    options.add_argument("--headless")
    browser = webdriver.Firefox(options=options)
    browser.get(VAC_PUBLIC_LIST_URL)
    sleep(3)

    return __find_urls(browser.page_source, initial_date, days_ahead)


def __find_urls(html_content, initial_date, days_ahead):
    urls = []
    html = html_content
    soup = BeautifulSoup(html, 'lxml')
    for i in soup.find(id='boletinsAnteriores').find_all('a'):
        date_range = [
            datetime.strptime(initial_date, '%d/%m/%Y') + timedelta(days=x)
            for x in range(days_ahead)
        ]
        for day in date_range:
            is_searched_date = day.strftime('%d/%m/%Y') or day.strftime('%d.%m.%Y')
            url = i['href']
            if is_searched_date in i.text:
                if 'http' in url:
                    urls.append({'url': url, 'date': day.strftime('%d_%m_%Y')})
                else:
                    logger.info(f'ignoring bad url: {url}')

    return urls
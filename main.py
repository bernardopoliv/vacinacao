from datetime import datetime
from time import sleep

import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text
from selenium import webdriver

from settings import VAC_PUBLIC_LIST_URL, NAME_LOOKUPS, ROOT_DIR


def download(date=None):
    if date is None:
        # Default: current day
        date = datetime.today().strftime('%d/%m/%Y')

    browser = webdriver.Firefox()
    browser.get(VAC_PUBLIC_LIST_URL)
    # sleep(4)
    html = browser.page_source
    soup = BeautifulSoup(html, 'lxml')

    urls = []
    for i in soup.find(id='boletinsAnteriores').find_all('a'):
        if date in i.text:
            url = i['href']
            urls.append(url)

    files = []
    for i, url in enumerate(urls, start=1):
        response = requests.get(url)
        filename = f'{ROOT_DIR}file_{date.replace("/", "_")}_{i}.pdf'
        files.append(filename)

        with open(filename, 'wb') as f:
            f.write(response.content)

    return files


def read(filenames: list):
    for f in filenames:
        text = extract_text(f)
        for name in NAME_LOOKUPS:
            if name in text:
                print(f'{f}: {name}')


if __name__ == '__main__':
    filenames = download('05/05/2021')
    read(filenames)

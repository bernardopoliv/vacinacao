from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta
from time import sleep

import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text
from selenium import webdriver

import settings


def download(initial_date: str, days_ahead: int = 1):
    if initial_date is None:
        # Default: current day
        initial_date = datetime.today().strftime('%d/%m/%Y')

    browser = webdriver.Firefox()
    browser.get(settings.VAC_PUBLIC_LIST_URL)
    sleep(4)

    urls = find_urls(browser, initial_date, days_ahead)
    print(f'Found {len(urls)} lists. Downloading...')

    file_names = _download(urls)
    print('File(s) downloaded successfully!\n')
    return file_names


def _download(urls):
    filenames = []

    for i, url in enumerate(urls, start=1):
        try:
            response = requests.get(url['url'])
        except Exception:
            continue

        filename = f'{settings.ROOT_DIR}file_{url["date"]}__{i}.pdf'
        filenames.append(filename)

        with open(filename, 'wb') as f:
            f.write(response.content)
    return filenames


def find_urls(browser, initial_date, days_ahead):
    urls = []
    html = browser.page_source
    soup = BeautifulSoup(html, 'lxml')
    for i in soup.find(id='boletinsAnteriores').find_all('a'):
        date_range = [
            datetime.strptime(initial_date, "%d/%m/%Y") + timedelta(days=x)
            for x in range(days_ahead)
        ]
        for day in date_range:
            if day.strftime('%d/%m/%Y') in i.text:
                url = i['href']
                urls.append({"url": url, "date": day.strftime('%d_%m_%Y')})

    return urls


def _read(filename):
    try:
        results = extract_text(filename)
    except Exception:
        return

    found = []
    for name in settings.NAME_LOOKUPS:
        if name in results:
            found.append(name)
    print(
        f'{filename.split("/")[-1]}: '
        f'{found if found else "No results in this file."}'
    )


def read(filenames):
    with ProcessPoolExecutor() as pool:
        pool.map(_read, filenames)


if __name__ == '__main__':
    filenames = download(settings.INITIAL_DATE, settings.DAYS_AHEAD)
    read(filenames=filenames)

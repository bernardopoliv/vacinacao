import argparse
import asyncio
import glob
import os
import random
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta
from time import sleep

import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

import settings

parser = argparse.ArgumentParser(description='Look for your name in Ceará vaccination lists.')
parser.add_argument('-k', '--keep', action='store_true', help='keep downloaded files in files directory.')


async def perform_request(url):
    print(url)
    loop = asyncio.get_event_loop()
    try:
        return loop.run_in_executor(None, requests.get, url)
    except:
        return


def download(initial_date: str, days_ahead: int = 1):
    if initial_date is None:
        # Default: current day
        initial_date = datetime.today().strftime('%d/%m/%Y')

    options = Options()
    options.add_argument("--headless")
    browser = webdriver.Firefox(firefox_options=options)
    browser.get(settings.VAC_PUBLIC_LIST_URL)
    sleep(3)
    urls = find_urls(browser, initial_date, days_ahead)
    print(f'Found {len(urls)} lists. Downloading...')

    file_names = asyncio.run(_download(urls))
    print('File(s) downloaded successfully!\n')
    return file_names


async def _download(urls):
    filenames = []
    futures = await asyncio.gather(*[
        perform_request(url['url']) for url in urls
    ])

    for coro in asyncio.as_completed(futures):
        response = await coro
        filename = f'{settings.ROOT_DIR}/files/file__{random.randint(1, 300)}.pdf'
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
            url = i['href']
            if day.strftime('%d/%m/%Y') in i.text and 'http' in url:
                urls.append({"url": url, "date": day.strftime('%d_%m_%Y')})

    return urls


def _read(filename):
    try:
        results = extract_text(filename)
    except Exception:
        return

    found = [name for name in settings.NAME_LOOKUPS if name in results]

    print(
        f'{filename.split("/")[-1]}: '
        f'{found if found else "No results in this file."}'
    )


def read(filenames):
    with ProcessPoolExecutor() as pool:
        pool.map(_read, filenames)


def delete_files(file_directory):
    files = glob.glob('{}/*'.format(file_directory), recursive=True)
    for f in files:
        try:
            os.remove(f)
        except OSError as e:
            print("Error: %s : %s" % (f, e.strerror))


if __name__ == '__main__':
    args = parser.parse_args()

    filenames = download(settings.INITIAL_DATE, settings.DAYS_AHEAD)
    read(filenames=filenames)

    if not args.keep:
        delete_files(settings.FILES_DIR)

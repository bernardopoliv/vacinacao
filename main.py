import argparse
import asyncio
import glob
import os
import urllib
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta
from time import sleep
from typing import List

import boto3
import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from settings import (
    VAC_PUBLIC_LIST_URL,
    FILES_DIR,
    NAME_LOOKUPS,
    INITIAL_DATE,
    DAYS_AHEAD,
    S3_FILES_BUCKET
)

parser = argparse.ArgumentParser(
    description='Look for your name in Ceará vaccination lists.'
)
parser.add_argument(
    '-k',
    '--keep',
    action='store_true',
    help='keep downloaded files in files directory.',
)


async def perform_request(url):
    print(url)
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, requests.get, url)


def download(initial_date: str, days_ahead: int = 1):
    if initial_date is None:
        # Default: current day
        initial_date = datetime.today().strftime('%d/%m/%Y')

    options = Options()
    options.add_argument("--headless")
    browser = webdriver.Firefox(firefox_options=options)
    browser.get(VAC_PUBLIC_LIST_URL)
    sleep(3)
    urls = find_urls(browser, initial_date, days_ahead)
    print(f'Found {len(urls)} lists. Downloading...')

    filenames = asyncio.run(_download(urls))
    print('File(s) downloaded successfully!\n')
    return filenames


async def _download(urls):
    filenames: List[str] = []
    future_responses = await asyncio.gather(
        *[perform_request(url['url']) for url in urls]
    )

    for resp in asyncio.as_completed(future_responses):
        response = await resp
        filename = urllib.parse.quote(response.url, '')
        filenames.append(filename)

        print(f'Uploading {filename} to S3 bucket')
        with open(filename, 'wb') as f:
            f.write(response.content)
            upload_to_s3(filename)

    return filenames


def upload_to_s3(filename):
    s3 = boto3.client('s3')
    with open(filename, "rb") as file:
        s3.upload_fileobj(file, S3_FILES_BUCKET, filename)


def find_urls(browser, initial_date, days_ahead):
    urls = []
    html = browser.page_source
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
                    print(f'ignoring bad url: {url}')

    return urls


def _read(filename):
    try:
        results = extract_text(filename).lower()
    except Exception:
        return

    found = [name for name in NAME_LOOKUPS if name.lower() in results]

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

    filenames = download(INITIAL_DATE, DAYS_AHEAD)
    read(filenames=filenames)

    if not args.keep:
        delete_files(FILES_DIR)

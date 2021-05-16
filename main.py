import asyncio
import urllib
import logging
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta
from time import sleep
from typing import List

import boto3
import botocore
import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from log_utils import setup_logging
from settings import (
    VAC_PUBLIC_LIST_URL,
    NAME_LOOKUPS,
    INITIAL_DATE,
    DAYS_AHEAD,
    S3_FILES_BUCKET
)


logger = logging.getLogger(__name__)
setup_logging(logger)


async def perform_request(url):
    logger.info(url)
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
    logger.info(f'Found {len(urls)} lists. Downloading...')

    filenames = asyncio.run(_download(urls))
    logger.info(f'{len(filenames)} files downloaded successfully!\n')

    filenames = [name for name in filenames if not file_exists_in_s3(name)]
    logger.info(f'Uploading {len(filenames)} new files to S3 bucket...')

    for name in filenames:
        upload_to_s3(name)

    return filenames


def file_exists_in_s3(filename):
    try:
        boto3.resource('s3').Object(S3_FILES_BUCKET, filename).load()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            # The object does not exist.
            return False
        else:
            # Something else has gone wrong.
            raise
    else:
        # The object does exist.
        return True


async def _download(urls):
    filenames: List[str] = []
    future_responses = await asyncio.gather(
        *[perform_request(url['url']) for url in urls]
    )

    for resp in asyncio.as_completed(future_responses):
        response = await resp
        filename = urllib.parse.quote(response.url.split("/")[-1], '')
        logger.info(f'Downloading: {filename}')
        with open(filename, 'wb') as file:
            file.write(response.content)
            filenames.append(file.name)

    return filenames


def upload_to_s3(filename):
    s3 = boto3.client('s3')
    logger.info(f'Uploading {filename} to S3...')
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
                    logger.info(f'ignoring bad url: {url}')

    return urls


def _read(filename):
    logger.info(f"Starting text extraction on '{filename}'...")
    try:
        raw_results = extract_text(filename)
        results = raw_results.lower()
    except Exception:
        return

    logger.info("Searching for name in results...")
    found = [name for name in NAME_LOOKUPS if name.lower() in results]

    logger.info(
        f'{filename.split("/")[-1]}: '
        f'{found if found else "No results in this file."}'
    )


def read(filenames):
    with ProcessPoolExecutor() as pool:
        pool.map(_read, filenames)


if __name__ == '__main__':
    logger.info("Starting...")
    filenames = download(INITIAL_DATE, DAYS_AHEAD)
    read(filenames=filenames)

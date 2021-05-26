import asyncio
import io
from typing import List

import boto3
import botocore

from vacinacao.log_utils import setup_logging
from vacinacao.settings import S3_FILES_BUCKET, PULL_RESULTS_ASYNC

logger = setup_logging(__name__)
s3 = boto3.client("s3")


def upload(filename: str, file_in_memory=None) -> None:
    logger.info(f'Uploading {filename} to S3...')

    if file_in_memory:
        s3.upload_fileobj(io.BytesIO(file_in_memory), S3_FILES_BUCKET, filename)
    else:
        with open(filename, "rb") as file:
            s3.upload_fileobj(file, S3_FILES_BUCKET, filename)

    logger.info(f"Finished uploading {filename} to S3.")


def file_exists(filename: str) -> bool:
    try:
        logger.debug(f"Looking for '{filename}' in S3...")
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
        logger.debug(f"'{filename}' exists.")
        return True


def pull(key: str) -> bytes:
    logger.info(f'Pulling file: {key}')
    s3_file = boto3.resource('s3').Object(S3_FILES_BUCKET, key)
    response = s3_file.get()
    content = response['Body'].read()
    logger.info(f"Got content for file {key}")
    return content


def get_existing_files(bucket_name) -> List[str]:
    logger.info("Looking for existing files in the S3 bucket...")
    return [
        f.key for f
        in boto3.resource('s3').Bucket(bucket_name).objects.all()
    ]


async def async_pull(key):
    logger.info(f'Async pulling file: {key}')
    s3_file = boto3.resource('s3').Object(S3_FILES_BUCKET, key)
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, s3_file.get)


def fetch_file_names(endswith):
    return [
        f for f in get_existing_files(S3_FILES_BUCKET) if f.endswith(endswith)
    ]


async def _read(s3_keys):
    future_results = await asyncio.gather(
        *[asyncio.ensure_future(s3.bound_async_pull(key)) for key in s3_keys]
    )

    results = []
    for r in asyncio.as_completed(future_results):
        result = await r
        results.append(
            str(result['Body'].read())
        )
        logger.info("Downloaded and appended content for result.")
    return results


def pull_files(keys: List[str]) -> dict:
    if PULL_RESULTS_ASYNC:
        logger.info("Pulling files async.")
        results = asyncio.run(_read(keys))
    else:
        logger.info("Pulling files synchronously.")
        results = {result_key: str(pull(result_key)) for result_key in keys}

    return results

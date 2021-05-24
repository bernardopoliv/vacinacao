import asyncio
import io
from typing import List

import boto3
import botocore

from vacinacao.log_utils import setup_logging
from vacinacao.settings import S3_FILES_BUCKET

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
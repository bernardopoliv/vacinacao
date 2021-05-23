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


def pull(key: str) -> bytes:
    logger.info(f'Pulling file: {key}')
    s3_file = boto3.resource('s3').Object(S3_FILES_BUCKET, key)
    response = s3_file.get()
    return response['Body'].read()


def get_existing_files(bucket_name) -> List[str]:
    return [
        f.key for f
        in boto3.resource('s3').Bucket(bucket_name).objects.all()
    ]


async def async_pull(key):
    logger.info(f'Async pulling file: {key}')
    s3_file = boto3.resource('s3').Object(S3_FILES_BUCKET, key)
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, s3_file.get)

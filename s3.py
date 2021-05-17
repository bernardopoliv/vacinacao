from typing import List

import boto3
import botocore

from log_utils import setup_logging
from settings import S3_FILES_BUCKET


logger = setup_logging(__name__)
s3 = boto3.client("s3")


def upload(filename: str) -> None:
    logger.info(f'Uploading {filename} to S3...')
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
    s3_file = boto3.resource('s3').Object(S3_FILES_BUCKET, key)
    response = s3_file.get()
    return response['Body'].read()


def get_existing_files(bucket_name) -> List[str]:
    return [
        f.key for f
        in boto3.resource('s3').Bucket(bucket_name).objects.all()
    ]

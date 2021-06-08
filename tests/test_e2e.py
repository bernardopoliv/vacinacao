import os
import io
import gzip
import pytest
from datetime import date

import boto3
from moto import mock_s3

from vacinacao.entrypoints import app
from vacinacao.settings import S3_FILES_BUCKET
from vacinacao.service_layer.indexer import get_index_filename_for_date


PATH = os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def client():
    """
    Test client with mocked s3 pre-loaded with a mock index.
    """
    with app.test_client() as client:
        with mock_s3() as s3:
            s3 = boto3.resource("s3")

            s3_client = boto3.client("s3")
            s3.create_bucket(Bucket=S3_FILES_BUCKET)

            index_fixture = bytes(
                open(PATH + "/../tests/index_fixture.json").read(), "utf8"
            )
            s3_client.upload_fileobj(
                io.BytesIO(gzip.compress(index_fixture)),
                S3_FILES_BUCKET,
                get_index_filename_for_date(date.today()),
            )
            yield client


@pytest.mark.e2e
def test_searching_a_name(client, snapshot):
    # A guest can open the page
    response = client.get("/")
    snapshot.assert_match(response.data, "main_page.html")

    # Searches a name
    response = client.post(
        "/search", json={"name": "Jose"}, headers={"Content-Type": "application/json"}
    )

    # The results contain the expected entry.
    expected_fragment = {
        "names": "Jose",
        "url": "https://site-da-prefeitura.com/abc.pdf",
    }
    assert expected_fragment in response.json

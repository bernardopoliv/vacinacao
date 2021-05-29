import pytest

from vacinacao.entrypoints import app


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


@pytest.mark.e2e
def test_searching_a_name(client, snapshot):
    # A guest can open the page
    response = client.get("/")
    snapshot.assert_match(response.data, "main_page.html")

    # Searches a name
    response = client.post("/search", json={"name": "Jose"}, headers={"Content-Type": "application/json"})

    # The results contain the PDF's name.
    expected_fragment = {'names': 'Jose', 'file_key': '290521PROFESSORESD1_results.txt'}
    assert expected_fragment in response.json["found"]

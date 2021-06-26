import pytest

from vacinacao.service_layer.utils import sanitize


@pytest.mark.parametrize(
    "unformatted_names,expected_name",
    [
        (("José", "José ", "Jos3e", 'J/"os#$%é'), "Jose"),
        (("Zé das Couve", "Zé das C9*7ouve "), "Ze das Couve"),
        (("Conceição",), "Conceicao"),
    ],
)
def test_sanitize(unformatted_names, expected_name):
    for name in unformatted_names:
        assert sanitize(name) == expected_name

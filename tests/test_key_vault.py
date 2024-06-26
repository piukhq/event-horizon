from collections.abc import Generator
from unittest import mock

import pytest

from azure.keyvault.secrets import SecretClient

from event_horizon.key_vault import KeyVault


@pytest.fixture(name="mocked_client")
def mock_client() -> mock.MagicMock:
    return mock.MagicMock(spec=SecretClient)


def test_init_keyvault() -> None:
    try:
        KeyVault("http://vault")
    except Exception:
        pytest.fail("Could not init KeyVault instance")


def test_init_keyvault_no_args() -> None:
    with pytest.raises(ValueError):
        KeyVault()


def test_get_secret(mocked_client: mock.MagicMock) -> None:
    fake_secrets = [
        ('{"value": "secret #1"}', "value"),
        ('{"other_key": "secret #2"}', "other_key"),
        ('"a-json-string-object"', None),
        ('{"another_key": "secret #2"}', None),
        ("just-a-normal-string", None),
    ]

    def secret_factory() -> Generator:
        for secret in fake_secrets:
            mock_secret = mock.MagicMock()
            mock_secret.value = secret[0]
            yield mock_secret

    mocked_client.get_secret.side_effect = secret_factory()

    key_vault = KeyVault(client=mocked_client)
    results = [key_vault.get_secret("made-up-name", key=key_to_retrieve) for _, key_to_retrieve in fake_secrets.copy()]

    assert results == [
        "secret #1",
        "secret #2",
        "a-json-string-object",
        {"another_key": "secret #2"},
        "just-a-normal-string",
    ]


def test_get_secret_no_key_in_secret(mocked_client: mock.MagicMock) -> None:
    mocked_client.get_secret.return_value.value = '{"value": "shhh! secret"}'
    key_vault = KeyVault(client=mocked_client)
    with pytest.raises(KeyError):
        key_vault.get_secret("made-up-name", key="no-key-with-this-name")

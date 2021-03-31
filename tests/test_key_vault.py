from unittest import mock

import pytest

from azure.keyvault.secrets import SecretClient

from app.key_vault import KeyVault


@pytest.fixture
def mock_client() -> SecretClient:
    return mock.MagicMock(spec=SecretClient)


def test_init_keyvault() -> None:
    with pytest.raises(ValueError):
        KeyVault()


def test_get_secret(mock_client: SecretClient) -> None:
    mock_client.get_secret.return_value.value = '{"value": "shhh! secret"}'
    key_vault = KeyVault(client=mock_client)
    assert key_vault.get_secret("test") == "shhh! secret"


def test_get_secret_no_key_in_secret(mock_client: SecretClient) -> None:
    mock_client.get_secret.return_value.value = '{"value": "shhh! secret"}'
    key_vault = KeyVault(client=mock_client)
    with pytest.raises(KeyError):
        key_vault.get_secret("test", "no-key-with-this-name")


def test_get_secrets(mock_client: SecretClient) -> None:
    secret_values = [
        '{"value": "secret #1"}',
        '{"other_key": "secret #2"}',
        '"just-a-stringy-secret"',
        '{"another_key": "secret #2"}',
    ]

    def secret_factory(arg: str) -> mock.MagicMock:
        mock_secret = mock.MagicMock()
        mock_secret.value = secret_values.pop(0)
        return mock_secret

    mock_client.get_secret.side_effect = secret_factory

    key_vault = KeyVault(client=mock_client)
    secret_dict = key_vault.get_secrets({"name1": "value", "name2": "other_key", "name3": None, "name4": None})
    assert secret_dict == {
        "name1": "secret #1",
        "name2": "secret #2",
        "name3": "just-a-stringy-secret",
        "name4": {"another_key": "secret #2"},
    }


def test_get_secrets_no_key_in_any_secret_requested(mock_client: SecretClient) -> None:
    mock_client.get_secret.return_value.value = '{"value": "shhh! secret"}'

    key_vault = KeyVault(client=mock_client)
    with pytest.raises(KeyError):
        key_vault.get_secrets({"name1": "no-key-with-this-name"})

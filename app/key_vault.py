import json

from typing import Any, Optional

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


class KeyVault:
    def __init__(self, vault_url: Optional[str] = None, /, *, client: Optional[SecretClient] = None) -> None:
        if not (client or vault_url):
            raise ValueError("must provide either vault_url or client")
        self.client = client or SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())

    def get_secret(self, name: str, /, *, key: Optional[str] = "value") -> Any:
        """Return the content of a secret in the vault.

        Secrets may be a mapping or other JSON serializable objects. Obtain
        a specific element of a secret mapping by providing a key.

        Example secrets named 'secret1', 'secret2', 'secret3', 'secret4' and
        'secret5' in the vault respectively:

            * '{"value": "123456789"}'
            * '{"key": "--- RSA PRIVATE KEY ---\\nkey matter..."}'
            * '"dcc34040b3d145eb92e899eae2b0d886"'  # json string
            * '{"value": "f0fb00f0741b45929660"}'
            * "44ef3c2b18b4484dbb9229226beaa98c"  # normal string

        >>> get_secret("secret1", "value")
        123456789
        >>> get_secret("secret2", "key")
        --- RSA PRIVATE KEY ---\\nkey matter...
        >>> get_secret("secret3", None)
        dcc34040b3d145eb92e899eae2b0d886
        >>> get_secret("secret4, None)
        {"value": "f0fb00f0741b45929660"}
        >>> get_secret("secret5, None)
        44ef3c2b18b4484dbb9229226beaa98c

        """
        secret = self.client.get_secret(name)
        try:
            val = json.loads(secret.value)
        except json.decoder.JSONDecodeError:
            return secret.value
        else:
            return val[key] if key is not None else val

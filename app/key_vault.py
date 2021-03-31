import json

from typing import Any, Dict, Optional

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


class KeyVault:
    def __init__(self, *, vault_url: Optional[str] = None, client: Optional[SecretClient] = None) -> None:
        if not (client or vault_url):
            raise ValueError("must provide either vault_url or client")
        self.client = client or SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())

    def get_secret(self, name: str, key: Optional[str] = "value") -> str:
        return self.get_secrets({name: key})[name]

    def get_secrets(self, name_key_map: Dict[str, Optional[str]]) -> Dict[str, Any]:
        """Return the content of secrets in the vault as a dict keyed by
        requested secret name.

        Secrets may be a mapping or other JSON serializable objects. Obtain
        specific elements of a secret mapping by providing a key.

        Example secrets named 'secret-password', 'secret-cert',
        'secret-string-1' and 'string-secret-2' in the vault respectively:

            * '{"value": "!#123456789!#"}'
            * '{"key": "--- RSA PRIVATE KEY ---\\nkey goes here....."}'
            * '"dcc34040b3d145eb92e899eae2b0d886"'
            * '{"value": "f0fb00f0741b45929660"}'

        >>> get_secrets({"secret-password": "value", "secret-cert": "key",
        ... "secret-string1": None, "secret-string2": None})
        {"secret-password": "!#123456789!#",
         "secret-cert": "--- RSA PRIVATE KEY ---\\nkey goes here.....",
         "secret-string-1": "dcc34040b3d145eb92e899eae2b0d886"}
         "secret-string-2": {"value": "f0fb00f0741b45929660"}}

        """
        secrets: Dict[str, str] = {}
        for name, key in name_key_map.items():
            val = json.loads(self.client.get_secret(name).value)
            secrets[name] = val[key] if key is not None else val
        return secrets

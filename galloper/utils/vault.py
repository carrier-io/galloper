import re

import hvac

from galloper.config import Config


class VaultClient:
    def __init__(self, config):
        self.client = hvac.Client(
            url=config['url'],
            verify=config.get('ssl_verify', False),
            namespace=config.get('namespace', None),
        )

        if 'auth_token' in config:
            self.client.token = config['auth_token']
        elif 'auth_role_id' in config:
            self.client.auth_approle(
                config.get('auth_role_id'),
                config.get('auth_secret_id', '')
            )
        if not self.client.is_authenticated():
            raise AssertionError('Failed to authenticated in Vault')
        if self.client.sys.is_sealed():
            raise AssertionError('Vault is sealed')

        self.secrets_path = config['secrets_path']
        self.mount_point = config['secrets_mount_point']

        self._secrets = self.fetch_secrets()

    def fetch_secrets(self):
        return self.client.secrets.kv.v2.read_secret_version(
            path=self.secrets_path,
            mount_point = self.mount_point
        ).get('data', dict()).get('data', dict())

    def get_secrets(self):
        return self._secrets

    def expand_secrets(self, src):
        if isinstance(src, dict):
            return {key: self.expand_secrets(value) for key, value in src.items()}
        if isinstance(src, list):
            return [self.expand_secrets(item) for item in src]
        if isinstance(src, str):
            placeholders = set(re.findall(r'({{secret\s?:\s?)(\S+?)(\s?}})', src))
            for key in placeholders:
                # If no such secret exists in Vault - will leave as is
                value = self._secrets.get(key[1], ''.join(key))
                src = src.replace(''.join(key), value)
            return src
        return src


def create_vault_client(project):
    config = Config()
    if not config.VAULT_URL:
        raise ValueError("VAULT_URL environment variable is not set")

    vault_config = dict(
        url=config.VAULT_URL,
        auth_token=project.secrets_json['vault_token'],
        secrets_path=f"carrier_{project.id}_secrets",
        secrets_mount_point='carrier_kv',
        # auth_role_id=project.vault_role_id,
        # auth_secret_id=project.vault_secret_id,
        # namespace=project.vault_namespace,
        # secrets_path=project.vault_path,
        # secrets_path=project.vault_mount_point,
    )
    return VaultClient(vault_config)
        
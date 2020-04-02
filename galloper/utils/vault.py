import hvac

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
            raise ValueError('Failed to authenticated in Vault')
        if self.client.sys.is_sealed():
            raise AssertionError('Vault is sealed')

        self.secrets_path = config['secrets_path']
        self.mount_point = config['secrets_mount_point']

    def get_secrets(self):
        return self.client.secrets.kv.v2.read_secret_version(
            path=self.secrets_path,
            mount_point = self.mount_point
        ).get('data', dict()).get('data', dict())
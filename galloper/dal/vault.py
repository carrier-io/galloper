#!/usr/bin/python
# coding=utf-8

#     Copyright 2020 getcarrier.io
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

""" Vault tools """

from jinja2 import Template

import hvac  # pylint: disable=E0401
import requests  # pylint: disable=E0401
from requests.exceptions import ConnectionError
import galloper.constants as consts
from galloper.database.models.vault import Vault
from galloper.database.models.project import Project
from flask import current_app


def init_vault():
    """ Initialize Vault """
    # Get Vault client
    try:
        client = hvac.Client(url=consts.VAULT_URL)
        # Initialize it if needed
        if not client.sys.is_initialized():
            vault = Vault.query.get(consts.VAULT_DB_PK)
            # Remove stale DB keys
            if vault is not None:
                Vault.apply_full_delete_by_pk(pk=consts.VAULT_DB_PK)
            # Initialize Vault
            vault_data = client.sys.initialize()
            # Save keys to DB
            vault = Vault(
                id=consts.VAULT_DB_PK,
                unseal_json=vault_data,
            )
            vault.insert()
        # Unseal if needed
        unseal(client)
        # Enable AppRole auth method if needed
        client = get_root_client()
        auth_methods = client.sys.list_auth_methods()
        if "carrier-approle/" not in auth_methods["data"].keys():
            client.sys.enable_auth_method(
                method_type="approle",
                path="carrier-approle",
            )
    except ConnectionError:
        return 0


def unseal(client):
    if client.sys.is_sealed():
        try:
            vault = Vault.query.get(consts.VAULT_DB_PK)
            client.sys.submit_unseal_keys(keys=vault.unseal_json["keys"])
        except AttributeError:
            init_vault()


def create_client():
    client = hvac.Client(url=consts.VAULT_URL)
    unseal(client)
    return client


def get_root_client():
    """ Get "root" Vault client instance """
    # Get Vault client
    client = create_client()
    # Get root token from DB
    vault = Vault.query.get(consts.VAULT_DB_PK)
    # Add auth info to client
    client.token = vault.unseal_json["root_token"]
    # Done
    return client


def get_project_client(project_id):
    """ Get "project" Vault client instance """
    # Get Vault client
    client = create_client()
    # Get project from DB
    project = Project.query.get(project_id)
    # Auth to Vault
    client.auth_approle(
        project.secrets_json["vault_auth_role_id"], project.secrets_json["vault_auth_secret_id"],
        mount_point="carrier-approle",
    )
    # Done
    return client


def initialize_project_space(project_id):
    """ Create project approle, policy and KV """
    client = get_root_client()
    # Create policy for project
    policy = """
        # Login with AppRole
        path "auth/approle/login" {
          capabilities = [ "create", "read" ]
        }

        # Read/write project secrets
        path "kv-for-{project_id}/*" {
          capabilities = ["create", "read", "update", "delete", "list"]
        }
        # Read/write project hidden secrets
        path "kv-for-hidden-{project_id}/*" {
          capabilities = ["create", "read", "update", "delete", "list"]
        }
    """.replace("{project_id}", str(project_id))
    client.sys.create_or_update_policy(
        name=f"policy-for-{project_id}",
        policy=policy,
    )
    # Create secrets KV
    client.sys.enable_secrets_engine(
        backend_type="kv",
        path=f"kv-for-{project_id}",
        options={"version": "2"},
    )
    client.secrets.kv.v2.create_or_update_secret(
        path="project-secrets",
        mount_point=f"kv-for-{project_id}",
        secret=dict(),
    )
    # Create hidden secrets KV
    client.sys.enable_secrets_engine(
        backend_type="kv",
        path=f"kv-for-hidden-{project_id}",
        options={"version": "2"},
    )
    client.secrets.kv.v2.create_or_update_secret(
        path="project-secrets",
        mount_point=f"kv-for-hidden-{project_id}",
        secret=dict(),
    )
    # Create AppRole
    approle_name = f"role-for-{project_id}"
    requests.post(
        f"{consts.VAULT_URL}/v1/auth/carrier-approle/role/{approle_name}",
        headers={"X-Vault-Token": client.token},
        json={"policies": [f"policy-for-{project_id}"]}
    )
    approle_role_id = requests.get(
        f"{consts.VAULT_URL}/v1/auth/carrier-approle/role/{approle_name}/role-id",
        headers={"X-Vault-Token": client.token},
    ).json()["data"]["role_id"]
    approle_secret_id = requests.post(
        f"{consts.VAULT_URL}/v1/auth/carrier-approle/role/{approle_name}/secret-id",
        headers={"X-Vault-Token": client.token},
    ).json()["data"]["secret_id"]
    # Done
    return {
        "auth_role_id": approle_role_id,
        "auth_secret_id": approle_secret_id
    }


def remove_project_space(project_id):
    """ Remove project-specific data from Vault """
    client = get_root_client()
    # Remove AppRole
    requests.delete(
        f"{consts.VAULT_URL}/v1/auth/carrier-approle/role/role-for-{project_id}",
        headers={"X-Vault-Token": client.token},
    )
    # Remove secrets KV
    client.sys.disable_secrets_engine(
        path=f"kv-for-{project_id}",
    )
    # Remove hidden secrets KV
    client.sys.disable_secrets_engine(
        path=f"kv-for-hidden-{project_id}",
    )
    # Remove policy
    client.sys.delete_policy(
        name=f"policy-for-{project_id}",
    )


def set_project_secrets(project_id, secrets):
    """ Set project secrets """
    client = get_project_client(project_id)
    client.secrets.kv.v2.create_or_update_secret(
        path="project-secrets",
        mount_point=f"kv-for-{project_id}",
        secret=secrets,
    )


def set_project_hidden_secrets(project_id, secrets):
    """ Set project hidden secrets """
    client = get_project_client(project_id)
    client.secrets.kv.v2.create_or_update_secret(
        path="project-secrets",
        mount_point=f"kv-for-hidden-{project_id}",
        secret=secrets,
    )


def get_project_secrets(project_id):
    """ Get project secrets """
    client = get_project_client(project_id)
    return client.secrets.kv.v2.read_secret_version(
        path="project-secrets",
        mount_point=f"kv-for-{project_id}",
    ).get("data", dict()).get("data", dict())


def get_project_hidden_secrets(project_id):
    """ Get project hidden secrets """
    client = get_project_client(project_id)
    return client.secrets.kv.v2.read_secret_version(
        path="project-secrets",
        mount_point=f"kv-for-hidden-{project_id}",
    ).get("data", dict()).get("data", dict())


def unsecret(value, secrets=None, project_id=None):
    if not secrets:
        secrets = get_project_secrets(project_id)
        hidden_secrets = get_project_hidden_secrets(project_id)
        for key, _value in hidden_secrets.items():
            if key not in list(secrets.keys()):
                secrets[key] = _value
    if isinstance(value, str):
        template = Template(value)
        return template.render(secret=secrets)
    elif isinstance(value, list):
        return unsecret_list(secrets, value)
    elif isinstance(value, dict):
        return unsecret_json(secrets, value)
    else:
        return value


def unsecret_json(secrets, json):
    for key in json.keys():
        json[key] = unsecret(json[key], secrets)
    return json


def unsecret_list(secrets, array):
    for i in range(len(array)):
        array[i] = unsecret(array[i], secrets)
    return array

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

import hvac  # pylint: disable=E0401
import requests  # pylint: disable=E0401
import galloper.constants as consts
from galloper.database.models.vault import Vault
from galloper.database.models.project import Project


def init_vault():
    """ Initialize Vault """
    # Get Vault client
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
    if client.sys.is_sealed():
        vault = Vault.query.get(consts.VAULT_DB_PK)
        client.sys.submit_unseal_keys(keys=vault.unseal_json["keys"])
    # Enable AppRole auth method if needed
    client = get_root_client()
    auth_methods = client.sys.list_auth_methods()
    if "carrier-approle/" not in auth_methods["data"].keys():
        client.sys.enable_auth_method(
            method_type="approle",
            path="carrier-approle",
        )


def get_root_client():
    """ Get "root" Vault client instance """
    # Get Vault client
    client = hvac.Client(url=consts.VAULT_URL)
    # Get root token from DB
    vault = Vault.query.get(consts.VAULT_DB_PK)
    # Add auth info to client
    client.token = vault.unseal_json["root_token"]
    # Done
    return client


def get_project_client(project_id):
    """ Get "project" Vault client instance """
    # Get Vault client
    client = hvac.Client(url=consts.VAULT_URL)
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
    """.replace("{project_id}", str(project_id))
    client.sys.create_or_update_policy(
        name=f"policy-for-{project_id}",
        policy=policy,
    )
    # Create KV
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
    # Remove KV
    client.sys.disable_secrets_engine(
        path=f"kv-for-{project_id}",
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


def get_project_secrets(project_id):
    """ Get project secrets """
    client = get_project_client(project_id)
    return client.secrets.kv.v2.read_secret_version(
        path="project-secrets",
        mount_point=f"kv-for-{project_id}",
    ).get("data", dict()).get("data", dict())

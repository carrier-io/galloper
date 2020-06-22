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

from json import loads, dumps
from requests import post, get
from galloper.dal.vault import get_project_secrets, set_project_secrets
import smtplib
from galloper.constants import EMAIL_NOTIFICATION_PATH
from galloper.api.base import create_task, update_task
from galloper.data_utils.file_utils import File


def jira_integration(args, project):
    try:
        if args["test"]:
            url = f'{args["config"]["jira_url"]}/rest/api/2/project'
            res = get(url, auth=(args["config"]["jira_login"], args["config"]["jira_password"]))
            if res.status_code == 200:
                message = "Successfully connected to Jira"
            else:
                message = "Connection failed"
            if "failed" not in message and args["config"]["jira_project"] not in res.text:
                message = "Connection succeed but project not found"
            return message
        else:
            jira_perf_api_config = {
                "assignee": args["config"]["jira_login"],
                "check_functional_errors": "True",
                "check_performance_degradation": "True",
                "check_missed_thresholds": "True",
                "performance_degradation_rate": 20,
                "missed_thresholds_rate": 50,
                "jira_labels": "performance, api",
                "jira_watchers": "",
                "jira_epic_key": ""
            }
            secrets = get_project_secrets(project.id)
            secrets["jira"] = dumps(args["config"])
            secrets["jira_perf_api"] = dumps(jira_perf_api_config)
            set_project_secrets(project.id, secrets)
            return "Jira settings saved"
    except Exception as e:
        return f"Failed. Jira settings not saved. {str(e)}"


def smtp_integration(args, project):
    try:
        if args["test"]:
            try:
                s = smtplib.SMTP_SSL(host=args['config']['smtp_host'], port=int(args['config']['smtp_port']))
                s.ehlo()
                s.login(args['config']['smtp_user'], args['config']['smtp_password'])
                return "SMTP server connected"
            except smtplib.SMTPException as e:
                return f"SMTP server not connected. {str(e)}"
        else:
            secrets = get_project_secrets(project.id)
            secrets["smtp"] = dumps(args["config"])
            if "email_notification_id" in secrets:
                update_task(secrets["email_notification_id"], dumps(args["config"]))
            else:
                email_notification_args = {
                    "funcname": "email_notification",
                    "invoke_func": "lambda_function.lambda_handler",
                    "runtime": "Python 3.7",
                    "env_vars": dumps(args["config"])
                }
                email_notification = create_task(project, File(EMAIL_NOTIFICATION_PATH), email_notification_args)
                secrets["email_notification_id"] = email_notification.task_id
            set_project_secrets(project.id, secrets)
            return "SMTP setting saved"
    except Exception as e:
        return f"Failed. SMTP server not connected. {str(e)}"

#   Copyright 2019 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from requests import get
from galloper.constants import LOKI_HOST


def get_results(test, int_start_time, int_end_time):
    url = f"{LOKI_HOST}/loki/api/v1/query_range"
    data = {
        "direction": "BACKWARD",
        "limit": 100000,
        "query": '{filename="/tmp/' + test + '.log"}',
        "start": int_start_time,
        "end": int_end_time
    }
    results = get(url, params=data, headers={"Content-Type": "application/json"}).json()
    issues = {}
    for result in results["data"]["result"]:
        for value in result['values']:
            _values = value[1].strip().split("\t")
            _issue = {"count": 1}
            _issue_key = ''
            for _ in _values:
                if ":" in _:
                    key, value = _[:_.index(':')], _[_.index(':')+1:].strip()
                    if key == 'Error key' and value in issues:
                        issues[value]["count"] += 1
                        continue
                    _issue[key] = value
            if 'Error key' in _issue and _issue['Error key'] not in issues.keys():
                issues[_issue['Error key']] = _issue
    return issues

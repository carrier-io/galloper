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

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
            _values = value[1].split("\t")
            _issue = {"count": 1}
            _issue_key = ''
            for _ in _values:
                if "Error key: " in _:
                    _issue_key = _.replace("Error key: ", "")
                    if _issue_key in issues:
                        issues[_issue_key]["count"] += 1
                        continue
                    else:
                        issues[_issue_key] = {}
                elif "Request name: " in _:
                    _issue['name'] = _.replace("Request name: ", "")
                elif "Method: " in _:
                    _issue['method'] = _.replace("Method: ", "")
                elif "Response code: " in _:
                    _issue['code'] = _.replace("Response code: ", "")
                elif "URL: " in _:
                    _issue['url'] = _.replace("URL: ", "")
                elif "Error message: " in _:
                    _issue['error'] = _.replace("Error message: ", "")
                elif "Request params: " in _:
                    _issue['params'] = _.replace("Request params: ", "")
                elif "URL: " in _:
                    _issue['url'] = _.replace("URL: ", "")
                elif "Headers: " in _:
                    _issue['headers'] = _.replace("Headers: ", "")
                elif "Response body: " in _:
                    _issue['response'] = _.replace("Response body: ", "")
            if _issue_key and not issues[_issue_key]:
                issues[_issue_key] = _issue
    return issues

import itertools
from pprint import pprint
from uuid import uuid4

results = [
    {
        "id": 174,
        "project_id": 1,
        "report_uid": "12345",
        "name": "Essential JS 2 for TypeScript - Webmail",
        "session_id": "3bde3e7a6a69a0bb49d4c2fbd4a51a90",
        "identifier": "Essential JS 2 for TypeScript - Webmail:/showcase/typescript/webmail/@3bde3e7a6a69a0bb49d4c2fbd4a51a90open(https://ej2.syncfusion.com/showcase/typescript/webmail/#/home)",
        "type": "page",
        "bucket_name": "reports",
        "file_name": "Essential JS 2 for TypeScript - Webmail_854fd83a-7dfb-490e-9b18-f25b24a25d00.html",
        "thresholds_total": 0,
        "thresholds_failed": 0,
        "requests": 35,
        "domains": 15,
        "total": 4073,
        "speed_index": 1014,
        "time_to_first_byte": 104,
        "time_to_first_paint": 974,
        "dom_content_loading": 911,
        "dom_processing": 2489,
        "locators": [
            {
                "command": "open",
                "target": "https://ej2.syncfusion.com/showcase/typescript/webmail/#/home",
                "value": ""
            }
        ],
        "resolution": "1911x950",
        "browser_version": "Chrome 84.0.4147.89"
    },
    {
        "id": 178,
        "project_id": 1,
        "report_uid": "12345",
        "name": "Essential JS 2 for TypeScript - Webmail",
        "session_id": "3bde3e7a6a69a0bb49d4c2fbd4a51a90",
        "identifier": "Essential JS 2 for TypeScript - Webmail:/showcase/typescript/webmail/@click(css selector=#tree li.e-level-2[data-uid='21'])",
        "type": "action",
        "bucket_name": "reports",
        "file_name": "Essential JS 2 for TypeScript - Webmail_1a28b2ac-7502-4700-9c20-84e5d5ab35fa.html",
        "thresholds_total": 0,
        "thresholds_failed": 0,
        "requests": 2,
        "domains": 2,
        "total": 2997,
        "speed_index": 982,
        "time_to_first_byte": 19,
        "time_to_first_paint": 0,
        "dom_content_loading": 1,
        "dom_processing": 0,
        "locators": [
            {
                "command": "open",
                "target": "https://ej2.syncfusion.com/showcase/typescript/webmail/#/home",
                "value": ""
            },
            {
                "command": "click",
                "target": "#tree li.e-level-2[data-uid='21']",
                "value": ""
            }
        ],
        "resolution": "1911x950",
        "browser_version": "Chrome 84.0.4147.89"
    },
    {
        "id": 181,
        "project_id": 1,
        "report_uid": "12345",
        "name": "Essential JS 2 for TypeScript - Webmail",
        "session_id": "3bde3e7a6a69a0bb49d4c2fbd4a51a90",
        "identifier": "Essential JS 2 for TypeScript - Webmail:/showcase/typescript/webmail/@click(css selector=li.e-level-1[data-uid='SF10205'])",
        "type": "action",
        "bucket_name": "reports",
        "file_name": "Essential JS 2 for TypeScript - Webmail_b98b028d-1abf-4944-ac03-093914106fc5.html",
        "thresholds_total": 0,
        "thresholds_failed": 0,
        "requests": 1,
        "domains": 1,
        "total": 448,
        "speed_index": 1261,
        "time_to_first_byte": 448,
        "time_to_first_paint": 0,
        "dom_content_loading": 1,
        "dom_processing": 0,
        "locators": [
            {
                "command": "open",
                "target": "https://ej2.syncfusion.com/showcase/typescript/webmail/#/home",
                "value": ""
            },
            {
                "command": "click",
                "target": "#tree li.e-level-2[data-uid='21']",
                "value": ""
            },
            {
                "command": "click",
                "target": "li.e-level-1[data-uid='SF10205']",
                "value": ""
            }
        ],
        "resolution": "1911x950",
        "browser_version": "Chrome 84.0.4147.89"
    },
    {
        "id": 183,
        "project_id": 1,
        "report_uid": "12345",
        "name": "Essential JS 2 for TypeScript - Webmail",
        "session_id": "3bde3e7a6a69a0bb49d4c2fbd4a51a90",
        "identifier": "Essential JS 2 for TypeScript - Webmail:/showcase/typescript/webmail/@click(css selector=li.e-level-1[data-uid='SF10202'])",
        "type": "action",
        "bucket_name": "reports",
        "file_name": "Essential JS 2 for TypeScript - Webmail_41a7ec6b-ed8e-4a15-a0ca-5bbc12638e88.html",
        "thresholds_total": 0,
        "thresholds_failed": 0,
        "requests": 1,
        "domains": 1,
        "total": 56,
        "speed_index": 1390,
        "time_to_first_byte": 55,
        "time_to_first_paint": 0,
        "dom_content_loading": 1,
        "dom_processing": 0,
        "locators": [
            {
                "command": "open",
                "target": "https://ej2.syncfusion.com/showcase/typescript/webmail/#/home",
                "value": ""
            },
            {
                "command": "click",
                "target": "#tree li.e-level-2[data-uid='21']",
                "value": ""
            },
            {
                "command": "click",
                "target": "li.e-level-1[data-uid='SF10205']",
                "value": ""
            },
            {
                "command": "click",
                "target": "li.e-level-1[data-uid='SF10202']",
                "value": ""
            }
        ],
        "resolution": "1911x950",
        "browser_version": "Chrome 84.0.4147.89"
    },
    {
        "id": 173,
        "project_id": 1,
        "report_uid": "12345",
        "name": "Essential JS 2 for TypeScript - Webmail",
        "session_id": "bdbf22b1d84826c8ebc524ee03c9cdc0",
        "identifier": "Essential JS 2 for TypeScript - Webmail:/showcase/typescript/webmail/@bdbf22b1d84826c8ebc524ee03c9cdc0open(https://ej2.syncfusion.com/showcase/typescript/webmail/#/home)",
        "type": "page",
        "bucket_name": "reports",
        "file_name": "Essential JS 2 for TypeScript - Webmail_db6423be-296d-4853-8201-f9a33cea2467.html",
        "thresholds_total": 0,
        "thresholds_failed": 0,
        "requests": 34,
        "domains": 15,
        "total": 2477,
        "speed_index": 872,
        "time_to_first_byte": 86,
        "time_to_first_paint": 859,
        "dom_content_loading": 832,
        "dom_processing": 2315,
        "locators": [
            {
                "command": "open",
                "target": "https://ej2.syncfusion.com/showcase/typescript/webmail/#/home",
                "value": ""
            }
        ],
        "resolution": "1911x950",
        "browser_version": "Chrome 84.0.4147.89"
    },
    {
        "id": 176,
        "project_id": 1,
        "report_uid": "12345",
        "name": "Essential JS 2 for TypeScript - Webmail",
        "session_id": "bdbf22b1d84826c8ebc524ee03c9cdc0",
        "identifier": "Essential JS 2 for TypeScript - Webmail:/showcase/typescript/webmail/@click(css selector=#tree li.e-level-2[data-uid='21'])",
        "type": "action",
        "bucket_name": "reports",
        "file_name": "Essential JS 2 for TypeScript - Webmail_b1abd3a7-dd20-44f1-9468-f1a6fb7df023.html",
        "thresholds_total": 0,
        "thresholds_failed": 0,
        "requests": 3,
        "domains": 2,
        "total": 5062,
        "speed_index": 872,
        "time_to_first_byte": 64,
        "time_to_first_paint": 0,
        "dom_content_loading": 1,
        "dom_processing": 0,
        "locators": [
            {
                "command": "open",
                "target": "https://ej2.syncfusion.com/showcase/typescript/webmail/#/home",
                "value": ""
            },
            {
                "command": "click",
                "target": "#tree li.e-level-2[data-uid='21']",
                "value": ""
            }
        ],
        "resolution": "1911x950",
        "browser_version": "Chrome 84.0.4147.89"
    },
    {
        "id": 179,
        "project_id": 1,
        "report_uid": "12345",
        "name": "Essential JS 2 for TypeScript - Webmail",
        "session_id": "bdbf22b1d84826c8ebc524ee03c9cdc0",
        "identifier": "Essential JS 2 for TypeScript - Webmail:/showcase/typescript/webmail/@click(css selector=li.e-level-1[data-uid='SF10208'])",
        "type": "action",
        "bucket_name": "reports",
        "file_name": "Essential JS 2 for TypeScript - Webmail_7897f546-e51c-4a6b-af24-49ebe9da1ede.html",
        "thresholds_total": 0,
        "thresholds_failed": 0,
        "requests": 1,
        "domains": 1,
        "total": 64,
        "speed_index": 1056,
        "time_to_first_byte": 63,
        "time_to_first_paint": 0,
        "dom_content_loading": 1,
        "dom_processing": 0,
        "locators": [
            {
                "command": "open",
                "target": "https://ej2.syncfusion.com/showcase/typescript/webmail/#/home",
                "value": ""
            },
            {
                "command": "click",
                "target": "#tree li.e-level-2[data-uid='21']",
                "value": ""
            },
            {
                "command": "click",
                "target": "li.e-level-1[data-uid='SF10208']",
                "value": ""
            }
        ],
        "resolution": "1911x950",
        "browser_version": "Chrome 84.0.4147.89"
    },
    {
        "id": 182,
        "project_id": 1,
        "report_uid": "12345",
        "name": "Essential JS 2 for TypeScript - Webmail",
        "session_id": "bdbf22b1d84826c8ebc524ee03c9cdc0",
        "identifier": "Essential JS 2 for TypeScript - Webmail:/showcase/typescript/webmail/@click(css selector=li.e-level-1[data-uid='SF10203'])",
        "type": "action",
        "bucket_name": "reports",
        "file_name": "Essential JS 2 for TypeScript - Webmail_3bb9b68c-7c7d-4046-99fa-eb602503ec6f.html",
        "thresholds_total": 0,
        "thresholds_failed": 0,
        "requests": 1,
        "domains": 1,
        "total": 22,
        "speed_index": 1189,
        "time_to_first_byte": 22,
        "time_to_first_paint": 0,
        "dom_content_loading": 1,
        "dom_processing": 0,
        "locators": [
            {
                "command": "open",
                "target": "https://ej2.syncfusion.com/showcase/typescript/webmail/#/home",
                "value": ""
            },
            {
                "command": "click",
                "target": "#tree li.e-level-2[data-uid='21']",
                "value": ""
            },
            {
                "command": "click",
                "target": "li.e-level-1[data-uid='SF10208']",
                "value": ""
            },
            {
                "command": "click",
                "target": "li.e-level-1[data-uid='SF10203']",
                "value": ""
            }
        ],
        "resolution": "1911x950",
        "browser_version": "Chrome 84.0.4147.89"
    },
    {
        "id": 175,
        "project_id": 1,
        "report_uid": "12345",
        "name": "Essential JS 2 for TypeScript - Webmail",
        "session_id": "faf3af520017b594f5deb69582aab612",
        "identifier": "Essential JS 2 for TypeScript - Webmail:/showcase/typescript/webmail/@faf3af520017b594f5deb69582aab612open(https://ej2.syncfusion.com/showcase/typescript/webmail/#/home)",
        "type": "page",
        "bucket_name": "reports",
        "file_name": "Essential JS 2 for TypeScript - Webmail_339c2a41-a04c-4ede-9ade-014588ab1471.html",
        "thresholds_total": 0,
        "thresholds_failed": 0,
        "requests": 35,
        "domains": 15,
        "total": 4178,
        "speed_index": 1111,
        "time_to_first_byte": 116,
        "time_to_first_paint": 1073,
        "dom_content_loading": 1005,
        "dom_processing": 2506,
        "locators": [
            {
                "command": "open",
                "target": "https://ej2.syncfusion.com/showcase/typescript/webmail/#/home",
                "value": ""
            }
        ],
        "resolution": "1911x950",
        "browser_version": "Chrome 84.0.4147.89"
    },
    {
        "id": 177,
        "project_id": 1,
        "report_uid": "12345",
        "name": "Essential JS 2 for TypeScript - Webmail",
        "session_id": "faf3af520017b594f5deb69582aab612",
        "identifier": "Essential JS 2 for TypeScript - Webmail:/showcase/typescript/webmail/@click(css selector=#tree li.e-level-2[data-uid='11'])",
        "type": "action",
        "bucket_name": "reports",
        "file_name": "Essential JS 2 for TypeScript - Webmail_0ad27951-d19c-4b0a-b9be-92016fba450f.html",
        "thresholds_total": 0,
        "thresholds_failed": 0,
        "requests": 2,
        "domains": 2,
        "total": 982,
        "speed_index": 1079,
        "time_to_first_byte": 21,
        "time_to_first_paint": 0,
        "dom_content_loading": 1,
        "dom_processing": 0,
        "locators": [
            {
                "command": "open",
                "target": "https://ej2.syncfusion.com/showcase/typescript/webmail/#/home",
                "value": ""
            },
            {
                "command": "click",
                "target": "#tree li.e-level-2[data-uid='11']",
                "value": ""
            }
        ],
        "resolution": "1911x950",
        "browser_version": "Chrome 84.0.4147.89"
    },
    {
        "id": 180,
        "project_id": 1,
        "report_uid": "12345",
        "name": "Essential JS 2 for TypeScript - Webmail",
        "session_id": "faf3af520017b594f5deb69582aab612",
        "identifier": "Essential JS 2 for TypeScript - Webmail:/showcase/typescript/webmail/@click(css selector=li.e-level-1[data-uid='SF10095'])",
        "type": "action",
        "bucket_name": "reports",
        "file_name": "Essential JS 2 for TypeScript - Webmail_759a66c8-5beb-40db-a355-b75e30747236.html",
        "thresholds_total": 0,
        "thresholds_failed": 0,
        "requests": 1,
        "domains": 1,
        "total": 54,
        "speed_index": 1351,
        "time_to_first_byte": 53,
        "time_to_first_paint": 0,
        "dom_content_loading": 1,
        "dom_processing": 0,
        "locators": [
            {
                "command": "open",
                "target": "https://ej2.syncfusion.com/showcase/typescript/webmail/#/home",
                "value": ""
            },
            {
                "command": "click",
                "target": "#tree li.e-level-2[data-uid='11']",
                "value": ""
            },
            {
                "command": "click",
                "target": "li.e-level-1[data-uid='SF10095']",
                "value": ""
            }
        ],
        "resolution": "1911x950",
        "browser_version": "Chrome 84.0.4147.89"
    }
]


def find_if_exists(curr_node, node_list):
    res = list(filter(lambda x: x['data']['identifier'] == curr_node['identifier'], node_list))
    if len(res) == 1:
        return res[0]
    if len(res) > 1:
        raise Exception("Bug! Node duplication")
    return None


def find_node(curr_node, node_list):
    if curr_node['data']['identifier'] == 'start_point':
        return curr_node

    res = list(filter(lambda x: x['data']['identifier'] == curr_node['data']['identifier'], node_list))
    if len(res) == 1:
        return res[0]
    if len(res) > 1:
        raise Exception("Bug! Node duplication")
    return None


def result_to_node(res):
    return {
        "data": {
            "id": res['id'],
            "name": res['name'],
            "session_id": res['session_id'],
            "identifier": res['identifier'],
            "type": res['type'],
            # "status": status,
            "result_id": res['id'],
            # "file": f"/api/v1/artifacts/{project_id}/reports/{result.file_name}"
        }
    }


def make_edge(node_from, node_to):
    return {
        "data": {
            "source": node_from['data']['id'],
            "target": node_to['data']['id']
            # "time": f"{round(threshold_result['time'] / 1000, 2)} sec"
        },
        # "classes": status
    }


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def get_flow(steps):
    flows = {}
    start = {"data": {"id": 'start', "name": 'Start', "identifier": "start_point"}}
    for step in steps:
        curr_session_id = step['session_id']
        if curr_session_id in flows.keys():
            flows[curr_session_id].append(result_to_node(step))
        else:
            flows[curr_session_id] = [start, result_to_node(step)]
    return flows


def get_nodes(steps):
    nodes = [
        {"data": {"id": 'start', "name": 'Start', "identifier": "start_point"}}
    ]
    for result in steps:
        current_node = find_if_exists(result, nodes)
        if not current_node:
            current_node = result_to_node(result)
            nodes.append(current_node)
    return nodes


edges = []
nodes = get_nodes(results)

flow = get_flow(results)

for session, steps in flow.items():
    print(session)
    for curr, upcoming in pairwise(steps):
        current_node = find_node(curr, nodes)
        upcoming_node = find_node(upcoming, nodes)
        print(f"{current_node['data']['id']} -> {upcoming_node['data']['id']}")
        edge = make_edge(current_node, upcoming_node)
        edges.append(edge)

pprint(nodes)

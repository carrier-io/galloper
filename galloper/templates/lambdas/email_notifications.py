import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
from data_manager import *
from report_builder import *


def email_notification(event):
    args = parse_args(event, 'api')
    comparison_metric = args['comparison_metric']
    user_list = args['user_list']
    smtp_config = {'host': args['smpt_host'],
                   'port': args['smpt_port'],
                   'user': args['smpt_user'],
                   'password': args['smpt_password']}

    tests_data = get_last_builds(args)
    if tests_data.__len__() == 0:
        print("No data found")
        return
    last_test_data = list(tests_data[0].get_points())
    last_test_data = append_thresholds_to_test_data(last_test_data, args)
    baseline = get_baseline(args)
    test_description = create_test_description(last_test_data, baseline, comparison_metric)
    builds_comparison = create_builds_comparison(tests_data)

    charts = create_charts(builds_comparison, last_test_data, baseline, comparison_metric)

    top_five_baseline = get_top_five_baseline(last_test_data, baseline, comparison_metric)

    top_five_thresholds = get_top_five_thresholds(last_test_data, comparison_metric)

    email_body = create_email_body(test_description, last_test_data, baseline, builds_comparison, top_five_baseline,
                                   top_five_thresholds)

    send_email(smtp_config, user_list, email_body, charts)


def send_email(smtp_config, user_list, email_body, charts):
    s = smtplib.SMTP_SSL(host=smtp_config['host'], port=int(smtp_config['port']))
    s.ehlo()
    s.login(smtp_config['user'], smtp_config['password'])

    for user in user_list:
        if all(i in user for i in ["<mailto:", "|"]):
            user = user.split("|")[1].replace(">", "").replace("<", "")
        msgRoot = MIMEMultipart('related')
        msgRoot['Subject'] = "Test notification"
        msgRoot['From'] = smtp_config['user']
        msgRoot['To'] = user
        msgAlternative = MIMEMultipart('alternative')
        msgAlternative.attach(MIMEText(email_body, 'html'))
        msgRoot.attach(msgAlternative)
        for chart in charts:
            msgRoot.attach(chart)
        s.sendmail(smtp_config['user'], user, msgRoot.as_string())
    s.quit()


def create_email_body(test_params, last_test_data, baseline, builds_comparison, top_five_baseline, top_five_thresholds):
    env = Environment(loader=FileSystemLoader('./templates/'))
    template = env.get_template("email_template.html")
    html = template.render(t_params=test_params, summary=last_test_data, baseline=baseline, comparison=builds_comparison,
                           top_five_baseline=top_five_baseline, top_five_thresholds=top_five_thresholds)
    return html


def create_ui_email_body(test_params, top_five_thresholds, builds_comparison, last_test_data):
    env = Environment(loader=FileSystemLoader('./templates/'))
    template = env.get_template("ui_email_template.html")
    html = template.render(t_params=test_params, top_five_thresholds=top_five_thresholds, comparison=builds_comparison,
                           summary=last_test_data)
    return html


def parse_args(event, test_type):
    args = {}
    if 'influx_port' in event.keys():
        args['influx_port'] = event['influx_port']
    else:
        args['influx_port'] = 8086

    if 'smpt_port' in event.keys():
        args['smpt_port'] = event['smpt_port']
    else:
        args['smpt_port'] = 465

    if 'smpt_host' in event.keys():
        args['smpt_host'] = event['smpt_host']
    else:
        args['smpt_host'] = 'smtp.gmail.com'

    if 'influx_thresholds_database' in event.keys():
        args['influx_thresholds_database'] = event['influx_thresholds_database']
    else:
        args['influx_thresholds_database'] = 'thresholds'

    if 'influx_ui_tests_database' in event.keys():
        args['influx_ui_tests_database'] = event['influx_ui_tests_database']
    else:
        args['influx_ui_tests_database'] = 'perfui'

    if 'influx_comparison_database' in event.keys():
        args['influx_comparison_database'] = event['influx_comparison_database']
    else:
        args['influx_comparison_database'] = 'comparison'

    if 'influx_user' in event.keys():
        args['influx_user'] = event['influx_user']
    else:
        args['influx_user'] = ''

    if 'influx_password' in event.keys():
        args['influx_password'] = event['influx_password']
    else:
        args['influx_password'] = ''

    if 'test_limit' in event.keys():
        args['test_limit'] = event['test_limit']
    else:
        args['test_limit'] = 5

    if 'comparison_metric' in event.keys():
        args['comparison_metric'] = event['comparison_metric']
    else:
        args['comparison_metric'] = 'pct95'

    args['smpt_user'] = event['smpt_user']
    args['smpt_password'] = event['smpt_password']
    args['influx_host'] = event['influx_host']
    args['users'] = event['users']
    args['user_list'] = event['user_list']
    if test_type is 'ui':
        args['ui_scenario'] = event['ui_scenario']
        args['ui_suite'] = event['ui_suite']
    if test_type is 'api':
        args['simulation'] = event['simulation']
        args['test_type'] = event['test_type']

    return args


def ui_email_notification(event):
    args = parse_args(event, 'ui')
    smtp_config = {'host': args['smpt_host'],
                   'port': args['smpt_port'],
                   'user': args['smpt_user'],
                   'password': args['smpt_password']}
    tests_data = get_ui_last_builds(args)
    if tests_data.__len__() == 0:
        print("No data found")
        return
    tests_data = aggregate_results(tests_data)
    last_test_data = tests_data[0]
    last_test_data = append_ui_thresholds_to_test_data(last_test_data, args)
    test_params = create_ui_test_discription(last_test_data)
    top_five_thresholds = get_top_five_thresholds(last_test_data, 'time')
    builds_comparison = create_ui_builds_comparison(tests_data)
    charts = create_ui_charts(last_test_data, builds_comparison)
    last_test_data = aggregate_last_test_results(last_test_data)
    email_body = create_ui_email_body(test_params, top_five_thresholds, builds_comparison, last_test_data)
    send_email(smtp_config, args['user_list'], email_body, charts)

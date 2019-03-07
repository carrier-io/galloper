import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
from data_manager import get_last_builds, get_baseline, append_thresholds_to_test_data
from report_builder import create_test_description, create_builds_comparison, create_charts, get_top_five_baseline,\
    get_top_five_thresholds


def email_notification(args):
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

    email_body = create_email_body(test_description, last_test_data, builds_comparison, top_five_baseline,
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


def create_email_body(test_params, last_test_data, builds_comparison, top_five_baseline, top_five_thresholds):
    env = Environment(loader=FileSystemLoader('./templates/'))
    template = env.get_template("email_template.html")
    html = template.render(t_params=test_params, summary=last_test_data, comparison=builds_comparison,
                           top_five_baseline=top_five_baseline, top_five_thresholds=top_five_thresholds)
    return html


# TODO how to pass parameters to script
def parse_args():
    args = {
        'simulation': 'test',
        'test_type': 'demo',
        'test_limit': 5,
        'users': 1,
        'comparison_metric': 'pct95',
        'user_list': [''],
        'influx_host': '',
        'influx_port': '8086',
        'influx_comparison_database': 'comparison',
        'influx_thresholds_database': 'thresholds',
        'influx_user': '',
        'influx_password': '',
        'smpt_user': '',
        'smpt_password': '',
        'smpt_port': 465,
        'smpt_host': 'smtp.gmail.com'
    }
    return args


if __name__ == "__main__":
    args = parse_args()
    email_notification(args)

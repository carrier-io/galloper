import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from data_manager import DataManager
from report_builder import ReportBuilder


class EmailNotification:
    def __init__(self, arguments):
        self.args = arguments
        self.data_manager = DataManager(arguments)
        self.report_builder = ReportBuilder()
        self.smtp_config = {'host': arguments['smpt_host'],
                            'port': arguments['smpt_port'],
                            'user': arguments['smpt_user'],
                            'password': arguments['smpt_password']}

    def email_notification(self):
        tests_data, last_test_data, baseline = self.data_manager.get_api_test_info()
        email_body, charts = self.report_builder.create_api_email_body(tests_data, last_test_data, baseline,
                                                                       self.args['comparison_metric'])
        self.send_email(self.smtp_config, self.args['user_list'], email_body, charts)

    def ui_email_notification(self):
        tests_data, last_test_data = self.data_manager.get_ui_test_info()
        email_body, charts = self.report_builder.create_ui_email_body(tests_data, last_test_data)
        self.send_email(self.smtp_config, self.args['user_list'], email_body, charts)

    @staticmethod
    def send_email(smtp_config, user_list, email_body, charts):
        s = smtplib.SMTP_SSL(host=smtp_config['host'], port=int(smtp_config['port']))
        s.ehlo()
        s.login(smtp_config['user'], smtp_config['password'])

        for user in user_list:
            if all(i in user for i in ["<mailto:", "|"]):
                user = user.split("|")[1].replace(">", "").replace("<", "")
            msg_root = MIMEMultipart('related')
            msg_root['Subject'] = "Test notification"
            msg_root['From'] = smtp_config['user']
            msg_root['To'] = user
            msg_alternative = MIMEMultipart('alternative')
            msg_alternative.attach(MIMEText(email_body, 'html'))
            msg_root.attach(msg_alternative)
            for chart in charts:
                msg_root.attach(chart)
            s.sendmail(smtp_config['user'], user, msg_root.as_string())
        s.quit()

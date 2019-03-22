from email_notifications import *


def ui_email_lambda_handler(event, context):
    try:
        ui_email_notification(event)
    except Exception as e:
        return e
    return "Email has been sent"


def email_lambda_handler(event, context):
    try:
        email_notification(event)
    except Exception as e:
        return e
    return "Email has been sent"


if __name__ == "__main__":
    print("main")
    #ui_email_notification()
    #email_notification()


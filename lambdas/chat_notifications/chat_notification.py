from api_data_manager import APIDataManager
from slack_notifications import SlackNotifications
from telegram_notifications import TelegramNotifications
from ms_teams_notifications import MSTeamsNotifications


class ChatNotification:
    def __init__(self, arguments):
        self.args = arguments
        self.notifications = dict(slack=SlackNotifications, telegram=TelegramNotifications,
                                  ms_teams=MSTeamsNotifications)

    def api_notifications(self):
        summary, last_test_data, previous_test = APIDataManager(self.args).prepare_api_test_data()
        self.notifications[self.args['chat']](self.args).api_notifications(summary, last_test_data,
                                                                           previous_test)

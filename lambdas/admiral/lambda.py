from os import environ
from nltk.stem.wordnet import WordNetLemmatizer
from slackclient import SlackClient
from utils import remove_noise



def message_processing(sc, message, lem):
    response = ''
    ts = message['ts']
    if 'thread_ts' in message:
        ts = message['thread_ts']
    if 'vision' in message['text'].lower():
        response = remove_noise(message['text'], lem)


def cleanup():
    pass


def main_slack():
    lem = WordNetLemmatizer()
    sc = SlackClient(environ.get('SLACK_TOKEN'))
    cleanup_interval = 3600
    cleanup_time = 0
    if sc.rtm_connect():
        for each in sc.rtm_read():
            print("Message received: %s" % each)
            if each['type'] == 'message':
                if 'message' in each and (isinstance(each['message'], dict)):
                    if each['subtype'] == 'message_changed':
                        message = each['message']
                        message['channel'] = each['channel']
                        message_processing(sc, message=message, lem=lem)
                elif 'user' in each and each['user'] != 'B9S4RQYJG' and 'bot_id' not in each:
                    message_processing(sc, message=each, lem=lem)
        cleanup_time += 1
        if cleanup_time >= cleanup_interval:
            cleanup()
            cleanup_time = 0
    else:
        print("Connection Failed")

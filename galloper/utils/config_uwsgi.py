from galloper.config import Config

uwsgi_conf = """
[uwsgi]
http-socket = {IP}:{port}
module = galloper.app:_app
processes = 1
threads = 1
master = true
"""

def main():
    config = Config()
    with open('/etc/uwsgi.ini', 'w') as f:
        f.write(uwsgi_conf.format(
            IP=config.APP_HOST,
            port=config.APP_PORT,
        ))
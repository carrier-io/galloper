from galloper.config import Config

uWSGI_CONF = """
[uwsgi]
http-socket = {host}:{port}
module = galloper.wsgi:app

master = true
processes = 2
threads = 4

vacuum = true
die-on-term = true
"""


def main():
    config = Config()
    with open("/etc/uwsgi.ini", "w") as f:
        f.write(uWSGI_CONF.format(
            host=config.APP_HOST,
            port=config.APP_PORT,
        ))

from requests import get
from os.path import join


class File:
    def __init__(self, url):
        self.url = url
        self.filename = url.split("/")[-1]

    def save(self, path):
        r = get(self.url, allow_redirects=True)
        open(path, 'wb').write(r.content)

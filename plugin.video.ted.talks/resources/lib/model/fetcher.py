import requests

class Fetcher:

    def __init__(self, logger):
        self.logger = logger

    def get(self, url):
        self.logger('GET {}'.format(url))

        r = requests.get(url)
        if r.ok:
            return r
        else:
            self.logger('%s\n%s\n%s'.format(r.status_code, r.headers, r.text))
            raise Exception('Failed to GET {}: {}'.format(url, r.status_code))


    def get_HTML(self, url):
        return self.get(url).text

import requests, json
from .utils import saveCookies, loadCookies, log


class LiveChannels:

    def __init__(self):
        self.LIST_URL = 'http://tpfeed.cbc.ca/f/ExhSPC/t_t3UKJR6MAT?pretty=true&sort=pubDate%7Cdesc'
        self.LIST_ELEMENT = 'entries'

        # Create requests session object
        self.session = requests.Session()
        session_cookies = loadCookies()
        if not session_cookies == None:
            self.session.cookies = session_cookies


    def getLiveChannels(self):
        r = self.session.get(self.LIST_URL)

        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None
        saveCookies(self.session.cookies)

        streams = []
        items = json.loads(r.content)[self.LIST_ELEMENT]
        return items

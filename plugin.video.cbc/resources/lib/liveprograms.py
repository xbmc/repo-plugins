import requests, json
from .utils import save_cookies, loadCookies, log


class LivePrograms:


    def __init__(self):
        self.LIST_URL = 'https://tpfeed.cbc.ca/f/ExhSPC/FNiv9xQx_BnT?q=id:*&pretty=true&sort=pubDate%7Cdesc'
        self.LIST_ELEMENT = 'entries'

        # Create requests session object
        self.session = requests.Session()
        session_cookies = loadCookies()
        if not session_cookies == None:
            self.session.cookies = session_cookies


    def getLivePrograms(self):
        r = self.session.get(self.LIST_URL)

        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None
        save_cookies(self.session.cookies)

        streams = []
        items = json.loads(r.content)[self.LIST_ELEMENT]
        return items

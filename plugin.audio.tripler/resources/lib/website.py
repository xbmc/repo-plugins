from resources.lib.scraper import USER_AGENT

from urllib.request import Request, build_opener, HTTPCookieProcessor
from urllib.parse import urlencode
from urllib.error import HTTPError

import http.cookiejar
import os

class TripleRWebsite():
    def __init__(self, cookiepath):
        self._cookiepath = cookiepath
        self.cj = http.cookiejar.LWPCookieJar()

    def _loadcj(self):
        if os.path.isfile(self._cookiepath):
            self.cj.load(self._cookiepath)
            return True
        else:
            return False

    def _delcj(self):
        self.cj = http.cookiejar.LWPCookieJar()
        try:
            os.remove(self._cookiepath)
        except:
            pass

    def request(self, url, data=None):
        if data:
            req = Request(url, data.encode())
        else:
            req = Request(url)
        req.add_header('User-Agent', USER_AGENT)

        opener = build_opener(HTTPCookieProcessor(self.cj))

        try:
            response = opener.open(req)
        except HTTPError as e:
            return e

        source = response.read().decode()
        response.close()

        return source

    def login(self, emailaddress, password):
        if password is None and self._loadcj():
            account_url = 'https://www.rrr.org.au/account'
            source = self.request(account_url)
            if self._check_login(source, emailaddress):
                return self.cj
            else:
                return False

        if emailaddress and password:
            login_url = 'https://www.rrr.org.au/sign-in'
            login_data = urlencode(
                {
                    'subscriber_account[email]': emailaddress,
                    'subscriber_account[password]': password,
                    '_csrf': ['', 'javascript-disabled'],
                }
            )

            source = self.request(login_url, data=login_data)

            if isinstance(source, HTTPError):
                return False

            if source and self._check_login(source, emailaddress):
                self.cj.save(self._cookiepath)
                return self.cj
        else:
            return False

    def _check_login(self, source, emailaddress):
        if emailaddress.lower() in source.lower():
            return True
        else:
            return False

    def logout(self):
        logout_url = 'https://www.rrr.org.au/sign-out'
        logout_data = urlencode(
            {
                '_csrf': ['', 'javascript-disabled'],
            }
        )
        source = self.request(logout_url, data=logout_data)
        if isinstance(source, HTTPError):
            if source.code == 500:
                return True
            else:
                return False
        if source:
            self._delcj()
            return True
        else:
            return False

    def logged_in(self):
        return self._loadcj()

    def subscribed(self):
        check_url = 'https://www.rrr.org.au/account/check-active.json'
        source = self.request(check_url)
        if isinstance(source, HTTPError):
            if source.code == 500:
                return True
            else:
                return False
        return self._check_subscription(source)

    def _check_subscription(self, source):
        if '"active":' in source and 'true' in source:
            return True
        else:
            return False

    def enter(self, resource_path):
        entry_url = ''.join(('https://www.rrr.org.au/subscriber-', resource_path[1:]))
        entry_data = urlencode(
            {
                'entry[null]': '',
                '_csrf': ['', 'javascript-disabled'],
            }
        )

        return self.request(entry_url, entry_data)

from resources.lib.rssaddon.http_status_error import HttpStatusError
from resources.lib.rssaddon.http_client import http_request
import base64

import xbmcaddon

class GPodder:

    _GPODDER_API = {
        "login": "%s/api/2/auth/%s/login.json",
        "subscriptions": "%s/subscriptions/%s.%s"
    }

    _addon = None
    _host = None
    _user = None

    def __init__(self, addon: xbmcaddon.Addon, host: str, user: str):

        self._addon = addon
        self._host = host
        self._user = user

    def login(self, password: str) -> str:
        auth_string = "%s:%s" % (self._user, password)
        b64auth = {
            "Authorization": "Basic %s" % base64.urlsafe_b64encode(auth_string.encode("utf-8")).decode("utf-8")
        }
        response, cookies = http_request(self._addon,
                                         self._GPODDER_API["login"] % (self._host,
                                                                       self._user), b64auth, "POST")

        if "sessionid" not in cookies:
            raise HttpStatusError("Invalid session. Check credentials")

        return cookies["sessionid"]

    def request_subscriptions(self, sessionid: str) -> str:

        session_cookie = {
            "Cookie": "%s=%s" % ("sessionid", sessionid)
        }
        response, cookies = http_request(self._addon,
                                         self._GPODDER_API["subscriptions"] % (self._host,
                                                                               self._user,
                                                                               "opml"), session_cookie)

        return response

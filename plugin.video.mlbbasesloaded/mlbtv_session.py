import os
import pickle
import time
from xbmcswift2 import xbmcaddon, xbmcgui
import requests
from globals import *
import sys

class MlbTvSession():
    def __init__(self):
        if not os.path.exists(COOKIE_PATH):
            self._login()
        cookies = self._load_cookies()
        if self._cookies_expired(cookies):
            self._login()

    def save_cookies(self, cookies):
        self._write_cookies(cookies)

    def get_cookies(self):
        cookies = self._load_cookies()
        if self._cookies_expired(cookies):
            self._login()
            cookies = self._load_cookies()
        return cookies

    def _cookies_expired(self, cookies):
        if not cookies:
            return False
        return time.time() >= max([c.expires for c in cookies])

    def _load_cookies(self):
        with open(COOKIE_PATH, 'rb') as f:
            return pickle.load(f)

    def _write_cookies(self, cookies):
        with open(COOKIE_PATH, 'wb') as f:
            pickle.dump(cookies, f)

    def _login(self):
        settings = xbmcaddon.Addon(id='plugin.video.mlbbasesloaded')
        username = str(settings.getSetting(id="username"))
        password = str(settings.getSetting(id="password"))
        if not username or not password:
            msg = "Please set your username and password in the settings"
            dialog = xbmcgui.Dialog()
            ok = dialog.ok('Invalid Login', msg)
            sys.exit()

        url = 'https://securea.mlb.com/authenticate.do'
        login_data = {'password': password, 'emailAddress': username, 'uri': '/account/login_register.jsp', 'registrationAction': 'identify'}
        headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
             "Accept-Encoding": "gzip, deflate",
             "Accept-Language": "en-US,en;q=0.8",
             "Content-Type": "application/x-www-form-urlencoded",
             "Origin": "https://securea.mlb.com",
             "Connection": "keep-alive",
             "Cookie": "SESSION_1=wf_forwardUrl%3D%3D%3Dhttp%3A%2F%2Fm.mlb.com%2Ftv%2Fe14-469412-2016-03-02%2Fv545147283%2F%3F%26media_type%3Dvideo%26clickOrigin%3DMedia%2520Grid%26team%3Dmlb%7Ewf_flowId%3D%3D%3Dregistration.dynaindex%7Ewf_template%3D%3D%3Dmp5default%7Ewf_mediaTypeTemplate%3D%3D%3Dvideo%7Estage%3D%3D%3D3%7EflowId%3D%3D%3Dregistration.dynaindex%7EforwardUrl%3D%3D%3Dhttp%3A%2F%2Fm.mlb.com%2Ftv%2Fe14-469412-2016-03-02%2Fv545147283%2F%3F%26media_type%3Dvideo%26clickOrigin%3DMedia%2520Grid%26team%3Dmlb%3B",
             "User-Agent": UA_PC}
        session = requests.Session()
        response = session.post(url, data=login_data, headers=headers)
        if response.url == url:
            msg = "Please check that your username and password are correct"
            dialog = xbmcgui.Dialog()
            ok = dialog.ok('Invalid Login', msg)
            sys.exit()
        else:
            xbmc.log("_login cookies response {0}".format(session.cookies))
            self._write_cookies(session.cookies)
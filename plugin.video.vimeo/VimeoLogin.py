'''
    Vimeo plugin for XBMC
    Copyright (C) 2010-2012 Tobias Ussing And Henrik Mosgaard Jensen

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import urllib
import re
import cookielib
try: import simplejson as json
except ImportError: import json
import urllib2

# ERRORCODES:
# 0 = Ignore
# 200 = OK
# 303 = See other (returned an error message)
# 500 = uncaught error


class VimeoLogin():
    def __init__(self):
        self.xbmc = sys.modules["__main__"].xbmc
        self.v = sys.modules["__main__"].client

        self.settings = sys.modules["__main__"].settings
        self.language = sys.modules["__main__"].language
        self.plugin = sys.modules["__main__"].plugin
        self.dbg = sys.modules["__main__"].dbg

        self.common = sys.modules["__main__"].common
        self.utils = sys.modules["__main__"].utils

    def login(self, params={}):
        self.common.log("")
        self.settings.openSettings()

        uname = self.settings.getSetting("user_email")
        if uname == "":
            return

        (result, status) = self._login()
        if (status == 200):
            self.utils.showMessage(self.language(30029), result)
            self.xbmc.executebuiltin("Container.Refresh")
        self.common.log("Done")

    def _login(self):
        self.common.log("")
        self.settings.setSetting("userid", "")
        self.settings.setSetting("oauth_token_secret", "")
        self.settings.setSetting("oauth_token", "")

        self.v.get_request_token()
        (result, status) = self.login_get_verifier(self.v.get_authorization_url("write"))

        if status != 200:
            return (result, status)
        
        self.v.set_verifier(result)

        token = str(self.v.get_access_token())
        self.common.log("login token: " + token)

        match = re.match('oauth_token_secret=(.*)&oauth_token=(.*)', token)

        if not match:
            self.common.log("login failed")
            return (self.language(30609), 303)

        self.settings.setSetting("oauth_token_secret", match.group(1))
        self.settings.setSetting("oauth_token", match.group(2))

        self.common.log("Done")
        return (self.language(30030), 200)

    def extractUserId(self, page):
        self.common.log("")
        userid = ""
        uid = self.common.parseDOM(page["content"], "li", attrs={"class": "me subnav"})
        if len(uid) > 0:
            uid = self.common.parseDOM(uid, "a", ret="href")
            userid = uid[0]
            userid = userid.replace("/user","")
            userid = userid.replace("/","")

        self.common.log("Done: " + repr(userid))
        return userid

    def extractCrossSiteScriptingToken(self):
        self.common.log("")
        result = self.common.fetchPage({"link": "https://vimeo.com/log_in"})

        xsrft = self.common.parseDOM(result["content"], "input",
                                     attrs={"id": "xsrft", "name": "token"},
                                     ret="value")

        if len(xsrft) == 0 and result["content"].find("xsrft:") > 0:
            xsrft = self.ExtractVersion6CrossSiteScriptingToken(result["content"])

        if len(xsrft) == 0:
            self.common.log("Failed to find cross site scripting token: " + repr(result))
        else:
            ck = cookielib.Cookie(version=0, name='xsrft', value=xsrft[0], port=None, port_specified=False, domain='.vimeo.com', domain_specified=True, domain_initial_dot=True, path='/', path_specified=True, secure=False, expires=None, discard=False, comment=None, comment_url=None, rest={}, rfc2109=False)
            sys.modules["__main__"].cookiejar.set_cookie(ck)

        self.common.log("Done: " + repr(xsrft))
        return xsrft

    def ExtractVersion6CrossSiteScriptingToken(self, html):
        self.common.log("")

        if html.find("xsrft:'") > 0:
            xsrft = html[html.find("xsrft:'") + len("xsrft:'"):]
            xsrft = xsrft[:xsrft.find("'")]
            xsrft = [xsrft]
            return xsrft

        if html.find("xsrft: '") > 0:
            xsrft = html[html.find("xsrft: '") + len("xsrft: '"):]
            xsrft = xsrft[:xsrft.find("'")]
            xsrft = [xsrft]
            return xsrft

        self.common.log("Done")
        return []

    def performHttpLogin(self, xsrft):
        self.common.log("")
        request = {'action': 'login',
                   'service': 'vimeo',
                   'email': self.settings.getSetting("user_email"),
                   'password': self.settings.getSetting("user_password"),
                   'token': xsrft}

        result = self.common.fetchPage({"link": "https://vimeo.com/log_in", "post_data": request,
                                "refering": "https://www.vimeo.com/log_in", "hide_post_data": True})

        self.common.log("Done")
        return result

    def checkIfHttpLoginFailed(self, page):
        self.common.log("")
        failure = self.common.parseDOM(page["content"], "body",  attrs={"class": "logged_out"})

        login_failed = ""
        if len(failure) > 0:
            login_failed = self.common.parseDOM(page["content"], "div",  attrs={"class": "validation-advice"})
            if len(login_failed) == 0:
                login_failed = "true"

        self.common.log("Done")
        return login_failed

    def extractLoginTokens(self, auth_url):
        self.common.log("")
        result = self.common.fetchPage({"link": auth_url})
        login_oauth_token = self.common.parseDOM(result["content"], "input", attrs={"type": "hidden", "name": "oauth_token"} , ret="value")
        login_token = self.common.parseDOM(result["content"], "input",  attrs={"type": "hidden", "id": "token", "name": "token"}, ret="value")

        self.common.log("Done: " + repr((login_oauth_token, login_token)))
        return login_oauth_token, login_token

    def authorizeAndExtractVerifier(self, login_token, login_oauth_token):
        self.common.log("")
        data = {'token': login_token,
                'oauth_token': login_oauth_token,
                'permission': 'write',
                'accept': 'Allow'}

        result = self.common.fetchPage({"link": "https://vimeo.com/oauth/confirmed", "post_data": data})
        verifier = self.common.getParameters(result["new_url"])
        self.common.log("Done")
        return verifier["oauth_verifier"]

    def login_get_verifier(self, auth_url):
        self.common.log("login_get_verifier - auth_url: " + auth_url)

        self.common.log("Part 1 httpLogin", 3)
        token = self.extractCrossSiteScriptingToken()
        login_page = self.performHttpLogin(token[0])
        login_failed = self.checkIfHttpLoginFailed(login_page)

        if len(login_failed) > 0:
            login_error = self.language(30621)
            if login_failed != "true":
                login_error = login_failed
                self.common.log("login failed - vimeo returned: " + repr(login_failed))

            self.common.log("login_get_verifier sanity check failed, bad username or password?")
            return (login_error, 303)

        userid = self.extractUserId(login_page)

        if not userid:
            self.common.log("login_get_verifier no userid in cookie jar login failed")
            return (self.language(30606), 303)

        self.common.log("Part 2 request user specific authorization token", 3)
        login_oauth_token, login_token = self.extractLoginTokens(auth_url)
        if len(login_oauth_token) == 0 or len(login_token) == 0:
            self.common.log("unable to find oauth tokens: login seems to have failed")
            return (self.language(30606), 303)

        self.common.log("Part 3 authorized the plugin and extract the verifier", 3)
        verifier = self.authorizeAndExtractVerifier(login_token[0], login_oauth_token[0])
        if len(verifier) == 0:
            self.common.log("failed to authorize plugin, unable to extract verifier: " + repr(verifier))
            return (self.language(30606), 303)

        self.common.log("setting userid: " + repr(userid), 3)
        self.settings.setSetting("userid", userid)

        self.common.log("Login success, got verifier: " + verifier, 3)
        return (verifier, 200)

    def _getAuth(self):
        self.common.log("")
        auth = self.settings.getSetting("oauth_token")
        self.common.log("authentication token: " + repr(auth), 1)

        if (auth):
            self.common.log("returning stored authentication token")
            return auth
        else:
            self.common.log("no authentication token found, requesting new token")
            (result, status) = self._login()

            if status == 200:
                self.common.log("returning new authentication token")
                return self.settings.getSetting("oauth_token")

        self.common.log("couldn't get new authentication token since login failed")
        return False

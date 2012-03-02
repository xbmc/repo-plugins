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
try: import simplejson as json
except ImportError: import json

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
        self.settings.openSettings()
        (result, status) = self._login()
        self.utils.showMessage(self.language(30029), result)
        self.xbmc.executebuiltin("Container.Refresh")

    def _login(self):
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

        self.common.log("login done")
        return (self.language(30030), 200)

    def extractUserIdFromCookieJar(self):
        self.common.log("")
        cookies = self.common.getCookieInfoAsHTML()
        userid = ""
        cookies = self.common.parseDOM(cookies, "cookie", attrs={"name": "uid"}, ret="value")
        if len(cookies) > 0:
            uid = urllib.unquote_plus(cookies[0])
            userid = uid.split("|")[0]

        return userid

    def extractCrossSiteScriptingToken(self):
        self.common.log("")
        result = self.common.fetchPage({"link": "http://vimeo.com/log_in"})

        xsrft = self.common.parseDOM(result["content"], "input",
                                     attrs={"type": "hidden", "id": "xsrft", "name": "token"},
                                     ret="value")
        return xsrft

    def performHttpLogin(self, xsrft):
        self.common.log("")
        request = {'sign_in[email]': self.settings.getSetting("user_email"),
                   'sign_in[password]': self.settings.getSetting("user_password"),
                   'token': xsrft}

        self.common.fetchPage({"link": "http://vimeo.com/log_in", "post_data": request,
                                "refering": "http://www.vimeo.com/log_in",
                                "cookie": "xsrft=" + xsrft})
        self.common.log("Done")

    def checkIfHttpLoginFailed(self):
        self.common.log("")
        result = self.common.fetchPage({"link": "http://vimeo.com/", "refering": "http://vimeo.com/log_in"})

        login_failed = result['content'].find("joinimage loggedout") > 0

        # We should check for this part on the web login to se if http fails and send the message back to the user
        # <div id="message" style="display:block;">
        #
        #    <div class="inner">
        #                    The email address and password you entered do not match.            </div>
        # </div>

        return login_failed

    def extractLoginTokens(self, auth_url):
        self.common.log("")
        result = self.common.fetchPage({"link": auth_url})

        login_oauth_token = self.common.parseDOM(result["content"], "input", attrs={"type": "hidden", "name": "oauth_token"} , ret="value")
        login_token = self.common.parseDOM(result["content"], "input",  attrs={"type": "hidden", "id": "xsrft", "name": "token"}, ret="value")

        return login_oauth_token, login_token

    def authorizeAndExtractVerifier(self, login_token, login_oauth_token):
        self.common.log("")
        data = {'token': login_token,
                'oauth_token': login_oauth_token,
                'permission': 'write',
                'accept': 'Allow'}

        result = self.common.fetchPage({"link": "http://vimeo.com/oauth/confirmed", "post_data": data})


        verifier = self.common.getParameters(result["new_url"])
        return verifier["oauth_verifier"]

    def login_get_verifier(self, auth_url):
        self.common.log("login_get_verifier - auth_url: " + auth_url)

        if self.settings.getSetting("accept") != "0":
            self.common.log("login failed accept disabled") # this is fucking retarded
            return (self.language(30606), 303)

        # part 1 httpLogin
        token = self.extractCrossSiteScriptingToken()
        self.performHttpLogin(token[0])
        login_failed = self.checkIfHttpLoginFailed()

        if (login_failed):
            self.common.log("login_get_verifier sanity check failed, bad username or password?")
            return (self.language(30621), 303)

        userid = self.extractUserIdFromCookieJar()

        if not userid:
            self.common.log("login_get_verifier no userid in cookie jar login failed")
            return (self.language(30606), 303)

        # part 2 request user specific authorization token
        login_oauth_token, login_token = self.extractLoginTokens(auth_url)

        if len(login_oauth_token) == 0 or len(login_token) == 0:
            self.common.log("unable to find oauth tokens: login seems to have failed")
            return (self.language(30606), 303)

        #part 3 authorized the plugin and extract the verifier
        verifier = self.authorizeAndExtractVerifier(login_token[0], login_oauth_token[0])
        if len(verifier) == 0:
            self.common.log("failed to authorize plugin, unable to extract verifier: " + repr(verifier))
            return (self.language(30606), 303)

        self.common.log("setting userid: " + repr(userid), 3)
        self.settings.setSetting("userid", userid)
        
        self.common.log("Login success, got verifier: " + verifier, 3)

        return (verifier, 200)

    def _getAuth(self):
        auth = self.settings.getSetting("oauth_token")
        self.common.log("authentication token: " + repr(auth), 5)

        if (auth):
            self.common.log("returning stored authentication token")
            return auth
        else:

            (result, status) = self._login()

            if status == 200:
                self.common.log("returning new authentication token")
                return self.settings.getSetting("oauth_token")

        self.common.log("couldn't get new authentication token since login failed")
        return False
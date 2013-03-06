'''
    YouTube plugin for XBMC
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

import re
import sys
import time
try: import simplejson as json
except ImportError: import json

# ERRORCODES:
# 0 = Ignore
# 200 = OK
# 303 = See other (returned an error message)
# 500 = uncaught error


class YouTubeLogin():
    APIKEY = "AI39si6hWF7uOkKh4B9OEAX-gK337xbwR9Vax-cdeF9CF9iNAcQftT8NVhEXaORRLHAmHxj6GjM-Prw04odK4FxACFfKkiH9lg"

    urls = {}
    urls[u"oauth_api_login"] = u"https://accounts.google.com/o/oauth2/auth?client_id=208795275779.apps.googleusercontent.com&redirect_uri=urn:ietf:wg:oauth:2.0:oob&scope=http%3A%2F%2Fgdata.youtube.com&response_type=code"

    def __init__(self):
        self.xbmc = sys.modules["__main__"].xbmc

        self.pluginsettings = sys.modules["__main__"].pluginsettings
        self.settings = sys.modules["__main__"].settings
        self.language = sys.modules["__main__"].language
        self.plugin = sys.modules["__main__"].plugin
        self.dbg = sys.modules["__main__"].dbg

        self.utils = sys.modules["__main__"].utils
        self.core = sys.modules["__main__"].core
        self.common = sys.modules["__main__"].common

    def login(self, params={}):
        get = params.get
        self.common.log("")

        old_user_name = self.pluginsettings.userName()
        old_user_password = self.pluginsettings.userPassword()
        self.settings.openSettings()

        user_name = self.pluginsettings.userName()
        user_password = self.pluginsettings.userPassword()

        self.dbg = self.pluginsettings.debugModeIsEnabled()
        result = ""
        status = 500

        if not user_name:
            return (result, 200)

        refreshed = False
        if get("new", "false") == "false" and self.pluginsettings.authenticationRefreshRoken and old_user_name == user_name and old_user_password == user_password:
            self.common.log("refreshing token: " + str(refreshed))
            refreshed = self.core._oRefreshToken()

        if not refreshed:
            result, status = self.authorize()

        self.xbmc.executebuiltin("Container.Refresh")
        return (result, status)

    def authorize(self):
        self.common.log("token not refresh, or new uname or password")
        self.settings.setSetting("oauth2_access_token", "")
        self.settings.setSetting("oauth2_refresh_token", "")
        self.settings.setSetting("oauth2_expires_at", "")
        (result, status) = self._httpLogin({"new": "true"})
        if status == 200:
            (result, status) = self._apiLogin()
        if status == 200:
            self.utils.showErrorMessage(self.language(30031), result, 303)
        else:
            self.utils.showErrorMessage(self.language(30609), result, status)
        return result, status

    def _apiLogin(self):
        self.common.log("")

        url = self.urls[u"oauth_api_login"]

        logged_in = False
        fetch_options = {"link": url, "no-language-cookie": "true"}
        step = 0
        self.common.log("Part A")
        while not logged_in and fetch_options and step < 6:
            self.common.log("Step : " + str(step))
            step += 1

            ret = self.core._fetchPage(fetch_options)
            fetch_options = False

            newurl = self.common.parseDOM(ret["content"], "form", attrs={"method": "POST"}, ret="action")
            state_wrapper = self.common.parseDOM(ret["content"], "input", attrs={"id": "state_wrapper"}, ret="value")

            if len(newurl) > 0 and len(state_wrapper) > 0:
                url_data = {"state_wrapper": state_wrapper[0],
                            "submit_access": "true"}

                fetch_options = {"link": newurl[0].replace("&amp;", "&"), "url_data": url_data, "no-language-cookie": "true"}
                self.common.log("Part B")
                continue

            code = self.common.parseDOM(ret["content"], "input", attrs={"id": "code"}, ret="value")
            if len(code) > 0:
                url = "https://accounts.google.com/o/oauth2/token"
                url_data = {"client_id": "208795275779.apps.googleusercontent.com",
                            "client_secret": "sZn1pllhAfyonULAWfoGKCfp",
                            "code": code[0],
                            "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
                            "grant_type": "authorization_code"}
                fetch_options = {"link": url, "url_data": url_data}
                self.common.log("Part C")
                continue

            # use token
            if ret["content"].find("access_token") > -1:
                self.common.log("Part D")
                oauth = json.loads(ret["content"])

                if len(oauth) > 0:
                    self.common.log("Part D " + repr(oauth["expires_in"]))
                    self.settings.setSetting("oauth2_expires_at", str(int(oauth["expires_in"]) + time.time()))
                    self.settings.setSetting("oauth2_access_token", oauth["access_token"])
                    self.settings.setSetting("oauth2_refresh_token", oauth["refresh_token"])

                    logged_in = True
                    self.common.log("Done:" + self.settings.getSetting("username"))

        if logged_in:
            return (self.language(30030), 200)
        else:
            self.common.log("Failed")
            return (self.language(30609), 303)

    def _httpLogin(self, params={}):
        get = params.get
        self.common.log("")
        status = 500

        if get("new", "false") == "true" or get("page", "false") != "false":
            self.settings.setSetting("login_info", "")
            self.settings.setSetting("SID", "")
            self.settings.setSetting("login_cookies", "")
        elif self.settings.getSetting("login_info") != "":
            self.common.log("returning existing login info: " + self.settings.getSetting("login_info"))
            return (self.settings.getSetting("login_info"), 200)

        fetch_options = {"link": get("link", "http://www.youtube.com/")}

        step = 0
        galx = ""
        ret = {}

        while fetch_options and step < 18:  # 6 steps for 2-factor login
            self.common.log("Step : " + str(step))
            step += 1

            if step == 17:
                return (self.core._findErrors(ret), 303)

            ret = self.core._fetchPage(fetch_options)

            if ret["content"].find(" captcha") > -1:
                self.common.log("Captcha needs to be filled")
                break
            fetch_options = False

            # Check if we are logged in.
            nick = self.common.parseDOM(ret["content"], "p", attrs={"class": "masthead-expanded-acct-sw-id2"})

            # Check if there are any errors to report
            errors = self.core._findErrors(ret, silent=True)
            if errors:
                if errors.find("cookie-clear-message-1") == -1 and (errors.find("The code you entered didn") == -1 or (errors.find("The code you entered didn") > -1 and step > 12)):
                    self.common.log("Returning error: " + repr(errors))
                    return (errors, 303)

            if len(nick) > 0 and nick[0] != "Sign In":
                self.common.log("Logged in. Parsing data: " + repr(nick))
                status = self._getLoginInfo(nick)
                return(ret, status)

            # Click login link on youtube.com
            newurl = self.common.parseDOM(ret["content"], "button", attrs={"href": ".*?ServiceLogin.*?"}, ret="href")
            if len(newurl) > 0:
                # Start login procedure
                if newurl[0] != "#":
                    fetch_options = {"link": newurl[0].replace("&amp;", "&"), "referer": ret["location"]}
                    self.common.log("Part A : " + repr(fetch_options))

            # Fill out login information and send.
            newurl = self.common.parseDOM(ret["content"].replace("\n", " "), "form", attrs={"id": "gaia_loginform"}, ret="action")
            if len(newurl) > 0:
                (galx, url_data) = self._fillLoginInfo(ret)
                if len(galx) > 0 and len(url_data) > 0:
                    fetch_options = {"link": newurl[0], "no-language-cookie": "true", "url_data": url_data, "hidden": "true", "referer": ret["location"]}
                    self.common.log("Part B")
                    self.common.log("fetch options: " + repr(fetch_options), 10)  # WARNING, SHOWS LOGIN INFO/PASSWORD
                    continue

            newurl = self.common.parseDOM(ret["content"], "meta", attrs={"http-equiv": "refresh"}, ret="content")
            if len(newurl) > 0:
                newurl = newurl[0].replace("&amp;", "&")
                newurl = newurl[newurl.find("&#39;") + 5:newurl.rfind("&#39;")]
                fetch_options = {"link": newurl, "no-language-cookie": "true", "referer": ret["location"]}
                self.common.log("Part C: "  + repr(fetch_options))
                continue

            ## 2-factor login start
            if ret["content"].find("smsUserPin") > -1:
                url_data = self._fillUserPin(ret["content"])
                if len(url_data) == 0:
                    return (False, 500)

                new_part = self.common.parseDOM(ret["content"], "form", attrs={"name": "verifyForm"}, ret="action")
                fetch_options = {"link": new_part[0], "url_data": url_data, "no-language-cookie": "true", "referer": ret["location"]}

                self.common.log("Part D: " + repr(fetch_options))
                continue

            smsToken = self.common.parseDOM(ret["content"].replace("\n", ""), "input", attrs={"name": "smsToken"}, ret="value")

            if len(smsToken) > 0 and galx != "":
                url_data = {"smsToken": smsToken[0],
                            "PersistentCookie": "yes",
                            "service": "youtube",
                            "GALX": galx}

                target_url = self.common.parseDOM(ret["content"], "form", attrs={"name": "hiddenpost"}, ret="action")
                fetch_options = {"link": target_url[0], "url_data": url_data, "no-language-cookie": "true", "referer": ret["location"]}
                self.common.log("Part E: " + repr(fetch_options))
                continue

            ## 2-factor login finish
            if not fetch_options:
                # Check for errors.
                return (self.core._findErrors(ret), 303)

        return (ret, status)

    def _fillLoginInfo(self, ret):
        content = ret["content"]
        rmShown = self.common.parseDOM(content, "input", attrs={"name": "rmShown"}, ret="value")
        cont = self.common.parseDOM(content, "input", attrs={"name": "continue"}, ret="value")
        uilel = self.common.parseDOM(content, "input", attrs={"name": "uilel"}, ret="value") # Deprecated?
        if len(uilel) == 0: # Deprecated?
            uilel = self.common.parseDOM(content, "input", attrs= {"id":"uilel"}, ret="value")
        if len(uilel) == 0 and ret["new_url"].find("uilel=") > -1:
            uilel = ret["new_url"][ret["new_url"].find("uilel=")+6]
            if uilel.find("&") > -1:
                uilel = uilel[:uilel.find("&")]
            uilel = [uilel]
        dsh = self.common.parseDOM(content, "input", attrs={"name": "dsh"}, ret="value")
        if len(dsh) == 0:
            dsh = self.common.parseDOM(content, "input", attrs={"id": "dsh"}, ret="value")

        galx = self.common.parseDOM(content, "input", attrs={"name": "GALX"}, ret="value")
        uname = self.pluginsettings.userName()
        pword = self.pluginsettings.userPassword()

        if pword == "":
            pword = self.common.getUserInput(self.language(30628), hidden=True)

        if len(galx) == 0 or len(cont) == 0 or len(uilel) == 0 or len(dsh) == 0 or len(rmShown) == 0 or uname == "" or pword == "":
            self.common.log("_fillLoginInfo missing values for login form " + repr(galx) + repr(cont) + repr(uilel) + repr(dsh) + repr(rmShown) + repr(uname) + str(len(pword)))
            return ("", {})
        else:
            galx = galx[0]
            url_data = {"pstMsg": "0",
                        "ltmpl": "sso",
                        "dnConn": "",
                        "continue": cont[0],
                        "service": "youtube",
                        "uilel": uilel[0],
                        "dsh": dsh[0],
                        "hl": "en_US",
                        "timeStmp": "",
                        "secTok": "",
                        "GALX": galx,
                        "Email": uname,
                        "Passwd": pword,
                        "PersistentCookie": "yes",
                        "rmShown": rmShown[0],
                        "signin": "Sign in",
                        "asts": ""
                        }
        return (galx, url_data)

    def _fillUserPin(self, content):
        self.common.log(repr(content), 5)
        smsToken = self.common.parseDOM(content, "input", attrs={"name": "smsToken"}, ret="value")
        self.smsToken = smsToken
        userpin = self.common.getUserInputNumbers(self.language(30627))

        if len(userpin) > 0:
            url_data = {"smsToken": smsToken[0],
                        "PersistentCookie": "yes",
                        "smsUserPin": userpin,
                        "smsVerifyPin": "Verify",
                        "timeStmp": "",
                        "secTok": ""}
            self.common.log("Done: " + repr(url_data))
            return url_data
        else:
            self.common.log("Replace this with a message telling users that they didn't enter a pin")
            return {}

    def _getLoginInfo(self, nick):
        self.common.log(nick)
        status = 303

        # Save cookiefile in settings
        cookies = self.common.getCookieInfoAsHTML()
        login_info = self.common.parseDOM(cookies, "cookie", attrs={"name": "LOGIN_INFO"}, ret="value")
        SID = self.common.parseDOM(cookies, "cookie", attrs={"name": "SID", "domain": ".youtube.com"}, ret="value")
        scookies = {}
        self.common.log("COOKIES:" + repr(cookies))
        tnames = re.compile(" name='(.*?)' ").findall(cookies)
        for key in tnames:
            tval = self.common.parseDOM(cookies, "cookie", attrs={"name": key}, ret="value")
            if len(tval) > 0:
                scookies[key] = tval[0]
        self.common.log("COOKIES:" + repr(scookies))

        if len(login_info) == 1:
            self.common.log("LOGIN_INFO: " + repr(login_info))
            self.settings.setSetting("login_info", login_info[0])
        else:
            self.common.log("Failed to get LOGIN_INFO from youtube: " + repr(login_info))

        if len(SID) == 1:
            self.common.log("SID: " + repr(SID))
            self.settings.setSetting("SID", SID[0])
        else:
            self.common.log("Failed to get SID from youtube: " + repr(SID))

        if len(SID) == 1 and len(login_info) == 1:
            status = 200
            self.settings.setSetting("login_cookies", repr(scookies))

        self.common.log("Done")
        return status

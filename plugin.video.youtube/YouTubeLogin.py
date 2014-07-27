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
        fetch_options = {"link": url}
        step = 0
        self.common.log("Go to the api login page")
        while not logged_in and fetch_options and step < 6:
            self.common.log("Step : " + str(step))
            step += 1

            ret = self.core._fetchPage(fetch_options)
            fetch_options = False

            for accounts in self.common.parseDOM(ret["content"], "ol", attrs={"id": "account-list"}):
                self.common.log("Detected google plus with page administrator.")
                acurl = self.common.parseDOM(accounts, "a", ret="href")
                acname = self.common.parseDOM(accounts, "span", attrs={"class": "account-name"})
                if len(acurl):
                    fetch_options = {"link": acurl[0].replace("&amp;", "&")}
                    continue

            newurl = self.common.parseDOM(ret["content"], "form", attrs={"method": "POST"}, ret="action")
            state_wrapper = self.common.parseDOM(ret["content"], "input", attrs={"id": "state_wrapper"}, ret="value")

            if len(newurl) > 0 and len(state_wrapper) > 0:
                url_data = {"state_wrapper": state_wrapper[0],
                            "submit_access": "true"}

                fetch_options = {"link": newurl[0].replace("&amp;", "&"), "url_data": url_data}
                self.common.log("Press 'Accept' button")
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
                self.common.log("Extract and use access code")
                continue

            # use token
            if ret["content"].find("access_token") > -1:
                self.common.log("Saving access_token")
                oauth = json.loads(ret["content"])

                if len(oauth) > 0:
                    self.settings.setSetting("oauth2_expires_at", str(int(oauth["expires_in"]) + time.time()))
                    self.settings.setSetting("oauth2_access_token", oauth["access_token"])
                    self.settings.setSetting("oauth2_refresh_token", oauth["refresh_token"])

                    logged_in = True
                    self.common.log("Done: " + self.settings.getSetting("username"))

        if logged_in:
            return (self.language(30030), 200)
        else:
            self.common.log("Failed")
            return (self.language(30609), 303)

    def _httpLogin(self, params={}):
        get = params.get
        self.common.log("")

        if get("new", "false") == "true" or get("page", "false") != "false":
            self.settings.setSetting("cookies_saved", "false")
        elif self.settings.getSetting("cookies_saved") == "true":
            self.common.log("Use saved cookies")
            return (self.settings.getSetting("cookies_saved"), 200)

        fetch_options = {"link": get("link", "http://www.youtube.com/"), "no-language-cookie": "true"}

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
            nick = self.common.parseDOM(ret["content"], "div", attrs={"class": "yt-masthead-picker-name"})

            if len(nick) > 0 and nick[0] != "Sign In":
                self.common.log("Logged in. Parsing data: " + repr(nick))
                sys.modules["__main__"].cookiejar.save()
                self.settings.setSetting("cookies_saved", "true")
                return(ret, 200)

            # Check if there are any errors to report
            errors = self.core._findErrors(ret, silent=True)
            if errors:
                if errors.find("cookie-clear-message-1") == -1 and (errors.find("The code you entered didn") == -1 or (errors.find("The code you entered didn") > -1 and step > 12)):
                    self.common.log("Returning error: " + repr(errors))
                    return (errors, 303)

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
                    fetch_options = {"link": newurl[0], "url_data": url_data, "hidden": "true", "referer": ret["location"]}
                    self.common.log("Part B")
                    self.common.log("fetch options: " + repr(fetch_options), 10)  # WARNING, SHOWS LOGIN INFO/PASSWORD
                    continue

            newurl = self.common.parseDOM(ret["content"], "meta", attrs={"http-equiv": "refresh"}, ret="content")
            if len(newurl) > 0:
                newurl = newurl[0].replace("&amp;", "&")
                newurl = newurl[newurl.find("&#39;") + 5:newurl.rfind("&#39;")]
                fetch_options = {"link": newurl, "referer": ret["location"]}
                self.common.log("Part C: "  + repr(fetch_options))
                continue

            ## 2-factor login start
            if ret["content"].find("smsUserPin") > -1:
                url_data = self._fillUserPin(ret["content"])
                if len(url_data) == 0:
                    return (False, 500)

                new_part = self.common.parseDOM(ret["content"], "form", attrs={"id": "gaia_secondfactorform"}, ret="action")
                t_url = ret["new_url"]
                t_url = t_url[:t_url.find("/", 10) + 1] + new_part[0].replace("&amp;", "&")
                fetch_options = {"link": t_url, "url_data": url_data, "referer": ret["new_url"]}

                self.common.log("Part D: " + repr(fetch_options))
                continue

            smsToken = self.common.parseDOM(ret["content"].replace("\n", ""), "input", attrs={"name": "smsToken"}, ret="value")

            if len(smsToken) > 0 and galx != "":
                url_data = {"smsToken": smsToken[0],
                            "PersistentCookie": "yes",
                            "service": "youtube",
                            "GALX": galx}

                target_url = self.common.parseDOM(ret["content"], "form", attrs={"name": "hiddenpost"}, ret="action")
                fetch_options = {"link": target_url[0], "url_data": url_data, "referer": ret["location"]}
                self.common.log("Part E: " + repr(fetch_options))
                continue

            ## 2-factor login finish
            if not fetch_options:
                # Check for errors.
                return (self.core._findErrors(ret), 303)

        return (ret, 500)

    def _fillLoginInfo(self, ret):
        self.common.log("")
        content = ret["content"]

        url_data = {}

        for name in self.common.parseDOM(content, "input", ret="name"):
            for val in self.common.parseDOM(content, "input", attrs={"name": name}, ret="value"):
                url_data[name] = self.common.makeAscii(val)

        self.common.log("Extracted url_data: " + repr(url_data), 0)
        url_data["Email"] = self.pluginsettings.userName()
        url_data["Passwd"] = self.pluginsettings.userPassword()
        if url_data["Passwd"] == "":
            url_data["Passwd"] = self.common.getUserInput(self.language(30628), hidden=True)

        self.common.log("Done")
        return (url_data["GALX"], url_data)

    def _fillUserPin(self, content):
        self.common.log("")
        #form = self.common.parseDOM(content, "form", attrs={"id": "gaia_secondfactorform"}, ret=True)
        form = self.common.parseDOM(content, "form", attrs={"id": "gaia_secondfactorform"}, ret=True)

        url_data = {}
        for name in self.common.parseDOM(form, "input", ret="name"):
            if name not in ["smsSend", "retry"]:
                #for val in self.common.parseDOM(form, "input", attrs={"name": name}, ret="value"):
                #    url_data[name] = self.common.makeAscii(val)
             if name not in ["smsSend", "retry"]:
                 for val in self.common.parseDOM(form, "input", attrs={"name": name}, ret="value"):
                     url_data[name] = self.common.makeAscii(val)
                

        self.common.log("url_data: " + repr(form), 0)

        if "smsToken" in url_data:
            self.smsToken = url_data["smsToken"]
        if "continue" in url_data:
            url_data["continue"] = url_data["continue"].replace("&amp;", "&")
        userpin = self.common.getUserInputNumbers(self.language(30627))

        if len(userpin) > 0:
            url_data["smsUserPin"] = userpin
            self.common.log("Done: " + repr(url_data))
            url_data["smsVerifyPin"] = "Verify" # Overwrite this variable since it might contain unicode.
            return url_data
        else:
            self.common.log("Error")
            return {}

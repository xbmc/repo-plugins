# -*- coding: utf-8 -*-
# Wakanim - Watch videos from the german anime platform Wakanim.tv on Kodi.
# Copyright (C) 2017 MrKrabat
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
from cgi import parse_header
from bs4 import BeautifulSoup
from time import timezone

PY3 = sys.version_info.major >= 3
if PY3:
    from urllib.parse import urlencode, quote_plus
    from urllib.request import urlopen, build_opener, HTTPCookieProcessor, install_opener
    from http.cookiejar import LWPCookieJar, Cookie
else:
    from urllib import urlencode, quote_plus
    from urllib2 import urlopen, build_opener, HTTPCookieProcessor, install_opener
    from cookielib import LWPCookieJar, Cookie

import xbmc
import xbmcgui


def start(args):
    """Login and session handler
    """
    # create cookiejar
    args._cj = LWPCookieJar()

    # lets urllib handle cookies
    opener = build_opener(HTTPCookieProcessor(args._cj))
    opener.addheaders = [("User-Agent",      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.62 Safari/537.36"),
                         ("Accept-Encoding", "identity"),
                         ("Accept-Charset",  "utf-8"),
                         ("DNT",             "1")]
    install_opener(opener)

    # load cookies
    try:
        args._cj.load(getCookiePath(args), ignore_discard=True)
    except IOError:
        # cookie file does not exist
        pass

    args._cj.set_cookie(Cookie(0, "timezoneoffset", str(timezone//60), None, False, "www.wakanim.tv", False, False, "/", True, False, None, False, None, None, {"HttpOnly": None}, False))


def close(args):
    """Saves cookies and session
    """
    if args._cj:
        args._cj.save(getCookiePath(args), ignore_discard=True)


def getPage(args, url, data=None):
    """Load HTML and login if necessary
    """
    # encode data
    if data:
        data = urlencode(data).encode("utf-8")

    # get page
    response = urlopen(url, data)
    html = getHTML(response)

    # check if loggedin
    if isLoggedin(html):
        return html

    # get account informations
    username = args._addon.getSetting("wakanim_username")
    password = args._addon.getSetting("wakanim_password")
    logindict = {"Username":   username,
                 "Password":   password,
                 "RememberMe": True,
                 "login":      "Verbindung"}

    # get security tokens
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find_all("form", {"class": "nav-user_login"})[0]
    for inputform in form.find_all("input", {"type": "hidden"}):
        if inputform.get("name") == u"RememberMe":
            continue
        logindict[inputform.get("name")] = inputform.get("value")

    # POST to login page
    post_data = urlencode(logindict)
    response = urlopen("https://www.wakanim.tv/" + args._country + "/v2/account/login?ReturnUrl=" + quote_plus(url.replace("https://www.wakanim.tv", "")),
                       post_data.encode(getCharset(response)))

    # get page again
    response = urlopen(url, data)
    html = getHTML(response)

    # 2FA required
    if u"/v2/client/authorizewebclient" in html:
        xbmc.log("[PLUGIN] %s: 2FA required" % args._addonname, xbmc.LOGNOTICE)
        soup = BeautifulSoup(html, "html.parser")
        RequestVerificationToken = soup.find("input", {"name": "__RequestVerificationToken"})["value"]

        # request 2FA email
        post_data = urlencode({"__RequestVerificationToken": RequestVerificationToken,
                               "method":                     "Email"})
        response = urlopen("https://www.wakanim.tv/" + args._country + "/v2/client/generatetokenwebclient",
                           post_data.encode(getCharset(response)))
        getHTML(response)

        # nuke session cookies and inform user
        xbmcgui.Dialog().ok(args._addonname, args._addon.getLocalizedString(30047))
        try:
            os.remove(getCookiePath(args))
        except WindowsError:
            pass
        args._cj = None
        return ""

    if isLoggedin(html):
        return html
    else:
        xbmc.log("[PLUGIN] %s: Login failed" % args._addonname, xbmc.LOGERROR)
        xbmcgui.Dialog().ok(args._addonname, args._addon.getLocalizedString(30040))
        return ""


def isLoggedin(html):
    """Check if user logged in
    """
    return u"header-main_user_name" in html


def getCookies(args):
    """Returns all cookies as string and urlencoded
    """
    ret = ""
    for cookie in args._cj:
        ret += urlencode({cookie.name: cookie.value}) + ";"

    return "|User-Agent=Mozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F67.0.3396.62%20Safari%2F537.36&Cookie=" + ret[:-1]


def getCookiePath(args):
    """Get cookie file path
    """
    profile_path = xbmc.translatePath(args._addon.getAddonInfo("profile"))
    if args.PY2:
        return os.path.join(profile_path.decode("utf-8"), u"cookies.lwp")
    else:
        return os.path.join(profile_path, "cookies.lwp")


def getCharset(response):
    """Get header charset
    """
    _, p = parse_header(response.headers.get("Content-Type", ""))
    return p.get("charset", "utf-8")


def getHTML(response):
    """Load HTML in unicode
    """
    return response.read().decode(getCharset(response))

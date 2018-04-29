# -*- coding: utf-8 -*-
# Watchbox
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

from os.path import join
from cgi import parse_header
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode
try:
    from urllib2 import urlopen, build_opener, HTTPCookieProcessor, install_opener
except ImportError:
    from urllib.request import urlopen, build_opener, HTTPCookieProcessor, install_opener
try:
    from cookielib import LWPCookieJar
except ImportError:
    from http.cookiejar import LWPCookieJar

import xbmc


def start(args):
    """Login and session handler
    """
    # create cookiejar
    args._cj = LWPCookieJar()

    # lets urllib handle cookies
    opener = build_opener(HTTPCookieProcessor(args._cj))
    opener.addheaders = [("User-Agent",      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"),
                         ("Accept-Encoding", "identity"),
                         ("Accept-Charset",  "utf-8")]
    install_opener(opener)

    # get account informations
    username = args._addon.getSetting("watchbox_username")
    password = args._addon.getSetting("watchbox_password")

    # load cookies
    try:
        args._cj.load(getCookiePath(args), ignore_discard=True)

        # check if session is valid
        html = getPage(args, "https://www.watchbox.de/profil/")
        if username in html:
            # session is valid
            return True

    except IOError:
        # cookie file does not exist
        pass

    # build POST data
    post_data = urlencode({"email":    username,
                           "password": password,
                           "lasturl":  "/"})

    # POST to login page
    response = urlopen("https://www.watchbox.de/login/", post_data.encode("utf-8"))
    html = response.read()

    # check for login string
    html = getPage(args, "https://www.watchbox.de/profil/")
    return username in html


def close(args):
    """Saves cookies and session
    """
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
    return html


def getCookies(args):
    """Returns all cookies as string and urlencoded
    """
    ret = ""
    if args._login:
        for cookie in args._cj:
            ret += urlencode({cookie.name: cookie.value}) + ";"

    return "|User-Agent=Mozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F60.0.3112.113%20Safari%2F537.36&Cookie=" + ret[:-1]


def getCookiePath(args):
    """Get cookie file path
    """
    profile_path = xbmc.translatePath(args._addon.getAddonInfo("profile"))
    if args.PY2:
        return join(profile_path.decode("utf-8"), u"cookies.lwp")
    else:
        return join(profile_path, "cookies.lwp")


def getCharset(response):
    """Get header charset
    """
    _, p = parse_header(response.headers.get("Content-Type", ""))
    return p.get("charset", "utf-8")


def getHTML(response):
    """Load HTML in unicode
    """
    return response.read().decode(getCharset(response))

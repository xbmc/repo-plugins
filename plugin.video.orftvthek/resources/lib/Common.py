#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
   Parsedom for XBMC plugins
   Copyright (C) 2010-2011 Tobias Ussing And Henrik Mosgaard Jensen

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
"""

from kodi_six.utils import py2_encode, py2_decode
from future.builtins import str
from future.builtins import range
import sys
import xbmc

PY3 = sys.version_info.major >=3
if PY3:
    from urllib.parse import unquote, urlencode
    from urllib.request import urlopen as OpenRequest
    from urllib.request import Request as HTTPRequest
    from urllib.error import HTTPError
    from html.parser import HTMLParser
    from html import unescape
else:
    from urllib import unquote, urlencode
    from urllib2 import urlopen as OpenRequest
    from urllib2 import Request as HTTPRequest
    from urllib2 import HTTPError
    from HTMLParser import HTMLParser
    parser = HTMLParser()
    unescape = parser.unescape

import re

USERAGENT = u"Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1"

def replaceHTMLCodes(txt):
    log(repr(txt))
    txt = re.sub('(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', txt)
    txt = unescape(txt)
    txt = txt.replace("&amp;", "&")
    log(repr(txt))
    return txt


def stripTags(html):
    log(repr(html))
    sub_start = html.find("<")
    sub_end = html.find(">")
    while sub_end > sub_start > -1:
        html = html.replace(html[sub_start:sub_end + 1], "").strip()
        sub_start = html.find("<")
        sub_end = html.find(">")

    log(repr(html))
    return html


def _getDOMContent(html, name, match, ret):  # Cleanup
    log("match: " + match)

    endstr = u"</" + name  # + ">"

    start = html.find(match)
    end = html.find(endstr, start)
    pos = html.find("<" + name, start + 1 )

    log(str(start) + " < " + str(end) + ", pos = " + str(pos) + ", endpos: " + str(end))

    while pos < end and pos != -1:  # Ignore too early </endstr> return
        tend = html.find(endstr, end + len(endstr))
        if tend != -1:
            end = tend
        pos = html.find("<" + name, pos + 1)
        log("loop: " + str(start) + " < " + str(end) + " pos = " + str(pos))

    log("start: %s, len: %s, end: %s" % (start, len(match), end))
    if start == -1 and end == -1:
        result = u""
    elif start > -1 and end > -1:
        result = html[start + len(match):end]
    elif end > -1:
        result = html[:end]
    elif start > -1:
        result = html[start + len(match):]

    if ret:
        endstr = html[end:html.find(">", html.find(endstr)) + 1]
        result = match + result + endstr

    log("done result length: " + str(len(result)))
    return result

def _getDOMAttributes(match, name, ret):
    lst = re.compile('<' + name + '.*?' + ret + '=([\'"].[^>]*?[\'"])>', re.M | re.S).findall(match)
    if len(lst) == 0:
        lst = re.compile('<' + name + '.*?' + ret + '=(.[^>]*?)>', re.M | re.S).findall(match)
    ret = []
    for tmp in lst:
        cont_char = tmp[0]
        if cont_char in "'\"":
            log("Using %s as quotation mark" % cont_char)

            # Limit down to next variable.
            if tmp.find('=' + cont_char, tmp.find(cont_char, 1)) > -1:
                tmp = tmp[:tmp.find('=' + cont_char, tmp.find(cont_char, 1))]

            # Limit to the last quotation mark
            if tmp.rfind(cont_char, 1) > -1:
                tmp = tmp[1:tmp.rfind(cont_char)]
        else:
            log("No quotation mark found")
            if tmp.find(" ") > 0:
                tmp = tmp[:tmp.find(" ")]
            elif tmp.find("/") > 0:
                tmp = tmp[:tmp.find("/")]
            elif tmp.find(">") > 0:
                tmp = tmp[:tmp.find(">")]

        ret.append(tmp.strip())

    log("Done: " + repr(ret))
    return ret

def _getDOMElements(item, name, attrs):
    lst = []
    for key in attrs:
        lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=[\'"]' + attrs[key] + '[\'"].*?>))', re.M | re.S).findall(item)
        if len(lst2) == 0 and attrs[key].find(" ") == -1:  # Try matching without quotation marks
            lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=' + attrs[key] + '.*?>))', re.M | re.S).findall(item)
        if len(lst) == 0:
            log("Setting main list " + repr(lst2))
            lst = lst2
            lst2 = []
        else:
            log("Setting new list " + repr(lst2))
            test = list(range(len(lst)))
            test.reverse()
            for i in test:  # Delete anything missing from the next list.
                if not lst[i] in lst2:
                    log("Purging mismatch " + str(len(lst)) + " - " + repr(lst[i]))
                    del(lst[i])

    if len(lst) == 0 and attrs == {}:
        log("No list found, trying to match on name only")
        lst = re.compile('(<' + name + '>)', re.M | re.S).findall(item)
        if len(lst) == 0:
            lst = re.compile('(<' + name + ' .*?>)', re.M | re.S).findall(item)

    log("Done: " + str(type(lst)))
    return lst


def parseDOM(html, name=u"", attrs={}, ret=False):
    log("Name: " + repr(name) + " - Attrs:" + repr(attrs) + " - Ret: " + repr(ret) + " - HTML: " + str(type(html)))
    ret = py2_decode(ret)
    if isinstance(name, str):
        try:
            name = name
        except:
            log("Couldn't decode name binary string: " + repr(name))

    if isinstance(html, str):
        try:
            html = [py2_decode(html)]
        except:
            log("Couldn't decode html binary string. Data length: " + repr(len(html)))
            html = [html]
    elif isinstance(html, bytes):
        html = [html.decode('ascii')]
    elif str(type(html)) == "<type 'unicode'>":
        html = [str(html)]
    elif not isinstance(html, list):
        log("Input isn't list or string/unicode.")
        return u""

    if not name.strip():
        log("Missing tag name")
        return u""

    ret_lst = []
    for item in html:
        temp_item = re.compile('(<[^>]*?\n[^>]*?>)').findall(item)
        for match in temp_item:
            item = item.replace(match, match.replace("\n", " "))

        lst = _getDOMElements(item, name, attrs)

        if isinstance(ret, str):
            log("Getting attribute %s content for %s matches " % (ret, len(lst)))
            lst2 = []
            for match in lst:
                lst2 += _getDOMAttributes(match, name, ret)
            lst = lst2
        else:
            log("Getting element content for %s matches " % len(lst))
            lst2 = []
            for match in lst:
                log("Getting element content for %s" % match)
                temp = _getDOMContent(item, name, match, ret).strip()
                item = item[item.find(temp, item.find(match)) + len(temp):]
                lst2.append(temp)
            lst = lst2
        ret_lst += lst

    log("Done: " + repr(ret_lst))
    return ret_lst

def fetchPage(params={}):
    get = params.get
    link = get("link")
    ret_obj = {}
    if get("post_data"):
        log("called for : " + repr(params['link']))
    else:
        log("called for : " + repr(params))

    if not link or int(get("error", "0")) > 2:
        log("giving up")
        ret_obj["status"] = 500
        return ret_obj

    if get("post_data"):
        if get("hide_post_data"):
            log("Posting data")
        else:
            log("Posting data: " + urlencode(get("post_data")))

        request = HTTPRequest(link, urlencode(get("post_data")))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    else:
        log("Got request")
        request = HTTPRequest(link)

    if get("headers"):
        for head in get("headers"):
            request.add_header(head[0], head[1])

    request.add_header('User-Agent', USERAGENT)

    if get("cookie"):
        request.add_header('Cookie', get("cookie"))

    if get("refering"):
        request.add_header('Referer', get("refering"))

    try:
        log("connecting to server...")

        con = OpenRequest(request)
        ret_obj["header"] = con.info()
        ret_obj["new_url"] = con.geturl()
        if get("no-content", "false") == u"false" or get("no-content", "false") == "false":
            inputdata = con.read()
            ret_obj["content"] = inputdata.decode("utf-8")

        con.close()

        log("Done")
        ret_obj["status"] = 200
        return ret_obj

    except HTTPError as e:
        err = str(e)
        log("HTTPError : " + err)
        log("HTTPError - Headers: " + str(e.headers) + " - Content: " + e.fp.read())

        params["error"] = str(int(get("error", "0")) + 1)
        ret = fetchPage(params)

        if not "content" in ret and e.fp:
            ret["content"] = e.fp.read()
            return ret

        ret_obj["status"] = 500
        return ret_obj

def log(msg):
    debug = False
    if debug:
        output = py2_encode(msg)
        xbmc.log(output, xbmc.LOGDEBUG)

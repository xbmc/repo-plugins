'''
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
'''

import sys
import urllib
import urllib2
import re
import io
import inspect
import time
import HTMLParser
#import chardet
import json

version = u"2.5.1"
plugin = u"CommonFunctions-" + version
print plugin

USERAGENT = u"Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1"

if hasattr(sys.modules["__main__"], "xbmc"):
    xbmc = sys.modules["__main__"].xbmc
else:
    import xbmc

if hasattr(sys.modules["__main__"], "xbmcgui"):
    xbmcgui = sys.modules["__main__"].xbmcgui
else:
    import xbmcgui

if hasattr(sys.modules["__main__"], "dbg"):
    dbg = sys.modules["__main__"].dbg
else:
    dbg = False

if hasattr(sys.modules["__main__"], "dbglevel"):
    dbglevel = sys.modules["__main__"].dbglevel
else:
    dbglevel = 3

if hasattr(sys.modules["__main__"], "opener"):
    urllib2.install_opener(sys.modules["__main__"].opener)


# This function raises a keyboard for user input
def getUserInput(title=u"Input", default=u"", hidden=False):
    log("", 5)
    result = None

    # Fix for when this functions is called with default=None
    if not default:
        default = u""

    keyboard = xbmc.Keyboard(default, title)
    keyboard.setHiddenInput(hidden)
    keyboard.doModal()

    if keyboard.isConfirmed():
        result = keyboard.getText()

    log(repr(result), 5)
    return result


# This function raises a keyboard numpad for user input
def getUserInputNumbers(title=u"Input", default=u""):
    log("", 5)
    result = None

    # Fix for when this functions is called with default=None
    if not default:
        default = u""

    keyboard = xbmcgui.Dialog()
    result = keyboard.numeric(0, title, default)

    log(repr(result), 5)
    return str(result)


def getXBMCVersion():
    log("", 3)
    version = xbmc.getInfoLabel( "System.BuildVersion" )
    log(version, 3)
    for key in ["-", " "]:
        if version.find(key) -1:
            version = version[:version.find(key)]
    version = float(version)
    log(repr(version))
    return version

# Converts the request url passed on by xbmc to the plugin into a dict of key-value pairs
def getParameters(parameterString):
    log("", 5)
    commands = {}
    if getXBMCVersion() >= 12.0:
        parameterString = urllib.unquote_plus(parameterString)
    splitCommands = parameterString[parameterString.find('?') + 1:].split('&')

    for command in splitCommands:
        if (len(command) > 0):
            splitCommand = command.split('=')
            key = splitCommand[0]
            try: 
                value = splitCommand[1].encode("utf-8")
            except:
                log("Error utf-8 encoding argument value: " + repr(splitCommand[1]))
                value = splitCommand[1]

            commands[key] = value

    log(repr(commands), 5)
    return commands


def replaceHTMLCodes(txt):
    log(repr(txt), 5)

    # Fix missing ; in &#<number>;
    txt = re.sub("(&#[0-9]+)([^;^0-9]+)", "\\1;\\2", makeUTF8(txt))

    txt = HTMLParser.HTMLParser().unescape(txt)
    txt = txt.replace("&amp;", "&")
    log(repr(txt), 5)
    return txt


def stripTags(html):
    log(repr(html), 5)
    sub_start = html.find("<")
    sub_end = html.find(">")
    while sub_start < sub_end and sub_start > -1:
        html = html.replace(html[sub_start:sub_end + 1], "").strip()
        sub_start = html.find("<")
        sub_end = html.find(">")

    log(repr(html), 5)
    return html


def _getDOMContent(html, name, match, ret):  # Cleanup
    log("match: " + match, 3)

    endstr = u"</" + name  # + ">"

    start = html.find(match)
    end = html.find(endstr, start)
    pos = html.find("<" + name, start + 1 )

    log(str(start) + " < " + str(end) + ", pos = " + str(pos) + ", endpos: " + str(end), 8)

    while pos < end and pos != -1:  # Ignore too early </endstr> return
        tend = html.find(endstr, end + len(endstr))
        if tend != -1:
            end = tend
        pos = html.find("<" + name, pos + 1)
        log("loop: " + str(start) + " < " + str(end) + " pos = " + str(pos), 8)

    log("start: %s, len: %s, end: %s" % (start, len(match), end), 3)
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

    log("done result length: " + str(len(result)), 3)
    return result

def _getDOMAttributes(match, name, ret):
    log("", 3)

    lst = re.compile('<' + name + '.*?' + ret + '=([\'"].[^>]*?[\'"])>', re.M | re.S).findall(match)
    if len(lst) == 0:
        lst = re.compile('<' + name + '.*?' + ret + '=(.[^>]*?)>', re.M | re.S).findall(match)
    ret = []
    for tmp in lst:
        cont_char = tmp[0]
        if cont_char in "'\"":
            log("Using %s as quotation mark" % cont_char, 3)

            # Limit down to next variable.
            if tmp.find('=' + cont_char, tmp.find(cont_char, 1)) > -1:
                tmp = tmp[:tmp.find('=' + cont_char, tmp.find(cont_char, 1))]

            # Limit to the last quotation mark
            if tmp.rfind(cont_char, 1) > -1:
                tmp = tmp[1:tmp.rfind(cont_char)]
        else:
            log("No quotation mark found", 3)
            if tmp.find(" ") > 0:
                tmp = tmp[:tmp.find(" ")]
            elif tmp.find("/") > 0:
                tmp = tmp[:tmp.find("/")]
            elif tmp.find(">") > 0:
                tmp = tmp[:tmp.find(">")]

        ret.append(tmp.strip())

    log("Done: " + repr(ret), 3)
    return ret

def _getDOMElements(item, name, attrs):
    log("", 3)

    lst = []
    for key in attrs:
        lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=[\'"]' + attrs[key] + '[\'"].*?>))', re.M | re.S).findall(item)
        if len(lst2) == 0 and attrs[key].find(" ") == -1:  # Try matching without quotation marks
            lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=' + attrs[key] + '.*?>))', re.M | re.S).findall(item)

        if len(lst) == 0:
            log("Setting main list " + repr(lst2), 5)
            lst = lst2
            lst2 = []
        else:
            log("Setting new list " + repr(lst2), 5)
            test = range(len(lst))
            test.reverse()
            for i in test:  # Delete anything missing from the next list.
                if not lst[i] in lst2:
                    log("Purging mismatch " + str(len(lst)) + " - " + repr(lst[i]), 3)
                    del(lst[i])

    if len(lst) == 0 and attrs == {}:
        log("No list found, trying to match on name only", 3)
        lst = re.compile('(<' + name + '>)', re.M | re.S).findall(item)
        if len(lst) == 0:
            lst = re.compile('(<' + name + ' .*?>)', re.M | re.S).findall(item)

    log("Done: " + str(type(lst)), 3)
    return lst

def parseDOM(html, name=u"", attrs={}, ret=False):
    log("Name: " + repr(name) + " - Attrs:" + repr(attrs) + " - Ret: " + repr(ret) + " - HTML: " + str(type(html)), 3)

    if isinstance(name, str): # Should be handled
        try:
            name = name #.decode("utf-8")
        except:
            log("Couldn't decode name binary string: " + repr(name))

    if isinstance(html, str):
        try:
            html = [html.decode("utf-8")] # Replace with chardet thingy
        except:
            log("Couldn't decode html binary string. Data length: " + repr(len(html)))
            html = [html]
    elif isinstance(html, unicode):
        html = [html]
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
            log("Getting attribute %s content for %s matches " % (ret, len(lst) ), 3)
            lst2 = []
            for match in lst:
                lst2 += _getDOMAttributes(match, name, ret)
            lst = lst2
        else:
            log("Getting element content for %s matches " % len(lst), 3)
            lst2 = []
            for match in lst:
                log("Getting element content for %s" % match, 4)
                temp = _getDOMContent(item, name, match, ret).strip()
                item = item[item.find(temp, item.find(match)) + len(temp):]
                lst2.append(temp)
            lst = lst2
        ret_lst += lst

    log("Done: " + repr(ret_lst), 3)
    return ret_lst


def extractJS(data, function=False, variable=False, match=False, evaluate=False, values=False):
    log("")
    scripts = parseDOM(data, "script")
    if len(scripts) == 0:
        log("Couldn't find any script tags. Assuming javascript file was given.")
        scripts = [data]

    lst = []
    log("Extracting", 4)
    for script in scripts:
        tmp_lst = []
        if function:
            tmp_lst = re.compile(function + '\(.*?\).*?;', re.M | re.S).findall(script)
        elif variable:
            tmp_lst = re.compile(variable + '[ ]+=.*?;', re.M | re.S).findall(script)            
        else:
            tmp_lst = [script]
        if len(tmp_lst) > 0:
            log("Found: " + repr(tmp_lst), 4)
            lst += tmp_lst
        else:
            log("Found nothing on: " + script, 4)

    test = range(0, len(lst))
    test.reverse()
    for i in test:
        if match and lst[i].find(match) == -1:
            log("Removing item: " + repr(lst[i]), 10)
            del lst[i]
        else:
            log("Cleaning item: " + repr(lst[i]), 4)
            if lst[i][0] == u"\n":
                lst[i] == lst[i][1:]
            if lst[i][len(lst) -1] == u"\n":
                lst[i] == lst[i][:len(lst)- 2]
            lst[i] = lst[i].strip()

    if values or evaluate:
        for i in range(0, len(lst)):
            log("Getting values %s" % lst[i])
            if function:
                if evaluate: # include the ( ) for evaluation
                    data = re.compile("(\(.*?\))", re.M | re.S).findall(lst[i])
                else:
                    data = re.compile("\((.*?)\)", re.M | re.S).findall(lst[i])
            elif variable:
                tlst = re.compile(variable +".*?=.*?;", re.M | re.S).findall(lst[i])
                data = []
                for tmp in tlst: # This breaks for some stuff. "ad_tag": "http://ad-emea.doubleclick.net/N4061/pfadx/com.ytpwatch.entertainment/main_563326'' # ends early, must end with } 
                    cont_char = tmp[0]
                    cont_char = tmp[tmp.find("=") + 1:].strip()
                    cont_char = cont_char[0]
                    if cont_char in "'\"":
                        log("Using %s as quotation mark" % cont_char, 1)
                        tmp = tmp[tmp.find(cont_char) + 1:tmp.rfind(cont_char)]
                    else:
                        log("No quotation mark found", 1)
                        tmp = tmp[tmp.find("=") + 1: tmp.rfind(";")]

                    tmp = tmp.strip()
                    if len(tmp) > 0:
                        data.append(tmp)
            else:
                log("ERROR: Don't know what to extract values from")

            log("Values extracted: %s" % repr(data))
            if len(data) > 0:
                lst[i] = data[0]

    if evaluate:
        for i in range(0, len(lst)):
            log("Evaluating %s" % lst[i])
            data = lst[i].strip()
            try:
                try:
                    lst[i] = json.loads(data)
                except:
                    log("Couldn't json.loads, trying eval")
                    lst[i] = eval(data)
            except:
                log("Couldn't eval: %s from %s" % (repr(data), repr(lst[i])))

    log("Done: " + str(len(lst)))
    return lst

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
            log("Posting data", 2)
        else:
            log("Posting data: " + urllib.urlencode(get("post_data")), 2)

        request = urllib2.Request(link, urllib.urlencode(get("post_data")))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    else:
        log("Got request", 2)
        request = urllib2.Request(link)

    if get("headers"):
        for head in get("headers"):
            request.add_header(head[0], head[1])

    request.add_header('User-Agent', USERAGENT)

    if get("cookie"):
        request.add_header('Cookie', get("cookie"))

    if get("refering"):
        request.add_header('Referer', get("refering"))

    try:
        log("connecting to server...", 1)

        con = urllib2.urlopen(request)
        ret_obj["header"] = con.info()
        ret_obj["new_url"] = con.geturl()
        if get("no-content", "false") == u"false" or get("no-content", "false") == "false":
            inputdata = con.read()
            #data_type = chardet.detect(inputdata)
            #inputdata = inputdata.decode(data_type["encoding"])
            ret_obj["content"] = inputdata.decode("utf-8")

        con.close()

        log("Done")
        ret_obj["status"] = 200
        return ret_obj

    except urllib2.HTTPError, e:
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

    except urllib2.URLError, e:
        err = str(e)
        log("URLError : " + err)

        time.sleep(3)
        params["error"] = str(int(get("error", "0")) + 1)
        ret_obj = fetchPage(params)
        return ret_obj


def getCookieInfoAsHTML():
    log("", 5)
    if hasattr(sys.modules["__main__"], "cookiejar"):
        cookiejar = sys.modules["__main__"].cookiejar

        cookie = repr(cookiejar)
        cookie = cookie.replace("<_LWPCookieJar.LWPCookieJar[", "")
        cookie = cookie.replace("), Cookie(version=0,", "></cookie><cookie ")
        cookie = cookie.replace(")]>", "></cookie>")
        cookie = cookie.replace("Cookie(version=0,", "<cookie ")
        cookie = cookie.replace(", ", " ")
        log(repr(cookie), 5)
        return cookie

    log("Found no cookie", 5)
    return ""


# This function implements a horrible hack related to python 2.4's terrible unicode handling.
def makeAscii(data):
    log(repr(data), 5)
    #if sys.hexversion >= 0x02050000:
    #        return data

    try:
        return data.encode('ascii', "ignore")
    except:
        log("Hit except on : " + repr(data))
        s = u""
        for i in data:
            try:
                i.encode("ascii", "ignore")
            except:
                log("Can't convert character", 4)
                continue
            else:
                s += i

        log(repr(s), 5)
        return s


# This function handles stupid utf handling in python.
def makeUTF8(data):
    log(repr(data), 5)
    return data
    try:
        return data.decode('utf8', 'xmlcharrefreplace') # was 'ignore'
    except:
        log("Hit except on : " + repr(data))
        s = u""
        for i in data:
            try:
                i.decode("utf8", "xmlcharrefreplace") 
            except:
                log("Can't convert character", 4)
                continue
            else:
                s += i
        log(repr(s), 5)
        return s


def openFile(filepath, options=u"r"):
    log(repr(filepath) + " - " + repr(options))
    if options.find("b") == -1:  # Toggle binary mode on failure
        alternate = options + u"b"
    else:
        alternate = options.replace(u"b", u"")

    try:
        log("Trying normal: %s" % options)
        return io.open(filepath, options)
    except:
        log("Fallback to binary: %s" % alternate)
        return io.open(filepath, alternate)


def log(description, level=0):
    if dbg and dbglevel > level:
        try:
            xbmc.log((u"[%s] %s : '%s'" % (plugin, inspect.stack()[1][3], description)).decode("utf-8"), xbmc.LOGNOTICE)
        except:
            xbmc.log(u"FALLBACK [%s] %s : '%s'" % (plugin, inspect.stack()[1][3], repr(description)), xbmc.LOGNOTICE)

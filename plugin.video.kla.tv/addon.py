# -*- coding: cp1252 -*-
import urllib, urllib2, re, xbmcplugin, xbmcgui, json
import xbmcaddon
import sys

# Set default encoding to 'UTF-8' instead of 'ascii'
reload(sys)
sys.setdefaultencoding("UTF8")

addon = xbmcaddon.Addon('plugin.video.kla.tv')
__language__ = addon.getLocalizedString
__icon__ = addon.getAddonInfo('icon')
__fanart__ = addon.getAddonInfo('fanart')

lang_setting = max([int(addon.getSetting('LanguageID') or 0) or 0, 0])

if lang_setting >= 30951:
	lang_setting -= 30951

exp_lang_codes = ['en', 'de', 'fr', 'pl']
payload_index = {
    "en": 2,
    "de": 1,
    "pl": 6,
    "fr": 3
}

if lang_setting == 0:
    lang_id = addon.getLocalizedString(id=30950)
else:
    lang_id = exp_lang_codes[lang_setting-1]

payload_id = payload_index.get(lang_id, 2)

# headers = ['User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3']
headers = [['User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0 SeaMonkey/2.46'],
           ['Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8']]


def INDEX(url):
    req = urllib2.Request(url)

    req.add_header(*headers[0])
    req.add_header('Accept', 'application/json, text/plain, */*')
    req.add_header('Content-Type', 'application/json;charset=utf-8')

    post_args = {"mode": "action",
                 "data":
                     {"type": "loadingNextVideos",
                      "offset": 0,
                      "count": 48,
                      "category": "",
                      "sendtyp": "",
                      "langid": str(payload_id)
                      }
                 }

    data = json.dumps(post_args)

    content = urllib2.urlopen(req, data=data).read()

    video_index = json.loads(content)

    data_digest = video_index.get('data', [])
    for video in data_digest:
        title = video.get('title', '')
        image = 'https://www.kla.tv/{}'.format(video.get('img', ''))
        url = "https://www.kla.tv/{}".format(video.get('longlink', '')).replace('lang=de', 'lang={}'.format(lang_id))
        if url == 'https://www.kla.tv/':
            continue
        addDir(title.encode('utf8'), url.encode('utf8'), 2, image)


def VIDEOLINKS(url, name):
    req = urllib2.Request(url)
    for header in headers:
        req.add_header(*header)

    response = urllib2.urlopen(req)

    link = response.read().replace('\n', '').replace('\t', ' ')
    while '  ' in link:
        link = link.replace('  ', ' ')
    response.close()

    compiled_regex = re.compile('file: "(.+?)", label: "(.+?)"')
    value_tuples = compiled_regex.findall(link)

    for entry in value_tuples:
        if "blockid" in entry[0].lower() or "label:" in entry[0].lower():
            continue
        addLink('{0} ({1})'.format(name, entry[1]), 'https://www.kla.tv/{}'.format(entry[0]), __icon__)


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param


def addLink(name, url, iconimage):
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


params = get_params()
url = None
name = None
mode = None

try:
    url = urllib.unquote_plus(params["url"])
except:
    pass
try:
    name = urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode = int(params["mode"])
except:
    pass

print "Mode: " + str(mode)
print "URL: " + str(url)
print "Name: " + str(name)

if mode == None or url == None or len(url) < 1:
    print ""
    INDEX('https://www.kla.tv/en')

elif mode == 1:
    print "" + url
    INDEX(url)

elif mode == 2:
    print "" + url
    VIDEOLINKS(url, name)

else:
    print "" + url
    INDEX('https://www.kla.tv/en')

xbmcplugin.endOfDirectory(int(sys.argv[1]))

# -*- coding: cp1252 -*-
import urllib, urllib2, re, xbmcplugin, xbmcgui, json
import xbmcaddon
import sys

from StringIO import StringIO
import gzip

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

exp_lang_codes = ['de', 'en', 'fr', 'nl', 'it', 'pl']
payload_index = {
    "de": 1,
    "en": 2,
    "fr": 3,
    "nl": 4,
    "it": 5,
    "pl": 6 
}

if lang_setting == 0:
    lang_id = addon.getLocalizedString(id=30950)
else:
    lang_id = exp_lang_codes[lang_setting-1]

payload_id = payload_index.get(lang_id, 2)


base_headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0 SeaMonkey/2.46",
    "Accept-Encoding": "gzip"
}

page_headers = base_headers.copy()
page_headers.update({
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
})

api_headers = base_headers.copy()
api_headers.update({
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=utf-8"
})


def decode_response(response):
    if response.info().get('Content-Encoding') == "gzip":
        buff = StringIO(response.read())
        f = gzip.GzipFile(fileobj=buff)
        return f.read()
    else:
        return response.read()


def INDEX(url):
    req = urllib2.Request(url, headers=api_headers)

    post_args = {"mode": "action",
                 "data":
                     {"type": "loadingNextVideos",
                      "offset": 0,
                      "count": 60,
                      "category": "",
                      "sendtyp": "",
                      "langid": str(payload_id)
                      }
                 }

    data = json.dumps(post_args)

    content = decode_response(urllib2.urlopen(req, data=data))

    video_index = json.loads(content)

    data_digest = video_index.get('data', [])
    for video in data_digest:
        title = video.get('title', '')
        image = 'https://www.kla.tv/{}'.format(video.get('img', ''))
        url = "https://www.kla.tv/{}".format(video.get('longlink', '')).replace('lang=de', 'lang={}'.format(lang_id))
        if url == 'https://www.kla.tv/':
            continue
        add_dir(title.encode('utf8'), url.encode('utf8'), 2, image)


def VIDEOLINKS(url, name):
    req = urllib2.Request(url, headers=page_headers)

    response = urllib2.urlopen(req)

    link = decode_response(response).replace('\n', '').replace('\t', ' ')
    while '  ' in link:
        link = link.replace('  ', ' ')
    response.close()

    compiled_regex = re.compile('"src": "(.+?)", "label": "(.+?)"')
    value_tuples = compiled_regex.findall(link)

    for entry in value_tuples:
        if "blockid" in entry[0].lower() or "label:" in entry[0].lower():
            continue
        add_link('{0} ({1})'.format(name, entry[1]), 'https://www.kla.tv/{}'.format(entry[0]), __icon__)


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
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param


def add_link(name, url, icon_image):
    liz = xbmcgui.ListItem(name)
    liz.setArt({"thumb": icon_image})
    liz.setInfo(type="Video", infoLabels={"title": name, "mediatype": "video"})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz)
    return ok


def add_dir(name, url, mode, icon_image):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
    liz = xbmcgui.ListItem(name)
    liz.setInfo(type="Video", infoLabels={"title": name, "mediatype": "video"})
    liz.setArt({"thumb": icon_image})
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


if mode == None or url == None or len(url) < 1:
    INDEX('https://www.kla.tv/en')

elif mode == 1:
    INDEX(url)

elif mode == 2:
    VIDEOLINKS(url, name)

else:
    INDEX('https://www.kla.tv/en')

xbmcplugin.endOfDirectory(int(sys.argv[1]))

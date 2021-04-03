# -*- coding: utf-8 -*-
import routing
import logging
import requests
from bs4 import BeautifulSoup
import re
import xbmcaddon
from sys import exit
from resources.lib import kodiutils
from resources.lib import kodilogging
from xbmcgui import ListItem, Dialog, INPUT_ALPHANUM
from xbmcplugin import addDirectoryItem, endOfDirectory, setResolvedUrl

if kodiutils.PY3:
    from urllib.parse import urlencode
    from html.parser import HTMLParser
else:
    from urllib import urlencode
    from HTMLParser import HTMLParser


ADDON = xbmcaddon.Addon()
ICON = ADDON.getAddonInfo("icon")
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()

HEADERS_VOD = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Mobile Safari/537.36",
    "Cookie": "rtp_cookie_privacy=permit 1,2,3,4;"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36",
    "Referer": "https://www.rtp.pt/",
}


@plugin.route('/')
def index():
    direto = ListItem("[B]{}[/B]".format(kodiutils.get_string(32004)))
    addDirectoryItem(handle=plugin.handle, listitem=direto, isFolder=True, url=plugin.url_for(live))

    programas = ListItem("[B]{}[/B]".format(kodiutils.get_string(32005)))
    addDirectoryItem(handle=plugin.handle, listitem=programas, isFolder=True, url=plugin.url_for(programs))

    estudoemcasaitem = ListItem("[B]{}[/B]".format(kodiutils.get_string(32010)))
    addDirectoryItem(handle=plugin.handle, listitem=estudoemcasaitem, isFolder=True, url=plugin.url_for(estudoemcasa))

    pesquisar = ListItem("[B]{}[/B]".format(kodiutils.get_string(32006)))
    addDirectoryItem(handle=plugin.handle, listitem=pesquisar, isFolder=True, url=plugin.url_for(search))

    endOfDirectory(plugin.handle)


@plugin.route('/search')
def search():

    input_text = Dialog().input(kodiutils.get_string(32007), "", INPUT_ALPHANUM)

    try:
        req = requests.get("https://www.rtp.pt/play/pesquisa?q={}".format(input_text), headers=HEADERS_VOD).text
    except:
        raise_notification()
        return

    pagei = ListItem("{} [B]{}[/B]".format(kodiutils.get_string(32008), input_text))
    addDirectoryItem(handle=plugin.handle, listitem=pagei, isFolder=False, url="")

    soup = BeautifulSoup(req, 'html.parser')

    for a in soup.find('section').find_all('a'):
        url = a.get('href')
        title = a.get('title')
        img = a.find('img').get('src')
        metas = a.find_next_sibling('i').find_all('meta')
        description = metas[1].get('content')

        liz = ListItem("{}".format(kodiutils.compat_py23str(title)))
        liz.setArt({"thumb": img,
                    "icon": img,
                    "fanart": kodiutils.FANART})
        liz.setInfo("Video", infoLabels={"plot": kodiutils.strip_html_tags(kodiutils.compat_py23str(description)), "title": kodiutils.compat_py23str(title)})

        addDirectoryItem(
            plugin.handle,
            plugin.url_for(
                programs_episodes,
                title=kodiutils.compat_py23str(title),
                ep=kodiutils.compat_py23str(title),
                img=kodiutils.compat_py23str(img),
                description=kodiutils.compat_py23str(description),
                url=kodiutils.compat_py23str(url),
                page=1
            ), liz, True)
    endOfDirectory(plugin.handle)


@plugin.route('/live')
def live():
    # Request dvr
    try:
        req = requests.get("http://www.rtp.pt/play/direto", headers=HEADERS).text
    except:
        raise_notification()
        return

    match = re.compile(r'<a.+?title=".+? - (.+?)" href="/play/(.+?)".*?\n.*?\n.*?<img alt="(.+?)" src="(.+?)".*?\n.*?\n.*?width:(.+?)%').findall(req)

    for prog, key, emissao, img, percent in match:
        dvr = prog
        if img.startswith("/"):
            img = "http:{}".format(img)
        progimg = img
        progpercent = percent
        prefix = "em direto"
        name = emissao[emissao.index(prefix) + len(prefix):].strip() if prefix in emissao else emissao

        liz = ListItem("[B][COLOR blue]{}[/COLOR][/B] ({}) [B]{}%[/B]".format(
            kodiutils.compat_py23str(name),
            kodiutils.strip_html_tags(kodiutils.compat_py23str(dvr)),
            kodiutils.compat_py23str(progpercent))
        )
        liz.setArt({"thumb": progimg,
                    "icon": progimg,
                    "fanart": kodiutils.FANART})
        liz.setProperty('IsPlayable', 'true')
        liz.setInfo("Video", infoLabels={"plot": kodiutils.strip_html_tags(kodiutils.compat_py23str(dvr))})
        addDirectoryItem(
            plugin.handle,
            plugin.url_for(
                live_play,
                label=kodiutils.compat_py23str(name),
                channel=kodiutils.compat_py23str(key.lower()),
                img=kodiutils.compat_py23str(progimg),
                prog=kodiutils.compat_py23str(dvr)
            ), liz, False)

    endOfDirectory(plugin.handle)


@plugin.route('/live/play')
def live_play():
    channel = plugin.args["channel"][0]
    name = plugin.args["label"][0]
    prog = plugin.args["prog"][0]

    icon = ICON
    if "img" in plugin.args:
        icon = plugin.args["img"][0]

    try:
        req = requests.get("https://www.rtp.pt/play/" + channel, headers=HEADERS)
        req.encoding = "latin-1"
        stream = kodiutils.find_stream_url(req.text)
    except:
        raise_notification()
        return

    liz = ListItem("[COLOR blue][B]{}[/B][/COLOR] ({})".format(
        kodiutils.compat_py23str(name),
        kodiutils.compat_py23str(prog))
    )
    liz.setArt({"thumb": icon, "icon": icon})
    liz.setProperty('IsPlayable', 'true')
    liz.setPath("{}|{}".format(stream, urlencode(HEADERS)))
    setResolvedUrl(plugin.handle, True, liz)


@plugin.route('/programs')
def programs():
    try:
        req = requests.get("http://www.rtp.pt/play/programas", headers=HEADERS)
        req.encoding = "latin-1"
        req = req.text
    except:
        raise_notification()
        return

    match = re.compile(r'<div class="meta-data"><h4>(.+?)</h4>').findall(req)

    i = 0
    for name in match:
        name = HTMLParser().unescape(kodiutils.compat_py23str(name))
        name = name.encode('utf8', 'replace')
        liz = ListItem(name)
        addDirectoryItem(handle=plugin.handle, listitem=liz, isFolder=True, url=plugin.url_for(programs_category, name=name, id=i, page=1))
        i = i + 1

    endOfDirectory(plugin.handle)


@plugin.route('/programs/category')
def programs_category():
    page = plugin.args["page"][0]
    cat_id = plugin.args["id"][0]
    cat_name = plugin.args["name"][0]

    try:
        req = requests.get("https://www.rtp.pt/play/bg_l_pg/?listcategory={}&page={}".format(
            cat_id,
            page), headers=HEADERS_VOD)
        req.encoding = "latin-1"
        req = req.text
    except:
        raise_notification()
        return

    pagei = ListItem("[B]{}[/B] - {} {}".format(kodiutils.compat_py23str(cat_name), kodiutils.get_string(32009), page))
    pagei.setProperty('IsPlayable', 'false')
    addDirectoryItem(handle=plugin.handle, listitem=pagei, isFolder=False, url="")

    soup = BeautifulSoup(req, 'html.parser')

    for a in soup.find_all('a'):
        url = a.get('href')
        title = a.get('title')
        img = a.find('img').get('src')
        metas = a.find_next_sibling('i').find_all('meta')
        description = metas[1].get('content')
        ep = metas[0].get('content')[-12:]

        liz = ListItem("{} ({})".format(
            kodiutils.compat_py23str(title),
            kodiutils.compat_py23str(ep))
        )
        liz.setArt({"thumb": img,
                    "icon": img,
                    "fanart": kodiutils.FANART})
        liz.setInfo("Video", infoLabels={"plot": kodiutils.strip_html_tags(kodiutils.compat_py23str(description)), "title": kodiutils.compat_py23str(title)})

        addDirectoryItem(
            plugin.handle,
            plugin.url_for(
                programs_episodes,
                title=kodiutils.compat_py23str(title),
                ep=kodiutils.compat_py23str(ep),
                img=img,
                description=kodiutils.compat_py23str(description),
                url=kodiutils.compat_py23str(url),
                page=1
            ), liz, True)

    newpage = str(int(page) + 1)
    nextpage = ListItem("[B]{}[/B] - {} {} >>>".format(kodiutils.compat_py23str(cat_name), kodiutils.get_string(32009), newpage))
    addDirectoryItem(handle=plugin.handle, listitem=nextpage, isFolder=True, url=plugin.url_for(programs_category, name=kodiutils.compat_py23str(cat_name), id=cat_id, page=newpage))

    endOfDirectory(plugin.handle)


@plugin.route('/programs/episodes')
def programs_episodes():
    title = plugin.args["title"][0]
    ep = plugin.args["ep"][0]
    img = plugin.args["img"][0]
    url = plugin.args["url"][0]
    page = plugin.args["page"][0]

    if url.find("estudoemcasa") >= 0:
        prog_id = url.split("/")[3][1:]
        mainurl = "https://www.rtp.pt/play/estudoemcasa"
    else:
        prog_id = url.split("/")[2][1:]
        mainurl = "https://www.rtp.pt/play"

    try:
        req = requests.get("{}/bg_l_ep/?listProgram={}&page={}".format(
            mainurl,
            prog_id,
            page), headers=HEADERS_VOD)
        req.encoding = "latin-1"
        req = req.text
    except:
        raise_notification()
        return

    pagei = ListItem("[B]{}[/B] - {} {}".format(kodiutils.compat_py23str(title), kodiutils.get_string(32009), page))
    pagei.setProperty('IsPlayable', 'false')
    addDirectoryItem(handle=plugin.handle, listitem=pagei, isFolder=False, url="")

    soup = BeautifulSoup(req, 'html.parser')

    for a in soup.find_all('a'):
        url = a.get('href')
        if a.find('script') != None:
            match = re.search(r'\'(.+?)\'', str(a.find('script')))
            if len(match.groups()) > 0:
                img = match.group(1)
        metas = a.find_next_sibling('i').find_all('meta')
        description = metas[1].get('content')
        ep = metas[0].get('content')

        liz = ListItem(ep)
        liz.setArt({"thumb": img,
                    "icon": img,
                    "fanart": kodiutils.FANART})
        liz.setInfo("Video", infoLabels={"plot": kodiutils.strip_html_tags(kodiutils.compat_py23str(description)) + "...", "title": kodiutils.compat_py23str(ep)})
        liz.setProperty('IsPlayable', 'true')

        addDirectoryItem(
            plugin.handle,
            plugin.url_for(
                programs_play,
                title=kodiutils.compat_py23str(title),
                ep=kodiutils.compat_py23str(ep),
                img=kodiutils.compat_py23str(img),
                description=kodiutils.compat_py23str(description),
                url=kodiutils.compat_py23str(url)
            ), liz, False)

    newpage = str(int(page) + 1)
    nextpage = ListItem("[B]{}[/B] - {} {} >>>".format(kodiutils.compat_py23str(title), kodiutils.get_string(32009), newpage))
    addDirectoryItem(handle=plugin.handle,
        listitem=nextpage,
        isFolder=True,
        url=plugin.url_for(programs_episodes,
            title=kodiutils.compat_py23str(title),
            ep=kodiutils.compat_py23str(ep),
            img=kodiutils.compat_py23str(img),
            url=kodiutils.compat_py23str(url),
            page=newpage))

    endOfDirectory(plugin.handle)


@plugin.route('/programs/play')
def programs_play():
    title = plugin.args["title"][0]
    ep = plugin.args["ep"][0]
    img = plugin.args["img"][0]
    url = plugin.args["url"][0]

    try:
        req = requests.get("https://www.rtp.pt" + url, headers=HEADERS)
        req.encoding = "latin-1"
        stream = kodiutils.find_stream_url(req.text)
    except:
        raise_notification()
        return

    liz = ListItem("{} ({})".format(
        kodiutils.compat_py23str(title),
        kodiutils.compat_py23str(ep))
    )
    liz.setArt({"thumb": img, "icon": img})
    liz.setProperty('IsPlayable', 'true')
    liz.setPath("{}|{}".format(stream, urlencode(HEADERS)))

    subtitles = kodiutils.find_subtitles(req.text)
    if subtitles:
        liz.setSubtitles([subtitles])

    setResolvedUrl(plugin.handle, True, liz)


@plugin.route('/estudoemcasa')
def estudoemcasa():
    try:
        req = requests.get("https://www.rtp.pt/play/estudoemcasa/", headers=HEADERS)
        req.encoding = "latin-1"
        req = req.text
    except:
        raise_notification()
        return

    soup = BeautifulSoup(req, 'html.parser')

    for a in soup.find_all('a', class_='item wide-169'):
        url = a.get('href')
        title = a.get('title')
        img = a.find('img').get('data-src')

        liz = ListItem("{}".format(
            kodiutils.compat_py23str(title))
        )
        liz.setArt({"thumb": img,
                    "icon": img,
                    "fanart": kodiutils.FANART})
        liz.setInfo("Video", infoLabels={"title": kodiutils.compat_py23str(title)})

        addDirectoryItem(
            plugin.handle,
            plugin.url_for(
                programs_episodes,
                title=kodiutils.compat_py23str(title),
                img=kodiutils.compat_py23str(img),
                url=kodiutils.compat_py23str(url),
                ep=kodiutils.compat_py23str(title),
                page=1
            ), liz, True)

    endOfDirectory(plugin.handle)


def raise_notification():
    kodiutils.ok(kodiutils.get_string(32000),kodiutils.get_string(32002))
    exit(0)


def run():
    plugin.run()

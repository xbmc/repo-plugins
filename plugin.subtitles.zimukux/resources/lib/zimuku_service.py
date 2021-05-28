# -*- coding: utf-8 -*-
"""
Subtitle add-on for Kodi 19+ derived from https://github.com/taxigps/xbmc-addons-chinese/tree/master/service.subtitles.zimuku
Copyright (C) <2021>  <root@wokanxing.info>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import os
import sys
import time
import urllib
import urllib.parse
import requests
from bs4 import BeautifulSoup
from kodi_six import xbmc, xbmcgui, xbmcaddon, xbmcplugin, xbmcvfs

import zimuku_archive

__addon__ = xbmcaddon.Addon()
__author__ = __addon__.getAddonInfo('author')
__scriptid__ = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__language__ = __addon__.getLocalizedString

__cwd__ = xbmc.translatePath(__addon__.getAddonInfo('path'))
__profile__ = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__resource__ = xbmc.translatePath(os.path.join(__cwd__, 'resources', 'lib'))
__temp__ = xbmc.translatePath(os.path.join(__profile__, 'temp'))

sys.path.append(__resource__)

ZIMUKU_BASE = __addon__.getSetting("ZiMuKuUrl")
ZIMUKU_API = '%s/search?q=%%s' % ZIMUKU_BASE
ZIMUKU_RESOURCE_BASE = ZIMUKU_BASE
UserAgent = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'

MIN_SIZE = 1024


def log(module, msg, level=xbmc.LOGDEBUG):
    xbmc.log("{0}::{1} - {2}".format(__scriptname__, module, msg), level=level)


def get_page(url, **kwargs):
    """
    Get page with requests.

    Parameters:
        url     Target URL.
        kwargs  Attached headers. HTTP_HEADER_KEY = HTTP_HEADER_VALUE. Use '_' instead of '-' in HTTP_HEADER_KEY since '-' is illegal in python variable name.

    Return:
        headers     The http response headers.
        http_body   The http response body.
    """
    headers = None
    http_body = None
    try:
        request_headers = {'User-Agent': UserAgent}
        if kwargs:
            for key, value in list(kwargs.items()):
                request_headers[key.replace('_', '-')] = value

        http_response = requests.Session().get(url, headers=request_headers)
        log(sys._getframe().f_code.co_name, 'Got url %s' % (url))
        headers = http_response.headers
        http_body = http_response.content

    except Exception as e:
        log(sys._getframe().f_code.co_name,
            "Error: %s.    Failed to access %s" % (e, url),
            level=xbmc.LOGWARNING)

    return headers, http_body


def Search(item):
    subtitles_list = []

    if item['mansearch']:
        search_str = item['mansearchstr']
    elif len(item['tvshow']) > 0:
        search_str = item['tvshow']
    else:
        search_str = item['title']
    log(
        sys._getframe().f_code.co_name, "Search for [%s], item: %s" %
        (os.path.basename(item['file_original_path']), item))
    url = ZIMUKU_API % (urllib.parse.quote(search_str))
    log(sys._getframe().f_code.co_name, "Search API url: %s" % (url))
    try:
        # Search page.
        _headers, data = get_page(url)
        soup = BeautifulSoup(data, 'html.parser')
    except Exception as e:
        log(sys._getframe().f_code.co_name,
            '%s: %s    Error searching.' % (Exception, e),
            level=xbmc.LOGERROR)
        return
    # 1. 从搜索结果中看看是否能直接找到
    if item['season'] != '' and item['episode'] != '':
        ep_list = soup.find_all("td", class_="first")
        s_e = 'S%02dE%02d' % (int(item['season']), int(item['episode']))
        log(sys._getframe().f_code.co_name,
            "find [%s] in %s" % (s_e, [ep.a.text for ep in ep_list]))
        for ep in reversed(ep_list):
            sub_name = ep.a.text
            if s_e in sub_name.upper():
                link = urllib.parse.urljoin(ZIMUKU_BASE, ep.a.get('href'))
                # alt="&nbsp;简体中文字幕&nbsp;English字幕&nbsp;双语字幕"
                alt_text = ep.img.get('alt')
                langs = alt_text.split('&nbsp;')
                if langs[0] == '':
                    langs = langs[1:]
                subtitles_list.append({
                    "language_name": "Chinese",
                    "filename": sub_name,
                    "link": link,
                    "language_flag": 'zh',
                    "rating": '0',
                    "lang": langs
                })
                break
    # 2. 直接找不到，看是否存在同一季的链接
    urls = []
    if len(subtitles_list) == 0 and item['season'] != '':
        season_list = soup.find_all("div", class_="item prel clearfix")
        season = ('一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二',
                  '十三', '十四', '十五')[int(item['season']) - 1]
        for s in season_list:
            season_name = s.b.text
            if '第%s季' % season in season_name:
                urls = [
                    urllib.parse.urljoin(
                        ZIMUKU_BASE,
                        s.find("div", class_="title").a.get('href'))
                ]
                break
    # 3. 都不行的话，就把全部字幕都列出来
    if len(subtitles_list) == 0:
        if len(urls) == 0:
            season_list = soup.find_all("div", class_="item prel clearfix")
            for it in reversed(season_list):
                #moviename = it.find("div", class_="title").a.text
                urls.append(
                    urllib.parse.urljoin(
                        ZIMUKU_BASE,
                        it.find("div", class_="title").a.get('href')))
        for url in urls:
            try:
                # Movie page.
                log(sys._getframe().f_code.co_name, "get_page: %s" % (url))
                _headers, data = get_page(url)
                soup = BeautifulSoup(data, 'html.parser').find(
                    "div", class_="subs box clearfix")
            except:
                log(sys._getframe().f_code.co_name,
                    'Error get movie page.',
                    level=xbmc.LOGERROR)
                return
            subs = soup.tbody.find_all("tr")
            for sub in reversed(subs):
                link = urllib.parse.urljoin(ZIMUKU_BASE, sub.a.get('href'))
                version = sub.a.text
                try:
                    td = sub.find("td", class_="tac lang")
                    r2 = td.find_all("img")
                    langs = [x.get('title').rstrip('字幕') for x in r2]
                except:
                    langs = '未知'
                name = '%s (%s)' % (version, ",".join(langs))

                # Get rating. rating from str(int [0 , 5]).
                try:
                    rating_div = sub.find("td", class_="tac hidden-xs")
                    rating_div_str = str(rating_div)
                    rating_star_str = "allstar"
                    rating = rating_div_str[
                        rating_div_str.find(rating_star_str) +
                        len(rating_star_str)]
                    if rating not in ["0", "1", "2", "3", "4", "5"]:
                        log(sys._getframe().f_code.co_name,
                            "Failed to locate rating in %s from %s" %
                            (rating_div_str, link),
                            level=xbmc.LOGWARNING)
                        rating = "0"
                except:
                    rating = "0"

                if '简体中文' in langs or '繁體中文' in langs or '双语' in langs:
                    # In GUI, only "lang", "filename" and "rating" displays to users, .
                    subtitles_list.append({
                        "language_name": "Chinese",
                        "filename": name,
                        "link": link,
                        "language_flag": 'zh',
                        "rating": str(rating),
                        "lang": langs
                    })
                elif 'English' in langs:
                    subtitles_list.append({
                        "language_name": "English",
                        "filename": name,
                        "link": link,
                        "language_flag": 'en',
                        "rating": str(rating),
                        "lang": langs
                    })
                else:
                    log(sys._getframe().f_code.co_name,
                        "Unrecognized lang: %s" % (langs))
                    subtitles_list.append({
                        "language_name": "Unknown",
                        "filename": name,
                        "link": link,
                        "language_flag": 'en',
                        "rating": str(rating),
                        "lang": langs
                    })

    if subtitles_list:
        for it in subtitles_list:
            listitem = xbmcgui.ListItem(label=it["language_name"],
                                        label2=it["filename"])
            listitem.setArt({
                'icon': it["rating"],
                'thumb': it["language_flag"]
            })
            listitem.setProperty("sync", "false")
            listitem.setProperty("hearing_imp", "false")

            url = "plugin://%s/?action=download&link=%s&lang=%s" % (
                __scriptid__, it["link"], it["lang"])
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                        url=url,
                                        listitem=listitem,
                                        isFolder=False)


def store_file(filename, data):
    """
    Store file function. Store bin(data) into os.path.join(__temp__, "subtitles<time>.<ext>")

    This may store subtitle files or compressed archive. So write in binary mode.

    Params:
        filename    The name of the file. May include non-unicode chars, so may cause problems if used as filename to store directly.
        data        The data of the file. May be compressed.

    Return:
        The absolute path to the file.
    """
    # Store file in an ascii name since some chars may cause some problems.
    t = time.time()
    ts = time.strftime("%Y%m%d%H%M%S", time.localtime(t)) + \
        str(int((t - int(t)) * 1000))
    tempfile = os.path.join(
        __temp__,
        "subtitles%s%s" % (ts, os.path.splitext(filename)[1])).replace(
            '\\', '/')
    with open(tempfile, "wb") as subFile:
        subFile.write(data)
    # May require close file explicitly to ensure the file.
    subFile.close()
    return tempfile.replace('\\', '/')


def DownloadLinks(links, referer):
    """
    Download subtitles one by one until success.

    Parameters:
        links   The list of subtitle download links.
        referer The url of dld list page, used as referer.

    Return:
        '', []          If nothing to return.
        filename, data  If success.
    """
    filename = None
    data = None
    small_size_confirmed = False
    data_size = -1
    link_string = ''

    for link in links:
        url = link.get('href')
        if not url.startswith('http://'):
            url = urllib.parse.urljoin(ZIMUKU_RESOURCE_BASE, url)
        link_string += url + ' '

        try:
            log(sys._getframe().f_code.co_name,
                "Download subtitle url: %s" % (url))
            # Download subtitle one by one until success.
            headers, data = get_page(url, Referer=referer)

            filename = headers['Content-Disposition'].split(
                'filename=')[1].strip('"').strip("'")
            small_size_confirmed = data_size == len(data)
            if len(data) > MIN_SIZE or small_size_confirmed:
                break
            else:
                data_size = len(data)

        except Exception:
            if filename is not None:
                log(sys._getframe().f_code.co_name,
                    "Failed to download subtitle data of %s." % (filename))
                filename = None
            else:
                log(sys._getframe().f_code.co_name,
                    "Failed to download subtitle from %s" % (url))

    if filename is not None:
        if data is not None and (len(data) > MIN_SIZE or small_size_confirmed):
            return filename, data
        else:
            log(sys._getframe().f_code.co_name,
                'File received but too small: %s %d bytes' %
                (filename, len(data)),
                level=xbmc.LOGWARNING)
            return '', ''
    else:
        log(sys._getframe().f_code.co_name,
            'Failed to download subtitle from all links: %s' % (referer),
            level=xbmc.LOGWARNING)
        return '', ''


def Download(url, lang):
    if not xbmcvfs.exists(__temp__.replace('\\', '/')):
        xbmcvfs.mkdirs(__temp__)
    dirs, files = xbmcvfs.listdir(__temp__)
    for file in files:
        xbmcvfs.delete(os.path.join(__temp__, file))

    subtitle_list = []
    exts = (".srt", ".sub", ".smi", ".ssa", ".ass", ".sup")
    supported_archive_exts = (".zip", ".7z", ".tar", ".bz2", ".rar", ".gz",
                              ".xz", ".iso", ".tgz", ".tbz2", ".cbr")

    log(sys._getframe().f_code.co_name, "Download page: %s" % (url))
    try:
        # Subtitle detail page.
        _headers, data = get_page(url)
        soup = BeautifulSoup(data, 'html.parser')
        url = soup.find("li", class_="dlsub").a.get('href')

        global ZIMUKU_RESOURCE_BASE
        if not (url.startswith('http://') or url.startswith('https://')):
            url = urllib.parse.urljoin(ZIMUKU_RESOURCE_BASE, url)
        else:
            ZIMUKU_RESOURCE_BASE = "{host_info.scheme}://{host_info.netloc}".format(
                host_info=urllib.parse.urlparse(url))
        log(sys._getframe().f_code.co_name, "Download links: %s" % (url))

        # Subtitle download-list page.
        _headers, data = get_page(url)
        soup = BeautifulSoup(data, 'html.parser')
        links = soup.find("div", {"class": "clearfix"}).find_all('a')
    except:
        log(sys._getframe().f_code.co_name,
            "Error (%d) [%s]" %
            (sys.exc_info()[2].tb_lineno, sys.exc_info()[1]),
            level=xbmc.LOGERROR)
        return []

    filename, data = DownloadLinks(links, url)
    if filename == '':
        # No file received.
        return []

    if filename.endswith(exts):
        tempfile = store_file(filename, data)
        subtitle_list.append(tempfile)

    elif filename.endswith(supported_archive_exts):
        tempfile = store_file(filename, data)
        # libarchive requires the access to the file, so sleep a while to ensure the file.
        xbmc.sleep(500)
        # Import here to avoid waste.
        archive_path, list = zimuku_archive.unpack(tempfile)

        if len(list) == 1:
            subtitle_list.append(
                os.path.join(archive_path, list[0]).replace('\\', '/'))
        elif len(list) > 1:
            # hack to fix encoding problem of zip file after Kodi 18
            if data[:2] == 'PK':
                try:
                    dlist = [x.encode('CP437').decode('gbk') for x in list]
                except:
                    dlist = list
            else:
                dlist = list

            sel = xbmcgui.Dialog().select('请选择压缩包中的字幕', dlist)
            if sel == -1:
                sel = 0
            subtitle_list.append(
                os.path.join(archive_path, list[sel]).replace('\\', '/'))

    else:
        log(sys._getframe().f_code.co_name,
            "Unsupported file: %s" % (filename),
            level=xbmc.LOGWARNING)
        xbmc.executebuiltin(
            ('XBMC.Notification("zimuku","不支持的压缩格式，请选择其他字幕文件。")'), True)

    if len(subtitle_list) > 0:
        log(sys._getframe().f_code.co_name,
            "Get subtitle file: %s" % (subtitle_list[0]),
            level=xbmc.LOGINFO)
    return subtitle_list


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = paramstring
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


def handle_params(params):
    if params['action'] == 'search' or params['action'] == 'manualsearch':
        item = {'temp': False, 'rar': False, 'mansearch': False}
        item['year'] = xbmc.getInfoLabel("VideoPlayer.Year")  # Year
        item['season'] = str(xbmc.getInfoLabel("VideoPlayer.Season"))  # Season
        item['episode'] = str(xbmc.getInfoLabel("VideoPlayer.Episode"))
        item['tvshow'] = xbmc.getInfoLabel("VideoPlayer.TVshowtitle")  # Show
        # try to get original title
        item['title'] = xbmc.getInfoLabel("VideoPlayer.OriginalTitle")
        # Full path of a playing file
        item['file_original_path'] = urllib.parse.unquote(
            xbmc.Player().getPlayingFile())
        item['3let_language'] = []

        if 'searchstring' in params:
            item['mansearch'] = True
            item['mansearchstr'] = params['searchstring']

        for lang in urllib.parse.unquote(params['languages']).split(","):
            item['3let_language'].append(
                xbmc.convertLanguage(lang, xbmc.ISO_639_2))

        if item['title'] == "":
            # no original title, get just Title
            item['title'] = xbmc.getInfoLabel("VideoPlayer.Title")
            # get movie title and year if is filename
            if item['title'] == os.path.basename(
                    xbmc.Player().getPlayingFile()):
                title, year = xbmc.getCleanMovieTitle(item['title'])
                item['title'] = title.replace('[', '').replace(']', '')
                item['year'] = year

        # Check if season is "Special"
        if item['episode'].lower().find("s") > -1:
            #
            item['season'] = "0"
            item['episode'] = item['episode'][-1:]

        if (item['file_original_path'].find("http") > -1):
            item['temp'] = True

        elif (item['file_original_path'].find("rar://") > -1):
            item['rar'] = True
            item['file_original_path'] = os.path.dirname(
                item['file_original_path'][6:])

        elif (item['file_original_path'].find("stack://") > -1):
            stackPath = item['file_original_path'].split(" , ")
            item['file_original_path'] = stackPath[0][8:]

        Search(item)

    elif params['action'] == 'download':
        subs = Download(params["link"], params["lang"])
        for sub in subs:
            listitem = xbmcgui.ListItem(label=sub)
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                        url=sub,
                                        listitem=listitem,
                                        isFolder=False)


def run():
    params = get_params()
    handle_params(params)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

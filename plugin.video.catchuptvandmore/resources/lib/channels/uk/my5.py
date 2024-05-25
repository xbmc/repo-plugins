# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Joaopa, nictjir  GNU General Public License v2.0+
# (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)
# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re
import json
import base64
import urlquick
import time

from codequick import Listitem, Resolver, Route

try:
    import urllib.parse
except ImportError:
    import urllib

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    from Crypto.Hash import HMAC, SHA256
except ImportError:
    from Cryptodome.Cipher import AES
    from Cryptodome.Util.Padding import unpad
    from Cryptodome.Hash import HMAC, SHA256

from resources.lib.menu_utils import item_post_treatment
from resources.lib import web_utils, resolver_proxy

CORONA_URL = 'https://corona.channel5.com/'
BASIS_URL = CORONA_URL + 'shows/%s/seasons'
URL_SEASONS = BASIS_URL + '.json'
URL_EPISODES = BASIS_URL + '/%s/episodes.json'
FEEDS_API = 'https://feeds-api.channel5.com/collections/%s/concise.json'
URL_VIEW_ALL = CORONA_URL + 'shows/search.json'
URL_WATCHABLE = CORONA_URL + 'watchables/search.json'
URL_SHOWS = CORONA_URL + 'shows/search.json'
BASE_IMG = 'https://api-images.channel5.com/otis/images'
IMG_URL = BASE_IMG + '/episode/%s/320x180.jpg'
SHOW_IMG_URL = BASE_IMG + '/show/%s/320x180.jpg'
ONEOFF = CORONA_URL + 'shows/%s/episodes/next.json'
LIC_BASE = 'https://cassie.channel5.com/api/v2'
LICC_URL = LIC_BASE + '/%s/my5desktopng/%s.json?timestamp=%s'
KEYURL = "https://player.akamaized.net/html5player/core/html5-c5-player.js"

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}
feeds_api_params = {
    'vod_available': 'my5desktop',
    'friendly': '1'
}

view_api_params = {
    'platform': 'my5desktop',
    'friendly': '1'
}

lic_headers = {
    'User-Agent': web_utils.get_random_ua(),
    'Referer': 'https://www.channel5.com/',
    'Content-Type': '',
}


def getdata(ui, media):
    resp = urlquick.get(KEYURL, headers=GENERIC_HEADERS, max_age=-1)
    content = resp.content.decode("utf-8", "ignore")
    ss = re.compile(r';}}}\)\(\'(......)\'\)};').search(content).group(1)
    m = re.compile(r'\(\){return "(.{3000,})";\}').search(content).group(1)

    timeStamp = str(int(time.time()))
    CALL_URL = LICC_URL % (media, ui, timeStamp)

    try:
        h = urllib.parse.unquote(m)
        hmac_update = bytes(CALL_URL, encoding="utf-8")
    except Exception:
        h = urllib.unquote(m.encode('utf-8')).decode('utf-8', 'ignore')
        hmac_update = str(CALL_URL)

    z = [ord(c) for c in h]
    y = 0
    sout = ""
    for x in z:
        if (y > 5):
            y = 0
        k = x ^ ord(ss[y])
        if (k > 31) and (k < 127):
            sout = sout + chr(k)
        y = y + 1

    m = re.compile(r'SSL_MA..(.{24})..(.{24})').findall(sout)[0]
    h = HMAC.new(base64.urlsafe_b64decode(str(m[0])), digestmod=SHA256)
    h.update(hmac_update)
    auth = base64.urlsafe_b64encode(h.digest()).decode('utf-8')[:-1].replace("+", "-").replace("/", "_")

    return CALL_URL, auth, m[1]


def ivdata(lic_full, auth):
    params = {'auth': auth}
    resp = urlquick.get(lic_full, headers=GENERIC_HEADERS, params=params, max_age=-1)
    root = json.loads(resp.text)
    return root['iv'], root['data']


def mangle(result):
    return result.replace("-", "+").replace("_", "/")


def getUseful(s):
    keyserver = 'NA'
    streamUrl = 'NA'
    subtitile = 'NA'
    data = json.loads(s)
    jsonData = data['assets']
    for x in jsonData:
        if (x['drm'] == "widevine"):
            keyserver = (x['keyserver'])
            u = (x['renditions'])
            for i in u:
                streamUrl = i['url']
    return streamUrl, keyserver, subtitile


def part2(iv, aesKey, rdata):
    realIv = base64.b64decode(mangle(iv)).ljust(16, b'\0')
    realAesKey = base64.b64decode(mangle(aesKey)).ljust(16, b'\0')
    realRData = base64.b64decode(mangle(rdata))
    cipher = AES.new(realAesKey, AES.MODE_CBC, iv=realIv)
    dataToParse = unpad(cipher.decrypt(realRData), 16).decode('utf-8')
    return getUseful(dataToParse)


@Route.register
def list_categories(plugin, **kwargs):
    resp = urlquick.get(FEEDS_API % 'PLC_My5SubGenreBrowsePageSubNav', headers=GENERIC_HEADERS,
                        params=feeds_api_params, max_age=-1)
    root = json.loads(resp.text)
    for i in range(int(root['total_items'])):
        # need a try as sometimes the web page reports more total_items than there is listed
        try:
            item = Listitem()
            item.label = root['filters']['contents'][i]['title']
            browse_name = root['filters']['contents'][i]['id']
            offset = "0"
            item.set_callback(list_subcategories, browse_name=browse_name, offset=offset)
            item_post_treatment(item)
            yield item
        except (IndexError, ValueError, AttributeError):
            pass


@Route.register
def list_subcategories(plugin, browse_name, offset, **kwargs):
    if (browse_name == "PLC_My5AllShows"):
        w_params = {
            'limit': '25',
            'offset': str(offset),
            'platform': 'my5desktop',
            'friendly': '1',
        }
        resp = urlquick.get(URL_SHOWS, headers=GENERIC_HEADERS, params=w_params, max_age=-1)
        root = json.loads(resp.text)

        item_number = int(root['size'])

        for emission in root['shows']:
            item = Listitem()
            title = emission['title']
            item.label = title
            item.info['plot'] = emission['s_desc']
            fname = emission['f_name']
            picture_id = emission['id']
            item.art['thumb'] = item.art['landscape'] = SHOW_IMG_URL % picture_id
            if "standalone" in emission:
                item.set_callback(get_video_url, fname=fname, season_f_name="",
                                  show_id="show_id", standalone="yes")
            else:
                item.set_callback(list_seasons, fname=fname, pid=picture_id, title=title)
            item_post_treatment(item)
            yield item
        if 'next_page_url' in root:
            offset = str(int(offset) + int(root['limit']))
            yield Listitem.next_page(browse_name=browse_name, offset=offset)
    else:
        resp = urlquick.get(FEEDS_API % browse_name, headers=GENERIC_HEADERS,
                            params=feeds_api_params, max_age=-1)
        root = json.loads(resp.text)
        item_number = int(root['total_items'])

        if root['filters']['type'] == 'Collection':
            offset = 0
            # need a try as sometimes the web page reports more total_items than there is listed
            try:
                for i in range(item_number):
                    item = Listitem()
                    item.label = root['filters']['contents'][i]['title']
                    browse_name = root['filters']['contents'][i]['id']
                    item.set_callback(list_collections, browse_name=browse_name, offset=offset)
                    item_post_treatment(item)
                    yield item
            except (IndexError, ValueError, AttributeError):
                pass
        elif root['filters']['type'] == 'Show':
            ids = root['filters']['ids']
            w_params = {
                'limit': str(item_number),
                'offset': '0',
                'platform': 'my5desktop',
                'friendly': '1'
            }
            for i in range(item_number):
                try:
                    w_params.update({'ids[]': ids[i]})
                except (IndexError, ValueError):
                    pass
            resp = urlquick.get(URL_SHOWS, headers=GENERIC_HEADERS, params=w_params, max_age=-1)
            root = json.loads(resp.text)
            for watchable in root['shows']:
                item = Listitem()
                item.label = watchable['title']
                item.info['plot'] = watchable['s_desc']
                item.art['thumb'] = item.art['landscape'] = SHOW_IMG_URL % watchable['id']
                show_id = watchable['id']
                fname = watchable['f_name']
                item.set_callback(get_video_url, fname=fname, season_f_name="season_f_name",
                                  show_id=show_id, standalone="yes")
                item_post_treatment(item)
                yield item
        elif root['filters']['type'] == 'Watchable':
            ids = root['filters']['ids']
            w_params = {
                'limit': str(item_number),
                'offset': '0',
                'platform': 'my5desktop',
                'friendly': '1'
            }
            for i in range(item_number):
                try:
                    w_params.update({'ids[]': ids[i]})
                except (IndexError, ValueError):
                    pass
            resp = urlquick.get(URL_WATCHABLE, headers=GENERIC_HEADERS, params=w_params, max_age=-1)
            root = json.loads(resp.text)

            for watchable in root['watchables']:
                item = Listitem()
                item.label = watchable['sh_title']
                item.info['plot'] = watchable['s_desc']
                item.info['duration'] = int(int(watchable['len']) // 1000)
                item.art['thumb'] = item.art['landscape'] = SHOW_IMG_URL % watchable['sh_id']
                show_id = watchable['id']
                item.set_callback(get_video_url, fname="fname", season_f_name="season_f_name",
                                  show_id=show_id, standalone="no")
                item_post_treatment(item)
                yield item


@Route.register
def list_collections(plugin, browse_name, offset, **kwargs):
    resp = urlquick.get(FEEDS_API % browse_name, headers=GENERIC_HEADERS,
                        params=feeds_api_params, max_age=-1)
    root = json.loads(resp.text)
    subgenre = root['filters']['vod_subgenres']
    view_all_params = {
        'platform': 'my5desktop',
        'friendly': '1',
        'limit': '25',
        'offset': offset,
        'vod_subgenres[]': subgenre
    }
    resp = urlquick.get(URL_VIEW_ALL, headers=GENERIC_HEADERS, params=view_all_params, max_age=-1)
    root = json.loads(resp.text)

    for emission in root['shows']:
        item = Listitem()
        title = emission['title']
        item.label = title
        item.info['plot'] = emission['s_desc']
        fname = emission['f_name']
        picture_id = emission['id']
        item.art['thumb'] = item.art['landscape'] = SHOW_IMG_URL % picture_id
        if "standalone" in emission:
            item.set_callback(get_video_url, fname=fname, season_f_name="",
                              show_id="show_id", standalone="yes")
        else:
            item.set_callback(list_seasons, fname=fname, pid=picture_id, title=title)
        item_post_treatment(item)
        yield item
    if 'next_page_url' in root:
        offset = str(int(offset) + int(view_all_params['limit']))
        yield Listitem.next_page(browse_name=browse_name, offset=offset)


@Route.register
def list_seasons(plugin, fname, pid, title, **kwargs):
    resp = urlquick.get(URL_SEASONS % fname, headers=GENERIC_HEADERS, params=view_api_params)
    root = json.loads(resp.text)

    for season in root['seasons']:
        item = Listitem()
        season_number = season['seasonNumber']
        item.label = title + '\nSeason ' + season_number
        item.art['thumb'] = item.art['landscape'] = SHOW_IMG_URL % pid
        item.set_callback(list_episodes, fname=fname, season_number=season_number)
        item_post_treatment(item)
        yield item


@Route.register
def list_episodes(plugin, fname, season_number, **kwargs):
    resp = urlquick.get(URL_EPISODES % (fname, season_number), headers=GENERIC_HEADERS,
                        params=view_api_params, max_age=-1)
    root = json.loads(resp.text)

    for episode in root['episodes']:
        item = Listitem()
        picture_id = episode['id']
        item.art['thumb'] = item.art['landscape'] = IMG_URL % picture_id
        item.label = episode['title']
        item.info['plot'] = episode['s_desc']
        t = int(int(episode['len']) // 1000)
        item.info['duration'] = t
        season_f_name = episode['sea_f_name']
        fname = episode['f_name']
        show_id = episode['id']
        item.set_callback(get_video_url, fname=fname, season_f_name=season_f_name,
                          show_id=show_id, standalone="no")
        item_post_treatment(item)
        yield item


@Resolver.register
def get_video_url(plugin, fname, season_f_name, show_id, standalone, **kwargs):
    if (standalone == "yes"):
        resp = urlquick.get(ONEOFF % fname, headers=GENERIC_HEADERS,
                            params=view_api_params, max_age=-1)
        root = json.loads(resp.text)
        show_id = root['id']

    LICFULL_URL, auth, aesKey = getdata(show_id, 'media')
    iv, data = ivdata(LICFULL_URL, auth)
    video_url, drm_url, sub_url = part2(iv, aesKey, data)

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, license_url=drm_url,
                                                  manifest_type='mpd', headers=lic_headers)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    LICFULL_URL, auth, aesKey = getdata(item_id, 'live_media')
    iv, data = ivdata(LICFULL_URL, auth)
    video_url, drm_url, sub_url = part2(iv, aesKey, data)

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, license_url=drm_url,
                                                  manifest_type='mpd', headers=lic_headers)

#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Tristan Fischer
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import hashlib
import re
from base64 import b64decode
from BeautifulSoup import BeautifulSoup
from binascii import unhexlify
from urllib import unquote, urlencode
from urllib2 import urlopen, Request, HTTPError, URLError

MAIN_URL = 'http://www.myvideo.de/'

UA = ('Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) '
      'AppleWebKit/535.1 (KHTML, like Gecko) '
      'Chrome/13.0.782.6 Safari/535.1')
GK = ('WXpnME1EZGhNRGhpTTJNM01XVmhOREU0WldNNVpHTTJOakpt'
      'TW1FMU5tVTBNR05pWkRaa05XRXhNVFJoWVRVd1ptSXhaVEV3'
      'TnpsbA0KTVRkbU1tSTRNdz09')

CATEGORIES = ({'title': 'Top 100',
               'path': 'Top_100'},
              {'title': 'Videos',
               'path': 'Videos_A-Z'},
              {'title': 'Serien',
               'path': 'Serien'},
              {'title': 'Filme',
               'path': 'Filme'},
              {'title': 'Musik',
               'path': 'Musik'})

BLOCKED_SUBCATS = ('/Videos_A-Z/Video_Flight',
                   '/Videos_A-Z/Videos_in_Playlisten',
                   '/musik-tv',
                   '/channel/Clipgenerator',
                   '/echo',
                   '/Themen/Sexy',
                   '/Top_100/Top_100_Playlisten',
                   '/Serien/WWE')

R_ID = re.compile('watch/([0-9]+)/?')

DEBUG = False


def get_categories():
    __start()
    return CATEGORIES


def get_sub_categories(path):
    __log('get_sub_categories started with path: %s' % path)
    tree = __get_tree(MAIN_URL)
    section = tree.find('div', {'class': 'body topNavFW'})
    sub_cats = []
    link = section.find('a', {'href': '/%s' % path})
    if link:
        for l in link.parent.findAll('a', {'class': 'topsub nArrow'}):
            if l['href'] in BLOCKED_SUBCATS:
                __log('skipping entry with link: %s' % l['href'])
                continue
            sub_cats.append({'title': l.span.string.strip(),
                             'path': l['href'][1:]})
    __log('get_sub_categories finished with %d elements' % len(sub_cats))
    return sub_cats


def get_search_result(query):
    __log('get_search_result started with path: %s' % query)
    path = '/Videos_A-Z?%s' % urlencode({'searchWord': query})
    items = get_path(path)
    return items


def get_path(path):
    __log('get_path started with path: %s' % path)
    tree = __get_tree(MAIN_URL + path)
    if 'Top_100' in path:
        items = __parse_video_charts(tree, path)
    elif 'filme_video_list' in path:
        items = __parse_movies(tree, path)
    elif 'video_list' in path:
        items = __parse_channels(tree, path)
    elif 'mv_charts' in path:
        items = __parse_channels(tree, path)
    elif 'Musik_Charts' in path:
        items = __parse_music_charts(tree, path)
    elif 'Charts' in path:  # fixme: still needed?
        items = __parse_video_charts(tree, path)
    elif 'channel' in path:
        items = __parse_channels(tree, path)
    elif 'playlist' in path:  # fixme: needs to be rewritten
        items = __parse_playlists(tree, path)
    elif 'Musik_K' in path:
        if not 'lpage' in path:
            items = __parse_letter(tree, path)
        else:
            items = __parse_music_artists(tree, path)
    elif 'Musik_Videos' in path:
        items = __parse_video_default(tree, path)
    elif 'Musik' in path:
        items = __parse_music(tree, path)
    elif 'Filme' in path:
        items = __parse_movies(tree, path)
    elif 'Kategorien' in path:
        items = __parse_categories(tree, path)
    elif 'Alle_Serien_A-Z' in path:
        items = __parse_shows_overview(tree, path)
    elif 'Serien' in path:
        items = __parse_shows(tree, path)
    else:
        items = __parse_video_default(tree, path)
    return items


def get_video(video_id, console_debug=False):
    __log('get_video started with video_id: %s' % video_id)
    r_adv = re.compile('var flashvars={(.+?)}')
    r_adv_p = re.compile('(.+?):\'(.+?)\',?')
    r_swf = re.compile('swfobject.embedSWF\(\'(.+?)\'')
    r_rtmpurl = re.compile('connectionurl=\'(.*?)\'')
    r_playpath = re.compile('source=\'(.*?)\'')
    r_path = re.compile('path=\'(.*?)\'')
    video = {}
    params = {}
    encxml = ''
    videopage_url = MAIN_URL + 'watch/%s/' % video_id
    html = __get_url(videopage_url, MAIN_URL)
    sec = re.search(r_adv, html).group(1)
    for (a, b) in re.findall(r_adv_p, sec):
        if not a == '_encxml':
            params[a] = b
        else:
            encxml = unquote(b)
    xmldata_url = '%s?%s' % (encxml, urlencode(params))
    if 'flash_playertype=MTV' in xmldata_url:
        __log('get_video avoiding MTV player')
        xmldata_url = ('http://www.myvideo.de/dynamic/get_player_video_xml.php'
                       '?flash_playertype=D&ID=%s&_countlimit=4&autorun=yes') \
                       % video_id
    enc_data = __get_url(xmldata_url, videopage_url).split('=')[1]
    enc_data_b = unhexlify(enc_data)
    sk = __md5(b64decode(b64decode(GK)) + __md5(str(video_id)))
    dec_data = __rc4crypt(enc_data_b, sk)
    rtmpurl = re.search(r_rtmpurl, dec_data).group(1)
    video['rtmpurl'] = unquote(rtmpurl)
    if 'myvideo2flash' in video['rtmpurl']:
        __log('get_video forcing RTMPT')
        video['rtmpurl'] = video['rtmpurl'].replace('rtmpe://', 'rtmpt://')
    playpath = re.search(r_playpath, dec_data).group(1)
    video['file'] = unquote(playpath)
    ppath, prefix = unquote(playpath).split('.')
    video['playpath'] = '%s:%s' % (prefix, ppath)
    swfobj = re.search(r_swf, html).group(1)
    video['swfobj'] = unquote(swfobj)
    video['pageurl'] = videopage_url
    m_filepath = re.search(r_path, dec_data)
    video['filepath'] = m_filepath.group(1)
    if not video['rtmpurl']:
        __log('get_video using FLV')
        video_url = video['filepath'] + video['file']
        if console_debug:
            print 'wget %s' % video_url
    else:
        __log('get_video using RTMPE or RTMPT')
        if console_debug:
            print ('rtmpdump '
                   '--rtmp "%s" '
                   '--flv "test.flv" '
                   '--tcUrl "%s" '
                   '--swfVfy "%s" '
                   '--pageUrl "%s" '
                   '--playpath "%s"') % (video['rtmpurl'],
                                         video['rtmpurl'],
                                         video['swfobj'],
                                         video['pageurl'],
                                         video['playpath'])
        video_url = ('%s '
                     'tcUrl=%s '
                     'swfVfy=%s '
                     'pageUrl=%s '
                     'playpath=%s') % (video['rtmpurl'],
                                       video['rtmpurl'],
                                       video['swfobj'],
                                       video['pageurl'],
                                       video['playpath'])
    return video_url


def __parse_video_charts(tree, path):
    __log('__parse_video_charts started with path: %s' % path)
    r_div = re.compile('vThumb')
    subtree = tree.find('div', {'class': 'lContent'})
    sections = subtree.findAll('div', {'class': r_div})
    items = []
    for sec in sections:
        path = sec.a['href']
        is_folder, video_id = __detect_folder(path)
        title = sec.a['title']
        thumb = sec.img['src']
        try:
            length_str = sec.span.string
            length = __format_length(length_str)
        except AttributeError:
            length = '0:00'
        items.append({'title': title,
                      'thumb': thumb,
                      'length': length,
                      'path': path,
                      'is_folder': is_folder,
                      'video_id': video_id})
    __log('__parse_video_charts finished with %d elements' % len(items))
    return items


def __parse_video_default(tree, path):
    __log('__parse_video_default started with path: %s' % path)
    subtree = tree.find('div', {'class': 'lContent'})
    r_td = re.compile('hslice.*?video_list')
    items = []
    pagination = subtree.find('div', {'class': 'pView'})
    if pagination:
        prev_link = pagination.find('a', {'class': 'pView pnBack'})
        if prev_link:
            items.append({'title': prev_link['title'],
                          'pagenination': 'PREV',
                          'path': prev_link['href']})
        next_link = pagination.find('a', {'class': 'pView pnNext'})
        if next_link:
            items.append({'title': next_link['title'],
                          'pagenination': 'NEXT',
                          'path': next_link['href']})
    sections = subtree.findAll('div', {'class': r_td})
    for sec in sections:
        link = sec.find('a', {'class': 'vLink'})
        if not link:
            continue
        path = link['href']
        is_folder, video_id = __detect_folder(path)
        title = link['title']
        thumb = link.img['src']
        length_str = sec.find('span', {'class': 'vViews'}).string
        length = __format_length(length_str)
        username = sec.find('span', {'class': 'nick'}).a['title']
        span = sec.find('span', {'id': 'vc%s' % video_id})
        if span:
            views = span.string.replace('.', '')
        else:
            views = 0
        date = sec.find('div', {'class': 'sCenter vAdded'}).string
        items.append({'title': title,
                      'thumb': thumb,
                      'length': length,
                      'path': path,
                      'is_folder': is_folder,
                      'username': username,
                      'views': views,
                      'date': date,
                      'video_id': video_id})
    __log('__parse_video_default finished with %d elements' % len(items))
    return items


def __parse_music(tree, path):
    __log('__parse_music started with path: %s' % path)
    r_td = re.compile('floatLeft fRand')
    subtree = tree.find('div', {'class': 'lContent'})
    sections = subtree.findAll('div', {'class': r_td})
    items = []
    for sec in sections:
        div = sec.find('div', {'class': 'vThumb chThumb'})
        if div:
            path = div.a['href']
            is_folder, video_id = __detect_folder(path)
            title = div.a['title']
            thumb = div.img['src']
            length_str = div.find('span', {'class': 'vViews'}).string
            length = __format_length(length_str)
            items.append({'title': title,
                          'thumb': thumb,
                          'length': length,
                          'path': path,
                          'is_folder': is_folder,
                          'video_id': video_id})
    __log('__parse_music finished with %d elements' % len(items))
    return items


def __parse_categories(tree, path):
    __log('__parse_categories started with path: %s' % path)
    r_td = re.compile('body sCenter cGround sTLeft')
    sections = tree.findAll('td', {'class': r_td})
    items = []
    for sec in sections:
        d = sec.find('div', {'class': 'sCenter kTitle'})
        path = d.a['href']
        is_folder = True
        title = d.a.string
        thumb = sec.find('div', {'class': 'vThumb kThumb'}).a.img['src']
        items.append({'title': title,
                      'thumb': thumb,
                      'path': path,
                      'is_folder': is_folder})
    __log('__parse_categories finished with %d elements' % len(items))
    return items


def __parse_music_charts(tree, path):
    __log('__parse_music_charts started with path: %s' % path)
    r_section = re.compile('lBox floatLeft pHalfBox charts_box')
    sections = tree.findAll('div', {'class': r_section})
    items = []
    for sec in sections:
        d = sec.find('td', {'class': 'wLListLeft'})
        title = d.nextSibling.string.strip()
        path = sec.find('a', {'class': 'sBold'})['href']
        is_folder = True
        items.append({'title': title,
                      'path': path,
                      'is_folder': is_folder})
    __log('__parse_music_charts finished with %d elements' % len(items))
    return items


def __parse_shows_overview(tree, path):
    __log('__parse_shows_overview started with path: %s' % path)
    subtree = tree.find('div', {'class': 'lContent'})
    sections = subtree.findAll('div', {'class': 'lBox seriesDetail'})
    items = []
    for sec in sections:
        prevs = sec.previousSibling
        path = prevs.a['href']
        is_folder = True
        title = prevs.a.string
        thumb = sec.find('div', {'class': 'vThumb pChThumb'}).div.img['src']
        items.append({'title': title,
                      'thumb': thumb,
                      'path': path,
                      'is_folder': is_folder})
    __log('__parse_shows_overview finished with %d elements' % len(items))
    return items


def __parse_playlists(tree, path):
    __log('__parse_playlists started with path: %s' % path)
    subtree = tree.find('div', {'class': 'globalBxBorder globalBx'})
    sections = subtree.findAll('div', {'class': 'vds_video_sidebar_item'})
    items = []
    for sec in sections:
        d = sec.find('div', {'class': 'nTitle'})
        title = d.a['title']
        path = d.a['href']
        is_folder = True
        thumb = sec.find('img', {'class': 'vThumb nThumb pThumb'})['src']
        items.append({'title': title,
                      'thumb': thumb,
                      'path': path,
                      'is_folder': is_folder})
    __log('__parse_playlists finished with %d elements' % len(items))
    return items


def __parse_channels(tree, path):
    __log('__parse_channels started with path: %s' % path)
    r_div = re.compile('lBox floatLeft qLeftBox charts_box')
    r_td = re.compile('body sTLeft')
    subtree = tree.find('div', {'class': r_div})
    subtree2 = tree.find('div', {'class': 'uBList'})
    items = []
    if subtree:  # video channel
        __log('__parse_channels assuming video channel')
        r_pagination = re.compile('pViewBottom')
        r_pagelink = re.compile('src=\'(.+?)\'')
        pagination = tree.find('div', {'class': r_pagination})
        if pagination:
            prev_link = pagination.find('a',
                                        {'class': 'pView pSmaller pnBack'})
            if prev_link:
                link = re.search(r_pagelink, prev_link['onclick']).group(1)
                items.append({'title': prev_link['title'],
                              'pagenination': 'PREV',
                              'path': link})
            next_link = pagination.find('a',
                                        {'class': 'pView pSmaller pnNext'})
            if next_link:
                link = re.search(r_pagelink, next_link['onclick']).group(1)
                items.append({'title': next_link['title'],
                              'pagenination': 'NEXT',
                              'path': link})
        sections = subtree.findAll('td', {'class': r_td})
        for sec in sections:
            d = sec.find('div', {'class': 'pChHead'})
            if d:
                title = d.a['title']
                path = d.a['href']
                is_folder, video_id = __detect_folder(path)
                length_str = sec.find('span', {'class': 'vViews'}).string
                length = __format_length(length_str)
                thumb = sec.find('img', {'class': 'vThumb'})['src']
                items.append({'title': title,
                              'thumb': thumb,
                              'path': path,
                              'length': length,
                              'video_id': video_id,
                              'is_folder': is_folder})
    elif subtree2:  # music channel
        __log('__parse_channels assuming music channel')
        r_pagination = re.compile('pView')
        r_pagelink = re.compile('src=\'(.+?)\'')
        pagination = tree.find('table', {'class': r_pagination})
        if pagination:
            prev_link = pagination.find('a', {'class': 'pView pnBack'})
            if prev_link:
                link = re.search(r_pagelink, prev_link['onclick']).group(1)
                items.append({'title': prev_link['title'],
                              'pagenination': 'PREV',
                              'path': link})
            next_link = pagination.find('a', {'class': 'pView pnNext'})
            if next_link:
                link = re.search(r_pagelink, next_link['onclick']).group(1)
                items.append({'title': next_link['title'],
                              'pagenination': 'NEXT',
                              'path': link})
        sections = subtree2.findAll('div', {'class': 'uBItem'})
        for sec in sections:
            d = sec.find('div', {'class': 'sCenter uBTitle'})
            title = d.a['title']
            path = d.a['href']
            is_folder, video_id = __detect_folder(path)
            length_str = sec.find('span', {'class': 'vViews uBvViews'}).string
            length = __format_length(length_str)
            thumb = sec.find('img', {'class': 'uBThumb uBvThumb'})['src']
            items.append({'title': title,
                          'thumb': thumb,
                          'path': path,
                          'length': length,
                          'video_id': video_id,
                          'is_folder': is_folder})
    __log('__parse_channels finished with %d elements' % len(items))
    return items


def __parse_shows(tree, path):
    __log('__parse_shows started with path: %s' % path)
    r_td = re.compile('body sTLeft series_member')
    subtree = tree.find('div', {'class': 'lContent'})
    items = []
    if subtree:
        sections = subtree.findAll('td', {'class': r_td})
        for sec in sections:
            d = sec.find('div', {'class': 'pChHead'})
            title = d.a['title']
            path = d.a['href']
            is_folder = True
            thumb = sec.find('img', {'class': 'vThumb'})['src']
            items.append({'title': title,
                          'thumb': thumb,
                          'path': path,
                          'is_folder': is_folder})
    __log('__parse_shows finished with %d elements' % len(items))
    return items


def __parse_movies(tree, path):
    __log('__parse_movies started with path: %s' % path)
    r_pagination = re.compile('pView')
    r_pagelink = re.compile('src=\'(.+?)\'')
    items = []
    pagination = tree.find('div', {'class': r_pagination})
    if pagination:
        prev_link = pagination.find('a', {'class': 'pView pnBack'})
        if prev_link:
            link = re.search(r_pagelink, prev_link['onclick']).group(1)
            items.append({'title': prev_link['title'],
                          'pagenination': 'PREV',
                          'path': link})
        next_link = pagination.find('a', {'class': 'pView pnNext'})
        if next_link:
            link = re.search(r_pagelink, next_link['onclick']).group(1)
            items.append({'title': next_link['title'],
                          'pagenination': 'NEXT',
                          'path': link})
    sections = tree.findAll('div', {'class': 'filme_entry'})
    for sec in sections:
        d = sec.find('div', {'class': 'vTitle'})
        title = d.a['title']
        path = d.a['href']
        is_folder, video_id = __detect_folder(path)
        length_str = sec.find('span', {'class': 'vViews'}).string
        length = __format_length(length_str)
        thumb = sec.find('img', {'class': 'vThumb'})['src']
        items.append({'title': title,
                      'thumb': thumb,
                      'path': path,
                      'length': length,
                      'video_id': video_id,
                      'is_folder': is_folder})
    __log('__parse_movies finished with %d elements' % len(items))
    return items


def __parse_letter(tree, path):
    __log('__parse_letter started with path: %s' % path)
    sections = tree.findAll('td', {'class': 'mView'})
    items = []
    for sec in sections:
        title = sec.a.string.strip()
        path = sec.a['href']
        is_folder = True
        items.append({'title': title,
                      'path': path,
                      'is_folder': is_folder})
    __log('__parse_letter finished with %d elements' % len(items))
    return items


def __parse_music_artists(tree, path):
    __log('__parse_music_artists started with path: %s' % path)
    subtree = tree.find('div', {'class': 'lContent'})
    items = []
    if subtree:
        sections = subtree.findAll('td', {'class': 'body sTLeft'})
        for sec in sections:
            d = sec.find('div', {'class': 'pChThumb pPrThumb'})
            title = d.a['title']
            path = d.a['href']
            is_folder, video_id = __detect_folder(path)
            thumb = d.img['src']
            items.append({'title': title,
                          'thumb': thumb,
                          'path': path,
                          'video_id': video_id,
                          'is_folder': is_folder})
    __log('__parse_music_artists finished with %d elements' % len(items))
    return items


def __format_length(length_str):
    if ' min' in length_str:
        length = length_str.replace(' min', '')
    elif ' Std.' in length_str:
        length = length_str.replace(' Std.', '')
    else:
        length = '0:00'
    return length


def __detect_folder(path):
    video_id = None
    is_folder = True
    m_id = re.search(R_ID, path)
    if m_id:
        video_id = m_id.group(1)
        is_folder = False
    return is_folder, video_id


def __get_tree(url, referer=None):
    html = __get_url(url, referer)
    tree = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
    return tree


def __start():
    __log('started')
    pass


def __get_url(url, referer=None):
    __log('__get_url opening url: %s' % url)
    req = Request(url)
    if referer:
        req.add_header('Referer', referer)
    req.add_header('Accept', ('text/html,application/xhtml+xml,'
                              'application/xml;q=0.9,*/*;q=0.8'))
    req.add_header('User-Agent', UA)
    html = urlopen(req).read()
    __log('__get_url got %d bytes' % len(html))
    return html


def __rc4crypt(data, key):
    x = 0
    box = range(256)
    for i in range(256):
        x = (x + box[i] + ord(key[i % len(key)])) % 256
        box[i], box[x] = box[x], box[i]
    x = 0
    y = 0
    out = []
    for char in data:
        x = (x + 1) % 256
        y = (y + box[x]) % 256
        box[x], box[y] = box[y], box[x]
        out.append(chr(ord(char) ^ box[(box[x] + box[y]) % 256]))
    return ''.join(out)


def __md5(s):
    return hashlib.md5(s).hexdigest()


def __log(msg):
    print('MyVideo.de scraper: %s' % msg)

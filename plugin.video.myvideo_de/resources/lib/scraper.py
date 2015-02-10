#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Tristan Fischer (sphere@dersphere.de)
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

GK = (
    'WXpnME1EZGhNRGhpTTJNM01XVmhOREU0WldNNVpHTTJOakpt'
    'TW1FMU5tVTBNR05pWkRaa05XRXhNVFJoWVRVd1ptSXhaVEV3'
    'TnpsbA0KTVRkbU1tSTRNdz09'
)

CATEGORIES = (
    {'title': 'Top 100', 'path': 'Top_100'},
    {'title': 'Videos', 'path': 'Videos_A-Z'},
    {'title': 'Community', 'path': 'Videos_A-Z/Videos_in_Kategorien'},
    {'title': 'TV', 'path': 'Serien'},
    {'title': 'Filme', 'path': 'Filme'},
    {'title': 'Musik', 'path': 'Musik'}
)

R_ID = re.compile('watch/([0-9]+)/?')


class NetworkError(Exception):
    pass


def get_categories():
    return CATEGORIES


def get_search_path(query):
    log('get_search_result started with path: %s' % query)
    path = '/Videos_A-Z?%s' % urlencode({'searchWord': query})
    return path


class BaseScraper(object):

    # Todo Modifiers (Heute, Woche, Monat, ...)

    path_matches = []

    pagination_section_props = []
    next_page_props = []
    prev_page_props = []

    subtree_props = []
    section_props = []

    a_props = []
    img_props = []
    duration_props = []
    author_props = []
    date_props = []

    needs_cookie = False

    def get_tree(self, path):
        extra_arg = None
        if 'EXTRA_ARG=' in path:
            path, extra_arg = path.split('EXTRA_ARG=')
        self.path = path
        self.extra_arg = extra_arg
        tree = requester.get_tree(
            MAIN_URL + path, needs_cookie=self.needs_cookie
        )
        return tree

    @classmethod
    def choose_scraper(cls, path):
        log('Trying to find a matching scraper class for path: "%s"' % path)
        for subcls in cls.__subclasses__():
            for path_match in subcls.path_matches:
                if path_match in path:
                    return subcls()

    def parse(self, tree):
        sections = self.get_sections(tree)
        if not sections:
            self.log('Found no sections :(')
        items = (self.parse_item(section) for section in sections)
        # Need this double generator pass to filter out skipped items
        items = (i for i in items if i)
        next_page, prev_page = self.parse_pagination(tree)
        return items, next_page, prev_page

    def get_sections(self, tree):
        if self.subtree_props:
            subtree = tree.find(*self.subtree_props)
            if subtree:
                self.log('found subtree')
                tree = subtree
        sections = tree.findAll(*self.section_props)
        #print 'sections: %s' % sections
        return sections

    def parse_item(self, section):
        a = section.find(*self.a_props)
        if not a:
            log('Skipping item: %s' % section)
            return
        path = a['href']
        is_folder, video_id = self.detect_folder(path)
        item = {
            'title': a['title'] or a.string,
            'path': path,
            'is_folder': is_folder,
            'video_id': video_id,
        }
        if self.img_props:
            item['thumb'] = self.get_img(section)
        if self.duration_props:
            duration_elem = section.find(*self.duration_props)
            if duration_elem and duration_elem.string:
                item['duration'] = self.format_length(duration_elem.string)
        if self.author_props:
            author_elem = section.find(*self.author_props)
            if author_elem and author_elem.a:
                item['author'] = {
                    'name': author_elem.a['title'],
                    'id': author_elem.a['href'].rsplit('=')[-1]
                }
        if self.date_props:
            date_elem = section.find(*self.date_props)
            if date_elem and date_elem.string:
                item['date'] = date_elem.string
        return item

    def get_img(self, section):
        img = section.find(*self.img_props)
        if img:
            return img.get('longdesc') or img.get('src')
        else:
            self.log('Error in get_img!')

    def parse_pagination(self, tree):

        def get_path(a_elem):
            if a['href'] == '#':
                re_path = re.compile('.src=\'(.*?)\'')
                path = re_path.search(a['onclick']).group(1)
            else:
                path = a['href']
            return {
                'number': a['title'],
                'path': path
            }

        next_page = prev_page = None
        if self.pagination_section_props:
            section = tree.find(*self.pagination_section_props)
            if section:
                self.log('found pagination section')
                if self.next_page_props:
                    a = section.find(*self.next_page_props)
                    if a:
                        self.log('found pagenination next link')
                        next_page = get_path(a)
                if self.prev_page_props:
                    a = section.find(*self.prev_page_props)
                    if a:
                        self.log('found pagenination prev link')
                        prev_page = get_path(a)
        return next_page, prev_page

    @staticmethod
    def detect_folder(path):
        video_id = None
        is_folder = True
        m_id = re.search(R_ID, path)
        if m_id:
            video_id = m_id.group(1)
            is_folder = False
        return is_folder, video_id

    @staticmethod
    def format_length(length_str):
        if ' min' in length_str or ' Std.' in length_str:
            h = m = s = '0'
            if ' min' in length_str:
                m, s = length_str.replace(' min', '').split(':')
            elif ' Std.' in length_str:
                h, m, s = length_str.replace(' Std.', '').split(':')
            seconds = int(h) * 3600 + int(m) * 60 + int(s)
            return seconds
        return 0

    def log(self, msg):
        print('MyVideo.de scraper %s: %s' % (self.__class__.__name__, msg))

# FIXME Rating/Votes
# FIXME Plot


# Needs to be before TopCategoryScraper
class TopScraper(BaseScraper):
    path_matches = ('Top_100/', )
    subtree_props = ('div', {'class': 'lContent'})
    section_props = ('div', {'class': re.compile('vThumb')})
    a_props = ('a', )
    img_props = ('img', )
    duration_props = ('span', {'class': 'vViews'})
    author_props = ('span', {'class': 'nick'})


class TopCategoryScraper(BaseScraper):
    path_matches = ('Top_100', )
    section_props = ('div', {'id': re.compile('id_[0-9]+_init')})
    title_div_props = ('div', {'class': re.compile('entry-title hidden')})
    path_td_props = ('td', {'class': re.compile('shAll')})

    def parse_item(self, section):
        title_div = section.find(*self.title_div_props)
        path_td = section.find(*self.path_td_props)
        path = path_td.a['href']
        is_folder, video_id = self.detect_folder(path)
        item = {
            'title': title_div.string.strip(),
            'path': path,
            'is_folder': is_folder,
            'video_id': video_id,
        }
        return item


# Needs to be before VideoScraper
class VideoCategoryScraper(BaseScraper):
    path_matches = ('Videos_in_Kategorien', )
    subtree_props = ('div', {'class': 'lContent'})
    section_props = ('div', {'class': 'body floatLeft cGround sTLeft'})
    a_props = ('div', {'class': 'sCenter kTitle'})
    img_props = ('img', {'class': 'vThumb kThumb'})

    def parse_item(self, section):
        div = section.find(*self.a_props)
        if not div:
            log('Skipping item: %s' % section)
            return
        path = div.a['href']
        is_folder, video_id = self.detect_folder(path)
        item = {
            'title': div.a['title'] or div.a.string,
            'path': path,
            'is_folder': is_folder,
            'video_id': video_id,
        }
        if self.img_props:
            item['thumb'] = self.get_img(section)
        return item


class VideoScraper(BaseScraper):
    path_matches = ('Videos_A-Z', 'Videos_A-Z?', 'Neue_Musik_Videos')
    pagination_section_props = ('div', {'class': 'pViewBottom'})
    next_page_props = ('a', {'class': 'pView pnNext'})
    prev_page_props = ('a', {'class': 'pView pnBack'})
    subtree_props = ('div', {'class': 'lContent'})
    section_props = ('div', {'class': re.compile('entry-content')})
    a_props = ('a', {'class': 'vLink'})
    img_props = ('img', )
    duration_props = ('span', {'class': 'vViews'})
    author_props = ('span', {'class': 'nick'})
    date_props = ('div', {'class': re.compile('vAdded')})


# Needs to be BEFORE ShowOverviewScraper
class AllShowOverviewScraper(BaseScraper):
    path_matches = ('Serien/Alle_Serien_A-Z', )
    subtree_props = ('div', {'class': 'lContent'})
    section_props = ('div', {'class': 'lBox seriesDetail'})
    a_props = ('a', )
    img_props = ('img', {'class': 'vThumb'})
    needs_cookie = True

    def parse_item(self, section):
        previous_section = section.previousSibling
        path = previous_section.a['href']
        is_folder, video_id = self.detect_folder(path)
        item = {
            'title': unicode(previous_section.a.string),
            'path': path,
            'is_folder': is_folder,
            'video_id': video_id,
            'thumb': section.find(*self.img_props)['longdesc']
        }
        return item


class ShowOverviewScraper(BaseScraper):
    path_matches = ('Serien/', )
    subtree_props = ('div', {'class': 'lContent'})
    section_props = ('div', {'class': re.compile('series_member')})
    a_props = ('a', {'class': 'series_head'})
    img_props = ('img', {'class': 'vThumb'})
    # FIXME: Ganze-Folge property


class ShowCategoryScraper(BaseScraper):
    path_matches = ('Serien', )

    def parse(self, tree):
        sub_categories = [
            ('Top Episoden', 'Top_100/Top_100_Serien'),
            ('Alle Serien', '/Serien/Alle_Serien_A-Z'),
            ('  ProSieben', '/Serien/ProSieben'),
            ('  Sat 1', '/Serien/Sat_1'),
            ('  Anime TV', '/Serien/Anime_TV'),
            ('  kabel eins', '/Serien/kabel_eins'),
            ('  sixx', '/Serien/sixx'),
            ('  ProSieben MAXX', '/Serien/ProSieben_MAXX'),
            ('  YEP!', '/Serien/YEP'),
            ('  Sony Retro', '/Serien/Sony_Retro'),
            ('  Your Family Entertainment', '/Serien/Your_Family_Entertainment'),
            ('  BBC', '/Serien/BBC'),
            ('  Welt der Wunder', '/Serien/Welt_der_Wunder'),
            ('Weitere Serien', '/Serien/Weitere_Serien'),
        ]
        items = [{
            'title': title,
            'path': path,
            'is_folder': True,
            'video_id': None,
        } for title, path in sub_categories]
        return items, False, False


# Needs to be before MusicChannelScraper and VideoChannelScraper
class ChannelScraper(BaseScraper):
    path_matches = (
        'channel/', 'full_episodes',
        'mv_user_branded_content_box', 'highlight_clips'
    )

    def parse(self, tree):
        if tree.find(*MusicChannelScraper.subtree_props):
            self.log('Redirecting to scraper-class: MusicChannelScraper')
            return MusicChannelScraper().parse(tree)
        if tree.find(*SpecialVideoChannelScraper.subtree_props):
            self.log('Redirecting to scraper-class: SpecialVideoChannelScraper')
            return SpecialVideoChannelScraper().parse(tree)
        clips_found = tree.find(*VideoChannelClipScraper.subtree_props)
        full_found = tree.find(*VideoChannelFullScraper.subtree_props)
        if clips_found or full_found:
            self.log('Redirecting to scraper-class: VideoChannelFullScraper')
        if clips_found and full_found:
            self.log('Found clips and full episodes')
            if not self.extra_arg:
                items = [{
                    'title': 'Full Episodes',
                    'path': self.path + 'EXTRA_ARG=FULL',
                    'is_folder': True,
                    'video_id': None,
                }, {
                    'title': 'Clips',
                    'path': self.path + 'EXTRA_ARG=CLIPS',
                    'is_folder': True,
                    'video_id': None,
                }]
                return items, None, None
            elif self.extra_arg == 'FULL':
                return VideoChannelFullScraper().parse(tree)
            elif self.extra_arg == 'CLIPS':
                return VideoChannelClipScraper().parse(tree)
        elif clips_found:
            return VideoChannelClipScraper().parse(tree)
        elif full_found:
            return VideoChannelFullScraper().parse(tree)


class SpecialVideoChannelScraper(BaseScraper):
    a_prop_re = re.compile('is-video')
    section_re = re.compile('videolist--item')
    subtree_props = ('div', {'class': 'layout--module is-eyecatcher'})
    section_props = ('div', {'class': section_re})
    a_props = ('a', {'class': a_prop_re})
    img_props = ('img', {'class': 'thumbnail--pic'})


class VideoChannelClipScraper(BaseScraper):
    subtree_re = re.compile('chIDhighlight_clips')
    section_re = re.compile('highlight_clips')
    subtree_props = ('div', {'class': subtree_re})
    section_props = ('div', {'class': section_re})
    a_props = ('a', {'class': 'series_play'})
    img_props = ('img', {'class': 'vThumb'})
    duration_props = ('span', {'class': 'vViews'})
    pagination_section_props = ('div', {'class': subtree_re})
    next_page_props = ('a', {'class': 'pView pSmaller pnNext'})
    prev_page_props = ('a', {'class': 'pView pSmaller pnBack'})


class VideoChannelFullScraper(BaseScraper):
    subtree_re = re.compile('chIDfull_episodes')
    section_re = re.compile('full_episodes')
    subtree_props = ('div', {'class': subtree_re})
    section_props = ('div', {'class': section_re})
    a_props = ('a', {'class': 'series_play'})
    img_props = ('img', {'class': 'vThumb'})
    duration_props = ('span', {'class': 'vViews'})
    pagination_section_props = ('div', {'class': subtree_re})
    next_page_props = ('a', {'class': 'pView pSmaller pnNext'})
    prev_page_props = ('a', {'class': 'pView pSmaller pnBack'})


class MusicChannelScraper(BaseScraper):
    subtree_props = ('div', {'class': 'uBList'})
    section_props = ('div', {'class': 'uBItem'})
    a_props = ('a', {'class': 'uBTitle uBvTitle'})
    img_props = ('img', {'class': re.compile('uBThumb uBvThumb')})
    duration_props = ('span', {'class': 'vViews uBvViews'})
    pagination_section_props = ('table', {'class': 'pView floatRight'})
    next_page_props = ('a', {'class': 'pView pnNext'})
    prev_page_props = ('a', {'class': 'pView pnBack'})
    # FIXME: add clips


class MovieScraper(BaseScraper):
    path_matches = ('Filme/', 'filme_video_list')
    subtree_props = ('div', {'class': 'lContent lContFoot'})
    section_props = ('div', {'class': 'filme_entry'})
    a_plot_props = ('a', {'class': 'vLink'})
    div_title_props = ('div', {'class': 'lHead'})
    img_props = ('img', {'class': 'vThumb'})
    duration_props = ('span', {'class': 'vViews'})
    pagination_section_props = ('div', {'class': 'pView pViewBottom'})
    next_page_props = ('a', {'class': 'pView pnNext'})
    prev_page_props = ('a', {'class': 'pView pnBack'})
    # FIXME: add "filmeDetail"

    def parse_item(self, section):
        next_section = section.nextSibling
        div_title = next_section.find(*self.div_title_props)
        a_plot = section.find(*self.a_plot_props)
        path = a_plot['href']
        is_folder, video_id = self.detect_folder(path)
        item = {
            'title': div_title.string,
            'path': path,
            'description': a_plot['title'],
            'is_folder': is_folder,
            'video_id': video_id,
            'thumb': section.find(*self.img_props)['src']
        }
        return item


class MovieCategoryScraper(BaseScraper):
    path_matches = ('Filme', )

    def parse(self, tree):
        sub_categories = [
            ('Top Filme', 'Top_100/Top_100_Filme'),
            ('Neuste Filme', '/Videos_A-Z?searchChannelID=369&searchChannel=Film'),
            ('  Comedy', '/Filme/Comedy'),
            ('  Action', '/Filme/Action'),
            ('  Horror', '/Filme/Horror'),
            ('  Sci-Fi', '/Filme/Sci-Fi'),
            ('  Thriller', '/Filme/Thriller'),
            ('  Drama', '/Filme/Drama'),
            ('  Western', '/Filme/Western'),
            ('  Dokumentation', '/Filme/Dokumentation'),
            ('  Konzerte', '/Filme/Konzerte'),
            ('Alle Filme', '/Filme/Alle_Filme'),
        ]
        items = [{
            'title': title,
            'path': path,
            'is_folder': True,
            'video_id': None,
        } for title, path in sub_categories]
        return items, False, False


# Needs to be before ArtistOverviewLetterScraper
class ArtistOverviewScraper(BaseScraper):
    path_matches = ('Musik_K%C3%BCnstler?lpage', )
    subtree_props = ('div', {'class': 'lBox mLeftBox music_channels'})
    section_props = ('div', {'class': 'body floatLeft sTLeft'})
    a_props = ('a', {'class': 'pPrTitle'})
    img_props = ('div', {'class': 'pChThumb pPrThumb'})

    def get_img(self, section):
        img = section.find(*self.img_props)
        if img and img.find('img'):
            img = img.find('img')
            return img.get('longdesc') or img.get('src')
        else:
            self.log('Error in get_img!')


# Needs to be before MusicScraper
class ArtistOverviewLetterScraper(BaseScraper):
    path_matches = ('Musik_K%C3%Bcnstler', )

    def parse(self, tree):
        p = 'Musik/Musik_K%C3%BCnstler?lpage='
        letters = (
            '0-9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
            'L', 'M', 'N', 'O', 'P-R', 'S', 'T', 'U-Z'
        )
        return [{
            'title': s,
            'path': p + str(i),
            'is_folder': True,
        } for i, s in enumerate(letters)], None, None


class MusicScraper(BaseScraper):
    path_matches = ('Musik/', 'music_videos')
    pagination_section_props = ('div', {'class': 'pViewBottom'})
    next_page_props = ('a', {'class': 'pView pSmaller pnNext'})
    prev_page_props = ('a', {'class': 'pView pSmaller pnBack'})
    subtree_props = ('div', {'class': 'lContent'})
    section_props = ('div', {'class': 'floatLeft fRand'})
    a_props = ('a', {'target': '_top'})
    img_props = ('img', )
    duration_props = ('span', {'class': 'vViews'})
    author_props = ('span', {'class': 'nick'})
    date_props = ('div', {'class': re.compile('vAdded')})


class MusicCategoryScraper(BaseScraper):
    path_matches = ('Musik', )

    def parse(self, tree):
        sub_categories = [
            ('Charts', '/Top_100/Top_100_Single_Charts'),
            ('Neue Musik Videos', '/Musik/Neue_Musik_Videos'),
            ('  Rock', '/Musik/Rock'),
            ('  Pop', '/Musik/Pop'),
            ('  Rap/R&B', '/Musik/Rap/R%26B'),
            ('  Schlager', '/Musik/Neue_Musik_Videos?searchChannelID=206&amp;searchChannel=Schlager'),
            ('  Electro', '/Musik/Neue_Musik_Videos?searchChannelID=205&amp;searchChannel=Electro'),
            ('  Metal', '/Musik/Neue_Musik_Videos?searchChannelID=204&amp;searchChannel=Metal'),
            ('  RnB', '/Musik/Neue_Musik_Videos?searchChannelID=207&amp;searchChannel=RnB'),
            ('Musik Kuenstler', '/Musik/Musik_K%C3%Bcnstler'),
        ]
        items = [{
            'title': title,
            'path': path,
            'is_folder': True,
            'video_id': None,
        } for title, path in sub_categories]
        return items, False, False


def get_path(path):
    log('get_path started with path: %s' % path)
    scraper = BaseScraper.choose_scraper(path)
    if not scraper:
        raise NotImplementedError
    log('Found matching scraper-class: %s' % scraper.__class__.__name__)
    tree = scraper.get_tree(path)
    return scraper.parse(tree)


def get_video(video_id):
    log('get_video started with video_id: %s' % video_id)
    r_adv = re.compile('var flashvars={(.+?)}')
    r_adv_p = re.compile('(.+?):\'(.+?)\',?')
    r_swf = re.compile('swfobject.embedSWF\(\'(.+?)\'')
    r_rtmpurl = re.compile('connectionurl=\'(.*?)\'')
    r_playpath = re.compile('source=\'(.*?)\'')
    r_path = re.compile('path=\'(.*?)\'')
    r_title = re.compile("<h1(?: class='globalHd')?>(.*?)</h1>")
    video = {}
    params = {}
    encxml = ''
    videopage_url = MAIN_URL + 'watch/%s/' % video_id
    html = requester.get_url(videopage_url, MAIN_URL)
    video['title'] = re.search(r_title, html).group(1)
    sec = re.search(r_adv, html).group(1)
    for (a, b) in re.findall(r_adv_p, sec):
        if not a == '_encxml':
            params[a] = b
        else:
            encxml = unquote(b)
    if not params.get('domain'):
        params['domain'] = 'www.myvideo.de'
    xmldata_url = '%s?%s' % (encxml, urlencode(params))
    if 'flash_playertype=MTV' in xmldata_url:
        log('get_video avoiding MTV player')
        xmldata_url = (
            'http://www.myvideo.de/dynamic/get_player_video_xml.php'
            '?flash_playertype=D&ID=%s&_countlimit=4&autorun=yes'
        ) % video_id
    enc_data = requester.get_url(xmldata_url, videopage_url).split('=')[1]
    enc_data_b = unhexlify(enc_data)
    sk = __md5(b64decode(b64decode(GK)) + __md5(str(video_id)))
    dec_data = __rc4crypt(enc_data_b, sk)
    print repr(dec_data)
    rtmpurl = re.search(r_rtmpurl, dec_data).group(1)
    video['rtmpurl'] = unquote(rtmpurl)
    video['rtmpurl'] = video['rtmpurl'].replace('rtmpe://', 'rtmp://')
    playpath = re.search(r_playpath, dec_data).group(1)
    video['file'] = unquote(playpath)
    m_filepath = re.search(r_path, dec_data)
    video['filepath'] = m_filepath.group(1)
    if not video['file'].endswith('f4m'):
        ppath, prefix = unquote(playpath).split('.')
        video['playpath'] = '%s:%s' % (prefix, ppath)
    else:
        video['hls_playlist'] = (
            video['filepath'] + video['file']
        ).replace('.f4m', '.m3u8')
    swfobj = re.search(r_swf, html).group(1)
    video['swfobj'] = unquote(swfobj)
    video['pageurl'] = videopage_url
    return video


class SessionRequester(object):

    def __init__(self):
        self.cookie = None

    def get_tree(self, url, referer=MAIN_URL, needs_cookie=False):
        if needs_cookie and not self.cookie:
            # do a useless request to get a cookie...
            self.get_url(MAIN_URL)
        html = self.get_url(url, referer)
        html = html.decode('utf-8', 'ignore')  # Fix MyVideo.de bad enc
        tree = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
        return tree

    def get_url(self, url, referer=MAIN_URL):
        url = url.replace('.de//', '.de/')  # FIXME
        log('SessionRequester.get_url opening url: %s' % url)
        request = Request(url)
        headers = [
            ('Accept', ('text/html,application/xhtml+xml,'
                        'application/xml;q=0.9,*/*;q=0.8')),
            ('User-Agent', ('Mozilla/5.0 (Windows NT 6.1; WOW64) '
                            'AppleWebKit/537.36 (KHTML, like Gecko) '
                            'Chrome/27.0.1453.15 Safari/537.36')),
            ('Accept-Language', 'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4'),
        ]
        for header in headers:
            request.add_header(*header)
        if referer:
            request.add_header('Referer', referer)
        if self.cookie:
            request.add_header('Cookie', self.cookie)
        try:
            response = urlopen(request)
            if response.headers.get('Set-Cookie'):
                self.cookie = response.headers.get('Set-Cookie')
                log('SessionRequester.get_url got a cookie:%s' % self.cookie)
            html = response.read()
        except HTTPError, error:
            raise NetworkError('HTTPError: %s' % error)
        except URLError, error:
            raise NetworkError('URLError: %s' % error)
        log('SessionRequester.get_url got %d bytes' % len(html))
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


def log(msg):
    print('MyVideo.de scraper: %s' % msg)


requester = SessionRequester()

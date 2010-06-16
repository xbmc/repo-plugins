#api_nrk.py
#
# NRK plugin for XBMC Media center
# Copyright (C) 2009 Victor Vikene  contact: z0py3r@hotmail.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#

import os
import re
import sys
import xbmc
from utils import Key, Plugin, decode_htmlentities
from urllib import quote_plus, unquote_plus
from connection_manager import DataHandle, Session

#
#  Define constants:
# --------------------------------------------------------
# Used to determine state in instance and reference within
# regular expression results
#

SHOW          = 'prosjekt';     SHOW_CLIP        = 'klipp'
SHOW_FOLDER   = 'kategori';     SHOW_CLIP_INDEX  = 'indeks'
PLAYLIST      = 'spilleliste';  PLAYLIST_ITEM    = 'spillefil'
PLAYLIST_CLIP = 'verdi';        PLAYLIST_VIGNETE = 'vignett'
PLAYLIST_ALT_CLIP = 'spill'

PROGRAM = 'program';  VIGNETE  = 'vignett';  
SEARCH  = 'search';   ROOT     = 'root'
CHANNELS = 'kanalene'

# Views are both identifiers for instance and for some views
# in the web api
TOP_THIS_MONTH = 'msManed';   BY_THEME = 'theme'
TOP_THIS_WEEK  = 'msUke';     VIEW_ALL = 'visalle'
TOP_TOTAL      = 'msTotalt';  BY_CHAR  = 'letter'
RELEVANT       = 'aktuelt';   PROGRAM  = 'program'
LIVE           = 'direkte';   ARCHIVE  = 'arkiv'
RECOMMENDED    = 'recommended'
TOP_BY_INPUT   = 'topbyinput' 
ARTICLES       = 'articles'

#Playlists
SPORT = 'sport';  NEWS = 'nyheter';  SUPER = 'super'
NATURE = 'natur'; REGION = 'distrikt'

# Contents
FILES   = 'files';    MOVIES      = 'movies'
SONGS   = 'songs';    TVSHOWS     = 'tvshows'
ARTISTS = 'artists';  EPISODES    = 'episodes'
ALBUMS  = 'albums';   MUSICVIDEOS = 'musicvideos'

# others..
REGION = 'distrikt';  ENCODING = 'iso-8859-1'

# Connection speed
CONNECTION_SPEED_LOW    =  400   #bitrate: 300 kbps
CONNECTION_SPEED_MEDIUM =  800   #bitrate: 650 kbps
CONNECTION_SPEED_HIGH   =  1200  #bitrate: 900 kbps

rpath = os.path.join(os.getcwd(), 'resources', 'images')
speed = CONNECTION_SPEED_LOW

NDMR = 'ndmr'; NDHO = 'ndho'; NDNO = 'ndno'; NDRO = 'ndro'
NDSF = 'ndsf'; NDSL = 'ndsl'; NDTL = 'ndtl'; NDTT = 'ndtt'
NDOS = 'ndos'; NDOA = 'ndoa'; NDOP = 'ndop'

region_abbr = {
        NDMR: 'more_og_romsdal', NDHO: 'hordaland', 
        NDNO: 'nordnorge',       NDRO: 'rogaland', 
        NDSF: 'sognogfjordane',  NDSL: 'sorlandet',
        NDTL: 'trondelag',       NDTT: 'ostafjells',
        NDOS: 'ostfold',         NDOA: 'ostlandssendigen',
        NDOP: 'oppland'
    }

# shortcuts    
lang = sys.modules[ "__main__" ].__language__


def seconds_to_hms(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return h,m,s
# - EOM -

        
class Api:
    
    def __set_dataman(self, cache):
        self.dman = DataHandle(cache)
        self.dman.default_encoding = ENCODING
    # - EOM -
    
    def __init__(self, speed, cache):
        self.__set_dataman(cache)
        self.speed = speed

    @staticmethod
    def _merge_playlists(cat, xml):
        mcount = 0
        icount = 0
        for i in xml:
            if i.key.type == PLAYLIST_VIGNETE:
                i.thumbnail = Plugin.image('news.png')  
            elif i.key.type == PLAYLIST_ITEM:
                mcount -= 1
                try:
                    xml[icount].thumbnail = cat[mcount].thumbnail
                    xml[icount].plot = cat[mcount].plot
                except IndexError:
                    pass
            icount += 1
        return xml
    
    
    def _get_intro(self, id, arg=None):
        if True == True:
        
            if   id == REGION: name = NEWS;   img = 'news.png'
            elif id == NEWS:   name = NEWS;   img = 'news.png'
            elif id == SPORT:  name = SPORT;  img = 'sport.png'
            elif id == SUPER:  name = SUPER;  img = 'kids.png'
            elif id == NATURE: name = NATURE; img = 'ntur.png'
            else: 
                name = NEWS; img = 'news.png'
                
            title = '%s %s' % (name, 'hovedvignett')
            img = Plugin.image(img)
            key = Key('new', type=PLAYLIST_VIGNETE)
            istart = MediaObj(title=title, thumbnail=img, key=key)
            istart.isPlayable = True; istart.isFolder = False
            istart.url = Plugin.videopath(name + '_intro_main.avi')
            
            title = '%s %s' % (name, 'vignett')
            key = Key('new', type=PLAYLIST_VIGNETE)
            imid = MediaObj(title=title, thumbnail=img, key=key)
            imid.isPlayable = True; imid.isFolder = False
            imid.url = Plugin.videopath(name + '_intro.avi')
            
            return istart, imid, istart
            
        else:    
            url = uri.playlist(loop=id, type=arg)
            data = self.dman.get_data(url)
            if data:
                tmp_list = extract.playlist(data)
                return tmp_list[0], tmp_list[2], tmp_list[-1]
                
                
    def get_all_shows(self):
        url = uri.live_content(BY_CHAR, '@')
        data = self.dman.get_data(url)
        if data:
            return extract.catalog(data)
    
    
    def get_live_shows(self):
        url = uri.live_content()
        data = self.dman.get_data(url, cache=False)
        shows = extract.catalog(data, parent=LIVE, ext=extract.ext_live_show)
        return shows
    

        
    def get_shows_by_theme(self, id):
        url = uri.live_content(BY_THEME, id)
        data = self.dman.get_data(url)
        if data:
            return extract.catalog(data)
        
        
    def get_shows_by_character(self, char):
        url = uri.live_content(BY_CHAR, char)
        data = self.dman.get_data(url)
        if data:
            return extract.catalog(data)
        
    
    def get_show(self, id, type):
        url  = uri.menu_fragment(id, type)
        data = self.dman.get_data(url)
        return extract.show(data)
    
    
    def get_most_viewed_shows(self, days):
        url = uri.most_viewed(days)
        data = self.dman.get_data(url)
        return extract.catalog(data, ext=extract.ext_top_shows)
        
        
    def get_show_clip(self, id, parent=None, abs=True):
        url  = uri.media_xml(id, self.speed)
        data = self.dman.get_data(url, persistent = True)      
        item = extract.show_clip(data)
        
        if abs == True:
            url  = uri.mms_to_http(item.url)
            data = self.dman.get_data(url)
            item.url = extract.mms_url(data)
        item.id = id
        
        return item

        
        
    def get_search_result(self, sstr, page):
        url = uri.search(search=sstr, page=page)
        data = self.dman.get_data(url)
        if data:
            return extract.search(data)
        
        
    def get_viewstate(self, ident):
        url = uri.subpath(ident)
        data = self.dman.get_data(url)
        if data:
            return extract.viewstate(data)
        
    
    def get_playlist_item(self, id):
        url = uri.playlist(story=id)
        data = self.dman.get_data(url)
        if data:
            return extract.playlist(data)[0]
            
            
    def get_playlist(self, ident, type=None):
    
        if ident == 'distrikt':
            type = region_abbr[type]
            
        headers   = uri.xmsheader; headers.update(uri.baseheaders)
        viewstate = self.get_viewstate(ident)
        
        if not viewstate:
            return
            
        form = uri.build_form(ident, viewstate, cat=type)
        url  = uri.subpath(ident)
        data = self.dman.get_data(url, 'POST', form, headers)
        pcat = extract.catalog(data, type); pcat.reverse()
        url  = uri.playlist(loop=ident, type=type)
        data = self.dman.get_data(url)
        pxml = extract.playlist(data, vignetes=False)
        siv, miv, eiv = self._get_intro(ident, type)
        pxml = self.inject_vignetes(pxml, siv, miv, eiv)
        
        return self._merge_playlists(pcat, pxml)
        
        
    def get_playlist_from_view(self, id, view, subcat):
        headers = uri.xmsheader
        headers.update(uri.baseheaders)
        
        vstate = self.get_viewstate(id)
        form   = uri.build_form(id, vstate, view, subcat)
        url    = uri.subpath(id)
        data   = self.dman.get_data(url, 'POST', form, headers)
        
        if view == PROGRAM:
            return extract.show(data)
        else:
            siv, miv, eiv = self._get_intro(id, subcat)
            catalog = extract.catalog(data)
            catalog = self.inject_vignetes(catalog, siv, miv, eiv)
            return catalog   
           
           
    def inject_vignetes(self, catalog, siv, miv, eiv):
        catalog.insert(0, siv); 
        count = 0; total = len(catalog)
        
        for i in range(0, total):
            count += 1
            if count % 2 == 0: 
                if count < total - 1:
                    catalog.insert(count, miv)
        catalog.append(eiv)
        
        return catalog
        
        
    def get_subtitles(self, id):
        url  = uri.super_xml(id)
        data = self.dman.get_data(url)
        subs = extract.subtitles(data)
        subs = convert.sub_to_srt(subs)
        return subs
    
    
    def get_video_id(self, index_id):
        url   = uri.subpath(SHOW_CLIP_INDEX, str(index_id))
        heads = uri.cookieheader; heads.update(uri.baseheaders)
        data  = self.dman.get_data(url, headers=headers)
        return extract.video_id(data)
    # - EOM -
        
        
    def get_path(self, id, type):
        url  = uri.path_fragment(id, type)
        data = self.dman.get_data(url)
        path = extract.current_path(data)
        print 'Current path: %s' % path.encode('ascii', 'replace')
        return path
 
    
    def get_recommended_shows(self):    
        url   = uri.subpath()
        heads = uri.cookieheader; heads.update(uri.baseheaders)
        data  = self.dman.get_data(url, headers=heads)
        return extract.recommended(data)
    
    def get_articles(self):    
        url   = uri.subpath()
        heads = uri.cookieheader; heads.update(uri.baseheaders)
        data  = self.dman.get_data(url, headers=heads)
        return extract.articles(data)    
        
        
        
class convert:

    @staticmethod
    def sub_to_srt(subtitle):
        scount = 0; scont = ''
        
        for s in subtitle:
            #Create srt subtitle format
            scount += 1; seconds = s[0]; texting = s[1]
            h_start, m_start, s_start = seconds_to_hms(seconds)
            h_end,   m_end,   s_end   = seconds_to_hms(seconds + 4)
            
            sub = ('%d\n%02d:%02d:%02d,000 --> ' +
                            '%02d:%02d:%02d,000\n<b>%s</b>\n\n') % (
                                sub_counter,
                            #HH:MM:SS,fff start
                            h_start, m_start, s_start,
                        #HH:MM:SS,fff end
                        h_end, m_end, s_end,
                    texting
                ) 
            scont += sub
        
        return scont

        
        
class uri:
    
    baseurl = 'http://www1.nrk.no/nett-tv'
        
    #Map some translations for condition testing
    #within the project section
    lang_trans = {
            SHOW_FOLDER: 'category', SHOW_CLIP: 'broadcast', SHOW: 'project'
        }
        
    @staticmethod
    def search(search, sort='date', page=1, max=1):
        path  = '/DynamiskLaster.aspx'; search = quote_plus(search)
        query = '?SearchResultList$search:%s|sort:%s|page:%d|max:%d'
        query = query % ( search, sort, page, max)
        
        return ''.join(( uri.baseurl, path, query ))

        
    @staticmethod    
    def live_content(view=None, param=None):
        path  = '/DynamiskLaster.aspx'; query = '?LiveContent$%s:%s'
        
        if not view and not param:
            return ''.join(( uri.baseurl, path, '?LiveContent' ))
        else:
            query = query % ( str(view), str(param) )
            return ''.join(( uri.baseurl, path, query ))

        
    @staticmethod
    def menu_fragment(id, type, showRoot=True):
        #Swap between norwegian and english
        if uri.lang_trans[type]: type = uri.lang_trans[type]
            
        path  = '/menyfragment.aspx'; sr = str(showRoot).lower()
        query = '?type=%s&id=%s&showroot=%s' % (type, id, sr)
        return uri.baseurl + path + query 

        
    @staticmethod    
    def path_fragment(id, type=''):
        path  = '/stifragment.aspx'; query = '?id=%s&type=%s' % (id, type)
        return ''.join(( uri.baseurl + path + query ))
        
        
    @staticmethod
    def most_viewed(days):
        path = '/ml/topp12.aspx';  query = '?dager=%d' % days
        return ''.join(( uri.baseurl, path, query ))

        
    @staticmethod
    def playlist(loop=None, type=None, story=None):
        path = '/spilleliste.ashx'; query = '?'
        
        if loop is not None: query += 'loop=%s&' % str(loop)
        if type is not None: query += 'type=%s&' % str(type)
        if story is not None: query += 'story=%d&' % int(story)
            
        return uri.baseurl + path + query

        
    @staticmethod
    def media_xml(id, speed, showsuper=True):
        path = '/silverlight/getmediaxml.ashx'; ss = str(showsuper).lower()
        query = '?id=%s&hastighet=%d&vissuper=%s' % (id, speed, ss)
        
        return uri.baseurl + path + query 
        
    
    @staticmethod
    def super_xml(id):
        path = '/silverlight/getsuperxml.ashx?id=%s'
        return uri.baseurl + path % id
        
        
    @staticmethod
    def subpath(*args):
        """ Just a wrap up to keep the code cleaner"""
        path = '/'.join(args)
        return '/'.join((uri.baseurl, path,))
    
    
    @staticmethod    
    def content_image(name, ext):
        """ Return a template for a alternate image path. This is used
            cause of xbmc's handling of images without extension
        """
        
        template = "http://fil.nrk.no/contentfile/file/1.%s!img%s.%s"
        return template % (name,name, ext)
        
        
    @staticmethod
    def mms_to_http(url):
        """ Swaps a mms scheme to a http scheme. Used for extracting 
            the correct url to pass to the player
        """
        return url.replace('mms://', 'http://')
    # - EOM -
    
    
    @staticmethod
    def http_to_mms(url):
        """ Swaps a http scheme to a mms scheme."""
        return url.replace('http://', 'mms://')
    # - EOM -
    
    
    @staticmethod
    def build_form(id, viewstate, view='aktuelt', cat=''):
        return (
                'ctl00$scriptManager1=' +
                'ctl00$contentPlaceHolder$loopPanel' +
                '|ctl00$contentPlaceHolder$asyncPBTrigger_loop_%s' +
                '&__EVENTTARGET=ctl00$contentPlaceHolder' +
                '$asyncPBTrigger_loop_%s' + 		
                '&__VIEWSTATE=%s&ctl00$contentPlaceHolder$mainCat=%s'
                '&ctl00$contentPlaceHolder$subCat=%s&'
            ) % ( view, view, quote_plus(viewstate), id.capitalize(), cat)
    # - EOM -
    
    
    xmsheader = {'X-MicrosoftAjax': 'Delta=true'}
    
    cookieheader = { 'Cookie': ('NetTV2.0Speed=NetTV2.0Speed=%s; ' +
                     'UseSilverlight=UseSilverlight=1') % speed  }
                       
    baseheaders = {
		'Content-Type': ('application/x-www-form-urlencoded; charset=UTF-8'),
		'User-Agent': ('Mozilla/5.0 (Windows; U; WindowsNT 5.1; ' +
						'nb-NO; rv:1.9.0.11) Gecko/2009060215 ' +
						'Firefox/3.0.11'),
		'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
		#'Accept-Encoding': 'gzip,deflate',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
	}
    
    
    
    
class regex:

    show = r"""(?sx)
                    <li\sclass="(?P<exp>(?:expand|noexpand))"\s
                    id="(?:child|root)[0-9]+?">
                    .*?<a\shref="/nett-tv/(?:kategori|klipp)/
                    (?P<id>[0-9]*)".+?title="(?P<plot>.*?)"\s
                    class="icon-(?P<type>folder|sound|video)
                    -black.*?>(?P<title>.*?)</a>
                """
                
    catalog = r"""(?sx)
                    ref.+?(?:(?P<plref>\w+?)/spill)?      #parent idx: 0
                    /(?P<type>\w+?)/                      #type   idx: 1
                    (?P<id>\d{2,}).+?                     #ident  idx: 2
                    src="(?P<image>.+?)".+?               #img    idx: 3
                    <a.+?>(?P<title>.*?)</.+?             #title  idx: 4
                    <a.+?>(?P<plot>.*?)<                  #desc   idx: 5
                """
    
    recommended   = r"""(?sx)
                    <div\sclass="intro-element\sintro-element-small">.*?
                    <a\shref="/nett-tv/(?P<type>klipp)/(?P<id>.*?)".*?
                    title="(?P<plot>.*?)">.*?<img\ssrc="(?P<image>.*?)".*?/>.*?
                    </a>.*?<div\sclass="intro-element-content">
                    <h2><a\shref="/nett-tv/klipp/.*?".*?>(?P<title>.*?)</a></h2>
                    """
    
    articles      = r"""(?sx)
                    <div\sclass="intro-element">.*?
                    <div.*?>.*?<a.*?>.*?<img.*?src="(?P<image>.*?)".*?>.*?
                    <h2>.*?<a.*?href="(?P<url>.*?)".*?>(?P<title>.*?)</a>.*?
                    <a.*?>(?P<plot>.*?)</a>
                    """
                    
    show_clip_xml = r"""(?sx)
                    <mediadefinition>.*?
                    <title>(?P<title>.*?)</title>.*?       #title idx: 0
                    <desc(?:ription>(?P<plot>.*?)          #plot  idx: 1
                    </desc.+?)?.*?
                    <mediaurl>(?P<url>.*?)</mediaurl>.*?   #url   idx: 2
                    <imageurl>(?P<image>.*?)</imageurl>.*? #img   idx: 3
                    <supringurl(?:>(?P<suburl>.*?)         #subt  idx: 4
                    </supringurl>)?.*?
                    <chapters(?:>(?P<chapters>.*?)         #chapt idx: 5
                    </chapters>)?.*?
                    </mediadefinition>
                """
                
    show_clip_index = r"""(?sx)
                    <chapteritem>.*?
                    <title>(?P<title>.+?)</title>.*?
                    <timeindex>(?P<time>\d+)</timeindex>.*?
                    <image(?:url>(?P<image>.*?)
                    </image.+?)?.*?
                    </chapteritem>
                """
                
    playlist_xml = r"""(?sx)
                    <item>.*?<title>-{0,1}(?P<title>.*?)</title>.*?
                    <media:content\surl="(?P<url>.*?)"\s
                    type="(?P<type>.*?)"\s/>.*?</item>
                """
    
    search     = r"""(?sx)
                    <li.+?ref.+?(?:(?P<plref>\w+?)/spill)?/(?P<type>\w+?)
                    /(?P<id>\d{2,}).+?>(?P<title>.*?)</a>.*?
                    <div.+?>(?P<plot>.*?)</div>
                """
    
    clip_index = r"""(?sx)
                    Player.+?xml.+?id=(?P<id>\d+).+?
                    \.seekTo\((?P<time>\d+)\)
                """

    qbrick         = r"""(?sx)href="(?P<url>.*?)"/"""
    viewstate      = r""""__VIEWSTATE".+?value="(?P<vstate>/.*?)".+?/"""
    image_identity = r"""crop/(?:\d\.(?P<id>\d*)(?:\.\d*)?)"""
    path_fragment  = r"""<a.+?>(?P<path>.*?)<.+?/li>"""
    show_subtitles = r"""text="(?P<text>.*?)".+?marker="(?P<marker>.*?)"."""
    

class extract:

    @staticmethod
    def search(data):
        search = []
        #Iterate through the search result and append to stack
        for m in re.finditer(regex.search, data):
            item = MediaObj()
            type = m.group('type').encode('ascii')
            item.key = Key(type=type, id=m.group('id'))

            if item.key.type == SHOW_CLIP_INDEX:
                item.icon = video_index_icon
                item.isPlayable = True
            elif item.key.type == SHOW_CLIP:
                item.icon = video_icon
                item.isPlayable = True
            
            item.title = m.group('title')
            item.plot = m.group('plot')
            
            search.append(item)
        return search
        
         
    @staticmethod
    def catalog(data, arg=None, parent=None, ext=None):
        istack = []
        for m in re.finditer(regex.catalog, data):	
            item = MediaObj()
            item.plot = m.group('plot')
            item.title = m.group('title')
            item.thumbnail = m.group('image').encode('ascii', 'ignore')
            #State identifiers
            item.key = Key()
            item.key.id = int(m.group('id'))
            if arg:
                item.key.arg = arg
            if parent:
                item.key.parent = parent
            item.key.type = m.group('type').encode('ascii', 'ignore')
            if ext:
                item = ext(item)
            istack.append(item)
        return istack
    # - EOM -
    
    
    @staticmethod
    def recommended(data):
        istack = []
        for m in re.finditer(regex.recommended, data):	
            item = MediaObj()
            plot = m.group('plot').decode('iso-8859-1')
            item.plot =  decode_htmlentities( plot ) 
            item.title =  m.group('title') 
            item.thumbnail = m.group('image').encode('ascii', 'ignore')
            #State identifiers
            item.key = Key()
            item.key.id = int(m.group('id'))
            item.key.type = m.group('type').encode('ascii', 'ignore')
            istack.append(item)
        return istack
    # - EOM -
    
    
    @staticmethod
    def articles(data):
        istack = []
        for m in re.finditer(regex.recommended, data):	
            item = MediaObj()
            plot = m.group('plot').decode('iso-8859-1')
            item.plot =  decode_htmlentities( plot ) 
            item.title =  m.group('title') 
            item.thumbnail = m.group('image').encode('ascii', 'ignore')
            #State identifiers
            item.key = Key()
            item.key.id = int(m.group('id'))
            item.key.type = m.group('type').encode('ascii', 'ignore')
            istack.append(item)
        return istack
    # - EOM -
    
    
    @staticmethod
    def ext_live_show(item):
        item.starts = item.plot[0:5]
        item.title += ' - starter ' + item.starts
        return item
    
    @staticmethod
    def ext_top_shows(item):
        item.views = item.plot
        item.title += ' - ' + item.views
        return item
        
    @staticmethod
    def show(data):
        istack = []
        for m in re.finditer(regex.show, data):
            item = MediaObj()
            item.title = m.group('title')
            item.plot = m.group('plot')

            if m.group('type') == 'folder':
                item.defntion = 'katalog'
                type = SHOW_FOLDER
                item.icon = folder_icon
                
            elif m.group('type') == 'sound':
                item.defntion = 'lyd/wma'
                item.icon = sound_icon
                
            elif m.group('type') == 'video':
                item.defntion = 'video/wmv'
                item.icon = sound_icon
                
            if m.group('type') == 'video' or m.group('type') == 'sound':
                item.isPlayable = True
                type = SHOW_CLIP
            
            item.key = Key()
            item.key.type = type
            item.key.id = int(m.group('id'))
            if m.group('exp') == 'noexpand' and item.key.type == SHOW_FOLDER:
                continue
            istack.append(item)
        return istack
    # - EOM -
    
    
    
    @staticmethod
    def show_clip(data):
        match = re.search(regex.show_clip_xml, data)

        item = MediaObj()
        item.url = unicode(match.group('url'), 'utf-8')
        print item.url
        if item.url.lower().endswith('wma'):
            item.defntion = 'lyd/wma'
        elif item.url.lower().endswith('wmv'):
            item.defntion = 'video/wma'
            item.icon = video_icon
        item.plot = match.group('plot')
        item.title = match.group('title')
        item.thumbnail = match.group('image')
        item.subtitle = match.group('suburl')
        item.chapters = match.group('chapters')
        return item
    # - EOM -
    
    
    
    @staticmethod
    def chapters(cstring):
        
        clist = []
        for chapter in re.findall(nrk.regex.show_clip_index, cstring):
            citem = MediaObj(title = chapter[0], time = chapter[1])
            if chapter[2]:
                citem.thumbnail = chapter[2]
            citem.thumbnail = nrk.video_index_icon
            citem.key = Key(type = SHOW_CLIP_INDEX)
            clist.append(citem)
        
        return clist
    # - EOM -
    
    
    @staticmethod
    def playlist(data, vignetes=True):
        plist = []
        for match in re.finditer(regex.playlist_xml, data):
            item = MediaObj()
            item.url = match.group('url').replace('&amp;', '&')
            item.title = match.group('title')
            #item.defntion = match.group('type')
            item.defntion = 'video/mp4'
            item.isFolder = False
            item.isPlayable = True
            item.key = Key()
            if item.title.endswith(PLAYLIST_VIGNETE):
                item.key.type = PLAYLIST_VIGNETE
            else:
                item.key.type = PLAYLIST_ITEM 
                
            if item.key.type == PLAYLIST_VIGNETE and vignetes == False:
                continue
            else:
                plist.append(item)
            
        return plist
    # - EOM -

    
    @staticmethod
    def viewstate(data):
        match = re.search(regex.viewstate, data)
        print 'Found viewstate %s' % match.group('vstate')
        return match.group('vstate')
    # - EOM -
    

    @staticmethod
    def mms_url(data):
        nurl = ''
        print data
        
        #Do a check for qbrick playlist
        if data.startswith('<asx'):
            match = re.search(regex.qbrick, data)
            try:
                nurl = match.group('url')
            except:
                nurl = ""
        else:
            for c in data[18:]:
                if c != '\r':
                    nurl += c
                else: break
            nurl = nurl.replace('http', 'mms')
        return nurl
    # - EOM -
    
    
    @staticmethod
    def current_path(data):
        path = []
        for match in re.finditer(regex.path_fragment,data):
            path.append(match.group('path'))
        path = ' - '.join(path)
        return path
    # - EOM -

    
    @staticmethod
    def video_id(data):
        match = re.search(regex.clip_index, data)
        try:
            info = match.group('id'), float(match.group('time'))
        except:
            pass
        else:
            return info
    # - EOM -
    
    
    @staticmethod
    def subtitles(data):
        sub = []
        for m in re.finditer(regex.show_subtitles, data):
            append( (int(m.group('marker')), m.group('text')) )
        return sub
    
    



class BaseObj:

    def __getattr__(self, name):
        return None
    # - EOM -
        
    def update(self, other):
        self.__dict__.update(other.__dict__)


class MediaObj(BaseObj):

    def __init__( self,*args, **kwargs ):  
        self.plot =''
        self.title     = ''
        self.defntion  = ''
        self.thumbnail = ''
        self.isFolder  = True
        
        for key in kwargs:
            self.__dict__[key] = kwargs[key]


feed_alt_icon  = os.path.join(rpath, 'rss-alt-icon.png')
video_icon     = os.path.join(rpath, 'video-icon.png')
sound_icon     = os.path.join(rpath, 'sound-icon.png')
folder_icon    = 'defaultFolder.png'
video_index_icon  = os.path.join(rpath, 'video-index-icon.png')
default_playlist_icon = os.path.join(rpath, 'news.png')


class PlaylistView:
    
    views = {
            ARCHIVE: (lang(30200),   'archive-icon.png', ), 
            RELEVANT: (lang(30201), 'news-icon.png', ), 
            TOP_TOTAL: (lang(30202), 'stats-icon.png', ), 
            TOP_THIS_WEEK: (lang(30203),   'stats-icon.png', ), 
            TOP_THIS_MONTH: (lang(30204), 'stats-icon.png', ) 
        }
    
    def __init__(self, parent):
        self.parent = parent
        
    def __getattr__(self, key):
        if self.views.has_key(key):
            lbl, ico = self.views[key]
            ico = os.path.join( rpath, ico )
            vkey = Key(
                    type = PLAYLIST, id = self.parent.id, 
                    view = key, arg = self.parent.arg
                )
            return MediaObj(key=vkey, title=lbl, thumbnail=ico)


class Playlist:
    entries = {
        REGION: ( 'Distrikt', 'regions-icon.png',
                (ARCHIVE, RELEVANT, TOP_TOTAL, TOP_THIS_WEEK, TOP_THIS_MONTH)
            )
        }
            
            
            
            
class views:
    

    search = MediaObj(
                #title = 'Sok', 
                title = lang(30205),
                defntion = 'folder/perspektiv',
                isFolder = True,
                thumbnail = os.path.join(rpath, 'search-icon.png'),
                key = Key(
                    id = 1, 
                    type = SEARCH
                )
            )
    
    archive = MediaObj(
                #title = 'Arkiv', 
                title = lang(30200),
                defntion = 'folder/perspektiv',
                isFolder = True,
                thumbnail = os.path.join(rpath, 'archive-icon.png'),
                key = Key(
                    id = REGION, 
                    type = PLAYLIST,
                    view = PROGRAM,
                    arg = PROGRAM
                )
            )
            
    @staticmethod
    def by_char():
        import string
        items = []
        for c in string.ascii_uppercase:
            item = MediaObj(
                    #title = 'Vis bokstav "%s"' % c,
                    title = lang(30206) % c,
                    thumbnail = os.path.join(rpath, '%s.png' % c),
                    key = Key(id = c, type = PROGRAM, view=BY_CHAR)
                )
            items.append(item)
        return items
        

                
    @staticmethod
    def playlist(parent):
        return [
                MediaObj(
                    key = Key(
                        type = PLAYLIST, id = parent.id, 
                        view = RELEVANT, arg = parent.arg
                    ),
                    #title = 'Aktuelt',
                    title = lang(30201),
                    thumbnail = os.path.join(rpath, 'news-icon.png')
                ), MediaObj(
                    key = Key(
                        type = PLAYLIST, id = parent.id, 
                        view = TOP_TOTAL, arg = parent.arg
                    ),
                    #title = 'Mest sett totalt', 
                    title = lang(30202),
                    thumbnail = os.path.join(rpath, 'stats-icon.png')
                ), MediaObj(
                    key = Key(
                        type = PLAYLIST, id = parent.id, 
                        view = TOP_THIS_MONTH, arg = parent.arg
                    ),
                    #title = 'Mest sett denne maned',
                    title = lang(30204), 
                    thumbnail = os.path.join(rpath, 'stats-icon.png')
                ), MediaObj(
                    key = Key(
                        type = PLAYLIST, id = parent.id, 
                        view = TOP_THIS_WEEK, arg = parent.arg
                    ),
                    #title = 'Mest sett denne uken',
                    title = lang(30203),
                    thumbnail = os.path.join(rpath, 'stats-icon.png')
                )
            ]

    @staticmethod
    def program(parent, resource_path = rpath):
        return [
                MediaObj(
                    key = Key(id = None, type = PROGRAM, view = BY_CHAR),
                    #title = 'Vis alfabetisk',
                    title = lang(30208), 
                    parent = parent,
                    thumbnail = os.path.join(resource_path, 'char-icon.png')
                ), MediaObj(
                    key = Key(id = '@',type = PROGRAM, view = VIEW_ALL),
                    #title = 'Vis alle',
                    title = lang(30207),
                    parent = parent,
                    thumbnail = os.path.join(resource_path, 'all-icon.png')
                ), MediaObj(
                    key = Key(type = PROGRAM, view = BY_THEME),
                    #title = 'Vis tema liste',
                    title = lang(30209), 
                    parent = parent,
                    thumbnail = os.path.join(resource_path, 'theme-icon.png')
                ), MediaObj(
                    key = Key(type = PROGRAM, id = 3650, view = TOP_TOTAL),
                    #title = 'Mest sett totalt', 
                    title = lang(30202),
                    parent = parent,
                    thumbnail = os.path.join(resource_path, 'stats-icon.png')
                ), MediaObj(
                    key = Key(type = PROGRAM, id = 31, view = TOP_THIS_MONTH),
                    #title = 'Mest sett denne maned',
                    title = lang(30204), 
                    parent = parent,
                    thumbnail = os.path.join(resource_path, 'stats-icon.png')
                ), MediaObj(
                    key = Key(type = PROGRAM, id = 7, view = TOP_THIS_WEEK),
                    #title = 'Mest sett denne uken', 
                    title = lang(30203),
                    parent = parent,
                    thumbnail = os.path.join(resource_path, 'stats-icon.png')
                ), MediaObj(
                    key = Key(type = PROGRAM, id = 0, view = TOP_BY_INPUT),
                    #title = 'Mest sett siste X dager', 
                    title = lang(30218),
                    parent = parent,
                    thumbnail = os.path.join(resource_path, 'input.png')
                ), MediaObj(
                    key = Key(type = PROGRAM, view = RECOMMENDED),
                    #title = 'Anbefalte programmer', 
                    title = lang(30217),
                    parent = parent,
                    thumbnail = os.path.join(resource_path, 'favorites.png')
                ), MediaObj(
                    key = Key(type = PROGRAM, view = ARTICLES),
                    #title = 'Artikler', 
                    title = lang(30219),
                    parent = parent,
                    thumbnail = os.path.join(resource_path, 'article.png')
                )
            ]
    
    
    theme_title = {
             2: 'Barn',    7: 'Natur',   20: 'Dokumentar',
            10: 'Sport',   4: 'Fakta',    9: 'Livssyn',    
             6: 'Mat',     8: 'Nyheter', 22: 'Tegnsprak',
            21: 'Ung',    19: 'Samisk',  11: 'Underholdning', 
             3: 'Drama',   5: 'Kultur',   12: 'Distrikt'
        }
        
    @staticmethod
    def by_theme(resource_path = rpath):
        return [
                MediaObj( 
                    #title = 'Barn',
                    title = lang(30100),
                    thumbnail = os.path.join(resource_path, 'kids.png'),
                    key = Key(id = 2, type = PROGRAM, view = BY_THEME)
                ), MediaObj(
                    #title = 'Natur',
                    title = lang(30101),
                    thumbnail = os.path.join(resource_path, 'ntur.png'),
                    key = Key(id = 7,type = PROGRAM,view = BY_THEME)
                ), MediaObj(
                    #title = 'Drama',
                    title = lang(30102),
                    thumbnail = os.path.join(resource_path,'drma.png'),
                    key = Key(id = 3, type = PROGRAM, view = BY_THEME)
                ), MediaObj(
                    #title = 'Sport',
                    title = lang(30103),
                    thumbnail = os.path.join(resource_path, 'sprt.png'),
                    key = Key(id = 10, type = PROGRAM, view = BY_THEME)
                ), MediaObj(
                    #title = 'Fakta',
                    title = lang(30104),
                    thumbnail = os.path.join(resource_path, 'fact.png'),
                    key = Key(id = 4, type = PROGRAM, view = BY_THEME)
                ), MediaObj(
                    #title = 'Livssyn',
                    title = lang(30105),
                    thumbnail = os.path.join(resource_path, 'life.png'),
                    key = Key(id = 9, type = PROGRAM, view = BY_THEME)
                ), MediaObj(
                    #title = 'Mat',
                    title = lang(30106),
                    thumbnail = os.path.join(resource_path, 'food.png'),
                    key = Key(id = 6, type = PROGRAM, view = BY_THEME)
                ), MediaObj(
                    #title = 'Nyheter',
                    title = lang(30107),
                    thumbnail = os.path.join(resource_path, 'news.png'),
                    key = Key(id = 8,type = PROGRAM, view = BY_THEME)
                ), MediaObj(
                    #title = 'Samisk',
                    title = lang(30108),
                    thumbnail = os.path.join(resource_path, 'sami.png'),
                    key = Key(id = 19, type = PROGRAM, view = BY_THEME)
                ), MediaObj(
                    #title = 'Ung',
                    title = lang(30109),
                    thumbnail = os.path.join(resource_path, 'teen.png'),
                    key = Key(id = 21, type = PROGRAM, view = BY_THEME)
                ), MediaObj(
                    #title = 'Tegnspraak',
                    title = lang(30110),
                    thumbnail = os.path.join(resource_path,'sign.png'),
                    key = Key(id = 22, type = PROGRAM, view = BY_THEME)
                ), MediaObj(
                    #title = 'Underholdning',
                    title = lang(30111),
                    thumbnail = os.path.join(resource_path,'entn.png'),
                    key = Key(id = 11, type = PROGRAM, view = BY_THEME)
                ), MediaObj(
                    #title = 'Dokumentar',
                    title = lang(30112),
                    thumbnail = os.path.join(resource_path,'docu.png'),
                    key = Key(id = 20, type = PROGRAM, view = BY_THEME)
                ), MediaObj(
                    #title = 'Kultur',
                    title = lang(30113),
                    thumbnail = os.path.join(resource_path,'cult.png'),
                    key = Key(id = 5, type = PROGRAM, view = BY_THEME)
                ), MediaObj(
                    #title = REGION,
                    title = lang(30114),
                    thumbnail = os.path.join(resource_path,'rgns.png'),
                    key = Key(id = 13, type = PROGRAM, view = BY_THEME)
                )
            ]
    
    @staticmethod
    def regions(resource_path = rpath):
        return[
                MediaObj(
                    #title = 'More og Romsdal',
                    title = lang(30150),
                    thumbnail = os.path.join(resource_path, 'ndmr.gif'),
                    key = Key(id = REGION, arg = 'ndmr', type = PLAYLIST)
                ), MediaObj(
                    #title = 'Hordaland',
                    title = lang(30151),
                    thumbnail = os.path.join(resource_path, 'ndho.gif'),
                    key = Key(id = REGION, arg = 'ndho', type = PLAYLIST)
                ), MediaObj(
                    #title = 'Nord-Norge',
                    title = lang(30152),
                    thumbnail = os.path.join(resource_path, 'ndno.gif'),
                    key = Key(id = REGION, arg = 'ndno', type = PLAYLIST)
                ), MediaObj(
                    #title = 'Rogaland',
                    title = lang(30153),
                    thumbnail = os.path.join(resource_path, 'ndro.gif'),
                    key = Key(id = REGION, arg = 'ndro', type = PLAYLIST)
                ), MediaObj(
                    #title = 'Sogn og Fjordane',
                    title = lang(30154),
                    thumbnail = os.path.join(resource_path, 'ndsf.gif'),
                    key = Key(id = REGION, arg = 'ndsf', type = PLAYLIST)
                ), MediaObj(
                    #title = 'Sorlandet',
                    title = lang(30155),
                    thumbnail = os.path.join(resource_path, 'ndsl.gif'),
                    key = Key(id = REGION, args = 'ndsl', type = PLAYLIST)
                ), MediaObj(
                    #title = 'Trondelag',
                    title = lang(30156),
                    thumbnail = os.path.join(resource_path, 'ndtl.gif'),
                    key = Key(id = REGION,arg = 'ndtl', type = PLAYLIST)
                ), MediaObj(
                    #title = 'Ostafjells',
                    title = lang(30157),
                    thumbnail = os.path.join(resource_path, 'ndtt.gif'),
                    key = Key(id = REGION, arg = 'ndtt', type = PLAYLIST)
                ), MediaObj(
                    #title = 'Ostfold',
                    title = lang(30158),
                    thumbnail = os.path.join(resource_path, 'ndos.gif'),
                    key = Key(id = REGION, arg = 'ndos', type = PLAYLIST)
                ), MediaObj(
                    #title = 'Ostlandssendingen',
                    title = lang(30159),
                    thumbnail = os.path.join(resource_path, 'ndoa.gif'),
                    key = Key(id = REGION, arg = 'ndoa', type = PLAYLIST)
                ), MediaObj(
                    #title = 'Hedmark og oppland',
                    title = lang(30160),
                    thumbnail = os.path.join(resource_path, 'ndop.gif'),
                    key = Key(id = REGION, arg = 'ndop', type = PLAYLIST)
                )
            ]

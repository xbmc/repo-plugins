#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Andres Trapanotto (andres.trapanotto@gmail.com)
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
# Note: Some media titles had the <em> </em> html included. This is 
#   stripped by a hardcoded regex.
# ToDo:
#   * To strip title html tags with BeautifulSoup
#

import datetime, re
from urllib import urlencode
from urllib2 import urlopen, Request
from BeautifulSoup import BeautifulSoup

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.7 '
    '(KHTML, like Gecko) Chrome/16.0.912.77 Safari/535.7'
)

REFERER = 'http://www.conectate.gob.ar/'

VIDEO_LANDING_URL = (
    'http://www.conectate.gob.ar/'
)


class Scraper(object):

    def __init__(self, force_refresh=False):
        self.force_refresh = force_refresh
        self.requests = {}

#   Get show names from site index
    def get_show_names(self, menuargc, page):
        log('get_show_names started for %s' % menuargc)
#        url = 'http://www.conectate.gob.ar/educar-portal-video-web/module/busqueda/busquedaAvanzada.do?modulo=menu&temaCanalId=1&canalId=1&tipoEmisionId=3&pagina=1'
        url = 'http://www.conectate.gob.ar/educar-portal-video-web/module/busqueda/busquedaAvanzada.do?modulo=menu&%s&pagina=%s' % (menuargc, page)
        html = self.__get_url(url)
        programas_ids = re.compile('<a href=".+?(idRecurso=\d+?)"><img src=".+?" alt=".+?" class=".+?" /></a>').findall(html)
        programas_titles = re.compile('<a href=".+?idRecurso=\d+?"><img src=".+?" alt="(.+?)" class=".+?" /></a>').findall(html)
        programas_icons = re.compile('<a href=".+?idRecurso=\d+?"><img src="(.+?)" alt=".+?" class=".+?" /></a>').findall(html)
#        log('get_show_names len(programas_titles)= %d ' % len(programas_titles))
        video_topics = []
        for programas_id, programas_icon, programas_title in zip(programas_ids, programas_icons, programas_titles):
            video_topics.append({
                'id': programas_id,
                'name': str(BeautifulSoup(programas_title,convertEntities=BeautifulSoup.HTML_ENTITIES)),
                'icon': programas_icon
            })
#        log('get_show_names got %d topics' % len(video_topics))
        return video_topics


    def get_episodes_by_show_name(self, show_name):
        log('get_episodes_by_show_name started')
        url = 'http://www.conectate.gob.ar/educar-portal-video-web/module/detalleRecurso/DetalleRecurso.do?%s' % show_name
        html = self.__get_url(url)
        programas_ids = re.compile('<a href=".+?(idRecurso=\d+?)">.+?</a>').findall(html)
        programas_titles = re.compile('<a href=".+?idRecurso=\d+?">(.+?)</a>').findall(html)
        programas_icon = re.compile('<img src="(.+?image_id=.+?)" />').findall(html)
#        programas_description = ''
#        programas_description = re.compile('<p>\s*(.+?)\r\s*</p>').findall(html)
        programas_description = re.compile('<p>(.+?)</p>').findall(html)[0]
        videos = []
        for programas_id, programas_title in zip(programas_ids, programas_titles):
            videos.append({
                'id': programas_id,
                'title': str(BeautifulSoup(programas_title,convertEntities=BeautifulSoup.HTML_ENTITIES)),
                'thumbnail': programas_icon[0],
                'count': 1,
                'duration': '',
                'originaltitle': str(BeautifulSoup(programas_title,convertEntities=BeautifulSoup.HTML_ENTITIES)),
                'description': programas_description,
                'date': '',
                'filesize': '',
                'author': '',
                'genres': ''

            })
        log('get_episodes_by_show_name got %d videos' % len(videos))
#        print videos
        return videos

    def get_single_episodes(self, menuargc, page):
        log('get_single_episodes started')
        url = 'http://conectate.gob.ar/educar-portal-video-web/module/busqueda/busquedaAvanzada.do?%s&pagina=%s' % (menuargc, page)
        html = self.__get_url(url)

        programas_ids = re.compile('<a href=".+?(idRecurso=\d+?)"><img src=".+?" alt=".+?" .+?/></a>').findall(html)
        programas_titles = re.compile('<a href=".+?idRecurso=\d+?"><img src=".+?" alt="(?:<em>)?(.+?)(?:</em>)?" .+?/></a>').findall(html)
        programas_icons = re.compile('<a href=".+?idRecurso=\d+?"><img src="(.+?)" alt=".+?" .+?/></a>').findall(html)
#        programas_descriptions = re.compile('<p>\s*(.+?)\r\s*</p>').findall(html)
        programas_descriptions = re.compile('<p>(.+?)</p>').findall(html)
#        log('get_show_names len(programas_ids)= %d ' % len(programas_ids))
#        log('get_show_names len(programas_titles)= %d ' % len(programas_titles))
        videos = []
        for programas_id, programas_title, programas_icon, programas_description in zip(programas_ids, programas_titles, programas_icons, programas_descriptions):
            videos.append({
                'id': programas_id,
                'title': str(BeautifulSoup(programas_title,convertEntities=BeautifulSoup.HTML_ENTITIES)),
                'thumbnail': programas_icon,
                'duration': '',
                'originaltitle': str(BeautifulSoup(programas_title,convertEntities=BeautifulSoup.HTML_ENTITIES)),
                'description': programas_description,
                'date': '',
                'filesize': '',
                'author': '',
                'genres': ''

            })
        log('get_single_episodes got %d videos' % len(videos))
#        print videos
        return videos

    def get_video(self, id):
        import xbmcaddon
        log('get_video started with id=%s' % id)
        addon = xbmcaddon.Addon(id='plugin.video.conectate')

        #url = 'http://www.conectate.gob.ar/educar-portal-video-web/module/detalleRecurso/DetalleRecurso.do?canalId=1&modulo=menu&temaCanalId=1&tipoEmisionId=3&recursoPadreId=50027&idRecurso=50030'
        url = 'http://www.conectate.gob.ar/educar-portal-video-web/module/detalleRecurso/DetalleRecurso.do?%s' % id
        html = self.__get_url(url)
        media_sd = re.compile('\'file\' \: \'(.+?)\'').findall(html)[0]
        media_hd = re.compile('\'hd.file\' \: \'(.+?)\'').findall(html)[0]
        hd_setting_value = addon.getSetting('hd_setting')
#        log('get_video hd_setting_value=%r' % hd_setting_value )
#        log('get_video media_hd=%s' % media_hd )
        if (media_hd and ( hd_setting_value == 'true' )):
            media_url = media_hd
        else:
            media_url = media_sd
        
        media_sub_url = re.compile('\'captions.file\' \: \'(.+?)\'').findall(html)
        if (len(media_sub_url) == 1):
            media_sub=media_sub_url[0]
        else:
            media_sub = ''
            
        media_title = re.compile('<title>(.+?).\|.+?</title>').findall(html)
#        media_title = re.compile('<title>(?:<em>)?(.+?).(?:<em>)?.?\|.+?</title>').findall(html)
        media_thumb = re.compile('<img src=".+?repositorio/Imagen/ver.+?" />').findall(html)
        media_description = re.compile('<!p>\s*(.+?)\r\s*</p>').findall(html)
        
        video = {
            'title': str(BeautifulSoup(media_title[0],convertEntities=BeautifulSoup.HTML_ENTITIES)),
            'thumbnail': media_thumb[0],
            'url': media_url,
            'url_sub': media_sub,
            'description': str(BeautifulSoup(media_description[0],convertEntities=BeautifulSoup.HTML_ENTITIES))
        }
        log('get_video finished')
#        print video
        return video

    def __get_url(self, url, get_dict='', post_dict=''):
        log('__get_url started with url=%s, get_dict=%s, post_dict=%s'
            % (url, get_dict, post_dict))
        uid = '%s-%s-%s' % (url, urlencode(get_dict), urlencode(post_dict))
        if uid in self.requests.keys():
            log('__get_url using cache for url=%s' % url)
            response = self.requests[uid]
        else:
            if get_dict:
                full_url = '%s?%s' % (url, urlencode(get_dict))
            else:
                full_url = url
            req = Request(full_url)
            req.add_header('User-Agent', USER_AGENT)
            req.add_header('Referer', REFERER)
            log('__get_url opening url=%s' % full_url)
            if post_dict:
                response = urlopen(req, urlencode(post_dict)).read()
            else:
                response = urlopen(req).read()
            self.requests[uid] = response
            log('__get_url finished with %d bytes result' % len(response))
        return response

def log(text):
    print 'Conectate.gob.ar scraper: %s' % text

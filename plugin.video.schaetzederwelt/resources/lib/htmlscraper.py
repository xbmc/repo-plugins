#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013, 2014 CHF (chrifri@gmx.de)
#     
#     This file is part of the XBMC Add-on: plugin.video.schaetzederwelt
#     
#     plugin.video.schaetzederwelt is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#     
#     plugin.video.schaetzederwelt is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#     
#     You should have received a copy of the GNU General Public License
#     along with plugin.video.schaetzederwelt. If not, see <http://www.gnu.org/licenses/>.
#     
#     Diese Datei ist Teil des XBMC Add-on: plugin.video.schaetzederwelt.
#     
#     plugin.video.schaetzederwelt ist Freie Software: Sie können es unter den Bedingungen
#     der GNU General Public License, wie von der Free Software Foundation,
#     Version 3 der Lizenz oder (nach Ihrer Wahl) jeder späteren
#     veröffentlichten Version, weiterverbreiten und/oder modifizieren.
#     
#     plugin.video.schaetzederwelt wird in der Hoffnung, dass es nützlich sein wird, aber
#     OHNE JEDE GEWÄHELEISTUNG, bereitgestellt; sogar ohne die implizite
#     Gewährleistung der MARKTFÄHIGKEIT oder EIGNUNG FÜR EINEN BESTIMMTEN ZWECK.
#     Siehe die GNU General Public License für weitere Details.
#     
#     Sie sollten eine Kopie der GNU General Public License zusammen mit diesem
#     Programm erhalten haben. Wenn nicht, siehe <http://www.gnu.org/licenses/>.
#
from urllib2 import urlopen, Request
import logging
import re
import socket
import json

BASE_URL = 'http://swrmediathek.de'
MAIN_URL = "http://swrmediathek.de/tvshow.htm?show=945f9950-cc74-11df-9bbb-0026b975f2e6"
EKEY_URL = "http://swrmediathek.de/AjaxEntry?ekey="
REQUEST_HEADERS = {"User-Agent" : "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)"}
SOCKET_TIMEOUT = 30
MAIN_PAGE_CACHE = None
MAX_TIMEOUT_RETRIES = 20
logger = logging.getLogger('plugin.video.schaetzederwelt')
kontinente_und_anderes = ['Europa', 'Afrika', 'Amerika', 'Australien', 'Asien', 'Pazifik']
 
     
def build_menuitems(url_for, endpoint, localizer):
    
    #log_info("Oeffne Showseite ...")
    page = get_content_from_url(MAIN_URL)
    
    #log_info("Hole alle Ids der einzelnen Sendungen ...")
    pattern = regex_pattern_for_items()
    
    items = []
    for match in pattern.finditer(page):
        item = {'label' : enrich_title(match.group('title').decode('utf-8')).strip(),
                'thumbnail' : BASE_URL + match.group('img'),
                'icon' : BASE_URL + match.group('img'),
                'path' : url_for(endpoint, ekey=match.group('ekey')),
                'context_menu' : [(localizer('toggle_watched'), 'XBMC.Action(ToggleWatched)')],
                'is_playable' : True
                }
        items.append(item)
    
    items.sort(key=lambda video: video['label'])
    log_info("Anzahl Videos: " + str(len(items)))
    #log_info("Videos: " + str(items))
    return items


def regex_pattern_for_items():
    return re.compile('<a href=\"/player.htm\?show=(?P<ekey>[a-z0-9-]*)\">[\n\t]*<img src=\"(?P<img>.*)\"[\n\t ]*alt=\".*\"[\n\t ]*title=\"(?P<title>.*)\"[\n\t ]*/>')


def enrich_title(title):
    match = re.match('.*, (?P<land>.*), Folge', title)
    if (match is not None):
        land = match.group('land')
        #log_info("Land: " + land)
    else:
        land = 'ungeordnet'
    #return '{0}: {1}'.format(land, title).encode('utf-8')
    return land + ' - ' + title
    
    
def get_json_for_ekey(ekey):
    # TODO: auf get_content_from_url umstellen, aber: return response.read() umstellen auf return response
    log_info("Lese ekey JSON: " + ekey)
    request = Request(EKEY_URL + ekey, headers = REQUEST_HEADERS)
    response = urlopen(request, timeout = SOCKET_TIMEOUT)
    json_object = json.load(response)
    log_info("Title: " + str(json_object['attr']['entry_title'].encode('utf-8')))
    # desc: Regex: 'entry_descl'
    #log_info("descr: " + json_object['attr']['entry_descl'])
    # image: entry_image_16_9
    #log_info("img: " + json_object['attr']['entry_image_16_9'])    
    # url: {"val0":"h264","val1":"3" - hochauflösend bzw. regex: 'rmtp ... l.mp4'
    #url = re.match('.*(?P<url>rtmp.*\.l\.mp4)', str(json_object['sub']))
    #log_info("url: " + url.group('url'))
    
    # Listen durchsuchen: s.a. http://stackoverflow.com/questions/9542738/python-find-in-list
    # Kontinent:
    # Suche nach Europa, Amerika, Asien, Australien, Ozeanien, Afrika
    # Liste traversieren: Wenn Atrtribut name == entry_keywd
    kontinent = None
    for item in json_object['sub']:
        if(item['name'] == 'entry_keywd' and kontinent is None):
            #log_info("item['attr']['val']" + item['attr']['val'])
            if (item['attr']['val'] in kontinente_und_anderes):
                kontinent = item['attr']['val']
        elif(item['name'] == 'entry_media'):            
            if (item['attr']['val0'] == 'h264' and item['attr']['val1'] == '3'):
               url =  item['attr']['val2']
            

    if (kontinent is None):
        kontinent = ''
    log_info("Kontinent: " + kontinent)
    log_info("url: " + url)
    
    # Land:
    # Suche in Titel nach 'Folge', davor kommt das Land, wenn nicht, dann leer lassen
    match = re.match('.* (?P<land>.*), Folge', str(json_object['attr']['entry_title'].encode('utf-8')))
    if (match is not None):
        land = match.group('land')
        log_info("Land: " + land)
    else:
        land = ''
    
    return {'ekey':ekey, 'label':json_object['attr']['entry_title'], 'url':url, 'land':land, 'kontinent':kontinent, 'img':json_object['attr']['entry_image_16_9']}

  

def get_content_from_url(url):
    request = Request(url, headers = REQUEST_HEADERS)
    #log_info("Timeout: " + str(socket.getdefaulttimeout()))
    sitereached = False
    timeoutcounter = 0
    while not sitereached and timeoutcounter < MAX_TIMEOUT_RETRIES:
        try:
            response = urlopen(request, timeout = SOCKET_TIMEOUT)
            sitereached = True
        except socket.timeout:
           log_info("Timeout (" + str(SOCKET_TIMEOUT) + " sec) reached accessing " + url)
           timeoutcounter+=1            
        except Exception,e:
            log_info("Exception " + str(e) + " accessing URL " + url)
            raise e
    if (timeoutcounter == MAX_TIMEOUT_RETRIES):
        log_info("Limit for retries after timeout reached: " + str(MAX_TIMEOUT_RETRIES))
        log_info("Site may be down?")
        raise socket.timeout        
                    
    log_info("URL opened: " + url)
    return response.read()


def log_info(msg):
    logger.info('HtmlScraper: %s' % msg)

def log_debug(msg):
    logger.debug('HtmlScraper: %s' % msg)
    
    

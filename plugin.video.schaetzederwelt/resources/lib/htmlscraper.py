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

MAIN_URL = "http://www.swr.de/schaetze-der-welt/"
REQUEST_HEADERS = {"User-Agent" : "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)"}
SOCKET_TIMEOUT = 30
MAIN_PAGE_CACHE = None
MAX_TIMEOUT_RETRIES = 20
logger = logging.getLogger('plugin.video.schaetzederwelt')

def scrape_topic_per_regex(topic, url_for, endpoint, localizer):
    log_info("Scraping " + topic)
    page = get_content_from_url(get_actual_from_baseurl("http://www.swr.de/schaetze-der-welt/" + topic + "/.*.html"))
           
    pattern = re.compile('teaser teaser-08 schaetze-der-welt\">(\n| )*<h2>(\n| )*<a href=\"(?P<url>.*)\">(\n| )*<img.*src=\"(?P<img>.*.jpg)\".*/>(\n| )*\t(\n| )*<span.*>(?P<titel1>(.*\n.*|.*)) *</span>(\n| )*<span.*>(?P<titel2>(.*\n.*|.*)) *</span>(\n| )*</a.*(\n| )*</h2.*(\n| )*<div.*(\n| )*<p>(?P<desc>.*)(\n| )*<a')    
    log_info("RegEx processed, gathering videos...")
            
    items = [{
             # Kurztext, Titel
             'label': m.group('titel1').decode('utf-8', 'ignore') + ', ' + m.group('titel2').decode('utf-8', 'ignore'),
             # URL fuer die Videoseite
             'path' : url_for(endpoint, url=m.group('url')),
             # Bild
             'thumbnail' : m.group('img'),
             'icon' : m.group('img'),
             #'fanart_image' : './fanart.jpg',
             # Beschreibung
             'info' : { 'plot' : m.group('desc')},
             # Add watch toggle button manually
             'context_menu' : [(localizer('toggle_watched'), 'XBMC.Action(ToggleWatched)')],
             'is_playable' : True
            } for m in pattern.finditer(page)]
    
    log_info(str(len(items)) + " Videos gathered.")
    items.sort(key=lambda video: video['label'])
    return items


def scrape_a_to_z_per_regex(letter, url_for, endpoint, localizer):
    log_info("Scraping " + letter)
    page = get_content_from_url(get_actual_from_baseurl("http://www.swr.de/schaetze-der-welt/denkmaeler/.*.html"))
    pattern = re.compile('<p><a name=\"' + letter + '\"></a>' + letter + '</p>\n *<ul>\n *(<li><a href=\".*\".*</a></li>\n *)*')
    erg = pattern.search(page)    
    pattern2 = re.compile('<li><a href=\"(?P<url>.*)\">(?P<text>.*)</a></li>')
    log_info("RexEx processed, gathering monuments for letter " + letter)
    #log_info(pattern2.findall(page, erg.start(), erg.end()))    
    
    items = [{
             # Kurztext, Titel
             'label': m.group(2).decode('utf-8', 'ignore'),
             # URL fuer die Videoseite
             'path' : url_for(endpoint, url=m.group(1)),
             # Bild
             'thumbnail' : '',
             'icon' : '', 
             # Beschreibung
             'info' : '',
             'context_menu' : [(localizer('toggle_watched'), 'XBMC.Action(ToggleWatched)')],
             'is_playable' : True  
            } for m in pattern2.finditer(page, erg.start(), erg.end())]    
    
    log_info(str(len(items)) + " monuments gathered.")
    return items


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


def get_actual_from_baseurl(regexp):
    global MAIN_PAGE_CACHE
    
    if (MAIN_PAGE_CACHE == None):
        log_debug("Filling MAIN_PAGE_CACHE")                       
        MAIN_PAGE_CACHE = get_content_from_url(MAIN_URL)
    
    log_debug("using MAIN_PAGE_CACHE")
    actual_url=re.search(regexp, MAIN_PAGE_CACHE)
    if (actual_url != None):
        return actual_url.group(0)
    else:
        return None


def get_video_from_url(regexp, url):                           
    page = get_content_from_url(url)    
    video_url=re.search(regexp, page)
    if (video_url != None):        
        return video_url.group(0)
    else:
        return None


def log_info(msg):
    logger.info('HtmlScraper: %s' % msg)

def log_debug(msg):
    logger.debug('HtmlScraper: %s' % msg)
    
    

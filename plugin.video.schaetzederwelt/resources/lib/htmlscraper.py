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
import re

MAIN_URL = "http://www.swr.de/schaetze-der-welt/"


def scrape_topic_per_regex(topic, url_for, endpoint):
    log("Scraping")
    url = get_ActualURL_from_URL("http://www.swr.de/schaetze-der-welt/" + topic + "/.*.html", MAIN_URL)
    r = urlopen(url)
    log("URL opened...")
    page = r.read()
           
    pattern = re.compile('teaser teaser-08 schaetze-der-welt\">(\n| )*<h2>(\n| )*<a href=\"(?P<url>.*)\">(\n| )*<img.*src=\"(?P<img>.*.jpg)\".*/>(\n| )*\t(\n| )*<span.*>(?P<titel1>(.*\n.*|.*)) *</span>(\n| )*<span.*>(?P<titel2>(.*\n.*|.*)) *</span>(\n| )*</a.*(\n| )*</h2.*(\n| )*<div.*(\n| )*<p>(?P<desc>.*)(\n| )*<a')    
    log("RegEx processed, gathering videos...")
            
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
             'is_playable' : True
            } for m in pattern.finditer(page)]
    
    log(str(len(items)) + " Videos gathered.")
    items.sort(key=lambda video: video['label'])
    return items


def scrape_a_to_z_per_regex(letter, url_for, endpoint):
    log("Scraping")
    url = get_ActualURL_from_URL("http://www.swr.de/schaetze-der-welt/denkmaeler/.*.html", MAIN_URL)    
    r = urlopen(url)
    log("URL opened...")
    page = r.read()        

    pattern = re.compile('<p><a name=\"' + letter + '\"></a>' + letter + '</p>\n *<ul>\n *(<li><a href=\".*\".*</a></li>\n *)*')
    erg = pattern.search(page)    
    pattern2 = re.compile('<li><a href=\"(?P<url>.*)\">(?P<text>.*)</a></li>')
    log("RexEx processed, gathering monuments for letter " + letter)
    #log(pattern2.findall(page, erg.start(), erg.end()))    
    
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
             'is_playable' : True  
            } for m in pattern2.finditer(page, erg.start(), erg.end())]    
    
    log(str(len(items)) + " Memorials gathered.")
    return items
        

def get_ActualURL_from_URL(regexp, url):
    requ = urlopen(Request(url))
    string = requ.read()
    url_mp4=re.search(regexp, string)
    if (url_mp4 != None):        
        return url_mp4.group(0)
    else:
        return None

    
def log(msg):
    print('HtmlScraper: %s' % msg)
    
    
    
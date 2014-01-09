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


from xbmcswift2 import Plugin, xbmcgui
from resources.lib import htmlscraper
import string


MAIN_MENU_TOPICS = [
     {'label': 'afrika', 'endpoint' : 'topic', 'path' : 'afrika'},
     {'label': 'amerika', 'endpoint' : 'topic', 'path' : 'amerika'},
     {'label': 'asien', 'endpoint' : 'topic', 'path' : 'asien'},
     {'label': 'australien-ozeanien', 'endpoint' : 'topic', 'path' : 'australien-ozeanien'},
     {'label': 'europa', 'endpoint' : 'topic', 'path' : 'europa'},
     {'label': 'spezial', 'endpoint' : 'topic', 'path' : 'spezial'},
     {'label': 'a_to_z_menu', 'endpoint' : 'a_to_z_menu', 'path' : ''}
]


I18NINDEX = { 
             'afrika' : 30001,
             'amerika' : 30002,
             'asien' : 30003,
             'australien-ozeanien' : 30004,
             'europa' : 30005,
             'spezial' : 30006,
             'a_to_z_menu' : 30007,
             'video_not_online' : 30008,
             'clear_cache' : 30009,
             'cache_cleared' : 30010
             }


plugin = Plugin()

@plugin.route('/')
def index():
    items = [{'label' : get_localized_string(item['label']), 
              'path' : plugin.url_for(endpoint = item['endpoint'], path = item['path'])} for item in MAIN_MENU_TOPICS]
    
    for item in items:
        item['context_menu'] = [(get_localized_string('clear_cache'), 'XBMC.RunPlugin(%s)' % plugin.url_for(endpoint = 'clear_cache', path = item['path']))]
        #item.add_context_menu_items([{'label': get_localized_string('clear_cache'), 'path' : plugin.url_for('clear_cache', path = item['path'])}])
    return plugin.finish(items)

@plugin.route('/topic/<path>')
def topic(path):                
    if (len(plugin.get_storage(path).items()) == 0):
        plugin.log.info("Cache is empty for items in topic " + path)         
        # Cache items
        if (path in string.ascii_uppercase):
            plugin.get_storage(path)['items'] = htmlscraper.scrape_a_to_z_per_regex(path, plugin.url_for, 'play_video')
        else:
            plugin.get_storage(path)['items'] = htmlscraper.scrape_topic_per_regex(path, plugin.url_for, 'play_video')
        #plugin.log.info(str(path) + " stored in cache")
    else:
        plugin.log.info(str(path) + " items retrieved from cache")
         
    items =  plugin.get_storage(path)['items']
    return plugin.finish(items)


@plugin.route('/atozmenu/')  
def a_to_z_menu():
    items = [{'label': le, 
              'path': plugin.url_for('topic', path=le)
            } for le in string.ascii_uppercase ]
    #items.append({'label': '0-9', 'path': plugin.url_for('a_to_z', letter='0-9')})    
    return plugin.finish(items)


@plugin.route('/video/<url>')
def play_video(url):
    videolink = htmlscraper.get_ActualURL_from_URL("http.*l\.mp4", url)
    if (videolink != None):
        plugin.log.info("Playing url: %s" % videolink)
        plugin.set_resolved_url(videolink)
    else:
        plugin.log.info("videolink is None")
        xbmcgui.Dialog().ok(plugin.name, get_localized_string("video_not_online"))
        return plugin.finish()


@plugin.route('/clear_cache/<path>')  
def clear_cache(path):
    token = path.split('/')
    
    if (token[-1] == "?path="):
        # path is empty for Index item
        for path in string.ascii_uppercase:
            plugin.get_storage(path).clear()
        menuitem = 'a_to_z_menu'
    else:
        plugin.get_storage(token[-1]).clear()
        menuitem = token[-1]
            
    plugin.log.info("Cache cleared for: %s" % menuitem)
    message = get_localized_string("cache_cleared") + ' \'' + get_localized_string(menuitem) + '\'.'  
    xbmcgui.Dialog().ok(plugin.name, message)
    return plugin.redirect(plugin.url_for('index'))


def get_localized_string(label):
    return plugin.get_string(I18NINDEX[label])


if __name__ == '__main__':
    plugin.run()

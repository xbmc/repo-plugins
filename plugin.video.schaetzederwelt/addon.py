#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013-2015 CHF (chrifri@gmx.de)
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

plugin = Plugin()


I18NINDEX = { 
             'video_not_online' : 30008,
             'toggle_watched' : 30011,
             }

def get_localized_string(label):
    return plugin.get_string(I18NINDEX[label])


@plugin.route('/')
def index():
    return (htmlscraper.build_menuitems(plugin.url_for, 'play_video', get_localized_string))

@plugin.route('/video/<ekey>')
def play_video(ekey):
    item = htmlscraper.get_json_for_ekey(ekey)
    if (item['url'] != None):
        plugin.log.info("Playing url: %s" % item['url'])
        plugin.set_resolved_url(item['url'])
    else:
        plugin.log.info("url is None")
        xbmcgui.Dialog().ok(plugin.name, get_localized_string("video_not_online"))
        return plugin.finish()


if __name__ == '__main__':
    plugin.run()

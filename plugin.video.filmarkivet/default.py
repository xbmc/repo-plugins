# -*- coding: utf-8 -*-

'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os, sys, time
import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import data

from itertools import repeat
from plugin import plugin

addon = xbmcaddon.Addon()
ADDON_PATH = addon.getAddonInfo('path')
__translation = addon.getLocalizedString


@plugin.route('/')
def view_top():
	text_categories = __translation(30010)
	text_years = __translation(30011)
	text_provinces = __translation(30012)
	text_cities = __translation(30013)
	text_themes = __translation(30020)
	text_popular = __translation(30021)
	text_latest = __translation(30022)
	text_search = __translation(30023)

	xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for("/categories/categories"), xbmcgui.ListItem(text_categories), True)
	xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for("/categories/years"), xbmcgui.ListItem(text_years), True)
	xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for("/categories/provinces"), xbmcgui.ListItem(text_provinces), True)
	xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for("/categories/cities"), xbmcgui.ListItem(text_cities), True)
	xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for("/themes"), xbmcgui.ListItem(text_themes), True)
	xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for("/popular"), xbmcgui.ListItem(text_popular), True)
	xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for("/recent"), xbmcgui.ListItem(text_latest), True)
	xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for("/search"), xbmcgui.ListItem(text_search), True)
	xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/categories/<subcat>')
def categories(subcat):
	view(data.parse_categories(subcat))


@plugin.route('/category/<arg>/<page>')
def category(arg, page="1"):
	films, next_url = data.parse_category(arg, int(page))
	view(films, next_url=next_url)


@plugin.route('/themes')
def themes():
	view(data.parse_themes())


@plugin.route('/theme/<theme_id>')
@plugin.route('/theme/<theme_id>/<page>')
def theme(theme_id, page="1"):
	films, next_url = data.parse_theme(theme_id, int(page))
	view(films, next_url=next_url)


@plugin.route('/popular')
@plugin.route('/popular/<page>')
def popular(page="1"):
	films, next_url = data.parse_popular(int(page))
	view(films, next_url=next_url)


@plugin.route('/recent')
@plugin.route('/recent/<page>')
def recent(page="1"):
	films, next_url = data.parse_recent(int(page))
	view(films, next_url=next_url)


@plugin.route('/search')
@plugin.route('/search/<search_string>')
@plugin.route('/search/<search_string>/<page>')
def search(search_string=None, page="1"):
	if search_string == None:
		search_string = unikeyboard("", "")

	films, next_url = data.parse_search(search_string, int(page))
	view(films, next_url=next_url)


@plugin.route('/film/<video_id>')
def play(video_id):
	url = data.parse_media_url(video_id)
	xbmcplugin.setResolvedUrl(plugin.handle, True, xbmcgui.ListItem(path=url))


# Show keyboard with given message as instructions. Return result string or None.
def unikeyboard(default, message):
	keyboard = xbmc.Keyboard(default, message)
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		return keyboard.getText()
	else:
		return None


# Show a list of data.
def view(elements, next_url=None):
	if not elements:
		error_title = __translation(30002)
		error_message1 = __translation(30003)
		error_message2 = __translation(30004)
		dialog = xbmcgui.Dialog()
		dialog.ok(error_title, error_message1, error_message2)
		return

	total = len(elements)
	for title, url, descr, thumb in elements:
		descr = descr() if callable(descr) else descr
		thumb = thumb() if callable(thumb) else thumb

		li = xbmcgui.ListItem(title, thumbnailImage=thumb)
		playable = plugin.route_for(url) == play
		li.setProperty('isplayable', str(playable))
		if playable:
			li.setInfo('video', {'plot':descr})
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(url), li, not playable, total)

	if next_url:
		text_next_page = __translation(30001)
		addPager(text_next_page, next_url, '', total)
	xbmcplugin.endOfDirectory(plugin.handle)


# Add pager line at bottom of a list.
def addPager(title, url, thumb, total):
	li = xbmcgui.ListItem(title, thumbnailImage=thumb)
	playable = plugin.route_for(url) == play
	li.setProperty('isplayable', str(playable))
	if playable:
		li.setInfo('video', {'plot':descr})
	xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(url), li, not playable, total)


 
if ( __name__ == "__main__" ):
	plugin.run()


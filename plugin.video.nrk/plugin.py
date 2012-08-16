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

""" some xbmcswift boilerplate """

import xbmcaddon
import xbmcswift

addon = xbmcaddon.Addon()
plugin = xbmcswift.Plugin(addon.getAddonInfo('name'), addon.getAddonInfo('id'), '')

def url_for(url):
  return 'plugin://%s%s' % (plugin._plugin_id, url)

def route_for(path):
  for rule in plugin._routes:
    try:
      view_func, items = rule.match(path)
    except xbmcswift.urls.NotFoundException:
      continue
    return view_func
  return None

plugin.route_for = route_for
plugin.url_for = url_for


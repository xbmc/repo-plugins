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
import xbmcaddon
import xbmcswift2 as xbmcswift

class Plugin(xbmcswift.Plugin):
  def __init__(self):
    xbmcswift.Plugin.__init__(self)
  
  @property
  def path(self):
    return self.addon.getAddonInfo('path')
  
  def make_url(self, url):
    return 'plugin://%s%s' % (self.id, url)

  def route_for(self, path):
    for rule in self._routes:
      try:
        view_func, items = rule.match(path)
      except xbmcswift.urls.NotFoundException:
        continue
      return view_func
    return None

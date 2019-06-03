# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
from resources.lib import tokenresolver

try:
    from urllib.request import build_opener, install_opener, ProxyHandler, Request, urlopen
except ImportError:
    from urllib2 import build_opener, install_opener, ProxyHandler, Request, urlopen


class Favorites:
    ''' Track, cache and manage VRT favorites '''

    def __init__(self, _kodi):
        ''' Initialize favorites, relies on XBMC vfs and a special VRT token '''
        self._kodi = _kodi
        self._tokenresolver = tokenresolver.TokenResolver(_kodi)
        self._proxies = _kodi.get_proxies()
        install_opener(build_opener(ProxyHandler(self._proxies)))
        # This is our internal representation
        self._favorites = dict()

    def is_activated(self):
        ''' Is favorites activated in the menu and do we have credentials ? '''
        return self._kodi.get_setting('usefavorites') == 'true' and self._kodi.has_credentials()

    def get_favorites(self, ttl=None):
        ''' Get a cached copy or a newer favorites from VRT, or fall back to a cached file '''
        if not self.is_activated():
            return
        import json
        api_json = self._kodi.get_cache('favorites.json', ttl)
        if not api_json:
            xvrttoken = self._tokenresolver.get_fav_xvrttoken()
            if xvrttoken:
                headers = {
                    'authorization': 'Bearer ' + xvrttoken,
                    'content-type': 'application/json',
                    'Referer': 'https://www.vrt.be/vrtnu',
                }
                req = Request('https://video-user-data.vrt.be/favorites', headers=headers)
                self._kodi.log_notice('URL post: https://video-user-data.vrt.be/favorites', 'Verbose')
                try:
                    api_json = json.load(urlopen(req))
                except Exception:
                    # Force favorites from cache
                    api_json = self._kodi.get_cache('favorites.json', ttl=None)
                else:
                    self._kodi.update_cache('favorites.json', api_json)
        self._favorites = api_json

    def set_favorite(self, program, path, value=True):
        ''' Set a program as favorite, and update local copy '''
        import json

        self.get_favorites(ttl=60 * 60)
        if value is self.is_favorite(path):
            # Already followed/unfollowed, nothing to do
            return

        xvrttoken = self._tokenresolver.get_fav_xvrttoken()
        headers = {
            'authorization': 'Bearer ' + xvrttoken,
            'content-type': 'application/json',
            # 'Cookie': 'X-VRT-Token=' + xvrttoken,
            'Referer': 'https://www.vrt.be/vrtnu',
        }
        payload = dict(isFavorite=value, programUrl=path, title=program)
        data = json.dumps(payload).encode('utf-8')
        self._kodi.log_notice('URL post: https://video-user-data.vrt.be/favorites/%s' % self.uuid(path), 'Verbose')
        req = Request('https://video-user-data.vrt.be/favorites/%s' % self.uuid(path), data=data, headers=headers)
        # TODO: Test that we get a HTTP 200, otherwise log and fail graceful
        result = urlopen(req)
        if result.getcode() != 200:
            self._kodi.log_error("Failed to follow program '%s' at VRT NU" % path)
        # NOTE: Updates to favorites take a longer time to take effect, so we keep our own cache and use it
        self._favorites[self.uuid(path)] = dict(value=payload)
        self._kodi.update_cache('favorites.json', self._favorites)
        self.invalidate_caches()

    def is_favorite(self, path):
        ''' Is a program a favorite ? '''
        value = False
        favorite = self._favorites.get(self.uuid(path))
        if favorite:
            value = favorite.get('value', dict(isFavorite=False)).get('isFavorite', False)
        return value

    def follow(self, program, path):
        ''' Follow your favorite program '''
        self._kodi.show_notification(message='Follow ' + program)
        self.set_favorite(program, path, True)
        self._kodi.container_refresh()

    def unfollow(self, program, path):
        ''' Unfollow your favorite program '''
        self._kodi.show_notification(message='Unfollow ' + program)
        self.set_favorite(program, path, False)
        self._kodi.container_refresh()

    def uuid(self, path):
        ''' Return a favorite uuid, used for lookups in favorites dict '''
        return path.replace('/', '').replace('-', '')

    def name(self, path):
        ''' Return the favorite name '''
        return path.replace('.relevant/', '/').split('/')[-2]

    def names(self):
        ''' Return all favorite names '''
        return [self.name(p.get('value').get('programUrl')) for p in self._favorites.values() if p.get('value').get('isFavorite')]

    def titles(self):
        ''' Return all favorite titles '''
        return [p.get('value').get('title') for p in self._favorites.values() if p.get('value').get('isFavorite')]

    def invalidate_caches(self):
        ''' Invalidate caches that rely on favorites '''
        self._kodi.invalidate_caches('my-offline-*.json')
        self._kodi.invalidate_caches('my-recent-*.json')

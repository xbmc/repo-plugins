# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
''' Implementation of Favorites class '''

from __future__ import absolute_import, division, unicode_literals

try:  # Python 3
    from urllib.parse import unquote
    from urllib.request import build_opener, install_opener, ProxyHandler, Request, urlopen
except ImportError:  # Python 2
    from urllib2 import build_opener, install_opener, ProxyHandler, Request, unquote, urlopen


class Favorites:
    ''' Track, cache and manage VRT favorites '''

    def __init__(self, _kodi):
        ''' Initialize favorites, relies on XBMC vfs and a special VRT token '''
        self._kodi = _kodi
        self._proxies = _kodi.get_proxies()
        install_opener(build_opener(ProxyHandler(self._proxies)))
        # This is our internal representation
        self._favorites = dict()

    def is_activated(self):
        ''' Is favorites activated in the menu and do we have credentials ? '''
        return self._kodi.get_setting('usefavorites') == 'true' and self._kodi.credentials_filled_in()

    def get_favorites(self, ttl=None):
        ''' Get a cached copy or a newer favorites from VRT, or fall back to a cached file '''
        if not self.is_activated():
            return
        favorites_json = self._kodi.get_cache('favorites.json', ttl)
        if not favorites_json:
            from tokenresolver import TokenResolver
            xvrttoken = TokenResolver(self._kodi).get_xvrttoken(token_variant='user')
            if xvrttoken:
                headers = {
                    'authorization': 'Bearer ' + xvrttoken,
                    'content-type': 'application/json',
                    'Referer': 'https://www.vrt.be/vrtnu',
                }
                req = Request('https://video-user-data.vrt.be/favorites', headers=headers)
                self._kodi.log('URL post: https://video-user-data.vrt.be/favorites', 'Verbose')
                import json
                try:
                    favorites_json = json.load(urlopen(req))
                except Exception:  # pylint: disable=broad-except
                    # Force favorites from cache
                    favorites_json = self._kodi.get_cache('favorites.json', ttl=None)
                else:
                    self._kodi.update_cache('favorites.json', favorites_json)
        if favorites_json:
            self._favorites = favorites_json

    def set_favorite(self, program, title, value=True):
        ''' Set a program as favorite, and update local copy '''

        self.get_favorites(ttl=60 * 60)
        if value is self.is_favorite(program):
            # Already followed/unfollowed, nothing to do
            return True

        from tokenresolver import TokenResolver
        xvrttoken = TokenResolver(self._kodi).get_xvrttoken(token_variant='user')
        if xvrttoken is None:
            self._kodi.log_error('Failed to get favorites token from VRT NU')
            self._kodi.show_notification(message=self._kodi.localize(30975))
            return False

        headers = {
            'authorization': 'Bearer ' + xvrttoken,
            'content-type': 'application/json',
            'Referer': 'https://www.vrt.be/vrtnu',
        }

        from statichelper import program_to_url
        payload = dict(isFavorite=value, programUrl=program_to_url(program, 'short'), title=title)
        import json
        data = json.dumps(payload).encode('utf-8')
        program_uuid = self.program_to_uuid(program)
        self._kodi.log('URL post: https://video-user-data.vrt.be/favorites/{uuid}', 'Verbose', uuid=program_uuid)
        req = Request('https://video-user-data.vrt.be/favorites/%s' % program_uuid, data=data, headers=headers)
        result = urlopen(req)
        if result.getcode() != 200:
            self._kodi.log_error("Failed to (un)follow program '{program}' at VRT NU".format(program=program))
            self._kodi.show_notification(message=self._kodi.localize(30976, program=program))
            return False
        # NOTE: Updates to favorites take a longer time to take effect, so we keep our own cache and use it
        self._favorites[program_uuid] = dict(value=payload)
        self._kodi.update_cache('favorites.json', self._favorites)
        self.invalidate_caches()
        return True

    def is_favorite(self, program):
        ''' Is a program a favorite ? '''
        value = False
        favorite = self._favorites.get(self.program_to_uuid(program))
        if favorite is not None:
            value = favorite.get('value', {}).get('isFavorite')
        return value is True

    def follow(self, program, title):
        ''' Follow your favorite program '''
        succeeded = self.set_favorite(program, title, True)
        if succeeded:
            self._kodi.show_notification(message=self._kodi.localize(30411, title=title))
            self._kodi.container_refresh()

    def unfollow(self, program, title, move_down=False):
        ''' Unfollow your favorite program '''
        succeeded = self.set_favorite(program, title, False)
        if succeeded:
            self._kodi.show_notification(message=self._kodi.localize(30412, title=title))
            # If the current item is selected and we need to move down before removing
            if move_down:
                self._kodi.input_down()
            self._kodi.container_refresh()

    @staticmethod
    def program_to_uuid(program):
        ''' Convert a program url component (e.g. de-campus-cup) to a favorite uuid (e.g. vrtnuazdecampuscup), used for lookups in favorites dict '''
        return 'vrtnuaz' + program.replace('-', '')

    def titles(self):
        ''' Return all favorite titles '''
        return [value.get('value').get('title') for value in list(self._favorites.values()) if value.get('value').get('isFavorite')]

    def programs(self):
        ''' Return all favorite programs '''
        from statichelper import url_to_program
        return [url_to_program(value.get('value').get('programUrl')) for value in list(self._favorites.values()) if value.get('value').get('isFavorite')]

    def invalidate_caches(self):
        ''' Invalidate caches that rely on favorites '''
        # NOTE: Do not invalidate favorites cache as we manage it ourselves
        # self._kodi.invalidate_caches('favorites.json')
        self._kodi.invalidate_caches('my-offline-*.json')
        self._kodi.invalidate_caches('my-recent-*.json')

    def refresh_favorites(self):
        ''' External API call to refresh favorites, used in Troubleshooting section '''
        self.get_favorites(ttl=0)
        self._kodi.show_notification(message=self._kodi.localize(30982))

    def manage_favorites(self):
        ''' Allow the user to unselect favorites to be removed from the listing '''
        from statichelper import url_to_program
        self.get_favorites(ttl=0)
        if not self._favorites:
            self._kodi.show_ok_dialog(heading=self._kodi.localize(30418), message=self._kodi.localize(30419))  # No favorites found
            return

        def by_title(item):
            ''' Sort by title '''
            return item.get('value').get('title')

        items = [dict(program=url_to_program(value.get('value').get('programUrl')),
                      title=unquote(value.get('value').get('title')),
                      enabled=value.get('value').get('isFavorite')) for value in list(sorted(self._favorites.values(), key=by_title))]
        titles = [item['title'] for item in items]
        preselect = [idx for idx in range(0, len(items) - 1) if items[idx]['enabled']]
        selected = self._kodi.show_multiselect(self._kodi.localize(30420), options=titles, preselect=preselect)  # Please select/unselect to follow/unfollow
        if selected is not None:
            for idx in set(preselect).difference(set(selected)):
                self.unfollow(program=items[idx]['program'], title=items[idx]['title'])
            for idx in set(selected).difference(set(preselect)):
                self.follow(program=items[idx]['program'], title=items[idx]['title'])

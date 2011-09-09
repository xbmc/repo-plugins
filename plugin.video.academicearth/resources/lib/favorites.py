# Copyright 2011 Jonathan Beluch.  
# 
# This program is free software: you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published by 
# the Free Software Foundation, either version 3 of the License, or 
# (at your option) any later version. 
# 
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
# GNU General Public License for more details. 
# 
# You should have received a copy of the GNU General Public License 
# along with this program.  If not, see <http://www.gnu.org/licenses/>. 
from xbmcswift import Module, download_page as _download_page
from BeautifulSoup import BeautifulSoup as BS
from urllib import urlencode
import cookielib
import urllib2
import os
from urlparse import urljoin
from xbmcswift import xbmcgui

favorites = Module('favorites')
BASE_URL = 'http://academicearth.org'
def full_url(path):
    return urljoin(BASE_URL, path)
LOGIN_URL = full_url('users/login')

def htmlify(url):
    return BS(s.download_page(url))

class AuthSession(object):
    '''This class handles cookies and session information.'''
    def __init__(self, get_cookie_fn_method):
        self.cookie_jar = None
        self.opener = None
        self.get_cookie_fn = get_cookie_fn_method
        self.authenticated = False

    def load_cookies_from_disk(self):
        try:
            self.cookie_jar.load(ignore_discard=True, ignore_expires=True)
        except IOError:
            pass
        
    def _set_opener(self, cookie_jar):
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))

    def _set_cookie_jar(self):
        self.cookie_jar_path = self.get_cookie_fn()
        if not os.path.exists(os.path.dirname(self.cookie_jar_path)):
            os.makedirs(os.path.dirname(self.cookie_jar_path))
        self.cookie_jar = cookielib.LWPCookieJar(self.cookie_jar_path)

    def authenticate(self, username=None, password=None):
        username = username or favorites._plugin.get_setting('username')
        password = password or favorites._plugin.get_setting('password')

        params = {
            '_method': 'POST',
            'data[User][username]': username,
            'data[User][password]': password,
            'data[User][goto]': '//',
            'header-login-submit': 'Login',
        }
        resp = self.opener.open(LOGIN_URL, urlencode(params))

        if resp.geturl().startswith(LOGIN_URL):
            dialog = xbmcgui.Dialog()
            # Incorrect username/password error message
            dialog.ok(favorites._plugin.get_string(30000), favorites._plugin.get_string(30401))
            favorites._plugin.open_settings()
            return False

        self.cookie_jar.save(ignore_discard=True, ignore_expires=True)

    def download_page(self, url):
        if not self.cookie_jar:
            self._set_cookie_jar()
            self._set_opener(self.cookie_jar)
        self.load_cookies_from_disk()

        resp = self.opener.open(url)

        # We need to check if we were redirected to the login page. If we were
        # then we'll call authenticate which should log in properly. If the
        # call to authenticate returns False, then there was a problem logging
        # in so we should just return None.
        if resp.geturl() == LOGIN_URL + '/':
            if self.authenticate() is False:
                return None

        resp = self.opener.open(url)
        return resp.read()

def get_cookie_fn():
    return favorites._plugin.cache_fn('.cookies')
s = AuthSession(get_cookie_fn)

## View functions for favorites
@favorites.route('/', url=full_url('favorites'))
def show_favorites(url):
    '''Shows your favorite videos from http://acadmemicearth.org/favorites.'
    '''
    src = s.download_page(url)
    if not src:
        return
    html = BS(src)

    videos = html.find('ul', {'class': 'favorites-list'}).findAll('li')

    items = [{
        'label': item.h3.a.string,
        'url': favorites.url_for('watch_lecture',
                                 url=full_url(item.h3.a['href'])),
        'thumbnail': full_url(item.img['src']),
        'is_folder': False,
        'is_playable': True,
        'context_menu': [
            (favorites._plugin.get_string(30301), 
             'XBMC.RunPlugin(%s)' % favorites.url_for(
                'favorites.remove_lecture',
                url=full_url(item.find('div', {'class': 'delete'}).a['href'])
            )),
        ],
    } for item in videos]

    xbmcgui.Dialog().ok(favorites._plugin.get_string(30000), favorites._plugin.get_string(30404))

    return favorites.add_items(items)

@favorites.route('/remove/<url>/')
def remove_lecture(url):
    '''This is a context menu view to remove an item from a user's favorites on
    academciearth.org'''
    if not s.download_page(url):
        xbmcgui.Dialog().ok(favorites._plugin.get_string(30000), favorites._plugin.get_string(30403))

@favorites.route('/add/<url>/')
def add_lecture(url):
    '''This is a context menu view to add an item to a user's favorites on
    academciearth.org'''
    if not s.download_page(url):
        xbmcgui.Dialog().ok(favorites._plugin.get_string(30000), favorites._plugin.get_string(30404))

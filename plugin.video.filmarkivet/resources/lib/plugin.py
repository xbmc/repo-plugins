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

import sys, requests
import xbmcgui, xbmcplugin
from resources.lib.filmarkivet import Filmarkivet
from resources.lib.kodiutils import AddonUtils, keyboard_get_string
from urllib.parse import parse_qs


def run():
    addon_utils = AddonUtils()
    params = parse_qs(sys.argv[2][1:])

    if "content_type" in params:
        content_type = params["content_type"][0]

    fa = Filmarkivet(addon_utils)
    if "mode" in params:
        try:
            mode = params["mode"][0]
            page = int(params["page"][0]) if "page" in params else 1
            url = params["url"][0] if "url" in params else None

            if mode == "categories":
                addon_utils.view_menu(fa.get_categories())
            if mode == "category" and url:
                movies = fa.get_url_movies(url, mode="category", page=page, limit=True)
                addon_utils.view_menu(movies)
            if mode == "letters":
                addon_utils.view_menu(fa.get_letters())
            if mode == "letter":
                if "l" in params:
                    addon_utils.view_menu(fa.get_letter_movies(params["l"][0]))
            if mode == "themes":
                addon_utils.view_menu(fa.get_themes())
            if mode == "theme" and url:
                categories = fa.get_theme_categories(url)
                addon_utils.view_menu(categories)
            if mode == "plot":
                desc = fa.get_plot(params["url"][1])
                info_title = "{0} - {1}".format(addon_utils.name,
                                                params["title"][0])
                xbmcgui.Dialog().textviewer(info_title, str(desc))
            if mode == "watch":
                media_url = fa.get_media_url(requests.utils.unquote(url))
                xbmcplugin.setResolvedUrl(addon_utils.handle, True,
                    xbmcgui.ListItem(path=media_url))
            if mode == "search":
                key = params["key"][0] if "key" in params else \
                    keyboard_get_string("", addon_utils.localize(30023))
                movies = fa.get_url_movies("/sokresultat/?q={0}".format(key),
                                           mode="search&key={0}".format(key),
                                           page=page, limit=True)
                addon_utils.view_menu(movies)
        except Exception as e:
            addon_utils.show_error(e)
    else:
        addon_utils.view_menu(fa.get_mainmenu())

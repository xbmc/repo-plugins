
# coding=utf-8
# -*- coding: utf-8 -*-
#
# plugin.video.arteplussept, Kodi add-on to watch videos from http://www.arte.tv/guide/fr/plus7/
# Copyright (C) 2015  known-as-bmf
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
from xbmcswift2 import Plugin


# global declarations
# plugin stuff
plugin = Plugin()


class PluginInformation:
    name = plugin.name
    version = plugin.addon.getAddonInfo('version')


# settings stuff
languages = ['fr', 'de', 'en', 'es', 'pl']
qualities = ['SQ', 'EQ', 'HQ']

# defaults to fr
language = plugin.get_setting('lang', choices=languages) or languages[0]
# defaults to SQ
quality = plugin.get_setting('quality', choices=qualities) or qualities[0]

# my imports
import view


@plugin.route('/', name='index')
def index():
    return view.build_categories(language)


@plugin.route('/category/<category_code>', name='category')
def category(category_code):
    return view.build_category(category_code, language)


@plugin.route('/creative', name='creative')
def creative():
    return []


@plugin.route('/magazines', name='magazines')
def magazines():
    plugin.set_content('tvshows')
    return plugin.finish(view.build_magazines(language))


@plugin.route('/sub_category/<sub_category_code>', name='sub_category_by_code')
def sub_category_by_code(sub_category_code):
    plugin.set_content('tvshows')
    return plugin.finish(view.build_sub_category_by_code(sub_category_code, language))


@plugin.route('/sub_category/<category_code>/<sub_category_title>', name='sub_category_by_title')
def sub_category_by_title(category_code, sub_category_title):
    plugin.set_content('tvshows')
    return plugin.finish(view.build_sub_category_by_title(category_code, sub_category_title, language))


@plugin.route('/collection/<kind>/<collection_id>', name='collection')
def collection(kind, collection_id):
    plugin.set_content('tvshows')
    return plugin.finish(view.build_mixed_collection(kind, collection_id, language))


@plugin.route('/play/<kind>/<program_id>', name='play')
def play(kind, program_id):
    return plugin.set_resolved_url(view.build_stream_url(kind, program_id, language, quality))


@plugin.route('/weekly', name='weekly')
def weekly():
    plugin.set_content('tvshows')
    return plugin.finish(view.build_weekly(language))


"""

@plugin.route('/broadcast', name='broadcast')
def broadcast():
    plugin.set_content('tvshows')
    items = custom.map_broadcast_item(
        custom.past_week_programs(language.get('short', 'fr')))
    return plugin.finish(items)

"""

# plugin bootstrap
if __name__ == '__main__':
    plugin.run()

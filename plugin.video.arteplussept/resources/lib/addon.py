
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


# my imports
import view
from settings import Settings

settings = Settings(plugin)


@plugin.route('/', name='index')
def index():
    return view.build_categories(settings)


@plugin.route('/category/<category_code>', name='category')
def category(category_code):
    return view.build_category(category_code, settings)


# @plugin.route('/creative', name='creative')
# def creative():
#     return []


@plugin.route('/magazines', name='magazines')
def magazines():
    plugin.set_content('tvshows')
    return plugin.finish(view.build_magazines(settings))


@plugin.route('/newest', name='newest')
def newest():
    plugin.set_content('tvshows')
    return plugin.finish(view.build_newest(settings))


@plugin.route('/most_viewed', name='most_viewed')
def most_viewed():
    plugin.set_content('tvshows')
    return plugin.finish(view.build_most_viewed(settings))


@plugin.route('/last_chance', name='last_chance')
def last_chance():
    plugin.set_content('tvshows')
    return plugin.finish(view.build_last_chance(settings))


@plugin.route('/sub_category/<sub_category_code>', name='sub_category_by_code')
def sub_category_by_code(sub_category_code):
    plugin.set_content('tvshows')
    return plugin.finish(view.build_sub_category_by_code(sub_category_code, settings))


@plugin.route('/sub_category/<category_code>/<sub_category_title>', name='sub_category_by_title')
def sub_category_by_title(category_code, sub_category_title):
    plugin.set_content('tvshows')
    return plugin.finish(view.build_sub_category_by_title(category_code, sub_category_title, settings))


@plugin.route('/collection/<kind>/<collection_id>', name='collection')
def collection(kind, collection_id):
    plugin.set_content('tvshows')
    return plugin.finish(view.build_mixed_collection(kind, collection_id, settings))


@plugin.route('/streams/<program_id>', name='streams')
def streams(program_id):
    plugin.set_content('tvshows')
    return plugin.finish(view.build_video_streams(program_id, settings))


@plugin.route('/play/<kind>/<program_id>', name='play')
@plugin.route('/play/<kind>/<program_id>/<audio_slot>', name='play_specific')
def play(kind, program_id, audio_slot='1'):
    return plugin.set_resolved_url(view.build_stream_url(kind, program_id, int(audio_slot), settings))


@plugin.route('/weekly', name='weekly')
def weekly():
    plugin.set_content('tvshows')
    return plugin.finish(view.build_weekly(settings))


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

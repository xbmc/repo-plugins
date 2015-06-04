#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2015 known-as-bmf
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from xbmcswift2 import Plugin
from xbmcswift2 import actions
import requests
import os
import json
import urllib2


plugin = Plugin()

base_url = 'http://www.arte.tv'

# http://www.arte.tv/papi/tvguide/videos/stream/{lang}/{id}_PLUS7-{lang}/{protocol}/{quality}.json
# lang     : F | D
# protocol : HBBTV | RTMP
# quality  : SQ (High) | EQ (Med) | HQ (Low)
video_json = base_url + '/papi/tvguide/videos/stream/player/{lang}/{id}_PLUS7-{lang}/{protocol}/ALL.json'

# http://www.arte.tv/papi/tvguide/videos/livestream/{lang}/
# lang : F | D
live_json = base_url + '/papi/tvguide/videos/livestream/{lang}/'

# http://www.arte.tv/guide/{lang}/plus7/par_dates.json?value={date}
# lang : fr | de
# date : date sous la forme yyyy-mm-jj

# http://www.arte.tv/guide/{lang}/plus7/par_themes.json?value={genre}
# lang  : fr | de
# genre : trigramme du genre (ACT DOC DEC EUR GEO SOC JUN AUT CIN ART CUL ENV)

# http://www.arte.tv/guide/{lang}/plus7/par_emissions.json?value={emission}
# lang     : fr | de
# emission : trigramme de l'emission (VMI TSG AJT JTE COU FUM KAR DCA MTR PNB PHI SUA TRA VOX XEN YOU

categories = [('new',         30001),
              ('selection',   30002),
              ('most_viewed', 30003),
              ('last_chance', 30004),
              ('themes',      30005)]

themes = [('ACT', 3000501),
          ('DOC', 3000502),
          ('DEC', 3000503),
          ('EUR', 3000504),
          ('GEO', 3000505),
          ('SOC', 3000506),
          ('JUN', 3000507),
          ('AUT', 3000508),
          ('CIN', 3000509),
          ('ART', 3000510),
          ('CUL', 3000511),
          ('ENV', 3000512)]

headers = {'user-agent': plugin.name + '/' + plugin.addon.getAddonInfo('version')}

language = 'fr' if plugin.get_setting('lang', int) == 0 else 'de'
prefer_vost = plugin.get_setting('prefer_vost', bool)
quality = plugin.get_setting('quality', int)
protocol = 'HBBTV' if plugin.get_setting('protocol', int) == 0 else 'RMP4'
download_folder = plugin.get_setting('download_folder', str)
download_quality = plugin.get_setting('download_quality', int)


@plugin.route('/')
def index():
    items = [{
        'label': plugin.get_string(value),
        'path': plugin.url_for('show_' + key)
    } for key, value in categories]
    items.append({
        'label': plugin.get_string(30006),
        'path': plugin.url_for('play_live'),
        'is_playable': True
    })
    return items


@plugin.route('/new', name='show_new',
              options={'json_url': base_url + '/guide/{lang}/plus7.json'})
@plugin.route('/selection', name='show_selection',
              options={'json_url': base_url + '/guide/{lang}/plus7/selection.json'})
@plugin.route('/most_viewed', name='show_most_viewed',
              options={'json_url': base_url + '/guide/{lang}/plus7/plus_vues.json'})
@plugin.route('/last_chance', name='show_last_chance',
              options={'json_url': base_url + '/guide/{lang}/plus7/derniere_chance.json'})
@plugin.route('/themes/<theme>', name='show_theme',
              options={'json_url': base_url + '/guide/{lang}/plus7/par_themes.json'})
def list(json_url, theme=None):
    plugin.set_content('tvshows')

    payload = {}
    if theme:
        payload['value'] = theme

    data = load_json(json_url.format(lang=language), payload)

    items = []
    for video in data['videos']:
        item = {
            'label': video['title'],
            'path': plugin.url_for('play', id=str(video['em'])),
            'thumbnail': video['image_url'],
            'is_playable': True,
            'info_type': 'video',
            'info': {
                'label': video['title'],
                'title': video['title'],
                'duration': str(video['duration']),
                'genre': video['video_channels'] if video['video_channels'] else '',
                'plot': video['desc'] if video['desc'] else '',
                #'aired': video['airdate_long'].encode('utf-8') if video['airdate_long'] is not None else '',
            },
            'properties': {
                'fanart_image': video['image_url'],
            },
            'context_menu': [
                (plugin.get_string(30021), actions.background(plugin.url_for('download', id=str(video['em'])))),
            ],
        }
        #item['context_menu'].append((plugin.get_string(30020), plugin.url_for('enqueue', item=item)))
        items.append(item)
    return plugin.finish(items)


@plugin.route('/show_themes', name='show_themes')
def show_themes():
    items = [{
        'label': plugin.get_string(value),
        'path': plugin.url_for('show_theme', theme=key)
    } for key, value in themes]
    return plugin.finish(items)


@plugin.route('/play/<id>', name='play')
def play(id):
    return plugin.set_resolved_url(create_item(id))


#@plugin.route('/enqueue/<item>', name='enqueue')
#def enqueue(item):
#    plugin.add_to_playlist([item])


@plugin.route('/download/<id>', name='download')
def download_file(id):
    if download_folder:
        video = create_item(id, True)
        filename = id + '_' + video['label'] + os.extsep + 'mp4'
        block_sz = 8192
        f = open(os.path.join(download_folder, filename), 'wb')
        u = urllib2.urlopen(video['path'])
        plugin.notify(filename, plugin.get_string(30007))
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break
            f.write(buffer)
        f.close()
        plugin.notify(filename, plugin.get_string(30008))
    else:
        plugin.notify(plugin.get_string(30010), plugin.get_string(30009))


@plugin.route('/live', name='play_live')
def play_live():
    data = load_json(live_json.format(lang=language[0].upper()))
    url = data['video']['VSR'][0]['VUR']
    return plugin.play_video({
        'label': data['video']['VTI'],
        'path': (url + ' live=1')
    })


quality_map = {0: 'SQ', 1: 'EQ', 2: 'HQ', 3: 'MQ'}
def create_item(id, safe_title=False):
    data = load_json(video_json.format(id=id, lang=language[0].upper(), protocol=protocol))
    filtered = []
    video = None
    # we try every quality (starting from the preferred one)
    # if it is not found, try every other from highest to lowest
    chosen_quality = download_quality if safe_title else quality
    for q in [quality_map[chosen_quality]] + [i for i in ['SQ', 'EQ', 'HQ', 'MQ'] if i is not quality_map[chosen_quality]]:
        # vost preferred
        if prefer_vost:
            filtered = [item for item in data['videoJsonPlayer']['VSR'].values() if match(item, q, True)]
        # no vost found or vost not preferred
        if len(filtered) == 0:
            filtered = [item for item in data['videoJsonPlayer']['VSR'].values() if match(item, q)]
        # here len(filtered) sould be 1
        if len(filtered) == 1:
            video = filtered[0]
            break
    return {
        'label': data['videoJsonPlayer']['VST']['VNA'] if safe_title else data['videoJsonPlayer']['VTI'],
        'path': video['url']
    }


# versionProg :
#       1 = Version langue URL
#       2 = Version inverse de langue URL
#       3 = VO-STF VOSTF
#       8 = VF-STMF ST sourds/mal
def match(item, quality, vost=False):
    return ((item['VQU'] == quality) and ((vost and item['versionProg'] == '3') or (not vost and item['versionProg'] == '1')))


def load_json(url, params={}):
    r = requests.get(url, params=params, headers=headers)
    return r.json()


if __name__ == '__main__':
    plugin.run()

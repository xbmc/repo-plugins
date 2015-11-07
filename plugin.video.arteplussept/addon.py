#!/usr/bin/python
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
from xbmcswift2 import actions
import requests
import os
import urllib2
# import datetime


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

# http://www.arte.tv/papi/tvguide/videos/plus7/program/{lang}/{detailLevel}/{category}/{cluster}/{recommended}/{sort}/{limit}/{offset}/DE_FR.json
# lang : F | D
# detailLevel : L2 | L3 (the higher the most verbose)
# category : categorie (HIS... see below)
# cluster : emission (VMI... see below)
# recommended : 1 | -1
# sort : AIRDATE_DESC | AIRDATE_ASC | ALPHA | VIEWS | LAST_CHANCE
# limit : n of results
# offset : starts at 1
#
# cluster : emission
# 28 Minutes                        VMI
# 360° GEO                          TSG
# ARTE Journal                      AJT
# ARTE Junior                       JUN
# ARTE Reportage                    JTE
# Au cœur de la nuit                ACN
# Cinéma sur ARTE                   FIL
# Court-circuit                     COU
# Cuisines des terroirs             CUI
# Futuremag                         FUM
# Karambolage                       KAR
# Le Dessous des cartes             DCA
# Maestro                           MAE
# Metropolis                        MTR
# Personne ne bouge !               PNB
# Philosophie                       PHI
# Square                            SUA
# Tracks                            TRA
# Vox Pop                           VOX
# X:enius                           XEN
# Yourope                           YOU
#
# category : categories
# Actu & société                    ACT
# Séries & fiction                  FIC
# Cinéma                            CIN
# Arts & spectacles classiques      ART
# Culture pop                       CUL
# Découverte                        DEC
# Histoire                          HIS
# Junior                            JUN
listing_json = base_url + '/papi/tvguide/videos/plus7/program/{lang}/L2/{category}/{cluster}/{highlight}/{sort}/{limit}/{offset}/DE_FR.json'

def get_menu_items():
    return [(plugin.url_for('listing'),                                   30001), # new http://www.arte.tv/papi/tvguide/videos/plus7/program/F/L2/ALL/ALL/-1/AIRDATE_DESC/0/0/DE_FR.json
            (plugin.url_for('listing', highlight='1', limit='6'),         30002), # selection http://www.arte.tv/papi/tvguide/videos/plus7/program/F/L2/ALL/ALL/1/AIRDATE_DESC/6/0/DE_FR.json
            (plugin.url_for('listing', sort='VIEWS', limit='20'),         30003), # most_viewed http://www.arte.tv/papi/tvguide/videos/plus7/program/F/L2/ALL/ALL/-1/VIEWS/0/0/DE_FR.json
            (plugin.url_for('listing', sort='LAST_CHANCE', limit='20'),   30004), # last chance http://www.arte.tv/papi/tvguide/videos/plus7/program/F/L2/ALL/ALL/-1/LAST_CHANCE/0/0/DE_FR.json
            (plugin.url_for('categories'),                                30005)] # categories http://www.arte.tv/papi/tvguide/videos/plus7/program/F/L2/XXX/ALL/-1/AIRDATE_DESC/0/0/DE_FR.json


def get_categories():
    return [('ACT', 3000501),
            ('FIC', 3000502),
            ('CIN', 3000503),
            ('ART', 3000504),
            ('CUL', 3000505),
            ('DEC', 3000506),
            ('HIS', 3000507),
            ('JUN', 3000508)]

headers = {'user-agent': plugin.name + '/' + plugin.addon.getAddonInfo('version')}

quality_map = {0: 'SQ', 1: 'EQ', 2: 'HQ', 3: 'MQ'}

# Settings
language = 'FR' if plugin.get_setting('lang', int) == 0 else 'DE'
prefer_vost = plugin.get_setting('prefer_vost', bool)
quality = plugin.get_setting('quality', int)
protocol = 'HBBTV' if plugin.get_setting('protocol', int) == 0 else 'RMP4'
download_folder = plugin.get_setting('download_folder', str)
download_quality = plugin.get_setting('download_quality', int)


@plugin.route('/')
def index():
    items = [{
        'label': plugin.get_string(sid),
        'path': path
    } for path, sid in get_menu_items()]
    items.append({
        'label': plugin.get_string(30006),
        'path': plugin.url_for('play_live'),
        'is_playable': True
    })
    return items


@plugin.route('/listing', name='listing')
def show_listing():
    plugin.set_content('tvshows')

    # very ugly workaround ahead (plugin.request.args.XXX returns an array for unknown reason)
    url = listing_json.format(lang=language[0],
                              category=plugin.request.args.get('category', ['ALL'])[0],
                              cluster=plugin.request.args.get('cluster', ['ALL'])[0],
                              highlight=plugin.request.args.get('highlight', ['-1'])[0],
                              sort=plugin.request.args.get('sort', ['AIRDATE_DESC'])[0],
                              limit=plugin.request.args.get('limit', ['0'])[0],
                              offset=plugin.request.args.get('offset', ['0'])[0])

    data = load_json(url)

    listing_key = 'program{lang}List'.format(lang=language)

    items = []
    for video in data[listing_key]:
        vdo = video['VDO']
        item = {
            'label': vdo.get('VTI'),
            'path': plugin.url_for('play', vid=str(vdo.get('VPI'))),
            'thumbnail': vdo.get('VTU').get('IUR'),
            'is_playable': True,
            'info_type': 'video',
            'info': {
                'label': vdo.get('VTI'),
                'title': vdo.get('VTI'),
                'duration': str(vdo.get('VDU')),
                'genre': vdo.get('VCG'),
                'plot': vdo.get('VDE'),
                'plotoutline': vdo.get('V7T'),
                'year': vdo.get('productionYear'),
                'director': vdo.get('PPD'),
                #'aired': datetime.datetime.strptime(vdo.get('VDA')[:-6], '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d') if vdo.get('VDA') else None
            },
            'properties': {
                'fanart_image': vdo.get('VTU').get('IUR'),
            },
            'context_menu': [
                (plugin.get_string(30021), actions.background(plugin.url_for('download', vid=str(vdo.get('VPI'))))),
            ],
        }
        # item['context_menu'].append((plugin.get_string(30020), plugin.url_for('enqueue', item=item)))
        items.append(item)
    return plugin.finish(items)


@plugin.route('/categories', name='categories')
def show_categories():
    items = [{
        'label': plugin.get_string(value),
        'path': plugin.url_for('listing', sort='AIRDATE_DESC', category=key)
    } for key, value in get_categories()]
    return plugin.finish(items)


@plugin.route('/play/<vid>', name='play')
def play(vid):
    return plugin.set_resolved_url(create_item(vid))


# @plugin.route('/enqueue/<item>', name='enqueue')
# def enqueue(item):
#     plugin.add_to_playlist([item])


@plugin.route('/download/<vid>', name='download')
def download_file(vid):
    if download_folder:
        video = create_item(vid, True)
        filename = vid + '_' + video['label'] + os.extsep + 'mp4'
        block_sz = 8192
        f = open(os.path.join(download_folder, filename), 'wb')
        u = urllib2.urlopen(video['path'])
        plugin.notify(filename, plugin.get_string(30007))
        while True:
            buff = u.read(block_sz)
            if not buff:
                break
            f.write(buff)
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


def create_item(vid, downloading=False):
    chosen_protocol = protocol if not downloading else 'HBBTV'
    chosen_quality = quality if not downloading else download_quality

    data = load_json(video_json.format(id=vid, lang=language[0].upper(), protocol=chosen_protocol))
    filtered = []
    video = None

    # we try every quality (starting from the preferred one)
    # if it is not found, try every other from highest to lowest
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
        'label': data['videoJsonPlayer']['VST']['VNA'] if downloading else data['videoJsonPlayer']['VTI'],
        'path': video['url']
    }


# versionProg :
#       1 = Version langue URL
#       2 = Version inverse de langue URL
#       3 = VO-STF VOSTF
#       8 = VF-STMF ST sourds/mal
def match(item, chosen_quality, vost=False):
    return (item['VQU'] == chosen_quality) and ((vost and item['versionProg'] == '3') or (not vost and item['versionProg'] == '1'))


def load_json(url, params=None):
    r = requests.get(url, params=params, headers=headers)
    return r.json()


if __name__ == '__main__':
    plugin.run()

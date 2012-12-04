# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Benjamin Bertrand
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.
# http://www.gnu.org/copyleft/gpl.html

import requests
import time
import hashlib
import urlparse
from datetime import timedelta
from config import plugin


CATALOGUE_URL = 'http://static.m6replay.fr/catalog/m6group_web/%s/catalogue.json'
CLIP_URL = 'http://static.m6replay.fr/catalog/m6group_web/%s/clip/%s/clip_infos-%s.json'
IMAGES_URL = 'http://static.m6replay.fr/images/'
CODE = {'M6': 'm6replay', 'W9': 'w9replay'}
TTL = int(plugin.get_setting('cached_ttl'))


def get_json(url):
    """Return the json-encode content of the HTTP GET request"""
    try:
        plugin.log.info('JSON request: %s' % url)
        r = requests.get(url)
        return r.json
    except (requests.ConnectionError, requests.HTTPError):
        plugin.log.error('JSON request failed' % url)


def url_thumb(item):
    """Return the url of the thumb associated to item (program or clip)"""
    try:
        img = urlparse.urljoin(IMAGES_URL, item[u'img'][u'vignette'])
    except TypeError:
        img = None
    return img


def get_id_parent(full_catalog, id_gnr):
    """Return the parent id of gnr"""
    id_parent = full_catalog[u'gnrList'][id_gnr][u'idParent']
    if id_parent is None:
        # Genre has no parent
        return id_gnr
    else:
        return str(id_parent)


def extract_date(date_string):
    """Extract the date in XBMC format %d.%m.%Y from date_string"""
    try:
        t = time.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    except TypeError:
        return ''
    else:
        return time.strftime('%d.%m.%Y', t)


def get_date(clp):
    """Return the antenna or publication date in XBMC format"""
    return extract_date(clp[u'antennaDate']) or extract_date(clp[u'publiDate'])


@plugin.cached(TTL)
def get_catalog(channel):
    """Return a catalog with only the needed information

    This catalog is cached"""
    code = CODE[channel]
    full_catalog = get_json(CATALOGUE_URL % code)
    # Only get main genres (no parent)
    genres = [{'id': id_gnr,
               'label': gnr[u'name']
              } for id_gnr, gnr in full_catalog[u'gnrList'].items() if gnr[u'idParent'] is None]
    # Get programs with visible clips
    programs = [{'id': id_pgm,
                 'label': pgm[u'name'],
                 'desc': pgm[u'desc'],
                 'thumb': url_thumb(pgm),
                 'clips': pgm[u'clpList'][u'vi'],
                 'id_gnr': get_id_parent(full_catalog, str(pgm[u'idGnr'])),
                } for id_pgm, pgm in full_catalog[u'pgmList'].items() if pgm[u'clpList'][u'vi']]
    # Get visible clips
    clips = [{'id': id_clp,
              'label': ' - '.join([clp[u'programName'], clp[u'clpName']]),
              'desc': clp[u'desc'],
              'date': get_date(clp),
              'duration': str(timedelta(seconds=clp[u'duration'])),
              'thumb': url_thumb(clp),
              'id_pgm': str(clp[u'idPgm'])
             } for id_clp, clp in full_catalog[u'clpList'].items() if clp[u'type'] == u'vi']
    return {'genres': genres,
            'programs': programs,
            'clips': clips}


def get_genres(channel):
    """Return the list of main genres"""
    catalog = get_catalog(channel)
    return catalog['genres']


def get_programs(channel, id_gnr='all'):
    """Return the list of all programs or
    programs belonging to the specified genre"""
    catalog = get_catalog(channel)
    all_programs = catalog['programs']
    if id_gnr == 'all':
        return all_programs
    else:
        return [pgm for pgm in all_programs if pgm['id_gnr'] == id_gnr]


def get_clips(channel, id_pgm='all'):
    """Return the list of all clips or
    clips belonging to the specified program"""
    catalog = get_catalog(channel)
    all_clips = catalog['clips']
    if id_pgm == 'all':
        return all_clips
    else:
        return [clp for clp in all_clips if clp['id_pgm'] == id_pgm]


def get_clip_url(channel, clip):
    """Return the playable url of the clip"""
    clip_key = '/'.join([clip[-2:], clip[-4:-2]])
    asset = get_json(CLIP_URL % (CODE[channel], clip_key, clip))[u'asset']
    urls = [val[u'url'] for val in asset.values() if val[u'url'].startswith('mp4:')]
    if urls:
        return get_rtmp_url(urls[0])
    return None


def encode_playpath(app, playpath, timestamp):
    """Return the encoded token url (with hash)"""
    delay = 86400
    secret_key = 'vw8kuo85j2xMc'
    url = '%s?s=%d&e=%d' % (playpath, timestamp, timestamp + delay)
    url_hash = hashlib.md5('/'.join([secret_key, app, url[4:]])).hexdigest()
    token_url = url + '&h=' + url_hash
    return token_url


def get_rtmp_url(playpath):
    """Return the playable rtmp url"""
    rtmp = 'rtmpe://groupemsix.fcod.llnwd.net'
    app = 'a2883/e1'
    #filename = os.path.basename(playpath)
    token_url = encode_playpath(app, playpath, int(time.time()))
    rtmp_url = '/'.join([rtmp, app, token_url])
    return rtmp_url + ' timeout=10'

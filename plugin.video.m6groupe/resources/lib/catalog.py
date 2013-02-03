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
TTL = int(plugin.get_setting('cached_ttl'))
if plugin.get_setting('swf_verify') == 'true':
    SWF_VERIFY = ' swfUrl=http://www.m6replay.fr/rel-3/M6ReplayV3Application-3.swf swfVfy=1'
else:
    SWF_VERIFY = ''
# Bump the CATALOG_API to force a refresh of the catalog
CATALOG_API = '1.0'


def code(channel):
    """Return the channel code"""
    return channel.lower() + 'replay'


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
    try:
        id_parent = full_catalog[u'gnrList'][id_gnr][u'idParent']
    except KeyError:
        # Unknown genre, just return the given id
        return id_gnr
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
def get_catalog(channel, api):
    """Return a catalog with only the needed information

    This catalog is cached
    The api argument is used to force a refresh of the catalog
    """
    full_catalog = get_json(CATALOGUE_URL % code(channel))
    # Only get main genres (no parent)
    genres = [{'id': id_gnr,
               'label': gnr[u'name'],
               'thumb': url_thumb(gnr),
              } for id_gnr, gnr in full_catalog[u'gnrList'].items() if gnr[u'idParent'] is None]
    plugin.log.debug('genres:')
    plugin.log.debug(genres)
    # Get programs with visible clips
    programs = [{'id': id_pgm,
                 'label': pgm[u'name'],
                 'desc': pgm[u'desc'],
                 'thumb': url_thumb(pgm),
                 'clips': pgm[u'clpList'][u'vi'],
                 'id_gnr': get_id_parent(full_catalog, str(pgm[u'idGnr'])),
                } for id_pgm, pgm in full_catalog[u'pgmList'].items() if pgm[u'clpList'][u'vi']]
    plugin.log.debug('programs:')
    plugin.log.debug(programs)
    # Get visible clips
    clips = [{'id': id_clp,
              'label': ' - '.join([clp[u'programName'], clp[u'clpName']]),
              'desc': clp[u'desc'],
              'date': get_date(clp),
              'duration': str(timedelta(seconds=clp[u'duration'])),
              'thumb': url_thumb(clp),
              'id_pgm': str(clp[u'idPgm'])
             } for id_clp, clp in full_catalog[u'clpList'].items() if clp[u'type'] == u'vi']
    plugin.log.debug('clips:')
    plugin.log.debug(clips)
    return {'genres': genres,
            'programs': programs,
            'clips': clips}


def get_genres(channel):
    """Return the list of main genres"""
    catalog = get_catalog(channel, CATALOG_API)
    return catalog['genres']


def get_programs(channel, id_gnr='all'):
    """Return the list of all programs or
    programs belonging to the specified genre"""
    catalog = get_catalog(channel, CATALOG_API)
    all_programs = catalog['programs']
    if id_gnr == 'all':
        return all_programs
    else:
        return [pgm for pgm in all_programs if pgm['id_gnr'] == id_gnr]


def get_clips(channel, id_pgm='all'):
    """Return the list of all clips or
    clips belonging to the specified program"""
    catalog = get_catalog(channel, CATALOG_API)
    all_clips = catalog['clips']
    if id_pgm == 'all':
        return all_clips
    else:
        return [clp for clp in all_clips if clp['id_pgm'] == id_pgm]


def get_clip_url(channel, clip):
    """Return the playable url of the clip"""
    clip_key = '/'.join([clip[-2:], clip[-4:-2]])
    asset = get_json(CLIP_URL % (code(channel), clip_key, clip))[u'asset']
    urls = [val[u'url'] for val in asset.values()]
    # Look for a mp4 url
    for url in urls:
        if url.startswith('mp4:'):
            plugin.log.debug('mp4 url found')
            return get_rtmp_url(url)
    # No mp4 url found, try to convert it from the f4m url
    for url in urls:
        if url.endswith('.f4m'):
            plugin.log.debug('using .f4m url')
            link = 'mp4:production/regienum/' + url.split('/')[-1].replace('.f4m', '.mp4')
            return get_rtmp_url(link)
    # No url found
    plugin.log.debug('no url found')
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
    return rtmp_url + SWF_VERIFY + ' timeout=10'

'''
    RockPeaks plugin for XBMC
    Copyright 2013 Artem Matsak

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

from string import ascii_lowercase
import CommonFunctions
from xbmcswift2 import xbmc, xbmcplugin, actions, Plugin, ListItem
from RockPeaksAPI import RockPeaksAPI
from RockPeaksLogin import RockPeaksLogin


common = CommonFunctions
plugin = Plugin()
api = RockPeaksAPI()
login = RockPeaksLogin(plugin, api)

pageSize = 25

@plugin.route('/')
def index():
    do_login = 'login' in plugin.request.args and plugin.request.args['login'][0] == '1'
    if do_login:
        login.login()

    items = [
        {
            'label': plugin.get_string(30500),
            'path': plugin.url_for('search', page='0', update_listing='0'),
        },
        {
            'label': plugin.get_string(30501),
            'path': plugin.url_for('latest_videos', page='0', update_listing='0'),
        },
        {
            'label': plugin.get_string(30502),
            'path': plugin.url_for('latest_discs', page='0', update_listing='0'),
        },
        {
            'label': plugin.get_string(30503),
            'path': plugin.url_for('artist_index'),
        },
        {
            'label': plugin.get_string(30504),
            'path': plugin.url_for('show_index'),
        },
        {
            'label': plugin.get_string(30505),
            'path': plugin.url_for('genre_index'),
        }
    ]
    if len(plugin.get_setting('sessid')) == 0:
        items.append({
            'label': plugin.get_string(30506),
            'path': plugin.url_for('index', login='1'),
        })
    else:
        items.append({
            'label': plugin.get_string(30507),
            'path': plugin.url_for('tracked_artists', page='0', update_listing='0'),
        })
        items.append({
            'label': plugin.get_string(30508),
            'path': plugin.url_for('playlist_index', page='0', update_listing='0'),
        })

    return plugin.finish(items, update_listing=do_login)

@plugin.route('/genres/index/')
def genre_index():
    data = api.request('genre.getMasterGenres', {})
    items = [_make_genre_item(genre) for genre in data['genres']['genre']]
    return items

@plugin.route('/search/<page>/')
def search(page='0'):
    update_listing = 'update_listing' not in plugin.request.args or plugin.request.args['update_listing'][0] == '1'
    if not update_listing:
        keys = common.getUserInput(plugin.get_string(30509), '')
        plugin.set_setting('search_keys', keys)
    else:
        keys = plugin.get_setting('search_keys')

    page = int(page)
    data = api.request('search.searchContent', {
        'keys': keys,
        'page': page
    })
    items = [_make_search_result_item(search_result) for search_result in data['items']['item']]
    # It's possible for _make_search_result_item() to return an empty item.
    items = filter(None, items)
    _add_pager(items, {'endpoint': 'search'}, page, 10, int(data['items']['count']))
    return plugin.finish(items, update_listing=update_listing)

@plugin.route('/discs/latest/<page>/')
def latest_discs(page='0'):
    update_listing = 'update_listing' not in plugin.request.args or plugin.request.args['update_listing'][0] == '1'
    page = int(page)
    data = api.request('disc.getDiscs', {
        'page': page,
        'limit': pageSize
    })
    items = [_make_disc_item(disc) for disc in data['discs']['disc']]
    _add_pager(items, {'endpoint': 'latest_discs'}, page, pageSize, int(data['discs']['count']))
    return plugin.finish(items, update_listing=update_listing)

@plugin.route('/playlists/index/<page>/')
def playlist_index(page='0'):
    update_listing = 'update_listing' not in plugin.request.args or plugin.request.args['update_listing'][0] == '1'
    page = int(page)
    data = api.request('user.getPlaylists', {
        'sessid': plugin.get_setting('sessid'),
        'page': page,
        'limit': pageSize
    })
    items = [_make_playlist_item(playlist) for playlist in data['playlists']['playlist']]
    _add_pager(items, {'endpoint': 'playlist_index'}, page, pageSize, int(data['playlists']['count']))
    return plugin.finish(items, update_listing=update_listing)

@plugin.route('/tracked_artists/<page>/')
def tracked_artists(page='0'):
    update_listing = 'update_listing' not in plugin.request.args or plugin.request.args['update_listing'][0] == '1'
    page = int(page)
    data = api.request('user.getTrackedArtists', {
        'sessid': plugin.get_setting('sessid'),
        'page': page,
        'limit': pageSize
    })
    items = [_make_artist_item(artist) for artist in data['artists']['artist']]
    _add_pager(items, {'endpoint': 'tracked_artists'}, page, pageSize, int(data['artists']['count']))
    return plugin.finish(items, update_listing=update_listing)

@plugin.route('/videos/latest/<page>/')
def latest_videos(page='0'):
    update_listing = 'update_listing' not in plugin.request.args or plugin.request.args['update_listing'][0] == '1'
    page = int(page)
    data = api.request('video.getVideos', {
        'sources': _get_supported_sources(),
        'status': 1,
        'sort': 'date',
        'order': 'desc',
        'page': page,
        'limit': pageSize
    })
    items = [_make_video_item(video) for video in data['videos']['video']]
    _add_pager(items, {'endpoint': 'latest_videos'}, page, pageSize, int(data['videos']['count']))
    return plugin.finish(items, update_listing=update_listing)

@plugin.route('/artists/index', name='artist_index', options={'entity': 'artist'})
@plugin.route('/shows/index', name='show_index', options={'entity': 'show'})
def entity_index(entity):
    items = []

    alpha_func = ''
    if entity == 'artist':
        alpha_func = 'artist_alpha'
    else:
        alpha_func = 'show_alpha'

    items = [{
        'label': l.upper(),
        'path': plugin.url_for(alpha_func, letter=l, page='0', update_listing='0')
    } for l in ascii_lowercase]
    items.insert(0, {
        'label': '#',
        'path': plugin.url_for(alpha_func, letter='misc', page='0', update_listing='0')
    })

    return items

@plugin.route('/artists/alpha/<letter>/<page>/')
def artist_alpha(letter, page='0'):
    update_listing = 'update_listing' not in plugin.request.args or plugin.request.args['update_listing'][0] == '1'
    page = int(page)
    data = api.request('artist.getArtists', {
        'letter': letter,
        'page': page,
        'limit': pageSize
    })
    items = [_make_artist_item(artist) for artist in data['artists']['artist']]
    _add_pager(items, {'endpoint': 'artist_alpha', 'letter': letter}, page, pageSize, int(data['artists']['count']))
    return plugin.finish(items, update_listing=update_listing)

@plugin.route('/shows/alpha/<letter>/<page>/')
def show_alpha(letter, page='0'):
    update_listing = 'update_listing' not in plugin.request.args or plugin.request.args['update_listing'][0] == '1'
    page = int(page)
    data = api.request('show.getShows', {
        'letter': letter,
        'page': page,
        'limit': pageSize
    })
    items = [_make_show_item(show) for show in data['shows']['show']]
    _add_pager(items, {'endpoint': 'show_alpha', 'letter': letter}, page, pageSize, int(data['shows']['count']))
    return plugin.finish(items, update_listing=update_listing)

@plugin.route('/discs/<disc_id>/')
def disc_videos(disc_id):
    data = api.request('disc.getInfo', {
        'id': disc_id,
        'video_sources': _get_supported_sources(),
        'video_status': 1
    })
    items = [_make_video_item(video) for video in data['disc']['videos']['video']]
    return items

@plugin.route('/discs/<disc_id>/play_all/')
def disc_play_all(disc_id):
    data = api.request('disc.getInfo', {
        'id': disc_id,
        'video_sources': _get_supported_sources(),
        'video_status': 1
    })
    items = [_make_video_item(video) for video in data['disc']['videos']['video']]
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    for item in items:
        listitem = ListItem.from_dict(**item)
        playlist.add(item['path'], listitem.as_xbmc_listitem())
    player = xbmc.Player()
    player.playPlaylist(playlist)

@plugin.route('/playlists/<playlist_id>/')
def playlist_videos(playlist_id):
    data = api.request('playlist.getInfo', {
        'id': playlist_id,
        'video_sources': _get_supported_sources(),
        'video_status': 1
    })
    items = [_make_video_item(video) for video in data['playlist']['videos']['video']]
    return items

@plugin.route('/playlists/<playlist_id>/play_all/')
def playlist_play_all(playlist_id):
    data = api.request('playlist.getInfo', {
        'id': playlist_id,
        'video_sources': _get_supported_sources(),
        'video_status': 1
    })
    items = [_make_video_item(video) for video in data['playlist']['videos']['video']]
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    for item in items:
        listitem = ListItem.from_dict(**item)
        playlist.add(item['path'], listitem.as_xbmc_listitem())
    player = xbmc.Player()
    player.playPlaylist(playlist)

@plugin.route('/genres/<genre_name>/<page>')
def genre_videos(genre_name, page='0'):
    update_listing = 'update_listing' not in plugin.request.args or plugin.request.args['update_listing'][0] == '1'
    page = int(page)
    data = api.request('video.getVideos', {
        'genres': genre_name,
        'sources': _get_supported_sources(),
        'status': 1,
        'sort': 'added',
        'order': 'desc',
        'page': page,
        'limit': pageSize
    })
    items = [_make_video_item(video) for video in data['videos']['video']]
    _add_pager(items, {'endpoint': 'genre_videos', 'genre_name': genre_name}, page, pageSize, int(data['videos']['count']))
    return plugin.finish(items, update_listing=update_listing, sort_methods=_get_video_sort_methods())

@plugin.route('/artists/<artist_id>/<page>/')
def artist_videos(artist_id, page='0'):
    update_listing = 'update_listing' not in plugin.request.args or plugin.request.args['update_listing'][0] == '1'
    page = int(page)
    data = api.request('video.getVideos', {
        'artist_id': artist_id,
        'sources': _get_supported_sources(),
        'status': 1,
        'sort': 'added',
        'order': 'desc',
        'page': page,
        'limit': pageSize
    })
    items = [_make_video_item(video, ['artist']) for video in data['videos']['video']]
    _add_pager(items, {'endpoint': 'artist_videos', 'artist_id': artist_id}, page, pageSize, int(data['videos']['count']))
    return plugin.finish(items, update_listing=update_listing, sort_methods=_get_video_sort_methods())
    
@plugin.route('/shows/<show_id>/<page>/')
def show_videos(show_id, page='0'):
    update_listing = 'update_listing' not in plugin.request.args or plugin.request.args['update_listing'][0] == '1'
    page = int(page)
    data = api.request('video.getVideos', {
        'show_id': show_id,
        'sources': _get_supported_sources(),
        'status': 1,
        'sort': 'added',
        'order': 'desc',
        'page': page,
        'limit': pageSize
    })
    items = [_make_video_item(video, ['show']) for video in data['videos']['video']]
    _add_pager(items, {'endpoint': 'show_videos', 'show_id': show_id}, page, pageSize, int(data['videos']['count']))
    return plugin.finish(items, update_listing=update_listing, sort_methods=_get_video_sort_methods())
    
@plugin.route('/videos/play/<source>/<video_id>')
def play_video(source, video_id):
    plugin.set_resolved_url(_get_playback_path(source, video_id))

def _disc_play_all_ctx(disc_id):
    label = 'Play all'
    url = plugin.url_for('disc_play_all', disc_id=disc_id)
    return (label, actions.background(url))

def _playlist_play_all_ctx(playlist_id):
    label = 'Play all'
    url = plugin.url_for('playlist_play_all', playlist_id=playlist_id)
    return (label, actions.background(url))

def _make_disc_item(disc):
    item = {
        'label': disc['title'],
        'path': plugin.url_for('disc_videos', disc_id=disc['id']),
        'thumbnail': disc['artwork'],
        'context_menu': [
            _disc_play_all_ctx(disc['id']),
        ]
    }
    return item

def _make_playlist_item(playlist):
    item = {
        'label': playlist['name'],
        'path': plugin.url_for('playlist_videos', playlist_id=playlist['id']),
        'thumbnail': playlist['image'],
        'context_menu': [
            _playlist_play_all_ctx(playlist['id']),
        ]
    }
    return item

def _make_genre_item(genre):
    item = {
        'label': genre['name'],
        'path': plugin.url_for('genre_videos', genre_name=genre['name'], page='0', update_listing='0'),
    }
    return item

def _make_artist_item(artist):
    item = {
        'label': artist['name'],
        'path': plugin.url_for('artist_videos', artist_id=artist['id'], page='0', update_listing='0'),
        'thumbnail': artist['publicity_image']
    }
    return item

def _make_show_item(show):
    item = {
        'label': show['name'],
        'path': plugin.url_for('show_videos', show_id=show['id'], page='0', update_listing='0'),
        'thumbnail': show['image']
    }
    return item

def _make_video_item(video, omit_info=[]):
    label = video['title']
    if 'artist' not in omit_info:
        label += ' | ' + video['artist']
    if 'show' not in omit_info:
        label += ' | ' + video['show']
    if 'date' not in omit_info:
        label += ' | ' + video['date_string']
    item = {
        'label': label,
        'path': plugin.url_for('play_video', source=video['source']['name'], video_id=video['source']['id']),
        'thumbnail': video['image'],
        'info': {
            'title': label,
            'date': '%(d)02d.%(m)02d.%(y)04d' % {'d': int(video['date']['day'] or '1'), 'm': int(video['date']['month'] or '1'), 'y': int(video['date']['year'] or '0')},
            'rating': float(video['rp_ranking'] or "0") / 100.0,
            'duration': _format_duration(int(video['duration'])),
            'dateadded': video['added']
           },
        'is_playable': True,
    }

    return item

def _make_search_result_item(search_result):
    item = None
    if search_result['type'] == 'Artist':
        item = _make_artist_item(search_result)
        item['label'] = plugin.get_string(30510) % item['label']
    elif search_result['type'] == 'Show':
        item = _make_show_item(search_result)
        item['label'] = plugin.get_string(30511) % item['label']
    elif search_result['type'] == 'Clip':
        if 'source' in search_result and 'name' in search_result['source'] and search_result['source']['name'] in ['youtube', 'vimeo', 'dailymotion'] and search_result['source']['status'] == '1':
            item = _make_video_item(search_result)
            item['label'] = plugin.get_string(30512) % item['label']
    return item

def _get_video_sort_methods():
    return [
        xbmcplugin.SORT_METHOD_UNSORTED,
        xbmcplugin.SORT_METHOD_LABEL,
        xbmcplugin.SORT_METHOD_DATE,
        xbmcplugin.SORT_METHOD_VIDEO_RATING
    ]

def _get_supported_sources():
    return 'youtube,vimeo,dailymotion'

def _get_playback_path(source, video_id):
    if source == 'youtube':
        return 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' % video_id
    elif source == 'vimeo':
        return 'plugin://plugin.video.vimeo/?action=play_video&videoid=%s' % video_id
    elif source == 'dailymotion':
        return 'plugin://plugin.video.dailymotion_com/?mode=playVideo&url=%s' % video_id

def _add_pager(items, params, page, pageSize, count):
    if pageSize * (page+1) < count:
        params['page'] = str(page + 1)
        items.insert(0, {
            'label': 'Next page >>',
            'path': plugin.url_for(**params)
        })
    if page > 0:
        params['page'] = str(page - 1)
        items.insert(0, {
            'label': '<< Previous page',
            'path': plugin.url_for(**params)
        })

def _format_duration(seconds):
    h = seconds / 3600
    m = (seconds - h*3600) / 60
    s = seconds - h*3600 - m*60
    if h > 0:
        return '%(h)02d:%(m)02d:%(s)02d' % {'h': h, 'm': m, 's': s}
    else:
        return '%(m)02d:%(s)02d' % {'m': m, 's': s}

if __name__ == '__main__':
    login.login(silent=True)
    plugin.run()

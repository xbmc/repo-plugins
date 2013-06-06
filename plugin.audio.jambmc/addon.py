#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Tristan Fischer (sphere@dersphere.de)
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

import xbmcvfs  # FIXME: Import form xbmcswift if fixed upstream
from xbmcswift2 import Plugin, xbmcgui, NotFoundException, xbmc
from resources.lib.api import JamendoApi, ApiError, ConnectionError
from resources.lib.geolocate import get_location, QuotaReached
from resources.lib.downloader import JamendoDownloader


STRINGS = {
    # Root menu entries
    'discover': 30000,
    'search': 30001,
    'show_tracks': 30002,
    'show_albums': 30003,
    'show_artists': 30004,
    'show_radios': 30005,
    'show_playlists': 30006,
    'search_tracks': 30007,
    'search_albums': 30008,
    'search_artists': 30009,
    'search_playlists': 30010,
    'show_history': 30011,
    'show_downloaded_tracks': 30012,
    'show_mixtapes': 30013,
    'show_featured_tracks': 30014,
    'show_user_artists': 30015,
    'show_user_albums': 30016,
    'show_user_tracks': 30017,
    'show_user_account': 30018,
    'show_user_playlists': 30019,
    'show_near_artists': 30020,
    'show_downloaded_albums': 30021,
    # Misc strings
    'page': 30025,
    'language': 30026,
    'instruments': 30027,
    'vartags': 30028,
    # Context menu
    'album_info': 30030,
    'song_info': 30031,
    'show_tracks_in_this_album': 30032,
    'show_albums_by_this_artist': 30033,
    'show_similar_tracks': 30034,
    'addon_settings': 30035,
    'download_track': 30036,
    'download_album': 30037,
    # Dialogs
    'search_heading_album': 30040,
    'search_heading_artist': 30041,
    'search_heading_tracks': 30042,
    'search_heading_playlist': 30043,
    'no_download_path': 30044,
    'want_set_now': 30045,
    'choose_download_folder': 30046,
    'enter_username': 30047,
    'select_user': 30048,
    'no_username_set': 30049,
    'geolocating': 30050,
    'will_send_one_request_to': 30051,
    'freegeoip_net': 30052,
    # Error dialogs
    'connection_error': 30060,
    'api_error': 30061,
    'api_returned': 30062,
    'try_again_later': 30063,
    'check_network_or': 30064,
    'try_again_later': 30065,
    # Notifications
    'download_suceeded': 30070,
    'history_empty': 30071,
    'downloads_empty': 30072,
    # Mixtapes
    'mixtape_name': 30090,
    'delete_mixtape_head': 30091,
    'are_you_sure': 30092,
    'add_to_new_mixtape': 30093,
    'add_to_mixtape_s': 30094,
    'del_from_mixtape_s': 30095,
    'select_mixtape': 30096,
    'add_mixtape': 30097,
    'add_del_track_to_mixtape': 30098,
    'delete_mixtape': 30099,
    'rename_mixtape': 30124,
    # Sort methods
    'sort_method_default': 30100,
    'sort_method_buzzrate': 30101,
    'sort_method_downloads_week': 30102,
    'sort_method_downloads_month': 30103,
    'sort_method_downloads_total': 30104,
    'sort_method_joindate_asc': 30105,
    'sort_method_joindate_desc': 30107,
    'sort_method_listens_week': 30108,
    'sort_method_listens_month': 30109,
    'sort_method_listens_total': 30110,
    'sort_method_name': 30111,
    'sort_method_popularity_week': 30112,
    'sort_method_popularity_month': 30113,
    'sort_method_popularity_total': 30114,
    'sort_method_releasedate_asc': 30115,
    'sort_method_releasedate_desc': 30116,
    # Tags
    'current_tags': 30120,
    'tag_type_genres': 30121,
    'tag_type_instruments': 30122,
    'tag_type_moods': 30123,
}


class Plugin_patched(Plugin):

    def _dispatch(self, path):
        for rule in self._routes:
            try:
                view_func, items = rule.match(path)
            except NotFoundException:
                continue
            self._request.view = view_func.__name__  # added
            self._request.view_params = items  # added
            listitems = view_func(**items)
            if not self._end_of_directory and self.handle >= 0:
                if listitems is None:
                    self.finish(succeeded=False)
                else:
                    listitems = self.finish(listitems)
            return listitems
        raise NotFoundException('No matching view found for %s' % path)


plugin = Plugin_patched()
api = JamendoApi(
    client_id='de0f381a',
    limit=plugin.get_setting('limit', int),
    image_size=plugin.get_setting(
        'image_size',
        choices=('big', 'medium', 'small')
    ),
)


########################### Static Views ######################################

@plugin.route('/')
def show_root_menu():
    fix_xbmc_music_library_view()
    items = [
        {'label': _('discover'),
         'path': plugin.url_for(endpoint='show_discover_root'),
         'thumbnail': 'DefaultMusicCompilations.png'},
        {'label': _('search'),
         'path': plugin.url_for(endpoint='show_search_root'),
         'thumbnail': 'DefaultMusicVideos.png'},
        {'label': _('show_radios'),
         'path': plugin.url_for(endpoint='show_radios'),
         'thumbnail': 'DefaultMusicGenres.png'},
        {'label': _('show_history'),
         'path': plugin.url_for(endpoint='show_history'),
         'thumbnail': 'DefaultMusicYears.png'},
        {'label': _('show_downloaded_tracks'),
         'path': plugin.url_for(endpoint='show_downloaded_tracks'),
         'thumbnail': 'DefaultMusicPlaylists.png'},
        {'label': _('show_downloaded_albums'),
         'path': plugin.url_for(endpoint='show_downloaded_albums'),
         'thumbnail': 'DefaultMusicPlaylists.png'},
        {'label': _('show_mixtapes'),
         'path': plugin.url_for(endpoint='show_mixtapes'),
         'thumbnail': 'DefaultMusicSongs.png'},
        {'label': _('show_featured_tracks'),
         'path': plugin.url_for(endpoint='show_featured_tracks'),
         'thumbnail': 'DefaultMusicAlbums.png'},
        {'label': _('show_user_account'),
         'path': plugin.url_for(endpoint='show_user_root'),
         'thumbnail': 'DefaultAddonMusic.png'},
    ]
    return add_static_items(items)


@plugin.route('/search/')
def show_search_root():
    items = [
        {'label': _('search_tracks'),
         'path': plugin.url_for(endpoint='search_tracks'),
         'thumbnail': 'DefaultMusicSongs.png'},
        {'label': _('search_albums'),
         'path': plugin.url_for(endpoint='search_albums'),
         'thumbnail': 'DefaultMusicAlbums.png'},
        {'label': _('search_artists'),
         'path': plugin.url_for(endpoint='search_artists'),
         'thumbnail': 'DefaultMusicArtists.png'},
        {'label': _('search_playlists'),
         'path': plugin.url_for(endpoint='search_playlists'),
         'thumbnail': 'DefaultMusicPlaylists.png'},
    ]
    return add_static_items(items)


@plugin.route('/discover/')
def show_discover_root():
    items = [
        {'label': _('show_tracks'),
         'path': plugin.url_for(endpoint='show_tracks'),
         'thumbnail': 'DefaultMusicSongs.png'},
        {'label': _('show_albums'),
         'path': plugin.url_for(endpoint='show_albums'),
         'thumbnail': 'DefaultMusicAlbums.png'},
        {'label': _('show_artists'),
         'path': plugin.url_for(endpoint='show_artists'),
         'thumbnail': 'DefaultMusicArtists.png'},
        {'label': _('show_playlists'),
         'path': plugin.url_for(endpoint='show_playlists'),
         'thumbnail': 'DefaultMusicPlaylists.png'},
        {'label': _('show_near_artists'),
         'path': plugin.url_for(endpoint='show_near_artists'),
         'thumbnail': 'DefaultMusicArtists.png'},
    ]
    return add_static_items(items)


@plugin.route('/user/')
def show_user_root():
    items = [
        {'label': _('show_user_artists'),
         'path': plugin.url_for(endpoint='show_user_artists'),
         'thumbnail': 'DefaultMusicArtists.png'},
        {'label': _('show_user_albums'),
         'path': plugin.url_for(endpoint='show_user_albums'),
         'thumbnail': 'DefaultMusicAlbums.png'},
        {'label': _('show_user_tracks'),
         'path': plugin.url_for(endpoint='show_user_tracks'),
         'thumbnail': 'DefaultMusicSongs.png'},
        {'label': _('show_user_playlists'),
         'path': plugin.url_for(endpoint='show_user_playlists'),
         'thumbnail': 'DefaultMusicPlaylists.png'},
    ]
    return add_static_items(items)


########################### Dynamic Views #####################################

@plugin.route('/albums/')
def show_albums():
    page = int(get_args('page', 1))
    sort_method = get_args('sort_method', 'popularity_month')
    albums = get_cached(api.get_albums, page=page, sort_method=sort_method)
    items = format_albums(albums)
    items.append(get_sort_method_switcher_item('albums', sort_method))
    items.extend(get_page_switcher_items(len(items)))
    return add_items(items)


@plugin.route('/albums/<artist_id>/')
def show_albums_by_artist(artist_id):
    page = int(get_args('page', 1))
    albums = get_cached(api.get_albums, page=page, artist_id=artist_id)
    items = format_albums(albums)
    items.extend(get_page_switcher_items(len(items)))
    return add_items(items)


@plugin.route('/artists/')
def show_artists():
    page = int(get_args('page', 1))
    sort_method = get_args('sort_method', 'popularity_month')
    artists = get_cached(api.get_artists, page=page, sort_method=sort_method)
    items = format_artists(artists)
    items.append(get_sort_method_switcher_item('artists', sort_method))
    items.extend(get_page_switcher_items(len(items)))
    return add_items(items)


@plugin.route('/artists/near/')
def show_near_artists():
    lat_long = plugin.get_setting('lat_long', str)
    while not lat_long:
        confirmed = xbmcgui.Dialog().yesno(
            _('geolocating'),
            _('will_send_one_request_to'),
            _('freegeoip_net'),
            _('are_you_sure')
        )
        if not confirmed:
            return
        try:
            location = get_location()
        except QuotaReached:
            plugin.notify(_('try_again_later'))
            return
        lat_long = '%s_%s' % (location['latitude'], location['longitude'])
        plugin.set_setting('lat_long', lat_long)
    artists = get_cached(api.get_artists_by_location, coords=lat_long)
    items = format_artists_location(artists)
    return add_items(items)


@plugin.route('/playlists/')
def show_playlists():
    page = int(get_args('page', 1))
    playlists = get_cached(api.get_playlists, page=page)
    items = format_playlists(playlists)
    items.extend(get_page_switcher_items(len(items)))
    return add_items(items, same_cover=True)


@plugin.route('/radios/')
def show_radios():
    page = int(get_args('page', 1))
    radios = get_cached(api.get_radios, page=page)
    items = format_radios(radios)
    items.extend(get_page_switcher_items(len(items)))
    return add_items(items)


@plugin.route('/tracks/')
def show_tracks():
    page = int(get_args('page', 1))
    sort_method = get_args('sort_method', 'popularity_month')
    tags = get_args('tags')
    tracks = get_cached(
        api.get_tracks,
        page=page,
        sort_method=sort_method,
        tags=tags
    )
    items = format_tracks(tracks)
    items.append(get_sort_method_switcher_item('tracks', sort_method))
    items.append(get_tag_filter_item())
    items.extend(get_page_switcher_items(len(items)))
    return add_items(items)


@plugin.route('/tracks/album/<album_id>/')
def show_tracks_in_album(album_id):
    tracks = get_cached(api.get_tracks, album_id=album_id)
    items = format_tracks(tracks)
    items.extend(get_page_switcher_items(len(items)))
    return add_items(items, same_cover=True)


@plugin.route('/tracks/featured/')
def show_featured_tracks():
    page = int(get_args('page', 1))
    sort_method = 'releasedate_desc'
    tracks = get_cached(
        api.get_tracks,
        page=page,
        sort_method=sort_method,
        featured=True
    )
    items = format_tracks(tracks)
    items.extend(get_page_switcher_items(len(items)))
    return add_items(items)


@plugin.route('/tracks/playlist/<playlist_id>/')
def show_tracks_in_playlist(playlist_id):
    playlist, tracks = get_cached(
        api.get_playlist_tracks,
        playlist_id=playlist_id
    )
    items = format_playlist_tracks(playlist, tracks)
    items.extend(get_page_switcher_items(len(items)))
    return add_items(items, same_cover=True)


@plugin.route('/tracks/similar/<track_id>/')
def show_similar_tracks(track_id):
    page = int(get_args('page', 1))
    tracks = get_cached(api.get_similar_tracks, track_id=track_id, page=page)
    items = format_similar_tracks(tracks)
    items.extend(get_page_switcher_items(len(items)))
    return add_items(items)


############################# Search Views ####################################


@plugin.route('/albums/search/')
def search_albums():
    query = get_args('input') or plugin.keyboard(
        heading=_('search_heading_album')
    )
    if query:
        albums = get_cached(api.get_albums, search_terms=query)
        items = format_albums(albums)
        return add_items(items)


@plugin.route('/artists/search/')
def search_artists():
    query = get_args('input') or plugin.keyboard(
        heading=_('search_heading_artist')
    )
    if query:
        artists = api.get_artists(search_terms=query)
        items = format_artists(artists)
        return add_items(items)


@plugin.route('/playlists/search/')
def search_playlists():
    query = get_args('input') or plugin.keyboard(
        heading=_('search_heading_playlist')
    )
    if query:
        playlists = api.get_playlists(search_terms=query)
        items = format_playlists(playlists)
        return add_items(items, same_cover=True)


@plugin.route('/tracks/search/')
def search_tracks():
    query = get_args('input') or plugin.keyboard(
        heading=_('search_heading_tracks')
    )
    if query:
        tracks = api.search_tracks(search_terms=query)
        items = format_tracks(tracks)
        return add_items(items)


############################ Jamendo Views ####################################

@plugin.route('/user/albums/')
def show_user_albums():
    user_id = get_user_account()
    if user_id:
        page = int(get_args('page', 1))
        albums = api.get_user_albums(user_id=user_id, page=page)
        items = format_albums(albums)
        items.extend(get_page_switcher_items(len(items)))
        return add_items(items)


@plugin.route('/user/artists/')
def show_user_artists():
    user_id = get_user_account()
    if user_id:
        page = int(get_args('page', 1))
        artists = api.get_user_artists(user_id=user_id, page=page)
        items = format_artists(artists)
        items.extend(get_page_switcher_items(len(items)))
        return add_items(items)


@plugin.route('/user/playlists/')
def show_user_playlists():
    user_id = get_user_account()
    if user_id:
        playlists = api.get_playlists(user_id=user_id)
        items = format_playlists(playlists)
        return add_items(items, same_cover=True)


@plugin.route('/user/set_user_account/')
def set_user_account():
    query = get_args('input') or plugin.keyboard(
        heading=_('enter_username')
    )
    if query:
        users = api.get_users(search_terms=query)
        if users:
            selected = xbmcgui.Dialog().select(
                _('select_user'), [u['name'] for u in users]
            )
            if selected >= 0:
                user = users[selected]
                plugin.set_setting('user_name', user['name'])
                plugin.set_setting('user_id', user['id'])


@plugin.route('/user/tracks/')
def show_user_tracks():
    user_id = get_user_account()
    if user_id:
        page = int(get_args('page', 1))
        tracks = api.get_user_tracks(user_id=user_id, page=page)
        items = format_tracks(tracks)
        items.extend(get_page_switcher_items(len(items)))
        return add_items(items)


############################## Downloads ######################################

@plugin.route('/downloads/albums/')
def show_downloaded_albums():
    downloads = plugin.get_storage('downloaded_albums')
    if downloads.items():
        albums = [t['data'] for t in downloads.itervalues()]
        items = format_downloaded_albums(albums)
        return add_items(items)
    plugin.notify(_('downloads_empty'))


@plugin.route('/downloads/albums/<album_id>/')
def show_downloaded_album_tracks(album_id):
    downloads = plugin.get_storage('downloaded_albums')
    album = downloads[album_id]
    tracks = [t['data'] for t in album['tracks'].itervalues()]
    items = format_tracks(tracks)
    return add_items(items, same_cover=True)


@plugin.route('/downloads/tracks/')
def show_downloaded_tracks():
    downloads = plugin.get_storage('downloaded_tracks')
    if downloads.items():
        tracks = [t['data'] for t in downloads.itervalues()]
        items = format_tracks(tracks)
        return add_items(items)
    plugin.notify(_('downloads_empty'))


############################### History #######################################

@plugin.route('/history/')
def show_history():
    history = plugin.get_storage('history')
    tracks = history.get('items', [])
    if tracks:
        items = format_tracks(reversed(tracks))
        return add_items(items)
    plugin.notify(_('history_empty'))


############################## Mixtapes #######################################

@plugin.route('/mixtapes/')
def show_mixtapes():
    mixtapes = plugin.get_storage('mixtapes')
    items = format_mixtapes(mixtapes)
    items.append(get_add_mixtape_item())
    return add_static_items(items)


@plugin.route('/mixtapes/add')
def add_mixtape(return_name=False):
    name = get_args('input') or plugin.keyboard(
        heading=_('mixtape_name')
    )
    if name:
        mixtapes = plugin.get_storage('mixtapes')
        if not name in mixtapes:
            mixtapes[name] = []
            mixtapes.sync()
        if return_name:
            return name


@plugin.route('/mixtapes/del/<mixtape_id>')
def del_mixtape(mixtape_id):
    mixtapes = plugin.get_storage('mixtapes')
    confirmed = xbmcgui.Dialog().yesno(
        _('delete_mixtape_head'),
        _('are_you_sure')
    )
    if confirmed and mixtape_id in mixtapes:
        del mixtapes[mixtape_id]
        mixtapes.sync()
        _refresh_view()


@plugin.route('/mixtapes/rename/<mixtape_id>')
def rename_mixtape(mixtape_id):
    mixtapes = plugin.get_storage('mixtapes')
    mixtape = mixtapes.pop(mixtape_id)
    new_mixtape_id = plugin.keyboard(
        heading=_('mixtape_name'),
        default=mixtape_id
    )
    mixtapes[new_mixtape_id] = mixtape
    mixtapes.sync()
    _refresh_view()


@plugin.route('/mixtapes/add/<track_id>')
def add_del_track_to_mixtape(track_id):
    mixtapes = plugin.get_storage('mixtapes')
    items = [{
        'label':_('add_to_new_mixtape'),
    }]
    for (mixtape_id, mixtape) in mixtapes.iteritems():
        track_ids = [t['id'] for t in mixtape]
        if track_id in track_ids:
            items.append({
                'label': _('del_from_mixtape_s') % mixtape_id.decode('utf-8'),
                'action': 'del',
                'mixtape_id': mixtape_id
            })
        else:
            items.append({
                'label': _('add_to_mixtape_s') % mixtape_id.decode('utf-8'),
                'action': 'add',
                'mixtape_id': mixtape_id
            })
    selected = xbmcgui.Dialog().select(
        _('select_mixtape'), [i['label'] for i in items]
    )
    if selected == 0:
        mixtape_id = add_mixtape(return_name=True)
        if mixtape_id:
            add_track_to_mixtape(mixtape_id, track_id)
    elif selected > 0:
        action = items[selected]['action']
        mixtape_id = items[selected]['mixtape_id']
        if action == 'add':
            add_track_to_mixtape(mixtape_id, track_id)
        elif action == 'del':
            del_track_from_mixtape(mixtape_id, track_id)


@plugin.route('/mixtapes/<mixtape_id>/')
def show_mixtape(mixtape_id):
    mixtapes = plugin.get_storage('mixtapes')
    tracks = mixtapes[mixtape_id]
    items = format_tracks(tracks)
    return add_items(items)


@plugin.route('/mixtapes/<mixtape_id>/add/<track_id>')
def add_track_to_mixtape(mixtape_id, track_id):
    mixtapes = plugin.get_storage('mixtapes')
    track = get_cached(api.get_track, track_id)
    mixtapes[mixtape_id].append(track)
    mixtapes.sync()


@plugin.route('/mixtapes/<mixtape_id>/del/<track_id>')
def del_track_from_mixtape(mixtape_id, track_id):
    mixtapes = plugin.get_storage('mixtapes')
    mixtapes[mixtape_id] = [
        t for t in mixtapes[mixtape_id]
        if not t['id'] == track_id
    ]
    mixtapes.sync()


########################### Callback Views ####################################

@plugin.route('/sort_methods/<entity>/')
def show_sort_methods(entity):
    sort_methods = api.get_sort_methods(entity)
    items = format_sort_methods(sort_methods, entity)
    return add_static_items(items)


@plugin.route('/tracks/tags/')
def show_tags():
    tags = api.get_tags()
    items = format_tags(tags)
    return add_static_items(items)


############################ Action Views #####################################

@plugin.route('/download/track/<track_id>')
def download_track(track_id):
    download_path = get_download_path('tracks_download_path')
    if not download_path:
        return
    show_progress = plugin.get_setting('show_track_download_progress', bool)
    downloader = JamendoDownloader(api, download_path, show_progress)
    formats = ('mp3', 'ogg', 'flac')
    audioformat = plugin.get_setting('download_format', choices=formats)
    include_cover = plugin.get_setting('download_track_cover', bool)
    tracks = downloader.download_tracks([track_id], audioformat, include_cover)
    if tracks:
        downloaded_tracks = plugin.get_storage('downloaded_tracks')
        downloaded_tracks.update(tracks)
        downloaded_tracks.sync()
        plugin.notify(msg=_('download_suceeded'))


@plugin.route('/download/album/<album_id>')
def download_album(album_id):
    download_path = get_download_path('albums_download_path')
    if not download_path:
        return
    show_progress = plugin.get_setting('show_album_download_progress', bool)
    downloader = JamendoDownloader(api, download_path, show_progress)
    formats = ('mp3', 'ogg', 'flac')
    audioformat = plugin.get_setting('download_format', choices=formats)
    include_cover = plugin.get_setting('download_album_cover', bool)
    album = downloader.download_album(album_id, audioformat, include_cover)
    if album:
        downloaded_albums = plugin.get_storage('downloaded_albums')
        downloaded_albums.update(album)
        downloaded_albums.sync()
        plugin.notify(msg=_('download_suceeded'))


@plugin.route('/play/radio/<radio_id>')
def play_radio(radio_id):
    stream_url = api.get_radio_url(radio_id)
    return plugin.set_resolved_url(stream_url)


@plugin.route('/play/track/<track_id>')
def play_track(track_id):
    add_track_to_history(track_id)
    track_url = get_downloaded_track(track_id)
    if not track_url:
        formats = ('mp3', 'ogg')
        audioformat = plugin.get_setting('playback_format', choices=formats)
        track_url = api.get_track_url(track_id, audioformat)
    return plugin.set_resolved_url(track_url)


@plugin.route('/settings')
def open_settings():
    plugin.open_settings()


############################# Formaters #######################################

def format_albums(albums):
    plugin.set_content('albums')
    items = [{
        'label': u'%s - %s' % (album['artist_name'], album['name']),
        'info': {
            'count': i + 2,
            'artist': album['artist_name'],
            'album': album['name'],
            'year': int(album.get('releasedate', '0-0-0').split('-')[0]),
        },
        'context_menu': context_menu_album(
            artist_id=album['artist_id'],
            album_id=album['id'],
        ),
        'replace_context_menu': True,
        'thumbnail': album['image'],
        'path': plugin.url_for(
            endpoint='show_tracks_in_album',
            album_id=album['id']
        )
    } for i, album in enumerate(albums)]
    return items


def format_artists(artists):
    plugin.set_content('artists')
    items = [{
        'label': artist['name'],
        'info': {
            'count': i + 2,
            'artist': artist['name'],
        },
        'context_menu': context_menu_artist(artist['id']),
        'replace_context_menu': True,
        'thumbnail': get_artist_image(artist['image']),
        'path': plugin.url_for(
            endpoint='show_albums_by_artist',
            artist_id=artist['id'],
        )
    } for i, artist in enumerate(artists)]
    return items


def format_artists_location(artists):
    plugin.set_content('artists')
    items = [{
        'label': u'%s (%s - %s)' % (
            artist['name'],
            artist['locations'][0]['country'],
            artist['locations'][0]['city'],
        ),
        'info': {
            'count': i + 2,
            'artist': artist['name'],
        },
        'context_menu': context_menu_artist(artist['id']),
        'replace_context_menu': True,
        'thumbnail': get_artist_image(artist['image']),
        'path': plugin.url_for(
            endpoint='show_albums_by_artist',
            artist_id=artist['id'],
        )
    } for i, artist in enumerate(artists)]
    return items


def format_comment(musicinfo):
    return '[CR]'.join((
        '[B]%s[/B]: %s' % (
            _('language'),
            musicinfo['lang']
        ),
        '[B]%s[/B]: %s' % (
            _('instruments'),
            ', '.join(musicinfo['tags']['instruments'])
        ),
        '[B]%s[/B]: %s' % (
            _('vartags'),
            ', '.join(musicinfo['tags']['vartags'])
        ),
    ))


def format_downloaded_albums(albums):
    plugin.set_content('albums')
    items = [{
        'label': u'%s - %s' % (album['artist_name'], album['name']),
        'info': {
            'count': i + 2,
            'artist': album['artist_name'],
            'album': album['name'],
            'year': int(album.get('releasedate', '0-0-0').split('-')[0]),
        },
        'context_menu': context_menu_album(
            artist_id=album['artist_id'],
            album_id=album['id'],
        ),
        'replace_context_menu': True,
        'thumbnail': album['image'],
        'path': plugin.url_for(
            endpoint='show_downloaded_album_tracks',
            album_id=album['id']
        )
    } for i, album in enumerate(albums)]
    return items


def format_mixtapes(mixtapes):
    items = [{
        'label': mixtape_id,
        'info': {
            'count': i + 1,
        },
        'context_menu': context_menu_mixtape(
            mixtape_id=mixtape_id,
        ),
        'replace_context_menu': True,
        'path': plugin.url_for(
            endpoint='show_mixtape',
            mixtape_id=mixtape_id
        )
    } for i, (mixtape_id, mixtape) in enumerate(mixtapes.iteritems())]
    return items


def format_playlists(playlists):
    plugin.set_content('music')
    items = [{
        'label': u'%s (%s)' % (playlist['name'], playlist['user_name']),
        'info': {
            'count': i + 2,
            'artist': playlist['user_name'],
            'album': playlist['name'],
            'year': int(playlist.get('creationdate', '0-0-0').split('-')[0]),
        },
        'context_menu': context_menu_empty(),
        'replace_context_menu': True,
        'path': plugin.url_for(
            endpoint='show_tracks_in_playlist',
            playlist_id=playlist['id']
        )
    } for i, playlist in enumerate(playlists)]
    return items


def format_playlist_tracks(playlist, tracks):
    plugin.set_content('songs')
    items = [{
        'label': track['name'],
        'info': {
            'count': i + 2,
            'tracknumber': int(track['position']),
            'duration': track['duration'],
            'title': track['name'],
        },
        'context_menu': context_menu_track(
            artist_id=track['artist_id'],
            track_id=track['id'],
            album_id=track['album_id'],
        ),
        'replace_context_menu': True,
        'is_playable': True,
        'path': plugin.url_for(
            endpoint='play_track',
            track_id=track['id']
        )
    } for i, track in enumerate(tracks)]
    return items


def format_radios(radios):
    plugin.set_content('music')
    items = [{
        'label': radio['dispname'],
        'info': {
            'count': i + 2,
        },
        'context_menu': context_menu_empty(),
        'replace_context_menu': True,
        'thumbnail': radio['image'],
        'is_playable': True,
        'path': plugin.url_for(
            endpoint='play_radio',
            radio_id=radio['id'],
        )
    } for i, radio in enumerate(radios)]
    return items


def format_similar_tracks(tracks):
    plugin.set_content('songs')
    items = [{
        'label': u'%s - %s (%s)' % (
            track['artist_name'],
            track['name'],
            track['album_name']
        ),
        'info': {
            'count': i + 2,
            'title': track['name'],
            'album': track['album_name'],
            'duration': track['duration'],
            'artist': track['artist_name'],
            'year': int(track.get('releasedate', '0-0-0').split('-')[0]),
        },
        'context_menu': context_menu_track(
            artist_id=track['artist_id'],
            track_id=track['id'],
            album_id=track['album_id']
        ),
        'replace_context_menu': True,
        'is_playable': True,
        'thumbnail': track['album_image'],
        'path': plugin.url_for(
            endpoint='play_track',
            track_id=track['id']
        )
    } for i, track in enumerate(tracks)]
    return items


def format_sort_methods(sort_methods, entity):
    original_params = plugin.request.view_params
    extra_params = {}
    current_method = get_args('sort_method')
    if 'tags' in plugin.request.args:
        extra_params['tags'] = get_args('tags')
    items = [{
        'label': (
            u'[B]%s[/B]' if sort_method == current_method else u'%s'
        ) % _('sort_method_%s' % sort_method),
        'thumbnail': 'DefaultMusicPlugins.png',
        'info': {
            'count': i,
        },
        'context_menu': context_menu_empty(),
        'replace_context_menu': True,
        'path': plugin.url_for(
            endpoint='show_%s' % entity,
            is_update='true',
            **dict(original_params, sort_method=sort_method, **extra_params)
        )
    } for i, sort_method in enumerate(sort_methods)]
    return items


def format_tags(tags):
    original_params = plugin.request.view_params
    extra_params = {}
    current_tags = [t for t in get_args('tags', '').split('+') if t]
    if 'sort_method' in plugin.request.args:
        extra_params['sort_method'] = get_args('sort_method')
    items = []
    for tag_type, type_tags in tags:
        for i, tag in enumerate(type_tags):
            tag_str = u'%s: %s' % (
                _('tag_type_%s' % tag_type),
                tag.capitalize()
            )
            if tag in current_tags:
                new_tags = '+'.join((t for t in current_tags if not t == tag))
                extra_params['tags'] = new_tags
                label = u'[B]%s[/B]' % tag_str
            else:
                new_tags = '+'.join(([tag] + current_tags))
                extra_params['tags'] = new_tags
                label = u'%s' % tag_str
            items.append({
                'label': label,
                'thumbnail': 'DefaultMusicPlugins.png',
                'info': {
                    'count': i,
                },
                'context_menu': context_menu_empty(),
                'replace_context_menu': True,
                'path': plugin.url_for(
                    endpoint='show_tracks',
                    is_update='true',
                    **dict(original_params, **extra_params)
                )
            })
    return items


def format_tracks(tracks):
    plugin.set_content('songs')
    items = [{
        'label': u'%s - %s (%s)' % (
            track['artist_name'],
            track['name'],
            track['album_name']
        ),
        'info': {
            'count': i + 2,
            'title': track['name'],
            'album': track['album_name'],
            'duration': track['duration'],
            'artist': track['artist_name'],
            'genre': u', '.join(track['musicinfo']['tags']['genres']),
            'comment': format_comment(track['musicinfo']),
            'year': int(track.get('releasedate', '0-0-0').split('-')[0]),
        },
        'context_menu': context_menu_track(
            artist_id=track['artist_id'],
            track_id=track['id'],
            album_id=track['album_id']
        ),
        'replace_context_menu': True,
        'is_playable': True,
        'thumbnail': track['album_image'],
        'path': plugin.url_for(
            endpoint='play_track',
            track_id=track['id']
        )
    } for i, track in enumerate(tracks)]
    return items


############################### Items #########################################

def get_add_mixtape_item():
    return {
        'label': u'[B]%s[/B]' % _('add_mixtape'),
        'context_menu': context_menu_empty(),
        'replace_context_menu': True,
        'info': {
            'count': 0,
        },
        'path': plugin.url_for(
            endpoint='add_mixtape',
        ),
    }


def get_page_switcher_items(items_len):
    current_page = int(get_args('page', 1))
    has_next_page = items_len >= api.current_limit
    has_previous_page = current_page > 1
    original_params = plugin.request.view_params
    extra_params = {}
    if 'sort_method' in plugin.request.args:
        extra_params['sort_method'] = get_args('sort_method')
    if 'tags' in plugin.request.args:
        extra_params['tags'] = get_args('tags', '')
    items = []
    if has_next_page:
        next_page = int(current_page) + 1
        extra_params['page'] = str(next_page)
        items.append({
            'label': u'>> %s %d >>' % (_('page'), next_page),
            'context_menu': context_menu_empty(),
            'replace_context_menu': True,
            'info': {
                'count': items_len + 2,
            },
            'path': plugin.url_for(
                endpoint=plugin.request.view,
                is_update='true',
                **dict(original_params, **extra_params)
            )
        })
    if has_previous_page:
        previous_page = int(current_page) - 1
        extra_params['page'] = str(previous_page)
        items.append({
            'label': u'<< %s %d <<' % (_('page'), previous_page),
            'context_menu': context_menu_empty(),
            'replace_context_menu': True,
            'info': {
                'count': 1,
            },
            'path': plugin.url_for(
                endpoint=plugin.request.view,
                is_update='true',
                **dict(original_params, **extra_params)
            )
        })
    return items


def get_sort_method_switcher_item(entity, current_method='default'):
    original_params = plugin.request.view_params
    extra_params = {}
    extra_params['entity'] = entity
    extra_params['sort_method'] = current_method
    if 'tags' in plugin.request.args:
        extra_params['tags'] = get_args('tags')
    return {
        'label': u'[B][[ %s ]][/B]' % _('sort_method_%s' % current_method),
        'thumbnail': 'DefaultMusicPlugins.png',
        'context_menu': context_menu_empty(),
        'replace_context_menu': True,
        'info': {
            'count': 0,
        },
        'path': plugin.url_for(
            endpoint='show_sort_methods',
            is_update='true',
            **dict(original_params, **extra_params)
        ),
    }


def get_tag_filter_item():
    current_tags = [t for t in get_args('tags', '').split('+') if t]
    extra_params = {}
    if 'sort_method' in plugin.request.args:
        extra_params['sort_method'] = get_args('sort_method')
    extra_params['tags'] = get_args('tags', '')
    return {
        'label': u'[B][[ %s: %s ]][/B]' % (
            _('current_tags'),
            len(current_tags)
        ),
        'thumbnail': 'DefaultMusicPlugins.png',
        'context_menu': context_menu_empty(),
        'replace_context_menu': True,
        'info': {
            'count': 0,
        },
        'path': plugin.url_for(
            endpoint='show_tags',
            is_update='true',
            **extra_params
        ),
    }


############################ Item-Adders ######################################

def add_items(items, same_cover=False):
    is_update = 'is_update' in plugin.request.args
    finish_kwargs = {
        'update_listing': is_update,
        'sort_methods': ('playlist_order', )
    }
    if plugin.get_setting('force_viewmode', bool) and not same_cover:
        finish_kwargs['view_mode'] = 'thumbnail'
    elif plugin.get_setting('force_viewmode_tracks', bool) and same_cover:
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


def add_static_items(items):
    for item in items:
        if not 'context_menu' in item:
            item['context_menu'] = context_menu_empty()
            item['replace_context_menu'] = True
    if 'is_update' in plugin.request.args:
        return plugin.finish(items, update_listing=True)
    else:
        return plugin.finish(items)


############################ Context-Menu #####################################

def context_menu_album(artist_id, album_id):
    return [
        (_('album_info'),
         _action('info')),
        (_('download_album'),
         _run(endpoint='download_album',
              album_id=album_id)),
        (_('show_tracks_in_this_album'),
         _view(endpoint='show_tracks_in_album',
               album_id=album_id)),
        (_('show_albums_by_this_artist'),
         _view(endpoint='show_albums_by_artist',
               artist_id=artist_id)),
        (_('addon_settings'),
         _run(endpoint='open_settings')),
    ]


def context_menu_artist(artist_id):
    return [
        (_('show_albums_by_this_artist'),
         _view(endpoint='show_albums_by_artist',
               artist_id=artist_id)),
        (_('addon_settings'),
         _run(endpoint='open_settings')),
    ]


def context_menu_empty():
    return [
        (_('addon_settings'),
         _run(endpoint='open_settings')),
    ]


def context_menu_mixtape(mixtape_id):
    return [
        (_('rename_mixtape'),
         _run(endpoint='rename_mixtape',
              mixtape_id=mixtape_id)),
        (_('delete_mixtape'),
         _run(endpoint='del_mixtape',
              mixtape_id=mixtape_id)),
        (_('addon_settings'),
         _run(endpoint='open_settings')),
    ]


def context_menu_track(artist_id, track_id, album_id):
    return [
        (_('song_info'),
         _action('info')),
        (_('download_track'),
         _run(endpoint='download_track',
              track_id=track_id)),
        (_('add_del_track_to_mixtape'),
         _run(endpoint='add_del_track_to_mixtape',
              track_id=track_id)),
        (_('show_albums_by_this_artist'),
         _view(endpoint='show_albums_by_artist',
               artist_id=artist_id)),
        (_('show_similar_tracks'),
         _view(endpoint='show_similar_tracks',
               track_id=track_id)),
        (_('show_tracks_in_this_album'),
         _view(endpoint='show_tracks_in_album',
               album_id=album_id)),
        (_('addon_settings'),
         _run(endpoint='open_settings')),
    ]


############################## Callers ########################################

def _action(arg):
    return 'XBMC.Action(%s)' % arg


def _run(*args, **kwargs):
    return 'XBMC.RunPlugin(%s)' % plugin.url_for(*args, **kwargs)


def _view(*args, **kwargs):
    return 'XBMC.Container.Update(%s)' % plugin.url_for(*args, **kwargs)


def _refresh_view():
    xbmc.executebuiltin('Container.Refresh')


############################## Helpers ########################################

def get_args(arg_name, default=None):
    return plugin.request.args.get(arg_name, [default])[0]


def get_cached(func, *args, **kwargs):
    @plugin.cached(kwargs.pop('TTL', 1440))
    def wrap(func_name, *args, **kwargs):
        return func(*args, **kwargs)
    return wrap(func.__name__, *args, **kwargs)


def get_download_path(setting_name):
    download_path = plugin.get_setting(setting_name, str)
    while not download_path:
        try_again = xbmcgui.Dialog().yesno(
            _('no_download_path'),
            _('want_set_now')
        )
        if not try_again:
            return
        download_path = xbmcgui.Dialog().browse(
            3,  # ShowAndGetWriteableDirectory
            _('choose_download_folder'),
            'music',
        )
        plugin.set_setting(setting_name, download_path)
    return download_path


def get_downloaded_track(track_id):
    tracks = plugin.get_storage('downloaded_tracks')
    if track_id in tracks:
        if xbmcvfs.exists(tracks[track_id]['file']):
            log('Track is already downloaded, playing local')
            return tracks[track_id]['file']
    albums = plugin.get_storage('downloaded_albums')
    for album in albums.itervalues():
        if track_id in album['tracks']:
            if xbmcvfs.exists(album['tracks'][track_id]['file']):
                log('Album is already downloaded, playing local')
                return album['tracks'][track_id]['file']


def get_artist_image(url):
    if url:
        # fix whitespace in some image urls
        return url.replace(' ', '%20')
    else:
        return 'DefaultActor.png'


def get_user_account():
    user_id = plugin.get_setting('user_id', str)
    while not user_id:
        try_again = xbmcgui.Dialog().yesno(
            _('no_username_set'),
            _('want_set_now')
        )
        if not try_again:
            return
        set_user_account()
        user_id = plugin.get_setting('user_id', str)
    return user_id


def add_track_to_history(track_id):
    history = plugin.get_storage('history')
    history_limit = plugin.get_setting('history_limit', int)
    if not 'items' in history:
        history['items'] = []
    if not track_id in [t['id'] for t in history['items']]:
        track = get_cached(api.get_track, track_id)
    else:
        track = [t for t in history['items'] if t['id'] == track_id][0]
        history['items'] = [
            t for t in history['items'] if not t['id'] == track_id
        ]
    history['items'].append(track)
    if history_limit:
        while len(history['items']) > history_limit:
            history['items'].pop(0)
    history.sync()


def log(text):
    plugin.log.info(text)


def fix_xbmc_music_library_view():
    # avoid context menu replacing bug by
    # switching window from musiclibrary to musicfiles
    if xbmcgui.getCurrentWindowId() == 10502:
        url = plugin.url_for(endpoint='show_root_menu')
        xbmc.executebuiltin('ReplaceWindow(MusicFiles, %s)' % url)


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        log('String is missing: %s' % string_id)
        return string_id

if __name__ == '__main__':
    try:
        plugin.run()
    except ApiError, message:
        xbmcgui.Dialog().ok(
            _('api_error'),
            _('api_returned'),
            unicode(message),
            _('try_again_later')
        )
    except ConnectionError:
        xbmcgui.Dialog().ok(
            _('connection_error'),
            '',
            _('check_network_or'),
            _('try_again_later')
        )

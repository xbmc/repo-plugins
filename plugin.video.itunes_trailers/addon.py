#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Tristan Fischer
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

from xbmcswift2 import Plugin, xbmcgui, xbmc
import xbmcvfs  # FIXME: import from swift after fixed there

from resources.lib.scraper import \
    NetworkError, MovieScraper, TrailerScraper, USER_AGENT

STRINGS = {
    'download_trailer': 30001,
    'already_downloaded': 30002,
    'add_to_cp': 30003,
    'download_in_progress': 30004,
    'add_to_trakt': 30005,
    'network_error': 30100,
    'no_download_path': 30101,
    'want_set_now': 30102,
}

CP_ADD_URL = 'plugin://plugin.video.couchpotato_manager/movies/add?title=%s'
TRAKT_ADD_URL = 'plugin://plugin.video.trakt_list_manager/movies/add?title=%s'

plugin = Plugin()


@plugin.route('/')
def show_movies():
    plugin.set_content('movies')
    source = plugin.get_setting(
        'source',
        choices=('all', 'most_recent', 'most_popular', 'exclusive')
    )
    limit = plugin.get_setting(
        'limit',
        choices=(0, 50, 100)
    )
    items = get_movies2(source, limit)
    finish_kwargs = {
        'sort_methods': ['date', 'title', 'playlist_order']
    }
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/movie/<movie_title>/<location>/show/')
def show_trailers(movie_title, location):
    play_resolution = plugin.get_setting(
        'trailer_quality',
        choices=('480', '720', '1080')
    )
    download_resolution = plugin.get_setting(
        'trailer_quality_download',
        choices=(play_resolution, '480', '720', '1080')
    )
    items = get_trailers(
        movie_title, location, play_resolution, download_resolution
    )
    finish_kwargs = {
        'sort_methods': ['date', 'playlist_order']
    }
    if plugin.get_setting('force_viewmode_trailers', bool):
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/trailer/play/<play_url>')
def play_trailer(play_url):
    downloads = plugin.get_storage('downloads')
    if play_url in downloads:
        if xbmcvfs.exists(downloads[play_url]):
            play_url = downloads[play_url]
            return plugin.set_resolved_url(play_url)
    play_url += '?|User-Agent=%s' % USER_AGENT
    return plugin.set_resolved_url(play_url)


@plugin.route('/trailer/download/<download_url>/<play_url>')
def download_trailer(download_url, play_url):
    import SimpleDownloader
    sd = SimpleDownloader.SimpleDownloader()
    sd.common.USERAGENT = USER_AGENT
    download_path = plugin.get_setting('trailer_download_path')
    while not download_path:
        try_again = xbmcgui.Dialog().yesno(
            _('no_download_path'),
            _('want_set_now')
        )
        if not try_again:
            return
        plugin.open_settings()
        download_path = plugin.get_setting('trailer_download_path')
    filename = download_url.split('/')[-1]
    params = {
        'url': download_url,
        'download_path': download_path
    }
    sd.download(filename, params)
    downloads = plugin.get_storage('downloads')
    downloads[play_url] = xbmc.translatePath(download_path + filename)
    downloads.sync()


@plugin.cached()
def get_movies2(source, limit):
    scraper = MovieScraper()
    if source == 'all':
        movies = scraper.get_all_movies(limit)
    elif source == 'most_recent':
        movies = scraper.get_most_recent_movies(limit)
    elif source == 'most_popular':
        movies = scraper.get_most_popular_movies(limit)
    elif source == 'exclusive':
        movies = scraper.get_exclusive_movies(limit)
    else:
        raise NotImplementedError

    def __context(movie_title):
        return [
            (
                _('add_to_cp'),
                'XBMC.RunPlugin(%s)' % CP_ADD_URL % movie_title
            ),
            (
                _('add_to_trakt'),
                'XBMC.RunPlugin(%s)' % TRAKT_ADD_URL % movie_title
            )
        ]

    items = [{
        'label': movie['title'],
        'thumbnail': movie['poster'],
        'info': {
            'count': i,
            'title': movie['title'],
            'originaltitle': movie['title'],
            'date': movie['postdate'],
            'year': movie['year'],
            'premiered': movie['releasedate'],
            'studio': movie['studio'],
            'mpaa': movie['rating'],
            'cast': movie.get('actors') or [],
            'director': movie.get('directors') or '',
            'genre': movie['genre'],
            'tagline': movie['types'],
            'credits': movie.get('moviesite', ''),
            'location': movie['location'],
            'types_count': movie['types_count'],
            'plot': '[CR]'.join(movie.get('actors') or [])  # workaround
        },
        'properties': {
            'fanart_image': movie['background'],
        },
        'context_menu': __context(movie['title']),
        'path': plugin.url_for(
            endpoint='show_trailers',
            movie_title=movie['title'].encode('utf-8'),
            location=movie['location']
        )
    } for i, movie in enumerate(movies)]
    return items


def get_trailers(movie_title, location, resolution_play, resolution_download):

    def get_url(urls, resolution):
        return [u for u in urls if resolution in u][0]

    scraper = TrailerScraper()
    trailers = scraper.get_trailers(location)
    downloads = plugin.get_storage('downloads')
    items = []
    for i, trailer in enumerate(trailers):
        title = '%s - %s (%s) ' % (
            movie_title, trailer['title'], trailer['duration']
        )
        play_url = get_url(trailer['urls'], resolution_play)
        download_url = get_url(trailer['urls'], resolution_download)
        if play_url in downloads:
            if xbmcvfs.exists(downloads[play_url]):
                title += _('already_downloaded')
            else:
                title += _('download_in_progress')
        items.append({
            'label': title,
            'info': {
                'count': i,
                'date': trailer['date'],
            },
            'properties': {
                'fanart_image': trailer['background'],
            },
            'context_menu': [
                (_('download_trailer'), 'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='download_trailer',
                    download_url=download_url,
                    play_url=play_url,
                ))
            ],
            'is_playable': True,
            'thumbnail': trailer['thumb'],
            'path': plugin.url_for(
                endpoint='play_trailer',
                play_url=play_url
            )
        })
    return items


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id


if __name__ == '__main__':
    try:
        plugin.run()
    except NetworkError:
        plugin.notify(msg=_('network_error'))

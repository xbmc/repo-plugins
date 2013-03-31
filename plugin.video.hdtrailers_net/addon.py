#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Tristan Fischer (sphere@dersphere.de)
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

from xbmcswift2 import Plugin, xbmcgui
from resources.lib import scraper

STRINGS = {
    'page': 30001,
    'latest': 30002,
    'most_watched': 30003,
    'top_ten': 30004,
    'all_by_initial': 30005,
    'opening': 30006,
    'coming_soon': 30007,
    'download': 30008,
    'already_downloaded': 30009,
    'download_in_progress': 30010,
    'add_to_cp': 30011,
    'no_download_path': 30130,
    'want_set_now': 30131,
    'network_error': 30150,
    'download_not_possible': 30151
}
CP_ADD_URL = 'plugin://plugin.video.couchpotato_manager/movies/add?title=%s'

plugin = Plugin()


@plugin.route('/')
def show_root_menu():
    items = [
        {'label': _('latest'),
         'path': plugin.url_for('show_movies', source='latest')},
        {'label': _('most_watched'),
         'path': plugin.url_for('show_movies', source='most_watched')},
        {'label': _('top_ten'),
         'path': plugin.url_for('show_movies', source='top_ten')},
        {'label': _('all_by_initial'),
         'path': plugin.url_for('show_initials')},
        {'label': _('opening'),
         'path': plugin.url_for('show_movies', source='opening')},
        {'label': _('coming_soon'),
         'path': plugin.url_for('show_movies', source='coming_soon')},
    ]
    return plugin.finish(items)


@plugin.route('/movies/initials/')
def show_initials():
    items = [{
        'label': initial,
        'path': plugin.url_for(
            endpoint='show_movies',
            source='initial',
            initial=initial,
        )
    } for initial in scraper.get_initials()]
    return plugin.finish(items)


@plugin.route('/movies/<source>/')
def show_movies(source):
    page = None
    if source == 'latest':
        page = int(plugin.request.args.get('page', ['1'])[0])
        movies, has_next_page = scraper.get_latest(page=page)
    elif source == 'most_watched':
        movies, has_next_page = scraper.get_most_watched()
    elif source == 'top_ten':
        movies, has_next_page = scraper.get_top_ten()
    elif source == 'initial':
        initial = plugin.request.args.get('initial', '0')[0].lower()
        movies, has_next_page = scraper.get_by_initial(initial=initial)
    elif source == 'opening':
        movies, has_next_page = scraper.get_opening_this_week()
    elif source == 'coming_soon':
        movies, has_next_page = scraper.get_coming_soon()

    items = []

    if page is not None:
        if page > 1:
            previous_page = str(page - 1)
            items.append({
                'label': '<< %s %s <<' % (_('page'), previous_page),
                'thumbnail': scraper.PREV_IMG,
                'path': plugin.url_for(
                    endpoint='show_movies',
                    source=source,
                    page=previous_page,
                    update='true'
                )
            })
        if has_next_page:
            next_page = str(page + 1)
            items.append({
                'label': '>> %s %s >>' % (_('page'), next_page),
                'thumbnail': scraper.NEXT_IMG,
                'path': plugin.url_for(
                    endpoint='show_movies',
                    source=source,
                    page=next_page,
                    update='true'
                )
            })

    items.extend([{
        'label': movie['title'],
        'thumbnail': movie['thumb'],
        'info': {
            'count': i,
        },
        'context_menu': [(
            _('add_to_cp'),
            'XBMC.RunPlugin(%s)' % CP_ADD_URL % movie['title']
        )],
        'path': plugin.url_for(
            endpoint='show_videos',
            movie_id=movie['id']
        ),
    } for i, movie in enumerate(movies)])
    content_type = plugin.get_setting(
        'content_type', choices=('videos', 'movies')
    )
    plugin.set_content(content_type)

    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'TITLE'),
        'update_listing': 'update' in plugin.request.args
    }
    if plugin.get_setting('force_viewmode', bool):
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/videos/<movie_id>/')
def show_videos(movie_id):
    movie, trailers, clips = scraper.get_videos(movie_id)
    downloads = plugin.get_storage('downloads')
    resolution = plugin.get_setting(
        'resolution', choices=('480p', '720p', '1080p')
    )
    show_trailer = plugin.get_setting('show_trailer', bool)
    show_clips = plugin.get_setting('show_clips', bool)
    show_source_in_title = plugin.get_setting('show_source_in_title', bool)

    videos = []
    if show_trailer:
        videos.extend(trailers)
    if show_clips:
        videos.extend(clips)

    items = []
    for i, video in enumerate(videos):
        if resolution in video.get('resolutions'):
            url = video['resolutions'][resolution]
            if show_source_in_title:
                title = '%s (%s)' % (video['title'], video['source'])
            else:
                title = video['title']
            if url in downloads:
                import xbmcvfs  # FIXME: import from swift after fixed there
                if xbmcvfs.exists(downloads[url]):
                    title = '%s - %s' % (title, _('already_downloaded'))
                else:
                    title = '%s - %s' % (title, _('download_in_progress'))
            items.append({
                'label': title,
                'thumbnail': movie['thumb'],
                'info': {
                    'studio': movie['title'],
                    'tagline': video['source'],
                    'date': video['date'],
                    'count': i,
                },
                'context_menu': [
                    (_('download'), 'XBMC.RunPlugin(%s)' % plugin.url_for(
                        endpoint='download_video',
                        source=video['source'],
                        url=url
                    ))
                ],
                'is_playable': True,
                'path': plugin.url_for(
                    endpoint='play_video',
                    source=video['source'],
                    url=url
                ),
            })

    finish_kwargs = {
        'sort_methods': ('DATE', 'TITLE', 'PLAYLIST_ORDER')
    }
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/video/<source>/<url>')
def play_video(source, url):
    downloads = plugin.get_storage('downloads')
    if url in downloads:
        local_file = downloads[url]
        # download was already started
        import xbmcvfs  # FIXME: import from swift after fixed there
        if xbmcvfs.exists(local_file):
            # download was also finished
            log('Using local file: %s' % local_file)
            return plugin.set_resolved_url(local_file)
    playable_url = _get_playable_url(source, url)
    log('Using URL: %s' % playable_url)
    return plugin.set_resolved_url(playable_url)


@plugin.route('/video/<source>/<url>/download')
def download_video(source, url):
    import SimpleDownloader
    sd = SimpleDownloader.SimpleDownloader()
    playable_url = _get_playable_url(source, url)
    if source == 'apple.com':
        sd.common.USERAGENT = 'QuickTime'
        playable_url = playable_url.split('|')[0]
    elif source == 'youtube.com':
        plugin.notify(msg=_('download_not_possible'))
        return
    download_path = plugin.get_setting('download_path')
    while not download_path:
        try_again = xbmcgui.Dialog().yesno(
            _('no_download_path'),
            _('want_set_now')
        )
        if not try_again:
            return
        plugin.open_settings()
        download_path = plugin.get_setting('download_path')
    filename = playable_url.split('?')[0].split('/')[-1]
    if filename == 'makeplaylist.dll':
        filename = playable_url.split('=')[-1]  # yahoo...
    params = {
        'url': playable_url,
        'download_path': download_path
    }
    sd.download(filename, params)
    downloads = plugin.get_storage('downloads')
    downloads[url] = xbmc.translatePath(download_path + filename)
    downloads.sync()


def _get_playable_url(source, raw_url, download_mode=False):
    if source == 'apple.com':
        raw_url = '%s|User-Agent=QuickTime' % raw_url
    elif source == 'youtube.com':
        import re
        video_id = re.search(r'v=(.+)&?', raw_url).groups(1)
        if download_mode:
            raw_url = (
                'plugin://plugin.video.youtube/'
                '?action=download&videoid=%s' % video_id
            )
        else:
            raw_url = (
                'plugin://plugin.video.youtube/'
                '?action=play_video&videoid=%s' % video_id
            )
    elif source == 'yahoo-redir':
        import re
        vid, res = re.search('id=(.+)&resolution=(.+)', raw_url).groups()
        raw_url = scraper.get_yahoo_url(vid, res)
    return raw_url


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id


def log(text):
    plugin.log.info(text)

if __name__ == '__main__':
    try:
        plugin.run()
    except scraper.NetworkError:
        plugin.notify(msg=_('network_error'))

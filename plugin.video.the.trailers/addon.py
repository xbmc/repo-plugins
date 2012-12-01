#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Tristan Fischer
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

# system imports
import os
import urllib

# xbmc imports
from xbmcswift import Plugin, xbmc, xbmcplugin, xbmcgui, clean_dict, xbmcaddon
import xbmcvfs
import SimpleDownloader

# addon imports
from resources.lib.exceptions import *
import resources.lib.apple_trailers as apple_trailers


__addon_name__ = 'The Trailers'
__id__ = 'plugin.video.the.trailers'

THUMBNAIL_VIEW_IDS = {'skin.confluence': 500,
                      'skin.aeon.nox': 551,
                      'skin.confluence-vertical': 500,
                      'skin.jx720': 52,
                      'skin.pm3-hd': 53,
                      'skin.rapier': 50,
                      'skin.simplicity': 500,
                      'skin.slik': 53,
                      'skin.touched': 500,
                      'skin.transparency': 53,
                      'skin.xeebo': 55}

SOURCES = [{'title': 'Apple Movie Trailers',
            'id': 'apple'}, ]

STRINGS = {'show_movie_info': 30000,
           'open_settings': 30001,
           'browse_by': 30002,
           'genre': 30003,
           'download_trailer': 30004,
           'show_downloads': 30006,
           'add_to_cp': 30007,
           'neterror_title': 30100,
           'neterror_line1': 30101,
           'neterror_line2': 30102,
           'choose_trailer_type': 30120,
           'choose_trailer_quality': 30121,
           'no_download_path': 30130,
           'please_set_path': 30131,
           'downloading_trailer': 30061}


class Plugin_mod(Plugin):

    def add_items(self, iterable, is_update=False, sort_method_ids=[],
                  override_view_mode=False):
        items = []
        urls = []
        for i, li_info in enumerate(iterable):
            items.append(self._make_listitem(**li_info))
            if self._mode in ['crawl', 'interactive', 'test']:
                print '[%d] %s%s%s (%s)' % (i + 1, '', li_info.get('label'),
                                            '', li_info.get('url'))
                urls.append(li_info.get('url'))
        if self._mode is 'xbmc':
            if override_view_mode:
                skin = xbmc.getSkinDir()
                thumbnail_view = THUMBNAIL_VIEW_IDS.get(skin)
                if thumbnail_view:
                    cmd = 'Container.SetViewMode(%s)' % thumbnail_view
                    xbmc.executebuiltin(cmd)
            xbmcplugin.addDirectoryItems(self.handle, items, len(items))
            for id in sort_method_ids:
                xbmcplugin.addSortMethod(self.handle, id)
            xbmcplugin.endOfDirectory(self.handle, updateListing=is_update)
        return urls

    def _make_listitem(self, label, label2='', iconImage='', thumbnail='',
                       path='', **options):
        li = xbmcgui.ListItem(label, label2=label2, iconImage=iconImage,
                              thumbnailImage=thumbnail, path=path)
        cleaned_info = clean_dict(options.get('info'))
        if cleaned_info:
            li.setInfo('video', cleaned_info)
        if options.get('is_playable'):
            li.setProperty('IsPlayable', 'true')
        if options.get('context_menu'):
            li.addContextMenuItems(options['context_menu'], replaceItems=True)
        return options['url'], li, options.get('is_folder', True)

plugin = Plugin_mod(__addon_name__, __id__, __file__)


@plugin.route('/', default=True)
def show_sources():
    __log('show_sources')
    if len(SOURCES) == 1:
        __log('show_sources redirecting to show_all_movies')
        url = plugin.url_for('show_all_movies',
                             source_id=SOURCES[0]['id'])
        return plugin.redirect(url)
    else:
        items = [{'label': i['title'],
                  'url': plugin.url_for('show_all_movies',
                                        source_id=i['id'])}
                 for i in SOURCES]
        return plugin.add_items(items)


@plugin.route('/<source_id>/movies/')
def show_all_movies(source_id):
    __log('show_all_movies started with source_id=%s' % source_id)
    source = __get_source(source_id)
    items = source.get_movies()
    return __add_movies(source_id, items)


@plugin.route('/<source_id>/movies/<filter_criteria>/')
def show_filter_content(source_id, filter_criteria):
    __log('show_filter_content started with source_id=%s filter_criteria=%s'
          % (source_id, filter_criteria))
    source = __get_source(source_id)
    items = [{'label': i['title'],
              'url': plugin.url_for('show_filtered_movies',
                                    source_id=source_id,
                                    filter_criteria=filter_criteria,
                                    filter_content=i['id'])}
             for i in source.get_filter_content(filter_criteria)]
    return plugin.add_items(items)


@plugin.route('/<source_id>/movies/<filter_criteria>/<filter_content>/')
def show_filtered_movies(source_id, filter_criteria, filter_content):
    __log(('show_filtered_movies started with source_id=%s '
           'filter_criteria=%s filter_content=%s')
          % (source_id, filter_criteria, filter_content))
    source = __get_source(source_id)
    if filter_criteria != 'all' and filter_content != 'all':
        items = source.get_movies(filters={filter_criteria: filter_content})
    else:
        items = source.get_movies()
    return __add_movies(source_id, items)


@plugin.route('/<source_id>/trailer/<movie_title>/play',
              mode='play', name='play_trailer')
@plugin.route('/<source_id>/trailer/<movie_title>/download',
              mode='download', name='download_trailer')
def get_trailer(source_id, movie_title, mode):
    __log('get_trailer started with mode=%s source_id=%s movie_title=%s '
          % (mode, source_id, movie_title))
    is_download = mode == 'download'
    try:
        local_path, remote_url, trailer_id = __select_check_trailer(
            source_id, movie_title, is_download=is_download,
        )
    except NoDownloadPath:
        xbmcgui.Dialog().ok(_('no_download_path'),
                            _('no_download_path'))
        return
    except (NoQualitySelected, NoTrailerSelected):
        return

    if mode == 'play':
        if plugin.get_setting('playback_mode') == '0':
            # stream
            return play_trailer(local_path, remote_url)
        elif plugin.get_setting('playback_mode') == '1':
            # download+play
            return download_play_trailer(local_path, remote_url, trailer_id)

    elif mode == 'download':
        # download in background
        return download_trailer(local_path, remote_url, trailer_id)


def ask_trailer_type(source, movie_title):
    # if the user wants to be asked, show the select dialog
    if plugin.get_setting('ask_trailer') == 'true':
        trailer_types = source.get_trailer_types(movie_title)
        if not trailer_types:
            __log('there are no trailers found for selection')
            return 'trailer'
        # is there more than one trailer_types, ask
        elif len(trailer_types) > 1:
            dialog = xbmcgui.Dialog()
            selected = dialog.select(_('choose_trailer_type'),
                                     [t['title'] for t in trailer_types])
            # if the user canceled the dialog, raise
            if selected == -1:
                raise NoTrailerSelected
        # there is only one trailer_type, don't ask and choose it
        else:
            selected = 0
        return trailer_types[selected]['id']
    # the user doesnt want to be asked, let the scraper choose the most recent
    else:
        return 'trailer'


def ask_trailer_quality(source, movie_title):
    trailer_qualities = source.get_trailer_qualities(movie_title)
    # if the user wants to be asked the quality, show the dialog
    if plugin.get_setting('ask_quality') == 'true':
        # if there are more than one trailer qualities, ask
        if len(trailer_qualities) > 1:
            dialog = xbmcgui.Dialog()
            selected = dialog.select(_('choose_trailer_quality'),
                                     [t['title'] for t in trailer_qualities])
            # if the user canceled the dialog, raise
            if selected == -1:
                raise NoQualitySelected
        # there is only one trailer quality, don't ask and choose it
        else:
            selected = 0
    # the user doesnt want to be asked, choose from settings
    else:
        selected = int(plugin.get_setting('trailer_quality'))
    return trailer_qualities[selected]['id']


def play_trailer(local_path, remote_url):
    # if remote_url is None, trailer is already downloaded - play local one
    trailer_url = remote_url or local_path
    return plugin.set_resolved_url(trailer_url)


def download_play_trailer(local_path, remote_url, trailer_id):
    # if remote_url is None, trailer is already downloaded - play it
    if not remote_url:
        return plugin.set_resolved_url(local_path)

    # we need to sleep before creating progress dialog
    xbmc.sleep(500)
    # create progress dialog
    pDialog = xbmcgui.DialogProgress()
    pDialog.create(__addon_name__)
    pDialog.update(0)

    # if there is a useragent set in the url, split it for urllib downloading
    if '?|User-Agent=' in remote_url:
        remote_url, useragent = remote_url.split('?|User-Agent=')
        __log('detected useragent:"%s"' % useragent)

        class _urlopener(urllib.URLopener):
            version = useragent
        urllib._urlopener = _urlopener()


    # split filename from local_path for dialog line
    download_path, filename = os.path.split(local_path)
    tmppath = os.path.join(
        xbmc.translatePath(plugin._plugin.getAddonInfo('profile')),
        filename,
    ).decode('utf-8')

    # TODO: change text to downloading and add the amt download speed/time?
    def _report_hook(count, blocksize, totalsize):
        percent = int(float(count * blocksize * 100) / totalsize)
        msg1 = _('downloading_trailer')
        msg2 = filename
        if pDialog.iscanceled():
            # raise KeyboardInterrupt to stop download in progress
            raise KeyboardInterrupt
        pDialog.update(percent, msg1, msg2)

    __log('start downloading: %s to path: %s' % (filename, download_path))
    try:
        if not urllib.urlretrieve(remote_url, tmppath, _report_hook):
            __log('downloading failed')
            xbmcvfs.delete(tmppath)
            pDialog.close()
            return
    # catch KeyboardInterrupt which was rised to stop the dl silently
    except KeyboardInterrupt:
        __log('downloading canceled')
        xbmcvfs.delete(tmppath)
        pDialog.close()
        return
    xbmc.sleep(100)
    __log('downloading successfully completed, start moving')
    xbmcvfs.copy(tmppath, local_path)
    xbmcvfs.delete(tmppath)
    __log('moving completed')
    pDialog.close()
    plugin.set_setting(trailer_id, local_path)
    __log('start playback')
    return plugin.set_resolved_url(local_path)


def download_trailer(local_path, remote_url, trailer_id):
     # if remote_url is None, trailer is already downloaded, do nothing
    if not remote_url:
        return
    sd = SimpleDownloader.SimpleDownloader()
    if '?|User-Agent=' in remote_url:
        remote_url, useragent = remote_url.split('?|User-Agent=')
        # Override User-Agent because SimpleDownloader doesn't support that
        # native. Downloading from apple requires QT User-Agent
        sd.common.USERAGENT = useragent
    download_path, filename = os.path.split(local_path)
    params = {'url': remote_url,
              'download_path': download_path}
    # start the download in background
    sd.download(filename, params)
    # set the setting - if the download is not finished but playback is tried,
    # the check isfile will fail and it won't be there before finish
    plugin.set_setting(trailer_id, local_path)
    __log('start downloading: %s to path: %s' % (filename, download_path))


@plugin.route('/add_to_couchpotato/<movie_title>')
def add_to_couchpotato(movie_title):
    __log('add_to_couchpotato started with movie_title=%s' % movie_title)
    cp_version = int(plugin.get_setting('cp_version'))
    if cp_version == 0:
        import resources.lib.couchpotatov1 as couchpotato
    else:
        import resources.lib.couchpotatov2 as couchpotato
    couchpotato.Main()
    return


@plugin.route('/settings/')
def open_settings():
    __log('open_settings started')
    plugin.open_settings()


def __add_movies(source_id, entries):
    __log('__add_movies start')
    items = []
    filter_criteria = __get_source(source_id).get_filter_criteria()
    for e in entries:
        movie = __format_movie(e)
        movie['context_menu'] = __movie_cm_entries(source_id,
                                                   e['title'],
                                                   filter_criteria)
        movie['url'] = plugin.url_for('play_trailer',
                                      source_id=source_id,
                                      movie_title=movie['label'])
        items.append(movie)
    sort_methods = [xbmcplugin.SORT_METHOD_DATE,
                    xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE]
    force_viewmode = plugin.get_setting('force_viewmode') == 'true'
    __log('__add_movies end')
    return plugin.add_items(items, sort_method_ids=sort_methods,
                            override_view_mode=force_viewmode)


def __format_movie(m):
    return {'label': m['title'],
            'is_playable': True,
            'is_folder': False,
            'iconImage': m.get('thumb', 'DefaultVideo.png'),
            'thumbnail': m.get('thumb', 'DefaultVideo.png'),
            'info': {'title': m.get('title'),
                     'duration': m.get('duration', '0:00'),
                     'size': int(m.get('size', 0)),
                     'mpaa': m.get('mpaa', ''),
                     'plot': m.get('plot', ''),
                     'cast': m.get('cast', []),
                     'genre': ', '.join(m.get('genre', [])),
                     'studio': m.get('studio', ''),
                     'date': m.get('post_date', ''),
                     'premiered': m.get('release_date', ''),
                     'year': int(m.get('year', 0)),
                     'rating': float(m.get('rating', 0.0)),
                     'director': m.get('director', ''),
                    },
           }


def __get_source(source_id):
    cache_path = os.path.join(
        xbmc.translatePath(plugin._plugin.getAddonInfo('profile')),
        'cache',
    )
    if not os.path.isdir(cache_path):
        os.makedirs(cache_path)
    if source_id == 'apple':
        __log('__get_source using: %s' % source_id)
        source = apple_trailers.AppleTrailers(cache_path)
        return source
    else:
        raise Exception('UNKNOWN SOURCE: %s' % source_id)


def __movie_cm_entries(source_id, movie_title, filter_criteria):
    download_url = plugin.url_for('download_trailer',
                                  source_id=source_id,
                                  movie_title=movie_title)
    show_settings_url = plugin.url_for('open_settings')
    cm_entries = [
        (_('show_movie_info'), 'XBMC.Action(Info)'),
        (_('download_trailer'), 'XBMC.RunPlugin(%s)' % download_url),
    ]
    if plugin.get_setting('cp_enable') == 'true':
        couchpotato_url = plugin.url_for('add_to_couchpotato',
                                           movie_title=movie_title)
        cm_entries.append(
           (_('add_to_cp'), 'XBMC.RunPlugin(%s)' % couchpotato_url),
        )
    for fc in filter_criteria:
        url = plugin.url_for('show_filter_content',
                             source_id=source_id,
                             filter_criteria=fc['id'])
        cm_entries.append(
            (_('browse_by') % fc['title'], 'XBMC.Container.Update(%s)' % url),
        )
    cm_entries.extend((
        (_('show_downloads'), 'XBMC.Container.Update(%s)' % ''),  # fixme
        (_('open_settings'), 'XBMC.Container.Update(%s)' % show_settings_url),
    ))
    return cm_entries


def __select_check_trailer(source_id, movie_title, is_download):
    __log(('__select_check_trailer started with source_id=%s movie_title=%s '
           'is_download=%s') % (source_id, movie_title, is_download))
    source = __get_source(source_id)
    trailer_type = ask_trailer_type(source, movie_title)

    # check if there is already a downloaded trailer in download_quality
    q_id = int(plugin.get_setting('trailer_quality_download'))
    trailer_quality = source.get_trailer_qualities(movie_title)[q_id]['id']
    download_trailer_id = '|'.join(
        (source_id, movie_title, trailer_type, trailer_quality),
    )
    local_path = plugin.get_setting(download_trailer_id)
    if local_path and xbmcvfs.exists(local_path):
        # there is a already downloaded trailer, signal with empty remote_url
        __log('trailer already downloaded, using downloaded version')
        remote_url = None
    else:
        # there is no already downloaded trailer
        if not is_download:
            # on play (and not download) the quality may differ
            trailer_quality = ask_trailer_quality(source, movie_title)
        if not plugin.get_setting('trailer_download_path'):
            xbmcgui.Dialog().ok(_('no_download_path'),
                                _('please_set_path'))
            plugin.open_settings()
        download_path = plugin.get_setting('trailer_download_path')
        if not download_path:
            __log('still no download_path set - aborting')
            raise NoDownloadPath
        safe_chars = ('-_. abcdefghijklmnopqrstuvwxyz'
                      'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        safe_title = ''.join([c for c in movie_title if c in safe_chars])
        filename = '%s-%s-%s' % (safe_title, trailer_type, trailer_quality)
        local_path = os.path.join(download_path, filename)
        remote_url = source.get_trailer(movie_title, trailer_quality,
                                        trailer_type)
    return (local_path, remote_url, download_trailer_id)


def _(s):
    s_id = STRINGS.get(s)
    if s_id:
        return plugin.get_string(s_id)
    else:
        return s


def __log(text):
    xbmc.log('%s addon: %s' % (__addon_name__, text))


if __name__ == '__main__':
    try:
        plugin.set_content('movies')
        plugin.run()
    except NetworkError as e:
        __log('NetworkError: %s' % e)
        xbmcgui.Dialog().ok(_('neterror_title'),
                            _('neterror_line1'),
                            _('neterror_line2'))

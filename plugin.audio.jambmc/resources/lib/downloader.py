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

import os
from urllib import urlretrieve

import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui

STRINGS = {
    'progress_head': 30080,
    'preparing_download': 30081,
    'downloading_to_s': 30082,
    'current_progress_s_mb': 30083,
    'current_file_s': 30084,
}

addon = xbmcaddon.Addon()


class DownloadAborted(Exception):
    pass


class JamendoDownloader(object):

    def __init__(self, api, download_path, show_progress=True):
        log('__init__ with path="%s"' % download_path)
        self.api = api
        self.download_path = download_path
        self.show_progress = show_progress
        self.temp_path = xbmc.translatePath(addon.getAddonInfo('profile'))
        if not xbmcvfs.exists(self.temp_path):
            xbmcvfs.mkdirs(self.temp_path)
        self._init_progress()

    def download_tracks(self, track_ids, audioformat, include_cover=True):
        downloaded_tracks = {}
        self._update_progress(10)
        line3 = _('downloading_to_s') % self.download_path
        self._update_progress(line3=line3)
        for i, track_id in enumerate(track_ids):
            track = self.api.get_track(track_id, audioformat=audioformat)
            filename = '%(artist)s - %(title)s (%(album)s) [%(year)s]' % {
                'artist': track['artist_name'].encode('ascii', 'ignore'),
                'title': track['name'].encode('ascii', 'ignore'),
                'album': track['album_name'].encode('ascii', 'ignore'),
                'year': track.get('releasedate', '0-0-0').split('-')[0],
            }
            if include_cover:
                cover_url = track['album_image']
                cover_filename = '%s.tbn' % filename
                line2 = _('current_file_s') % cover_filename
                self._update_progress(line2=line2)
                self._download_item(cover_url, cover_filename)
            percent = 10 + 90 / len(track_ids) * i
            self._update_progress(percent)
            track_filename = '%s.%s' % (filename, audioformat)
            line2 = _('current_file_s') % track_filename
            self._update_progress(line2=line2)
            try:
                track_file = self._download_item(
                    track['audio'],
                    track_filename
                )
            except DownloadAborted:
                return downloaded_tracks
            if track_file:
                downloaded_tracks[track_id] = {
                    'file': track_file,
                    'data': track
                }
        self._update_progress(100)
        return downloaded_tracks

    def download_album(self, album_id, audioformat, include_cover=True):
        downloaded_album = {}
        downloaded_tracks = {}
        self._update_progress(2)
        album = self.api.get_album(album_id=album_id)
        tracks = self.api.get_tracks(
            filter_dict={'album_id': album_id},
            audioformat=audioformat
        )
        self._update_progress(10)
        any_track = tracks[0]
        sub_dir = '%(artist)s - %(album)s [%(year)s]' % {
            'artist': album['artist_name'].encode('ascii', 'ignore'),
            'album': album['name'].encode('ascii', 'ignore'),
            'year': album.get('releasedate', '0-0-0').split('-')[0],
        }
        self.download_path = os.path.join(self.download_path, sub_dir)
        if not xbmcvfs.exists(self.download_path):
            xbmcvfs.mkdirs(self.download_path)
        line3 = _('downloading_to_s') % self.download_path
        self._update_progress(line3=line3)
        if include_cover:
            cover_url = any_track['album_image']
            cover_filename = 'folder.jpg'
            line2 = _('current_file_s') % cover_filename
            self._update_progress(line2=line2)
            self._download_item(cover_url, cover_filename)
        for i, track in enumerate(tracks):
            filename = '%(artist)s - %(title)s' % {
                'artist': track['artist_name'].encode('ascii', 'ignore'),
                'title': track['name'].encode('ascii', 'ignore'),
            }
            track_filename = '%s.%s' % (filename, audioformat)
            line2 = _('current_file_s') % track_filename
            self._update_progress(line2=line2)
            try:
                track_file = self._download_item(
                    track['audio'],
                    track_filename
                )
            except DownloadAborted:
                break
            if track_file:
                downloaded_tracks[track['id']] = {
                    'file': track_file,
                    'data': track
                }
            percent = 10 + 90 / len(tracks) * (i + 1)
            self._update_progress(percent)
        self._update_progress(100)
        downloaded_album[album['id']] = {
            'data': album,
            'tracks': downloaded_tracks
        }
        return downloaded_album

    def _download_item(self, url, filename):
        log('Downloading "%s" to "%s"' % (url, filename))
        temp_file = os.path.join(self.temp_path, filename)
        final_file = os.path.join(self.download_path, filename)
        try:
            urlretrieve(url, temp_file, self.__progress_hook)
        except IOError, e:
            log('IOError: "%s"' % str(e))
            return False
        except KeyboardInterrupt:
            raise DownloadAborted
        log('Moving "%s" to "%s"' % (temp_file, final_file))
        xbmcvfs.copy(temp_file, final_file)
        xbmcvfs.delete(temp_file)
        log('Item Done')
        return final_file

    def _init_progress(self):
        if self.show_progress:
            self.current_percent = 1
            self.progress_dialog = xbmcgui.DialogProgress()
            self.progress_dialog.create(_('progress_head'))
            self._update_progress(1, line1=_('preparing_download'))
        else:
            self.progress_dialog = None

    def _update_progress(self, percent=None, **kwargs):
        if self.show_progress:
            self.current_percent = percent or self.current_percent
            self.progress_dialog.update(
                self.current_percent, **kwargs
            )

    def _del_progress(self):
        if self.show_progress:
            self.progress_dialog.close()
            self.progress_dialog = None

    def __progress_hook(self, block_count, block_size, item_size):
        if self.show_progress:
            if self.progress_dialog.iscanceled():
                raise KeyboardInterrupt
            current_mb = (block_count * block_size / 1024.0 / 1024.0)
            line1 = _('current_progress_s_mb') % '%0.2f' % current_mb
            self._update_progress(line1=line1)

    def __del__(self):
        self._del_progress()


def log(msg):
    xbmc.log(u'[JemandoDownloader]: %s' % msg.encode('utf8', 'ignore'))


def _(string_id):
    if string_id in STRINGS:
        return addon.getLocalizedString(STRINGS[string_id])
    else:
        log('String is missing: %s' % string_id)
        return string_id

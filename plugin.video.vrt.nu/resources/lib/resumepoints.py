# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Implementation of ResumePoints class"""

from __future__ import absolute_import, division, unicode_literals

try:  # Python 3
    from urllib.error import HTTPError
except ImportError:  # Python 2
    from urllib2 import HTTPError

from data import SECONDS_MARGIN
from kodiutils import (container_refresh, get_cache, get_setting_bool, get_url_json, has_credentials, input_down,
                       invalidate_caches, localize, log, log_error, notification, open_url, update_cache)


class ResumePoints:
    """Track, cache and manage VRT resume points and watch list"""

    def __init__(self):
        """Initialize resumepoints, relies on XBMC vfs and a special VRT token"""
        self._data = dict()  # Our internal representation

    @staticmethod
    def is_activated():
        """Is resumepoints activated in the menu and do we have credentials ?"""
        return get_setting_bool('usefavorites', default=True) and get_setting_bool('useresumepoints', default=True) and has_credentials()

    @staticmethod
    def resumepoint_headers(url=None):
        """Generate http headers for VRT NU Resumepoints API"""
        from tokenresolver import TokenResolver
        xvrttoken = TokenResolver().get_token('X-VRT-Token', variant='user')
        headers = {}
        if xvrttoken:
            url = 'https://www.vrt.be' + url if url else 'https://www.vrt.be/vrtnu'
            headers = {
                'authorization': 'Bearer ' + xvrttoken,
                'content-type': 'application/json',
                'Referer': url,
            }
        else:
            log_error('Failed to get usertoken from VRT NU')
            notification(message=localize(30975))
        return headers

    def refresh(self, ttl=None):
        """Get a cached copy or a newer resumepoints from VRT, or fall back to a cached file"""
        if not self.is_activated():
            return
        resumepoints_json = get_cache('resume_points.json', ttl)
        if not resumepoints_json:
            resumepoints_url = 'https://video-user-data.vrt.be/resume_points'
            headers = self.resumepoint_headers()
            if not headers:
                return
            resumepoints_json = get_url_json(url=resumepoints_url, cache='resume_points.json', headers=headers)
        if resumepoints_json is not None:
            self._data = resumepoints_json

    def update(self, asset_id, title, url, watch_later=None, position=None, total=None, whatson_id=None, path=None):
        """Set program resumepoint or watchLater status and update local copy"""

        menu_caches = []
        self.refresh(ttl=5)

        # Add existing position and total if None
        if asset_id in self._data and position is None and total is None:
            position = self.get_position(asset_id)
            total = self.get_total(asset_id)

        # Update
        if (self.still_watching(position, total) or watch_later is True
                or (path and path.startswith('plugin://plugin.video.vrt.nu/play/upnext'))):
            # Normally, VRT NU resumepoints are deleted when an episode is (un)watched and Kodi GUI automatically sets
            # the (un)watched status when Kodi Player exits. This mechanism doesn't work with "Up Next" episodes because
            # these episodes are not initiated from a ListItem in Kodi GUI.
            # For "Up Next" episodes, we should never delete the VRT NU resumepoints to make sure the watched status
            # can be forced in Kodi GUI using the playcount infolabel.
            log(3, "[Resumepoints] Update resumepoint '{asset_id}' {position}/{total}", asset_id=asset_id, position=position, total=total)

            if asset_id is None:
                return True

            if watch_later is not None and position is None and total is None and watch_later is self.is_watchlater(asset_id):
                # watchLater status is not changed, nothing to do
                return True

            if watch_later is None and position == self.get_position(asset_id) and total == self.get_total(asset_id):
                # Resumepoint is not changed, nothing to do
                return True

            menu_caches.append('continue-*.json')

            if asset_id in self._data:
                # Update existing resumepoint values
                payload = self._data[asset_id]['value']
                payload['url'] = url
            else:
                # Create new resumepoint values
                payload = dict(position=0, total=100, url=url)

            if watch_later is not None:
                payload['watchLater'] = watch_later
                menu_caches.append('watchlater-*.json')

            if position is not None:
                payload['position'] = position

            if total is not None:
                payload['total'] = total

            if whatson_id is not None:
                payload['whatsonId'] = whatson_id

            # First update resumepoints to a fast local cache because online resumpoints take a longer time to take effect
            self.update_local(asset_id, dict(value=payload), menu_caches)

            # Asynchronously update online
            from threading import Thread
            Thread(target=self.update_online, name='ResumePointsUpdate', args=(asset_id, title, url, payload)).start()

        else:

            # Delete
            log(3, "[Resumepoints] Delete resumepoint '{asset_id}' {position}/{total}", asset_id=asset_id, position=position, total=total)

            # Do nothing if there is no resumepoint for this asset_id
            if not self._data.get(asset_id):
                log(3, "[Resumepoints] '{asset_id}' not present, nothing to delete", asset_id=asset_id)
                return True

            # Add menu caches
            menu_caches.append('continue-*.json')

            if self.is_watchlater(asset_id):
                menu_caches.append('watchlater-*.json')

            # Delete local representation and cache
            self.delete_local(asset_id, menu_caches)

            # Asynchronously delete online
            from threading import Thread
            Thread(target=self.delete_online, name='ResumePointsDelete', args=(asset_id,)).start()

        return True

    def update_online(self, asset_id, title, url, payload):
        """Update resumepoint online"""
        from json import dumps
        try:
            get_url_json('https://video-user-data.vrt.be/resume_points/{asset_id}'.format(asset_id=asset_id),
                         headers=self.resumepoint_headers(url), data=dumps(payload).encode())
        except HTTPError as exc:
            log_error('Failed to (un)watch episode {title} at VRT NU ({error})', title=title, error=exc)
            notification(message=localize(30977, title=title))
            return False
        return True

    def update_local(self, asset_id, resumepoint_json, menu_caches=None):
        """Update resumepoint locally and update cache"""
        self._data.update({asset_id: resumepoint_json})
        from json import dumps
        update_cache('resume_points.json', dumps(self._data))
        if menu_caches:
            invalidate_caches(*menu_caches)

    def delete_local(self, asset_id, menu_caches=None):
        """Delete resumepoint locally and update cache"""
        if asset_id in self._data:
            del self._data[asset_id]
            from json import dumps
            update_cache('resume_points.json', dumps(self._data))
            if menu_caches:
                invalidate_caches(*menu_caches)

    def delete_online(self, asset_id):
        """Delete resumepoint online"""
        try:
            result = open_url('https://video-user-data.vrt.be/resume_points/{asset_id}'.format(asset_id=asset_id),
                              headers=self.resumepoint_headers(), method='DELETE', raise_errors='all')
            log(3, "[Resumepoints] '{asset_id}' online deleted: {code}", asset_id=asset_id, code=result.getcode())
        except HTTPError as exc:
            log_error("Failed to remove '{asset_id}' from resumepoints: {error}", asset_id=asset_id, error=exc)
            return False
        return True

    def is_watchlater(self, asset_id):
        """Is a program set to watch later ?"""
        return self._data.get(asset_id, {}).get('value', {}).get('watchLater') is True

    def watchlater(self, asset_id, title, url):
        """Watch an episode later"""
        succeeded = self.update(asset_id=asset_id, title=title, url=url, watch_later=True)
        if succeeded:
            notification(message=localize(30403, title=title))
            container_refresh()

    def unwatchlater(self, asset_id, title, url, move_down=False):
        """Unwatch an episode later"""
        succeeded = self.update(asset_id=asset_id, title=title, url=url, watch_later=False)
        if succeeded:
            notification(message=localize(30404, title=title))
            # If the current item is selected and we need to move down before removing
            if move_down:
                input_down()
            container_refresh()

    def get_position(self, asset_id):
        """Return the stored position of a video"""
        return self._data.get(asset_id, {}).get('value', {}).get('position', 0)

    def get_total(self, asset_id):
        """Return the stored total length of a video"""
        return self._data.get(asset_id, {}).get('value', {}).get('total', 100)

    def get_url(self, asset_id, url_type='medium'):
        """Return the stored url a video"""
        from utils import reformat_url
        return reformat_url(self._data.get(asset_id, {}).get('value', {}).get('url'), url_type)

    def watchlater_urls(self):
        """Return all watchlater urls"""
        return [self.get_url(asset_id) for asset_id in self._data if self.is_watchlater(asset_id)]

    def resumepoints_urls(self):
        """Return all urls that have not been finished watching"""
        return [self.get_url(asset_id) for asset_id in self._data
                if self.still_watching(self.get_position(asset_id), self.get_total(asset_id))]

    @staticmethod
    def still_watching(position, total):
        """Determine if the video is still being watched"""
        if None not in (position, total) and SECONDS_MARGIN < position < (total - SECONDS_MARGIN):
            return True
        return False

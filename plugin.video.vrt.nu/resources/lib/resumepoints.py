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
    """Track, cache and manage VRT resume points and watchLater status"""

    RESUMEPOINTS_URL = 'https://ddt.profiel.vrt.be/resumePoints'
    RESUMEPOINTS_CACHE_FILE = 'resume_points_ddt.json'
    WATCHLATER_URL = 'https://video-user-data.vrt.be/resume_points'
    WATCHLATER_CACHE_FILE = 'resume_points.json'

    def __init__(self):
        """Initialize resumepoints, relies on XBMC vfs and a special VRT token"""
        self._watchlater = {}  # Our internal watchLater status representation
        self._resumepoints = {}  # Our internal Resumepoints representation

    @staticmethod
    def is_activated():
        """Is resumepoints activated in the menu and do we have credentials ?"""
        return get_setting_bool('usefavorites', default=True) and get_setting_bool('useresumepoints', default=True) and has_credentials()

    @staticmethod
    def watchlater_headers(url=None):
        """Generate http headers for VRT NU watchLater API"""
        from tokenresolver import TokenResolver
        xvrttoken = TokenResolver().get_token('X-VRT-Token', variant='user')
        headers = {}
        if xvrttoken:
            url = 'https://www.vrt.be' + url if url else 'https://www.vrt.be/vrtnu'
            headers = {
                'Authorization': 'Bearer ' + xvrttoken,
                'Content-Type': 'application/json',
                'Referer': url,
            }
        else:
            log_error('Failed to get usertoken from VRT NU')
            notification(message=localize(30975))
        return headers

    def refresh(self, ttl=None):
        """Get a cached copy or a newer resumepoints from VRT, or fall back to a cached file"""
        self.refresh_resumepoints(ttl)
        self.refresh_watchlater(ttl)

    def refresh_watchlater(self, ttl=None):
        """Get a cached copy or a newer watchLater list from VRT, or fall back to a cached file"""
        if not self.is_activated():
            return
        watchlater_json = get_cache(self.WATCHLATER_CACHE_FILE, ttl)
        if not watchlater_json:
            headers = self.watchlater_headers()
            if not headers:
                return
            watchlater_json = get_url_json(url=self.WATCHLATER_URL, cache=self.WATCHLATER_CACHE_FILE, headers=headers)
        if watchlater_json is not None:
            self._watchlater = watchlater_json

    def refresh_resumepoints(self, ttl=None):
        """Get a cached copy or a newer resumepoints from VRT, or fall back to a cached file"""
        if not self.is_activated():
            return
        resumepoints_json = get_cache(self.RESUMEPOINTS_CACHE_FILE, ttl)
        if not resumepoints_json:
            resumepoints_url = self.RESUMEPOINTS_URL + '?max=500&sortBy=-updated'
            headers = self.resumepoints_headers()
            if not headers:
                return
            resumepoints_json = get_url_json(url=resumepoints_url, cache=self.RESUMEPOINTS_CACHE_FILE, headers=headers)
        if resumepoints_json is not None:
            self._resumepoints = resumepoints_json

    @staticmethod
    def resumepoints_headers():
        """Generate http headers for VRT NU Resumepoint API"""
        from tokenresolver import TokenResolver
        vrtlogin_at = TokenResolver().get_token('vrtlogin-at')
        headers = {}
        if vrtlogin_at:
            headers = {
                'Authorization': 'Bearer ' + vrtlogin_at,
                'Content-Type': 'application/json',
            }
        else:
            log_error('Failed to get access token from VRT NU')
            notification(message=localize(30975))
        return headers

    def update_resumepoint(self, video_id, asset_str, title, position=None, total=None, path=None):
        """Set program resumepoint and update local copy"""

        if video_id is None:
            return True

        menu_caches = []
        self.refresh_resumepoints(ttl=5)

        # Add existing position and total if None
        if video_id in self._resumepoints and position is None and total is None:
            position = self.get_position(video_id)
            total = self.get_total(video_id)

        # Update
        if (self.still_watching(position, total) or (path and path.startswith('plugin://plugin.video.vrt.nu/play/upnext'))):
            # Normally, VRT NU resumepoints are deleted when an episode is (un)watched and Kodi GUI automatically sets
            # the (un)watched status when Kodi Player exits. This mechanism doesn't work with "Up Next" episodes because
            # these episodes are not initiated from a ListItem in Kodi GUI.
            # For "Up Next" episodes, we should never delete the VRT NU resumepoints to make sure the watched status
            # can be forced in Kodi GUI using the playcount infolabel.
            log(3, "[Resumepoints] Update resumepoint '{video_id}' {position}/{total}", video_id=video_id, position=position, total=total)

            if position == self.get_position(video_id) and total == self.get_total(video_id):
                # Resumepoint is not changed, nothing to do
                return True

            menu_caches.append('continue-*.json')

            # Update online
            gdpr = '{asset_str} gekeken tot {at} seconden.'.format(asset_str=asset_str, at=position)
            payload = dict(
                at=position,
                total=total,
                gdpr=gdpr,
            )
            from json import dumps
            try:
                resumepoint_json = get_url_json('{api}/{video_id}'.format(api=self.RESUMEPOINTS_URL, video_id=video_id),
                                                headers=self.resumepoints_headers(), data=dumps(payload).encode())
            except HTTPError as exc:
                log_error('Failed to update resumepoint of {title} at VRT NU ({error})', title=title, error=exc)
                notification(message=localize(30977, title=title))
                return False

            # Update local
            for idx, item in enumerate(self._resumepoints.get('items')):
                if item.get('mediaId') == video_id:
                    self._resumepoints.get('items')[idx] = resumepoint_json
                    break
            update_cache(self.RESUMEPOINTS_CACHE_FILE, dumps(self._resumepoints))
            if menu_caches:
                invalidate_caches(*menu_caches)
        else:

            # Delete
            log(3, "[Resumepoints] Delete resumepoint '{asset_str}' {position}/{total}", asset_str=asset_str, position=position, total=total)

            # Do nothing if there is no resumepoint for this video_id
            from json import dumps
            if video_id not in dumps(self._resumepoints):
                log(3, "[Resumepoints] '{video_id}' not present, nothing to delete", video_id=video_id)
                return True

            # Add menu caches
            menu_caches.append('continue-*.json')

            # Delete online
            try:
                result = open_url('{api}/{video_id}'.format(api=self.RESUMEPOINTS_URL, video_id=video_id),
                                  headers=self.resumepoints_headers(), method='DELETE', raise_errors='all')
                log(3, "[Resumepoints] '{video_id}' online deleted: {code}", video_id=video_id, code=result.getcode())
            except HTTPError as exc:
                log_error("Failed to remove resumepoint of '{video_id}': {error}", video_id=video_id, error=exc)
                return False

            # Delete local representation and cache
            for item in self._resumepoints.get('items'):
                if item.get('mediaId') == video_id:
                    self._resumepoints.get('items').remove(item)
                    break

            update_cache(self.RESUMEPOINTS_CACHE_FILE, dumps(self._resumepoints))
            if menu_caches:
                invalidate_caches(*menu_caches)
        return True

    def update_watchlater(self, asset_id, title, url, watch_later=None):
        """Set program watchLater status and update local copy"""

        menu_caches = []
        self.refresh_watchlater(ttl=5)

        # Update
        if watch_later is True:
            log(3, "[watchLater] Update {asset_id} watchLater status", asset_id=asset_id)

            if asset_id is None:
                return True

            if watch_later is not None and watch_later is self.is_watchlater(asset_id):
                # watchLater status is not changed, nothing to do
                return True

            if asset_id in self._watchlater:
                # Update existing watchLater values
                payload = self._watchlater[asset_id]['value']
                payload['url'] = url
            else:
                # Create new watchLater values
                payload = dict(position=0, total=100, url=url)

            payload['watchLater'] = watch_later
            menu_caches.append('watchlater-*.json')

            # First update watchLater status to a fast local cache because online watchLater status takes a longer time to take effect
            self.update_watchlater_local(asset_id, dict(value=payload), menu_caches)

            # Asynchronously update online
            from threading import Thread
            Thread(target=self.update_watchlater_online, name='WatchLaterUpdate', args=(asset_id, title, url, payload)).start()

        else:

            # Delete
            log(3, "[watchLater] Delete watchLater status of '{asset_id}'", asset_id=asset_id)

            # Do nothing if there is no watchLater status for this asset_id
            if not self._watchlater.get(asset_id):
                log(3, "[Resumepoints] '{asset_id}' not present, nothing to delete", asset_id=asset_id)
                return True

            # Add menu caches
            menu_caches.append('watchlater-*.json')

            # Delete local representation and cache
            self.delete_watchlater_local(asset_id, menu_caches)

            # Asynchronously delete online
            from threading import Thread
            Thread(target=self.delete_watchlater_online, name='WatchLaterDelete', args=(asset_id,)).start()

        return True

    def update_watchlater_online(self, asset_id, title, url, payload):
        """Update watchLater status online"""
        from json import dumps
        try:
            get_url_json('{api}/{asset_id}'.format(api=self.WATCHLATER_URL, asset_id=asset_id),
                         headers=self.watchlater_headers(url), data=dumps(payload).encode())
        except HTTPError as exc:
            log_error('Failed to update watchLater status of {title} at VRT NU ({error})', title=title, error=exc)
            notification(message=localize(30977, title=title))
            return False
        return True

    def update_watchlater_local(self, asset_id, resumepoint_json, menu_caches=None):
        """Update watchLater status locally and update cache"""
        self._watchlater.update({asset_id: resumepoint_json})
        from json import dumps
        update_cache(self.WATCHLATER_CACHE_FILE, dumps(self._watchlater))
        if menu_caches:
            invalidate_caches(*menu_caches)

    def delete_watchlater_local(self, asset_id, menu_caches=None):
        """Delete watchLater status locally and update cache"""
        if asset_id in self._watchlater:
            del self._watchlater[asset_id]
            from json import dumps
            update_cache(self.WATCHLATER_CACHE_FILE, dumps(self._watchlater))
            if menu_caches:
                invalidate_caches(*menu_caches)

    def delete_watchlater_online(self, asset_id):
        """Delete watchLater status online"""
        try:
            result = open_url('{api}/{asset_id}'.format(api=self.WATCHLATER_URL, asset_id=asset_id),
                              headers=self.watchlater_headers(), method='DELETE', raise_errors='all')
            log(3, "[watchLater] '{asset_id}' online deleted: {code}", asset_id=asset_id, code=result.getcode())
        except HTTPError as exc:
            log_error("Failed to remove watchLater status of '{asset_id}': {error}", asset_id=asset_id, error=exc)
            return False
        return True

    def is_watchlater(self, asset_id):
        """Is a program set to watch later ?"""
        return self._watchlater.get(asset_id, {}).get('value', {}).get('watchLater') is True

    def watchlater(self, asset_id, title, url):
        """Watch an episode later"""
        succeeded = self.update_watchlater(asset_id=asset_id, title=title, url=url, watch_later=True)
        if succeeded:
            notification(message=localize(30403, title=title))
            container_refresh()

    def unwatchlater(self, asset_id, title, url, move_down=False):
        """Unwatch an episode later"""
        succeeded = self.update_watchlater(asset_id=asset_id, title=title, url=url, watch_later=False)
        if succeeded:
            notification(message=localize(30404, title=title))
            # If the current item is selected and we need to move down before removing
            if move_down:
                input_down()
            container_refresh()

    def get_position(self, video_id):
        """Return the stored position of a video"""
        items = self._resumepoints.get('items')
        if items:
            for item in items:
                if item.get('mediaId') == video_id:
                    return item.get('at', 0)
        return 0

    def get_total(self, video_id):
        """Return the stored total length of a video"""
        items = self._resumepoints.get('items')
        if items:
            for item in items:
                if item.get('mediaId') == video_id:
                    return item.get('total', 100)
        return 100

    def get_watchlater_url(self, asset_id, url_type='medium'):
        """Return the stored url for a watchLater status asset"""
        from utils import reformat_url
        return reformat_url(self._watchlater.get(asset_id, {}).get('value', {}).get('url'), url_type)

    def watchlater_urls(self):
        """Return all watchlater urls"""
        return [self.get_watchlater_url(asset_id) for asset_id in self._watchlater if self.is_watchlater(asset_id)]

    def resumepoints_ids(self):
        """Return all ids that have not been finished watching"""
        ids = []
        items = self._resumepoints.get('items')
        if items:
            for item in items:
                if self.still_watching(item.get('at'), item.get('total')):
                    ids.append(item.get('mediaId'))
        return ids

    @staticmethod
    def still_watching(position, total):
        """Determine if the video is still being watched"""
        if None not in (position, total) and SECONDS_MARGIN < position < (total - SECONDS_MARGIN):
            return True
        return False

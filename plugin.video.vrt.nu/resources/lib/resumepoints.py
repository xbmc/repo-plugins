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
from kodiutils import (container_refresh, get_cache, get_setting_bool, get_url_json, has_credentials, invalidate_caches,
                       localize, log, log_error, notification, open_url, update_cache)


class ResumePoints:
    """Track, cache and manage VRT resume points and continue status"""

    GRAPHQL_URL = 'https://www.vrt.be/vrtnu-api/graphql/v1'
    RESUMEPOINTS_URL = 'https://ddt.profiel.vrt.be/resumePoints'
    RESUMEPOINTS_CACHE_FILE = 'resume_points.json'
    CONTINUE_CACHE_FILE = 'continue.json'

    def __init__(self):
        """Initialize resumepoints, relies on XBMC vfs and a special VRT token"""
        self._resumepoints = {}  # Our internal Resumepoints representation
        self._continue = {}  # Our internal continue status representation

    @staticmethod
    def is_activated():
        """Is resumepoints activated in the menu and do we have credentials ?"""
        return get_setting_bool('usefavorites', default=True) and get_setting_bool('useresumepoints', default=True) and has_credentials()

    def refresh(self, ttl=None):
        """Get a cached copy or a newer resumepoints from VRT, or fall back to a cached file"""
        self.refresh_resumepoints(ttl)
        self.refresh_continue(ttl)

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

    def refresh_continue(self, ttl=None):
        """Get a cached copy or a newer continue list from VRT, or fall back to a cached file"""
        if not self.is_activated():
            return
        continue_dict = get_cache(self.CONTINUE_CACHE_FILE, ttl)
        if not continue_dict:
            continue_dict = self._generate_continue_dict(self.get_continue())
        if continue_dict is not None:
            from json import dumps
            self._continue = continue_dict
            update_cache(self.CONTINUE_CACHE_FILE, dumps(self._continue))

    @staticmethod
    def resumepoints_headers():
        """Generate http headers for VRT MAX Resumepoint API"""
        from tokenresolver import TokenResolver
        access_token = TokenResolver().get_token('vrtnu-site_profile_at')
        headers = {}
        if access_token:
            headers = {
                'Authorization': 'Bearer ' + access_token,
                'Content-Type': 'application/json',
            }
        else:
            log_error('Failed to get access token from VRT MAX')
            notification(message=localize(30975))
        return headers

    def update_resumepoint(self, video_id, asset_str, title, position=None, total=None, path=None):
        """Set episode resumepoint and update local copy"""

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
            # Normally, VRT MAX resumepoints are deleted when an episode is (un)watched and Kodi GUI automatically sets
            # the (un)watched status when Kodi Player exits. This mechanism doesn't work with "Up Next" episodes because
            # these episodes are not initiated from a ListItem in Kodi GUI.
            # For "Up Next" episodes, we should never delete the VRT MAX resumepoints to make sure the watched status
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
                log_error('Failed to update resumepoint of {title} at VRT MAX ({error})', title=title, error=exc)
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

    def delete_continue(self, episode_id):
        """Delete a continue item from continue menu"""
        self._delete_continue_graphql(episode_id)
        container_refresh()

    def _delete_continue_graphql(self, episode_id):
        """Delete continue episode using GraphQL API"""
        from tokenresolver import TokenResolver
        access_token = TokenResolver().get_token('vrtnu-site_profile_at')
        result_json = {}
        if access_token:
            headers = {
                'Authorization': 'Bearer ' + access_token,
                'Content-Type': 'application/json',
            }
            graphql_query = """
                mutation listDelete($input: ListDeleteInput!) {
                  listDelete(input: $input)
                }
            """
            payload = dict(
                operationName='listDelete',
                variables=dict(
                    input=dict(
                        id=episode_id,
                        listName='verderkijken',
                    ),
                ),
                query=graphql_query,
            )
            from json import dumps
            data = dumps(payload).encode('utf-8')
            result_json = get_url_json(url=self.GRAPHQL_URL, cache=None, headers=headers, data=data, raise_errors='all')
        return result_json

    def get_continue(self):
        """Get continue using GraphQL API"""
        from tokenresolver import TokenResolver
        access_token = TokenResolver().get_token('vrtnu-site_profile_at')
        continue_json = {}
        if access_token:
            headers = {
                'Authorization': 'Bearer ' + access_token,
                'Content-Type': 'application/json',
            }
            graphql_query = """
                query ContinueEpisodes(
                  $listId: ID!
                  $endCursor: ID!
                  $pageSize: Int!
                ) {
                  list(listId: $listId) {
                    __typename
                    ... on PaginatedTileList {
                      paginated: paginatedItems(first: $pageSize, after: $endCursor) {
                        edges {
                          node {
                            __typename
                            ...episodeTile
                          }
                        }
                      }
                    }
                  }
                }
                fragment episodeTile on EpisodeTile {
                  __typename
                  id
                  title
                  episode {
                    title
                    id
                  }
                }
            """
            payload = dict(
                operationName='ContinueEpisodes',
                variables=dict(
                    listId='dynamic:/vrtnu.model.json@resume-list-video',
                    endCursor='',
                    pageSize=1000,
                ),
                query=graphql_query,
            )
            from json import dumps
            data = dumps(payload).encode('utf-8')
            continue_json = get_url_json(url=self.GRAPHQL_URL, cache=None, headers=headers, data=data, raise_errors='all')
        return continue_json

    @staticmethod
    def _generate_continue_dict(continue_json):
        """Generate a simple continue dict with episodeIds, programTitles and episodeTitles"""
        continue_dict = {}
        try:
            if continue_json:
                edges = continue_json.get('data', {}).get('list', {}).get('paginated', {}).get('edges', {})
                for item in edges:
                    episode_id = item.get('node').get('episode').get('id')
                    program_title = item.get('node').get('title')
                    episode_title = item.get('node').get('episode').get('title')
                    continue_dict[episode_id] = dict(
                        program_title=program_title,
                        episode_title=episode_title)
        except AttributeError:
            pass
        return continue_dict

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

    def continue_ids(self):
        """Return all continue episode_id's"""
        return list(self._continue.keys())

    @staticmethod
    def still_watching(position, total):
        """Determine if the video is still being watched"""
        if None not in (position, total) and SECONDS_MARGIN < position < (total - SECONDS_MARGIN):
            return True
        return False

# -*- coding: utf-8 -*-
"""

    Copyright (C) 2019-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import json
import math

from .common import get_plugin_url
from .constants import MODES
from .logger import Logger
from .utils import notify_all


class UpNext:
    LOG = Logger('UpNext')

    def __init__(self, settings, server, media_id, callback_args):
        """
        Contain the code required for using service.upnext

        :param server: plex server that has requested media id
        :param media_id: media id of the current episode
        :param callback_args: dict of arguments required for service.upnext `play_info`
        """
        self.settings = settings
        self.use_ep_thumbs = self.settings.up_next_episode_thumbs()
        self.server = server
        self.media_id = media_id
        self.callback_args = callback_args

    def run(self):
        """
        Main entry point
        Gather the required metadata and notify service.upnext
        """
        ne_metadata = None
        ce_metadata = self.get_metadata(self.media_id)

        if ce_metadata is not None:
            ce_season = int(ce_metadata.get('parentIndex'))
            ce_episode = int(ce_metadata.get('index'))
            self.LOG.debug('Found metadata for S%sE%s' %
                           (str(ce_season).zfill(2), str(ce_episode).zfill(2)))

            ne_metadata = self.get_next_episode_this_season(ce_metadata.get('parentRatingKey'),
                                                            ce_season, ce_episode)

            if ne_metadata is None:
                ne_metadata = self.get_next_season_episode_one(
                    ce_metadata.get('grandparentRatingKey'), ce_season
                )

        if ce_metadata is not None and ne_metadata is not None:
            self.LOG.debug('Found metadata for S%sE%s and S%sE%s' %
                           (ce_metadata.get('parentIndex', '0').zfill(2),
                            ce_metadata.get('index', '0').zfill(2),
                            ne_metadata.get('parentIndex', '0').zfill(2),
                            ne_metadata.get('index', '0').zfill(2)))
            up_next_data = self.get_up_next_data(ce_metadata, ne_metadata)

            self.LOG.debug('Notifying service.upnext with upnext_data:\n%s' %
                           json.dumps(up_next_data, indent=4))
            encoding = self.settings.up_next_encoding()
            notify_all(encoding, 'upnext_data', up_next_data)

    def get_metadata(self, media_id):
        """
        Get the metadata for media_id

        :param media_id: id of the media on the plex server
        """
        metadata = None
        try:
            metadata = self.server.get_metadata(media_id)
            metadata = metadata[0]
        except:  # pylint: disable=bare-except
            pass
        return metadata

    def get_next_episode_this_season(self, media_id, season, episode):
        """
        Get the metadata for the next episode of this season

        :param media_id: id of the season on the plex server
        :param season: season of `current_episode`
        :param episode: episode of `current_episode`
        """
        self.LOG.debug('Looking for S%sE%s' % (str(season).zfill(2), str(episode + 1).zfill(2)))
        next_episode = None

        episodes = self.server.get_children(media_id)
        if episodes is not None:
            found_current = False
            for video in episodes:
                if found_current:
                    self.LOG.debug('Found metadata for S%sE%s' %
                                   (str(season).zfill(2), str(video.get('index')).zfill(2)))
                    next_episode = video
                    break

                if int(video.get('index')) == episode:
                    found_current = True

        return next_episode

    def get_next_season_episode_one(self, media_id, season):
        """
        Get the metadata for the first episode of the next season

        :param media_id: id of the tv show on the plex server
        :param season: season of `current_episode`
        """
        self.LOG.debug('Looking for S%sE01' % str(season + 1).zfill(2))
        next_episode = None
        next_season = None

        seasons = self.server.get_children(media_id)

        if seasons is not None:
            self.LOG.debug('Found tv show seasons')
            for directory in seasons:
                if directory.get('index') and (int(directory.get('index')) == season + 1):
                    self.LOG.debug('Found season S%s' % str(season + 1).zfill(2))
                    next_season = directory
                    break

            if next_season is not None:
                self.LOG.debug('Looking for S%s episodes' % str(season + 1).zfill(2))
                episodes = self.server.get_children(next_season.get('ratingKey'))
                if episodes is not None:
                    for video in episodes:
                        if int(video.get('index')) == 1:
                            self.LOG.debug('Found metadata for S%sE01' % str(season + 1).zfill(2))
                            next_episode = video
                            break

        return next_episode

    def get_up_next_data(self, current_metadata, next_metadata):
        """
        Get `upnext_data` that is required for service.upnext notification

        :param current_metadata: metadata for the `current_episode`
        :param next_metadata: metadata for the `next_episode`
        """
        return {
            "current_episode": self._up_next_episode(current_metadata),
            "next_episode": self._up_next_episode(next_metadata),
            "play_url": self.playback_url({
                "media_id": next_metadata.get('ratingKey', '0'),
                "force": self.callback_args.get('force', None),
                "transcode": self.callback_args.get('transcode', False),
                "transcode_profile": self.callback_args.get('transcode_profile', 0),
                "server_uuid": self.server.uuid,
            }),
        }

    def get_image(self, url):
        """
        Get formatted image urls
        """
        if not url:
            return ''
        if url.startswith('/'):
            url = self.server.join_url(self.server.get_url_location(), url)
        return self.server.get_kodi_header_formatted_url(url)

    @staticmethod
    def playback_url(data):
        """
        Create a playback url for Up Next
        """

        data['mode'] = MODES.PLAYLIBRARY

        if data['transcode'] is None:
            data['transcode'] = 0
        data['transcode'] = int(data['transcode'])

        data['transcode_profile'] = int(data.get('transcode_profile', 0))

        return get_plugin_url(data)

    def _up_next_episode(self, metadata):
        """
        Create an episode dict from the provided metadata, this will either be
        `current_episode` or `next_episode`
        """
        episode_image = self.get_image(metadata.get('thumb'))
        fanart_image = self.get_image(metadata.get('art'))
        tvshow_image = self.get_image(metadata.get('grandparentThumb'))

        episode = {
            "episodeid": str(metadata.get('ratingKey', -1)),
            "tvshowid": str(metadata.get('grandparentRatingKey', -1)),
            "title": metadata.get('title', ''),
            "art": {
                "tvshow.poster": tvshow_image,
                "thumb": episode_image,
                "tvshow.fanart": fanart_image,
                "tvshow.landscape": episode_image if self.use_ep_thumbs else fanart_image,
                "tvshow.clearart": "",
                "tvshow.clearlogo": "",
            },
            "plot": metadata.get('summary', ''),
            "showtitle": metadata.get('grandparentTitle', ''),
            "playcount": int(metadata.get('viewCount', 0)),
            "season": str(metadata.get('parentIndex', 0)).zfill(2),
            "episode": str(metadata.get('index', 0)).zfill(2),
            "rating": float(metadata.get('rating', 0)),
            "firstaired": metadata.get('originallyAvailableAt', ''),
        }

        try:
            episode["runtime"] = math.floor(int(metadata.get('duration')) / 1000)
        except (TypeError, ValueError):
            pass

        return episode

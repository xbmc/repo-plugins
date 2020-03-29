# -*- coding: utf-8 -*-
"""
     
    Copyright (C) 2012-2019 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

import json

from . import cache, utils
from .common import kodi, log_utils
from .constants import Keys, SCOPES
from .error_handling import api_error_handler
from .twitch_exceptions import PlaybackFailed, TwitchException

from twitch import queries as twitch_queries
from twitch import oauth
from twitch.api import usher
from twitch.api import v5 as twitch
from twitch.api.parameters import Boolean, Period, ClipPeriod, Direction, Language, SortBy, StreamType, VideoSort

i18n = utils.i18n


class Twitch:
    api = twitch
    usher = usher
    queries = twitch_queries
    client_id = utils.get_client_id()
    client_secret = ''
    app_token = ''
    access_token = utils.get_oauth_token(token_only=True, required=False)
    required_scopes = SCOPES

    def __init__(self):
        self.queries.CLIENT_ID = self.client_id
        self.queries.CLIENT_SECRET = self.client_secret
        self.queries.OAUTH_TOKEN = self.access_token
        self.queries.APP_TOKEN = self.app_token
        self.client = oauth.clients.MobileClient(self.client_id, self.client_secret)
        if self.access_token:
            if not self.valid_token(self.client_id, self.access_token, self.required_scopes):
                self.queries.OAUTH_TOKEN = ''
                self.access_token = ''

    @cache.cache_method(cache_limit=1)
    def valid_token(self, client_id, token, scopes):  # client_id, token used for unique caching only
        token_check = self.root()
        while True:
            if not token_check['token']['valid']:
                result = kodi.Dialog().ok(heading=i18n('oauth_token'), line1=i18n('invalid_token'),
                                          line2=i18n('get_new_oauth_token') % (i18n('settings'), i18n('login'), i18n('get_oauth_token')))
                log_utils.log('Error: Current OAuth token is invalid.', log_utils.LOGERROR)
                return False
            else:
                if token_check['token']['client_id'] == self.client_id:
                    if token_check['token']['authorization']:
                        token_scopes = token_check['token']['authorization']['scopes']
                        missing_scopes = [value for value in scopes if value not in token_scopes]
                        if len(missing_scopes) > 0:
                            result = kodi.Dialog().ok(heading=i18n('oauth_token'), line1=i18n('missing_scopes') % missing_scopes,
                                                      line2=i18n('get_new_oauth_token') % (i18n('settings'), i18n('login'), i18n('get_oauth_token')))
                            log_utils.log('Error: Current OAuth token is missing required scopes |%s|' % missing_scopes, log_utils.LOGERROR)
                            return False
                        else:
                            return True
                    else:
                        return False
                else:
                    matches_default = token_check['token']['client_id'] == utils.get_client_id(default=True)
                    message = 'Token created using default Client-ID |%s|' % str(matches_default)
                    log_utils.log('Error: OAuth Client-ID mismatch: %s' % message, log_utils.LOGERROR)
                    if matches_default:
                        result = kodi.Dialog().ok(heading=i18n('oauth_token'), line1=i18n('client_id_mismatch'), line2=i18n('ok_to_resolve'))
                        utils.clear_client_id()
                        self.client_id = utils.get_client_id(default=True)
                        self.queries.CLIENT_ID = self.client_id
                        self.client = oauth.clients.MobileClient(self.client_id, self.client_secret)
                    else:
                        result = kodi.Dialog().ok(heading=i18n('oauth_token'), line1=i18n('client_id_mismatch'),
                                                  line2=i18n('get_new_oauth_token') % (i18n('settings'), i18n('login'), i18n('get_oauth_token')))
                        return False

    @api_error_handler
    def root(self):
        results = self.api.root()
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=1)
    def get_user(self, token):  # token used for unique caching only
        results = self.api.users.user()
        return self.error_check(results)

    def get_user_id(self):
        results = self.get_user(self.access_token)
        return results.get(Keys._ID)

    def get_username(self):
        results = self.get_user(self.access_token)
        return results.get(Keys.NAME)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_user_ids(self, logins):
        results = self.api.users.users(logins=logins)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_featured_streams(self, offset, limit):
        results = self.api.streams.get_featured(offset=offset, limit=limit)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_top_games(self, offset, limit):
        results = self.api.games.get_top(offset=offset, limit=limit)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_collections(self, channel_id, cursor, limit):
        results = self.api.collections.get_collections(channel_id=channel_id, cursor=cursor, limit=limit)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_all_streams(self, stream_type, platform, offset, limit, language=Language.ALL):
        results = self.api.streams.get_all(stream_type=stream_type, platform=platform, offset=offset, limit=limit, language=language)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_all_teams(self, offset, limit):
        results = self.api.teams.get_active(offset=offset, limit=limit)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_followed_channels(self, user_id, offset, limit, direction=Direction.DESC, sort_by=SortBy.LAST_BROADCAST):
        results = self.api.users.get_follows(user_id=user_id, limit=limit, offset=offset, direction=direction, sort_by=sort_by)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_top_videos(self, offset, limit, broadcast_type, period=Period.WEEK, game=None):
        results = self.api.videos.get_top(limit=limit, offset=offset, game=game, broadcast_type=broadcast_type, period=period)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_followed_clips(self, cursor, limit, trending=Boolean.TRUE, language=Language.ALL):
        results = self.api.clips.get_followed(limit=limit, cursor=cursor, trending=trending, language=language)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_top_clips(self, cursor, limit, channel=None, game=None, period=ClipPeriod.WEEK, trending=Boolean.TRUE, language=Language.ALL):
        results = self.api.clips.get_top(limit=limit, cursor=cursor, channels=channel, games=game, period=period, trending=trending, language=language)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_channel_videos(self, channel_id, offset, limit, broadcast_type, sort_by=VideoSort.TIME, language=Language.ALL):
        results = self.api.channels.get_videos(channel_id=channel_id, limit=limit, offset=offset, broadcast_type=broadcast_type, sort_by=sort_by, language=language)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_collection_videos(self, collection_id):
        results = self.api.collections.by_id(collection_id=collection_id, include_all=Boolean.FALSE)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_game_streams(self, game, offset, limit, language=Language.ALL):
        results = self.api.streams.get_all(game=game, limit=limit, offset=offset, language=language)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_channel_search(self, search_query, offset, limit):
        results = self.api.search.channels(search_query=search_query, limit=limit, offset=offset)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_stream_search(self, search_query, offset, limit):
        results = self.api.search.streams(search_query=search_query, limit=limit, offset=offset)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_game_search(self, search_query):
        results = self.api.search.games(search_query=search_query)
        return self.error_check(results)

    @api_error_handler
    def check_follow(self, channel_id):
        user_id = self.get_user_id()
        results = self.api.users.check_follows(user_id=user_id, channel_id=channel_id)
        return self.return_boolean(results)

    @api_error_handler
    def follow(self, channel_id):
        user_id = self.get_user_id()
        results = self.api.users.follow_channel(user_id=user_id, channel_id=channel_id)
        return self.error_check(results)

    @api_error_handler
    def unfollow(self, channel_id):
        user_id = self.get_user_id()
        results = self.api.users.unfollow_channel(user_id=user_id, channel_id=channel_id)
        return self.error_check(results)

    @api_error_handler
    def check_follow_game(self, game):
        username = self.get_username()
        results = self.api.games._check_follows(username=username, name=game, headers=self.get_private_credential_headers())
        return self.return_boolean(results)

    @api_error_handler
    def follow_game(self, game):
        username = self.get_username()
        results = self.api.games._follow(username=username, name=game, headers=self.get_private_credential_headers())
        return self.error_check(results)

    @api_error_handler
    def unfollow_game(self, game):
        username = self.get_username()
        results = self.api.games._unfollow(username=username, name=game, headers=self.get_private_credential_headers())
        return self.error_check(results)

    @api_error_handler
    def check_subscribed(self, channel_id):
        user_id = self.get_user_id()
        results = self.api.users.check_subscription(channel_id=channel_id, user_id=user_id)
        return self.return_boolean(results)

    @api_error_handler
    def blocks(self, offset, limit):
        user_id = self.get_user_id()
        results = self.api.users.get_blocks(user_id=user_id, limit=limit, offset=offset)
        return self.error_check(results)

    @api_error_handler
    def block_user(self, target_id):
        user_id = self.get_user_id()
        results = self.api.users.block_user(user_id=user_id, target_id=target_id)
        return self.error_check(results)

    @api_error_handler
    def unblock_user(self, target_id):
        user_id = self.get_user_id()
        results = self.api.users.unblock_user(user_id=user_id, target_id=target_id)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_video_by_id(self, video_id):
        results = self.api.videos.by_id(video_id=video_id)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def _get_video_token(self, video_id):
        results = self.usher.vod_token(video_id=video_id)
        if 'token' in results:
            results = json.loads(results['token'])
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_clip_by_slug(self, slug):
        results = self.api.clips.by_slug(slug=slug)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_channel_stream(self, channel_id):
        results = self.api.streams.by_id(channel_id=channel_id, stream_type=StreamType.ALL)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_streams_by_channels(self, names, offset, limit):
        query = self.queries.ApiQuery('streams')
        query.add_param('offset', offset)
        query.add_param('limit', limit)
        query.add_param('channel', names)
        results = query.execute()
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_followed_games(self, name, offset, limit):
        results = self.api.games._get_followed(username=name, limit=limit, offset=offset, headers=self.get_private_credential_headers())
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_followed_streams(self, stream_type, offset, limit):
        results = self.api.streams.get_followed(stream_type=stream_type, limit=limit, offset=offset)
        results = self.error_check(results)
        if isinstance(results.get('streams'), list):
            results['streams'] = sorted(results['streams'],
                                        key=lambda x: int(x.get('viewers', 0)),
                                        reverse=True)
        return results

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_vod(self, video_id):
        results = self.usher.video(video_id, headers=self.get_private_credential_headers())
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_clip(self, slug):
        return self.usher.clip(slug, headers=self.get_private_credential_headers())

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_live(self, name):
        results = self.usher.live(name, headers=self.get_private_credential_headers())
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def live_request(self, name):
        if not utils.inputstream_adpative_supports('EXT-X-DISCONTINUITY'):
            results = self.usher.live_request(name, platform='ps4', headers=self.get_private_credential_headers())
        else:
            results = self.usher.live_request(name, headers=self.get_private_credential_headers())
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def video_request(self, video_id):
        if not utils.inputstream_adpative_supports('EXT-X-DISCONTINUITY'):
            results = self.usher.video_request(video_id, platform='ps4', headers=self.get_private_credential_headers())
        else:
            results = self.usher.video_request(video_id, headers=self.get_private_credential_headers())
        return self.error_check(results)

    def get_user_blocks(self):
        limit = 100
        offset = 0

        user_blocks = []
        while True:
            temp = self.blocks(offset, limit)
            if len(temp[Keys.BLOCKS]) == 0:
                break
            for user in temp[Keys.BLOCKS]:
                user_blocks.append((user[Keys.USER][Keys._ID],
                                    user[Keys.USER][Keys.DISPLAY_NAME] if user[Keys.USER][Keys.DISPLAY_NAME] else user[Keys.USER][Keys.NAME]))
            offset += limit
            if temp[Keys.TOTAL] <= offset:
                break

        return user_blocks

    @staticmethod
    def error_check(results):
        if 'stream' in results and results['stream'] is None:
            raise PlaybackFailed()

        if 'error' in results:
            raise TwitchException(results)

        return results

    @staticmethod
    def return_boolean(results):
        if ('error' in results) and (results['status'] == 404):
            return False
        elif 'error' in results:
            raise TwitchException(results)
        else:
            return True

    @staticmethod
    def get_private_credential_headers():
        headers = {}
        private_client_id = utils.get_private_client_id()
        private_oauth_token = utils.get_private_oauth_token()
        if private_client_id:
            headers['Client-ID'] = private_client_id
            headers['Authorization'] = ''
        if private_oauth_token:
            headers['Authorization'] = 'OAuth {token}'.format(token=private_oauth_token)
            headers['Client-ID'] = ''
        return headers

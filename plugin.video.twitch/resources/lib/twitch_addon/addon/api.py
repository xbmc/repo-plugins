# -*- coding: utf-8 -*-
"""
     
    Copyright (C) 2012-2019 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

import json
import sys

from . import cache, utils
from .common import kodi, log_utils
from .constants import Keys, SCOPES
from .error_handling import api_error_handler
from .twitch_exceptions import PlaybackFailed, TwitchException

from twitch import queries as twitch_queries
from twitch import oauth
from twitch.api import usher
from twitch.api import helix as twitch
from twitch.api.parameters import Language, Boolean, VideoSort, PeriodHelix

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

        self.private_client_id = utils.get_private_client_id()
        self.private_access_token = utils.get_private_oauth_token()
        if self.private_access_token:
            if not self.valid_private_token(self.private_client_id, self.private_access_token):
                self.private_access_token = ''

        if self.access_token:
            if not self.valid_token(self.client_id, self.access_token, self.required_scopes):
                self.queries.OAUTH_TOKEN = ''
                self.access_token = ''

    @cache.cache_method(cache_limit=1)
    def valid_token(self, client_id, token, scopes):  # client_id, token used for unique caching only
        token_check = self.root()
        while True:
            if token_check.get('status') == 401:
                kodi.notify(i18n('oauth_token'), i18n('invalid_expired_token'))
                return False
            if token_check['client_id'] == self.client_id:
                if token_check['scopes']:
                    token_scopes = token_check['scopes']
                    missing_scopes = [value for value in scopes if value not in token_scopes]
                    if len(missing_scopes) > 0:
                        result = kodi.Dialog().ok(
                            i18n('oauth_token'),
                            '[CR]'.join([
                                i18n('missing_scopes') % missing_scopes,
                                i18n('get_new_oauth_token') %
                                (i18n('settings'), i18n('login'), i18n('get_oauth_token'))
                            ])
                        )
                        log_utils.log('Error: Current OAuth token is missing required scopes |%s|' % missing_scopes,
                                      log_utils.LOGERROR)
                        return False
                    else:
                        return True
                else:
                    return False
            else:
                matches_default = token_check['client_id'] == utils.get_client_id(default=True)
                log_utils.log('Error: OAuth Client-ID mismatch', log_utils.LOGERROR)
                if matches_default:
                    _ = kodi.Dialog().ok(
                        i18n('oauth_token'),
                        '[CR]'.join([i18n('client_id_mismatch'), i18n('ok_to_resolve')])
                    )
                    utils.clear_client_id()
                    self.client_id = utils.get_client_id(default=True)
                    self.queries.CLIENT_ID = self.client_id
                    self.client = oauth.clients.MobileClient(self.client_id, self.client_secret)
                else:
                    _ = kodi.Dialog().ok(
                        i18n('oauth_token'),
                        '[CR]'.join([
                            i18n('client_id_mismatch'),
                            i18n('get_new_oauth_token') %
                            (i18n('settings'), i18n('login'), i18n('get_oauth_token'))
                        ])
                    )
                    return False

    @cache.cache_method(cache_limit=1)
    def valid_private_token(self, client_id, token):  # client_id used for unique caching only
        token_check = self.validate(token)
        if token_check['client_id'] != self.private_client_id:
            matches_default = token_check['client_id'] == utils.get_client_id(default=True)
            log_utils.log('Error: Private OAuth Client-ID mismatch', log_utils.LOGERROR)
            if matches_default:
                log_utils.log('Private OAuth token matches add-on Client-ID', log_utils.LOGDEBUG)
                if not self.access_token:
                    self.access_token = self.private_access_token
                    self.queries.OAUTH_TOKEN = self.private_access_token
                    kodi.set_setting('oauth_token_helix', self.private_access_token)
                    kodi.set_setting('private_oauth_token', '')
                    self.private_access_token = ''
            return False
        return True

    @api_error_handler
    def root(self):
        results = oauth.validation.validate(self.access_token)
        return self.error_check(results)

    @api_error_handler
    def validate(self, token):
        results = oauth.validation.validate(token)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=1)
    def get_user(self, token):  # token used for unique caching only
        results = self.api.users.get_users()
        return self.error_check(results)

    def get_user_id(self):
        results = self.get_user(self.access_token)
        results = results.get('data', [{}])[0]
        return results.get(Keys.ID)  # NOQA

    def get_username(self):
        results = self.get_user(self.access_token)
        results = results.get('data', [{}])[0]
        return results.get(Keys.LOGIN)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_user_ids(self, logins):
        results = self.api.users.get_users(user_login=logins)
        results = self.error_check(results)
        ids = []
        for user in results.get(Keys.DATA, [{}]):
            if user.get(Keys.ID):
                ids.append(user.get(Keys.ID))
        return ids

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_users(self, user_ids):
        results = self.api.users.get_users(user_id=user_ids)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_top_games(self, after='MA==', before='MA==', first=20):
        results = self.api.games.get_top(after=after, before=before, first=first)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_all_streams(self, game_id=None, user_id=None, user_login=None, language=Language.ALL, after='MA==',
                        before='MA==', first=20):
        if game_id is None:
            game_id = []
        if user_login is None:
            user_login = []
        if user_id is None:
            user_id = []
        results = self.api.streams.get_streams(game_id=game_id, user_id=user_id, user_login=user_login,
                                               language=language, after=after, before=before, first=first)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_followed_channels(self, user_id='', after='MA==', first=20):
        results = self.api.users.get_follows(user_id=user_id, after=after, first=first)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_top_videos(self, broadcast_type, period=PeriodHelix.ALL,
                       after='MA==', before='MA==', first=20, game_id='', user_id=''):
        if not period:
            period = PeriodHelix.ALL
        results = self.api.videos.get_videos(user_id=user_id, game_id=game_id, broadcast_type=broadcast_type,
                                             period=period, after=after, before=before, first=first)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_clips(self, broadcaster_id='', game_id='', after='MA==', first=20):
        results = self.api.clips.get_clip(broadcaster_id=broadcaster_id, game_id=game_id, after=after, first=first)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_channel_videos(self, user_id, broadcast_type, period=PeriodHelix.ALL, after='MA==', before='MA==', first=20,
                           sort_by=VideoSort.TIME, language=Language.ALL):
        if not period:
            period = PeriodHelix.ALL
        results = self.api.videos.get_videos(user_id=user_id, broadcast_type=broadcast_type, period=period,
                                             after=after, before=before, first=first, sort_order=sort_by,
                                             language=language)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_game_streams(self, game_id=None, language=Language.ALL, after='MA==', before='MA==', first=20):
        if game_id is None:
            game_id = []
        results = self.api.streams.get_streams(game_id=game_id, language=language, after=after,
                                               before=before, first=first)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_channel_search(self, search_query, after='MA==', first=20):
        results = self.api.search.get_channels(search_query=search_query, after=after, first=first,
                                               live_only=Boolean.FALSE)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_stream_search(self, search_query, after='MA==', first=20):
        results = self.api.search.get_channels(search_query=search_query, after=after, first=first,
                                               live_only=Boolean.TRUE)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_game_search(self, search_query, after='MA==', first=20):
        results = self.api.search.get_categories(search_query=search_query, after=after, first=first)
        return self.error_check(results)

    @api_error_handler
    def check_follow(self, channel_id):
        user_id = self.get_user_id()
        results = self.api.users.get_follows(from_id=user_id, to_id=channel_id)
        results = self.error_check(results)
        return results.get('total') == 1

    @api_error_handler
    def follow(self, channel_id):
        results = self.api.users._follow_channel(channel_id=channel_id, headers=self.get_private_credential_headers())  # NOQA
        return self.error_check(results, private=True)

    @api_error_handler
    def unfollow(self, channel_id):
        results = self.api.users._unfollow_channel(channel_id=channel_id, headers=self.get_private_credential_headers())  # NOQA
        return self.error_check(results, private=True)

    @api_error_handler
    def follow_game(self, game_id):
        results = self.api.games._follow(game_id=game_id, headers=self.get_private_credential_headers())  # NOQA
        return self.error_check(results, private=True)

    @api_error_handler
    def unfollow_game(self, game_id):
        results = self.api.games._unfollow(game_id=game_id, headers=self.get_private_credential_headers())  # NOQA
        return self.error_check(results, private=True)

    @api_error_handler
    def check_subscribed(self, channel_id):
        user_id = self.get_user_id()
        results = self.api.subscriptions.get_user_subscriptions(broadcaster_id=channel_id, user_id=user_id)
        return self.return_boolean(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_video_by_id(self, video_id):
        results = self.api.videos.get_videos(video_id=video_id)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def _get_video_token(self, video_id):
        results = self.usher.vod_token(video_id=video_id, headers=self.get_private_credential_headers())
        if 'token' in results:
            results = json.loads(results['token'])
        return self.error_check(results, private=True)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_clip_by_slug(self, slug):
        results = self.api.clips.get_clip(clip_id=slug)
        return self.error_check(results)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_channel_stream(self, channel_id):
        results = self.api.streams.get_streams(user_id=channel_id)
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
    def get_followed_games(self, limit):
        results = self.api.games._get_followed(limit=limit, headers=self.get_private_credential_headers())  # NOQA
        return self.error_check(results, private=True)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_followed_streams(self, user_id, after='MA==', first=20):
        results = self.api.streams.get_followed(user_id=user_id, after=after, first=first)
        results = self.error_check(results)
        return results

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_vod(self, video_id):
        results = self.usher.video(video_id, headers=self.get_private_credential_headers())
        return self.error_check(results, private=True)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_clip(self, slug):
        return self.usher.clip(slug, headers=self.get_private_credential_headers())

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def get_live(self, name):
        results = self.usher.live(name, headers=self.get_private_credential_headers())
        return self.error_check(results, private=True)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def live_request(self, name):
        if not utils.inputstream_adpative_supports('EXT-X-DISCONTINUITY'):
            results = self.usher.live_request(name, platform='ps4', headers=self.get_private_credential_headers())
        else:
            results = self.usher.live_request(name, headers=self.get_private_credential_headers())
        return self.error_check(results, private=True)

    @api_error_handler
    @cache.cache_method(cache_limit=cache.limit)
    def video_request(self, video_id):
        if not utils.inputstream_adpative_supports('EXT-X-DISCONTINUITY'):
            results = self.usher.video_request(video_id, platform='ps4', headers=self.get_private_credential_headers())
        else:
            results = self.usher.video_request(video_id, headers=self.get_private_credential_headers())
        return self.error_check(results, private=True)

    @staticmethod
    def error_check(results, private=False):
        if isinstance(results, list):
            return results

        payload = results.copy()
        if 'response' in payload:
            payload = payload['response']

        if ('error' in payload) and (payload['status'] == 401):
            if not private:
                _ = kodi.Dialog().ok(
                    i18n('oauth_heading'),
                    i18n('oauth_message') % (i18n('settings'), i18n('login'), i18n('get_oauth_token'))
                )
            else:
                _ = kodi.Dialog().ok(
                    i18n('private_oauth_heading'),
                    i18n('private_oauth_message') % (i18n('settings'), i18n('login'), i18n('private_credentials'))
                )
            sys.exit()
        if 'stream' in payload and payload['stream'] is None:
            raise PlaybackFailed()

        if 'error' in payload:
            raise TwitchException(payload)

        return payload

    @staticmethod
    def return_boolean(results):
        if ('error' in results.get('response', {})) and (results['response']['status'] == 404):
            return False
        elif 'error' in results.get('response', {}):
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

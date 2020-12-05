# -*- coding: utf-8 -*-
""" Solocoo Channel API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging

from requests import HTTPError

from resources.lib.solocoo import SOLOCOO_API, util, StreamInfo
from resources.lib.solocoo.exceptions import NotAvailableInOfferException, UnavailableException
from resources.lib.solocoo.util import parse_channel, parse_program

_LOGGER = logging.getLogger(__name__)

ASSET_TYPE_CHANNEL = 'Channel'
ASSET_TYPE_PROGRAM = 'EPG'


class ChannelApi:
    """ Solocoo Channel API """

    def __init__(self, auth):
        """ Initialisation of the class.

        :param resources.lib.solocoo.auth.AuthApi auth: The Authentication object
        """
        self._auth = auth
        self._tokens = self._auth.login()
        self._tenant = self._auth.get_tenant()

    def get_channels(self, filter_unavailable=True, filter_pin=False):
        """ Get all channels.

        :param bool filter_unavailable: Hide unavailable channels.
        :param bool filter_pin:         Hide PIN-protected channels.

        :returns:                       A list of all channels.
        :rtype: list[resources.lib.solocoo.util.Channel]
        """
        entitlements = self._auth.list_entitlements()
        offers = entitlements.get('offers', [])

        # Fetch channel listing from TV API
        reply = util.http_get(SOLOCOO_API + '/bouquet', token_bearer=self._tokens.jwt_token)
        data = json.loads(reply.text)

        # Fetch channel listing from CAPI
        # We need this for the stationid that we can use to fetch a better EPG
        capi_reply = util.http_get(
            'https://{domain}/{env}/capi.aspx'.format(domain=self._tenant.get('domain'), env=self._tenant.get('env')),
            params={
                'z': 'epg',
                'f_format': 'clx',  # channel listing
                'd': 3,
                'v': 3,
                'u': self._tokens.device_serial,
                'a': self._tenant.get('app'),
                # 111 = BIT_CHANNEL_DETAIL_ID + BIT_CHANNEL_DETAIL_NUMBER + BIT_CHANNEL_DETAIL_STATIONID +
                #       BIT_CHANNEL_DETAIL_TITLE + BIT_CHANNEL_DETAIL_GENRES + BIT_CHANNEL_DETAIL_FLAGS
                'cs': 111,
                'lng': 'nl_BE',
                'streams': 15,
            },
            token_cookie=self._tokens.aspx_token)
        capi_data = json.loads(capi_reply.text)
        station_ids = {row.get('number'): str(row.get('stationid')) for row in capi_data[0][1]}

        # Parse list to Channel objects
        channels = [
            parse_channel(channel.get('assetInfo', {}), offers, station_ids.get(channel.get('assetInfo', {}).get('params', {}).get('lcn')))
            for channel in data.get('channels', []) if channel.get('alias', False) is False
        ]

        # Filter unavailable channels
        if filter_unavailable:
            channels = [channel for channel in channels if channel.available is not False]

        # Filter PIN protected channels
        if filter_pin:
            channels = [channel for channel in channels if channel.pin is False]

        return channels

    def get_asset(self, asset_id):
        """ Get channel information for the requested asset.

        :param str asset_id:            The ID of the asset

        :returns:                       The requested asset.
        :rtype: resources.lib.solocoo.util.Channel|resources.lib.solocoo.util.Program
        """
        reply = util.http_get(SOLOCOO_API + '/assets/{asset_id}'.format(asset_id=asset_id),
                              token_bearer=self._tokens.jwt_token)
        data = json.loads(reply.text)

        if data.get('type') == ASSET_TYPE_PROGRAM:
            return parse_program(data)

        if data.get('type') == ASSET_TYPE_CHANNEL:
            return parse_channel(data)

        raise Exception('Unknown asset type: %s' % data.get('type'))

    def get_asset_by_locid(self, loc_id):
        """ Convert a locId to a assetId.

        :param str loc_id:              The locID of the asset.

        :returns:                       The matching Asset.
        :rtype: resources.lib.solocoo.util.Channel|resources.lib.solocoo.util.Program
        """
        reply = util.http_get(
            'https://{domain}/{env}/capi.aspx'.format(domain=self._tenant.get('domain'), env=self._tenant.get('env')),
            params={
                'z': 'converttotvapi',
                'locId': loc_id,
                'type': 'EPGProgram',
            },
            token_cookie=self._tokens.aspx_token)
        data = json.loads(reply.text)
        return self.get_asset(data.get('assetId'))

    def get_replay(self, channel_id):
        """ Get a list of programs that are replayable from the given channel.

        :param str channel_id:          The ID of the asset.

        :returns:                       A list of Programs.
        :rtype: list[resources.lib.solocoo.util.Program]
        """
        entitlements = self._auth.list_entitlements()
        offers = entitlements.get('offers', [])

        # Execute query
        reply = util.http_get(SOLOCOO_API + '/assets',
                              params={
                                  'query': 'replay,groupedseries,station,' + channel_id,
                                  'limit': 1000,
                              },
                              token_bearer=self._tokens.jwt_token)
        data = json.loads(reply.text)

        # Parse list to Program objects
        programs = [
            parse_program(program, offers)
            for program in data.get('assets', [])
        ]

        return programs

    def get_series(self, series_id):
        """ Get a list of programs of the specified series.

        :param str series_id:          The ID of the series.

        :returns:                       A list of Programs.
        :rtype: list[resources.lib.solocoo.util.Program]
        """
        entitlements = self._auth.list_entitlements()
        offers = entitlements.get('offers', [])

        # Execute query
        reply = util.http_get(SOLOCOO_API + '/assets',
                              params={
                                  'query': 'replayepisodes,' + series_id,
                                  'limit': 1000,
                              },
                              token_bearer=self._tokens.jwt_token)
        data = json.loads(reply.text)

        # Parse list to Program objects
        programs = [
            parse_program(program, offers)
            for program in data.get('assets', [])
        ]

        return programs

    def get_stream(self, asset_id):
        """ Get stream information for the requested asset.

        :param str asset_id:            The ID of the asset

        :returns:                       Information on how to play this asset.
        :rtype: StreamInfo
        """
        _LOGGER.debug('Requesting stream info for channel %s', asset_id)
        try:
            reply = util.http_post(
                SOLOCOO_API + '/assets/{asset_id}/play'.format(asset_id=asset_id),
                token_bearer=self._tokens.jwt_token,
                data={
                    "player": {
                        "name": "Bitmovin",
                        "version": "8.22.0",
                        "capabilities": {
                            "mediaTypes": ["DASH"],  # ["DASH", "HLS", "MSSS", "Unspecified"]
                            "drmSystems": ["Widevine"]
                        },
                        "drmSystems": ["Widevine"]
                    }
                }
            )
        except HTTPError as ex:
            if ex.response.status_code == 402:
                raise NotAvailableInOfferException
            if ex.response.status_code == 403:
                raise UnavailableException
            if ex.response.status_code == 404:
                raise UnavailableException
            raise

        data = json.loads(reply.text)

        stream = StreamInfo(
            url=data.get('url'),
            protocol=data.get('mediaType'),
            drm_protocol=data.get('drm', {}).get('system'),
            drm_license_url=data.get('drm', {}).get('licenseUrl'),
            drm_certificate=data.get('drm', {}).get('cert'),
        )

        return stream

    def verify_pin(self, pin):
        """ Verify the PIN.

        :param str pin:                 The PIN to validate.

        :returns:                       Returns true if the PIN is valid.
        :rtype: boolean
        """
        try:
            util.http_post(
                SOLOCOO_API + '/pin/parental/verify',
                token_bearer=self._tokens.jwt_token,
                data={
                    "pin": pin,
                }
            )
            return True
        except HTTPError:
            return False

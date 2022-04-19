# -*- coding: utf-8 -*-
""" Solocoo EPG API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
from datetime import datetime, timedelta

import dateutil.parser
import dateutil.tz

from resources.lib.solocoo import SOLOCOO_API, util
from resources.lib.solocoo.util import parse_program, parse_program_capi

_LOGGER = logging.getLogger(__name__)


class EpgApi:
    """ Solocoo EPG API """

    # Request this many channels at the same time
    EPG_CHUNK_SIZE = 40
    EPG_CAPI_CHUNK_SIZE = 100

    EPG_NO_BROADCAST = 'Geen uitzending'

    def __init__(self, auth):
        """ Initialisation of the class.

        :param resources.lib.solocoo.auth.AuthApi auth: The Authentication object
        """
        self._auth = auth
        self._tokens = self._auth.get_tokens()
        self._tenant = self._auth.get_tenant()

    def get_guide(self, channels, date_from=None, date_to=None):
        """ Get the guide for the specified channels and date.

        :param list|str channels:       A single channel or a list of channels to fetch.
        :param str|datetime date_from:  The date of the guide we want to fetch.
        :param str|datetime date_to:    The date of the guide we want to fetch.

        :returns:                       A parsed dict with EPG data.
        :rtype: dict[str, list[resources.lib.solocoo.util.Program]]
        """
        # Allow to specify one channel, and we map it to a list
        if not isinstance(channels, list):
            channels = [channels]

        entitlements = self._auth.list_entitlements()
        offers = entitlements.get('offers', [])

        # Generate dates in UTC format
        if date_from is not None:
            date_from = self._parse_date(date_from)
        else:
            date_from = self._parse_date('today')

        if date_to is not None:
            date_to = self._parse_date(date_to)
        else:
            date_to = (date_from + timedelta(days=1))

        programs = {}

        for i in range(0, len(channels), self.EPG_CHUNK_SIZE):
            _LOGGER.debug('Fetching EPG at index %d', i)

            reply = util.http_get(SOLOCOO_API + '/schedule',
                                  params={
                                      'channels': ','.join(channels[i:i + self.EPG_CHUNK_SIZE]),
                                      'from': date_from.isoformat().replace('+00:00', ''),
                                      'until': date_to.isoformat().replace('+00:00', ''),
                                      'maxProgramsPerChannel': 2147483647,  # The android app also does this
                                  },
                                  token_bearer=self._tokens.jwt_token)
            data = json.loads(reply.text)

            # Parse to a dict (channel: list[Program])
            programs.update({channel: [parse_program(program, offers) for program in programs]
                             for channel, programs in data.get('epg', []).items()})

        return programs

    def get_guide_with_capi(self, channels, date_from=None, date_to=None):
        """ Get the guide for the specified channels and date. Lookup by stationid.

        :param list|str channels:       A single channel or a list of channels to fetch.
        :param str|datetime date_from:  The date of the guide we want to fetch.
        :param str|datetime date_to:    The date of the guide we want to fetch.

        :returns:                       A parsed dict with EPG data.
        :rtype: dict[str, list[resources.lib.solocoo.util.Program]]
        """
        # Allow to specify one channel, and we map it to a list
        if not isinstance(channels, list):
            channels = [channels]

        # Python 2.7 doesn't support .timestamp(), and windows doesn't do '%s', so we need to calculate it ourself
        epoch = datetime(1970, 1, 1, tzinfo=dateutil.tz.UTC)

        # Generate dates in UTC format
        if date_from is not None:
            date_from = self._parse_date(date_from)
        else:
            date_from = self._parse_date('today')
        date_from_posix = str(int((date_from - epoch).total_seconds())) + '000'

        if date_to is not None:
            date_to = self._parse_date(date_to)
        else:
            date_to = (date_from + timedelta(days=1))
        date_to_posix = str(int((date_to - epoch).total_seconds())) + '000'

        programs = {}

        for i in range(0, len(channels), self.EPG_CAPI_CHUNK_SIZE):
            _LOGGER.debug('Fetching EPG at index %d', i)

            reply = util.http_get(
                'https://{domain}/{env}/capi.aspx'.format(domain=self._tenant.get('domain'), env=self._tenant.get('env')),
                params={
                    'z': 'epg',
                    'f_format': 'pg',  # program guide
                    'v': 3,  # version
                    'u': self._tokens.device_serial,
                    'a': self._tenant.get('app'),
                    's': '!'.join(channels[i:i + self.EPG_CAPI_CHUNK_SIZE]),  # station id's separated with a !
                    'f': date_from_posix,  # from timestamp
                    't': date_to_posix,  # to timestamp
                    # 736763 = BIT_EPG_DETAIL_ID | BIT_EPG_DETAIL_TITLE | BIT_EPG_DETAIL_DESCRIPTION | BIT_EPG_DETAIL_AGE |
                    #          BIT_EPG_DETAIL_CATEGORY | BIT_EPG_DETAIL_START | BIT_EPG_DETAIL_END | BIT_EPG_DETAIL_FLAGS |
                    #          BIT_EPG_DETAIL_COVER | BIT_EPG_DETAIL_SEASON_NO | BIT_EPG_DETAIL_EPISODE_NO |
                    #          BIT_EPG_DETAIL_SERIES_ID | BIT_EPG_DETAIL_GENRES | BIT_EPG_DETAIL_CREDITS | BIT_EPG_DETAIL_FORMATS
                    'cs': 736763,
                    'lng': 'nl_BE',
                },
                token_cookie=self._tokens.aspx_token)

            data = json.loads(reply.text)

            # Parse to a dict (channel: list[Program])
            programs.update({channel: [parse_program_capi(program, self._tenant) for program in programs]
                             for channel, programs in data[1].items()})

        return programs

    @staticmethod
    def _parse_date(date):
        """ Parse the passed date to a real date.

        :param str|datetime date:       The date to parse.

        :returns:                       A parsed date.
        :rtype: datetime
         """
        if isinstance(date, datetime):
            return date

        if date == 'today':
            date_obj = datetime.today()
        elif date == 'yesterday':
            date_obj = (datetime.today() + timedelta(days=-1))
        elif date == 'tomorrow':
            date_obj = (datetime.today() + timedelta(days=1))
        else:
            date_obj = dateutil.parser.parse(date)

        # Mark as midnight in UTC
        date_obj = date_obj.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=dateutil.tz.tzlocal())
        date_obj = date_obj.astimezone(dateutil.tz.UTC)
        return date_obj

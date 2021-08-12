# -*- coding: utf-8 -*-
""" VTM GO EPG API """
from __future__ import absolute_import, division, unicode_literals

import json
import logging
from datetime import datetime, timedelta
from uuid import uuid4

import dateutil.parser
import dateutil.tz

from resources.lib import kodiutils
from resources.lib.vtmgo import util

_LOGGER = logging.getLogger(__name__)


class EpgChannel:
    """ Defines an Channel with EPG information """

    def __init__(self, uuid=None, key=None, name=None, logo=None, broadcasts=None):
        """
        :type uuid: str
        :type key: str
        :type name: str
        :type logo: str
        :type broadcasts: list[EpgBroadcast]
        """
        self.uuid = uuid
        self.key = key
        self.name = name
        self.logo = logo
        self.broadcasts = broadcasts

    def __repr__(self):
        return "%r" % self.__dict__


class EpgBroadcast:
    """ Defines an EPG broadcast"""

    def __init__(self, uuid=None, playable_type=None, title=None, time=None, duration=None, thumb=None, description=None, live=None, rerun=None, tip=None,
                 program_uuid=None, playable_uuid=None, channel_uuid=None, airing=None, genre=None):
        """
        :type uuid: str
        :type playable_type: str
        :type title: str
        :type time: datetime
        :type duration: int
        :type thumb: str
        :type description: str
        :type live: str
        :type rerun: str
        :type tip: str
        :type program_uuid: str
        :type playable_uuid: str
        :type channel_uuid: str
        :type airing: bool
        :type genre: str
        """
        self.uuid = uuid
        self.playable_type = playable_type
        self.title = title
        self.time = time
        self.duration = duration
        self.thumb = thumb
        self.description = description
        self.live = live
        self.rerun = rerun
        self.tip = tip
        self.program_uuid = program_uuid
        self.playable_uuid = playable_uuid
        self.channel_uuid = channel_uuid
        self.airing = airing
        self.genre = genre

    def __repr__(self):
        return "%r" % self.__dict__


class VtmGoEpg:
    """ VTM GO EPG API """
    EPG_URL = 'https://vtm.be/tv-gids/api/v2/broadcasts/{date}'

    EPG_NO_BROADCAST = 'Geen uitzending'

    def __init__(self):
        """ Initialise object """
        util.SESSION.cookies.set('authId', str(uuid4()))

    def get_epg(self, channel, date=None):
        """ Load EPG information for the specified channel and date.
        :type channel: str
        :type date: str
        :rtype: EpgChannel
        """
        date = self._parse_date(date)

        response = util.http_get(self.EPG_URL.format(date=date))
        epg = json.loads(response.text)

        # We get an EPG for all channels, but we only return the requested channel.
        for epg_channel in epg.get('channels', []):
            if epg_channel.get('seoKey') == channel:
                return EpgChannel(
                    name=epg_channel.get('name'),
                    key=epg_channel.get('seoKey'),
                    logo=epg_channel.get('channelLogoUrl'),
                    uuid=epg_channel.get('uuid'),
                    broadcasts=[
                        self._parse_broadcast(broadcast)
                        for broadcast in epg_channel.get('broadcasts', [])
                        if broadcast.get('title', '') != self.EPG_NO_BROADCAST
                    ]
                )

        raise Exception('Channel %s not found in the EPG' % channel)

    def get_epgs(self, date=None):
        """ Load EPG information for the specified date.
        :type date: str
        :rtype: EpgChannel[]
        """
        date = self._parse_date(date)

        response = util.http_get(self.EPG_URL.format(date=date))
        epg = json.loads(response.text)

        # We get an EPG for all channels
        return [
            EpgChannel(
                name=epg_channel.get('name'),
                key=epg_channel.get('seoKey'),
                logo=epg_channel.get('channelLogoUrl'),
                uuid=epg_channel.get('uuid'),
                broadcasts=[
                    self._parse_broadcast(broadcast)
                    for broadcast in epg_channel.get('broadcasts', [])
                    if broadcast.get('title', '') != self.EPG_NO_BROADCAST
                ]
            )
            for epg_channel in epg.get('channels', [])
        ]

    @staticmethod
    def _parse_date(date):
        """ Parse the passed date to a real date """
        if date is None:
            # Fetch today when no date is specified
            return datetime.today().strftime('%Y-%m-%d')
        if date == 'yesterday':
            return (datetime.today() + timedelta(days=-1)).strftime('%Y-%m-%d')
        if date == 'today':
            return datetime.today().strftime('%Y-%m-%d')
        if date == 'tomorrow':
            return (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        return date

    def get_broadcast(self, channel, timestamp):
        """ Load EPG information for the specified channel and date.
        :type channel: str
        :type timestamp: str
        :rtype: EpgBroadcast
        """
        # Parse to a real datetime
        timestamp = dateutil.parser.parse(timestamp).replace(tzinfo=dateutil.tz.gettz('CET'))

        # Load guide info for this date
        epg = self.get_epg(channel=channel, date=timestamp.strftime('%Y-%m-%d'))

        # Find a matching broadcast
        for broadcast in epg.broadcasts:
            if broadcast.time <= timestamp < (broadcast.time + timedelta(seconds=broadcast.duration)):
                return broadcast

        return None

    @staticmethod
    def _parse_broadcast(broadcast_json):
        """ Parse the epg data.
        :type broadcast_json: dict
        :rtype: EpgBroadcast
        """
        # The broadcast_json.get('duration') field doesn't include the advertisements, so the total time is incorrect
        duration = (broadcast_json.get('to') - broadcast_json.get('from')) / 1000

        # Check if this broadcast is currently airing
        timestamp = datetime.now(dateutil.tz.tzlocal())
        start = dateutil.parser.parse(broadcast_json.get('fromIso') + 'Z').astimezone(dateutil.tz.gettz('CET'))
        airing = bool(start <= timestamp < (start + timedelta(seconds=duration)))

        # Genre
        if broadcast_json.get('subGenres'):
            genre = broadcast_json.get('subGenres', [])[0]
        else:
            genre = broadcast_json.get('genre')

        return EpgBroadcast(
            uuid=broadcast_json.get('uuid'),
            playable_type=broadcast_json.get('playableType'),
            playable_uuid=broadcast_json.get('playableUuid'),
            title=broadcast_json.get('title'),
            time=start,
            duration=duration,
            thumb=broadcast_json.get('imageUrl'),
            description=broadcast_json.get('synopsis'),
            live=broadcast_json.get('live'),
            rerun=broadcast_json.get('rerun'),
            tip=broadcast_json.get('tip'),
            program_uuid=broadcast_json.get('programUuid'),
            channel_uuid=broadcast_json.get('channelUuid'),
            airing=airing,
            genre=genre,
        )

    @staticmethod
    def get_dates(date_format):
        """ Return a dict of dates.
        :rtype: list[dict]
        """
        dates = []
        today = datetime.today()

        # The API provides 2 days in the past and 8 days in the future
        for i in range(-2, 8):
            day = today + timedelta(days=i)

            if i == -1:
                dates.append({
                    'title': '%s, %s' % (kodiutils.localize(30301), day.strftime(date_format)),  # Yesterday
                    'key': 'yesterday',
                    'date': day.strftime('%d.%m.%Y'),
                    'highlight': False,
                })
            elif i == 0:
                dates.append({
                    'title': '%s, %s' % (kodiutils.localize(30302), day.strftime(date_format)),  # Today
                    'key': 'today',
                    'date': day.strftime('%d.%m.%Y'),
                    'highlight': True,
                })
            elif i == 1:
                dates.append({
                    'title': '%s, %s' % (kodiutils.localize(30303), day.strftime(date_format)),  # Tomorrow
                    'key': 'tomorrow',
                    'date': day.strftime('%d.%m.%Y'),
                    'highlight': False,
                })
            else:
                dates.append({
                    'title': day.strftime(date_format),
                    'key': day.strftime('%Y-%m-%d'),
                    'date': day.strftime('%d.%m.%Y'),
                    'highlight': False,
                })

        return dates

# -*- coding: utf-8 -*-
""" Solocoo utility functions """

from __future__ import absolute_import, division, unicode_literals

import logging
from datetime import datetime

import dateutil.parser
import dateutil.tz
import requests
from requests import HTTPError

from resources.lib import kodiutils
from resources.lib.solocoo import Channel, Credit, Epg, EpgSeries, VodEpisode, VodGenre, VodMovie, VodSeries
from resources.lib.solocoo.exceptions import InvalidTokenException

_LOGGER = logging.getLogger(__name__)

# Setup a static session that can be reused for all calls
SESSION = requests.Session()
SESSION.headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
}

PROXIES = kodiutils.get_proxies()


def find_image(images, image_type):
    """ Find the largest image of the specified type.

    :param List[dict] images:           A list of all images.
    :param str image_type:              Type of image (la=landscape, po=portrait, lv=live).

    :returns:                           The requested image in the highest quality.
    :rtype: str
    """
    for size in ['lg', 'md', 'sm']:
        for image in images:
            if image.get('type') == image_type and image.get('size') == size:
                return image.get('url')

    return None


def check_deals_entitlement(deals, offers):
    """ Check if we have are entitled to play an item.

    :param List[object] deals:          A list of deals.
    :param List[str] offers:            A list of the offers that we have.

    :returns:                           Returns False if we have no deal, True if we have a non-expiring deal or a datetime with the expiry date.
    :rtype: bool|datetime
    """

    # The API supports multiple deals for an item. A deal contains a list of offers it applies on, it can
    # also have a start and end time to indicate when the deal is active.
    #
    # This allows to define if something is playable for a specific offer, and to indicate the timeslot when this is
    # available.
    #
    # Example:
    # deals = [{'offers': ['0', '1', '2', '11'], 'start': '2020-07-30T09:15:00Z', 'end': '2020-07-30T10:25:00Z'},
    #          {'offers': ['0', '1', '2', '11'], 'start': '2020-07-30T10:30:00Z', 'end': '2020-08-06T09:15:00Z'}]

    # If we have no offers or deals, this isn't allowed
    if not offers or not deals:
        return False

    our_offers = set(offers)
    now = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

    # Check all deals, keep the best
    best_deal = None
    for deal in deals:
        # Check if deal is active
        start = deal.get('start', None)
        end = deal.get('end', None)
        if start and end and not start <= now <= end:
            continue

        # Check if we have a matching offer
        deal_offers = set(deal.get('offers', []))
        if not our_offers & deal_offers:
            continue

        if end is None:
            # We have a deal that doesn't expire
            # It won't get any better
            return True

        if best_deal is None or end > best_deal:
            # Keep the best deal
            best_deal = end

    if best_deal is not None:
        return dateutil.parser.parse(best_deal).astimezone(tz=dateutil.tz.tzlocal())

    return False


def parse_channel(channel, offers=None, station_id=None):
    """ Parse the API result of a channel into a Channel object.

    :param dict channel:                The channel info from the API.
    :param List[str] offers:            A list of offers that we have.
    :param str station_id:              The station ID of the CAPI.

    :returns:                           A channel that is parsed.
    :rtype: Channel
    """
    return Channel(
        uid=channel.get('id'),
        station_id=station_id,
        title=channel.get('title'),
        icon=find_image(channel.get('images'), 'la'),  # landscape
        preview=find_image(channel.get('images'), 'lv'),  # live
        number=channel.get('params', {}).get('lcn'),
        epg_now=parse_epg(channel.get('params', {}).get('now')),
        epg_next=parse_epg(channel.get('params', {}).get('next')),
        radio=channel.get('params', {}).get('radio', False),
        replay=channel.get('params', {}).get('replayExpiry', False) is not False,
        available=check_deals_entitlement(channel.get('deals'), offers),
        pin=channel.get('params', {}).get('pinProtected', False),
    )


def parse_epg(program, offers=None):
    """ Parse an Epg dict from the TV API.

    :param dict program:                The program object to parse.
    :param List[str] offers:            A list of offers that we have.

    :returns:                           A program that is parsed.
    :rtype: Epg
    """
    if not program:
        return None

    # Parse dates and convert from UTC to local timezone
    start = dateutil.parser.parse(program.get('params', {}).get('start')).replace(tzinfo=dateutil.tz.UTC).astimezone(tz=dateutil.tz.tzlocal())
    end = dateutil.parser.parse(program.get('params', {}).get('end')).replace(tzinfo=dateutil.tz.UTC).astimezone(tz=dateutil.tz.tzlocal())

    season = program.get('params', {}).get('seriesSeason')
    episode = program.get('params', {}).get('seriesEpisode')

    return Epg(
        uid=program.get('id'),
        title=program.get('title'),
        description=program.get('desc'),
        cover=find_image(program.get('images'), 'po'),  # poster
        preview=find_image(program.get('images'), 'la'),  # landscape
        start=start,
        end=end,
        duration=(end - start).total_seconds(),
        channel_id=program.get('params', {}).get('channelId'),
        formats=[epg_format.get('title') for epg_format in program.get('params', {}).get('formats')],
        genres=[epg_genre.get('title') for epg_genre in program.get('params', {}).get('genres')],
        replay=program.get('params', {}).get('replay', False),
        restart=program.get('params', {}).get('restart', False),
        age=program.get('params', {}).get('age'),
        series_id=program.get('params', {}).get('seriesId'),
        season=int(season) if season is not None else None,
        episode=int(episode) if episode is not None else None,
        credit=[
            Credit(credit.get('role'), credit.get('person'), credit.get('character'))
            for credit in program.get('params', {}).get('credits', [])
        ],
        available=check_deals_entitlement(program.get('deals'), offers),
    )


def parse_epg_series(program):
    """ Parse a EpgSeries dict from the TV API.

    :param dict program:                The series object to parse.

    :returns:                           A program that is parsed.
    :rtype: Epg
    """
    if not program:
        return None

    return EpgSeries(
        uid=program.get('id'),
        title=program.get('title'),
        description=program.get('desc'),
        cover=find_image(program.get('images'), 'po'),  # poster
        preview=find_image(program.get('images'), 'la'),  # landscape
        channel_id=program.get('params', {}).get('channelId'),
        formats=[epg_format.get('title') for epg_format in program.get('params', {}).get('formats')],
        genres=[epg_genre.get('title') for epg_genre in program.get('params', {}).get('genres')],
        age=program.get('params', {}).get('age'),
    )


def parse_epg_capi(program, tenant):
    """ Parse a program dict from the CAPI.

    :param dict program:                The program object to parse.
    :param dict tenant:                 The tenant object to help with some URL's.

    :returns:                           A program that is parsed.
    :rtype: Epg
    """
    if not program:
        return None

    # Parse dates and convert from UTC to local timezone
    start = datetime.fromtimestamp(program.get('start') / 1000, tz=dateutil.tz.UTC).astimezone(tz=dateutil.tz.tzlocal())
    end = datetime.fromtimestamp(program.get('end') / 1000, tz=dateutil.tz.UTC).astimezone(tz=dateutil.tz.tzlocal())
    now = datetime.now(tz=dateutil.tz.tzlocal())

    # Parse credits
    credit_list = []
    for credit in program.get('credits', []):
        if not credit.get('r'):  # Actor
            credit_list.append(Credit(role=Credit.ROLE_ACTOR, person=credit.get('p'), character=credit.get('c')))
        elif credit.get('r') == 1:  # Director
            credit_list.append(Credit(role=Credit.ROLE_DIRECTOR, person=credit.get('p')))
        elif credit.get('r') == 3:  # Producer
            credit_list.append(Credit(role=Credit.ROLE_PRODUCER, person=credit.get('p')))
        elif credit.get('r') == 4:  # Presenter
            credit_list.append(Credit(role=Credit.ROLE_PRESENTER, person=credit.get('p')))
        elif credit.get('r') == 5:  # Guest
            credit_list.append(Credit(role=Credit.ROLE_GUEST, person=credit.get('p')))
        elif credit.get('r') == 7:  # Composer
            credit_list.append(Credit(role=Credit.ROLE_COMPOSER, person=credit.get('p')))

    return Epg(
        uid=program.get('locId'),
        title=program.get('title'),
        description=program.get('description'),
        cover='https://{domain}/{env}/mmchan/mpimages/447x251/{file}'.format(domain=tenant.get('domain'),
                                                                             env=tenant.get('env'),
                                                                             file=program.get('cover').split('/')[-1]) if program.get('cover') else None,
        preview=None,
        start=start,
        end=end,
        duration=(end - start).total_seconds(),
        channel_id=None,
        formats=[program.get('formats')],  # We only have one format
        genres=program.get('genres'),
        replay=program.get('flags') & 16,  # BIT_EPG_FLAG_REPLAY
        restart=program.get('flags') & 32,  # BIT_EPG_FLAG_RESTART
        age=program.get('age'),
        series_id=program.get('seriesId'),
        season=program.get('seasonNo'),
        episode=program.get('episodeNo'),
        credit=credit_list,
        available=(program.get('flags') & 16) and (start < now),  # BIT_EPG_FLAG_REPLAY
    )


def parse_vod_genre(collection):
    """ Parse a genre from the Collections API.

    :param dict collection:             The collection object to parse.
    :returns:                           A genre that is parsed.
    :rtype: VodGenre
    """
    return VodGenre(
        uid=None,
        title=collection.get('title').capitalize() if collection.get('title') else VodGenre.map_label(collection.get('label')),
        query=collection.get('query'),
    )


def parse_vod_movie(asset):
    """ Parse a movie from the Collections API.

    :param dict asset:                  The asset object to parse.
    :returns:                           A movie that is parsed.
    :rtype: VodMovie
    """
    return VodMovie(
        uid=asset.get('id'),
        title=asset.get('title'),
        year=asset.get('params', {}).get('year'),
        duration=asset.get('params', {}).get('duration'),
        age=asset.get('params', {}).get('age'),
        cover=find_image(asset.get('images'), 'po'),  # poster
        preview=find_image(asset.get('images'), 'la'),  # landscape
    )


def parse_vod_series(asset):
    """ Parse a series from the Collections API.

    :param dict asset:                  The asset object to parse.
    :returns:                           A series that is parsed.
    :rtype: VodSeries
    """
    return VodSeries(
        uid=asset.get('id'),
        title=asset.get('title'),
        year=asset.get('params', {}).get('year'),
        age=asset.get('params', {}).get('age'),
        cover=find_image(asset.get('images'), 'po'),  # poster
        preview=find_image(asset.get('images'), 'la'),  # landscape
    )


def parse_vod_episode(asset):
    """ Parse an episode from the Collections API.

    :param dict asset:                  The asset object to parse.
    :returns:                           An epsiode that is parsed.
    :rtype: VodEpisode
    """
    return VodEpisode(
        uid=asset.get('id'),
        title=asset.get('title'),
        year=asset.get('params', {}).get('year'),
        duration=asset.get('params', {}).get('duration'),
        age=asset.get('params', {}).get('age'),
        cover=find_image(asset.get('images'), 'po'),  # poster
        preview=find_image(asset.get('images'), 'la'),  # landscape
        series_id=asset.get('params', {}).get('seriesId'),
        season=asset.get('params', {}).get('seriesSeason'),
        episode=asset.get('params', {}).get('seriesEpisode'),
    )


def http_get(url, params=None, token_bearer=None, token_cookie=None):
    """ Make a HTTP GET request for the specified URL.

    :param str url:                     The URL to call.
    :param dict params:                 The query parameters to include to the URL.
    :param str token_bearer:            The token to use in Bearer authentication.
    :param str token_cookie:            The token to use in Cookie authentication.

    :returns:                           The HTTP Response object.
    :rtype: requests.Response
    """
    try:
        return _request('GET', url=url, params=params, token_bearer=token_bearer, token_cookie=token_cookie)
    except HTTPError as ex:
        if ex.response.status_code == 401:
            raise InvalidTokenException
        raise


def http_post(url, params=None, form=None, data=None, token_bearer=None, token_cookie=None):
    """ Make a HTTP POST request for the specified URL.

    :param str url:                     The URL to call.
    :param dict params:                 The query parameters to include to the URL.
    :param dict form:                   A dictionary with form parameters to POST.
    :param dict data:                   A dictionary with json parameters to POST.
    :param str token_bearer:            The token to use in Bearer authentication.
    :param str token_cookie:            The token to use in Cookie authentication.

    :returns:                           The HTTP Response object.
    :rtype: requests.Response
    """
    try:
        return _request('POST', url=url, params=params, form=form, data=data, token_bearer=token_bearer,
                        token_cookie=token_cookie)
    except HTTPError as ex:
        if ex.response.status_code == 401:
            raise InvalidTokenException
        raise


def _request(method, url, params=None, form=None, data=None, token_bearer=None, token_cookie=None):
    """ Makes a request for the specified URL.

    :param str method:                  The HTTP Method to use.
    :param str url:                     The URL to call.
    :param dict params:                 The query parameters to include to the URL.
    :param dict form:                   A dictionary with form parameters to POST.
    :param dict data:                   A dictionary with json parameters to POST.
    :param str token_bearer:            The token to use in Bearer authentication.
    :param str token_cookie:            The token to use in Cookie authentication.

    :returns:                           The HTTP Response object.
    :rtype: requests.Response
    """
    if form or data:
        # Make sure we don't log the password
        debug_data = {}
        debug_data.update(form or data)
        if 'Password' in debug_data:
            debug_data['Password'] = '**redacted**'
        _LOGGER.debug('Sending %s %s: %s', method, url, debug_data)
    else:
        _LOGGER.debug('Sending %s %s', method, url)

    if token_bearer:
        headers = {
            'authorization': 'Bearer ' + token_bearer,
        }
    else:
        headers = {}

    if token_cookie:
        cookies = {
            '.ASPXAUTH': token_cookie
        }
    else:
        cookies = {}

    response = SESSION.request(method, url, params=params, data=form, json=data, headers=headers, cookies=cookies, proxies=PROXIES)

    # Set encoding to UTF-8 if no charset is indicated in http headers (https://github.com/psf/requests/issues/1604)
    if not response.encoding:
        response.encoding = 'utf-8'

    _LOGGER.debug('Got response (status=%s): %s', response.status_code, response.text)

    # Raise a generic HTTPError exception when we got an non-okay status code.
    response.raise_for_status()

    return response

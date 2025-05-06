# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

import itertools
import logging
import time
import pytz

from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

from codequick import Script
from codequick.support import logger_id
from resources.lib.utils import replace_markdown, remove_markdown, strptime, addon_info
from resources.lib.constants import FULLY_WATCHED_PERCENTAGE


MSG_ONLY_TODAY = 30501
MSG_DAYS_AVAILABLE = 30502
TXT_FOR_MEMBERS = Script.localize(30503)
TXT_SUBCRIPTION_FILM = ''.join(('[COLOR yellow]', Script.localize(30513), '[/COLOR]'))
TXT_AVAILABLE_OVER_A_YEAR = 30514
TXT_AVAILABLE_MONTHS = 30515
TXT_AVAILABLE_WEEKS = 30516
TXT_AVAILABLE_DAYS = 30317
TXT_AVAILABLE_HOURS = 30318

logger = logging.getLogger('.'.join((logger_id, __name__)))
tz_ams = pytz.timezone('Europe/Amsterdam')


class FilmItem:
    def __init__(self, film_info, show_price=True):
        self.film_info = film_info
        self.show_price_info = show_price
        self._price_info_txt = None
        self.playtime = None
        self.duration = None
        self._subscription_days = -1  # Number of days this film is still available with a subscription account.
        try:
            self.content = film_info['content']
        except (KeyError, TypeError):
            # It's not uncommon that an item obtained from nuxt is None.
            self._data = None
            return
        self.uuid = film_info.get('uuid')
        # noinspection PyBroadException
        try:
            self._end_time, self.is_expired = parse_end_date(self.content.get('endDate'))
            self._data = self._parse()
        except:
            self._data = None
            logger.error("Failed to create FilmItem\n", exc_info=True)

    @property
    def data(self):
        return self._data

    def _parse(self):
        """From data provided in *film_info* create a dict with info of that film in a format suitable
        for use in codequick.ListItem.from_dict().

        """
        data = self.content
        # Some films have an end date in the past and are not available any more
        if self.is_expired:
            return None

        title = data.get('title')

        try:
            subscr_end_date = strptime(data['svodEndDate'], "%Y-%m-%d %H:%M")
            subscr_end_date = tz_ams.localize(subscr_end_date).astimezone(pytz.utc)
            self._subscription_days = subscr_days = (subscr_end_date - datetime.now(tz=pytz.utc)) / timedelta(days=1)

            if subscr_days > 0:
                if self.show_price_info:
                    self._price_info_txt = TXT_SUBCRIPTION_FILM
                if subscr_days <= 1:
                    title = '{}    [COLOR orange]{}[/COLOR]'.format(title, Script.localize(MSG_ONLY_TODAY))
                elif subscr_days <= 14:
                    title = ''.join(('{}    [COLOR orange]', Script.localize(MSG_DAYS_AVAILABLE), '[/COLOR]')).format(
                        title, int(subscr_days) + 1)
        except (KeyError, ValueError):
            # Some dates are present that lack the time part, but these are all before 2020 anyway.
            subscr_end_date = None

        original_trailers = Script.setting.get_boolean('original-trailers')
        fanart_images = self.get_fanart()
        poster_image = img_url(data.get('poster') or (fanart_images.pop(0) if fanart_images else None))
        self.duration = duration = self.get_duration()

        film_item = {
            'label': title,
            'art': {
                'poster': poster_image,
                'fanart': img_url(data.get('background'))
            },
            'info': {
                'title': title,
                'mediatype': 'movie',
                'year': data.get('productionYear'),
                'dateadded': self.date_added(),
                'director': data.get('director'),
                'cast': list_from_items_string(data.get('cast')),
                'plot': self._create_long_plot(),
                'plotoutline': self._create_plot_outline(),
                'duration': duration,
                'tagline': self._quote(),
                'genre': list_from_items_string(data.get('genre')),
                'trailer': self._select_trailer_url(original_trailers),
            },
            'params': {
                'title': title,
                'uuid': self.uuid,
                'slug': self.film_info.get('full_slug')
            },
        }
        self.playtime = self.film_info.get('playtime')
        if self.playtime and duration:
            # Duration seems to be rounded up to whole minutes, so actual playing time could
            # still differ by 60 seconds when the video has been fully watched.
            if duration - self.playtime < max(60, duration * (1 - FULLY_WATCHED_PERCENTAGE)):
                self.playtime = 0
            film_item['properties'] = {
                'playcount': '1',
                'resumetime': str(self.playtime),
                'totaltime': str(duration)
            }

        if fanart_images:
            # add extra fanart images
            idx = 0
            art = film_item['art']
            for img in fanart_images:
                idx += 1
                art['fanart{}'.format(idx)] = img_url(img)

        return film_item

    # noinspection PyUnresolvedReferences
    def _select_trailer_url(self, prefer_original) -> str:
        """Retrieve trailer from the film content.

        Returns either Cinetree's trailer, or the original trailer depending on the presence of
        various trailer info and parameter *prefer_original*.

        The dict `self.content` is scanned for the fields with trailer information.

        Possible trailer fields are:
            - 'originalTrailer':    of type dict
            - 'originalTrailerUrl': of type string which is often empty, and usually refers to YouTube.
            - 'trailerVimeoURL':    of type string. Most often referring to vimeo, but can be an url to
              YouTube as well.


        There is no guarantee that fields ar present. Also strings type of fields can be empty, or have
        leading or trailing whitespace.

            If originalTrailer is present it will be a dict with fields 'plugin' and 'selected'.
        Field 'selected' is a unique string, but may be None to indicate that no trailer is present.
        Field 'plugin' should always be 'cinetree-autocomplete' and determines how the url to the video
        is constructed from the value of field 'selected'. This url points to a json document with stream
        urls, the same as a normal film.

        """
        film_data = self.content
        vimeo_url = film_data.get('trailerVimeoURL', '').strip()
        orig_url = film_data.get('originalTrailerURL', '').strip()
        orig_trailer = film_data.get('originalTrailer')

        try:
            if prefer_original:
                trailer = (orig_trailer if orig_trailer and orig_trailer.get('selected') else orig_url) or vimeo_url
            else:
                trailer = vimeo_url or (orig_trailer if orig_trailer and orig_trailer.get('selected') else orig_url)

            if not trailer:
                return ''

            if isinstance(trailer, str):
                return 'plugin://plugin.video.cinetree/resources/lib/main/play_trailer?url=' + quote_plus(trailer)
            else:
                if trailer['plugin'] == "cinetree-autocomplete":
                    return 'plugin://plugin.video.cinetree/resources/lib/main/play_trailer?url=' \
                           + quote_plus('https://api.cinetree.nl/videos/vaem/' + trailer['selected'])
                else:
                    logger.warning("Film %s has original trailer, but unexpected plugin '%s'.",
                                   film_data.get('title'), trailer['plugin'])
        except (KeyError, ValueError, AttributeError):
            logger.warning('Error parsing trailer in film %s', film_data.get('title'), exc_info=True)
        return ''

    @property
    def price_info(self):
        if getattr(self, '_price_info_txt', None) is None:
            if self.show_price_info:
                film_data = self.content
                price = film_data.get('tvodPrice', None)
                if price is None:
                    return ''
                price_txt = '[B]€ {:0.2f}[/B]'.format(int(price or 0) / 100).replace('.', ',', 1)
                subscr_price = film_data.get('tvodSubscribersPrice')
                if subscr_price:
                    subscr_price_txt = '\n[B]€ {:0.2f}[/B] {}'.format(int(subscr_price)/100, TXT_FOR_MEMBERS)
                    subscr_price_txt = subscr_price_txt.replace('.', ',', 1)
                else:
                    subscr_price_txt = ''
                self._price_info_txt = ''.join((price_txt, subscr_price_txt))
            else:
                self._price_info_txt = ''
        return self._price_info_txt

    @property
    def availability(self):
        """A human-readable representation of the time a film is still
        availability, like "Available for 3 months".

        Returns an empty string if `end_time` is empty, None, or in any other
        way invalid.

        """
        if getattr(self, '_availability', None) is None:
            # The vast majority of items do not have an end time, and never create
            # rental availability for subscription films.
            if not self._end_time or self._subscription_days > 0:
                return ''

            localise = addon_info['addon'].getLocalizedString
            dt_available = self._end_time - datetime.now(timezone.utc)
            days_available = int(dt_available.days + 0.99)

            if days_available > 365:
                self._availability = localise(TXT_AVAILABLE_OVER_A_YEAR)
            elif days_available > 60:
                self._availability = localise(TXT_AVAILABLE_MONTHS).format(int(days_available // 30))
            elif days_available > 14:
                self._availability = localise(TXT_AVAILABLE_WEEKS).format(int(days_available // 7))
            elif days_available >= 2:
                self._availability = ''.join((
                    '[COLOR orange]',
                    localise(TXT_AVAILABLE_DAYS).format(days_available),
                    '[/COLOR]'))
            else:
                self._availability = ''.join((
                    '[COLOR orange]',
                    localise(TXT_AVAILABLE_HOURS).format(int(dt_available.total_seconds() / 3600)),
                    '[/COLOR]'))
        return self._availability

    def _create_long_plot(self):
        film_data = self.content
        overview = (film_data.get('overviewText', ''), )
        if not overview[0]:
            overview = (film_data.get('shortSynopsis'), film_data.get('selectedByQuote'))
        plot = '\n\n'.join(t for t in itertools.chain(overview, (self.price_info, self.availability)) if t)
        return replace_markdown(plot)

    def _create_plot_outline(self):
        short_synopsis = self.content.get('shortSynopsis', '')
        if not short_synopsis:
            return None
        else:
            return '\n\n'.join(t for t in (replace_markdown(short_synopsis),
                                           self.price_info,
                                           self.availability) if t)

    def _quote(self):
        """Return the first found quote in film data.
        """
        blocks = self.content.get('blocks', [])
        for block in blocks:
            if block.get('component') == 'quote':
                quote = block.get('text')
                if quote:
                    return replace_markdown(quote)
        return None

    def get_duration(self):
        """Return the duration in seconds, or None if duration is empty or not present in
        `data`.

        The duration field can be absent, empty, None, a string in the format '104 min', or
        a string with just a number, that even may be a float or int. However, if there is a value,
        it always represents the duration in minutes.

        """
        try:
            minutes = self.content['duration'].split()[0]
            return int(float(minutes) * 60)
        except (KeyError, IndexError, ValueError):
            return None

    def get_fanart(self):
        """Get all available images that can serve as fanart

        """
        return [block.get('image') for block in self.content.get('blocks', []) if block.get('component') == 'image']

    def date_added(self):
        start_date = self.content.get('startDate')
        if start_date is None:
            first_published = self.film_info.get('first_published_at', '1970-01-01T00:00:00')
            return first_published[:19].replace('T', ' ')
        if len(start_date) == 10:
            # Y-m-d only; add hrs, mins and secs
            return start_date + ' 00:00:00'
        if len(start_date) == 16:
            # includes hours and minutes; add secs
            return start_date + ':00'
        else:
            logger.warning("Unexpected startDate format: '%s'", start_date)

    def __bool__(self):
        return self._data is not None


def parse_end_date(end_date):
    if not end_date:
        # most endDates are empty strings
        return None, False

    try:
        end_dt = strptime(end_date, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        return end_dt, end_dt < datetime.now(timezone.utc)  # time.gmtime()
    except ValueError:
        # some end dates are in a short format, but they are all long expired
        return None, True


def img_url(url):
    """Ensures a complete url for images.
    Some image url's in film listings are presented without protocol specification, but
    some are.
    This function ensures that these url's are correct.

    """
    if url and not url.startswith('http'):
        return 'https:' + url
    else:
        return url


def list_from_items_string(items: str):
    """return items that are seperated by a comma as a list
    Or None if no items are present.

    """
    if items:
        return items.split(',')
    else:
        return None


def create_collection_item(col_data):

    content = col_data.get('content') or col_data
    name = col_data.get('name')
    collection = {
        'label': name,
        'art': {'thumb': img_url(content.get('image'))},
        'info': {'plot': replace_markdown(content.get('description'))},
        # Full_slug path starts with collections (english) while path to .js uses collecties (Dutch)
        'params': {'slug': 'collecties/' + col_data.get('slug')}
    }
    return collection


def create_films_list(data, list_type='generic', add_price=True):
    """Extract FilmItems from data_dict.

    This function retrieves all relevant info found in that dict and
    generates FilmItem objects for each film.

    :param data: A dictionary of film data, like obtained from get_jsonp()
    :type data: dict
    :param list_type: The type of list to search for.
        Can be 'storyblok' for list from Storyblok, or 'generic' for any
        other list from cinetree api.
    :type list_type: str
    :param add_price: Whether price info is to be added to the descriptions.
    :type add_price: bool
    :rtype: Generator[FilmItem]

    """
    try:
        if list_type == 'storyblok':
            # Data returned by storyblok is already a list of film data.
            films_list = data
        elif list_type == 'generic':
            content = data['data'][0]['story']['content']
            films_list = content['films']
            if 'shorts' in content.keys():
                films_list.extend(content['shorts'])
        else:
            raise ValueError("Invalid value '{}' for parameter 'list_type'".format(list_type))
    except KeyError:
        raise ValueError("Invalid value of param data")

    film_items = (FilmItem(film, add_price) for film in films_list)
    return (item for item in film_items if item)

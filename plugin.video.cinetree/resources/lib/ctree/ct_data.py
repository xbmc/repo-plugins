# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2023 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

import logging
import time
import pytz

from datetime import datetime, timedelta
from urllib.parse import quote_plus

from codequick import Script
from codequick.support import logger_id
from resources.lib.utils import replace_markdown, remove_markdown


MSG_ONLY_TODAY = 30501
MSG_DAYS_AVAILABLE = 30502

logger = logging.getLogger('.'.join((logger_id, __name__)))
tz_ams = pytz.timezone('Europe/Amsterdam')


def create_film_item(film_info):
    """From data provided in *film_info* create a dict with info of that film in a format suitable
    for use in codequick.ListItem.from_dict().

    """
    try:
        data = film_info['content']

        # Some films have an end date in the past and are not available anymore
        if _is_expired(data.get('endDate')):
            return None

        quotes = _get_quotes(data)
        prefer_originals = Script.setting.get_boolean('original-trailers')
        trailer_url = _select_trailer_url(data, prefer_originals)
        title = data.get('title')

        try:
            subscr_end_date = datetime(*(time.strptime(data['svodEndDate'], "%Y-%m-%d %H:%M")[:6]))
            subscr_end_date = tz_ams.localize(subscr_end_date).astimezone(pytz.utc).replace(tzinfo=None)
            days_dif = (subscr_end_date - datetime.utcnow()) / timedelta(days=1)

            if days_dif > 0:
                if days_dif <= 1:
                    title = '{}    [COLOR orange]{}[/COLOR]'.format(title, Script.localize(MSG_ONLY_TODAY))
                elif days_dif <= 10:
                    title = ''.join(('{}    [COLOR orange]', Script.localize(MSG_DAYS_AVAILABLE), '[/COLOR]')).format(
                        title, int(days_dif) + 1)
            else:
                subscr_end_date = None
        except (KeyError, ValueError):
            # Some dates are present that lack the time part, but these are all before 2020 anyway.
            subscr_end_date = None

        fanart_images = get_fanart(data)
        poster_image = img_url(data.get('poster') or (fanart_images.pop(0) if fanart_images else None))
        duration = get_duration(data)

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
                'director': data.get('director'),
                'cast': list_from_items_string(data.get('cast')),
                'plot': replace_markdown(_create_long_plot(data, add_price=subscr_end_date is None)),
                'plotoutline': replace_markdown(data.get('shortSynopsis')),
                'duration': duration,
                'tagline': remove_markdown(quotes[0]['text']) if quotes else None,
                'genre': list_from_items_string(data.get('genre')),
                'trailer': trailer_url,
            },
            'params': {
                'title': title,
                'uuid': film_info.get('uuid'),
                'slug': film_info.get('full_slug'),
                'end_date': subscr_end_date},
            'properties': {
                # This causes Kodi not to offer the standard resume dialog, so we can show a dialog with
                # resume time at the time of resolving the video url.
                'resumetime': '0',
                'totaltime': duration
            }
        }

        if fanart_images:
            # add extra fanart images
            idx = 0
            art = film_item['art']
            for img in fanart_images:
                idx += 1
                art['fanart{}'.format(idx)] = img_url(img)
    except (KeyError, TypeError):
        film_item = None

    return film_item


# noinspection PyUnresolvedReferences
def _select_trailer_url(film_data: dict, prefer_original: bool) -> str:
    """Retrieve trailer from the *film_data*.

    Returns either Cinetree's trailer, or the original trailer depending on the presence of
    various trailer info and parameter *prefer_original*.

    :param film_data: A dict of film info, as in content field of a json object returned by Cinetree.
    :param prefer_original: If both the original trailer and Cinetree's trailer are present, return
        the original.

    The dict *film_data* is scanned for the fields with trailer information.

    Possible trailer fields are:
        - 'originalTrailer':    of type dict
        - 'originalTrailerUrl': of type string which is often empty, and usually refers to YouTube.
        - 'trailerVimeoURL':    of type string. Most often referring to vimeo, but can be an url to
          YouTube as well.


    There is no guarantee that fields ar present. Also string type of fields can be empty, or have
    leading or trailing whitespace.

        If originalTrailer is present it will be a dict with fields 'plugin' and 'selected'.
    Field 'selected' is a unique string, but may be None to indicate that no  trailer is present.
    Field 'plugin' should always be 'cinetree-autocomplete' and determines how the url to the video
    is constructed from the value of field 'selected'. This url points to a json document with stream
    urls, the same as a normal film.

    """

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


def _create_long_plot(film_data, add_price):
    plot = film_data.get('overviewText', '')
    if not plot:
        plot = '\n\n'.join((film_data.get('shortSynopsis', ''), film_data.get('selectedByQuote', '')))

    plot = plot.strip()

    price = film_data.get('tvodPrice', None)
    if not add_price or price is None:
        return plot

    # Add rental price to the bottom of the plot.
    # price may be an empty string
    price_txt = '\n\n[B]€ {:0.2f}[/B]'.format(int(price or 0) / 100).replace('.', ',', 1)
    subscr_price = film_data.get('tvodSubscribersPrice')
    if subscr_price:
        subscr_price_txt = '\n[B]€ {:0.2f}[/B] {}'.format(int(subscr_price)/100, Script.localize(30503))
        subscr_price_txt = subscr_price_txt.replace('.', ',', 1)
    else:
        subscr_price_txt = ''

    full_txt = ''.join((plot, price_txt, subscr_price_txt))
    return full_txt


def _get_quotes(film_data):
    """return a list of all quotes found in film data
    """
    result = []
    blocks = film_data.get('blocks', [])
    for block in blocks:
        if block.get('component') == 'quote':
            result.append({'from': block.get("from", ''), 'text': block.get('text', '')})
    return result


def _is_expired(end_date):
    if not end_date:
        # most endDates are empty strings
        return False

    try:
        end_time = time.strptime(end_date, "%Y-%m-%d %H:%M")
        return end_time < time.gmtime()
    except ValueError:
        # some end dates are in a short format, but they are all long expired
        return True


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


def get_duration(data):
    """Return the duration in seconds, or None if duration is empty or not present in
    `data`.

    The duration field can be absent, empty, None, a sting in the format '104 min', or
    a string with just a number, that even may be a float or int. However, if there is a value,
    it always represents the duration in minutes.

    """
    try:
        minutes = data['duration'].split()[0]
        return int(float(minutes) * 60)
    except (KeyError, IndexError, ValueError):
        return None


def get_fanart(film_content):
    """Get all available images that can serve as fanart

    """
    return [block.get('image') for block in film_content.get('blocks', []) if block.get('component') == 'image']


def list_from_items_string(items: str):
    """return items that are seperated by comma's as a list
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


def create_films_list(data, list_type='generic'):
    """Extract the list of films from data_dict.

    This function retrieves all relevant info found in that dict and
    creates a list of dicts, where each dict contains info about a
    film in a format suitable for kodi

    :param data: A dictionary of film data, like obtained from get_jsonp()
    :param list_type: The type of list to search for.
        Can be 'recommended' for the list of recommendations in subscription, 'subscription'  for
        the list of all films available in the monthly subscription, 'storyblok' for list from
        Storyblok, or 'generic' for any other list from cinetree api.

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

    film_items = (create_film_item(film) for film in films_list)
    return [item for item in film_items if item is not None]

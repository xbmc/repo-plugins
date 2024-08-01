
# ----------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022-2024 Dimitri Kroon.
#  This file is part of plugin.video.viwx.
#  SPDX-License-Identifier: GPL-2.0-or-later
#  See LICENSE.txt
# ----------------------------------------------------------------------------------------------------------------------

import time
import logging

import pytz
import requests
import xbmc

from datetime import datetime, timezone, timedelta

from codequick.support import logger_id

from . import errors
from . import fetch
from . import parsex
from . import cache
from . import itv_account

from .itv import get_live_schedule


logger = logging.getLogger(logger_id + '.itvx')


FEATURE_SET = 'hd,progressive,single-track,mpeg-dash,widevine,widevine-download,inband-ttml,hls,aes,inband-webvtt,outband-webvtt,inband-audio-description'
PLATFORM_TAG = 'mobile'


def get_page_data(url, cache_time=None):
    """Return the json data embedded in a <script> tag on a html page.

    Return the data from cache if present and not expired, or request the page by HTTP.
    """
    if not url.startswith('https://'):
        url = 'https://www.itv.com' + url

    # URL's with a trailing space have actually happened, but the web app doesn't seem to have a problem with it.
    url = url.rstrip()
    if cache_time:
        cached_data = cache.get_item(url)
        if cached_data:
            return cached_data

    html_doc = fetch.get_document(url)
    data = parsex.scrape_json(html_doc)
    if cache_time:
        cache.set_item(url, data, cache_time)
    return data


def get_now_next_schedule(local_tz=None):
    """Get the name and start time of the current and next programme for each live channel.

    Present start time conform Kodi's time zone setting.
    """
    if local_tz is None:
        local_tz = pytz.timezone('Europe/London')

    utc_tz = pytz.utc
    # Use local time format without seconds. Fix weird kodi formatting for 12-hour clock.
    time_format = xbmc.getRegion('time').replace(':%S', '').replace('%I%I:', '%I:')

    live_data = fetch.get_json(
        'https://nownext.oasvc.itv.com/channels',
        params={
            'broadcaster': 'itv',
            'featureSet': FEATURE_SET,
            'platformTag': PLATFORM_TAG})

    fanart_url = live_data['images']['backdrop']
    channels = live_data['channels']

    for channel in channels:
        channel['backdrop'] = fanart_url
        slots = channel.pop('slots')

        programs_list = []
        for prog in (slots['now'], slots['next']):
            displ_title = prog['displayTitle']
            if displ_title is None:
                # Some schedules have all fields set to None or False, i.e. no programme info available.
                # In practice, if displayTitle is None, everything else is as well.
                logger.info("No Now/Next info available for channel '%s': %s", channel.get('id'), prog)
                continue

            details = ': '.join(s for s in(displ_title, prog.get('detailedDisplayTitle')) if s)
            start_t = prog['start'][:19]
            utc_start = datetime(*(time.strptime(start_t, '%Y-%m-%dT%H:%M:%S')[0:6]), tzinfo=utc_tz)

            programs_list.append({
                'programme_details': details,
                'programmeTitle': displ_title,
                'orig_start': None,          # fast channels do not support play from start
                'startTime': utc_start.astimezone(local_tz).strftime(time_format)
            })
        channel['slot'] = programs_list
    return channels


def get_live_channels(local_tz=None):
    """Return a list of all available live channels. Include each channel's scheduled
    programmes in the channel data.

    For the stream-only FAST channels, only the current and next programme are
    available. For the regular channels a schedule from now up to 6 hours in the
    future will be returned.
    Programme start times will be presented in the user's local time zone.

    """
    cached_schedule = cache.get_item('live_schedule')
    if cached_schedule:
        return cached_schedule

    if local_tz is None:
        local_tz = pytz.timezone('Europe/London')

    schedule = get_now_next_schedule(local_tz)
    main_schedule = get_live_schedule(6, local_tz=local_tz)

    # Replace the schedule of the main channels with the longer one obtained from get_live_schedule().
    for channel in schedule:
        # The itv main live channels get their schedule from the full live schedule.
        if channel['channelType'] == 'simulcast':
            chan_id = channel['id']
            for main_chan in main_schedule:
                # Caution, might get broken when ITV becomes ITV1 everywhere.
                if main_chan['channel']['name'] == chan_id:
                    channel['slot'] = main_chan['slot']
                    break
    cache.set_item('live_schedule', schedule, expire_time=240)
    return schedule


def get_full_schedule():
    """Get the schedules of the main live channels from a week back to a week ahead.

    These are from the html pages that the website uses to show schedules.
    """
    today = datetime.utcnow()
    all_days = (today + timedelta(i) for i in range(-7, 8))
    # schedules = (get_page_data('watch/tv-guide/' + day.strftime('%Y-%m-%d')) for day in all_days)
    schedule = {}
    for day in all_days:
        page_data = get_page_data('/watch/tv-guide/' + day.strftime('%Y-%m-%d'))
        guide = page_data['tvGuideData']
        for chan_name, progr_list in guide.items():
            chan_schedule = schedule.setdefault(chan_name, [])
            chan_schedule.extend(filter(None, (parsex.parse_schedule_item(progr) for progr in progr_list)))
    return schedule


def main_page_items():
    main_data = get_page_data('https://www.itv.com', cache_time=None)

    hero_content = main_data.get('heroContent')
    if hero_content:
        for hero_data in hero_content:
            hero_item = parsex.parse_hero_content(hero_data)
            if hero_item:
                yield hero_item
    else:
        logger.warning("Main page has no heroContent.")

    if 'trendingSliderContent' in main_data.keys():
        yield {'type': 'collection',
               'show': {'label': 'Trending', 'params': {'slider': 'trendingSliderContent'}}}
    else:
        logger.warning("Main page has no 'Trending' slider.")

    if 'shortFormSliderContent' in main_data.keys():
        yield {'type': 'collection',
               'show': {'label': 'News', 'params': {'slider': 'newsShortForm'}}}
    else:
        logger.warning("Main page has no 'News' slider.")


def collection_content(url=None, slider=None, hide_paid=False):
    """Obtain the collection page defined by `url` and return the contents. If `slider`
    is not None, return the contents of that particular slider on the collection page.

    """
    uk_tz = pytz.timezone('Europe/London')
    time_fmt = ' '.join((xbmc.getRegion('dateshort'), xbmc.getRegion('time')))
    is_main_page = url == 'https://www.itv.com'

    page_data = get_page_data(url, cache_time=3600 if is_main_page else 43200)

    if slider:
        # Return the contents of the specified slider
        if slider == 'shortFormSlider':
            # return the items from the shortFormSlider on a collection page.
            for item in page_data['shortFormSlider']['items']:
                yield parsex.parse_shortform_item(item, uk_tz, time_fmt)
            return

        elif slider in ('newsShortForm', 'sportShortForm'):
            # Return items from the main page's News or Sports short form.
            for slider_data in page_data['shortFormSliderContent']:
                if slider_data['key'] == slider:
                    for short_item in slider_data['items']:
                        yield parsex.parse_shortform_item(short_item, uk_tz, time_fmt, hide_paid)
                    # A 'View All' item,
                    view_all_item = parsex.parse_view_all(slider_data)
                    if view_all_item:
                        yield view_all_item
            return

        elif slider == 'trendingSliderContent':
            # Only found on main page
            items_list = page_data['trendingSliderContent']['items']
            for trending_item in items_list:
                yield parsex.parse_collection_item(trending_item, hide_paid)
            return

        else:
            # `slider` is the name of an editorialSlider.
            # On the main page editorialSliders is a dict, on collection pages it is a list.
            # Although a dict on the main page, the names of the sliders are not exactly the
            # same as the keys of the dict.
            # Until now all editorial sliders on the main page have a 'view all' button, so
            # the contents of the slider itself should never be used, but better allow it
            # now in case it ever changes.
            if is_main_page:
                sliders_list = page_data['editorialSliders'].values()
            else:
                sliders_list = page_data['editorialSliders']
            items_list = None
            for slider_item in sliders_list:
                if slider_item['collection']['sliderName'] == slider:
                    items_list = slider_item['collection']['shows']
                    break
            if items_list is None:
                logger.error("Failed to parse collection content: Unknown slider '%s'", slider)
                return
            for item in items_list:
                yield parsex.parse_collection_item(item, hide_paid)
    else:
        # Return the contents of the page, e.i. a listing of individual items for the shortFromSlider
        # of the internal collection list, or a list of sub-collections from editorial sliders
        collection = page_data['collection']
        editorial_sliders = page_data.get('editorialSliders')
        shortform_slider = page_data.get('shortFormSlider')

        if shortform_slider is not None:
            yield parsex.parse_short_form_slider(shortform_slider, url)

        if collection is not None:
            for item in collection.get('shows', []):
                yield parsex.parse_collection_item(item, hide_paid)
        elif editorial_sliders:
            # Folders, or kind of sub-collections in a collection.
            for slider in editorial_sliders:
                yield parsex.parse_editorial_slider(url, slider)
        else:
            logger.warning("Missing both collections and editorial_sliders in data from '%s'.", url)
            return


def episodes(url, use_cache=False, prefer_bsl=False):
    """Get a listing of series and their episodes

    Return a tuple of a series map and a programmeId.
    The series map is a dict where keys are series numbers and values are dicts
    containing general info regarding the series itself and a list of episodes.
    Both formatted in a way that can be used by ListItem.from_dict().
    The programmeId is the programme ID used by ITVX, and is the same for each
    series and each episode.

    """
    if use_cache:
        cached_data = cache.get_item(url)
        if cached_data is not None:
            return cached_data['series_map'], cached_data['programme_id']

    page_data = get_page_data(url, cache_time=0)
    programme = page_data['programme']
    programme_id = programme.get('encodedProgrammeId', {}).get('underscore')
    programme_title = programme['title']
    programme_thumb = programme['image'].format(**parsex.IMG_PROPS_THUMB)
    programme_fanart = programme['image'].format(**parsex.IMG_PROPS_FANART)
    description  = programme.get('longDescription') or programme.get('description') or programme_title
    if 'FREE' in programme['tier']:
        brand_description = description
    else:
        brand_description = parsex.premium_plot(description)

    series_data = page_data.get('seriesList')
    if not series_data:
        return {}, None

    # The field 'seriesNumber' is not guaranteed to be unique - and not guaranteed an integer either.
    # Midsummer murder for instance has had 2 series with seriesNumber 4
    # By using this mapping, setdefault() and extend() on the episode list, series with the same
    # seriesNumber are automatically merged.
    series_map = {}
    for series in series_data:
        title = series['seriesLabel']
        series_idx = series['seriesNumber']
        series_obj = series_map.setdefault(
            series_idx, {
                'series': {
                    'label': title,
                    'art': {'thumb': programme_thumb, 'fanart': programme_fanart},
                    # TODO: add more info, like series number, number of episodes
                    'info': {'title': '[B]{} - {}[/B]'.format(programme_title, title),
                             'plot': '{}\n\n{} - {} episodes'.format(
                                 brand_description, title, series['numberOfAvailableEpisodes'])},

                    'params': {'url': url, 'series_idx': series_idx}
                },
                'episodes': []
            })
        series_obj['episodes'].extend(
            [parsex.parse_episode_title(episode, programme_fanart, prefer_bsl) for episode in series['titles']])

    programme_data = {'programme_id': programme_id, 'series_map': series_map}
    cache.set_item(url, programme_data, expire_time=1800)
    return series_map, programme_id


def categories():
    """Return all available categorie names."""
    data = get_page_data('https://www.itv.com/watch/categories', cache_time=86400)
    cat_list = data['subnav']['items']
    return ({'label': cat['label'], 'params': {'path': cat['url']}} for cat in cat_list)


def category_news(path):
    """Unlike other categories, news returns a list of sub-categories"""
    data = get_page_data(path, cache_time=86400).get('data')
    if not data:
        return []
    items = [{'label': 'Latest Stories', 'params': {'path': path, 'subcat': 'heroAndLatestData'}}]
    items.extend({'label': item['title'], 'params': {'path': path, 'subcat': 'curatedRails', 'rail': item['title']}}
                 for item in data['curatedRails'])
    items.extend(({'label': 'Latest Programmes', 'params': {'path': path, 'subcat': 'longformData'}},))
    return items


def category_content(url: str, hide_paid=False):
    """Return all programmes in a category"""
    cached_data = cache.get_item(url)
    if cached_data and cached_data['hide_paid'] == hide_paid:
        return cached_data['items_list']

    cat_data = get_page_data(url + '/all', cache_time=0)
    category = cat_data['category']['id']
    progr_list = cat_data.get('programmes')

    parse_progr = parsex.parse_category_item

    if hide_paid:
        items = [parse_progr(prog, category) for prog in progr_list if 'FREE' in prog['tier']]
    else:
        items = [parse_progr(prog, category) for prog in progr_list]
    items.sort(key=lambda prog: prog['show']['info']['sorttitle'])
    cache.set_item(url, {'items_list': items, 'hide_paid': hide_paid}, expire_time=3600)
    return items


def category_news_content(url, sub_cat, rail=None, hide_paid=False):
    """Return the content of one of the news sub categories."""
    page_data = get_page_data(url, cache_time=900)
    news_sub_cats = page_data['data']

    uk_tz = pytz.timezone('Europe/London')
    time_fmt = ' '.join((xbmc.getRegion('dateshort'), xbmc.getRegion('time')))

    # A normal listing of TV shows in the category News, like normal category content
    if sub_cat == 'longformData':
        items_list = news_sub_cats.get(sub_cat)
        if hide_paid:
            return [parsex.parse_category_item(prog, None) for prog in items_list if 'FREE' in prog['tier']]
        else:
            return [parsex.parse_category_item(prog, None) for prog in items_list]

    # News clips, like the news collection
    items_list = None
    if rail:
        for subcat in news_sub_cats.get(sub_cat, []):
            if subcat.get('title') == rail:
                items_list = subcat.get('clips', [])
                break
    elif sub_cat == 'heroAndLatestData':
        items_list = news_sub_cats.get(sub_cat)

    if not items_list:
        return []

    if hide_paid:
        return [parsex.parse_shortform_item(news_item, uk_tz, time_fmt)
                for news_item in items_list
                if not news_item.get('isPaid')]
    else:
        return [parsex.parse_shortform_item(news_item, uk_tz, time_fmt)
                for news_item in items_list]


def get_playlist_url_from_episode_page(page_url, prefer_bsl=False):
    """Obtain the url to the episode's playlist from the episode's HTML page.

    """
    logger.info("Get playlist from episode page - url=%s", page_url)
    data = get_page_data(page_url)

    try:
        episode = data['seriesList'][0]['titles'][0]
    except KeyError:
        # news item
        episode = data['episode']

    if prefer_bsl:
        return episode.get('bslPlaylistUrl') or episode['playlistUrl']
    else:
        return episode['playlistUrl']



def search(search_term, hide_paid=False):
    """Make a query on `search_term`

    When no search result are found itvX returns either HTTP status 204, or
    a normal json object with an emtpy list of results.

    """
    from urllib.parse import quote
    url = 'https://textsearch.prd.oasvc.itv.com/search?broadcaster=itv&featureSet=clearkey,outband-webvtt,hls,aes,' \
          'playready,widevine,fairplay,bbts,progressive,hd,rtmpe&onlyFree={}&platform=ctv&query={}'.format(
        str(hide_paid).lower(), quote(search_term))
    headers = {
        'User-Agent': fetch.USER_AGENT,
        'accept': 'application/json',
        'Origin': 'https://www.itv.com',
        'Referer': 'https://www.itv.com/',
        'accept-language': 'en-GB,en;q=0.5',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
    }
    resp = requests.get(url, headers=headers, timeout=fetch.WEB_TIMEOUT)

    if resp.status_code != 200:
        logger.debug("Search for '%s' (hide_paid=%s) failed with HTTP status %s",
                     search_term, hide_paid, resp.status_code)
        return None

    try:
        data = resp.json()
    except:
        logger.warning("Search for '%s' (hide_paid=%s) returned non-json content: '%s'",
                       search_term, hide_paid, resp.content)
        return None

    results = data.get('results')
    if not results:
        logger.debug("Search for '%s' returned an empty list of results. (hide_paid=%s)", search_term, hide_paid)
    return (parsex.parse_search_result(result) for result in results)


def my_list(user_id, programme_id=None, operation=None, offer_login=True, use_cache=True):
    """Get itvX's 'My List', or add or remove an item from 'My List' and return the updated list.

    A regular browser uses platform ctv in these requests.
    """
    if operation in ('add', 'remove'):
        url = 'https://my-list.prd.user.itv.com/user/{}/mylist/programme/{}?features={}&platform=ctv&size=52'.format(
            user_id, programme_id, FEATURE_SET)
    else:
        cached_list = cache.get_item('mylist_' + user_id)
        if use_cache and cached_list is not None:
            return cached_list
        else:
            url = 'https://my-list.prd.user.itv.com/user/{}/mylist?features={}&platform=ctv&size=52'.format(
                user_id, FEATURE_SET)

    fetcher = {
        'get': fetch.get_json,
        'add': fetch.post_json,
        'remove': fetch.delete_json}.get(operation, fetch.get_json)

    data = itv_account.fetch_authenticated(fetcher, url, data=None, login=offer_login)
    # Empty lists will return HTTP status 204, which results in data being None.
    if data:
        my_list_items = list(filter(None, (parsex.parse_my_list_item(item) for item in data)))
    else:
        my_list_items = []
    cache.set_item('mylist_' + user_id, my_list_items, 1800)
    cache.my_list_programmes = list(item['programme_id'] for item in my_list_items)
    return my_list_items


def initialise_my_list():
    """Get all items from itvX's 'My List'.
    Used when the module is first imported, or after account sign in to initialise
    the cached list of programme ID's before the plugin lists programmes.

    """
    try:
        my_list(itv_account.itv_session().user_id, offer_login=False, use_cache=False)
        logger.info("Updated MyList programme ID's.")
    except Exception as err:
        logger.info("Failed to update MyList programme ID's: %r.", err)
        if cache.my_list_programmes is None:
            # Mark my_list_programmes as 'failed to initialise'
            # This causes listings not to include an 'Add' or 'Remove' context menu item,
            # while preventing subsequent re-initialisation attempts.
            cache.my_list_programmes = False


def get_last_watched():
    user_id = itv_account.itv_session().user_id
    cache_key = 'last_watched_' + user_id
    cached_data = cache.get_item(cache_key)
    if cached_data is not None:
        return cached_data

    url = 'https://content.prd.user.itv.com/lastwatched/user/{}/ctv?features={}'.format(
            user_id, FEATURE_SET)
    header = {'accept': 'application/vnd.user.content.v1+json'}
    utc_now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    data = itv_account.fetch_authenticated(fetch.get_json, url, headers=header)
    watched_list = [parsex.parse_last_watched_item(item, utc_now) for item in data]
    cache.set_item(cache_key, watched_list, 600)
    return watched_list


def get_resume_point(production_id: str):
    try:
        production_id = production_id.replace('/', '_').replace('#', '.')
        url = 'https://content.prd.user.itv.com/resume/user/{}/productionid/{}'.format(
            itv_account.itv_session().user_id, production_id)
        data = itv_account.fetch_authenticated(fetch.get_json, url)
        resume_time = data['progress']['time'].split(':')
        resume_point = int(resume_time[0]) * 3600 + int(resume_time[1]) * 60 + float(resume_time[2])
        return resume_point
    except errors.HttpError as err:
        if err.code == 404:
            # Normal response when no resume data is found, e.g. with 'next episodes'.
            logger.debug("Resume point of production '%s' not available.", production_id)
        else:
            logger.error("HTTP error %s: %s on request for resume point of production '%s'.",
                         err.code, err.reason, production_id)
    except:
        logger.error("Error obtaining resume point of production '%s'.", production_id, exc_info=True)
    return None


def recommended(user_id, hide_paid=False):
    """Get the list of recommendations from ITVX.
    Always returns data, even if user_id is invalid or absent.

    """
    recommended_url = 'https://recommendations.prd.user.itv.com/recommendations/homepage/' + user_id

    recommended = cache.get_item(recommended_url)
    if not recommended:
        req_params = {'features': FEATURE_SET, 'platform': PLATFORM_TAG, 'size': 24, 'version': 3}
        recommended = fetch.get_json(recommended_url, params=req_params)
        if not recommended:
            return None
        cache.set_item(recommended_url, recommended, 43200)
    return list(filter(None, (parsex.parse_my_list_item(item, hide_paid) for item in recommended)))


def because_you_watched(user_id, name_only=False, hide_paid=False):
    """Return the list of recommendation based on the last watched programme.

    Returns 204 - No Content when user ID is invalid. Doesn't require authentication.
    """
    if not user_id:
        return
    byw_url = 'https://recommendations.prd.user.itv.com/recommendations/byw/' + user_id
    byw = cache.get_item(byw_url)
    if not byw:
        req_params = {'features': FEATURE_SET, 'platform': 'ctv', 'size': 12, 'version': 2}
        byw = fetch.get_json(byw_url, params=req_params)
        if not byw:
            return
        cache.set_item(byw_url, byw, 1800)

    if name_only:
        return byw['watched_programme']
    else:
        return list(filter(None, (parsex.parse_my_list_item(item, hide_paid) for item in byw['recommendations'])))

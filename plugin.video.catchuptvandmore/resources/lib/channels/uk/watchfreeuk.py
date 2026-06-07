# _____________________________________________________________________________
# Copyright (c) 2025, Dimitri Kroon
# SPDX-License-Identifier: GPL-2.0-or-later
# See LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt
# This file is part of Catch-up TV & More
# _____________________________________________________________________________
import itertools
import json
import re

from urllib.parse import urlencode

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import web_utils
from resources.lib import menu_utils
from resources.lib import resolver_proxy


DFLT_CACHE_TIME = 1200
DFLT_HEADERS = {"User-Agent": web_utils.get_random_ua()}
# Need a pretty long read timeout to accommodate search and playlist requests.
REQ_TIMEOUT = (3.5, 15)

BASE_URL = 'https://www.watchfreeuk.co.uk'


def clean_str(src_txt):
    """Strip all whitespace from every line in `src_txt` and
    combine them to a single line of text.
    """
    if src_txt is None:
        return ''
    return ' '.join(t.strip() for t in src_txt.strip().split('\n'))


def check_geo_block(resp):
    """Geo-blocked requests just return normally with status 200 - OK.
    Check the page's title to determine whether it was blocked. And if it
    was, raise a 403 - Forbidden error and remove the page from the cache
    to prevent getting the same error again when the user has resolved the
    block.

    Since this function already parses the html document, return the
    root element for further processing.
    """
    root = resp.parse()
    page_title = root.find('.//title')
    if page_title is None:
        # The content of a RenderableComponent does not have a title when it's
        # successfully returned. However, if it is geo-blocked, a regular HTML
        # page with a title tag is returned.
        return root

    if 'Service Unavailable' in page_title.text:
        urlhash = urlquick.hash_url(resp.request)
        urlquick.CacheHTTPAdapter(urlquick.CACHE_LOCATION).del_cache(urlhash)
        err = urlquick.HTTPError(page_title)
        err.code = 403
        err.msg = page_title
        raise err
    return root


def fetch(url, **kwargs):
    """Make a GET request to the specified `url` and return an xml tree
    that represents the HTML page

    """
    kwargs.setdefault('headers', DFLT_HEADERS)
    kwargs.setdefault('timeout', REQ_TIMEOUT)
    kwargs.setdefault('max_age', DFLT_CACHE_TIME)
    resp = urlquick.get(url, **kwargs)
    return check_geo_block(resp)


def parse_duration(tree):
    """Find duration in the tree and return its value in seconds.

    Durations exist in formats like '43m', or '1h 26m'.

    """
    try:
        span_duration = tree.find(".//span[@data-content-type='duration']")
        duration_txt = clean_str(span_duration[0].text)
        hrs_str, sep, mins_str = duration_txt.partition('h')
        if sep:
            hrs = int(hrs_str)
        else:
            hrs = 0
            mins_str = duration_txt
        mins = int(mins_str.strip(' m'))
        return hrs * 3600 + mins * 60
    except (AttributeError, ValueError, TypeError):
        return None


def get_all_texts(element):
    """Return the text of the element and all of the span tags below it
    as a single line of text.

    Return an empty string if element is None.

    """
    if element is None:
        return ''
    all_texts = itertools.chain(
        (element.text, ),
        (child.text for child in element.iterfind('.//span'))
    )
    return ' '.join(clean_str(t) for t in all_texts if t)


def parse_age_rating(tree):
    return get_all_texts(tree.find(".//span[@data-content-type='age-rating']"))


def params_from_x_data(x_data):
    """Parse the x_data string containing a RenderableComponent's javascript function
    and return a dict of the querystring parameters specified in that function.

    """
    import codecs

    params = {}
    param_str = re.search(r"this\.url\.params = \{(.+?)}(?![',])", x_data, re.DOTALL)[1]
    # Find lines of key/value pairs. However, the xml parser may have disregarded newline
    # characters, so allow the text to be one single line.
    for line in re.finditer(r"(\w+:\s.*?)(?:,\s|\s{2,})", param_str, re.DOTALL):
        key, val = line[1].split(': ', 1)
        key = key.strip()
        # Replace backslash-escaped characters, except unicode escapes.
        val = re.sub(r'\\([^u])', r'\1', val)
        # Decode unicode escaped characters.
        val = codecs.decode(val.strip("' \r\n\t\xA0"), 'unicode_escape')
        # val = val.strip("'")
        params[key] = val
    return params


def path_from_x_data(x_data):
    """Return the path of a RenderableComponent"""
    match = re.search(r"render\(\s*'([^']+)'", x_data)
    return match[1]


def renderable_url(component_div) -> str:
    """Build a full url to the renderable slider content from several attributes of the div."""
    x_data = component_div.get("x-data")
    query_string = urlencode(params_from_x_data(x_data))

    # Normal sliders have their rendering function in x-intersect, but the hero
    # slider has it in x-init, since it is rendered the moment the page is loaded.
    x_init = component_div.get('x-intersect') or component_div.get('x-init')
    url = ''.join((BASE_URL, path_from_x_data(x_init), query_string))
    return url


def parse_item_div(video_item):
    """Parse a <div> element that represents a video item.

    Scrape as much info as possible from the div and its children and return
    a codequick Listitem.

    """
    x_data = video_item.find('*/a').get('x-data')
    video_url = re.search(r"href: '([^']+)',", x_data)[1]

    # A playable's path contains its unique video ID and starts with '/watch'.
    match = re.search(r"/watch/vod/(\d+)/", video_url)
    uvid = match[1] if match else None

    card = video_item.find(".//div[@class='rounded overflow-hidden']")
    video_img = card.find('.//img').get('src')
    title = clean_str(card.find(".//p[@class='overlay-title']").text)

    num_episodes = get_all_texts(card.find(".//span[@data-content-type='episodes']"))
    # Find a string like 'S1:E8', used on items that represent a single episode.
    season_episode = get_all_texts(card.find(".//span[@data-content-type='season-episode']"))
    age_rating = parse_age_rating(card)

    overlay_text = card.find(".//p[@class='overlay-text mb-0']")
    if overlay_text is not None:
        description = clean_str(overlay_text.text)
    else:
        description = title

    li = Listitem()
    li.label = title
    li.art['thumb'] = li.art['landscape'] = video_img
    li.info['plot'] = '\n'.join(x for x in (description,
                                            ' ',
                                            num_episodes,
                                            season_episode,
                                            age_rating) if x)
    li.info['duration'] = parse_duration(card)
    if uvid:
        li.set_callback(play_vod, uvid=uvid)
    else:
        li.set_callback(list_series, url=video_url, )
    menu_utils.item_post_treatment(li, is_playable=uvid is not None)
    return li


@Route.register()
def main_menu(plugin, **__):
    yield Listitem.from_dict(
        callback=list_home_page,
        label='Home',
        params={'url': BASE_URL + '/'}
    )
    yield Listitem.from_dict(
        callback=list_page,
        label='True Crime',
        params={'url': BASE_URL + '/page/true-crime'}
    )
    yield Listitem.from_dict(
        callback=list_page,
        label='Legend',
        params={'url': BASE_URL + '/page/legend'}
    )
    yield Listitem.from_dict(
        callback=list_page,
        label='Series',
        params={'url': BASE_URL + '/page/series'}
    )
    yield Listitem.from_dict(
        callback=list_page,
        label='Movies',
        params={'url': BASE_URL + '/page/movies'}
    )
    yield Listitem.search(do_search)


@Route.register(content_type="videos")
def list_home_page(plugin, url, **_):
    """List the collections found on the home page.

    Collections, a.k. playlists, are shown in sliders on the home page. The contents
    of these sliders are lazy loaded and requested separately as RenderableComponent.
    If a collections has a dedicated page with more items, we let the callback
    request the page, rather than RenderableComponent.

    Currently, it's no use showing hero items. The hero slider only contains images,
    without any info. Not even a title.

    """
    root = fetch(url)
    main = root.find('*/main')

    # List all collections
    for slider_div in main.iterfind(".//div[@class='position-relative z-1 z-2-hover']"):
        callback = list_renderable_component
        slider_url = renderable_url(slider_div)
        fallback_url = None
        title_div = slider_div.find(".//div[@class='slider-title px-g']")
        title = title_div.find('.//h2').text

        # These pages the 'more' buttons link to load very slowly and often
        # contain exactly the same items as the slider, or contain all items
        # already available in a category.
        # Commented this out to just stick to the slider's content for now...
        #
        # more_link = title_div.find('.//a')
        # if more_link:
        #     # This collection has its own page with usually more items than the slider.
        #     fallback_url = slider_url
        #     slider_url = BASE_URL + more_link.get('href')
        #     callback = list_page

        li = Listitem.from_dict(
            callback=callback,
            label=title,
            info={'plot': 'Collection'},
            params={'url': slider_url, 'fallback_url': fallback_url}
        )
        yield li


@Route.register(content_type="videos")
def list_renderable_component(plugin, url, **_):
    """Request and list the content of a renderable component - usually a
    slider on the home page.
    """
    root = fetch(url)
    for video_div in root.iterfind(".//div[@class='swiper-slide']"):
        yield parse_item_div(video_div)


@Route.register(content_type="videos")
def list_page(plugin, url, fallback_url=None, **_):
    root = fetch(url)
    video_items = root.findall(
        ".//div[@class='col-auto layout-carousel-column']")
    if video_items:
        for video_item in video_items:
            yield parse_item_div(video_item)
    elif fallback_url:
        # Some collection pages, like collection LEGEND, do not have the
        # regular page structure. Request the original slider content if
        # the page failed.
        yield from list_renderable_component(plugin, fallback_url, **_)


@Route.register(redirect_single_item=True, content_type="videos")
def list_series(plugin, url, **_):
    root = fetch(url)
    seasons_list = root.find(".//ul[@class='dropdown-menu']")
    for li in seasons_list.iterfind('li'):
        btn = li.find('button')
        title = clean_str(btn.text)
        target = btn.get('data-bs-target')

        item = Listitem()
        item.label = title
        item.set_callback(list_episodes, url=url, series=target.strip('#'))
        menu_utils.item_post_treatment(item, is_playable=False)
        yield item


@Route.register(content_type="videos")
def list_episodes(plugin_, url, series, **_):
    """List the individual episodes of a series page"""
    root = fetch(url)
    series_div = root.find(f".//div[@id='{series}']")
    for episode_div in series_div.iterfind(".//div[@class='row py-5']"):
        video_img = episode_div.find('.//img').get('src')
        data_span = episode_div.find(".//span[@class='d-none']")
        uvid = data_span.get('data-uvid')
        card_body = episode_div.find(".//div[@class='card-body p-0 px-3']")
        title_header = card_body.find('h6')
        episode_nr = clean_str(title_header.text)
        title_link = title_header.find('a')
        url = title_link.get('href')
        video_title = clean_str(title_link.text)
        season_episode = clean_str(card_body.find(".//span[@data-content-type='season-episode']")[0].text)
        description = clean_str(card_body.find(".//p[@class='text-secondary mb-0']").text)
        age_rating = parse_age_rating(card_body)

        item = Listitem()
        item.label = ' ' .join((episode_nr, video_title))
        item.art['thumb'] = item.art['landscape'] = video_img
        item.info['duration'] = parse_duration(card_body)
        item.info['plot'] = ''.join((description, '\n\n', season_episode, '\n', age_rating))
        item.set_callback(play_vod, url=url, uvid=uvid)
        menu_utils.item_post_treatment(item, is_playable=True)
        yield item


@Route.register(content_type="videos")
def do_search(plugin, search_query):
    root = fetch(
        BASE_URL + '/renderable/search/search',
        params={'query': search_query,
                'cc': 'GB'}
    )
    for slider in root.iterfind("./div[@class='component slider']"):
        bold_slider_title = ''.join(('[B]', slider.find(".//h2").text, '[/B]', '\n'))
        for video_div in slider.iterfind(".//div[@class='swiper-slide']"):
            li = parse_item_div(video_div)
            # Search results are grouped into several sliders, like 'Movies',
            # or 'Series', etc. Add the slider's name to the description to
            # better indicate what kind of item it is.
            description = li.info['plot']
            li.info['plot'] = bold_slider_title + description
            yield li


@Resolver.register
def play_vod(plugin, uvid, **_):
    # Get tokens
    resp = urlquick.get(
        url='https://www.watchfreeuk.co.uk/api/player/token/' + uvid,
        headers={
            'user-agent': web_utils.get_random_ua(),
            'accept': 'application/json',
            'environment': 'production',
            'Referer': 'https://www.watchfreeuk.co.uk/'
        },
        timeout=REQ_TIMEOUT,
        max_age=0
    )
    try:
        tokens = json.loads(resp.content)
    except json.JSONDecodeError:
        check_geo_block(resp)
        raise
    analytics = json.loads(tokens['analytics'])

    # Get stream url
    headers = DFLT_HEADERS.copy()
    headers.update({
        'accept': 'application/json',
        'token': tokens['token'],
        'token-expiry': str(tokens['expiry']),
        'userid': '123456',
        'uvid': uvid
    })
    resp = urlquick.post(
        url='https://v2-streams-elb.simplestreamcdn.com/api/show/stream/' + uvid,
        headers=headers,
        params={'key': analytics['api_key'], 'platform': 'firefox'},
        timeout=REQ_TIMEOUT,
        max_age=-1
    )
    strm_data = json.loads(resp.content)
    strm_url = strm_data['response']['stream']
    return resolver_proxy.get_stream_with_quality(plugin, strm_url)

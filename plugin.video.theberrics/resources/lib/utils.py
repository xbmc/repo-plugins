import re

import requests

from scrapers.base import BaseScraper, GOOGLE_CACHE_URL, MAX_RESULTS

# for script.common.plugin.cache
try:
    import StorageServer
except:
    import storageserverdummy as StorageServer
cache = StorageServer.StorageServer("theberrics", 24)

BERRICS_VIDEO_URL = 'http://berrics.vo.llnwd.net/o45/{0}.mp4'
VIDEO_ID_RE = re.compile('data-media-file-id="([a-zA-Z0-9\-]+)"\s')


def get_items_for_category(category, plugin, page=1):
    """
    Collects all video items for the provided category
    """
    url = None
    # Hack for the news category which has a different url for each page
    if category == 'news':
        url = '/news/page:{0}'.format(page)
    scraper = BaseScraper.factory(category, plugin, url)

    # Return cached result or calls function.  Cache expires every 24 hours
    items, total = cache.cacheFunction(scraper.get_items, page)
    has_next = has_next_page(total, page)
    # Hack for the news category which has 100's of pages.
    if category == 'news':
        has_next = True
    return (items, has_next)


def get_items_for_year(category, year, page, plugin):
    """
    Collects all video items for the provided category/year
    """
    scraper = BaseScraper.factory(category, plugin, year)

    items, total = cache.cacheFunction(scraper.get_items, page)
    has_next = has_next_page(total, page)
    return (items, has_next)


def has_next_page(total, page):
    """
    Based on the page and total results, determines if there is a next page
    """
    has_next_page = False
    if total > (MAX_RESULTS * page):
        has_next_page = True
    return has_next_page


def get_years_for_category(category, plugin):
    """
    Collects all years and returns the items for the provided category
    """
    scraper = BaseScraper.factory(category, plugin)
    cache.cacheFunction(scraper.get_years)
    items = scraper.get_years()
    return items


def add_autoplay(url):
    """
    Adds autoplay to the url if it isn't present
    """
    if not url.endswith('?autoplay'):
        url = url + '?autoplay'
    return url


def get_video_url(url):
    """
    Fetches the actual mp4 video file url
    """
    url = add_autoplay(url)
    try:
        r = requests.get(url, timeout=5)
    except requests.Timeout:
        # If we timeout, try to load the page from google cache.
        cache_url = GOOGLE_CACHE_URL.format(url)
        r = requests.get(cache_url)
        if r.status_code != 200:
            raise Exception("Connection timed out trying to load video page "
                            "%s" % url)
    found = VIDEO_ID_RE.findall(r.text)
    if found:
        return BERRICS_VIDEO_URL.format(found[0])


def create_item_for_category(name, category, has_years, media_url, plugin):
    """
    Creates an item for the category list page
    """
    item = {
        'label': name,
        'icon': "{0}{1}.png".format(media_url, category),
        'thumbnail': "{0}{1}.png".format(media_url, category),
    }

    if has_years:
        item['path'] = plugin.url_for('show_years_for_category',
                                      category=category)
    else:
        item['path'] = plugin.url_for('show_category', category=category,
                                      page='1')
    return item


def add_pagination(items, page, has_next_page, kwargs, plugin,
                   route_name='show_category'):
    """
    Handles the logic for determining if pagination is necessary and
    adding previous / next items if needed.
    """
    has_pagination = False

    if has_next_page:
        items.append({
            'label': 'Next >>',
            'path': plugin.url_for(route_name, page=str(page + 1), **kwargs)
        })
        has_pagination = True

    if page > 1:
        items.insert(0, {
            'label': '<< Previous',
            'path': plugin.url_for(route_name, page=str(page - 1), **kwargs)
        })
        has_pagination = True

    return (items, has_pagination)

import re
import urlparse

from BeautifulSoup import BeautifulSoup
import requests

from scrapers.base import BaseScraper, GOOGLE_CACHE_URL, BASE_URL

# for script.common.plugin.cache
try:
    import StorageServer
except:
    import storageserverdummy as StorageServer
cache = StorageServer.StorageServer("thrasherskateboard", 24)


def get_items_for_category(category, plugin, page=1):
    """
    Collects all video items for the provided category
    """
    scraper = BaseScraper.factory(category, plugin, page)

    # Return cached result or calls function.  Cache expires every 24 hours
    items, total_pages = cache.cacheFunction(scraper.get_items, page)
    has_next = False
    if total_pages > page:
        has_next = True
    return (items, has_next)


def get_video_url(url):
    """
    Fetches the actual mp4 video file url
    """
    if not url.startswith(BASE_URL):
        url = BASE_URL + url
    try:
        r = requests.get(url, timeout=5)
    except requests.Timeout:
        # If we timeout, try to load the page from google cache.
        cache_url = GOOGLE_CACHE_URL.format(url)
        r = requests.get(cache_url)
        if r.status_code != 200:
            raise Exception("Connection timed out trying to load video page "
                            "%s" % url)
    soup = BeautifulSoup(r.text)
    meta = soup.find("meta", attrs={'property': 'og:video'})
    if meta:
        video_url = meta['content']
        parsed_url = urlparse.urlparse(video_url)
        params = urlparse.parse_qs(parsed_url.query)
        return params['file'][0]


def create_item_for_category(name, category, media_url, plugin):
    """
    Creates an item for the category list page
    """
    icon = "{0}{1}.png".format(media_url, category)
    item = {
        'label': name,
        'icon': icon,
        'thumbnail': icon,
    }

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

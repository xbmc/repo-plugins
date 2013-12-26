import importlib
from operator import itemgetter
import re

from BeautifulSoup import BeautifulSoup
import requests
from xbmcswift2 import actions


BASE_URL = 'http://theberrics.com'
GOOGLE_CACHE_URL = 'http://webcache.googleusercontent.com/search?q=cache:{0}'
SLUG_RE = re.compile(r'([a-zA-Z0-9\-]+)\.')
YEAR_RE = re.compile(r'[\d]{4}')
MAX_RESULTS = 30


class BaseScraper(object):

    def __init__(self, plugin, category, year_url=None):
        self.plugin = plugin
        self.category = category
        if year_url is not None:
            self.url = BASE_URL + year_url
        try:
            self.response = requests.get(self.url, timeout=5)
        except requests.Timeout:
            # If we timeout, try to load the page from google cache.
            url = GOOGLE_CACHE_URL.format(self.url)
            self.response = requests.get(url)
            if self.response.status_code != 200:
                raise Exception("Connection timed out to %s.  The website may "
                                "be down." % self.url)

        self.soup = BeautifulSoup(self.response.text)

    def log(self, msg):
        """
        A wrapper to more easily perform logging using the scraper
        """
        return self.plugin.log.debug(msg)

    def get_url(self, post):
        """
        Parses the HTML for the url for the video page
        @TODO: what if we can't find it?  Skip this video and continue?
        """
        a = post.find("a")
        return BASE_URL + a['href']

    def get_slice_start_and_end_for_page(self, page):
        """
        Calculates what the start and end should be for the list slice
        based on the page
        """
        start = (page - 1) * MAX_RESULTS
        end = MAX_RESULTS * page
        return (start, end)

    def _get_items(self, page=1, tag='div', attrs={}, sort=False):
        """
        Parses the HTML for all videos on a page and creates and returns
        a list from them.  The total number of items on the page is also
        returned for pagination.
        """
        start, end = self.get_slice_start_and_end_for_page(page)
        elements = self.soup.findAll(tag, attrs=attrs)
        total = len(elements)
        # hack for the oddball news category which always has 15 items
        if self.category != 'news':
            elements = elements[start:end]
        items = [self.get_item(el) for el in elements]
        if sort:
            items = sorted(items, key=itemgetter('label'), reverse=True)
        return (items, total)

    def get_years(self):
        """
        Returns all years as items for the category
        """
        lis = self.soup.findAll("li", attrs={'data-year': YEAR_RE})
        if not lis:
            raise Exception("Couldn't find any additional pages for %s" % (
                self.category,))

        urls = [li.find("a")['href'] for li in lis]
        items = [{
            'label': url.split('/')[-1],
            'label2': url.split('/')[1],
            'path': self.plugin.url_for('show_year', category=self.category,
                                        year=url),
            'is_playable': False
        } for url in urls]
        return items

    @staticmethod
    def get_title_from_url(url, replace=None):
        """
        Grabs the title from the end of the URL.

        Optionally if replace is specified, that string will be removed
        from the title.  This is useful if the url contains the category
        and the title.  i.e. /category-some-title.html?foo=bar would become
        `Some Title` if we specified replace to be 'category'
        """
        title = None
        # Grab the slug portion of the url.  No need to catch an exception
        # as we will get the entire string if the '/' character isn't present
        slug_url = url.split('/')[-1]
        # Get just the slug and none of the .html or params
        match = SLUG_RE.match(slug_url)
        if match:
            slug = match.groups()[0]
            title = ' '.join([word.title() for word in slug.split('-')])
            if replace:
                title = re.sub('(?i)' + re.escape(replace), '', title)
            title = title.strip()
        return title

    @staticmethod
    def factory(category, plugin, year_url=None):
        """
        Factory method for instantiating the correct scraper class based
        on the category string
        """
        # Dynamically import the module
        module = 'resources.lib.scrapers.' + category.replace('_', '')
        module = importlib.import_module(module)

        # Get the class name and return the instance
        class_name = ''.join([word.title() for word in category.split('_')])
        class_name += 'Scraper'
        klass = getattr(module, class_name)
        return klass(plugin, category, year_url=year_url)


class ThumbnailScraper(BaseScraper):
    """
    Base class for pages with many video thumbnails.

    There are several types of video lists on theberrics.com, most of them
    follow this layout.  So all common scraping functions for thumbnails
    are in this class.
    """

    def get_label(self, post):
        """
        Parses the HTML for the label
        """
        date = post.find("div", attrs={'class': 'post-date'})
        date = date.text.encode('ascii', 'ignore')

        name = post.find("div", attrs={'class': 'post-sub-title'})
        name = name.text.encode('ascii', 'ignore')
        name = name.replace('&nbsp;', '')
        if not name:
            url = self.get_url(post)
            name = ThumbnailScraper.get_title_from_url(url)

        if name:
            return "{0} - {1}".format(date, name)
        else:
            return date

    def get_icon(self, post):
        """
        Parses the HTML for the image for the video
        """
        img = post.find("img")
        try:
            icon = img['data-original']
            # Some image paths start with //img/path/file.png so we need to
            # add the http: protocol.
            if not icon.startswith('http:'):
                icon = 'http:' + icon
        except:
            # if we didn't find the img or it didn't have the data-original
            # attribute, use the default video icon
            icon = 'DefaultVideo.png'
        return icon

    def get_item(self, post):
        """
        Creates a single playable item
        """
        label = self.get_label(post)
        icon = self.get_icon(post)
        url = self.get_url(post)
        path = self.plugin.url_for('play_video', url=url)
        download_url = self.plugin.url_for('download_video', url=url)
        item = {
            'label': label,
            'label2': label,
            'icon': icon,
            'thumbnail': icon,
            'path': path,
            'is_playable': True,
            'context_menu': [
                ('Download Video', actions.background(download_url))
            ],
            'replace_context_menu': True
        }
        return item

    def get_items(self, page=1):
        """
        Parses the HTML for all videos and creates a list of them
        """
        attrs = {'class': 'post-thumb standard-post-thumb'}
        return self._get_items(page=page, attrs=attrs, sort=True)


class MenuItemScraper(BaseScraper):
    """
    Base class for pages with divs that have menu-items.

    There are several types of video lists on theberrics.com, this handles
    the 2nd most common layout which is a bunch of rectangle items that have a
    menu-item class.
    """

    def get_label(self, url):
        """
        Grabs the label from the url
        """
        return MenuItemScraper.get_title_from_url(url)

    def get_icon(self, post):
        img = post.find("img")
        return img['src']

    def get_item(self, post):
        url = self.get_url(post)
        label = self.get_label(url)
        icon = self.get_icon(post)
        path = self.plugin.url_for('play_video', url=url)
        item = {
            'label': label,
            'label2': label,
            'icon': icon,
            'thumbnail': icon,
            'path': path,
            'is_playable': True
        }
        return item

    def get_items(self, page=1):
        attrs = {'class': 'menu-item'}
        return self._get_items(page=page, attrs=attrs)

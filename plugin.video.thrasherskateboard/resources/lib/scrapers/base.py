import importlib
from operator import itemgetter
import re

from BeautifulSoup import BeautifulSoup
import requests
from xbmcswift2 import actions


BASE_URL = 'http://www.thrashermagazine.com'
GOOGLE_CACHE_URL = 'http://webcache.googleusercontent.com/search?q=cache:{0}'
PAGE_RE = re.compile(r'[\d]+ of ([\d]+)$')


class BaseScraper(object):

    def __init__(self, plugin, category, page):
        self.plugin = plugin
        self.category = category
        self.page = page
        self.set_url_for_page()
        try:
            self.response = requests.get(self.url, timeout=5)
        except requests.Timeout:
            # If we timeout, try to load the page from google cache.
            url = GOOGLE_CACHE_URL.format(self.url)
            self.response = requests.get(url)
            if self.response.status_code != 200:
                raise Exception("Connection timed out to %s.  The website may "
                                "be down." % self.url)

        self.soup = BeautifulSoup(self.response.text,
                                  convertEntities=BeautifulSoup.HTML_ENTITIES)

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
        return a['href']

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
        summary = self.get_summary(post)
        item['info'] = {}
        item['info']['plot'] = summary
        item['info']['plotoutline'] = summary
        return item

    def _get_items(self, page=1, tag='div', attrs={}, sort=False):
        """
        Parses the HTML for all videos on a page and creates and returns
        a list from them.  The total number of items on the page is also
        returned for pagination.
        """
        elements = self.soup.findAll(tag, attrs=attrs)
        items = [self.get_item(el) for el in elements]
        if sort:
            items = sorted(items, key=itemgetter('label'), reverse=True)
        return (items, self.get_total_pages())

    @staticmethod
    def factory(category, plugin, page=1):
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
        return klass(plugin, category, page)


class GenericItemScraper(BaseScraper):
    """
    Base class for pages that use the genericItem* classes
    """

    def set_url_for_page(self):
        if self.page > 1:
            self.url = self.url + '/Page-{0}/'.format(self.page - 1)

    def get_total_pages(self):
        pages = self.soup.find("div", attrs={"class": "k2Pagination"})
        pages = pages.text.strip()
        match = PAGE_RE.search(pages)
        total_pages = 1
        if match:
            total_pages = int(match.groups()[0])
        return total_pages

    def get_label(self, post):
        """
        Parses the HTML for the label
        """
        title = post.find("h2", attrs={'class': 'genericItemTitle'})
        title = title.text.strip()
        return title

    def get_icon(self, post):
        """
        Parses the HTML for the image for the video
        """
        summary_div = post.find("div", attrs={'class': 'genericItemIntroText'})
        img = summary_div.find("img")
        icon = BASE_URL + img['src']
        return icon

    def get_summary(self, post):
        """
        Grabs the summary for the post
        """
        summary = post.find("div", attrs={'class': 'genericItemIntroText'})
        summary = summary.text.strip()
        return summary

    def get_items(self, page=1):
        """
        Parses the HTML for all videos and creates a list of them
        """
        attrs = {'class': 'genericItemView'}
        return self._get_items(page=page, attrs=attrs)


class BoxScraper(BaseScraper):
    """
    Base scraper for pages that use the box classes
    """

    def set_url_for_page(self):
        if self.page > 1:
            limit_start = (self.page - 1) * 10
            url = self.url.replace('/task,viewcategroy/', '')
            if self.category == 'most_recent':
                url += "limitstart,{0}/task,frontpage/".format(limit_start)
            else:
                url += "limitstart,{0}/task,viewcategory/".format(limit_start)
            self.url = url

    def get_total_pages(self):
        pages = self.soup.find("div", attrs={"class": "pagecount"})
        pages = pages.text.strip()
        match = PAGE_RE.search(pages)
        total_pages = 1
        if match:
            total_pages = int(match.groups()[0])
        return total_pages

    def get_label(self, post):
        """
        Parses the HTML for the label
        """
        title = post.find("div", attrs={'class': 'title'})
        title = title.text.strip()
        return title

    def get_icon(self, post):
        """
        Retrieves the thumbnail from the post
        """
        img = post.find("img")
        img = img['src']
        if not img.startswith(BASE_URL):
            img = BASE_URL + img
        return img

    def get_summary(self, post):
        """
        Grabs the summary for the post
        """
        description = post.find("div", attrs={'class': 'description'})
        return description.text.strip()

    def get_items(self, page=1):
        """
        Parses the HTML for all videos and creates a list of them
        """
        attrs = {'class': 'box'}
        return self._get_items(page=page, attrs=attrs)

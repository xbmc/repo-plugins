import re

from base import BASE_URL, ThumbnailScraper


POST_RE = re.compile(r'\bpost \b')


class NewsScraper(ThumbnailScraper):
    url = 'http://theberrics.com/news'

    def get_label(self, post):
        date = post.find("div", attrs={'class': 'date'})
        date = date.text.encode('ascii', 'ignore')
        # post titles are either h2 or h1 for large posts
        title = post.find('h1') or post.find('h2')
        title = title.text.encode('ascii', 'ignore')
        title = title.replace('&nbsp;', '')

        return "{0} - {1}".format(date, title)

    def get_url(self, post):
        """
        Parses the HTML for the url
        @TODO: What happens if we can't find the url?  Can we skip and continue?
        """
        # post titles are either h2 or h1 for large posts
        heading = post.find("h1") or post.find("h2")
        a = heading.find("a")
        return BASE_URL + a['href']

    def get_items(self, page=1):
        attrs = {'class': POST_RE}
        return self._get_items(page=page, attrs=attrs)

    def get_summary(self, post):
        summary = ''
        try:
            div = post.find("div", attrs={'class': 'summary'})
            summary = div.find("p")
            summary = summary.text.encode('ascii', 'ignore')
        except:
            div = post.find("div", attrs={'class': 'text-content'})
            summary = div.find("p")
            summary = summary.text.encode('ascii', 'ignore')
        return summary.strip()

    def get_item(self, post):
        """
        Creates a single playable item
        """
        item = super(NewsScraper, self).get_item(post)
        summary = self.get_summary(post)
        item['info'] = {}
        item['info']['plot'] = summary
        item['info']['plotoutline'] = summary
        return item

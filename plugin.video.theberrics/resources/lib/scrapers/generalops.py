from base import ThumbnailScraper


class GeneralOpsScraper(ThumbnailScraper):
    url = 'http://theberrics.com/gen-ops'

    def get_label(self, post):
        date = post.find("div", attrs={'class': 'post-date'})
        date = date.text.encode('ascii', 'ignore')
        title = post.find("div", attrs={'class': 'post-title'})
        title = title.text.encode('ascii', 'ignore')
        # If there is an elipsis in the title, grab the title from the URL
        if '...' in title:
            url = self.get_url(post)
            title = ThumbnailScraper.get_title_from_url(url)
        subtitle = post.find("div", attrs={'class': 'post-sub-title'})
        subtitle = subtitle.text.encode('ascii', 'ignore')
        subtitle = subtitle.replace('&nbsp;', '')

        # If the subtitle is in the title, don't include it.
        if subtitle in title:
            subtitle = None

        if date and title and subtitle:
            return "{0} - {1} {2}".format(date, title, subtitle)
        elif date and title:
            return "{0} - {1}".format(date, title)
        else:
            return date

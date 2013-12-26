from base import ThumbnailScraper


class EstScraper(ThumbnailScraper):
    url = 'http://theberrics.com/est'

    def get_label(self, post):
        """
        Parses the HTML for the label
        """
        date = post.find("div", attrs={'class': 'post-date'})
        date = date.text.encode('ascii', 'ignore')
        title = post.find("div", attrs={'class': 'post-title'})
        title = title.text.encode('ascii', 'ignore')
        name = post.find("div", attrs={'class': 'post-sub-title'})
        name = name.text.encode('ascii', 'ignore')
        name = name.replace('&nbsp;', '')

        if title and name:
            return "{0} - {1} {2}".format(date, title, name)
        if name:
            return "{0} - {1}".format(date, name)
        else:
            return date

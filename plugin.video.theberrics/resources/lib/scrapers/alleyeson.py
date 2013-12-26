from base import ThumbnailScraper


class AllEyesOnScraper(ThumbnailScraper):
    url = 'http://theberrics.com/all-eyes-on'

    def get_label(self, post):
        date = post.find("div", attrs={'class': 'post-date'})
        date = date.text.encode('ascii', 'ignore')

        # Get skater's name from the URL since they use an elipsis on the title
        # if it's too long to fit.
        url = self.get_url(post)
        title = ThumbnailScraper.get_title_from_url(url, replace='All Eyes On')
        if title:
            label = "{0} - {1}"
            return label.format(date, title)
        else:
            return date

from base import ThumbnailScraper


class TrickipediaScraper(ThumbnailScraper):
    url = 'http://theberrics.com/trickipedia'

    def get_label(self, post):
        trick = post.find("div", attrs={'class': 'trick'})
        trick = trick.text
        skater = post.find("div", attrs={'class': 'name'})
        skater = skater.text
        return "{0} - {1}".format(trick, skater)

    def get_icon(self, post):
        """
        Parses the HTML for the image for the video
        """
        img = post.find("img")
        try:
            icon = img['data-original']
            icon = icon.replace('w=60', 'w=400')
            icon = icon.replace('h=60', 'h=400')
        except KeyError:
            icon = 'DefaultVideo.png'
        return icon

    def get_items(self, page=1):
        """
        Parses the HTML for all videos and creates a list of them
        """
        attrs = {'class': 'trick-div clearfix'}
        return self._get_items(page=page, attrs=attrs)

from base import BoxScraper


class MostRecentScraper(BoxScraper):
    url = 'http://www.thrashermagazine.com/component/option,com_hwdvideoshare/Itemid,90/lang,en/task,frontpage/'

    def get_items(self, page=1):
        attrs = {'class': 'box', 'id': 'FrontpageList'}
        return self._get_items(page=page, attrs=attrs)

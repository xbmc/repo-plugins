from base import MenuItemScraper


class BattleCommanderScraper(MenuItemScraper):
    url = 'http://theberrics.com/battle-commander'

    def get_label(self, url):
        """
        Grabs the label from the url
        """
        return MenuItemScraper.get_title_from_url(url,
                                                  replace='Battle Commander')

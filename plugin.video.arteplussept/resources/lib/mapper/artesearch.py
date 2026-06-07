"""
Module for Arte Search
"""

# pylint: disable=import-error
from xbmcswift2 import xbmc
from resources.lib import api
from resources.lib.mapper.artecollection import ArteCollection


class ArteSearch(ArteCollection):
    """
    Build item to initiate a search.
    Display a keyboard to received search query.
    Manage search with results spread in multiple pages.
    """

    def build_item(self):
        """
        Return menu entry to search content.
        """
        return {
            'label': self.plugin.addon.getLocalizedString(30012),
            'path': self.plugin.url_for('search_default')
        }

    def init_search(self):
        """Display keyboard to search for content. Then, display the menu of search results.
        Do not display an empty, if search is aborted or search for empty string"""
        query = self._get_search_query()
        if not query:
            self.plugin.end_of_directory(succeeded=False)
        res = api.init_search(self.settings.language, query)
        return self._build_menu(res.get('content'), 'search', zone_id=res.get('id'), query=query)

    def _get_search_query(self):
        """Display keyboard to enter a search query and return it"""
        search_query = ''
        keyboard = xbmc.Keyboard(search_query, self.plugin.addon.getLocalizedString(30012))
        keyboard.doModal()
        if keyboard.isConfirmed() is False:
            return None
        search_query = keyboard.getText()
        if len(search_query) == 0:
            return None
        return search_query

    def _get_page_meta(self, json_dict):
        return json_dict.get('pagination', None)

    def get_search_page(self, zone_id, page, query):
        """Display a page of search results identified with zone_id"""
        return self._build_menu(
            api.get_search_page(self.settings.language, zone_id, page, query),
            'search', zone_id=zone_id, query=query)

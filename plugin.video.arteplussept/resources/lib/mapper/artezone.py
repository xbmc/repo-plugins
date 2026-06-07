"""
Module for Arte Zone
"""

# pylint: disable=import-error
from resources.lib import api
from resources.lib.mapper.artecollection import ArteCollection


class ArteZone(ArteCollection):
    """
    A zone is a collection of video, that may be split in several pages.
    ArteSearch is a special type of zone.
    """

    def __init__(self, plugin, settings, cached_categories=None):
        super().__init__(plugin, settings)
        self.cached_categories = cached_categories

    def build_item(self, zone):
        """
        Return a menu entry to access content of cached category item i.e.
        a zone in the HOME page or SEARH page result.
        """
        zone_id = zone.get('id')
        cached_category = self._build_menu(
            zone.get('content'), 'category_page', zone_id=zone_id, page_id='HOME')
        if self._is_valid_menu(cached_category):
            self.cached_categories[zone_id] = cached_category
            return {
                'label': zone.get('title'),
                'path': self.plugin.url_for('cached_category', zone_id=zone_id)
            }
        return None

    def _is_valid_menu(self, cached_category):
        """
        Menu is valid, if it is a list with at least one element is not None.
        It is not valid if the list contains only None elements
        """
        return isinstance(cached_category, list) and \
            any(elem is not None for elem in cached_category)

    def build_menu(self, zone_id, page, page_id):
        """
        Return the list of items (videos or collection) in the page of the zone with id zone_id.
        page_id is the type of page e.g. HOME, SEARCH...
        """
        return self._build_menu(
            api.get_zone_page(self.settings.language, zone_id, page, page_id),
            'category_page', zone_id=zone_id, page_id=page_id)

    def _get_page_meta(self, json_dict):
        return json_dict.get('pagination', None)

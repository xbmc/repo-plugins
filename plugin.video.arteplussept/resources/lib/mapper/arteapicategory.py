"""
Module for Arte API Category
"""

from resources.lib import api
from resources.lib.mapper import mapper


class ArteApiCategory:
    """
    A API category is a collection of video, that may be split in several pages.
    It is similar to a zone which content comes from Home page, but
    it requires an API call to HBBTV Category endpoint with id coming from Home page.
    """

    def __init__(self, plugin, settings, cached_categories):
        self.plugin = plugin
        self.settings = settings
        self.cached_categories = cached_categories

    def build_item(self, item):
        """
        Return a menu entry to access content of cached category item i.e.
        a zone in the HOME page or SEARH page result.
        """
        return {
            'label': item.get('title'),
            'path': self.plugin.url_for(
                'api_category', category_code=item.get('link').get('page'))
        }

    def build_menu(self, category_code):
        """
        Return the list of items (videos or collection) in the page of the zone with id zone_id.
        page_id is the type of page e.g. HOME, SEARCH...
        """
        cat_menu = []
        idx = 0
        for subcat in api.category(category_code, self.settings.language):
            # Build and cache a menu for each sub category
            idx += 1
            cached_subcat = []
            for teaser in subcat.get('teasers', []):
                menu_item = mapper.map_generic_item(
                    self.plugin, teaser,
                    self.settings.show_video_streams)
                if menu_item is not None:
                    cached_subcat.append(menu_item)
            if cached_subcat:
                subcat_id = f"{category_code}_subcat{idx}"
                self.cached_categories[subcat_id] = cached_subcat
                cat_menu.append({
                    'label': subcat.get('title'),
                    'path': self.plugin.url_for(
                        'cached_category', zone_id=subcat_id)
                })
        return cat_menu

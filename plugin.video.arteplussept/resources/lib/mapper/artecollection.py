"""
Arte Collection is a set of videos or collections like in favorites or history.
"""

# pylint: disable=import-error
from xbmcswift2 import actions
from resources.lib.mapper.arteitem import ArteTvVideoItem


# Utility class that may become an abstract class
# pylint: disable=too-few-public-methods
class ArteCollection:
    """
    Arte Collection is a set of videos or collections like in favorites or history.
    It support pagination. A colleciton is usually a single page of a bigger set.
    It depends on Arte Item to display some of its elements.
    """
    def __init__(self, plugin, settings):
        self.plugin = plugin
        self.settings = settings

    def _build_menu(self, json_dict, collection_type, **nav_arg):
        """
        Build a menu to acces items maanged inside the collection.
        It builds previous page and next page items in the menu,
        if additional pages are available before or after respectively.
        """
        pages = json_dict.get('data', [])
        # implementation in current abstract class returns None.
        # Abstract class should NOT be instantiated
        # pylint: disable=assignment-from-none
        meta = self._get_page_meta(json_dict)
        items = [ArteTvVideoItem(self.plugin, item).map_artetv_item() for item in pages]
        if meta and meta.get('pages', False):
            total_pages = meta.get('pages')
            current_page = meta.get('page')
            if current_page > 1:
                # add previous page at the begining
                items.insert(0, {
                    'label': self.plugin.addon.getLocalizedString(30039),
                    'path': self.plugin.url_for(collection_type, page=current_page-1, **nav_arg),
                })
            if current_page < total_pages:
                # add next page at the end
                items.append({
                    'label': self.plugin.addon.getLocalizedString(30038),
                    'path': self.plugin.url_for(collection_type, page=current_page+1, **nav_arg),
                })
        return items

    def _get_page_meta(self, json_dict):
        """
        Abstract method to get pagination metadata, because they are stored
        either under pagination, either under meta.
        """
        return json_dict.get('meta', None)

    def _build_item(self, collection_type, item_label, purge_label_id):
        """
        Return menu entry to access collection content
        with an additional command to flush collection content
        """
        return {
            'label': item_label,
            'path': self.plugin.url_for(collection_type + '_default'),
            'context_menu': [
                (self.plugin.addon.getLocalizedString(purge_label_id),
                    actions.background(self.plugin.url_for('purge_' + collection_type)))
            ]
        }

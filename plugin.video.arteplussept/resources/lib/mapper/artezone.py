"""
Module for Arte Zone
"""

import xbmc
import xbmcgui
from resources.lib import api
from resources.lib.mapper.artecollection import ArteCollection


class ArteZone(ArteCollection):
    """
    A zone is a collection of video, that may be split in several pages.
    ArteSearch is a special type of zone.
    """

    def build_item(self, zone):
        """
        Return a menu entry to access content of cached category item i.e.
        a zone in the HOME page or SEARH page result.
        """

        if self._is_valid_zone(zone):
            zone_id = zone.get('id')
            li = xbmcgui.ListItem(label=zone.get('title'))
            li.setPath(self.plugin.url_for(
                'category_page', zone_id=zone_id, page_id='HOME', page='1'))
            li.setProperty('is_playable', 'False')
            return li
        xbmc.log(f"Ignore zone {zone.get('label')}. No valid content, only external.", xbmc.LOGINFO)
        return None

    def _is_valid_zone(self, zone):
        """
        Zone is valid, if it contains content data which empty
        or which contains not only EXTERNAL items
        """
        data = (zone or {}).get("content", {}).get("data")
        if isinstance(data, list) and len(data) >= 1:
            valid_count = 0
            for item in data:
                # kind may be a string or a dict with code key.
                item_kind = (item or {}).get("kind", {})
                if isinstance(item_kind, dict):
                    item_kind = item_kind.get("code")
                if item_kind != 'EXTERNAL':
                    valid_count = valid_count + 1
                else:
                    dplnk = item.get('deeplink', '')
                    if isinstance(dplnk, str) and dplnk.strip() != "" and dplnk.rsplit("/", 1)[-1]:
                        valid_count = valid_count + 1
            # if there is not at least one valid item, them zone is not valid
            return valid_count >= 1
        # we cannot be sure it is valid or not, we don't know what it contains
        return True

    def build_menu(self, zone_id, page, page_id):
        """
        Return the list of items (videos or collection) in the page of the zone with id zone_id.
        page_id is the type of page e.g. HOME, SEARCH...
        """
        return self._build_menu(
            api.get_zone_page(self.settings.language, zone_id, page),
            'category_page', zone_id=zone_id, page_id=page_id)

    def _get_page_meta(self, json_dict):
        return json_dict.get('pagination', None)

from tmdbhelper.lib.addon.plugin import get_localized, convert_media_type
from tmdbhelper.lib.api.tvdb.lists import ListLists, ListListItems


class ListAwards(ListLists):
    def get_items(self, info, **kwargs):
        self.plugin_category = get_localized(32460)
        return self._get_items('awards', 'dir_tvdb_award_categories')


class ListAwardCategories(ListLists):
    def get_items(self, info, tvdb_id, **kwargs):
        items = self._get_items(f'awards/{tvdb_id}/extended', 'tvdb_award_category', key='categories')
        self.plugin_category = self.plugin_category or get_localized(32460)
        return items


class ListAwardCategory(ListListItems):
    def _get_item(self, i, award_category, award_category_id, award_type, award_type_id):
        item = self.tvdb_api.mapper.get_type(i)
        if not item:
            return
        item = self.tvdb_api.mapper.get_info(item)
        tmdb_type = convert_media_type(item['infolabels'].get('mediatype'))
        item = self._get_item_tmdb_id(item, tmdb_type)
        if not item:
            return
        item['infoproperties']['award_category'] = award_category
        item['infoproperties']['award_category_id'] = award_category_id
        item['infoproperties']['award_type'] = award_type
        item['infoproperties']['award_type_id'] = award_type_id
        item['infoproperties']['plot_affix'] = f"{get_localized(32461) if i.get('isWinner') else get_localized(32462)} {award_category} {i.get('year')}"
        return item

    def get_items(self, info, tvdb_id, page=1, **kwargs):
        data = self.tvdb_api.get_request_lc('awards', 'categories', tvdb_id, 'extended')
        if not data or not data.get('nominees'):
            return

        award_category = data.get('name')
        award_category_id = data.get('id')
        award_type = data.get('award', {}).get('name')
        award_type_id = data.get('award', {}).get('id')

        _data = sorted(data['nominees'], key=lambda i: i.get('year') or 9999, reverse=True)
        items = self._get_threaded_items(_data, page, award_category, award_category_id, award_type, award_type_id)

        # Figure out container type based on counts of mediatypes
        mediatypes = {}
        for i in items:
            try:
                mediatypes.setdefault(i['infolabels']['mediatype'], []).append(i)
            except (KeyError, TypeError, AttributeError):
                continue
        info_mediatype = max(mediatypes, key=lambda k: len(mediatypes[k])) if mediatypes else 'movie'

        self.library = 'video'
        self.container_content = f'{info_mediatype}s'
        self.plugin_category = data.get('name') or get_localized(32460)
        self.tmdb_cache_only = False

        return items

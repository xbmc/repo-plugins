from xbmcgui import Dialog
from resources.lib.items.listitem import ListItem
from resources.lib.api.fanarttv.api import ARTWORK_TYPES
from resources.lib.api.tmdb.mapping import get_imagepath_poster, get_imagepath_fanart, get_imagepath_thumb, get_imagepath_logo
from resources.lib.addon.dialog import BusyDialog
from resources.lib.addon.plugin import get_localized, executebuiltin
from resources.lib.addon.tmdate import set_timestamp
from resources.lib.addon.window import get_property


class _ArtworkSelector():
    def get_ftv_art(self, ftv_type, ftv_id, artwork_type, season=None):
        ftv_items = self.ftv_api.get_all_artwork(ftv_id, ftv_type, season=season, artlist_type=artwork_type, season_type='season_only')
        return [
            ListItem(
                label=i.get('url'),
                label2=get_localized(32219).format(i.get('lang', ''), i.get('likes', 0), i.get('id', '')),
                art={'thumb': i.get('url')}).get_listitem()
            for i in ftv_items if i.get('url')]

    def get_tmdb_art(self, tmdb_type, tmdb_id, artwork_type, season=None):
        mappings = {
            'poster': {'func': get_imagepath_poster, 'key': 'posters'},
            'fanart': {'func': get_imagepath_fanart, 'key': 'backdrops'},
            'landscape': {'func': get_imagepath_thumb, 'key': 'backdrops'},
            'clearlogo': {'func': get_imagepath_logo, 'key': 'logos'}}
        if artwork_type not in mappings:
            return []
        tmdb_iargs = ['images'] if season is None else ['season', season, 'images']
        tmdb_items = self.tmdb_api.get_request_sc(tmdb_type, tmdb_id, *tmdb_iargs) or {}
        tmdb_items = tmdb_items.get(mappings[artwork_type]['key']) or []
        func = mappings[artwork_type]['func']
        return [
            ListItem(
                label=func(i.get('file_path')),
                label2=get_localized(32219).format(i.get('iso_639_1', ''), i.get('vote_count', 0), i.get('vote_average', 0)),
                art={'thumb': func(i.get('file_path'))}).get_listitem()
            for i in tmdb_items if i.get('file_path') and i.get('file_path', '')[-4:] != '.svg']

    def select_type(self, ftv_type, blacklist=[], item_artwork=None):
        artwork_types = [i for i in ARTWORK_TYPES.get(ftv_type, []) if i not in blacklist]  # Remove types that we previously looked for
        ditems = [ListItem(label=i, art={'thumb': item_artwork.get(i)}).get_listitem() for i in artwork_types] if item_artwork else artwork_types
        choice = Dialog().select(get_localized(13511), ditems, useDetails=True if item_artwork else False)
        if choice == -1:
            return
        return artwork_types[choice]

    def select_artwork(self, tmdb_type, tmdb_id, container_refresh=False, blacklist=[], season=None):
        with BusyDialog():
            item = self.get_item(tmdb_type, tmdb_id, season)
        if not item:
            return
        ftv_id, ftv_type = self.get_ftv_typeid(tmdb_type, item, season=season)
        if not ftv_id or not ftv_type:
            return
        item_artwork = self.get_item_artwork(item['artwork'], is_season=season is not None)
        artwork_type = self.select_type(ftv_type if season is None else 'season', blacklist, item_artwork=item_artwork)
        if not artwork_type:
            if container_refresh:
                executebuiltin('Container.Refresh')
                get_property('Widgets.Reload', set_property=f'{set_timestamp(0, True)}')
            return

        # Get artwork of type and build list
        items = self.get_ftv_art(ftv_type, ftv_id, artwork_type, season=season)
        items += self.get_tmdb_art(tmdb_type, tmdb_id, artwork_type, season=season)
        if season is not None:  # Also get base artwork at end of list
            items += self.get_ftv_art(ftv_type, ftv_id, artwork_type)
            items += self.get_tmdb_art(tmdb_type, tmdb_id, artwork_type)

        # Nothing found so notify user
        if not items:
            Dialog().notification(
                get_localized(39123),
                get_localized(32217).format(tmdb_type, tmdb_id))
            blacklist.append(artwork_type)  # Blacklist artwork type if not found before reprompting
            return self.select_artwork(tmdb_type, tmdb_id, container_refresh, blacklist, season=season)

        # Choose artwork from options
        choice = Dialog().select(get_localized(13511), items, useDetails=True)
        if choice == -1:  # If user hits back go back to main menu rather than exit completely
            return self.select_artwork(tmdb_type, tmdb_id, container_refresh, blacklist, season=season)
        success = items[choice].getLabel()
        if not success:
            return
        container_refresh = True

        # Cache our artwork
        manual = item['artwork'].setdefault('manual', {})
        manual[artwork_type] = success
        item['expires'] = self._timestamp()  # Reup our timestamp to force child items to recache
        self._cache.set_cache(item, cache_name=self.get_cache_name(tmdb_type, tmdb_id, season), cache_days=10000)
        return self.select_artwork(tmdb_type, tmdb_id, container_refresh, blacklist, season=season)

    def refresh_all_artwork(self, tmdb_type, tmdb_id, ok_dialog=True, container_refresh=True, season=None):
        old_cache_refresh = self.ftv_api.cache_refresh
        self.ftv_api.cache_refresh = True

        with BusyDialog():
            item = self.get_item(tmdb_type, tmdb_id, season, cache_refresh=True)
        if not item:
            return Dialog().ok(
                get_localized(39123),
                get_localized(32217).format(tmdb_type, tmdb_id)) if ok_dialog else None
        if ok_dialog:
            artwork_types = {k.capitalize() for k, v in item['artwork'].get('tmdb', {}).items() if v}
            artwork_types |= {k.capitalize() for k, v in item['artwork'].get('fanarttv', {}).items() if v}
            Dialog().ok(
                get_localized(39123),
                get_localized(32218).format(tmdb_type, tmdb_id, ', '.join(artwork_types)))

        # Refresh container to display new artwork
        if container_refresh:
            executebuiltin('Container.Refresh')
            get_property('Widgets.Reload', set_property=f'{set_timestamp(0, True)}')
        self.ftv_api.cache_refresh = old_cache_refresh  # Set it back to previous setting

    def manage_artwork(self, tmdb_id=None, tmdb_type=None, season=None):
        if not tmdb_id or not tmdb_type:
            return
        choice = Dialog().contextmenu([
            get_localized(32220),
            get_localized(32221)])
        if choice == -1:
            return
        if choice == 0:
            return self.select_artwork(tmdb_id=tmdb_id, tmdb_type=tmdb_type, season=season)
        if choice == 1:
            return self.refresh_all_artwork(tmdb_id=tmdb_id, tmdb_type=tmdb_type, season=season)

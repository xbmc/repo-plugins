# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import Dialog
from resources.lib.addon.tmdate import set_timestamp
from resources.lib.addon.thread import ParallelThread
from resources.lib.addon.window import get_property
from resources.lib.addon.dialog import BusyDialog
from resources.lib.addon.parser import try_int
from resources.lib.addon.plugin import set_kwargattr, convert_trakt_type, get_localized, executebuiltin, get_infolabel
from resources.lib.api.trakt.api import TraktAPI
from resources.lib.update.userlist import get_monitor_userlists
from resources.lib.update.library import add_to_library


def _menu_items():
    """ Build the menu of options
    method and sync_type indicate Trakt API call
    preconfigured=True
        - menu item is already preconfigured and will always be included
        - must have 'remove' bool and 'name' str attribs set
    preconfigured=False
        - checks sync to determine 'remove' bool automatically
        - must have 'name_add' and 'name_remove' str attribs set
    allow_episodes=False
        - do not include the menu item if it is a single episode
    """
    return [
        {
            'class': _UserList},
        {
            'class': _SyncItem,
            'kwargs': {
                'method': 'history',
                'sync_type': 'watched',
                'allow_episodes': True,
                'preconfigured': True,
                'remove': False,
                'name': get_localized(16103)}},
        {
            'class': _SyncItem,
            'kwargs': {
                'method': 'history',
                'sync_type': 'watched',
                'allow_episodes': True,
                'preconfigured': True,
                'remove': True,
                'name': get_localized(16104)}},
        {
            'class': _ProgressItem},
        {
            'class': _SyncItem,
            'kwargs': {
                'method': 'collection',
                'sync_type': 'collection',
                'allow_episodes': True,
                'name_add': get_localized(32289),
                'name_remove': get_localized(32290)}},
        {
            'class': _SyncItem,
            'kwargs': {
                'method': 'watchlist',
                'sync_type': 'watchlist',
                'allow_episodes': False,
                'name_add': get_localized(32291),
                'name_remove': get_localized(32292)}},
        {
            'class': _SyncItem,
            'kwargs': {
                'method': 'recommendations',
                'sync_type': 'recommendations',
                'allow_episodes': False,
                'name_add': get_localized(32293),
                'name_remove': get_localized(32294)}},
        {
            'class': _Comments},
    ]


def sync_trakt_item(trakt_type, unique_id, season=None, episode=None, id_type=None):
    if id_type in ['tmdb', 'tvdb', 'trakt']:
        unique_id = try_int(unique_id)
    menu = _Menu(
        items=_menu_items(), trakt_type=trakt_type, unique_id=unique_id, id_type=id_type,
        season=try_int(season, fallback=None), episode=try_int(episode, fallback=None))
    menu.select()


class _Menu():
    def __init__(self, items, **kwargs):
        set_kwargattr(self, kwargs)
        self._trakt = TraktAPI()
        self.build_menu(items)

    def build_menu(self, items):
        def _threaditem(i):
            return i['class'](self, **i.get('kwargs', {}))._getself()

        with BusyDialog():
            with ParallelThread(items, _threaditem) as pt:
                item_queue = pt.queue
            self.menu = [i for i in item_queue if i]

        return self.menu

    def select(self):
        """ Ask user to select item from menu and do the appropriate sync action """
        if not self.menu:
            self.build_menu()
        return self.sync(self._select())

    def _select(self):
        """ Ask user to select menu item """
        if not self.menu:
            return
        x = Dialog().contextmenu([i.name for i in self.menu])
        if x == -1:
            return
        return self.menu[x]

    def sync(self, item, notification=True):
        """ Run sync for selected menu item and notify user of outcome """
        if not item:
            return
        item.sync()
        if item._sync == -1 or not notification:
            return
        if item._sync and item._sync.status_code in [200, 201, 204]:
            get_property('TraktSyncLastActivities.Expires', clear_property=True)  # Wipe last activities cache to update now
            Dialog().ok(
                get_localized(32295),
                get_localized(32297).format(
                    item.name, self.trakt_type, self.id_type.upper(), self.unique_id))
            executebuiltin('Container.Refresh')
            get_property('Widgets.Reload', set_property=f'{set_timestamp(0, True)}')
            return
        Dialog().ok(
            get_localized(32295),
            get_localized(32296).format(
                item.name, self.trakt_type, self.id_type.upper(), self.unique_id))


class _SyncItem():
    def __init__(self, item, **kwargs):
        self._item, self._trakt = item, item._trakt
        self.preconfigured = False
        set_kwargattr(self, kwargs)

    def _getself(self):
        """ Method to see if we should return item in menu or not """
        if self._item.season is not None and (not self.allow_episodes or not self._item.episode):
            return  # Only sync episodes if allowed and we have an episode number

        # Allow early exit for preconfigured items (e.g. watched history to give both choices)
        if self.preconfigured:
            return self

        self.remove = self._trakt.is_sync(
            self._item.trakt_type, self._item.unique_id, self._item.season, self._item.episode,
            self._item.id_type, self.sync_type)
        self.name = self.name_remove if self.remove else self.name_add
        return self

    def sync(self):
        """ Called after user selects choice """
        with BusyDialog():
            self._sync = self._trakt.sync_item(
                f'{self.method}/remove' if self.remove else self.method,
                self._item.trakt_type, self._item.unique_id, self._item.id_type, self._item.season, self._item.episode)
        return self._sync


class _ProgressItem():
    def __init__(self, item, **kwargs):
        self._item, self._trakt = item, item._trakt
        set_kwargattr(self, kwargs)

    def _getself(self):
        """ Method to see if we should return item in menu or not """
        if self._item.trakt_type == 'movie':
            self.playback_id = self._trakt.get_movie_playprogress(
                self._item.unique_id, self._item.id_type, key='id')
        elif self._item.season is None or not self._item.episode:
            return  # Only sync episodes not seasons
        else:
            self.playback_id = self._trakt.get_episode_playprogress(
                self._item.unique_id, self._item.id_type, self._item.season, self._item.episode, key='id')

        if not self.playback_id:
            return

        self.name = get_localized(32417)

        return self

    def sync(self):
        """ Called after user selects choice """
        with BusyDialog():
            self._sync = self._trakt.delete_response('sync', 'playback', self.playback_id)
        return self._sync


class _UserList():
    def __init__(self, item, **kwargs):
        self._item, self._trakt = item, item._trakt
        set_kwargattr(self, kwargs)

    def _getself(self):
        self.remove = get_infolabel("ListItem.Property(param.owner)") == 'true'
        self.name = get_localized(32355) if self.remove else get_localized(32298)
        return self

    def _addlist(self):
        """ Create a new Trakt list and returns tuple of list and user slug """
        name = Dialog().input(get_localized(32356))
        if not name:
            return
        response = self._trakt.post_response('users/me/lists', postdata={'name': name})
        if not response or not response.json():
            return
        return (
            response.json().get('ids', {}).get('slug'),
            response.json().get('user', {}).get('ids', {}).get('slug'))

    def _getlist(self, get_currentlist=False):
        """ Get an existing Trakt list and returns tuple of list and user slug """
        if get_currentlist:
            return (
                get_infolabel("ListItem.Property(param.list_slug)"),
                get_infolabel("ListItem.Property(param.user_slug)"))
        with BusyDialog():
            list_sync = self._trakt.get_list_of_lists('users/me/lists') or []
            list_sync.append({'label': get_localized(32299)})
        x = Dialog().contextmenu([i.get('label') for i in list_sync])
        if x == -1:
            return
        if list_sync[x].get('label') == get_localized(32299):
            return self._addlist()
        return (
            list_sync[x].get('params', {}).get('list_slug'),
            list_sync[x].get('params', {}).get('user_slug'))

    def _addlibrary(self, tmdb_type, tmdb_id, slug=None, confirm=True):
        """ Add item to library
        Pass optional slug tuple (list, user) to check if in monitored lists
        """
        if slug and slug not in get_monitor_userlists():
            return
        if confirm and not Dialog().yesno(get_localized(20444), get_localized(32362)):
            return
        add_to_library(tmdb_type, tmdb_id=tmdb_id)

    def sync(self):
        """ Entry point """
        slug = self._getlist(get_currentlist=self.remove)
        if not slug:
            return
        with BusyDialog():
            self._sync = self._trakt.add_list_item(
                slug[0], self._item.trakt_type, self._item.unique_id, self._item.id_type,
                season=self._item.season, episode=self._item.episode, remove=self.remove)
        if self._sync and self._sync.status_code in [200, 201, 204] and self._item.id_type == 'tmdb':
            self._addlibrary(convert_trakt_type(self._item.trakt_type), self._item.unique_id, slug=slug)
        return self._sync


class _Comments():
    def __init__(self, item, **kwargs):
        self._item, self._trakt = item, item._trakt
        set_kwargattr(self, kwargs)

    def _getself(self):
        self.name = get_localized(32304)
        return self

    def _getcomment(self, itemlist, comments):
        """ Get a comment from a list of comments """
        if not itemlist:
            Dialog().ok(get_localized(32305), get_localized(32306))
            return -1
        x = Dialog().select(get_localized(32305), itemlist)
        if x == -1:
            return -1
        info = comments[x].get('comment')
        name = comments[x].get('user', {}).get('name')
        rate = comments[x].get('user_stats', {}).get('rating')
        info = f'{info}\n\n{get_localized(563)} {rate}/10' if rate else f'{info}'
        Dialog().textviewer(name, info)
        return self._getcomment(itemlist, comments)

    def sync(self):
        trakt_type = 'show' if self._item.trakt_type in ['season', 'episode'] else self._item.trakt_type
        with BusyDialog():
            slug = self._trakt.get_id(self._item.unique_id, self._item.id_type, trakt_type, 'slug')
            comments = self._trakt.get_response_json(f'{trakt_type}s', slug, 'comments', limit=50) or []
            itemlist = [i.get('comment', '').replace('\n', ' ') for i in comments]
        self._sync = self._getcomment(itemlist, comments)
        return self._sync

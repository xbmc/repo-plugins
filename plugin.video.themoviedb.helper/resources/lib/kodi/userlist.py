import xbmc
import xbmcgui
from resources.lib.addon.decorators import busy_dialog
from resources.lib.addon.plugin import ADDON, kodi_log
from resources.lib.trakt.api import TraktAPI
from resources.lib.kodi.library import add_to_library
from resources.lib.kodi.update import get_userlist


def get_monitor_userlists(list_slugs=None, user_slugs=None):
    saved_lists = list_slugs or ADDON.getSettingString('monitor_userlist') or ''
    saved_users = user_slugs or ADDON.getSettingString('monitor_userslug') or ''
    saved_lists = saved_lists.split(' | ') or []
    saved_users = saved_users.split(' | ') or []
    return [(i, saved_users[x]) for x, i in enumerate(saved_lists)]


def monitor_userlist():
    # Build list choices
    with busy_dialog():
        user_lists = [
            {'label': u'{} {}'.format(ADDON.getLocalizedString(32193), xbmc.getLocalizedString(20342)),
                'params': {'user_slug': 'me', 'list_slug': 'watchlist/movies'}},
            {'label': u'{} {}'.format(ADDON.getLocalizedString(32193), xbmc.getLocalizedString(20343)),
                'params': {'user_slug': 'me', 'list_slug': 'watchlist/shows'}}]
        user_lists += TraktAPI().get_list_of_lists('users/me/lists', authorize=True, next_page=False) or []
        user_lists += TraktAPI().get_list_of_lists('users/likes/lists', authorize=True, next_page=False) or []
        saved_lists = get_monitor_userlists()
        dialog_list = [i['label'] for i in user_lists]
        preselected = [
            x for x, i in enumerate(user_lists)
            if (i.get('params', {}).get('list_slug'), i.get('params', {}).get('user_slug')) in saved_lists]

    # Ask user to choose lists
    indices = xbmcgui.Dialog().multiselect(ADDON.getLocalizedString(32312), dialog_list, preselect=preselected)
    if indices is None:
        return

    # Build the new settings and check that lists aren't over limit
    added_lists, added_users = [], []
    for x in indices:
        list_slug = user_lists[x].get('params', {}).get('list_slug')
        user_slug = user_lists[x].get('params', {}).get('user_slug')
        if get_userlist(user_slug, list_slug, confirm=50):
            added_lists.append(list_slug)
            added_users.append(user_slug)

    # Set the added lists to our settings
    if not added_lists or not added_users:
        return
    added_lists = ' | '.join(added_lists)
    added_users = ' | '.join(added_users)
    ADDON.setSettingString('monitor_userlist', added_lists)
    ADDON.setSettingString('monitor_userslug', added_users)

    # Update library?
    if xbmcgui.Dialog().yesno(xbmc.getLocalizedString(653), ADDON.getLocalizedString(32132)):
        library_autoupdate(list_slugs=added_lists, user_slugs=added_users, busy_spinner=True)


def library_autoupdate(list_slugs=None, user_slugs=None, busy_spinner=False, force=False):
    kodi_log(u'UPDATING TV SHOWS LIBRARY', 1)
    xbmcgui.Dialog().notification('TMDbHelper', u'{}...'.format(ADDON.getLocalizedString(32167)))

    # Update library from Trakt lists
    library_adder = None
    user_lists = get_monitor_userlists(list_slugs, user_slugs)
    for list_slug, user_slug in user_lists:
        library_adder = add_to_library(
            info='trakt', user_slug=user_slug, list_slug=list_slug, confirm=False, allow_update=False,
            busy_spinner=busy_spinner, force=force, library_adder=library_adder, finished=False)

    # Update library from nfos
    add_to_library(info='update', busy_spinner=busy_spinner, library_adder=library_adder, finished=True, force=force)

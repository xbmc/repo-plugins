# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from tmdbhelper.lib.script.method.decorators import is_in_kwargs, choose_tmdb_id


@is_in_kwargs({'tmdb_type': ['movie', 'tv']})
@choose_tmdb_id
def add_to_library(tmdb_type=None, tmdb_id=None, **kwargs):
    from tmdbhelper.lib.update.library import add_to_library
    add_to_library(info=tmdb_type, tmdb_id=tmdb_id)


@is_in_kwargs({'user_list': True})
def add_user_list(user_list=None, user_slug=None, **kwargs):
    from tmdbhelper.lib.update.library import add_to_library
    user_slug = user_slug or 'me'
    add_to_library(info='trakt', user_slug=user_slug, list_slug=user_list, confirm=True, allow_update=True, busy_spinner=True)


def run_autoupdate(**kwargs):
    from xbmcgui import Dialog
    from tmdbhelper.lib.update.userlist import library_autoupdate
    from tmdbhelper.lib.addon.plugin import get_localized
    if kwargs.get('force') == 'select':
        choice = Dialog().yesno(
            get_localized(32391),
            get_localized(32392),
            yeslabel=get_localized(32393),
            nolabel=get_localized(32394))
        if choice == -1:
            return
        kwargs['force'] = True if choice else False
    library_autoupdate(
        list_slugs=kwargs.get('list_slug', None),
        user_slugs=kwargs.get('user_slug', None),
        busy_spinner=True if kwargs.get('busy_dialog', False) else False,
        force=kwargs.get('force', False))

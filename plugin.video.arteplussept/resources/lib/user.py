"""
Manage Arte user content and state e.g. favorites and last vieweds.
Manage settings and user interactions to create a token.
Manage token in cache. Avoid storing password in settings, only token.
"""

# pylint: disable=import-error
from xbmcswift2 import xbmc
from xbmcswift2 import xbmcgui

from resources.lib import api

# key to manage token in plugin storage
_STORAGE_KEY = 'token'
# Time to live of 30d
_TTL = 30*24*60


def login(plugin, settings):
    """
    Get user password from UI, create a token with Arte API, persist it in storage
    and update settings state to show user is logged in.
    """
    erase_password_in_old_config(plugin)

    # ensure user to log in is identified
    usr = settings.username
    if not usr:
        msg = f"{plugin.addon.getLocalizedString(30020)} : {plugin.addon.getLocalizedString(30021)}"
        plugin.notify(msg=msg, image='error')
        return False

    # ensure no user is not logged in
    loggedin_usr = is_logged_in_as(plugin)
    tkn_data = get_cached_token(plugin, usr, True)
    if len(loggedin_usr) > 0 and tkn_data:
        xbmc.log(
            f"\"{loggedin_usr}\" already authenticated to Arte TV : {tkn_data['access_token']}")
        # notify user that current token might be replaced
        accept_to_replace = xbmcgui.Dialog().yesno(
            plugin.addon.getLocalizedString(30015),
            plugin.addon.getLocalizedString(30016).format(new_user=usr, old_user=loggedin_usr),
            autoclose=10000
        )
        # user didn't accept replacement, so leave
        if not accept_to_replace:
            xbmc.log('Authentication aborted by user - keep initial token', level=xbmc.LOGWARNING)
            return False

    # get password
    pwd = get_user_password(plugin)
    if not pwd:
        xbmc.log('Authentication aborted by user - no password entered', level=xbmc.LOGWARNING)
        msg = f"{plugin.addon.getLocalizedString(30020)} : {plugin.addon.getLocalizedString(30022)}"
        plugin.notify(msg=msg, image='error')
        return False

    # get token for user and password
    tokens = api.get_and_persist_token_in_arte(plugin, usr, pwd)
    if tokens is None:
        xbmc.log('Authentication failed in arte', level=xbmc.LOGERROR)
        msg = f"{plugin.addon.getLocalizedString(30020)}"
        plugin.notify(msg=msg, image='error')
        return False

    # store token
    set_cached_token(plugin, usr, tokens)
    update_settings_state(plugin, usr)
    msg = plugin.addon.getLocalizedString(30017).format(user=usr)
    plugin.notify(msg=msg, image='info')
    return True


def get_user_password(plugin):
    """
    Display a keyboard to get user password.
    Return None. If user didn't enter a password or close the UI.
    """
    user_password = ''
    keyboard = xbmc.Keyboard(user_password, plugin.addon.getLocalizedString(30019), True)
    keyboard.doModal()
    if keyboard.isConfirmed() is False:
        return None
    user_password = keyboard.getText()
    if len(user_password) == 0:
        return None
    return user_password


def logout(plugin, settings):
    """Delete user token and reset settings state"""
    erase_password_in_old_config(plugin)

    set_cached_token(plugin, settings.username, '')
    clear_cached_tokens(plugin)
    update_settings_state(plugin, '')

    plugin.notify(msg=plugin.addon.getLocalizedString(30018), image='info')
    return True


def update_settings_state(plugin, usr):
    """Update setting state to know who belong the token to"""
    message = plugin.addon.getLocalizedString(30017).format(user=usr)
    if usr is None or len(usr) <= 0:
        message = plugin.addon.getLocalizedString(30018)
    return plugin.set_setting('login_acc', message)


def is_logged_in_as(plugin):
    """Extract the logged in user from settings state"""
    login_acc = plugin.get_setting('login_acc')
    usr = ''
    if isinstance(login_acc, str) and len(login_acc) > 1:
        # remove everything before opening double quote included
        usr = login_acc[login_acc.find('"')+1:]
        # remove everything after closing double quote included
        usr = usr[:usr.rfind('"')]
    return usr


def get_cached_token(plugin, token_idx, silent=False):
    """
    Return cached token for identified user or None.
    If user logged in and later changed the user email, it returns None
    """
    cached_token = plugin.get_storage(_STORAGE_KEY, TTL=_TTL)
    if token_idx in cached_token and isinstance(cached_token[token_idx], dict):
        tokens = cached_token[token_idx]
    else:
        tokens = None
        if not silent:
            plugin.notify(msg=plugin.addon.getLocalizedString(30014), image='warning')
    return tokens


def set_cached_token(plugin, token_idx, tokens):
    """Set cached token"""
    cached_token = plugin.get_storage(_STORAGE_KEY)
    cached_token[token_idx] = tokens


def clear_cached_tokens(plugin):
    """Clear every tokens. Not just the one of the user in parameter."""
    cached_token = plugin.get_storage(_STORAGE_KEY)
    cached_token.clear()


def erase_password_in_old_config(plugin):
    """
    Clean old password, that could be stored in settings from old way
    to authenticate user.
    Deprecated since creation JUL2023, v1.3.0.
    """
    return plugin.set_setting('password', '')

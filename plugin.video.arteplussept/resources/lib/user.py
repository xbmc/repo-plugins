"""
Manage Arte user content and state e.g. favorites and last vieweds.
Manage settings and user interactions to create a token.
Manage token in cache. Avoid storing password in settings, only token.
"""
import datetime
import time
import xbmc
import xbmcaddon
import xbmcgui

from resources.lib import api

# key to manage token in plugin storage
_STORAGE_KEY = 'token'
# Time to live of 30d
_TTL = 30*24*60

addon = xbmcaddon.Addon()


def login(plugin):
    """
    Unified login entry point.
    User chooses between:
    - Smart TV Device login
    - Password login
    """
    erase_password_in_old_config()

    choice = xbmcgui.Dialog().select(
        addon.getLocalizedString(30057),
        [
            addon.getLocalizedString(30046),
            addon.getLocalizedString(30047)
        ]
    )
    if choice == 0:
        return login_with_device_flow(plugin)
    if choice == 1:
        return login_with_password(plugin)
    return False


# ---------------------------------------------------------------------------
# PASSWORD LOGIN
# ---------------------------------------------------------------------------

def login_with_password(plugin):
    """
    Get user email and password from UI, create a token with Arte API, persist it in storage
    and update settings state to show user is logged in.
    """
    # get email from user
    email = get_user_email()
    if not email:
        xbmc.log('Authentication aborted by user - no email entered', level=xbmc.LOGWARNING)
        plugin.notify(msg=addon.getLocalizedString(30020), image='error')
        return False

    # if user already logged in with this email and token is valid, confirm s/he wants to override
    if not want_to_continue_or_override_auth(plugin, email):
        return False

    # get password
    pwd = get_user_password()
    if not pwd:
        xbmc.log('Authentication aborted by user - no password entered', level=xbmc.LOGWARNING)
        plugin.notify(msg=addon.getLocalizedString(30020), image='error')
        return False

    # get token for user and password
    token = api.authenticate_in_arte(plugin, email, pwd)
    token = _normalize_and_anchor_expiry_date(token)
    if token is None or not _is_future(token.get('expires_in')):
        xbmc.log('Authentication failed in arte', level=xbmc.LOGERROR)
        msg = f"{addon.getLocalizedString(30020)}"
        plugin.notify(msg=msg, image='error')
        return False

    # store token
    set_cached_token(plugin, email, token)
    update_login_state_settings(plugin, email)
    msg = addon.getLocalizedString(30017).format(user=email)
    plugin.notify(msg=msg, image='info')
    return True


def get_user_email():
    """
    Display a keyboard to get user email.
    Return None if user didn't enter an email or close the UI.
    """
    user_email = addon.getSettingString('username')
    keyboard = xbmc.Keyboard(user_email, addon.getLocalizedString(30013), False)
    keyboard.doModal()
    if keyboard.isConfirmed() is False:
        return None
    user_email = keyboard.getText()
    if len(user_email) == 0:
        return None
    return user_email


def want_to_continue_or_override_auth(plugin, new_user):
    """
    If user already authenticated (with a valid token and) with same email,
    confirm that s/he wants to override her/his token.
    Return False if user confirms replacement, True otherwise.
    Return true, if token is invalid or emails are different.
    """
    # assuming that new user's email and old user's email are the same,
    # since token can be retrieved/is indexed by email.
    current_tkn = get_cached_token(plugin, new_user, True)
    expiry_date = _get_expiry_date(current_tkn)
    if _is_future(expiry_date):
        xbmc.log(f"\"{new_user}\" already authenticated until : {expiry_date or 'unknown'}")
        # notify user that current token might be replaced
        accept_to_replace = xbmcgui.Dialog().yesno(
            addon.getLocalizedString(30015),
            # old_user=new_user highlight the unsual situation
            addon.getLocalizedString(30016).format(new_user=new_user, old_user=new_user),
            autoclose=10000
        )
        # user didn't accept replacement, so leave
        if not accept_to_replace:
            xbmc.log('Authentication aborted by user - keep initial token', level=xbmc.LOGWARNING)
            return False
    return True


def get_user_password():
    """
    Display a keyboard to get user password.
    Return None. If user didn't enter a password or close the UI.
    """
    user_password = ''
    keyboard = xbmc.Keyboard(user_password, addon.getLocalizedString(30019), True)
    keyboard.doModal()
    if keyboard.isConfirmed() is False:
        return None
    user_password = keyboard.getText()
    if len(user_password) == 0:
        return None
    return user_password


# ---------------------------------------------------------------------------
# SMART TV DEVICE FLOW LOGIN
# ---------------------------------------------------------------------------

def login_with_device_flow(plugin):
    """
    Smart TV Device Authorization Flow:
    1. Request device_code + user_code
    2. Show instructions and code to authenticate on another device
    3. Poll token endpoint until success
    4. Retrieve email from personal data endpoint
    5. Store token
    """
    # Step 1 - request device_code
    device_info = api.device_authorization_request()
    if not device_info:
        plugin.notify(addon.getLocalizedString(30020), image='error')
        return False

    device_code = device_info["device_code"]
    user_code = device_info["user_code"]
    verification_uri = device_info["verification_uri"]
    # verification_uri_complete = device_info["verification_uri_complete"]
    interval = device_info.get("interval", 5)

    # Step 2 - show instructions and code to authenticate on another device
    show_device_login_dialog(user_code, verification_uri)

    # Step 3 - poll token endpoint
    token = poll_device_token(device_code, interval, device_info["expires_in"])
    token = _normalize_and_anchor_expiry_date(token)
    if token is None or not _is_future(token.get('expires_in')):
        plugin.notify(addon.getLocalizedString(30020), image='error')
        return False

    # Step 4 - retrieve email from personal data endpoint
    user_data = api.get_personal_data(token)
    if user_data is None:
        xbmc.log('Failed to retrieve personal data from Arte API', level=xbmc.LOGERROR)
        plugin.notify(addon.getLocalizedString(30020), image='error')
        return False

    email = user_data.get('email')
    if not email:
        xbmc.log('Email not found in personal data from Arte API', level=xbmc.LOGERROR)
        plugin.notify(addon.getLocalizedString(30020), image='error')
        return False

    # Step 5 - store token
    set_cached_token(plugin, email, token)
    update_login_state_settings(plugin, email)
    msg = addon.getLocalizedString(30017).format(user=email)
    plugin.notify(msg=msg, image='info')
    return True


def show_device_login_dialog(user_code, verification_uri):
    """
    Display instructions and user code to authenticate on another device
    """
    xbmcgui.Dialog().ok(
        addon.getLocalizedString(30048),
        addon.getLocalizedString(30049).format(
            user_code=user_code, verification_uri=verification_uri)
    )


def poll_device_token(device_code, interval, expires_in):
    """
    Poll ARTE token endpoint until:
    - authorization_pending
    - slow_down
    - success (returns token)
    - error (returns None)
    """
    deadline = time.monotonic() + expires_in
    while time.monotonic() < deadline:
        data = api.device_token_request(device_code)

        if "access_token" in data:
            return data

        error = data.get("error")

        if error == "authorization_pending":
            time.sleep(min(interval, max(0, deadline - time.monotonic())))
            continue

        if error == "slow_down":
            interval += 5
            time.sleep(min(interval, max(0, deadline - time.monotonic())))
            continue

        xbmc.log(f"Device login error: {error}", level=xbmc.LOGERROR)
        return None

    xbmc.log("Device login expired before authorization completed", level=xbmc.LOGERROR)
    return None


# ---------------------------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------------------------


def logout(plugin):
    """Delete user token and reset settings state"""
    erase_password_in_old_config()

    # Possible improve - revoke token remotely or logout

    # clear token locally
    email = addon.getSettingString('username')
    set_cached_token(plugin, email, '')
    clear_cached_tokens(plugin)
    update_login_state_settings(plugin, email)
    plugin.notify(msg=addon.getLocalizedString(30018), image='info')
    return True

# ---------------------------------------------------------------------------
# EXISTING UTILITIES
# ---------------------------------------------------------------------------


def update_login_state_settings(plugin, email):
    """
    Update login state according to token validity of email's token
    """
    token = get_cached_token(plugin, email, True)
    token = _normalize_and_anchor_expiry_date(token)
    xbmc.log(f"Update login state for user {email}: {token.get('expires_in') if token else 'None'}")
    if token and _is_future(token.get('expires_in')):
        set_cached_token(plugin, email, token)
        message = addon.getLocalizedString(30017).format(user=email)
    else:
        message = addon.getLocalizedString(30018)
    addon.setSetting('login_acc', message)


def _normalize_and_anchor_expiry_date(token):
    """
    Return token with normalized expiry date in date time iso format.
    Return the token in parameter, potentially None
    """
    expiry_date = _get_expiry_date(token)
    if isinstance(expiry_date, datetime.datetime):
        token['expires_in'] = expiry_date.isoformat()
    return token


def _get_expiry_date(token):
    """
    Return token expiry date or None
    """
    if not isinstance(token, dict):
        return None

    expires_in = token.get('expires_in')
    creation_date = token.get('created')
    expiry_date = expires_in  # default to expires_in if it's a datetime or None
    if isinstance(expires_in, (int, float)):
        if isinstance(creation_date, (int, float)):
            expiry_date = datetime.datetime.fromtimestamp(
                creation_date + expires_in, datetime.timezone.utc)
        else:
            xbmc.log("Token has no valid created timestamp, " +
                     "assuming it expire_in is a timestamp on top of now",
                     level=xbmc.LOGWARNING)
            expiry_date = datetime.datetime.now(datetime.timezone.utc) + \
                datetime.timedelta(seconds=expires_in)
    elif isinstance(expires_in, str):
        expiry_date = datetime.datetime.fromisoformat(expires_in)
    # else let go through datetime and None
    return expiry_date


def _is_future(dt) -> bool:
    """
    Return True if ts is in future, False otherwise e.g. None
    """
    try:
        if isinstance(dt, (str)):
            dt = datetime.datetime.fromisoformat(dt)
        now = datetime.datetime.now(datetime.timezone.utc)
        return dt > now
    # pylint: disable=broad-exception-caught
    except Exception:
        pass
    xbmc.log("Unable to parse Arte token expiration date", xbmc.LOGERROR)
    return False


def get_cached_token(plugin, token_idx, silent=False):
    """
    Return cached token for identified user or None.
    If no token is in cache and silent is not True, then it warns user
    about the need to authenticate.
    If user logged in and later changed the user email, it returns None.
    """
    cached_token = plugin.get_storage(_STORAGE_KEY, ttl=_TTL)
    if token_idx in cached_token and isinstance(cached_token[token_idx], dict):
        token = cached_token[token_idx]
    else:
        token = None
        if not silent:
            plugin.notify(msg=addon.getLocalizedString(30014), image='warning')
    return token


def set_cached_token(plugin, email, token):
    """Set cached token"""
    cached_token = plugin.get_storage(_STORAGE_KEY)
    cached_token[email] = token
    addon.setSetting('username', email)


def clear_cached_tokens(plugin):
    """Clear every tokens. Not just the one of the user in parameter."""
    cached_token = plugin.get_storage(_STORAGE_KEY)
    cached_token.clear()


def erase_password_in_old_config():
    """
    Clean old password, that could be stored in settings from old way
    to authenticate user.
    Deprecated since creation JUL2023, v1.3.0.
    """
    return addon.setSetting('password', '')

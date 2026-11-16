"""Account actions triggered from the settings dialog (RunPlugin modes)."""

import time
from typing import Optional

import xbmc
import xbmcgui

from kofin.core import auth, ipc, settings, toast
from kofin.core.http import (
    Http,
    HttpError,
    JellyfinError,
    ServerUnreachable,
    Unauthorized,
    plugin_transport,
)
from kofin.core.log import Logger
from kofin.core.settings import Credentials
from kofin.plugin.router import Request

LOG = Logger(__name__)

QUICK_CONNECT_TIMEOUT_SECONDS = 180
QUICK_CONNECT_POLL_SECONDS = 1.5


def _text(string_id: int) -> str:
    return settings.localized(string_id)


def _notification(message: str, level: str = toast.INFO) -> None:
    toast.show(message, level, time_ms=4000)


def _device_name() -> str:
    return settings.device_name()


def login(request: Request) -> None:
    creds = Credentials.load()
    if creds.is_logged_in:
        _notification(_text(30025))
        return

    address_raw = settings.get_str("serverAddress")
    if not address_raw:
        address_raw = xbmcgui.Dialog().input(_text(30052))
        if not address_raw:
            return

    transport = plugin_transport(settings.user_agent())
    try:
        address = auth.normalize_address(address_raw)
        info = auth.public_info(transport, address)
    except HttpError as error:
        # A server that answered, badly. The description matters: a redirect
        # names the address the user should have typed, and "unreachable"
        # would mislead.
        LOG.warning("server ping answered badly for %s: %s", address, error)
        _notification(_text(30821) % error, toast.ERROR)
        return
    except JellyfinError as error:
        LOG.warning("server ping failed for %s: %s", address, error)
        _notification(_text(30018), toast.ERROR)
        return
    except ValueError as error:
        # An address no request can be made to: urllib cannot split it (a
        # port past 65535, an IPv6 literal without its brackets), or the IDNA
        # codec refuses its host name.
        LOG.warning("server address refused: %s", error)
        _notification(_text(30018), toast.ERROR)
        return

    header = auth.build_auth_header(
        _device_name(), creds.device_id, settings.addon_version()
    )
    server_name = info.get("ServerName") or address

    try:
        result = _authenticate(transport, address, header, server_name)
    except Unauthorized:
        _notification(_text(30017), toast.ERROR)
        return
    except JellyfinError as error:
        LOG.warning("sign-in failed: %s", error)
        _notification(_text(30018), toast.ERROR)
        return
    finally:
        transport.close()

    if result is None or not result.token:
        return

    creds.server_address = address
    creds.server_name = server_name
    creds.server_id = result.server_id
    creds.user_id = result.user_id
    creds.display_user = result.user_name
    creds.token = result.token
    creds.is_logged_in = True
    creds.save()

    ipc.notify(ipc.AUTH_CHANGED)
    _notification(_text(30016) % result.user_name)
    LOG.debug("signed in to %s", server_name)


def _authenticate(
    transport: Http, address: str, header: str, server_name: str
) -> Optional[auth.AuthResult]:
    quick_connect = False
    try:
        quick_connect = auth.quick_connect_enabled(transport, address, header)
    except JellyfinError:
        pass

    if quick_connect:
        choice = xbmcgui.Dialog().select(
            _text(30027) % server_name, [_text(30011), _text(30012)]
        )
        if choice < 0:
            return None
        if choice == 0:
            return _login_quick_connect(transport, address, header)
    return _login_password(transport, address, header)


def _login_password(
    transport: Http, address: str, header: str
) -> Optional[auth.AuthResult]:
    username = xbmcgui.Dialog().input(_text(30013))
    if not username:
        return None
    # Dialog.input answers "" both for a cancel and for an empty password,
    # which a Jellyfin account may have; the keyboard says which it was.
    keyboard = xbmc.Keyboard(heading=_text(30014), hidden=True)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return None
    return auth.authenticate_password(
        transport, address, header, username, keyboard.getText()
    )


def _login_quick_connect(
    transport: Http, address: str, header: str
) -> Optional[auth.AuthResult]:
    state = auth.quick_connect_initiate(transport, address, header)
    secret = state.get("Secret", "")
    code = state.get("Code", "")
    if not secret or not code:
        return None

    progress = xbmcgui.DialogProgress()
    progress.create(_text(30011), _text(30015) % code)
    monitor = xbmc.Monitor()
    started = time.time()
    try:
        while time.time() - started < QUICK_CONNECT_TIMEOUT_SECONDS:
            if progress.iscanceled():
                return None
            if auth.quick_connect_poll(transport, address, header, secret):
                return auth.authenticate_quick_connect(
                    transport, address, header, secret
                )
            percent = int((time.time() - started) * 100 / QUICK_CONNECT_TIMEOUT_SECONDS)
            progress.update(min(99, percent), _text(30015) % code)
            if monitor.waitForAbort(QUICK_CONNECT_POLL_SECONDS):
                return None
    finally:
        progress.close()
    _notification(_text(30024), toast.WARNING)
    return None


def logout(request: Request) -> None:
    creds = Credentials.load()
    if not creds.is_logged_in:
        _notification(_text(30026))
        return
    message = _text(30019) % creds.server_name
    if settings.get_list("librarySelection"):
        # The rows stay keyed to this account; a different one takes them out.
        message += "\n" + _text(30896)
    if not xbmcgui.Dialog().yesno("Kofin", message):
        return

    transport = plugin_transport(settings.user_agent())
    header = auth.build_auth_header(
        _device_name(), creds.device_id, settings.addon_version(), creds.token
    )
    auth.logout(transport, creds.server_address, header)
    transport.close()

    Credentials.clear()
    ipc.notify(ipc.AUTH_CHANGED)
    _notification(_text(30020))
    LOG.debug("signed out")


def test_connection(request: Request) -> None:
    from kofin.core.api import Api

    creds = Credentials.load()
    if not creds.is_logged_in:
        _notification(_text(30026))
        return

    api = Api.for_plugin(creds)
    try:
        info = api.public_info()
        api.views()
    except Unauthorized:
        _notification(_text(30022), toast.ERROR)
        return
    except ServerUnreachable:
        _notification(_text(30018), toast.ERROR)
        return
    except JellyfinError as error:
        # A server that answered, badly: not unreachable, not a session
        # problem.
        _notification(_text(30821) % error, toast.ERROR)
        return
    finally:
        api.close()
    _notification(_text(30021) % (info.get("ServerName", ""), info.get("Version", "")))


def restart(request: Request) -> None:
    ipc.notify(ipc.RESTART)
    _notification(_text(30023))

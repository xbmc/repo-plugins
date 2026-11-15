"""The phone login in Kodi: the QR code shown until the phone sends the login back (see loginserver)."""

import contextlib
import os
import time

import xbmc

from resources.lib import kodiutil

# Seconds the QR code waits for the phone.
TIMEOUT = 900
# Home window property set while a login runs: a second start waits for the first to end, since
# the QR window may be seconds in coming up and the Log in button pressed twice.
IN_PROGRESS = "%s.login_in_progress" % kodiutil.ADDON_ID


def wait_for_token(client, timeout=TIMEOUT):
    """Show the QR code and wait; return what the phone sent (the address with the token), None if closed or late.

    QR code -> page on the phone -> provider login -> the phone posts the result back.
    """
    home = kodiutil.home()
    if home.getProperty(IN_PROGRESS):
        kodiutil.log("another login already running: this one left the QR window out", xbmc.LOGINFO)
        return None
    home.setProperty(IN_PROGRESS, "1")
    try:
        return _phone_login(client, timeout)
    finally:
        home.clearProperty(IN_PROGRESS)


def _phone_login(client, timeout):
    """Show the QR code and wait: see wait_for_token."""
    from resources.lib.login import loginserver
    from resources.lib.login import qrwindow

    texts = {name: kodiutil.string(string_id) for name, string_id in loginserver.TEXT_IDS.items()}
    receiver = loginserver.LoginReceiver(client.login_url(), texts, xbmc.getLanguage(xbmc.ISO_639_1))
    url = receiver.phone_url(xbmc.getIPAddress())
    # Kodi on the phone itself can't scan its own QR code: the address opens in its browser, over
    # loopback, which works whatever address Kodi reports for the LAN.
    own_url = receiver.phone_url("127.0.0.1") if kodiutil.phone_or_tablet() else None
    hint = kodiutil.string(30268 if own_url else 30028)
    qr_png = os.path.join(kodiutil.PROFILE, "login_qr.png")
    qrwindow.make_qr_png(url, qr_png)
    window = qrwindow.QrWindow(kodiutil.PROFILE, kodiutil.string(30027), qr_png, url, hint, open_url=own_url)
    window.show()
    monitor = xbmc.Monitor()
    try:
        start = time.time()
        while receiver.token is None:
            if window.closed or time.time() - start > timeout or monitor.waitForAbort(0.5):
                return None
        return receiver.token
    finally:
        window.close()
        del window
        receiver.stop()
        with contextlib.suppress(OSError):
            os.remove(qr_png)

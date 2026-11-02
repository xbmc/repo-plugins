"""The phone login on the TV: the QR code shown until the phone sends the login back (see loginserver)."""

import contextlib
import os
import time

import xbmc

from resources.lib import kodiutil

# Seconds the QR code waits for the phone.
TIMEOUT = 900


def wait_for_token(client, timeout=TIMEOUT):
    """Show the QR code and wait; return what the phone sent (the address with the token), None if closed or late.

    QR code -> page on the phone -> provider login -> the phone posts the result back.
    """
    from resources.lib.login import loginserver
    from resources.lib.login import qrwindow

    texts = {name: kodiutil.string(string_id) for name, string_id in loginserver.TEXT_IDS.items()}
    receiver = loginserver.LoginReceiver(client.login_url(), texts, xbmc.getLanguage(xbmc.ISO_639_1))
    url = receiver.phone_url(xbmc.getIPAddress())
    qr_png = os.path.join(kodiutil.PROFILE, "login_qr.png")
    qrwindow.make_qr_png(url, qr_png)
    window = qrwindow.QrWindow(kodiutil.PROFILE, kodiutil.string(30027), qr_png, url, kodiutil.string(30028))
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

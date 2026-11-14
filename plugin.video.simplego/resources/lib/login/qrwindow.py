"""Full-screen dialog showing the phone-login QR code."""

import os
import struct
import zlib

import xbmcgui

from resources.lib import kodiutil

# Kodi action IDs (xbmc/input/actions/ActionIDs.h: parent dir, previous menu, nav back, ...),
# and the raw escape and backspace key codes.
ACTIONS_CLOSE = (9, 10, 92, 216, 247, 257, 275, 61467, 61448)
CENTRE = 0x00000002  # XBFONT_CENTER_X
# Names in Kodi's colour list (system/colors.xml): mediumvioletred is the nearest to the provider's magenta.
TITLE_COLOUR = "mediumvioletred"
URL_COLOUR = "white"
HINT_COLOUR = "lightgrey"


def _solid_png(path, rgb):
    """Write a 16x16 single-colour PNG: the dialog background, skin-independent."""
    raw = b"".join(b"\x00" + bytes(rgb) * 16 for _ in range(16))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 16, 16, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b"")
        )


def make_qr_png(text, path):
    """Write a PNG of the QR code for this text."""
    import pyqrcode

    pyqrcode.create(text, error="M").png(path, scale=12, quiet_zone=3)


class QrWindow(xbmcgui.WindowDialog):
    """Show a title, the QR code, its address and a hint; `closed` turns true when the user closes it.

    :param workdir: a folder for the background image
    :param title: the heading above the QR code
    :param qr_png: the QR code's image (see make_qr_png)
    :param url: the address the QR code holds, shown under it
    :param hint: the instructions shown at the bottom
    """

    def __init__(self, workdir, title, qr_png, url, hint):
        super().__init__()
        self.closed = False
        bg = os.path.join(workdir, "login_bg.png")
        if not os.path.exists(bg):
            _solid_png(bg, (16, 16, 20))
        self.addControl(xbmcgui.ControlImage(0, 0, 1280, 720, bg))
        # Colours by name (textColor takes only hex): Kodi's colour list, which a skin can override.
        title = kodiutil.coloured(TITLE_COLOUR, title)
        self.addControl(xbmcgui.ControlLabel(0, 30, 1280, 50, title, font="font30", alignment=CENTRE))
        self.addControl(xbmcgui.ControlImage(460, 100, 360, 360, qr_png))
        url = kodiutil.coloured(URL_COLOUR, url)
        self.addControl(xbmcgui.ControlLabel(0, 480, 1280, 40, url, font="font13", alignment=CENTRE))
        hint_box = xbmcgui.ControlTextBox(140, 530, 1000, 170, font="font13")
        self.addControl(hint_box)
        hint_box.setText(kodiutil.coloured(HINT_COLOUR, hint))

    def onAction(self, action):
        """Close the window on back, stop and the like (see ACTIONS_CLOSE)."""
        if action.getId() in ACTIONS_CLOSE:
            self.closed = True
            self.close()

"""
    Kodi video capturer for Hyperion

    Copyright (c) 2013-2016 Hyperion Team

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.
"""
from __future__ import annotations

import xbmc
import xbmcaddon
 
 
class MessageHandler:
    """Notify and logging facility for Kodi add-ons."""

    def __init__(self, addon: xbmcaddon.Addon) -> None:
        self._addon = addon
        self._addon_name = addon.getAddonInfo('name')
        self._addon_icon = addon.getAddonInfo('icon')

    def log(self, message: str, level=xbmc.LOGDEBUG) -> None:
        """Writes the message to the logger with the addon name as prefix."""
        xbmc.log(f"[{self._addon_name}] - {message}", level=level)

    def notify(self, label_id: int) -> None:
        """Displays a notification with the localized message."""
        message = self._addon.getLocalizedString(label_id)
        xbmc.executebuiltin(
            f"XBMC.Notification({self._addon_name},{message},1000,{self._addon_icon})"
        )
 
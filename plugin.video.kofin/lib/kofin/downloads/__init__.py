"""Offline downloads.

The store (kofin.db ``download`` table), the file layout, and the
service-side manager live here.
"""

import os

TAG = "Kofin Downloads"
# A downloaded episode's own tag, which its show never carries: Kodi's tag
# rule on episodes matches the episode's tags or its show's, so a rule on
# TAG would list every episode of a show with a download.
EPISODE_TAG = "Kofin Downloaded episodes"

ADDON_DATA = "special://profile/addon_data/plugin.video.kofin/"


def downloads_root() -> str:
    """The absolute downloads root: the setting, or the profile default.

    Here rather than in the manager so the plugin need not import the
    manager to resolve it.
    """
    import xbmcvfs

    from kofin.core import settings

    configured = settings.get_str("downloadsPath")
    if configured:
        return xbmcvfs.translatePath(configured).rstrip("/")
    return os.path.join(xbmcvfs.translatePath(ADDON_DATA), "downloads")


# What ``downloadsNotify`` never silences: failures, and the two empty-list
# answers of the manage buttons (30766, 30853).
LOUD_STRINGS = frozenset(
    {
        30018,  # server request failed
        30713,  # download failed
        30715,  # not enough free space
        30717,  # downloads folder not writable
        30720,  # not available offline
        30766,  # no shows are set to download new episodes
        30853,  # no playlist or music-library content is set to download
    }
)


def notify_allowed(string_id: int) -> bool:
    """Whether this toast may be shown, given the notification opt-out."""
    if string_id in LOUD_STRINGS:
        return True

    from kofin.core import settings

    return settings.get_bool("downloadsNotify")

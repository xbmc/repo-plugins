# -*- coding: utf-8 -*-
"""Answers Kodi's find-a-manual dialog from the REG-Vault catalogue.

Kodi calls this the way it calls a subtitle service - as a plugin, with a
directory listing for an answer:

  plugin://plugin.game.manuals.regvault/?action=search&path=<game>&title=<name>

The dialog hands over the game's path and leaves the matching to us, so the
ROM is hashed here rather than in Kodi. Each result's path is the manual
itself, which Kodi copies to wherever it wants it.

Everything that can be reasoned about without Kodi lives in resources/lib and
is tested on its own. This file is only the part that has to talk to Kodi.
"""

import sys
import urllib.parse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

sys.path.insert(0, xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo("path")))

from resources.lib import hashing  # noqa: E402
from resources.lib import regvault  # noqa: E402
from resources.lib import systems  # noqa: E402

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")

HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 else -1


def log(message, level=xbmc.LOGINFO):
    xbmc.log("%s: %s" % (ADDON_ID, message), level)


def setting_int(name, default):
    try:
        value = ADDON.getSettingInt(name)
        return default if value is None else value
    except (TypeError, ValueError, RuntimeError):
        return default


class VfsStream(object):
    """A readable, seekable view of a file through Kodi's filesystem.

    Games commonly live on a share, which plain open() cannot reach. This is
    enough of a file object for hashing, and for zipfile to read a zipped ROM.
    """

    def __init__(self, path):
        self._file = xbmcvfs.File(path)
        self._position = 0

    def read(self, size=-1):
        data = bytes(
            self._file.readBytes(size) if size and size > 0 else self._file.readBytes()
        )
        self._position += len(data)
        return data

    def seek(self, offset, whence=0):
        self._position = self._file.seek(offset, whence)
        return self._position

    def tell(self):
        return self._position

    def close(self):
        self._file.close()

    def seekable(self):
        return True

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        self.close()
        return False


def vfs_open(path):
    return VfsStream(path)


def human_size(size):
    """A file size written the way it would be read out."""
    if size <= 0:
        return ""

    if size < 1024 * 1024:
        return "%.0f KB" % (size / 1024.0)
    if size < 1024 * 1024 * 1024:
        return "%.1f MB" % (size / (1024.0 * 1024.0))

    return "%.1f GB" % (size / (1024.0 * 1024.0 * 1024.0))


def vfs_size(path):
    handle = xbmcvfs.File(path)
    try:
        return handle.size()
    finally:
        handle.close()


def search(params):
    """List whatever manuals the catalogue holds for one game."""
    path = params.get("path", "")

    if not path:
        xbmcplugin.endOfDirectory(HANDLE)
        return

    try:
        rom_hash, rom_name = hashing.hash_file(
            path,
            setting_int("rom_size_limit", 512) * 1024 * 1024,
            opener=vfs_open,
            sizer=vfs_size,
        )
    except hashing.Skipped as reason:
        log("not searching for %s: %s" % (path, reason))
        xbmcplugin.endOfDirectory(HANDLE)
        return

    client = regvault.Client()

    # The folder name is the better hint at which machine a game is for, and
    # the extension follows it. A wrong guess is only a 404, so each is tried.
    for system in systems.candidates(path, rom_name):
        try:
            game = client.lookup(system, rom_hash)
        except (regvault.Unavailable, regvault.RateLimited) as error:
            log("search failed: %s" % error, xbmc.LOGWARNING)
            break

        if not game:
            continue

        if not game.get("has_manual"):
            # The game is catalogued but has no manual, so the remaining
            # candidate systems cannot help either
            break

        # The catalogue can hold several entries for one game, and the entry a
        # ROM hashes to is not always the one its manual comes from -
        # manual_rom_hash names that one. Where they differ, describe it
        # instead, because what is being offered is the manual, not the file on
        # disk.
        #
        # This is not a corner case. The entry Super Mario Bros. hashes to is
        # merged from three sources and reads 2013 / Playtronic - a Wii U
        # re-release date against a Brazilian licensee - while the entry its
        # manual actually belongs to, built from one source, reads the 1985 /
        # Nintendo everyone would expect.
        described = game
        manual_hash = game.get("manual_rom_hash")

        if manual_hash and manual_hash != rom_hash:
            try:
                other = client.lookup(system, manual_hash)
            except (regvault.Unavailable, regvault.RateLimited) as error:
                log("could not read the manual's own entry: %s" % error, xbmc.LOGWARNING)
                other = None

            if other:
                described = other

        title = described.get("title_en") or game.get("title_en") or systems.stem(path)

        # Keyed on the ROM's own hash: that is the lookup the service documents,
        # and it follows manual_rom_hash itself to find the document
        url = "%s/game/%s/%s/manual" % (regvault.BASE_URL, system, rom_hash)

        try:
            size = client.size_of(url)
        except (regvault.Unavailable, regvault.RateLimited) as error:
            # Worth showing the manual anyway - not knowing how big it is is a
            # worse answer than nothing only if it stops the download
            log("could not size the manual: %s" % error, xbmc.LOGWARNING)
            size = 0

        item = xbmcgui.ListItem(label=title)
        item.setLabel2(human_size(size) or systems.display_name(system))

        # The described entry leads, and the ROM's own fills in behind it -
        # the two rarely carry the same set, and a missing picture is worth
        # more than a matching one
        assets = dict(game.get("assets") or {})
        assets.update({k: v for k, v in (described.get("assets") or {}).items() if v})

        art = {}

        # The box is what settles "is this my game" in one glance, well before
        # any of the text does
        if assets.get("box_front"):
            art["thumb"] = regvault.ASSET_BASE_URL + assets["box_front"]
            art["poster"] = art["thumb"]
        if assets.get("fanart"):
            art["fanart"] = regvault.ASSET_BASE_URL + assets["fanart"]
        if art:
            item.setArt(art)

        # The catalogue answers with a list for some games and one
        # comma-separated string for others, and the string form has no spaces
        # after its commas - so it is split apart and rejoined rather than
        # passed through as "Action,Platformer,2D"
        genre = described.get("genre") or []
        if isinstance(genre, str):
            genre = genre.split(",")

        genre = [part.strip() for part in genre if part and part.strip()]

        properties = {
            "manual.title": title,
            "manual.system": systems.display_name(system),
            "manual.region": systems.region(path),
            "manual.size": human_size(size),
            # Only if it could be when this machine's games came out - see
            # systems.plausible_year for why that check earns its keep
            "manual.year": (
                str(described.get("year"))
                if systems.plausible_year(system, described.get("year"))
                else ""
            ),
            "manual.publisher": described.get("publisher") or "",
            "manual.developer": described.get("developer") or "",
            "manual.genre": ", ".join(genre),
            "manual.plot": described.get("description_en") or game.get("description_en") or "",
        }

        # An empty property still counts as set, and the skin decides what to
        # show by asking whether one is there, so the blanks are dropped
        item.setProperties({k: v for k, v in properties.items() if v})

        xbmcplugin.addDirectoryItem(HANDLE, url, item, False)
        break

    xbmcplugin.endOfDirectory(HANDLE)


def main():
    params = dict(urllib.parse.parse_qsl(sys.argv[2][1:])) if len(sys.argv) > 2 else {}

    if params.get("action") == "search":
        search(params)
        return

    # There is nothing to browse: this add-on exists to answer Kodi, not to be
    # opened on its own
    xbmcplugin.endOfDirectory(HANDLE, succeeded=False)


if __name__ == "__main__":
    main()

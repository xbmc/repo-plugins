"""File layout, naming, sanitization and free-space for downloads.

Pure decisions plus one filesystem probe (:func:`free_space_ok`) — no Kodi
imports, so every rule here is table-testable. Layout: human-readable,
components frozen at download time, stored as POSIX-style paths relative to
the downloads root.
"""

import os
import posixpath
import re
import shutil
import sys
import unicodedata
from collections.abc import Collection
from typing import Any, Callable, Optional

from kofin.core.log import Logger

LOG = Logger(__name__)

JsonDict = dict[str, Any]

# What FAT/exFAT/NTFS refuse in a name (Android SD cards are the audience,
# and every other target accepts this subset too). Windows' reserved device
# names (CON, PRN, ...) are a Windows-API restriction, not a filesystem one,
# and no target here mounts the tree through that API. Control characters
# ride along in the same class.
_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WHITESPACE = re.compile(r"\s+")
_EXTENSION = re.compile(r"[a-z0-9]{1,8}")

# Free space kept in reserve beyond the download itself: Kodi's own caches
# and databases live on the same volume more often than not, and filling it
# to the last byte breaks them first (Emby's reserve, same number).
FREE_SPACE_RESERVE = 2 * 1024**3

# A request is confirmed once it would take a quarter of the free space.
CONFIRM_FREE_SPACE_RATIO = 0.25

MOVIES_DIR = "Movies"
SHOWS_DIR = "Shows"
MUSIC_DIR = "Music"


def sanitize(name: str) -> str:
    """A path component safe on every target filesystem.

    Unsafe characters are dropped, whitespace runs collapse, and trailing
    dots and spaces are stripped (FAT). Kodi's Python can run with an ASCII
    filesystem encoding; there the name folds to ASCII (NFKD). An empty
    result answers "untitled".
    """
    cleaned = _WHITESPACE.sub(" ", _UNSAFE.sub("", name)).strip().rstrip(". ")
    if cleaned and not _fits_filesystem(cleaned):
        folded = (
            unicodedata.normalize("NFKD", cleaned)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
        cleaned = _WHITESPACE.sub(" ", folded).strip().rstrip(". ")
    return cleaned or "untitled"


def _fits_filesystem(name: str) -> bool:
    try:
        name.encode(sys.getfilesystemencoding() or "utf-8")
    except UnicodeEncodeError:
        return False
    return True


def filename_from_disposition(value: str, fallback: str) -> str:
    """The server's filename out of a Content-Disposition header.

    Handles both the plain ``filename="..."`` parameter and the RFC 5987/2231
    ``filename*=UTF-8''...`` form via the stdlib parser. The result is taken
    as a bare basename and sanitized — a header is server input, and a path
    that walks out of the downloads tree must be impossible by construction.
    """
    from email.message import Message

    if value:
        message = Message()
        message["content-disposition"] = value
        raw = message.get_filename()
        if raw:
            # Basename first, then sanitize: dots inside a name survive
            # sanitize (only trailing ones are stripped), so the extension
            # needs no special-casing once the path parts are gone.
            name = sanitize(posixpath.basename(str(raw).replace("\\", "/")))
            if name != "untitled":
                return name
    return fallback


def extension(value: str, fallback: str) -> str:
    """A container or codec name the server gave, as a file extension, or
    ``fallback``. Anything but a short word of letters and digits would put a
    separator, a ``..`` or a second extension into the file name."""
    candidate = str(value or "").strip().lower()
    return candidate if _EXTENSION.fullmatch(candidate) else fallback


def contained(rel_path: str) -> bool:
    """Whether ``rel_path`` stays inside the folder it is joined to.

    A drive (Windows' ``C:name``) is refused too: ``os.path.join`` drops the
    folder for it, though it is not absolute."""
    if not rel_path or os.path.isabs(rel_path) or posixpath.isabs(rel_path):
        return False
    if os.path.splitdrive(rel_path)[0]:
        return False
    parts = rel_path.replace("\\", "/").split("/")
    return all(part not in ("", ".", "..") for part in parts)


def default_filename(item: JsonDict, container: str) -> str:
    """The filename when no Content-Disposition names one — every transcode,
    whose response carries no original name. Episodes lead with SxxEyy and
    songs with their track number, so a directory reads in order the way the
    server's own filenames do."""
    name = sanitize(str(item.get("Name") or item.get("Id") or "download"))
    item_type = item.get("Type", "")
    if item_type == "Episode":
        season = item.get("ParentIndexNumber")
        episode = item.get("IndexNumber")
        if season is not None and episode is not None:
            name = "S%02dE%02d %s" % (int(season), int(episode), name)
    elif item_type == "Audio":
        track = item.get("IndexNumber")
        if track is not None:
            name = "%02d %s" % (int(track), name)
    return "%s.%s" % (name, extension(container, "bin"))


def item_dirs(item: JsonDict) -> tuple[str, Optional[str]]:
    """(owning directory, leaf subdirectory) for an item, relative, POSIX.

    Movies: ``("Movies/<Title (Year)>", None)`` — the directory belongs to
    the film alone. Episodes: ``("Shows/<Show>", "Season NN")`` — the *show*
    directory is the owner and the season is a leaf inside it (season 0 is
    ``Specials``, Kodi's own convention; an episode with no season number
    sits directly under the show). Any other type raises.
    """
    item_type = item.get("Type", "")
    if item_type == "Movie":
        title = sanitize(str(item.get("Name") or ""))
        year = item.get("ProductionYear")
        return (
            posixpath.join(MOVIES_DIR, "%s (%s)" % (title, year) if year else title),
            None,
        )
    if item_type == "Episode":
        show = posixpath.join(SHOWS_DIR, sanitize(str(item.get("SeriesName") or "")))
        season = item.get("ParentIndexNumber")
        if season is None:
            return show, None
        if int(season) == 0:
            return show, "Specials"
        return show, "Season %02d" % int(season)
    if item_type == "Audio":
        # ``Music/<AlbumArtist>/<Album>``, the album directory owning its
        # tracks the way a show's owns its episodes (owner = album id). The
        # artist level is plain nesting — nothing owns or uniquifies it, like
        # the ``Shows/`` type directory.
        artists = item.get("AlbumArtists") or []
        artist = str(
            item.get("AlbumArtist")
            or (artists[0].get("Name") if artists else "")
            or (item.get("Artists") or [""])[0]
            or "Unknown artist"
        )
        album = str(item.get("Album") or "Unknown album")
        return (
            posixpath.join(MUSIC_DIR, sanitize(artist), sanitize(album)),
            None,
        )
    raise ValueError("no download layout for item type %r" % item_type)


def unique_dir(base: str, owner_id: str, taken: Callable[[str], bool]) -> str:
    """``base``, or ``base [<id-prefix>]`` when another *owner* holds it.

    Two titles can sanitize identically (a show and its remake, "Crash
    (2004)" twice); the suffix is deterministic and applied only on a real
    clash, so the common case stays clean. ``owner_id`` is the film's own id
    or — for an episode — its *series* id, and ``taken`` answers whether the
    directory already belongs to a different owner. Owners, not items: every
    episode of a show shares that show's directory, and a per-item test
    would suffix each sibling into a directory of its own.
    """
    if not taken(base):
        return base
    return "%s [%s]" % (base, owner_id[:8])


def stem(filename: str) -> str:
    """A file name without its extension: what sidecars are named after, and
    what a removal clears beside the file (every ``<stem>.*``)."""
    return filename.rsplit(".", 1)[0]


def stems_clash(first: str, second: str) -> bool:
    """Whether files of these two stems can be taken for each other's: the
    same stem, compared as FAT and exFAT compare names, or one that carries
    on past a dot from the other, which a removal of the shorter matches."""
    first, second = first.casefold(), second.casefold()
    return first == second or _carries_on(first, second) or _carries_on(second, first)


def _carries_on(longer: str, shorter: str) -> bool:
    return longer.startswith(shorter + ".")


# The last number unique_filename tries: past the discs of any album.
MAX_NAME_NUMBER = 999


def unique_filename(filename: str, held: Collection[str]) -> Optional[str]:
    """``filename``, or a numbered form of it from 2 whose stem clashes with
    none of the stems ``held``; None when no number up to
    ``MAX_NAME_NUMBER`` gives one.

    Two items of one directory can carry the same name: a track of each disc
    of an album, which a server holds as ``CD1/01.flac`` and ``CD2/01.flac``,
    or two transcoded tracks of one number and title. The number follows the
    stem, ``01 (2).flac``, unless the stem carries on past a dot from a held
    one (``01. Title`` beside ``01``), as every ``<stem> (n)`` then does too:
    there the number leads, ``(2) 01. Title.flac``.
    """
    base = stem(filename)
    extension = filename[len(base) :]
    if not _clashes(base, held):
        return filename
    folded = base.casefold()
    template = (
        "({number}) {stem}"
        if any(_carries_on(folded, other.casefold()) for other in held)
        else "{stem} ({number})"
    )
    for number in range(2, MAX_NAME_NUMBER + 1):
        candidate = template.format(stem=base, number=number)
        if not _clashes(candidate, held):
            return candidate + extension
    return None


def _clashes(candidate: str, held: Collection[str]) -> bool:
    return any(stems_clash(candidate, other) for other in held)


def free_bytes(root: str) -> int:
    """Bytes available to an unprivileged writer under ``root``, -1 unknown.

    -1 rather than 0 for "could not tell": 0 is a real answer that means a
    full disk, and the two must not read alike to a caller putting the
    number in front of a person.
    """
    try:
        # statvfs exists on POSIX only; disk_usage reads it there and asks
        # Windows for the caller's free bytes.
        return shutil.disk_usage(root).free
    except OSError as error:
        LOG.debug("free-space probe failed for %s: %s", root, error)
        return -1


def free_space_ok(root: str, expected_bytes: int) -> bool:
    """Whether the volume under ``root`` fits the download plus the reserve.

    A probe that cannot answer (exotic mount, permissions) allows the
    download rather than refusing it: the write itself will fail loudly if
    space truly runs out, while a false refusal is undiagnosable.
    """
    free = free_bytes(root)
    if free < 0:
        return True
    return free >= int(expected_bytes) + FREE_SPACE_RESERVE


def on_this_device(root: str) -> bool:
    """Whether ``root`` is a folder Python's own file calls reach. Kodi's
    ``translatePath`` leaves a network location (``smb://``, ``nfs://``) as
    it is, and ``os`` reads one as a folder under the working directory."""
    return "://" not in root


def absolute_path(root: str, rel_path: str) -> str:
    """The one spelling of a download's on-disk location.

    Raises ValueError for a path outside ``root``, and for any path under a
    ``root`` not on this device. A row's path was built from a server's
    answer, possibly to an earlier build, so it is checked on every use and
    not only when it is chosen.
    """
    if contained(rel_path) and on_this_device(root):
        absolute = os.path.join(root, rel_path)
        base = os.path.abspath(root)
        if os.path.commonpath([base, os.path.abspath(absolute)]) == base:
            return absolute
    raise ValueError("not inside the downloads folder: %r" % rel_path)


def path_in(root: str, rel_path: str) -> Optional[str]:
    """``absolute_path``, or None where it refuses: for the callers that only
    look at a file or remove one, which leave such a row alone."""
    try:
        return absolute_path(root, rel_path)
    except ValueError:
        return None


def part_path(root: str, rel_path: str) -> str:
    """The in-flight sibling ``absolute_path`` lands as."""
    return absolute_path(root, rel_path) + ".part"


# Names a folder as the downloads root kofin wrote to. A done row whose file
# is missing counts as deleted by hand only inside a folder that carries it:
# without it the folder is a drive that is not mounted, or a location changed
# to another folder.
MARKER = ".kofin-downloads"


def has_marker(root: str) -> bool:
    return os.path.isfile(os.path.join(root, MARKER))


def write_marker(root: str) -> bool:
    """Mark ``root``; False when the folder cannot be written."""
    try:
        with open(os.path.join(root, MARKER), "a", encoding="utf-8"):
            pass
    except OSError as error:
        LOG.debug("could not mark %s as the downloads folder: %s", root, error)
        return False
    return True

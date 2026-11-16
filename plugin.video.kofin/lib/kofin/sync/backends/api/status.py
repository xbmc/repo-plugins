"""What the sync has done and is doing, for the status dialog in the settings.

The library thread writes one small document when its state changes: what it
is doing, since when, the names of the libraries it is listing for the first
time, which the catalogue has no row of yet, which change-feed companion
the server answered for (``record_feed``), and the selected libraries the
server no longer lists (``record_missing``). Everything else the dialog shows is
read from the catalogue at the moment it is opened, by the plugin process that
draws it, so nothing is kept up to date for a dialog nobody has open.

The thread stamps what it writes with its account's namespace, and the
dialog reads only the document of the account that is logged in, or an
unstamped one.
"""

import json
import os
import threading
import time
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, NamedTuple, Optional, Union

import xbmc
import xbmcgui

from kofin.core import settings
from kofin.core.log import Logger
from kofin.sync import changefeed, kofindb, private
from . import capabilities, metadata, progress

if TYPE_CHECKING:
    from .store import Store

# A string by its id, and Kodi's own word for a kind.
Text = Callable[[int], str]
KindLabel = Callable[[str], str]
Clock = Callable[[float], time.struct_time]

LOG = Logger(__name__)

DOCUMENT = "sync-status.json"
# The kind whose rows a viewer would count for a library of each type.
COUNTED = {
    "movies": ("Movie",),
    "tvshows": ("Episode",),
    "musicvideos": ("MusicVideo",),
    "mixed": ("Movie", "Episode", "MusicVideo"),
    "music": ("Audio",),
}
# Where the databases to delete are listed, for a viewer not going back.
MIGRATION_PAGE = "https://github.com/kontell/plugin.video.kofin/wiki/Kodi-versions"


def path() -> str:
    return os.path.join(private.addon_data_path(), DOCUMENT)


def read(namespace: str = "") -> dict[str, Any]:
    """The document, as far as it has the shape ``write`` gives it. It is
    read by another process than the one that wrote it, and a field of
    another type (a hand edit, a later build's) is left out, not shown. A
    document another account's thread stamped reads as nothing for
    ``namespace``; one without a stamp is anyone's."""
    try:
        with open(path(), encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, ValueError):
        return {}
    if not isinstance(document, dict):
        return {}
    stamped = document.get("namespace")
    if namespace and isinstance(stamped, str) and stamped and stamped != namespace:
        return {}
    found: dict[str, Any] = {}
    state = document.get("state")
    if isinstance(state, str):
        found["state"] = state
    since = document.get("since")
    if isinstance(since, (int, float)) and not isinstance(since, bool):
        found["since"] = float(since)
    listing = document.get("listing")
    if isinstance(listing, list):
        found["listing"] = [name for name in listing if isinstance(name, str)]
    feed = document.get("feed")
    if isinstance(feed, str):
        found["feed"] = feed
    missing = document.get("missing")
    if isinstance(missing, list):
        found["missing"] = [name for name in missing if isinstance(name, str)]
    if document.get("earlier") is True:
        found["earlier"] = True
    return found


def write(
    state: str, listing: Iterable[str] = (), namespace: str = "", earlier: bool = False
) -> None:
    """Record what the sync is doing, in the words the dialog shows, and the
    names of the libraries whose first listing is under way, for the account
    ``namespace`` (the library thread's store). Written only when either
    changes; ``since`` is when the state began. The feed the library thread
    last detected rides along unchanged, and another account's document is
    replaced whole. ``earlier`` says the state is ``write_earlier``'s."""
    current = read(namespace)
    listing = list(listing)
    same = current.get("state") == state
    if (
        same
        and (current.get("listing") or []) == listing
        and current.get("earlier", False) == earlier
    ):
        return
    since = current.get("since") if same else None
    document: dict[str, Any] = {
        "state": state,
        "since": since or time.time(),
        "listing": listing,
    }
    for kept in ("feed", "missing"):
        if kept in current:
            document[kept] = current[kept]
    if earlier:
        document["earlier"] = True
    _store(document, namespace)


def write_earlier(namespace: str = "") -> None:
    """Sync is off over what the SQL build left (``EarlierLibrary``), which
    the dialog reads as a reason to give the way out instead of the report."""
    write(
        settings.localized(30420) % settings.localized(30888),
        namespace=namespace,
        earlier=True,
    )


def record_feed(tier: str, namespace: str = "") -> None:
    """Record which change-feed companion the server answered for
    (``changefeed.detect``: its ``TIER_*``), so the dialog can say whether
    KofinSyncQueue is there. Written only when the answer moved."""
    current = read(namespace)
    if current.get("feed") == tier:
        return
    document: dict[str, Any] = dict(current)
    document["feed"] = tier
    _store(document, namespace)


def record_missing(names: list[str], namespace: str = "") -> None:
    """Record the selected libraries the server no longer lists, by name,
    until they have left (``Library.settle_missing``). Written only when the
    list moved."""
    current = read(namespace)
    if (current.get("missing") or []) == names:
        return
    document: dict[str, Any] = dict(current)
    if names:
        document["missing"] = list(names)
    else:
        document.pop("missing", None)
    _store(document, namespace)


def _store(document: dict[str, Any], namespace: str = "") -> None:
    if namespace:
        document["namespace"] = namespace
    target = path()
    # A path of this thread's own: two service generations may write at once.
    part = "%s.%d.part" % (target, threading.get_ident())
    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(part, "w", encoding="utf-8") as handle:
            json.dump(document, handle)
        os.replace(part, target)
    except OSError as error:
        # A status that cannot be written is never a reason to fail a sync.
        LOG.debug("sync status not written: %s", error)
        try:
            os.remove(part)
        except OSError:
            pass


class LibraryStatus(NamedTuple):
    library: str
    name: str
    media: str
    total: int  # rows a viewer would count: movies, episodes, songs
    filed: int  # of them, in Kodi
    unfiled: int  # of them, settled without a row: Kodi cannot file them
    leaving: bool  # being removed
    stale: bool  # filed under an older scanner format (metadata.SCANNER_FORMAT)


class Snapshot(NamedTuple):
    libraries: list[LibraryStatus]
    pending: int
    failed: int
    error: str
    enumerated: float


def snapshot(store: "Store", scanner_format: int) -> Snapshot:
    """The catalogue as the dialog shows it, in a handful of queries."""
    with private.Database() as db:
        views = {
            view.view_id: (view.name, view.media_type)
            for view in kofindb.JellyfinDatabase(db.cursor).views()
        }
    whitelist = private.get_sync()["Whitelist"]
    counts = store.summary()
    leaving = store.leaving()
    libraries = []
    for library in sorted(
        set(whitelist) | set(leaving), key=lambda i: views.get(i, (i,))[0]
    ):
        name, media = views.get(library, (library, "mixed"))
        kinds = COUNTED.get(media, COUNTED["mixed"])
        total, filed, unfiled = (
            sum(counts.get((library, kind), (0, 0, 0))[part] for kind in kinds)
            for part in range(3)
        )
        libraries.append(
            LibraryStatus(
                library,
                name,
                media,
                total,
                filed,
                unfiled,
                library in leaving and library not in whitelist,
                media != "music"
                and filed > 0
                and store.scanner_format(library) < scanner_format,
            )
        )
    pending, failed, error = store.outstanding()
    return Snapshot(libraries, pending, failed, error, store.watermark()[1])


def rows(
    document: dict[str, Any],
    found: Snapshot,
    text: Text,
    kind_label: KindLabel,
    clock: Clock = time.localtime,
    features: Optional[dict[str, bool]] = None,
) -> list[str]:
    """The dialog's lines. ``text`` gives a string by its id and
    ``kind_label`` Kodi's own word for a kind; ``features`` is the capability
    table of this Kodi (``capabilities.table``), whose off entries are named
    on one row. The whole of what is shown is decided here, where it can be
    tested without a dialog."""
    lines = []
    state = document.get("state") or text(20177)
    began = _moment(document.get("since") or 0, clock)
    if began:
        # An update that began hours ago is one that stopped.
        state = "%s (%s)" % (state, began)
    lines.append("%s:  %s" % (text(30262), state))
    # A first listing: the server is still being asked what the library has.
    known = {library.name for library in found.libraries}
    for name in document.get("listing") or []:
        if name not in known:
            lines.append("%s:  %s" % (name, text(314)))
    for library in found.libraries:
        if library.leaving:
            lines.append("%s:  %s" % (library.name, text(30408)))
            continue
        kinds = COUNTED.get(library.media, COUNTED["mixed"])
        lines.append(
            "%s:  %s / %s %s"
            % (
                library.name,
                _number(library.filed),
                _number(library.total),
                kind_label(kinds[0]) if len(kinds) == 1 else "",
            )
        )
    # A special with no episode number is the usual one: without the row
    # a library a few short of the server's count reads as a failed import.
    unfiled = unfiled_row(found, text)
    if unfiled:
        lines.append(unfiled)
    stale = [library.name for library in found.libraries if library.stale]
    if stale:
        lines.append("%s:  %s" % (text(30867), ", ".join(stale)))
    missing = document.get("missing") or []
    if missing:
        lines.append("%s:  %s" % (text(30894), ", ".join(missing)))
    if found.pending:
        lines.append("%s:  %s" % (text(30863), _number(found.pending)))
    if found.failed:
        line = "%s:  %s" % (text(30864), _number(found.failed))
        if found.error:
            line += " (%s)" % found.error[:120]
        lines.append(line)
    enumerated = _moment(found.enumerated, clock)
    if enumerated:
        lines.append("%s:  %s" % (text(30865), enumerated))
    feed = document.get("feed")
    if feed is not None:
        # Whether the server has the companion the catch-up is built for.
        # Kodi's own "Not available" (10005) covers the official KodiSyncQueue
        # and no companion alike; the log names which.
        available = feed == changefeed.TIER_KOFIN
        lines.append(
            "%s:  %s" % (text(30886), text(30887) if available else text(10005))
        )
    if features is not None:
        # What this Kodi cannot do, counted here and named in the viewer the
        # row opens (``show``).
        off = off_features(features, text)
        if off:
            lines.append("%s:  %s" % (text(30876), _number(len(off))))
    return [line.rstrip() for line in lines]


def unfiled_row(found: Snapshot, text: Text) -> str:
    """The row counting what Kodi cannot import; empty when nothing."""
    unfiled = sum(library.unfiled for library in found.libraries)
    return "%s:  %s" % (text(30868), _number(unfiled)) if unfiled else ""


def counted(found: Snapshot) -> list[tuple[str, str]]:
    """The ``(library, kind)`` pairs that row counts, which is what the
    store is asked for (``store.unfiled``), so the list is as long as the
    count."""
    return [
        (library.library, kind)
        for library in found.libraries
        for kind in COUNTED.get(library.media, COUNTED["mixed"])
    ]


def unfiled_report(
    entries: Iterable[tuple[str, str, dict[str, Any]]], found: Snapshot, text: Text
) -> str:
    """What that row counts, for its text viewer: what to do, then each
    item by its show and its title, under its library's name when more
    than one library has any. ``entries`` are ``store.unfiled`` of
    ``counted(found)``. A library is its id: two may share a name."""
    names = {status.library: status.name for status in found.libraries}

    def name(library: str) -> str:
        return names.get(library) or library

    grouped: dict[str, list[str]] = {}
    for library, _kind, item in entries:
        grouped.setdefault(library, []).append(_item_name(item))
    lines = [text(30885)]
    for library in sorted(grouped, key=lambda key: (name(key).casefold(), key)):
        lines.append("")
        if len(grouped) > 1:
            lines.append("[B]%s[/B]" % name(library))
        lines.extend(sorted(grouped[library], key=str.casefold))
    return "\n".join(lines)


def _item_name(item: dict[str, Any]) -> str:
    title = (item.get("Name") or "").strip() or str(item.get("Id") or "")
    show = (item.get("SeriesName") or "").strip()
    return "%s \u2014 %s" % (show, title) if show else title


def off_features(features: dict[str, bool], text: Text) -> list[str]:
    """The labels of the features this Kodi lacks, in the table's order."""
    return [
        text(label)
        for name, label in capabilities.FEATURE_LABELS
        if not features.get(name, False)
    ]


def migration() -> str:
    """The way out of ``EarlierLibrary``, for a text viewer.

    Clean databases left with the SQL build, so the way out goes back to it
    through Kodi's Versions button, which keeps that version pinned until the
    newest is picked. A Kodi 23 is offered no such version, which leaves the
    last line.
    """
    steps = enumerate((30890, 30891, 30892), start=1)
    return "\n".join(
        (
            settings.localized(30889),
            "",
            *("%d. %s" % (number, settings.localized(text)) for number, text in steps),
            "",
            settings.localized(30893),
            MIGRATION_PAGE,
        )
    )


def show(store: "Store", logged_out: bool = False) -> None:
    """The report, as a dialog to read: one row per fact, the value in the
    row's own label (a select dialog's plain layout has no second field).

    It is what the catalogue and the sync's document hold at the moment it
    is opened. The first row reads them again, which is how a running import
    is watched, and it is the row under the cursor: under a cursor on the
    last row the list scrolls the sync's own line off the top as soon as
    there are more rows than fit.

    The first row, the last and the "Kodi cannot import" row are the only
    ones that do anything. A select dialog closes on whichever row is
    picked, so a fact that was picked is shown again as it was, the cursor
    on it; Back is what closes it. The row for what this Kodi lacks carries
    a count, and picking it opens the names, one feature a line, in a text
    viewer; picking the count of what Kodi cannot import opens what it
    counts the same way. Both lists are read with the rows they explain, so a pass
    that moves either while the report is open cannot make the text
    disagree with the row.

    With sync off over what the SQL build left there is nothing to report,
    and the catalogue would refuse to be read: the button opens the way out.
    """
    document = read(store.namespace)
    if document.get("earlier"):
        xbmcgui.Dialog().textviewer(document["state"], migration())
        return
    heading = "%s \u2014 %s" % (settings.localized(30859), settings.localized(30862))
    lines: list[str] = []
    off: list[str] = []
    unfiled = ""
    entries: list[tuple[str, str, dict[str, Any]]] = []
    cursor = 0
    while True:
        if cursor == 0:
            table = capabilities.table()
            off = off_features(table, settings.localized)
            found = snapshot(
                store, metadata.scanner_format({n for n, on in table.items() if on})
            )
            lines = rows(
                read(store.namespace),
                found,
                progress.stage,
                progress.label,
                features=table,
            )
            unfiled = unfiled_row(found, progress.stage)
            entries = store.unfiled(counted(found)) if unfiled else []
        choices: list[Union[str, xbmcgui.ListItem]] = [xbmc.getLocalizedString(184)]
        if logged_out:
            choices.append(settings.localized(30896))
        choices.extend(lines)
        cursor = xbmcgui.Dialog().select(heading, choices, preselect=cursor)
        if cursor < 0:
            return
        if off and cursor == len(choices) - 1:
            xbmcgui.Dialog().textviewer(settings.localized(30876), "\n".join(off))
        elif unfiled and choices[cursor] == unfiled:
            xbmcgui.Dialog().textviewer(
                progress.stage(30868),
                unfiled_report(entries, found, progress.stage),
            )


def _moment(stamp: float, clock: Clock) -> str:
    """A time as the dialog shows it; empty for none, and for a number no
    calendar has (the clock raises for one far enough out)."""
    if not stamp:
        return ""
    try:
        return time.strftime("%Y-%m-%d %H:%M", clock(stamp))
    except (OverflowError, OSError, ValueError):
        return ""


def _number(value: int) -> str:
    return f"{int(value):,}"

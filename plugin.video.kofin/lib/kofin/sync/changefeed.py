"""Change-feed providers: the companion-plugin tier ladder as code.

One internal record type covers every tier; each enhancement keys off
**field presence, not tier identity**. ``KofinFeed`` speaks the
KofinSyncQueue v1 protocol (typed records, query-time Etags, retention
cutoff in-band); ``LegacyFeed`` adapts the official KodiSyncQueue
``GetItems`` shape into sparse records — optional fields stay ``None`` and
the tier-1 features simply never engage.
"""

import calendar
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from collections.abc import Sequence

from kofin.core.http import HttpError, JellyfinError
from kofin.core.log import Logger

LOG = Logger(__name__)

JsonDict = dict[str, Any]

TIER_KOFIN = "kofin"
TIER_OFFICIAL = "official"
TIER_NONE = "none"

# The one protocol version this client speaks.
PROTOCOL_VERSION = 1

WATERMARK_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# The official KodiSyncQueue exclude list does not know playlists.
LEGACY_TYPES = ("movies", "tvshows", "boxsets", "musicvideos", "music")


@dataclass
class ChangeRecord:
    """One change-queue entry; ``library_ids`` is ``None`` where the feed does not say."""

    id: str
    status: str  # "Added" | "Updated" | "Removed"
    library_ids: Optional[list[str]] = None  # owning libraries; None = unknown


@dataclass
class Envelope:
    """Response envelope facts the watermark/retention logic consumes."""

    server_time: Optional[int] = None  # unix seconds
    retention_cutoff: Optional[int] = None  # unix seconds; None/0 = no cutoff


@dataclass
class ChangeSet:
    records: list[ChangeRecord] = field(default_factory=list)
    userdata: list[JsonDict] = field(default_factory=list)
    envelope: Envelope = field(default_factory=Envelope)


def _iso_to_unix(value: Optional[str]) -> Optional[int]:
    """Parse a server ISO timestamp to unix seconds; None when unusable.

    DateTime.MinValue-style sentinels (year 1) mean "no value" and map to
    None rather than a negative epoch.
    """
    if not value:
        return None

    try:
        parsed = time.strptime(str(value)[:19] + "Z", WATERMARK_FORMAT)
    except ValueError:
        return None

    if parsed.tm_year < 1970:
        return None

    return int(calendar.timegm(parsed))


def watermark_to_unix(watermark: str) -> int:
    """The ISO watermark setting as unix seconds; 0 = everything."""
    return _iso_to_unix(watermark) or 0


def unix_to_watermark(unix: int) -> str:
    return datetime.fromtimestamp(unix, tz=timezone.utc).strftime(WATERMARK_FORMAT)


def _as_int(value: Any) -> Optional[int]:
    try:
        result = int(value)
    except (TypeError, ValueError):
        return None

    return result or None


def parse_record(raw: JsonDict) -> Optional[ChangeRecord]:
    """A KofinSyncQueue response record → ChangeRecord; None when unusable."""
    item_id = raw.get("Id")
    status = raw.get("Status")

    if not item_id or status not in ("Added", "Updated", "Removed"):
        LOG.warning("dropping malformed change record: %s", raw)
        return None

    return ChangeRecord(
        id=str(item_id),
        status=str(status),
        library_ids=[str(x) for x in raw.get("LibraryIds") or []] or None,
    )


class KofinFeed:
    """Tier 1: the KofinSyncQueue companion (typed records, fast path)."""

    tier = TIER_KOFIN

    def __init__(self, api: Any) -> None:
        self.api = api

    def changes(
        self,
        last_sync: str,
        include: Sequence[str],
        libraries: Optional[Sequence[str]] = None,
    ) -> ChangeSet:
        # Sent unconditionally: a server that predates the parameter ignores
        # it, and one that honours it saves us the records outright.
        result = self.api.kofin_sync_queue(
            watermark_to_unix(last_sync),
            ",".join(include),
            ",".join(sorted(libraries or ())),
        )

        if not result:
            return ChangeSet()

        records = []
        for raw in result.get("Items") or []:
            record = parse_record(raw)
            if record is not None:
                records.append(record)

        return ChangeSet(
            records=records,
            userdata=list(result.get("UserData") or []),
            envelope=Envelope(
                server_time=_as_int(result.get("ServerTime")),
                retention_cutoff=_as_int(result.get("RetentionCutoff")),
            ),
        )

    def server_now(self) -> Optional[int]:
        """Server clock via the Info probe (also carries retention)."""
        return _as_int(self.api.kofin_sync_info().get("ServerTime"))


class LegacyFeed:
    """Tier 2: the official KodiSyncQueue — sparse records.

    The server clock and RetentionDateTime are sampled at query time.
    """

    tier = TIER_OFFICIAL

    def __init__(self, api: Any) -> None:
        self.api = api

    def changes(
        self,
        last_sync: str,
        include: Sequence[str],
        libraries: Optional[Sequence[str]] = None,
    ) -> ChangeSet:
        # The legacy protocol has no library dimension; its records carry no
        # library_ids, so they are kept and the ancestor walk decides.
        del libraries

        envelope = Envelope()

        try:
            server_time = self.api.server_time()
            envelope.server_time = _iso_to_unix(server_time.get("ServerDateTime"))
            envelope.retention_cutoff = _iso_to_unix(
                server_time.get("RetentionDateTime")
            )
        except JellyfinError as error:
            # The queue call below will surface a real outage; retention
            # detection just skips this cycle.
            LOG.warning("GetServerDateTime failed: %s", error)

        excluded = [x for x in LEGACY_TYPES if x not in include]
        result = self.api.sync_queue(last_sync, ",".join(excluded))

        if result is None:
            return ChangeSet(envelope=envelope)

        records = []
        for status, key in (
            ("Added", "ItemsAdded"),
            ("Updated", "ItemsUpdated"),
            ("Removed", "ItemsRemoved"),
        ):
            for item_id in result.get(key) or []:
                records.append(ChangeRecord(id=str(item_id), status=status))

        return ChangeSet(
            records=records,
            userdata=list(result.get("UserDataChanged") or []),
            envelope=envelope,
        )

    def server_now(self) -> Optional[int]:
        return _iso_to_unix(self.api.server_time().get("ServerDateTime"))


def _absent(error: JellyfinError) -> bool:
    """Whether a probe's failure says the plugin is not there: Jellyfin
    has no route for a plugin that is not installed and enabled."""
    return isinstance(error, HttpError) and error.status == 404


def detect(api: Any) -> Optional[Any]:
    """The tier ladder, best first: KofinSyncQueue → official → None.

    Only a 404 says a plugin is absent; any other failure of a probe is
    raised, since the server could not say. A KofinSyncQueue speaking an
    unknown protocol falls to tier 2.
    """
    try:
        info = api.kofin_sync_info()
    except JellyfinError as error:
        if not _absent(error):
            raise
        LOG.debug("no KofinSyncQueue companion detected (%s)", error)
    else:
        version = (
            _as_int(info.get("ProtocolVersion")) if isinstance(info, dict) else None
        )

        if version == PROTOCOL_VERSION:
            LOG.debug(
                "KofinSyncQueue companion detected (plugin %s, protocol %s)",
                info.get("PluginVersion", "?"),
                version,
            )
            return KofinFeed(api)

        LOG.warning(
            "KofinSyncQueue speaks protocol %s (this client: %s); "
            "falling back to the official companion path",
            version,
            PROTOCOL_VERSION,
        )

    try:
        api.server_time()
    except JellyfinError as error:
        if not _absent(error):
            raise
        LOG.debug("no KodiSyncQueue companion detected (%s)", error)
        return None

    return LegacyFeed(api)


def retention_overrun(last_sync: str, retention_cutoff: Optional[int]) -> bool:
    """Whether the server's queue does not reach back to our watermark.

    True means records between the watermark and the cutoff are gone, and
    only a complete enumeration brings them back. An empty watermark is a
    fresh install: nothing to overrun.
    """
    if not retention_cutoff:
        return False

    watermark = watermark_to_unix(last_sync)

    return bool(watermark) and watermark < retention_cutoff

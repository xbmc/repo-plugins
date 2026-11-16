"""Read public Kodi capabilities inside the addon; no HTTP server required.

``inspect`` is the probe the service runs at every start, and the service
writes its report to ``REPORT`` in the profile. ``table``, ``features`` and
``has`` read that report, so nothing else probes. A feature that is off is
named once, in the service log at start and in the Library status dialog,
never per item.
"""

import json
import os
from pathlib import Path
from typing import Any

import xbmc
import xbmcaddon
import xbmcgui

from kofin.core import kodirpc
from kofin.sync import private
from .contract import check
from .kinds import NAMES

REPORT = "api-capabilities.json"

# The features of requirements.json in the order the status dialog names
# them, each with the string id of its label.
FEATURE_LABELS = (
    ("season_plot", 30877),
    ("episode_tags", 30878),
    ("remove_set", 30879),
    ("video_versions", 30880),
    ("stream_flags", 30881),
    ("song_date_added", 30882),
    ("asset_clean", 30883),
    ("tempo", 30884),
)
FEATURES = tuple(name for name, _label in FEATURE_LABELS)
# Every feature on: a Kodi 23 carrying the kontell/xbmc changes.
ALL = frozenset(FEATURES)


def contract() -> dict[str, Any]:
    document: dict[str, Any] = json.loads(
        Path(__file__).with_name("requirements.json").read_text()
    )
    return document


def _python_names(contract_: dict[str, Any]) -> dict[str, set[str]]:
    """Every Python method the baseline or a feature asks about, by field."""
    wanted: dict[str, set[str]] = {}
    for field, names in contract_["python"].items():
        wanted.setdefault(field, set()).update(names)
    for probes in contract_.get("features", {}).values():
        for field, names in probes.get("python", {}).items():
            wanted.setdefault(field, set()).update(names)
    return wanted


def inspect(allow_dirty: bool = False) -> dict[str, Any]:
    contract_ = contract()
    schema = kodirpc.call(
        "JSONRPC.Introspect", {"getdescriptions": False, "getmetadata": True}
    )
    application = kodirpc.call(
        "Application.GetProperties", {"properties": ["version", "name"]}
    )
    if not isinstance(schema, dict):
        schema = {}
    capture = {
        "application": application if isinstance(application, dict) else {},
        "methods": schema.get("methods", {}),
        "types": schema.get("types", {}),
        "system_addons": {},
    }
    addons = set(contract_["system_addons"])
    for probes in contract_.get("features", {}).values():
        addons.update(probes.get("system_addons", {}))
    for name in sorted(addons):
        try:
            capture["system_addons"][name] = xbmcaddon.Addon(name).getAddonInfo(
                "version"
            )
        except Exception:
            capture["system_addons"][name] = "0"
    wanted = _python_names(contract_)
    item = xbmcgui.ListItem(offscreen=True)
    for key, tag in (
        ("python_video_methods", item.getVideoInfoTag()),
        ("python_music_methods", item.getMusicInfoTag()),
    ):
        capture[key] = {name: hasattr(tag, name) for name in wanted.get(key, ())}
    # Stream details are classes the listing constructs, not tag methods:
    # "AudioStreamDetail.setFlags" names the class and the method.
    capture["python_stream_methods"] = {
        name: hasattr(getattr(xbmc, name.split(".")[0], None), name.split(".")[1])
        for name in wanted.get("python_stream_methods", ())
    }
    report = check(capture, contract_, allow_dirty=allow_dirty)
    report.update(
        {
            "backend": "api",
            "native_sync_enabled": report["interfaces_passed"],
            "native_sync_scope": (list(NAMES) if report["interfaces_passed"] else []),
            "application": capture["application"],
        }
    )
    return report


def summary(report: dict[str, Any]) -> str:
    """One line for the service log: what is on, and what is off and why."""
    found = report.get("features") or {}
    on = [name for name in FEATURES if found.get(name) is True]
    off = [
        "%s (%s)" % (name, "; ".join(report.get("missing", {}).get(name) or ["-"]))
        for name in FEATURES
        if found.get(name) is not True
    ]
    return "on: %s; off: %s" % (", ".join(on) or "none", ", ".join(off) or "none")


def report_path() -> str:
    return os.path.join(private.addon_data_path(), REPORT)


def table() -> dict[str, bool]:
    """Every feature by name, on or off, as the last probe found this Kodi
    (``REPORT``). With no report yet, or one of another shape, every feature
    is off: the baseline is what a Kodi is until it has been asked."""
    try:
        with open(report_path(), encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, ValueError):
        document = {}
    found = document.get("features") if isinstance(document, dict) else None
    if not isinstance(found, dict):
        found = {}
    return {name: found.get(name) is True for name in FEATURES}


def features() -> frozenset[str]:
    """The names of the features this Kodi has."""
    return frozenset(name for name, on in table().items() if on)


def has(name: str) -> bool:
    return name in features()

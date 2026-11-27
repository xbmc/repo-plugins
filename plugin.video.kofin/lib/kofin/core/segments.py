"""Media-segment parsing: /MediaSegments body -> [{Type, Start, End}].

A pure parser, shared by the plugin play route's prefetch
(``plugin/play.py::prefetch_segments``) and the service's checker
(``service/segments.py``), which acts on segments.
"""

from typing import Any, Optional

from kofin.core.log import Logger

LOG = Logger(__name__)

# Overlap two segments of one type must exceed before the later one is taken
# for a second provider's opinion rather than a genuinely separate break. A
# Recap that ends exactly where the Intro begins is not a conflict.
OVERLAP_TOLERANCE = 1.0

# Jellyfin MediaSegmentType -> the per-type identity used by settings and
# labels (Introduction/Credits/Recap/Preview/Commercial).
SEGMENT_TYPES = {
    "Intro": "Introduction",
    "Outro": "Credits",
    "Recap": "Recap",
    "Preview": "Preview",
    "Commercial": "Commercial",
}


def parse_segments(response: Optional[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sorted, de-conflicted ``[{Type, Start, End}]`` (seconds) from a
    /MediaSegments body."""
    segments: list[dict[str, Any]] = []
    for item in (response or {}).get("Items") or []:
        segment_type = SEGMENT_TYPES.get(item.get("Type", ""))
        if not segment_type:
            continue
        start = float(item.get("StartTicks") or 0) / 10_000_000
        end = float(item.get("EndTicks") or 0) / 10_000_000
        if end <= start:
            continue
        segments.append({"Type": segment_type, "Start": start, "End": end})
    segments.sort(key=lambda segment: float(segment["Start"]))
    return deconflict(segments)


def deconflict(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One segment per overlapping run within a type.

    Two segment providers analysing the same library each write their own
    rows and the server hands back the union, and ``MediaSegmentDto`` drops
    ``SegmentProviderId``, so no client can attribute a segment to a
    provider. De-confliction is therefore on the times alone.

    First-by-start wins its run, rather than the union of it: over-skipping
    into content the viewer wanted is the worse failure. Within-type only,
    and only on real overlap, so three commercial breaks all survive and an
    abutting Recap/Intro pair is left alone.

    ``segments`` must already be sorted by start.
    """
    kept: list[dict[str, Any]] = []
    run_end: dict[str, float] = {}
    dropped = 0
    for segment in segments:
        segment_type = str(segment["Type"])
        previous = run_end.get(segment_type)
        if (
            previous is not None
            and float(segment["Start"]) < previous - OVERLAP_TOLERANCE
        ):
            dropped += 1
            continue
        kept.append(segment)
        run_end[segment_type] = float(segment["End"])
    if dropped:
        LOG.debug(
            "dropped %d overlapping segment(s) — more than one provider is "
            "analysing this library",
            dropped,
        )
    return kept

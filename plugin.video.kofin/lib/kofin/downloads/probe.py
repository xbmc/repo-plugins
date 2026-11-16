"""Completion probes for transcoded downloads.

A transcode states no Content-Length, and clean EOF is not proof of
completion either: when the encoder dies mid-job the server has already
answered 200 and simply stops sending, which ends the chunked response
*cleanly* — the one failure mode that leaves a truncated file looking
finished. So the file itself is measured and held against the item's
runtime.

Fragmented MP4 keeps its duration in the fragments, not the header
(``empty_moov``): each ``moof``/``traf`` carries its sample durations in
``trun``/``tfhd`` (falling back to the ``trex`` defaults), in the track's
``mdhd`` timescale. Summing them is exactly what ffprobe does for these
files, and it works on a truncated file too — which is the point. Ogg/Opus
keeps it in the last page's granule position. Both parsers stop quietly at
the first incomplete structure and report what is whole; a container neither
understands answers None and the caller treats the length as unverifiable.
"""

import os
import struct
from typing import Optional
from collections.abc import Iterator

from kofin.core.log import Logger

LOG = Logger(__name__)

# A moov/moof larger than this is not a real header box; skip rather than
# swallow gigabytes of a malformed file into memory.
_MAX_HEADER_BOX = 32 * 1024 * 1024

_TFHD_BASE_DATA_OFFSET = 0x000001
_TFHD_SAMPLE_DESCRIPTION = 0x000002
_TFHD_DEFAULT_DURATION = 0x000008
_TRUN_DATA_OFFSET = 0x000001
_TRUN_FIRST_FLAGS = 0x000004
_TRUN_SAMPLE_DURATION = 0x000100
_TRUN_SAMPLE_SIZE = 0x000200
_TRUN_SAMPLE_FLAGS = 0x000400
_TRUN_SAMPLE_CTO = 0x000800


def duration_seconds(path: str, container: str) -> Optional[float]:
    """The media duration on disk, or None when this probe cannot say."""
    kind = (container or "").lower()
    if kind in ("mp4", "m4v", "mov"):
        return fmp4_duration_seconds(path)
    if kind in ("opus", "ogg", "oga"):
        return ogg_duration_seconds(path)
    return None


def _boxes(data: bytes, start: int, end: int) -> Iterator[tuple[bytes, int, int]]:
    """(type, payload_start, payload_end) for each whole child box; a
    truncated or nonsense size ends the walk rather than raising."""
    offset = start
    while offset + 8 <= end:
        size, box_type = struct.unpack_from(">I4s", data, offset)
        header = 8
        if size == 1:
            if offset + 16 > end:
                return
            size = struct.unpack_from(">Q", data, offset + 8)[0]
            header = 16
        elif size == 0:
            size = end - offset
        if size < header or offset + size > end:
            return
        yield box_type, offset + header, offset + size
        offset += size


def _parse_moov(
    payload: bytes,
    timescales: dict[int, int],
    totals: dict[int, int],
    trex_defaults: dict[int, int],
) -> None:
    for box_type, start, end in _boxes(payload, 0, len(payload)):
        if box_type == b"trak":
            track_id = None
            timescale = 0
            duration = 0
            for child, c_start, c_end in _boxes(payload, start, end):
                if child == b"tkhd" and c_end - c_start >= 16:
                    version = payload[c_start]
                    at = c_start + (20 if version == 1 else 12)
                    if at + 4 <= c_end:
                        track_id = struct.unpack_from(">I", payload, at)[0]
                elif child == b"mdia":
                    for grand, g_start, g_end in _boxes(payload, c_start, c_end):
                        if grand == b"mdhd" and g_end - g_start >= 20:
                            version = payload[g_start]
                            at = g_start + (20 if version == 1 else 12)
                            if version == 1 and at + 12 <= g_end:
                                timescale = struct.unpack_from(">I", payload, at)[0]
                                duration = struct.unpack_from(">Q", payload, at + 4)[0]
                            elif version == 0 and at + 8 <= g_end:
                                timescale, duration = struct.unpack_from(
                                    ">II", payload, at
                                )
            if track_id is not None and timescale:
                timescales[track_id] = timescale
                # empty_moov stamps 0 here; a plain mp4 stamps the whole
                # duration. Folding it in makes the sum right either way.
                totals[track_id] = totals.get(track_id, 0) + duration
        elif box_type == b"mvex":
            for child, c_start, c_end in _boxes(payload, start, end):
                if child == b"trex" and c_end - c_start >= 16:
                    track_id, _index, default = struct.unpack_from(
                        ">III", payload, c_start + 4
                    )
                    trex_defaults[track_id] = default


def _parse_moof(
    payload: bytes, totals: dict[int, int], trex_defaults: dict[int, int]
) -> None:
    for box_type, start, end in _boxes(payload, 0, len(payload)):
        if box_type != b"traf":
            continue
        track_id = None
        default_duration = 0
        fragment_units = 0
        for child, c_start, c_end in _boxes(payload, start, end):
            if child == b"tfhd" and c_end - c_start >= 8:
                flags = int.from_bytes(payload[c_start + 1 : c_start + 4], "big")
                track_id = struct.unpack_from(">I", payload, c_start + 4)[0]
                at = c_start + 8
                if flags & _TFHD_BASE_DATA_OFFSET:
                    at += 8
                if flags & _TFHD_SAMPLE_DESCRIPTION:
                    at += 4
                if flags & _TFHD_DEFAULT_DURATION and at + 4 <= c_end:
                    default_duration = struct.unpack_from(">I", payload, at)[0]
                if not default_duration and track_id is not None:
                    default_duration = trex_defaults.get(track_id, 0)
            elif child == b"trun" and c_end - c_start >= 8:
                flags = int.from_bytes(payload[c_start + 1 : c_start + 4], "big")
                sample_count = struct.unpack_from(">I", payload, c_start + 4)[0]
                at = c_start + 8
                if flags & _TRUN_DATA_OFFSET:
                    at += 4
                if flags & _TRUN_FIRST_FLAGS:
                    at += 4
                if flags & _TRUN_SAMPLE_DURATION:
                    stride = 4 * (
                        1
                        + bool(flags & _TRUN_SAMPLE_SIZE)
                        + bool(flags & _TRUN_SAMPLE_FLAGS)
                        + bool(flags & _TRUN_SAMPLE_CTO)
                    )
                    for _ in range(sample_count):
                        if at + 4 > c_end:
                            break
                        fragment_units += struct.unpack_from(">I", payload, at)[0]
                        at += stride
                else:
                    fragment_units += sample_count * default_duration
        if track_id is not None and fragment_units:
            totals[track_id] = totals.get(track_id, 0) + fragment_units


def fmp4_duration_seconds(path: str) -> Optional[float]:
    timescales: dict[int, int] = {}
    totals: dict[int, int] = {}
    trex_defaults: dict[int, int] = {}
    try:
        with open(path, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            file_end = handle.tell()
            offset = 0
            while offset + 8 <= file_end:
                handle.seek(offset)
                header = handle.read(8)
                if len(header) < 8:
                    break
                size, box_type = struct.unpack(">I4s", header)
                header_size = 8
                if size == 1:
                    wide = handle.read(8)
                    if len(wide) < 8:
                        break
                    size = struct.unpack(">Q", wide)[0]
                    header_size = 16
                elif size == 0:
                    size = file_end - offset
                if size < header_size or offset + size > file_end:
                    # A cut-off final box — the .part a dead encoder leaves.
                    # Measure the whole fragments before it.
                    break
                if (
                    box_type in (b"moov", b"moof")
                    and size - header_size <= _MAX_HEADER_BOX
                ):
                    payload = handle.read(size - header_size)
                    if len(payload) < size - header_size:
                        break
                    if box_type == b"moov":
                        _parse_moov(payload, timescales, totals, trex_defaults)
                    else:
                        _parse_moof(payload, totals, trex_defaults)
                offset += size
    except OSError as error:
        LOG.debug("fmp4 probe failed for %s: %s", path, error)
        return None
    seconds = [
        units / timescales[track]
        for track, units in totals.items()
        if timescales.get(track)
    ]
    if not seconds:
        return None
    return max(seconds)


def ogg_duration_seconds(path: str) -> Optional[float]:
    """Duration off the last whole Ogg page's granule position.

    Opus granules count 48 kHz PCM samples whatever the encode rate
    (RFC 7845 §4); the codec pre-skip is ignored — tens of milliseconds
    against a truncation check. A page whose granule is -1 (no packet ends
    on it) walks back to the previous page.
    """
    try:
        with open(path, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            span = min(size, 65536)
            handle.seek(size - span)
            tail = handle.read(span)
    except OSError as error:
        LOG.debug("ogg probe failed for %s: %s", path, error)
        return None
    position = tail.rfind(b"OggS")
    while position != -1:
        if position + 14 <= len(tail):
            granule = int(struct.unpack_from("<q", tail, position + 6)[0])
            if granule >= 0:
                return granule / 48000.0
        position = tail.rfind(b"OggS", 0, position)
    return None

"""DASH manifests and CENC boxes, as the proxy reads and rewrites them (standard library only).

Timelines, URL templates, the Widevine pssh and key IDs of init segments and
media fragments, and the public rules of a Widevine licence.
"""

import base64
import re
from urllib.parse import urljoin

WIDEVINE_URN = "urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed"
WIDEVINE_SYSTEM_ID = bytes.fromhex("edef8ba979d64acea3c827dcd51d21ed")
# The provider's MPDs: self-closing Representation tags inside each AdaptationSet.
ADAPTATION_SET = re.compile(r"<AdaptationSet\b.*?</AdaptationSet>", re.S)
REPRESENTATION = re.compile(r"<Representation\b[^>]*/>")


def adaptation_sets(xml):
    """Return the AdaptationSets of a manifest or a period, as text."""
    return ADAPTATION_SET.findall(xml)


def representations(aset):
    """Return the Representation tags of an AdaptationSet, as text."""
    return REPRESENTATION.findall(aset)


def init_protection(data):
    """Return (base64 Widevine pssh box, default KID as UUID) of an init segment."""
    pssh = kid = None
    i = 0
    while pssh is None:
        i = data.find(b"pssh", i)
        if i < 4:
            break
        size = int.from_bytes(data[i - 4 : i], "big")
        if data[i + 8 : i + 24] == WIDEVINE_SYSTEM_ID:
            pssh = base64.b64encode(data[i - 4 : i - 4 + size]).decode()
        i += 4
    i = data.find(b"tenc")
    if i >= 4:
        kid = uuid(data[i + 12 : i + 28])
    return pssh, kid


def with_tenc_kid(data, kid):
    """Return an init segment naming this key ID (a UUID) in its tenc box; as it is without a kid or a tenc box.

    tenc (ISO/IEC 23001-7): box header and version (8 bytes), 4 bytes of flags and IV size, then the 16-byte KID.
    """
    i = data.find(b"tenc")
    if not kid or i < 4:
        return data
    return data[: i + 12] + bytes.fromhex(kid.replace("-", "")) + data[i + 28 :]


def fragment_protection(data):
    """Return (base64 Widevine pssh box, KID as UUID) a media fragment overrides its track's with; (None, None) if none."""
    pssh = init_protection(data)[0]
    i = data.find(b"sgpd")
    i = data.find(b"seig", i) if i >= 0 else -1
    if not pssh or i < 0:
        return None, None
    # sgpd v1 (ISO/IEC 14496-12): grouping_type "seig", default_length, entry_count (4 bytes each), then
    # the seig entry (ISO/IEC 23001-7): reserved, crypt/skip byte, isProtected, IV size, 16-byte KID.
    return pssh, uuid(data[i + 16 : i + 32])


# Seconds behind the live edge ISA starts a live stream (its live_delay; its default and least: 16).
# Not a cure for the sound starting up to ~3 s off the picture on some channels until a rebuffer a few
# seconds in (Kodi's SyncStream log): 24 changed nothing there (measured 2026-11-02).
LIVE_DELAY = 16
# Seconds of a live window kept where the programme allows no rewinding ("ts"):
# a little over the live delay, so it still starts at its usual point.
NO_TIMESHIFT_WINDOW = LIVE_DELAY + 4


def parse_timeline(template, default_scale=None):
    """Return (timescale, [(start, duration), ...]) of a SegmentTemplate's timeline; (None, []) without a usable one.

    Only the first <S> need carry a start time (audio has many entries of
    slightly different durations), so the whole timeline is walked.
    """
    scale = re.search(r'\btimescale="(\d+)"', template)
    scale = int(scale.group(1)) if scale else default_scale
    entries = re.findall(r"<S\b[^>]*/>", template)
    if not scale or not entries:
        return None, []
    segments, now = [], 0
    for s in entries:
        start, duration, repeat = (re.search(r'\b%s="(-?\d+)"' % k, s) for k in ("t", "d", "r"))
        if not duration:
            return None, []
        now = int(start.group(1)) if start else now
        for _ in range(1 + (int(repeat.group(1)) if repeat and int(repeat.group(1)) > 0 else 0)):
            segments.append((now, int(duration.group(1))))
            now += int(duration.group(1))
    return scale, segments


def timeline_xml(segments):
    """Return a SegmentTimeline for (start, duration) segments, runs of equal durations folded into r."""
    entries, i = [], 0
    while i < len(segments):
        j = i
        while j + 1 < len(segments) and segments[j + 1][1] == segments[i][1]:
            j += 1
        start = 't="%d" ' % segments[i][0] if i == 0 else ""
        entries.append('<S %sd="%d"%s/>' % (start, segments[i][1], ' r="%d"' % (j - i) if j > i else ""))
        i = j + 1
    return "<SegmentTimeline>%s</SegmentTimeline>" % "".join(entries)


def align_live_edges(mpd, window=None):
    """Cut every SegmentTimeline back to the newest segment all tracks already have.

    The origin publishes audio a moment before the matching video, and ISA
    starts each live track a fixed number of segments before its own newest:
    read in that moment, the sound would start one segment (4 s) late.

    :param window: also keep only the last that many seconds (and set
        timeShiftBufferDepth): no rewinding where a programme forbids it ("ts"),
        though the manifest's window is always 15 minutes
    """
    timelines = {}
    for template in re.findall(r"<SegmentTemplate\b.*?</SegmentTemplate>", mpd, re.S):
        scale, segments = parse_timeline(template)
        if segments:
            timelines[template] = (scale, segments)
    if len(timelines) < (1 if window else 2):
        return mpd
    common_end = min((s[-1][0] + s[-1][1]) / scale for scale, s in timelines.values())
    for template, (scale, segments) in timelines.items():
        # Half a second of slack: tracks' segment boundaries differ by a few milliseconds.
        kept = [s for s in segments if (s[0] + s[1]) / scale <= common_end + 0.5]
        if window:
            kept = [s for s in kept if s[0] / scale >= common_end - window - 0.5] or kept[-1:]
        if not kept or len(kept) == len(segments):
            continue
        timeline = timeline_xml(kept)
        mpd = mpd.replace(template, re.sub(r"<SegmentTimeline>.*?</SegmentTimeline>", timeline, template, flags=re.S))
    if window:
        mpd = re.sub(r'\btimeShiftBufferDepth="[^"]*"', 'timeShiftBufferDepth="PT%dS"' % window, mpd, count=1)
    return mpd


def key_pair(pssh):
    """Return the key IDs a Widevine pssh box asks for, to compare boxes that differ only in their bytes.

    An init segment's box and a fragment's may name the same pair in different bytes.
    Anything unparsable compares as itself.
    """
    if not pssh:
        return None
    try:
        box = base64.b64decode(pssh, validate=True)
        offset = 28
        if box[8] == 1:  # pssh version 1 (ISO/IEC 23001-7) lists its KIDs before the data
            offset += 4 + 16 * int.from_bytes(box[28:32], "big")
        size = int.from_bytes(box[offset : offset + 4], "big")
        # Field 2 of the data (Widevine's WidevinePsshData): the key IDs.
        kids = frozenset(v for f, v in protobuf_fields(box[offset + 4 : offset + 4 + size]) if f == 2)
        return kids or pssh
    except (ValueError, IndexError):
        return pssh


def uuid(raw):
    """Format 16 raw bytes as a UUID string."""
    k = raw.hex()
    return "%s-%s-%s-%s-%s" % (k[:8], k[8:12], k[12:16], k[16:20], k[20:])


def protobuf_fields(data):
    """Yield the (field number, value) pairs of a protobuf message: ints for varints, bytes otherwise."""
    i = 0
    while i < len(data):
        key, i = varint(data, i)
        field, wire = key >> 3, key & 7
        if wire == 0:
            value, i = varint(data, i)
        elif wire == 2:
            size, i = varint(data, i)
            value, i = data[i : i + size], i + size
        elif wire in (1, 5):
            size = 8 if wire == 1 else 4
            value, i = data[i : i + size], i + size
        else:
            return
        yield field, value


def varint(data, i):
    """Read a protobuf varint at offset i.

    :return: (value, offset after it)
    """
    value = shift = 0
    while True:
        b = data[i]
        i += 1
        value |= (b & 0x7F) << shift
        shift += 7
        if b < 0x80:
            return value, i


def template_value(aset, name):
    """Return the value of the first attribute of this name in an adaptation set; None if missing."""
    found = re.search(r'\b%s="([^"]+)"' % name, aset)
    return found.group(1) if found else None


def fill(template, tag, time=None):
    """Fill a URL template's $Bandwidth$, $RepresentationID$ and $Time$ from a Representation tag."""
    bandwidth = re.search(r'bandwidth="(\d+)"', tag)
    rep_id = re.search(r'\bid="([^"]+)"', tag)
    out = template.replace("$Bandwidth$", bandwidth.group(1) if bandwidth else "").replace(
        "$RepresentationID$", rep_id.group(1) if rep_id else ""
    )
    return out.replace("$Time$", str(time)) if time is not None else out


def init_url(aset, tag, mpd_url):
    """Return an encrypted representation's init segment URL (None if it is not encrypted)."""
    init = template_value(aset, "initialization")
    if not init or WIDEVINE_URN not in aset:
        return None
    return urljoin(mpd_url, fill(init, tag))


def media_url(aset, tag, mpd_url, time):
    """Return a representation's media fragment URL for a timeline time (None without both)."""
    media = template_value(aset, "media")
    if not media or time is None or not tag:
        return None
    return urljoin(mpd_url, fill(media, tag, time))


def start_time(aset, from_start):
    """Return the time of the fragment whose key playback starts with.

    The first one when played from the beginning, else the newest but one (the
    newest may still be in the making).
    """
    template = re.search(r"<SegmentTemplate\b.*?</SegmentTemplate>", aset, re.S)
    if not template:
        return None
    segments = parse_timeline(template.group(0), default_scale=1)[1]
    if not segments:
        return None
    return segments[0][0] if from_start else segments[-2 if len(segments) > 1 else -1][0]


def smallest(tags):
    """Return the representation of the lowest bandwidth: all of a group's qualities share one key."""
    return min(tags, key=lambda t: int((re.search(r'bandwidth="(\d+)"', t) or [0, 0])[1]), default=None)


def first_at(segments, scale, seconds):
    """Return the index of the first segment starting at or after `seconds` (half a segment of slack)."""
    for i, (start, duration) in enumerate(segments):
        if (start + duration / 2) / scale >= seconds:
            return i
    return len(segments)


KEY_LEVELS = {1: "SW_SECURE_CRYPTO", 2: "SW_SECURE_DECODE", 3: "HW_SECURE_CRYPTO", 4: "HW_SECURE_DECODE", 5: "HW_SECURE_ALL"}
HDCP = {0: "none", 1: "v1", 2: "v2", 3: "v2.1", 4: "v2.2", 5: "v2.3", 0xFF: "no digital output"}


def licence_keys(content):
    """Return the content keys' public rules in a Widevine licence: id, security level, required HDCP.

    For the log: why a licensed stream may still fail to play. Field numbers as in Widevine's
    license_protocol.proto: SignedMessage.msg (2) holds a License, whose key (3) entries are
    KeyContainers: id (1), type (4), level (5), required_protection (6, its hdcp is 1).
    """
    try:
        msg = next((v for f, v in protobuf_fields(content) if f == 2), b"")
        keys = []
        for f, container in protobuf_fields(msg):
            if f != 3:
                continue
            fields = dict(protobuf_fields(container))
            if fields.get(4) != 2:  # KeyContainer type 2: CONTENT (not SIGNING, OPERATOR_SESSION, ...)
                continue
            hdcp = dict(protobuf_fields(fields[6])).get(1, 0) if isinstance(fields.get(6), bytes) else 0
            keys.append(
                "%s %s HDCP %s" % (fields.get(1, b"").hex(), KEY_LEVELS.get(fields.get(5), fields.get(5)), HDCP.get(hdcp, hdcp))
            )
        return keys
    except (IndexError, TypeError, ValueError):
        return []

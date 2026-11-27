"""Kodi TV (PVR) files for IPTV Simple: an M3U playlist, an XMLTV guide and the genre maps.

IPTV Simple's own instance that reads them is iptvsimple's.
"""

import contextlib
import gzip
import hashlib
import json
import os
import re
import time
from xml.sax.saxutils import escape
from xml.sax.saxutils import quoteattr

from resources.lib.data import guidedata
from resources.lib.data import infopages
from resources.lib.util import atomicfile

INSTANCE_NAME = "Simple GO"
OUT_DIR = "iptv"
PLAYLIST = "channels.m3u"
# IPTV Simple reads gzipped XMLTV; a few days of guide shrink to a tenth.
GUIDE = "epg.xml.gz"
# What the files were last written from (see export): an export with nothing new rewrites nothing.
STATE = "export.json"
# Each guide block's XMLTV, kept between exports (see _Guide).
XML_DIR = "xml"
# Each guide block's info page keys, kept between exports (see _block_keys).
KEYS = "block-keys.json"
# Raised when _programme writes a programme otherwise, so kept blocks are made again.
XML_VERSION = 2


class Cancelled(Exception):
    """Raised by an export's progress callback to stop it; the previous files stay."""


GENRE_MAP = "genres.xml"
# Without mappings, for the "colours" setting off: a separate file, so switching changes
# genresPath and IPTV Simple restarts to read it.
GENRE_MAP_PLAIN = "genres-plain.xml"
# The files IPTV Simple reads.
OUTPUT_FILES = (GUIDE, PLAYLIST, GENRE_MAP, GENRE_MAP_PLAIN)


# Too broad to colour by when a programme has a more telling category; listed last.
BROAD_GENRES = ("Sorozatok", "Családi", "Egyéb")


def genre_map(colours=True):
    """Return IPTV Simple's genre text mapping file for guidedata.DVB_GENRES; without colours, an empty one."""
    genres = guidedata.DVB_GENRES.items() if colours else ()
    rows = "".join('  <genre genreId="0x%02X">%s</genre>\n' % (dvb, escape(text)) for text, dvb in genres)
    return '<?xml version="1.0" encoding="UTF-8"?>\n<genres>\n  <name>Simple GO</name>\n%s</genres>\n' % rows


def epg_id(channel):
    """Return the channel's ID in the playlist and the guide (tvg-id)."""
    return "simplego.%s" % channel["station_id"]


def _groups(channel):
    # IPTV Simple splits group-title on ";": the add-on's group, extra groups, then one per category.
    names = list(channel.get("groups") or []) + list(channel.get("genres") or [])
    return ";".join([INSTANCE_NAME] + [g.replace(";", ",") for g in names])


def _xmltv_time(iso):
    # "2026-10-25T17:55:00Z" -> "20261025175500 +0000"
    return re.sub(r"[-:T]", "", iso.rstrip("Z"))[:14] + " +0000"


def _catchup(channel, plugin_url):
    """Return the M3U catch-up attributes.

    catchup-days -1: IPTV Simple offers only programmes with a catchup-id, which
    only those the provider lets watch back get (see guidedata.watchable_back).
    """
    if not channel.get("catchup"):
        return ""
    # "stream", not "media": IPTV Simple takes an #EXTINF line containing "media=" for a recording.
    source = plugin_url(action="play", id=channel["id"], stream=channel["media_id"], programme="{catchup-id}")
    # urlencode would turn the braces of IPTV Simple's placeholder into %7B..%7D.
    source = source.replace("%7Bcatchup-id%7D", "{catchup-id}")
    return ' catchup="default" catchup-days="-1" catchup-source="%s"' % source


def export(
    client,
    channels,
    profile_dir,
    plugin_url,
    past_days=1,
    days_ahead=7,
    info_types=(),
    block_dir=None,
    progress=None,
    stats=None,
    pause=None,
):
    """Write the playlist and guide.

    :param block_dir: where the guide blocks are kept between uses (see provider.guide)
    :param info_types: the programme types ("movie", "series", "other") to add the
        cast to, from the programmes' info pages (see infopages.info_for)
    :param progress: progress(stage, done, total), stage "guide", "info", "build" or "compress";
        raising (Cancelled) stops the export before any file is written
    :param stats: a dict filled with each stage's duration and fetch counts
    :param pause: pause() is called before each block and info page, from any of the export's threads;
        it may wait (see util.pluginbusy)
    :return: (channel count, programme count)
    """
    out = os.path.join(profile_dir, OUT_DIR)
    os.makedirs(out, exist_ok=True)
    stats = {} if stats is None else stats
    report = progress or (lambda stage, done=0, total=0: None)

    # Monotonic: stands still while the device sleeps (wall clock once logged 11 h "writing").
    started = time.monotonic()
    by_station = {c["station_id"]: c for c in channels}
    fetched, block_counts = client.epg_blocks(
        past_days=past_days,
        days_ahead=days_ahead,
        stations=set(by_station),
        cache_dir=block_dir,
        progress=lambda done, total: report("guide", done, total),
        pause=pause,
    )
    # (date, offset, whether the first, GuideBlock)
    blocks = [(date, offset, i == 0, block) for i, (date, offset, block) in enumerate(fetched)]
    stats.update(block_counts, guide=time.monotonic() - started)
    started = time.monotonic()
    pages, block_keys = {}, None
    if info_types:
        block_keys = _block_keys(blocks, by_station, info_types, out, stats)
        wanted = {_key(k) for _, own in block_keys for k in own}
        pages = infopages.info_for(client, wanted, out, lambda done, total: report("info", done, total), stats, pause)
    stats["info"] = time.monotonic() - started

    report("build", 0, len(blocks))
    started = time.monotonic()
    guide = _Guide(out, by_station, pages, info_types)
    keys = [guide.key(*block, cast_keys=block_keys[i][0] if block_keys else ()) for i, block in enumerate(blocks)]
    # Unchanged input: no rewrite, so IPTV Simple has nothing new to read.
    key = _digest([channels, keys, plugin_url(action="play", id="", media="")])
    last = _read_state(out)
    if last.get("key") == key and all(os.path.exists(os.path.join(out, name)) for name in OUTPUT_FILES):
        stats.update(write=time.monotonic() - started, unchanged=True)
        return len(channels), last["programmes"]
    count = 0
    # Written block by block: a week's guide is never all in memory at once.
    with atomicfile.writer(os.path.join(out, GUIDE)) as add:
        head = ['<?xml version="1.0" encoding="UTF-8"?>', '<tv generator-info-name="plugin.video.simplego">']
        add("\n".join(head + [_channel_xml(c) for c in channels]) + "\n")
        for done, (block, block_key) in enumerate(zip(blocks, keys, strict=True), 1):
            if pause:
                pause()
            part = guide.xml(block, block_key)
            if part:
                add(part + "\n")
                count += part.count("<programme ")
            report("build", done, len(blocks))
        add("</tv>\n")
        guide.drop_unused()
        stats["rendered"] = guide.rendered
        report("compress")
    atomicfile.write(os.path.join(out, PLAYLIST), _playlist(channels, plugin_url))
    atomicfile.write(os.path.join(out, GENRE_MAP), genre_map())
    atomicfile.write(os.path.join(out, GENRE_MAP_PLAIN), genre_map(colours=False))
    atomicfile.write(os.path.join(out, STATE), json.dumps({"key": key, "programmes": count}))
    stats["write"] = time.monotonic() - started
    return len(channels), count


def _own(date, offset, first, block, by_station):
    """Return a GuideBlock's programmes of our channels that start in it (or before it, in the first block).

    A programme spanning two blocks is in both: it goes in the guide once, with the block it starts in.
    """
    since = "%sT%02d:00:00Z" % (date, offset) if date and not first else ""
    return {s: [p for p in progs if p["start_time"] >= since] for s, progs in block.channels().items() if s in by_station}


def _block_keys(blocks, by_station, info_types, out, stats):
    """Return each block's info page keys: [all its programmes', its own cast-typed programmes'].

    With the cast, an export read every block twice for these (the pages wanted, then each block's
    key): most of an export with nothing new, 23 s against 0.6 s without the cast on a TV stick.
    Kept (KEYS) by what they come of, so an unchanged block is not read at all.
    """
    path = os.path.join(out, KEYS)
    kept = atomicfile.read_json(path, {})
    context = _digest([sorted(by_station), sorted(info_types)])
    found, names, read = {}, [], 0
    for date, offset, first, block in blocks:
        name = _digest([block.digest(), date, offset, first, context])
        names.append(name)
        if name not in kept:
            every = (p for progs in block.channels().values() for p in progs)
            own = (p for progs in _own(date, offset, first, block, by_station).values() for p in progs)
            kept[name] = [
                sorted({"/".join(k) for p in every for k in infopages.keys_of(p)}),
                sorted({"/".join(k) for p in own if guidedata.kind(p) in info_types for k in infopages.keys_of(p)}),
            ]
            read += 1
        found[name] = kept[name]
    if read or len(found) != len(kept):
        # Only the blocks of this export: the file does not grow.
        atomicfile.write(path, json.dumps(found))
    stats["read"] = read
    return [found[name] for name in names]


def _key(text):
    """Return an info page key ("series/123") as infopages has it: ("series", "123")."""
    return tuple(text.split("/", 1))


class _Guide:
    """The XMLTV of the guide's blocks, each kept (XML_DIR) and made again only when its inputs changed.

    Inputs: its programmes, the channels' ids, colours and catch-up, and the cast.
    Without the cast, a block's key is made without reading its programmes.
    """

    def __init__(self, out, by_station, pages, info_types):
        self.dir = os.path.join(out, XML_DIR)
        os.makedirs(self.dir, exist_ok=True)
        self.by_station = by_station
        self.pages = pages
        self.info_types = sorted(info_types)
        self.context = _digest({s: self._channel(s) for s in by_station})
        self.used = set()
        self.rendered = 0

    def key(self, date, offset, first, block, cast_keys=()):
        """Return a digest of all a block's XML is made of.

        :param cast_keys: the info page keys of the block's programmes (see _block_keys)
        """
        cast = sorted([k, self.pages[_key(k)]] for k in cast_keys if _key(k) in self.pages)
        return _digest([XML_VERSION, date, offset, first, block.digest(), self.context, cast, self.info_types])

    def xml(self, block, key):
        """Return a block's XMLTV programmes: the kept ones if its key is the same, else made and kept."""
        date, offset = block[:2]
        name = ("%s-%02d" % (date, offset) if date else "all") + ".%s.xml.gz" % key[:20]
        self.used.add(name)
        path = os.path.join(self.dir, name)
        try:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                return f.read()
        except (OSError, EOFError):
            pass
        programmes = _own(*block, self.by_station)
        text = "\n".join(self._programme(s, p) for s, progs in programmes.items() for p in progs)
        atomicfile.write(path, text)
        self.rendered += 1
        return text

    def drop_unused(self):
        """Remove the kept XML of blocks this guide no longer has (or had made otherwise)."""
        for name in os.listdir(self.dir):
            if name not in self.used:
                with contextlib.suppress(OSError):
                    os.remove(os.path.join(self.dir, name))

    def _channel(self, station):
        channel = self.by_station[station]
        fallback = next((g for g in channel.get("genres") or [] if g in guidedata.DVB_GENRES), None)
        return [epg_id(channel), fallback, bool(channel.get("catchup"))]

    def _programme(self, station, p):
        channel_id, fallback, catchup = self._channel(station)
        info = infopages.programme_credits(p, self.pages) if guidedata.kind(p) in self.info_types else None
        return _programme(channel_id, p, fallback, info, catchup=catchup)


def _channel_xml(c):
    return "  <channel id=%s><display-name>%s</display-name><icon src=%s/></channel>" % (
        quoteattr(epg_id(c)),
        escape(c["name"]),
        quoteattr(c["logo"]),
    )


def _playlist(channels, plugin_url):
    """Return the M3U playlist of the channels."""
    m3u = ["#EXTM3U"]
    # IPTV Simple orders groups as it meets them: an #EXTGRP line puts ours and the extra ones
    # first; the empty one after it stops it applying to channels.
    extra = list(dict.fromkeys(g for c in channels for g in c.get("groups") or []))
    m3u += ["#EXTGRP:%s" % ";".join([INSTANCE_NAME] + [g.replace(";", ",") for g in extra]), "#EXTGRP:"]
    for c in channels:
        m3u.append(
            '#EXTINF:-1 tvg-id="%s" tvg-chno="%s" tvg-name="%s" tvg-logo="%s" group-title="%s"%s%s,%s'
            % (
                epg_id(c),
                c["number"],
                c["name"].replace('"', "'"),
                c["logo"],
                _groups(c).replace('"', "'"),
                ' radio="true"' if c["radio"] else "",
                _catchup(c, plugin_url),
                c["name"],
            )
        )
        m3u.append(plugin_url(action="play", id=c["id"], media=c["media_id"]))
    return "\n".join(m3u) + "\n"


def _digest(content):
    return hashlib.sha1(json.dumps(content, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _read_state(out):
    """Return what the last export wrote the files from ({"key", "programmes"}); {} if not known."""
    return atomicfile.read_json(os.path.join(out, STATE), {})


def _programme(channel_id, p, channel_genre=None, info=None, catchup=False):
    # The guide API puts the programme title in "description"; "episode_name"
    # is the episode title and "full_description" the synopsis.
    parts = [
        '  <programme start="%s" stop="%s" channel=%s%s>'
        % (
            _xmltv_time(p["start_time"]),
            _xmltv_time(p["end_time"]),
            quoteattr(channel_id),
            " catchup-id=%s" % quoteattr(guidedata.param(p)) if catchup and guidedata.watchable_back(p) else "",
        )
    ]
    parts.append('<title lang="hu">%s</title>' % escape(p.get("description") or ""))
    if p.get("episode_name"):
        parts.append('<sub-title lang="hu">%s</sub-title>' % escape(p["episode_name"]))
    plot = (p.get("full_description") or "").strip()
    if plot:
        parts.append('<desc lang="hu">%s</desc>' % escape(plot))
    parts.append(_credits(info or {}))
    # Trakt reads a Kodi TV channel's programme as it reads a played item.
    year = guidedata.played_year(p)
    if year:
        parts.append("<date>%d</date>" % year)
    parts.extend('<category lang="hu">%s</category>' % escape(name) for name in _categories(p, channel_genre))
    parts.append(_episode(p))
    image = guidedata.image(p)
    if image:
        parts.append("<icon src=%s/>" % quoteattr(image))
    # The number the rating says ("18+" is 18 here; the lock counts it as guidedata.ADULT_AGE).
    rating = guidedata.rating_number(p.get("ratings"))
    if rating is not None:
        parts.append("<rating><value>%d</value></rating>" % rating)
    parts.append("</programme>")
    return "".join(parts)


def _credits(info):
    """Return a programme's XMLTV credits (directors, actors, writers); "" without any."""
    roles = ("director", "actor", "writer")
    names = "".join("<%s>%s</%s>" % (role, escape(name), role) for role in roles for name in info.get(role, []))
    return "<credits>%s</credits>" % names if names else ""


def _categories(p, channel_genre=None):
    """Return a programme's category names in the order IPTV Simple should see them.

    IPTV Simple colours by the first category it can map, so broad ones go last;
    with none it knows, the channel's category gives the colour.
    """
    names = sorted((g["name"] for g in p.get("genres") or [] if g.get("name")), key=lambda n: n in BROAD_GENRES)
    if channel_genre and not any(n in guidedata.DVB_GENRES and n not in BROAD_GENRES for n in names):
        names.insert(0, channel_genre)
    return names


def _episode(p):
    """Return a programme's XMLTV episode number (season and episode from 0); "" without one."""
    numbers = guidedata.season_episode(p)
    if not numbers:
        return ""
    return '<episode-num system="xmltv_ns">%d.%d.</episode-num>' % (numbers[0] - 1, numbers[1] - 1)

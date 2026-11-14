"""The manifest as ISA gets it: each track's keys declared, key changes found.

The proxy writes each representation's pssh and default_KID (from its init segment) into the MPD,
so ISA asks for every key pair a channel uses; segments still come straight from the CDN through an
inserted <BaseURL>.

Where the fragments use another key than their init segment names, the proxy declares the
fragments' key and serves such init segments with that key ID (see licproxy): ISA goes by the
init segment.

Keys changing while a live channel plays: ISA keeps decrypting with the key it started with (no
version implements key rotation), and the picture stops. Each refresh reads the newest fragments'
keys; a change is noted for the player to restart there (see _watch_live_keys and keyfollower).
"""

import re
import time
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
from urllib.parse import urljoin

from resources.lib.net import transport
from resources.lib.stream import dash
from resources.lib.stream import keychanges

# A rewritten manifest, and where its rewrite's time went (for the log: which step to make faster, if any).
Rewritten = namedtuple("Rewritten", "mpd steps")
# Seconds an HTTP request to the provider or the CDN may take.
HTTP_TIMEOUT = 20
# A fragment's head (moof, naming its key) lies within its first this many bytes: its media data is not needed.
FRAGMENT_HEAD_BYTES = 65536


class ManifestRewriter:
    """One stream's manifest as ISA gets it: its keys read, declared, and their changes found.

    Not thread-safe: the proxy rewrites one manifest at a time (see licproxy).

    :param http: the HTTP session for the CDN (a net.transport.Session)
    :param proxy_base: proxy_base() is the proxy's address (known once it serves), for init segments
        served with their real key ID
    :param log: log(msg), where problems go
    :param debug: debug(msg), where timings and findings go (else log)
    :param audio_langs: preferred audio languages (ISO 639-2), best first; Hungarian is the fallback
    :param from_start: played from the start of its timeline: the first fragment's keys count, not the live edge's
    :param no_timeshift: asked at every live refresh: True while the programme allows no rewinding
    :param change_hint: found_changes from an earlier stream of this programme: no search again
    :param part: which key's part this stream plays (see _key_changes); else the one start_at falls in
    :param start_at: seconds into the stream playback starts at (None: 0), to pick the part
    :param label: the channel's name, for the log
    """

    def __init__(
        self,
        http,
        proxy_base,
        log,
        debug=None,
        audio_langs=(),
        from_start=False,
        no_timeshift=None,
        change_hint=None,
        part=None,
        start_at=None,
        label=None,
    ):
        self._http = http
        self._proxy_base = proxy_base
        self._log = log
        self._debug = debug or log
        self._audio_langs = [lang for lang in audio_langs if lang] + ["hun"]
        self._from_start = from_start
        self._no_timeshift = no_timeshift
        self._change_hint = change_hint
        self._part = part
        self._start_at = start_at
        self._label = label
        self._protection = {}  # init segment URL -> (pssh, kid, init's own kid if rotated)
        self._changes = None  # see _key_changes
        self._tracks_logged = False  # see _log_tracks
        self._live_last = None  # see _watch_live_keys
        self._live_noticed = None
        self.found_changes = None  # see _key_changes
        self.change_times = ()
        self.live_changes = ()  # see _watch_live_keys

    def has_keys(self):
        """Return whether any track's keys were read yet (the first rewrite has run)."""
        return bool(self._protection)

    def init_kid(self, url):
        """Return the key ID declared for this init segment; None if unknown."""
        return self._protection.get(url, (None, None, None))[1]

    def rewrite(self, mpd, mpd_url):
        """Return the manifest as ISA gets it (each track's keys declared, through the proxy where needed), timed.

        What it finds of the keys stays known (change_times, live_changes, found_changes).
        """
        began = time.time()
        asets = dash.adaptation_sets(mpd)
        static = dash.is_static(mpd)
        from_start = self._from_start or static
        self._read_keys(asets, mpd_url, from_start)
        keys = self._part_keys(asets, mpd_url) if static else self._protection
        if not static:
            self._watch_live_keys(asets, mpd_url)
        read = time.time()
        for period in re.findall(r"<Period\b.*?</Period>", mpd, re.S):
            mpd = mpd.replace(period, self._render(period, mpd_url, keys))
        rendered = time.time()
        if not static:
            live = not from_start and self._no_timeshift and self._no_timeshift()
            mpd = dash.align_live_edges(mpd, dash.NO_TIMESHIFT_WINDOW if live else None)
        if "<BaseURL>" not in mpd:
            mpd = mpd.replace("<Period", "<BaseURL>%s</BaseURL><Period" % urljoin(mpd_url, "."), 1)
        # Where a rewrite's time goes, for the log (see licproxy): which step to make faster, if any.
        steps = "keys %.0f ms, render %.0f ms, edges %.0f ms" % (
            (read - began) * 1000,
            (rendered - read) * 1000,
            (time.time() - rendered) * 1000,
        )
        return Rewritten(mpd, steps)

    def _read_keys(self, asets, mpd_url, from_start):
        """Read the key of every track not read yet: its init segment's, or its fragments' where they rotate.

        All fetched in parallel; the fragment only from each group's smallest quality (they share a key).
        """
        wanted = {}
        for aset in asets:
            tags = dash.representations(aset)
            smallest = dash.smallest(tags)
            for tag in tags:
                url = dash.init_url(aset, tag, mpd_url)
                if url and url not in self._protection:
                    wanted[url] = dash.media_url(aset, smallest, mpd_url, dash.start_time(aset, from_start))
        if not wanted:
            return
        tasks = [("init", url) for url in wanted] + [("fragment", url) for url in set(wanted.values()) if url]
        with ThreadPoolExecutor(max_workers=8) as pool:
            found = dict(zip(tasks, pool.map(self._fetch_keys, tasks), strict=True))
        for url, segment in wanted.items():
            if segment and not from_start:  # the fragment a live refresh would read first (see _watch_live_keys)
                self._live_last = dict(self._live_last or {}, **{url: segment})
            pssh, kid = found[("init", url)]
            rotated = found.get(("fragment", segment), (None, None))
            if rotated[1] and rotated[1] != kid:
                self._debug("rotated key: %s -> %s" % (kid, rotated[1]))
                self._protection[url] = (rotated[0], rotated[1], kid)
            elif pssh:
                self._protection[url] = (pssh, kid, None)

    def _watch_live_keys(self, asets, mpd_url):
        """Note where a live stream's fragments stop using the key declared for their track (see live_changes).

        At each refresh, the video's newest fragment but one (the newest may still be in the making) is
        read once, from its smallest quality (all share a key): a range request per segment. The video
        only: the restart reads every track's new key anyway.
        live_changes gets (when noticed, seconds before the live edge, track, old kid, new kid).
        """
        last, noticed = self._live_last or {}, self._live_noticed or {}
        checks = []
        for aset in asets:
            if not dash.is_video(aset) or dash.is_trick_mode(aset):
                continue
            tag = dash.smallest(dash.representations(aset))
            init = dash.init_url(aset, tag, mpd_url) if tag else None
            declared = self._protection.get(init) if init else None
            start = dash.start_time(aset, False)
            if not declared or not declared[1] or start is None:
                continue
            url = dash.media_url(aset, tag, mpd_url, start)
            if last.get(init) != url:
                checks.append((aset, init, declared[1], start, url))
        if not checks:
            return
        with ThreadPoolExecutor(max_workers=len(checks)) as pool:
            kids = list(pool.map(self._live_kid, [url for *_, url in checks]))
        for (aset, init, declared, start, url), kid in zip(checks, kids, strict=True):
            if kid is None:
                continue  # unread: tried again at the next refresh
            last[init] = url
            if kid in (declared, noticed.get(init)):
                continue
            noticed[init] = kid
            template = dash.SEGMENT_TEMPLATE.search(aset).group(0)
            scale, segments = dash.parse_timeline(template, default_scale=1)  # as start_time read it
            edge = (segments[-1][0] + segments[-1][1]) / scale
            track = (re.search(r'\bcontentType="(\w+)"', aset) or [None, "?"])[1]
            self.live_changes = tuple(self.live_changes) + ((time.time(), edge - start / scale, track, declared, kid),)
            self._debug(
                "live key change on %s (%s) at %s: %s -> %s, %.0f s before the live edge"
                % (self._label or "?", track, time.strftime("%H:%M:%S"), declared, kid, edge - start / scale)
            )
        self._live_last, self._live_noticed = last, noticed

    def _live_kid(self, url):
        """Return the key ID a live fragment names (its track's own if none); None if it cannot be read."""
        try:
            return self._fragment_key(url)[1] or ""
        except keychanges.Unknown as e:
            self._debug("live key check failed: %s" % e)
            return None

    def _part_keys(self, asets, mpd_url):
        """Return the keys a static manifest declares: those of the part it plays (see _key_changes)."""
        if self._changes is None:
            self._changes = self._key_changes(asets, mpd_url)
        if not self._changes:
            return self._protection
        if self._part is None:
            self._part = self.part_of(self._start_at or 0)
        self._part = min(self._part, len(self._changes))
        return self._changes[self._part - 1][2] if self._part else self._protection

    def _render(self, period, mpd_url, protection):
        """Return a period with each representation's pssh and default_KID, and only the tracks of one key pair.

        :param protection: init segment URL -> (pssh, kid, the init's own kid where the fragments use another)
        """

        def rep_protection(aset, tag):
            url = dash.init_url(aset, tag, mpd_url)
            return protection.get(url, (None, None, None)) if url else (None, None, None)

        asets = dash.adaptation_sets(period)
        main_pair = self._main_pair(asets, rep_protection)
        self._log_tracks(asets, rep_protection, main_pair)
        return dash.ADAPTATION_SET.sub(lambda m: self._protect(m.group(0), mpd_url, rep_protection, main_pair), period)

    def _main_pair(self, asets, rep_protection):
        """Return the key pair the tracks played must share; None to keep them all.

        Android ISA keeps one DRM session for all streams (HasLicenseKey always
        says yes), so only one pair's tracks can play. The others are dropped: left in, they stall
        playback or feed encrypted audio to the decoder (which crashed Kodi).
        The pair is the preferred audio language's, else the first audio's.
        """

        def audio_rank(aset):
            lang = re.search(r'\blang="([^"]+)"', aset)
            lang = lang.group(1).lower() if lang else ""
            return self._audio_langs.index(lang) if lang in self._audio_langs else len(self._audio_langs)

        main_pair = None
        for aset in sorted((a for a in asets if dash.is_audio(a)), key=audio_rank):
            for tag in dash.representations(aset):
                main_pair = main_pair or dash.key_pair(rep_protection(aset, tag)[0])
            if main_pair:
                break
        video_tags = [(a, t) for a in asets if dash.is_video(a) for t in dash.representations(a)]
        # No video track in the audio's pair: better some picture than none.
        if main_pair and not any(dash.key_pair(rep_protection(a, t)[0]) == main_pair for a, t in video_tags):
            return None
        return main_pair

    def _log_tracks(self, asets, rep_protection, main_pair):
        """Log the offered video tracks once per stream (size, bit rate, key pair, dropped), and the subtitles."""
        if self._tracks_logged:
            return
        self._tracks_logged = True
        pairs, tracks = {}, []
        for aset in (a for a in asets if dash.is_video(a) and not dash.is_trick_mode(a)):
            for tag in dash.representations(aset):
                size = re.search(r'\bwidth="(\d+)".*?\bheight="(\d+)"', tag) or re.search(r'\bheight="(\d+)"', tag)
                rate = re.search(r'\bbandwidth="(\d+)"', tag)
                pair = dash.key_pair(rep_protection(aset, tag)[0])
                name = pairs.setdefault(pair, "pair %d" % (len(pairs) + 1)) if pair else "clear"
                kept = not main_pair or pair == main_pair or not pair
                tracks.append(
                    "%s %.1f Mbit/s %s%s"
                    % (
                        "x".join(size.groups()) if size else "?",
                        int(rate.group(1)) / 1e6 if rate else 0,
                        name,
                        "" if kept else " (dropped)",
                    )
                )
        self._debug("video tracks offered: %s" % "; ".join(tracks))
        texts = []
        for aset in (a for a in asets if dash.is_text(a)):
            lang = re.search(r'\blang="([^"]+)"', aset)
            codecs = re.search(r'\bcodecs="([^"]+)"', aset)
            role = re.search(r'<Role\b[^>]*\bvalue="([^"]+)"', aset)
            texts.append(" ".join(m.group(1) for m in (lang, codecs, role) if m) or "?")
        self._debug("subtitle tracks offered: %s" % ("; ".join(texts) or "none"))

    def _protect(self, aset, mpd_url, rep_protection, main_pair):
        """Return an AdaptationSet with its representations' keys, those of other pairs dropped ("" if none left).

        Where keys rotate, its init segments go through /init with the fragments' key ID.
        """
        dropped = []

        def representation(m):
            tag = m.group(0)
            pssh, kid, _ = rep_protection(aset, tag)
            if not pssh or not kid:
                return tag
            if main_pair and dash.key_pair(pssh) != main_pair:
                dropped.append(tag)
                return ""
            return (
                tag[:-2].rstrip() + '><ContentProtection schemeIdUri="urn:mpeg:dash:mp4protection:2011" '
                'value="cenc" cenc:default_KID="%s"/><ContentProtection schemeIdUri="%s" value="Widevine">'
                "<cenc:pssh>%s</cenc:pssh></ContentProtection></Representation>" % (kid, dash.WIDEVINE_URN, pssh)
            )

        out = dash.REPRESENTATION.sub(representation, aset)
        if dropped and "<Representation" not in out:
            return ""
        tags = dash.representations(aset)
        rotated = [rep_protection(aset, t) for t in tags if rep_protection(aset, t)[2]]
        if rotated:
            init = re.search(r'initialization="([^"]+)"', out).group(1)
            proxied = "%s/init?u=%s&amp;k=%s" % (self._proxy_base(), quote(urljoin(mpd_url, init), safe="$"), rotated[0][1])
            out = out.replace('initialization="%s"' % init, 'initialization="%s"' % proxied)
        return out

    # ------------------------------------------------------- key changes

    def _key_changes(self, asets, mpd_url):
        """Find where a static manifest's fragments change key (a programme watched back across a rotation).

        ISA licenses one pair per stream and would decrypt past the change with
        the old key. Periods per key don't help: on Android Kodi cannot open the
        next period's video decoder while the old one is open ("InstanceGuard
        locked"). So the programme plays in parts, one stream each: the manifest
        stays whole (length, seeking) but declares its part's keys, and playback
        restarts with the next part's keys just before a change (see keyfollower).

        :return: [] for none, else [(media time in seconds, {aset: first segment of
            the new key}, {init URL: (pssh, kid, init kid)})] per change, in order
        """
        track_groups = keychanges.groups(asets, mpd_url)
        if not track_groups:
            return []
        keys = {}

        def key(group, n):
            url = dash.media_url(group.aset, group.tag, mpd_url, group.segments[n][0])
            if url not in keys:
                keys[url] = self._fragment_key(url)
            return keys[url]

        started = time.time()
        try:
            found = keychanges.find(track_groups, key, self._change_hint)
        except keychanges.Unknown as e:
            self._log("key change search failed, playing it in one part: %s" % e)
            return []
        if any(len(f) != len(found[0]) for f in found):
            self._log("tracks change keys at different counts (%s): playing it in one part" % [len(f) for f in found])
            return []
        out = [self._change(track_groups, found, k, key, mpd_url) for k in range(len(found[0]))]
        if None in out:
            self._log("a key change to no key of its own: playing it in one part")
            return []
        video = track_groups[keychanges.video_index(track_groups)]
        first = video.segments[0][0] / video.scale
        self.found_changes = found
        self.change_times = tuple(seconds - first for seconds, _, _ in out)
        for offset, (_, _, protection) in zip(self.change_times, out, strict=True):
            kids = ", ".join(sorted({p[1] for p in protection.values()}))
            self._debug("key change %.0f s into the stream: %s" % (offset, kids))
        if out:
            self._debug("key changes found in %.2fs, %d fragment heads read" % (time.time() - started, len(keys)))
        return out

    def _change(self, track_groups, found, k, key, mpd_url):
        """Return the k-th key change as _key_changes lists it (None if a track names no key there)."""
        video = track_groups[keychanges.video_index(track_groups)]
        index = found[keychanges.video_index(track_groups)][k]
        seconds = video.segments[index][0] / video.scale
        starts, protection = {}, {}
        for group, indexes in zip(track_groups, found, strict=True):
            starts[group.aset] = indexes[k]
            pssh, kid = key(group, indexes[k])
            if not kid:
                return None
            for tag in dash.representations(group.aset):
                url = dash.init_url(group.aset, tag, mpd_url)
                init_kid = self._protection.get(url) or (None, None, None)
                init_kid = init_kid[2] or init_kid[1]
                protection[url] = (pssh, kid, init_kid if kid != init_kid else None)
        return seconds, starts, protection

    def _fragment_key(self, url):
        """Return (pssh, kid) a fragment names for itself, (None, None) if none (its track's own key).

        :raises keychanges.Unknown: the fragment cannot be read
        """
        try:
            r = self._http.get(url, headers={"Range": "bytes=0-%d" % (FRAGMENT_HEAD_BYTES - 1)}, timeout=HTTP_TIMEOUT)
            data = r.content
        except transport.Error as e:
            raise keychanges.Unknown("%s: %s" % (url.rsplit("/", 1)[-1], e)) from e
        if r.status_code not in (200, 206):
            raise keychanges.Unknown("%s: HTTP %s" % (url.rsplit("/", 1)[-1], r.status_code))
        return dash.fragment_protection(data)

    @property
    def part(self):
        """Return which key's part of the programme the manifest declares the keys of (0: the first)."""
        return self._part or 0

    def part_of(self, seconds):
        """Return the part a position (seconds into the stream) falls in."""
        return sum(1 for t in self.change_times if seconds >= t)

    def _fetch_keys(self, task):
        """Return (pssh, kid) of an init segment, or the key a media fragment overrides it with."""
        kind, url = task
        try:
            if kind == "init":
                return dash.init_protection(self._http.get(url, timeout=HTTP_TIMEOUT).content)
            return self._fragment_key(url)
        except (transport.Error, keychanges.Unknown) as e:
            self._log("%s segment fetch failed: %s" % (kind, e))
            return None, None

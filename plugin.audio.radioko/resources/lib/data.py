# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-or-later
"""radioko.com's public lists, kept for a few hours in the add-on's own folder.

The add-on reads radioko.com's lists (the countries, each country's stations), plays the stations' own streams and
counts a play at Radio Browser as its terms ask: those are the only hosts it talks to. No Kodi module is used here,
so the tests run this file as it is.
"""
import gzip
import html
import json
import os
import re
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen

ORIGIN = 'https://radioko.com'
# Radio Browser's terms ask directories to count a play: the one request to anyone but radioko and the stations.
RB_CLICK = 'https://all.api.radio-browser.info/json/url/'
# The relay's signed address (an http stream reaches the add-on only as this https address).
RELAY = re.compile(r'/s/[A-Za-z0-9_-]{8,4000}\.[A-Za-z0-9_-]{43}$')
LOGO = re.compile(r'^/logos/[0-9a-f]{20}\.webp$')
LOGO_HASH = re.compile(r'^[0-9a-f]{20}$')
UUID = re.compile(r'^[0-9a-f-]{36}$')
EDITION = re.compile(r'^[a-z]{2}$')
CC = re.compile(r'^[A-Z]{2}$')
# Never a station from Turkey (radioko lists none; nothing here ever adds one).
NO_COUNTRY = 'TR'

HOUR = 3600
TTL_INDEX = 6 * HOUR        # the countries
TTL_LIST = 6 * HOUR         # a country's stations
TTL_FALLBACK = 1 * HOUR     # the featured list in place of the full one, and a full one that is not there yet
TTL_WORLD = 12 * HOUR       # every country's search index (some 3.7 MB)
TIMEOUT = 20


class Unreachable(Exception):
    """radioko.com did not answer, and nothing kept from an earlier answer can stand in."""


class NotFound(Exception):
    pass


def user_agent(version):
    return 'radioko-kodi/%s (+https://radioko.com)' % version


def fetch(url, ua, accept='application/json', timeout=TIMEOUT):
    """GET url -> (bytes, final url). NotFound on 404 or 410; any other failure: Unreachable."""
    req = Request(url, headers={'User-Agent': ua, 'Accept': accept, 'Accept-Encoding': 'gzip'})
    try:
        res = urlopen(req, timeout=timeout)
        try:
            body = res.read()
            if (res.headers.get('Content-Encoding') or '').lower() == 'gzip':
                body = gzip.decompress(body)
            return body, res.geturl()
        finally:
            res.close()
    except HTTPError as e:
        if e.code in (404, 410):
            raise NotFound(url)
        raise Unreachable('%s: HTTP %s' % (url, e.code))
    except (URLError, OSError, ValueError) as e:
        raise Unreachable('%s: %s' % (url, e))


def is_https(url):
    try:
        u = urlparse(url)
        return u.scheme == 'https' and bool(u.hostname)
    except (ValueError, AttributeError):
        return False


def relayed(url):
    return isinstance(url, str) and url.startswith('https://') and bool(RELAY.search(url))


def candidates(st):
    """A station's streams in the order they are tried: its own, then its other qualities (alts), each address once.
    HTTPS only: an http stream reaches the add-on only as the relay's signed https address; anything else is left out.
    fb: the relay's copy of a stream on a port other than 443."""
    seen = set()
    out = []
    alts = st.get('alts') if isinstance(st.get('alts'), list) else []
    for c in [st] + alts:
        if not isinstance(c, dict):
            continue
        url = c.get('stream')
        if not isinstance(url, str) or not is_https(url) or url in seen:
            continue
        seen.add(url)
        item = {'stream': url, 'hls': 1 if c.get('hls') else 0}
        if isinstance(c.get('f'), str):
            item['f'] = c['f']
        if relayed(c.get('fb')):
            item['fb'] = c['fb']
        out.append(item)
    return out


def other_port(c):
    """A direct https stream on a port other than 443: networks that let only 80 and 443 out drop it."""
    if c.get('hls') or relayed(c['stream']):
        return False
    try:
        return urlparse(c['stream']).port not in (None, 443)
    except ValueError:
        return False


def _slug_ok(slug):
    if not isinstance(slug, str) or len(slug) < 4 or len(slug) > 123 or slug[2] != '/' or not EDITION.match(slug[:2]):
        return False
    return all(ch == '-' or unicodedata.category(ch)[0] in 'LMN' for ch in slug[3:])


def clean_station(x):
    """What the add-on keeps of a station from radioko's lists, field by field; None: not a station."""
    if not isinstance(x, dict) or not _slug_ok(x.get('slug')) or x['slug'][:2] == NO_COUNTRY.lower():
        return None
    name = x.get('name')
    if not isinstance(name, str) or not name.strip():
        return None
    streams = candidates(x)
    if not streams:
        return None
    st = {'slug': x['slug'], 'name': name.strip()[:120], 'streams': streams,
          'uuid': x['uuid'] if isinstance(x.get('uuid'), str) and UUID.match(x['uuid']) else '',
          'logo': x['logo'] if isinstance(x.get('logo'), str) and LOGO.match(x['logo']) else '',
          'm': x['m'][:200] if isinstance(x.get('m'), str) else '',
          'also': x['also'][:200] if isinstance(x.get('also'), str) else ''}
    if isinstance(x.get('geo'), str) and CC.match(x['geo']):
        st['geo'] = x['geo']
    return st


def logo_url(logo):
    """Only logos radioko hosts: '/logos/<hash>.webp' or the bare hash of a search row."""
    if isinstance(logo, str) and LOGO.match(logo):
        return ORIGIN + logo
    if isinstance(logo, str) and LOGO_HASH.match(logo):
        return '%s/logos/%s.webp' % (ORIGIN, logo)
    return ''


def counts_click(uuid):
    """A Radio Browser record (a station of radioko's own registry has a version-7 id Radio Browser does not know)."""
    return bool(uuid) and UUID.match(uuid) is not None and uuid[14] != '7'


def click_url(uuid):
    return RB_CLICK + uuid if counts_click(uuid) else ''


def page_url(slug):
    return '%s/%s/' % (ORIGIN, quote(slug, safe='/-'))


_PLAY_TAG = re.compile(r'<[^>]*\bdata-play="([^"]*)"[^>]*>')
_STATION_ATTR = re.compile(r'\bdata-station="([^"]*)"')
_REFRESH = re.compile(r'<meta[^>]+http-equiv="refresh"[^>]+content="[^"]*url=/([a-z]{2}/[^/"\s]+)/', re.I)


def station_from_page(body, slug):
    """A station page's player data (the button that plays it), or ('moved', slug) for a page that sends to another."""
    text = body.decode('utf-8', 'replace')
    for m in _PLAY_TAG.finditer(text):
        if html.unescape(m.group(1)) != slug:
            continue
        data = _STATION_ATTR.search(m.group(0))
        if not data:
            continue
        try:
            return clean_station(json.loads(html.unescape(data.group(1))))
        except ValueError:
            return None
    moved = _REFRESH.search(text)
    if moved:
        return ('moved', unquote(moved.group(1)))
    return None


class Store(object):
    """radioko's lists, each kept in cache_dir for a few hours; a stale copy stands in when radioko.com is unreachable."""

    def __init__(self, cache_dir, version='1.0.0', get=fetch, clock=time.time, log=None):
        self.dir = cache_dir
        self.ua = user_agent(version)
        self.get = get
        self.clock = clock
        self.log = log or (lambda msg: None)
        self._mem = {}

    # ---- the cache ----
    def _path(self, name):
        return os.path.join(self.dir, name)

    def _age(self, name):
        try:
            return self.clock() - os.path.getmtime(self._path(name))
        except OSError:
            return None

    def _read(self, name):
        try:
            with open(self._path(name), 'rb') as f:
                return json.loads(f.read().decode('utf-8'))
        except (OSError, ValueError):
            return None

    def _write(self, name, body):
        try:
            if not os.path.isdir(self.dir):
                os.makedirs(self.dir)
            tmp = self._path(name + '.tmp')
            with open(tmp, 'wb') as f:
                f.write(body)
            os.replace(tmp, self._path(name))
        except OSError as e:
            self.log('cache write %s: %s' % (name, e))

    def _drop(self, name):
        try:
            os.remove(self._path(name))
        except OSError:
            pass

    def _fresh(self, name, ttl):
        age = self._age(name)
        return age is not None and 0 <= age < ttl

    def _load(self, name, path, ttl, valid):
        """The file at radioko.com/<path>, from the cache while fresh. NotFound passes through; on any other failure a
        stale copy stands in, else Unreachable."""
        if name in self._mem:
            return self._mem[name]
        if self._fresh(name, ttl):
            data = self._read(name)
            if data is not None and valid(data):
                self._mem[name] = data
                return data
        try:
            body, _ = self.get(ORIGIN + path, self.ua)
            data = json.loads(body.decode('utf-8'))
            if not valid(data):
                raise Unreachable('%s: not the expected list' % path)
            self._write(name, body)
        except (Unreachable, ValueError) as e:
            data = self._read(name)
            if data is None or not valid(data):
                raise Unreachable(str(e))
            self.log('%s: using the copy kept earlier (%s)' % (path, e))
        self._mem[name] = data
        return data

    # ---- the countries ----
    def editions(self):
        """{'langs': [...], 'editions': [{'p', 'cc', 'names': {lang: name}}]} in radioko's order, Turkey never."""
        def valid(d):
            return isinstance(d, dict) and isinstance(d.get('editions'), list) and isinstance(d.get('names'), dict)
        raw = self._load('editions.json', '/ext/editions.json', TTL_INDEX, valid)
        langs = [x for x in raw.get('langs') or [] if isinstance(x, str)]
        out = []
        for i, e in enumerate(raw['editions']):
            if not isinstance(e, dict) or not EDITION.match(str(e.get('p'))) or not CC.match(str(e.get('cc'))):
                continue
            if e['cc'] == NO_COUNTRY or e['p'] == NO_COUNTRY.lower():
                continue
            names = {}
            for lang, row in raw['names'].items():
                if isinstance(row, list) and i < len(row) and isinstance(row[i], str) and row[i].strip():
                    names[lang] = row[i].strip()
            out.append({'p': e['p'], 'cc': e['cc'], 'n': e.get('n') if isinstance(e.get('n'), int) else 0,
                        'names': names})
        return {'langs': langs or ['en'], 'editions': out, 'built': raw.get('built', '')}

    def edition(self, p):
        for e in self.editions()['editions']:
            if e['p'] == p:
                return e
        return None

    # ---- a country's stations ----
    def stations(self, p):
        """The edition's stations in radioko's order: every playable one (/ext/all/<p>.json) where radioko publishes it,
        else its featured ones (/ext/<p>.json)."""
        if not EDITION.match(p or '') or p == NO_COUNTRY.lower():
            return []
        key = 'stations:' + p
        if key in self._mem:
            return self._mem[key]

        def valid(d):
            return isinstance(d, dict) and isinstance(d.get('stations'), list)
        full, top, missing = 'all-%s.json' % p, 'top-%s.json' % p, 'all-%s.missing' % p
        data = None
        if not self._fresh(missing, TTL_FALLBACK):
            try:
                data = self._load(full, '/ext/all/%s.json' % p, TTL_LIST, valid)
                self._drop(missing)
            except NotFound:
                self._write(missing, b'')
                self._drop(full)
            except Unreachable as e:
                self.log('/ext/all/%s.json: %s' % (p, e))
        if data is None:
            try:
                data = self._load(top, '/ext/%s.json' % p, TTL_FALLBACK if self._fresh(missing, TTL_FALLBACK) else TTL_LIST, valid)
            except NotFound:
                data = {'stations': []}
        seen = set()
        out = []
        for x in data['stations']:
            st = clean_station(x)
            if st and st['slug'][:2] == p and st['slug'] not in seen:
                seen.add(st['slug'])
                out.append(st)
        self._mem[key] = out
        return out

    def station(self, slug):
        """A station by its address on radioko ('de/swr3'): from its country's list, else from its own page there."""
        if not _slug_ok(slug):
            return None
        for st in self.stations(slug[:2]):
            if st['slug'] == slug:
                return st
        for _ in range(2):
            try:
                body, final = self.get(page_url(slug), self.ua, accept='text/html')
            except NotFound:
                return None
            path = unquote(urlparse(final).path).strip('/')
            found = station_from_page(body, path if _slug_ok(path) else slug)
            if isinstance(found, tuple):
                slug = found[1]
                continue
            return found
        return None

    # ---- every country's search index ----
    def world(self):
        """Every country's stations for the search: [(edition, [slug, name, meta, logo hash, also?]), ...]."""
        def valid(d):
            return isinstance(d, list)
        raw = self._load('search-world.json', '/search.json', TTL_WORLD, valid)
        out = []
        for row in raw:
            if not isinstance(row, list) or len(row) < 3 or not isinstance(row[0], str) or not isinstance(row[1], str):
                continue
            ed, _, rest = row[0].partition('/')
            if not EDITION.match(ed) or ed == NO_COUNTRY.lower() or not rest:
                continue
            out.append((ed, [rest, row[1], row[2] if isinstance(row[2], str) else '',
                             row[3] if len(row) > 3 and isinstance(row[3], str) else '',
                             row[4] if len(row) > 4 and isinstance(row[4], str) else '']))
        return out

    def world_cached(self):
        return self._fresh('search-world.json', TTL_WORLD)

    def click(self, uuid):
        """Count a play at Radio Browser, as its terms ask (fire and forget)."""
        url = click_url(uuid)
        if not url:
            return False
        try:
            self.get(url, self.ua, timeout=5)
            return True
        except (Unreachable, NotFound):
            return False

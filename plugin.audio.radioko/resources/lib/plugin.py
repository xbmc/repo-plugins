# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-or-later
"""radioko for Kodi: the countries, each country's stations in radioko's order, search, and play."""
import json
import os
import re
import time
from urllib.parse import parse_qsl, urlencode

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from . import data
from . import search as finder

# The add-on's own words (resources/language/*/strings.po).
S = {'search_all': 30000, 'search_label': 30001, 'none': 30002, 'error': 30003, 'unreachable': 30004,
     'loading_all': 30005, 'pick': 30006, 'geo': 30007, 'search': 30008}
# Kodi's own words.
CORE = {'country': 574, 'next': 33078, 'automatic': 36588}
PAGE = 300          # stations per page of a country (the first page: its featured ones)
MAX_HITS = 100      # search results shown
WATCH = 30          # seconds the add-on waits for a stream to start before it leaves the player alone
SEP = u' · '   # " · ", as radioko writes it
# The measured format ("f" in radioko's lists) -> the type Kodi is told, so it opens the stream without asking first.
MIME = {'mp3': 'audio/mpeg', 'mp2': 'audio/mpeg', 'aac': 'audio/aac', 'he': 'audio/aac', 'hev2': 'audio/aac',
        'xhe': 'audio/aac', 'ogg-vorbis': 'audio/ogg', 'ogg-opus': 'audio/ogg', 'ogg-flac': 'audio/ogg', 'ogg': 'audio/ogg',
        'flac': 'audio/flac', 'opus': 'audio/mp4', 'ac3': 'audio/mp4', 'ec3': 'audio/mp4'}
HLS_MIME = 'application/vnd.apple.mpegurl'
# xHE-AAC: Kodi's FFmpeg does not decode it yet; such a stream is tried after the station's others.
LATE_FORMATS = ('xhe',)


# Kodi's regions (Settings > Interface > Regional, the names its language packs give them) -> the country, checked by
# hand against the Omega language packs' langinfo.xml ("(12h)" and the like left off). A region that is not one
# country (Central Europe, Middle East) is not in it.
REGIONS = {
    'Andorra': 'AD', 'Argentina': 'AR', 'Armenia': 'AM', 'Australia': 'AU', 'Azerbaijan': 'AZ', 'Beijing': 'CN',
    'Belarus': 'BY', 'Belgien': 'BE', 'Belgique': 'BE', 'Bosna i Hercegovina - puni prikaz': 'BA',
    'Bosna i Hercegovina - skra\u0107eni prikaz': 'BA', 'Brazil': 'BR', 'Budapest, Hungary': 'HU', 'Bulgaria': 'BG',
    'Burma': 'MM', 'CRO': 'HR', 'CZ': 'CZ', 'Canada': 'CA', 'Canarias': 'ES', 'Catalunya': 'ES',
    'Citt\u00e0 del Vaticano': 'VA', 'Cork': 'IE', 'Debrecen, Hungary': 'HU', 'Deutschland': 'DE', 'Dublin': 'IE',
    'Espa\u00f1a': 'ES', 'Ethiopia': 'ET', 'Finland': 'FI', 'France': 'FR', 'Galway': 'IE', 'IS': 'IS', 'India': 'IN',
    'Iran': 'IR', 'Ireland': 'IE', 'Israel': 'IL', 'Italia': 'IT', 'Japan': 'JP', 'Korea': 'KR',
    'La Coruna, Galicia': 'ES', 'Liechtenstein': 'LI', 'Limerick': 'IE', 'Luxembourg': 'LU', 'Luxemburg': 'LU',
    'Malta': 'MT', 'Mexico': 'MX', 'Mongolia': 'MN', 'NL': 'NL', 'Nagykanizsa, Hungary': 'HU', 'New Zealand': 'NZ',
    'Norway': 'NO', 'Pecs/Pogany, Hungary': 'HU', 'Philippines': 'PH', 'Polska': 'PL', 'Portugal': 'PT',
    'Principaut\u00e9 de Monaco': 'MC', 'Republica Moldova': 'MD', 'Riga, Latvia': 'LV', 'Rom\u00e2nia': 'RO',
    'Russia': 'RU', 'Santiago, Galicia': 'ES', 'Sardigna': 'IT', 'Schweiz': 'CH', 'Silesia': 'PL',
    'Skopje, Macedonia': 'MK', 'Slovenija': 'SI', 'Slovensko': 'SK', 'South Africa': 'ZA',
    'Srbija - puni prikaz': 'RS', 'Srbija - skra\u0107eni prikaz': 'RS', 'Suisse': 'CH', 'Svizzera': 'CH',
    'Sweden': 'SE', 'S\u00fcdtirol': 'IT', 'Tajikistan': 'TJ', 'Tallinn, Estonia': 'EE', 'Thailand': 'TH',
    'Tirana, Albania': 'AL', 'UK': 'GB', 'USA': 'US', 'Ukraine': 'UA', 'Uzbekistan': 'UZ', 'Vietnam': 'VN',
    'Waterford': 'IE', '\u00d6sterreich': 'AT', '\u0395\u03bb\u03bb\u03ac\u03b4\u03b1': 'GR',
    '\u039a\u03cd\u03c0\u03c1\u03bf\u03c2': 'CY',
    '\u0421\u0440\u0431\u0438\u0458\u0430 - \u043f\u0443\u043d\u0438 \u043f\u0440\u0438\u043a\u0430\u0437': 'RS',
    '\u0421\u0440\u0431\u0438\u0458\u0430 - \u0441\u043a\u0440\u0430\u045b\u0435\u043d\u0438 \u043f\u0440\u0438\u043a\u0430\u0437': 'RS',
    '\u53f0\u5317': 'TW'}


def site_lang(kodi_language, iso, english, langs):
    """Kodi's interface language -> one of radioko's page languages ('resource.language.zh_tw' -> 'zh-Hant'); else 'en'."""
    code = (kodi_language or '').lower().replace('resource.language.', '')
    base = code.replace('@', '_').split('_')[0] if code else (iso or '').lower().split('-')[0]
    if base == 'zh':
        traditional = code in ('zh_tw', 'zh_hk', 'zh_mo') or (not code and 'traditional' in (english or '').lower())
        if traditional and 'zh-Hant' in langs:
            return 'zh-Hant'
        return 'zh' if 'zh' in langs else 'en'
    if base in ('no', 'nn', 'nb'):
        base = 'nb'
    return base if base in langs else 'en'


def region_code(tag):
    """Kodi's language with its region ('en-us') -> the region ('US'), or '' (Kodi 21 gives 'en-')."""
    parts = (tag or '').replace('_', '-').split('-')
    if len(parts) >= 2 and len(parts[-1]) == 2 and parts[-1].isalpha():
        return parts[-1].upper()
    return ''


def region_country(name):
    """Kodi's region by its name ('USA (12h)', 'Deutschland') -> the country ('US', 'DE'), or ''."""
    return REGIONS.get(re.sub(r'\s*\([^)]*\)\s*$', '', (name or '').strip()), '')


def tries_of(streams):
    """The addresses tried in order: each stream (xHE-AAC last), and after a stream on another port the relay's copy."""
    ordered = [c for c in streams if c.get('f') not in LATE_FORMATS] + [c for c in streams if c.get('f') in LATE_FORMATS]
    out = []
    for c in ordered:
        out.append({'url': c['stream'], 'hls': c['hls'], 'f': c.get('f', '')})
        if c.get('fb') and data.other_port(c):
            out.append({'url': c['fb'], 'hls': c['hls'], 'f': c.get('f', '')})
    return out


class Watch(xbmc.Player):
    """What became of the stream handed to Kodi: started, failed (error, or ended before it started) or stopped."""

    def __init__(self):
        super(Watch, self).__init__()
        self.event = None

    def onAVStarted(self):  # noqa: N802 (Kodi's name)
        self.event = 'started'

    def onPlayBackError(self):  # noqa: N802
        self.event = 'error'

    def onPlayBackEnded(self):  # noqa: N802
        if self.event is None:
            self.event = 'ended'

    def onPlayBackStopped(self):  # noqa: N802
        if self.event is None:
            self.event = 'stopped'


class Plugin(object):

    def __init__(self, argv):
        self.base = argv[0] if argv else 'plugin://plugin.audio.radioko/'
        try:
            self.handle = int(argv[1])
        except (IndexError, ValueError):
            self.handle = -1
        query = argv[2] if len(argv) > 2 else ''
        self.params = dict(parse_qsl(query[1:] if query.startswith('?') else query))
        self.addon = xbmcaddon.Addon()
        self.id = self.addon.getAddonInfo('id')
        self.name = self.addon.getAddonInfo('name')
        self.icon = self.addon.getAddonInfo('icon')
        self.fanart = self.addon.getAddonInfo('fanart')
        profile = xbmcvfs.translatePath(self.addon.getAddonInfo('profile'))
        self.store = data.Store(os.path.join(profile, 'cache'), self.addon.getAddonInfo('version'), log=self.log)
        self._lang = None

    # ---- small things ----
    def log(self, msg, level=xbmc.LOGDEBUG):
        xbmc.log('[%s] %s' % (self.id, msg), level)

    def s(self, key):
        return self.addon.getLocalizedString(S[key])

    def core(self, key):
        return xbmc.getLocalizedString(CORE[key])

    def notify(self, msg):
        xbmcgui.Dialog().notification(self.name, msg, self.icon, 5000, False)

    def url(self, **kw):
        return '%s?%s' % (self.base, urlencode(kw))

    @staticmethod
    def setting_value(setting):
        """One of Kodi's own settings (its interface language, its region), read through JSON-RPC."""
        try:
            res = json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'Settings.GetSettingValue',
                                                             'params': {'setting': setting}})))
            value = res.get('result', {}).get('value', '')
            return value if isinstance(value, str) else ''
        except (ValueError, TypeError, AttributeError):
            return ''

    def lang(self, langs):
        if self._lang is None:
            kodi_language = self.setting_value('locale.language')
            self._lang = site_lang(kodi_language, xbmc.getLanguage(xbmc.ISO_639_1), xbmc.getLanguage(xbmc.ENGLISH_NAME), langs)
        return self._lang

    def country_name(self, edition, lang):
        names = edition['names']
        return names.get(lang) or names.get('en') or edition['cc']

    def preferred(self, editions):
        """The country shown first: the one chosen in the settings, else the region set in Kodi (when radioko has it)."""
        chosen = self.addon.getSetting('default_country')
        if chosen and any(e['p'] == chosen for e in editions):
            return chosen
        cc = region_country(self.setting_value('locale.country'))
        if not cc:
            try:
                cc = region_code(xbmc.getLanguage(xbmc.ISO_639_1, True))
            except (TypeError, RuntimeError):
                cc = ''
        for e in editions:
            if e['cc'] == cc:
                return e['p']
        return ''

    def folder(self, label, top=False, bottom=False):
        li = xbmcgui.ListItem(label=label, offscreen=True)
        li.setArt({'thumb': self.icon, 'icon': self.icon, 'fanart': self.fanart})
        if top or bottom:
            li.setProperty('SpecialSort', 'top' if top else 'bottom')
        return li

    def station_item(self, name, meta, logo, path=None):
        li = xbmcgui.ListItem(label=name, label2=meta, path=path or '', offscreen=True)
        art = data.logo_url(logo) or self.icon
        li.setArt({'thumb': art, 'icon': art, 'fanart': self.fanart})
        tag = li.getMusicInfoTag()
        tag.setMediaType('song')
        tag.setTitle(name)
        if meta:
            tag.setGenres([meta])
            tag.setComment(meta)
        return li

    def end(self, ok=True, content=None, category=None, sorts=(), cache=True):
        if self.handle < 0:
            return
        if ok:
            if category:
                xbmcplugin.setPluginCategory(self.handle, category)
            if content:
                xbmcplugin.setContent(self.handle, content)
            for method in sorts:
                xbmcplugin.addSortMethod(self.handle, method)
        xbmcplugin.endOfDirectory(self.handle, succeeded=ok, cacheToDisc=cache)

    # ---- routes ----
    def run(self):
        action = self.params.get('action', '')
        try:
            if action == 'country':
                try:
                    page = max(1, int(self.params.get('page', '1')))
                except ValueError:
                    page = 1
                self.country(self.params.get('p', ''), page)
            elif action == 'search':
                self.search(self.params.get('p', ''))
            elif action == 'play':
                self.play(self.params.get('slug', ''))
            elif action == 'choose_country':
                self.choose_country()
            else:
                self.root()
        except data.Unreachable as e:
            self.log('radioko.com unreachable: %s' % e, xbmc.LOGWARNING)
            self.notify(self.s('unreachable'))
            if action == 'play':
                self.resolve_none()
            elif action != 'choose_country':
                self.end(False)

    def root(self):
        index = self.store.editions()
        lang = self.lang(index['langs'])
        first = self.preferred(index['editions'])
        items = []
        for e in index['editions']:
            li = self.folder(self.country_name(e, lang), top=e['p'] == first)
            items.append((self.url(action='country', p=e['p']), li, True))
        items.append((self.url(action='search'), self.folder(self.s('search_all'), top=True), True))
        xbmcplugin.addDirectoryItems(self.handle, items, len(items))
        self.end(sorts=(xbmcplugin.SORT_METHOD_LABEL, xbmcplugin.SORT_METHOD_UNSORTED))

    def country(self, p, page):
        edition = self.store.edition(p)
        if not edition:
            self.notify(self.s('error'))
            self.end(False)
            return
        lang = self.lang(self.store.editions()['langs'])
        stations = self.store.stations(p)
        items = []
        if page == 1:
            items.append((self.url(action='search', p=p), self.folder(self.s('search'), top=True), True))
        for st in stations[(page - 1) * PAGE:page * PAGE]:
            items.append(self.station_entry(st))
        if page * PAGE < len(stations):
            items.append((self.url(action='country', p=p, page=page + 1), self.folder(self.core('next'), bottom=True), True))
        xbmcplugin.addDirectoryItems(self.handle, items, len(items))
        self.end(content='songs', category=self.country_name(edition, lang),
                 sorts=(xbmcplugin.SORT_METHOD_UNSORTED, xbmcplugin.SORT_METHOD_LABEL))

    def station_entry(self, st):
        li = self.station_item(st['name'], st['m'], st['logo'])
        return self.url(action='play', slug=st['slug']), self.playable(li), False

    @staticmethod
    def playable(li):
        li.setProperty('IsPlayable', 'true')
        return li

    def search(self, p):
        keyboard = xbmc.Keyboard('', self.s('search_label'))
        keyboard.doModal()
        q = keyboard.getText().strip() if keyboard.isConfirmed() else ''
        if not q:
            self.end(False)
            return
        index = self.store.editions()
        lang = self.lang(index['langs'])
        names = dict((e['p'], self.country_name(e, lang)) for e in index['editions'])
        items = []
        if p:
            stations = self.store.stations(p)
            rows = [(p, [st['slug'][3:], st['name'], st['m'], '', st['also']]) for st in stations]
            hits, _ = finder.search(rows, q, MAX_HITS)
            by_slug = dict((st['slug'], st) for st in stations)
            for r in hits:
                st = by_slug[r[0]]
                items.append(self.station_entry(st))
            category = names.get(p, p)
        else:
            rows = self.world_rows(index['editions'])
            hits, _ = finder.search(rows, q, MAX_HITS)
            for r in hits:
                meta = SEP.join(x for x in (names.get(r[0][:2], ''), r[2]) if x)
                items.append((self.url(action='play', slug=r[0]), self.playable(self.station_item(r[1], meta, r[3])), False))
            category = self.s('search_all')
        if not items:
            self.notify(self.s('none').replace('{q}', q))
            self.end(False)
            return
        xbmcplugin.addDirectoryItems(self.handle, items, len(items))
        self.end(content='songs', category=u'%s: %s' % (category, q), sorts=(xbmcplugin.SORT_METHOD_UNSORTED,), cache=False)

    def world_rows(self, editions):
        """Every country's index, the country shown first ahead of the others (as on radioko.com)."""
        progress = None
        if not self.store.world_cached():
            progress = xbmcgui.DialogProgressBG()
            progress.create(self.name, self.s('loading_all'))
        try:
            rows = self.store.world()
        finally:
            if progress:
                progress.close()
        first = self.preferred(editions)
        if first:
            rows = [r for r in rows if r[0] == first] + [r for r in rows if r[0] != first]
        return rows

    # ---- play ----
    def play_item(self, st, attempt):
        li = self.station_item(st['name'], st['m'], st['logo'], path=attempt['url'])
        mime = HLS_MIME if attempt['hls'] else MIME.get(attempt['f'])
        if mime:
            li.setMimeType(mime)
            li.setContentLookup(False)
        return li

    def resolve_none(self):
        if self.handle >= 0:
            xbmcplugin.setResolvedUrl(self.handle, False, xbmcgui.ListItem(offscreen=True))

    def play(self, slug):
        st = self.store.station(slug)
        if not st:
            self.notify(self.s('error'))
            self.resolve_none()
            return
        tries = tries_of(st['streams'])
        watch = Watch()
        first = self.play_item(st, tries[0])
        if self.handle >= 0:
            xbmcplugin.setResolvedUrl(self.handle, True, first)
        else:
            watch.play(tries[0]['url'], first)
        self.watch(st, tries, watch)

    def failed(self, st):
        if st.get('geo'):
            edition = None
            for e in self.store.editions()['editions']:
                if e['cc'] == st['geo']:
                    edition = e
            lang = self.lang(self.store.editions()['langs'])
            where = self.country_name(edition, lang) if edition else st['geo']
            self.notify(self.s('geo').replace('{country}', where))
        else:
            self.notify(self.s('error'))

    def watch(self, st, tries, watch):
        """Wait for the stream to start: then count the play at Radio Browser. A stream that fails hands over to the
        station's next one (its other qualities, the relay's copy); the last one failing says so."""
        monitor = xbmc.Monitor()
        urls = set(t['url'] for t in tries)
        i = 0
        since = time.time()
        while not monitor.abortRequested():
            event = watch.event
            if event == 'started':
                try:
                    now = watch.getPlayingFile()
                except RuntimeError:
                    now = ''
                counted = (not now or now in urls) and self.store.click(st['uuid'])
                self.log('%s: playing %s, play counted: %s' % (st['slug'], now or tries[i]['url'], bool(counted)))
                return
            if event == 'stopped':
                return
            if event in ('error', 'ended'):
                i += 1
                if i >= len(tries):
                    self.failed(st)
                    return
                self.log('%s: %s did not play, trying %s' % (st['slug'], tries[i - 1]['url'], tries[i]['url']))
                watch.event = None
                since = time.time()
                watch.play(tries[i]['url'], self.play_item(st, tries[i]))
            elif time.time() - since > WATCH:
                return
            if monitor.waitForAbort(0.25):
                return

    # ---- settings ----
    def choose_country(self):
        index = self.store.editions()
        lang = self.lang(index['langs'])
        editions = sorted(index['editions'], key=lambda e: finder.fold(self.country_name(e, lang)))
        labels = [self.core('automatic')] + [self.country_name(e, lang) for e in editions]
        chosen = self.addon.getSetting('default_country')
        at = 0
        for n, e in enumerate(editions):
            if e['p'] == chosen:
                at = n + 1
        picked = xbmcgui.Dialog().select(self.s('pick'), labels, preselect=at)
        if picked < 0:
            return
        if picked == 0:
            self.addon.setSetting('default_country', '')
        else:
            self.addon.setSetting('default_country', editions[picked - 1]['p'])
        self.addon.setSetting('default_country_name', labels[picked])
        xbmc.executebuiltin('Addon.OpenSettings(%s)' % self.id)

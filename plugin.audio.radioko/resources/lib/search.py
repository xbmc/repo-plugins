# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-or-later
"""The station search radioko.com and its other apps use, ported from the site's own script (site/search.js).

A query finds a station when each of its words is in the station's name, its genres and place, or what else finds it
(its name in the country's own script, the frequencies its page shows); accents and case aside, "radio" and "FM" not
needed; a frequency with its point, its comma or neither. The best matches come first, then radioko's own order.
"""
import re
import unicodedata

LATIN_FOLD = {u'ß': 'ss', u'ø': 'o', u'æ': 'ae', u'œ': 'oe', u'ł': 'l', u'đ': 'd',
              u'ð': 'd', u'þ': 'th', u'ı': 'i', u'ħ': 'h', u'ŋ': 'ng', u'ə': 'e',
              u'ǝ': 'e', u'ſ': 's', u'ŀ': 'l', u'ŧ': 't', u'ĸ': 'k', u'ƒ': 'f'}
_LATIN = re.compile(u'[' + u''.join(LATIN_FOLD) + u']')
_MARKS = re.compile(u'[̀-ͯ]')
_SPACE = re.compile(r'\s+')
_DEPOINT = re.compile(r'([0-9])[.,](?=[0-9])')
_GREEK = re.compile(u'[α-ω]')
_UNSPACED = re.compile(u'[฀-໿က-႟ក-៿぀-ヿ㐀-鿿豈-﫿]')
_BAND_AFTER = re.compile(r'^([0-9]{2,4}(?:[.,][0-9]+)?)(fm|am|mhz|khz)$')
_BAND_BEFORE = re.compile(r'^(fm|am)([0-9]{2,4}(?:[.,][0-9]+)?)$')
_DIGITS = '0123456789'
FINAL_SIGMA = u'ς'
SIGMA = u'σ'

GREEK_KEYS = {u'α': 'a', u'β': 'b', u'ψ': 'c', u'δ': 'd', u'ε': 'e', u'φ': 'f',
              u'γ': 'g', u'η': 'h', u'ι': 'i', u'ξ': 'j', u'κ': 'k', u'λ': 'l',
              u'μ': 'm', u'ν': 'n', u'ο': 'o', u'π': 'p', u'ρ': 'r', u'σ': 's',
              u'τ': 't', u'θ': 'u', u'ω': 'v', u'ς': 'w', u'χ': 'x', u'υ': 'y',
              u'ζ': 'z'}


def fold_keys(text):
    """Accents and case aside, and the Latin letters Unicode does not decompose as a plain keyboard writes them."""
    folded = _MARKS.sub('', unicodedata.normalize('NFKD', u'%s' % text)).lower()
    return _LATIN.sub(lambda m: LATIN_FOLD[m.group(0)], folded)


def fold(text):
    return fold_keys(text).replace(FINAL_SIGMA, SIGMA)


def greek_keys(text):
    """Greek letters typed with the Greek keyboard layout still on, read as the Latin keys they sit on."""
    return _GREEK.sub(lambda m: GREEK_KEYS.get(m.group(0), m.group(0)), text)


# The words any station could carry: radio, FM, AM and each language's word for radio, folded as the rows are.
BARE_WORDS = set(fold(w) for w in [
    'radio', 'radyo', 'raadio', 'radijas', 'radju', 'fm', 'am', 'mhz', 'khz', u'радио',
    u'радіо', u'радыё', u'фм',
    u'ράδιο', u'ραδιόφωνο', u'φμ',
    u'რადიო', u'ռադիո', u'רדיו',
    u'راديو', u'رادیو', u'إذاعة',
    u'اذاعة', u'ریڈیو', u'रेडियो',
    u'রেডিও', u'วิทยุ', u'ラジオ',
    u'라디오'])


def de_point(text):
    """A frequency's point or comma dropped ("94.9" -> "949")."""
    return _DEPOINT.sub(r'\1', text)


def _word_char(c):
    return bool(c) and unicodedata.category(c)[0] in 'LMN'


def _digit(c):
    return bool(c) and c in _DIGITS


def _runs(text):
    """Each run of letters, marks and digits: (start, run)."""
    out = []
    i, n = 0, len(text)
    while i < n:
        if _word_char(text[i]):
            j = i + 1
            while j < n and _word_char(text[j]):
                j += 1
            out.append((i, text[i:j]))
            i = j
        else:
            i += 1
    return out


def _words(text):
    """Runs of letters, marks and digits, each with the decimals written on to it ("90,3")."""
    out = []
    i, n = 0, len(text)
    while i < n:
        if _word_char(text[i]):
            j = i + 1
            while j < n and _word_char(text[j]):
                j += 1
            while j + 1 < n and text[j] in '.,' and _digit(text[j + 1]):
                k = j + 1
                while k < n and _digit(text[k]):
                    k += 1
                j = k
            out.append(text[i:j])
            i = j
        else:
            i += 1
    return out


def name_words(text):
    """A name's words but its radio words, a frequency one word ("ndr 90,3" -> ndr, 903)."""
    return [w for w in (de_point(x) for x in _words(text)) if w not in BARE_WORDS]


def name_lead(text):
    """The name from its first word that is not a radio word ("radio deejay" -> "deejay")."""
    for start, run in _runs(text):
        if run not in BARE_WORDS:
            return text[start:]
    return text


def _edge(text, i):
    """A word starts or ends at i: at either end, by a space or a sign, or where letters turn to digits or back;
    not inside a frequency ("96.1" holds no word "1")."""
    n = len(text)
    a = text[i - 1] if 0 < i <= n else ''
    b = text[i] if 0 <= i < n else ''
    if not a or not b:
        return True
    before = text[i - 2] if i >= 2 else ''
    after = text[i + 1] if i + 1 < n else ''
    if _digit(before) and a in '.,' and _digit(b):
        return False
    if _digit(a) and b in '.,' and _digit(after):
        return False
    return not _word_char(a) or not _word_char(b) or _digit(a) != _digit(b)


def _seek(text, word, whole=False):
    """word in text where a word starts (whole: and ends there)."""
    if word and _UNSPACED.match(word[0]):
        return word in text
    i = text.find(word)
    while i >= 0:
        j = i + len(word)
        if _edge(text, i) and (not whole or (_edge(text, j) and not _word_char(text[j] if j < len(text) else ''))):
            return True
        i = text.find(word, i + 1)
    return False


def _letters(word):
    return any(unicodedata.category(c)[0] == 'L' for c in word)


def search_row(edition, row):
    """A row of an edition's index, ready to match: [slug, name, meta, logo hash or '', also or '']."""
    slug, name, meta = row[0], row[1] or '', row[2] or ''
    logo = row[3] if len(row) > 3 and row[3] else ''
    also = row[4] if len(row) > 4 and row[4] else ''
    every = fold(u'%s %s%s' % (name, meta, u' ' + also if also else ''))
    own = fold(u'%s%s' % (name, u' ' + also if also else ''))
    n = fold(name)
    return [u'%s/%s' % (edition, slug) if edition else slug, name, meta, logo, every, n, fold(also) if also else '',
            _SPACE.sub('', every), de_point(every), own, de_point(own), _SPACE.sub('', n), name_lead(n), name_words(n),
            [w for w in name_words(fold(also)) if _letters(w)] if also else None]


def _word_in(r, w, keyed):
    """3: where a word of the name (or also) starts; 2: where a word starts elsewhere; 1: inside a word; 0: not."""
    d = de_point(w)
    if _seek(r[9], w) or _seek(r[10], d) or r[11].startswith(w):
        return 3
    if _seek(r[4], w) or _seek(r[8], d):
        return 2
    return 1 if len(w) > 1 and (w in r[4] or d in r[8] or (keyed and w in r[7])) else 0


def _rank(r, x):
    ws, need, bare, have, text, keyed = x['ws'], x['need'], x['bare'], x['have'], x['text'], x['keyed']
    glued = len(ws) > 1 and r[11].startswith(_SPACE.sub('', text))
    how = 3
    if not glued:
        for w in need:
            how = min(how, _word_in(r, w, keyed))
            if not how:
                return None

    def every(words):
        return bool(words) and all(w in have for w in words)

    whole = len(bare) > 0 and (every(r[13]) or every(r[14]))
    phrase = len(ws) > 1 and (glued or _seek(r[9], text, True) or _seek(r[10], de_point(text), True))
    lacks = len([w for w in bare if not _seek(r[9], w)])
    if any(s.startswith(ws[0]) for s in (r[5], r[6], r[11])):
        lead = 2
    elif r[12].startswith(need[0]):
        lead = 1
    else:
        lead = 0
    return (how, 1 if whole else 0, 1 if phrase else 0, -lacks, lead)


def readings(query):
    """The ways the query is read: as typed, and (Greek letters in it) as the Latin keys they sit on."""
    words = fold_keys(query).split()
    typed = []
    for w in words:
        m = _BAND_AFTER.match(w) or _BAND_BEFORE.match(w)
        typed.extend(m.groups() if m else [w])
    if not typed:
        return []
    reads = [lambda w: w.replace(FINAL_SIGMA, SIGMA)]
    if _GREEK.search(u''.join(typed)):
        reads.append(greek_keys)
    out = []
    for read in reads:
        ws = [read(w) for w in typed]
        need = [w for w in ws if w not in BARE_WORDS]
        out.append({'ws': ws, 'text': u' '.join(ws), 'keyed': read is greek_keys, 'need': need or ws,
                    'bare': [w for w in ws if w in BARE_WORDS] if need else [],
                    'have': set(name_words(u' '.join(ws + [read(w) for w in words])))})
    return out


def _maybe(pre, pre_flat, pre_point, x):
    """A cheap test every row the query finds passes (most rows that do not, fail)."""
    if len(x['ws']) > 1 and _SPACE.sub('', x['text']) in pre_flat:
        return True
    for w in x['need']:
        d = de_point(w)
        if not (w in pre_flat or w in pre or d in pre_point or d in de_point(pre_flat)):
            return False
    return True


def search(rows, query, limit=None):
    """The rows the query finds, best first. rows: [(edition, [slug, name, meta, logo, also]), ...] in radioko's
    order; returns (hits, total), each hit the search row (its [0] the station's slug with its edition)."""
    ways = readings(query)
    if not ways:
        return [], 0
    hits = []
    for edition, row in rows:
        name, meta = row[1] or '', row[2] or ''
        also = row[4] if len(row) > 4 and row[4] else ''
        pre = fold(u'%s %s %s\n%s %s' % (name, meta, also, name, also))
        pre_flat = _SPACE.sub('', pre)
        pre_point = de_point(pre)
        if not any(_maybe(pre, pre_flat, pre_point, x) for x in ways):
            continue
        r = search_row(edition, row)
        best = None
        for x in ways:
            score = _rank(r, x)
            if score is not None and (best is None or score > best):
                best = score
        if best is not None:
            hits.append((best, len(hits), r))
    hits.sort(key=lambda h: (tuple(-v for v in h[0]), h[1]))
    found = [h[2] for h in hits]
    return (found[:limit] if limit else found), len(found)

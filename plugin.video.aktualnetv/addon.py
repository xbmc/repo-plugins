# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmc, actions
from urllib import urlencode
import gzip
import io
import json
import re
import sys
import urllib2

if sys.version_info < (3, 0):
    import HTMLParser
    unescape = HTMLParser.HTMLParser().unescape
else:
    import html
    unescape = html.unescape


plugin = Plugin()
FANART = 'special://home/addons/%s/fanart.jpg' % plugin.id
ICON = 'special://home/addons/%s/icon.png' % plugin.id


def _get_file(url, referer = None):
    req = urllib2.Request(url)
    if referer:
        req.add_header('Referer', referer)
    req.add_header('Accept-Encoding', 'gzip')
    content = None
    f = urllib2.urlopen(req)
    ce = f.headers.get('Content-Encoding')
    if ce and 'gzip' in ce:
        gzipf = gzip.GzipFile(fileobj=io.BytesIO(f.read()), mode='rb')
        content = gzipf.read()
    else:
        content = f.read()
    f.close()
    return content


def _js_to_json(code):
    def fix_kv(m):
        v = m.group(0)
        if v in ('true', 'false', 'null'):
            return v
        if v.startswith('"'):
            return v
        if v.startswith("'"):
            v = v[1:-1]
            v = re.sub(r"\\\\|\\'|\"", lambda m: {
                '\\\\': '\\\\',
                "\\'": "'",
                '"': '\\"',
                }[m.group(0)], v)
        return '"%s"' % v

    res = re.sub(r'''(?x)
        "(?:[^"\\]*(?:\\\\|\\")?)*"|
        '(?:[^'\\]*(?:\\\\|\\')?)*'|
        [a-zA-Z_][.a-zA-Z_0-9]*
        ''', fix_kv, code
        )
    res = re.sub(r',(\s*\])', lambda m: m.group(1), res)
    return res


def _js_to_obj(code):
    return json.loads(_js_to_json(code))


def _decode_entities(s):
    s = unescape(s)
    s = re.sub(u'\\.\\.\\.', u'…', s)
    s = re.sub('\\s+', ' ', s)
    s = s.strip()
    return s


def _hq_img(addr):
    if addr.startswith('//'):
        addr = 'https:%s' % addr
    addr = re.sub('\\?.+$', '', addr)
    addr = re.sub('_w[0-9]+_h[0-9]+_', '_w782_h440_', addr)
    return addr


@plugin.cached(TTL=35)
def get_webpage(url):
    page = _get_file(url, 'https://video.aktualne.cz/').decode('utf-8')
    return page


@plugin.route('/')
def menu():
    items = [{
            'label': plugin.get_string(30011),
            'path': plugin.url_for('menu_playlist_short', path='index'),
            'thumbnail': ICON
            },
        {
            'label': plugin.get_string(30012),
            'path': plugin.url_for('menu_shows'),
            'thumbnail': ICON
            },
        {
            'label': plugin.get_string(30014),
            'path': plugin.url_for('menu_search_dialog'),
            'thumbnail': ICON
            }
        ]
    plugin.set_content('movies')
    return items


@plugin.route('/shows')
def menu_shows():
    page = get_webpage('https://video.aktualne.cz/')
    page = re.findall(u'<h2 id="porady">Pořady</h2>(.+?)</ul>', page, re.DOTALL)[0]
    matches = re.findall(u'<a class="(.+?)" href="/(.+?)/">.+?<span class="nazev">(.+?)</span>.+?</a>', page, re.DOTALL)
    items = [{
        'label': _decode_entities(re.sub('<.+?>', ' ', m[2])),
        'path': plugin.url_for('menu_playlist_short', path=m[1]),
        'thumbnail': 'https://i0.cz/bbx/video/img/video/porad-d-%s-uzky.jpg' % m[0]
        } for m in matches]
    return plugin.finish(items, view_mode='thumbnail')


def _create_playlist_menuitem(label, href, img):
    return {
        'label': label,
        'path': href,
        'thumbnail': img
        }


@plugin.route('/playlist/<path>', name='menu_playlist_short', options={'offset': '0'})
@plugin.route('/playlist/<path>_<offset>')
def menu_playlist(path, offset):
    offset = int(offset)
    if path == 'index':
        url = 'https://video.aktualne.cz/?offset=%d' % offset
    else:
        url = 'https://video.aktualne.cz/%s/?offset=%d' % (path, offset)
    page = get_webpage(url)
    next = re.search('class="doprava', page, flags=re.DOTALL) is not None
    items = []
    matches = re.findall(u'<div class="boxik.+?class="nahled" href="(.+?)".+? src="(.+?)" .+?class="nazev">(.+?)</span>.+?</div>', page, re.DOTALL)
    for m in matches:
        label = _decode_entities(m[2])
        img = m[1]
        href = re.sub(u'.+r~([0-9a-f]{32}).*', u'\\1', m[0])
        items.append(_create_playlist_menuitem(label, plugin.url_for('play_video', token=href), _hq_img(img)))
    if next:
        items.append({
            'label': plugin.get_string(30020),
            'path': plugin.url_for('menu_playlist', path=path, offset=str(offset + len(items)))
            })
    return items


@plugin.route('/video/<token>')
def play_video(token):
    url = 'https://video.aktualne.cz/-/r~%s/' % token
    page = get_webpage(url)

    s1 = re.search(u'(?s)embedData[0-9a-f]{32}\\[\'asset\'\\]\s*=\\s*(\\{.+?\\});', page, re.DOTALL)
    if s1:
        metadata = _js_to_obj(s1.group(1))
        formats = {}
        for i in metadata['sources']:
            f = '%s@%s' % (i['type'], i['label'])
            formats[f] = i['file']
            #formats[f] = re.sub('^http://', 'https://', i['file'])
        prefered_format = plugin.get_setting('format', choices=('video/mp4', 'video/webm'))
        prefered_quality = plugin.get_setting('quality', choices=('180p', '360p', '720p'))
        preference = '%s@%s' % (prefered_format, prefered_quality)
        format = preference if preference in formats else formats.keys()[0]

        plot = re.search(u'(?s)<p class="popis".+?\\| (.+?)</p>', page, re.DOTALL).group(1)
        show = re.search(u'(?s)\'GA\': htmldeentitize\\(\'(.+?)\'\\)', page, re.DOTALL).group(1)

        return [{
            'label': _decode_entities(metadata['title']),
            'is_playable': True,
            'path': formats[format],
            'thumbnail': _hq_img(metadata['image']) if 'image' in metadata else None,
            'info_type': 'video',
            'info': {
                'title': _decode_entities(metadata['title']),
                'studio': plugin.get_string(30001),
                'genre': 'News',
                'plot': _decode_entities(plot),
                'tagline': _decode_entities(show)
                },
            'stream_info': {
                'video': {
                    'duration': metadata['duration']
                    }
                }
            }]
    else:
        s2 = re.findall(u'(?s)BBX\\.context\\.assets\\[\'[0-9a-f]{32}\'\\]\\.push\\(({.+?})\\);', page, re.DOTALL)
        if s2:
            items = []
            for m in s2:
                i = _js_to_obj(m)
                items.append(_create_playlist_menuitem(
                    _decode_entities(i['title']),
                    plugin.url_for('play_video', token=i['mediaid']),
                    _hq_img(i['image'])
                    ))
            return items


@plugin.route('/search')
def menu_search_dialog():
    q = plugin.keyboard(heading=plugin.get_string(30014))
    if q:
        return menu_search(q, '0')


@plugin.route('/search/<q>', name='menu_search_short', options={'offset': '0'})
@plugin.route('/search/<q>_<offset>')
def menu_search(q, offset):
    offset = int(offset)
    url = 'https://video.aktualne.cz/hledani/?%s' % urlencode({
        'query': q,
        'time': 'time',
        'offset': offset
        })
    page = get_webpage(url)
    next = re.search('class="doprava', page, flags=re.DOTALL) is not None
    items = []
    matches = re.findall(u'<div class="boxik.+?class="nahled" href="(.+?)".+? src="(.+?)".+?class="nazev".+?>(.+?)</a>.+?</div>', page, re.DOTALL)
    for m in matches:
        label = _decode_entities(m[2])
        label = re.sub('</?strong>', '', label)
        img = m[1]
        href = re.sub(u'.+r~([0-9a-f]{32}).*', u'\\1', m[0])
        items.append(_create_playlist_menuitem(
            label,
            plugin.url_for('play_video', token=href),
            _hq_img(img)
            ))
    if next:
        items.append({
            'label': plugin.get_string(30020),
            'path': plugin.url_for('menu_search', q=q, offset=str(offset + len(items)))
            })
    return items


if __name__ == '__main__':
    plugin.run()

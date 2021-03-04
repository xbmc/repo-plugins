# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
''' A list of static data '''

from __future__ import absolute_import, division, unicode_literals

CHANNELS = [
    dict(
        name='ATV',
        label='Antwerpen',
        description='ATV is een regionale televisiezender voor de provincie Antwerpen.',
        live_stream='http://api.new.livestream.com/accounts/27755193/events/8452381/live.m3u8',
        logo='http://static.atv.be/atvbe/meta/android-chrome-192x192.png',
        website='https://atv.be/',
        preset=201,
    ),
    dict(
        name='BRUZZ',
        label='Brussel',
        description='Al het nieuws uit Brussel en de beste cultuurtips.',
        # live_stream='https://hls-origin01-bruzz.cdn02.rambla.be/adliveorigin-bruzz/_definst_/AZwy8w.smil/playlist.m3u8',
        live_stream='https://hls-origin01-bruzz.cdn02.rambla.be/main/adliveorigin-bruzz/_definst_/V3n5YY.smil/playlist.m3u8',
        referer='https://player.cdn01.rambla.be/players/video-js/',
        logo='https://i.imgur.com/rcfUiWV.jpg',
        website='https://www.bruzz.be/',
        preset=203,
    ),
    dict(
        name='Focus & WTV',
        label='West-Vlaanderen',
        description='Het meest belangwekkende nieuws uit West-Vlaanderen.',
        # live_stream='https://hls-origin01-focus-wtv.cdn01.rambla.be/main/adliveorigin-focus-wtv/_definst_/ARXpX7.smil/playlist.m3u8?',
        live_stream='https://hls-origin01-focus-wtv.cdn01.rambla.be/main/adliveorigin-focus-wtv/_definst_/ARXpX7.smil/playlist.m3u8',
        referer='http://player.clevercast.com/players/video-js/',
        logo='https://i.imgur.com/aGORIN8.png',
        website='https://www.focus-wtv.be/',
        preset=204,
    ),
    dict(
        name='ROB-tv',
        label='Oost-Brabant',
        description='Uw dagelijkse portie regionaal nieuws uit Oost-Brabant.',
        live_stream='http://api.new.livestream.com/accounts/27755193/events/8462344/live.m3u8',
        logo='http://static.tvl.be/robtvbe/meta/android-chrome-192x192.png',
        website='https://robtv.be/',
        preset=206,
    ),
    dict(
        name='TVL',
        label='Limburg',
        description='Het dagelijkse nieuws uit Limburg.',
        live_stream='http://api.new.livestream.com/accounts/27755193/events/8452383/live.m3u8',
        logo='http://static.tvl.be/tvlbe/meta/android-chrome-192x192.png',
        website='https://tvl.be/',
        preset=208,
    ),
    dict(
        name='TV Oost',
        label='Oost-Vlaanderen',
        description='Uw dagelijkse portie regionaal nieuws uit Oost-Vlaanderen.',
        live_stream='http://api.new.livestream.com/accounts/27755193/events/8511193/live.m3u8',
        logo='http://static.tvoost.be/tvoostbe/meta/android-chrome-192x192.png',
        website='https://tvoost.be/',
        preset=209,
    ),
]

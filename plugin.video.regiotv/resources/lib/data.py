# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
''' A list of static data '''

from __future__ import absolute_import, division, unicode_literals

CHANNELS = [
    dict(
        name='ATV',
        label='Antwerpen',
        # live_stream='https://player-api.new.livestream.com/accounts/27755193/events/8452381/live.m3u8',
        live_stream='http://api.new.livestream.com/accounts/27755193/events/8452381/live.m3u8',
        logo='https://i.imgur.com/iWXUmje.jpg',
        website='https://atv.be/',
    ),
    dict(
        name='BRUZZ',
        label='Brussel',
        # live_stream='https://hls-origin01-bruzz.cdn02.rambla.be/adliveorigin-bruzz/_definst_/AZwy8w.smil/chunklist_b3000000.m3u8',
        # live_stream='https://media.streamone.net/hlslive/account=H6AAMOMZSU0W/livestream=nJQBqssIRB82/live-audio101_dut=128000-video=2200000.m3u8',
        live_stream='https://hls-origin01-bruzz.cdn02.rambla.be/adliveorigin-bruzz/_definst_/AZwy8w.smil/playlist.m3u8',
        logo='https://i.imgur.com/rcfUiWV.jpg',
        website='https://www.bruzz.be/',
    ),
    dict(
        name='Focus TV',
        label='West-Vlaanderen',
        live_stream='https://hls-origin01-focus-wtv.cdn01.rambla.be/adliveorigin-focus-wtv/_definst_/AK4e8O.smil/playlist.m3u8',
        logo='https://i.imgur.com/aGORIN8.png',
        website='https://www.focustv.be/',
    ),
    dict(
        name='ROB-tv',
        label='Vlaams-Brabant',
        # live_stream='https://player-api.new.livestream.com/accounts/27755193/events/8462344/live.m3u8',
        live_stream='http://api.new.livestream.com/accounts/27755193/events/8462344/live.m3u8',
        logo='https://i.imgur.com/CzQe0q2.png',
        website='https://robtv.be/',
    ),
    dict(
        name='TVL',
        label='Limburg',
        # live_stream='https://player-api.new.livestream.com/accounts/27755193/events/8452383/live.m3u8',
        live_stream='http://api.new.livestream.com/accounts/27755193/events/8452383/live.m3u8',
        logo='https://i.ibb.co/KGRYRmt/download.jpg',
        website='https://tvl.be/',
    ),
    dict(
        name='TV Oost',
        label='Oost-Vlaanderen',
        # live_stream='https://player-api.new.livestream.com/accounts/27755193/events/8511193/live.m3u8',
        live_stream='http://api.new.livestream.com/accounts/27755193/events/8511193/live.m3u8',
        logo='https://i.imgur.com/JFVEcEA.png',
        website='https://tvoost.be/',
    ),
    dict(
        name='WTV',
        label='West-Vlaanderen',
        # live_stream='https://hls-origin01-focus-wtv.cdn01.rambla.be/adliveorigin-focus-wtv/_definst_/VzXNby.smil/chunklist_b3000000.m3u8',
        live_stream='https://hls-origin01-focus-wtv.cdn01.rambla.be/adliveorigin-focus-wtv/_definst_/VzXNby.smil/playlist.m3u8',
        logo='https://i.imgur.com/aGORIN8.png',
        website='https://www.wtv.be/',
    ),
]

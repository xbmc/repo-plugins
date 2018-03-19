# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2016  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

'''
SKELETON dictionary corresponds to the architecture of each menu of the addon
(elt1, elt2) -->
    elt1: label
    elt2: next function to call
'''
SKELETON = {
    ('root', 'generic_menu'): {

        ('live_tv', 'generic_menu'): {

            ('fr', 'build_live_tv_menu'): [
                ('tf1', 'none'),
                ('france2', 'none'),
                ('france3', 'none'),
                ('france5', 'none'),
                ('canalplus', 'none'),
                ('c8', 'none'),
                ('tmc', 'none'),
                ('tfx', 'none'),
                ('nrj12', 'none'),
                ('france4', 'none'),
                ('bfmtv', 'none'),
                ('cnews', 'none'),
                ('cstar', 'none'),
                ('gulli', 'none'),
                ('franceo', 'none'),
                ('tf1-series-films', 'none'),
                ('lequipe', 'none'),
                ('numero23', 'none'),
                ('cherie25', 'none'),
                ('la_1ere', 'none'),
                ('franceinfo', 'none'),
                ('bfmbusiness', 'none'),
                ('rmc', 'none'),
                ('lci', 'none'),
                ('lcp', 'none'),
                ('rmcdecouverte', 'none'),
                ('publicsenat', 'none'),
                ('france3regions', 'none'),
                ('francetvsport', 'none'),
                ('gong', 'none'),
                ('bfmparis', 'none')
            ],

            ('be', 'build_live_tv_menu'): [
                ('rtc', 'none'),
                ('telemb', 'none'),
                ('vrt', 'none'),
                ('auvio', 'none'),
                ('rtltvi', 'none'),
                ('plugrtl', 'none'),
                ('clubrtl', 'none')
            ],

            ('ca', 'build_live_tv_menu'): [
                ('telequebec', 'none'),
                ('yestv', 'none')
            ],

            ('ch', 'build_live_tv_menu'): [
                ('rougetv', 'none'),
                ('rts', 'none'),
                ('rsi', 'none'),
                ('srf', 'none'),
                ('rtr', 'none')
            ],

            ('uk', 'build_live_tv_menu'): [
                ('blaze', 'none'),
                ('skynews', 'none')
            ],

            ('wo', 'build_live_tv_menu'): [
                ('arirang', 'none'),
                ('arte', 'none'),
                ('bvn', 'none'),
                ('euronews', 'none'),
                ('france24', 'none'),
                ('icitelevision', 'none'),
                ('nhkworld', 'none'),
                ('dw', 'none'),
                ('tv5monde', 'none'),
                ('tivi5monde', 'none')
            ]
        },

        ('replay', 'generic_menu'): {

            ('be', 'generic_menu'): [
                ('auvio', 'replay_entry'),
                ('brf', 'replay_entry'),
                ('rtltvi', 'replay_entry'),
                ('plugrtl', 'replay_entry'),
                ('clubrtl', 'replay_entry'),
                ('vrt', 'replay_entry'),
                ('telemb', 'replay_entry'),
                ('rtc', 'replay_entry')
            ],

            ('ca', 'generic_menu'): [
                ('tv5', 'replay_entry'),
                ('unis', 'replay_entry'),
                ('telequebec', 'replay_entry')
            ],

            ('fr', 'generic_menu'): [
                ('tf1', 'replay_entry'),
                ('france2', 'replay_entry'),
                ('france3', 'replay_entry'),
                ('canalplus', 'replay_entry'),
                ('france5', 'replay_entry'),
                ('m6', 'replay_entry'),
                ('c8', 'replay_entry'),
                ('w9', 'replay_entry'),
                ('tmc', 'replay_entry'),
                ('tfx', 'replay_entry'),
                ('nrj12', 'replay_entry'),
                ('france4', 'replay_entry'),
                ('bfmtv', 'replay_entry'),
                ('cnews', 'replay_entry'),
                ('cstar', 'replay_entry'),
                ('gulli', 'replay_entry'),
                ('franceo', 'replay_entry'),
                ('tf1-series-films', 'replay_entry'),
                ('lequipe', 'replay_entry'),
                ('6ter', 'replay_entry'),
                ('numero23', 'replay_entry'),
                ('cherie25', 'replay_entry'),
                ('la_1ere', 'replay_entry'),
                ('bfmbusiness', 'replay_entry'),
                ('rmc', 'replay_entry'),
                ('01net', 'replay_entry'),
                ('tfou', 'replay_entry'),
                ('xtra', 'replay_entry'),
                ('lci', 'replay_entry'),
                ('lcp', 'replay_entry'),
                ('rmcdecouverte', 'replay_entry'),
                ('stories', 'replay_entry'),
                ('bruce', 'replay_entry'),
                ('crazy_kitchen', 'replay_entry'),
                ('home', 'replay_entry'),
                ('styles', 'replay_entry'),
                ('comedy', 'replay_entry'),
                ('publicsenat', 'replay_entry'),
                ('histoire', 'replay_entry'),
                ('tvbreizh', 'replay_entry'),
                ('ushuaiatv', 'replay_entry'),
                ('studio-4', 'replay_entry'),
                ('irl', 'replay_entry'),
                ('seasons', 'replay_entry'),
                ('comedie', 'replay_entry'),
                ('les-chaines-planete', 'replay_entry'),
                ('golfplus', 'replay_entry'),
                ('cineplus', 'replay_entry'),
                ('infosportplus', 'replay_entry'),
                ('gameone', 'replay_entry'),
                ('francetveducation', 'replay_entry'),
                ('gong', 'replay_entry'),
                ('francetvsport', 'replay_entry')
            ],

            ('jp', 'generic_menu'): [
                ('nhknews', 'replay_entry'),
                ('nhklifestyle', 'replay_entry'),
                ('tbsnews', 'replay_entry'),
                ('ntv', 'replay_entry'),
                ('ex', 'replay_entry'),
                ('tbs', 'replay_entry'),
                ('tx', 'replay_entry'),
                # ('cx': 'replay_entry'), (Protected by DRM)
                ('mbs', 'replay_entry'),
                ('abc', 'replay_entry'),
                ('ytv', 'replay_entry')
            ],

            ('ch', 'generic_menu'): [
                ('rts', 'replay_entry'),
                ('rsi', 'replay_entry'),
                ('srf', 'replay_entry'),
                ('rtr', 'replay_entry'),
                ('swissinfo', 'replay_entry'),
                ('rougetv', 'replay_entry')
            ],

            ('uk', 'generic_menu'): [
                ('blaze', 'replay_entry'),
                ('dave', 'replay_entry'),
                ('really', 'replay_entry'),
                ('yesterday', 'replay_entry'),
                ('drama', 'replay_entry'),
                ('skynews', 'replay_entry'),
                ('skysports', 'replay_entry')
            ],

            ('wo', 'generic_menu'): [
                ('tv5mondeafrique', 'replay_entry'),
                ('arte', 'replay_entry'),
                ('france24', 'replay_entry'),
                ('nhkworld', 'replay_entry'),
                ('tv5monde', 'replay_entry'),
                ('tivi5monde', 'replay_entry'),
                ('bvn', 'replay_entry'),
                ('icitelevision', 'replay_entry'),
                ('mtv', 'replay_entry'),
                ('arirang', 'replay_entry')
            ]
        },
        ('websites', 'generic_menu'): [
            ('allocine', 'website_entry'),
            ('tetesaclaques', 'website_entry'),
            ('taratata', 'website_entry'),
            ('noob', 'website_entry'),
            ('culturepub', 'website_entry'),
            ('autoplus', 'website_entry'),
            ('notrehistoirech', 'website_entry'),
            ('30millionsdamis', 'website_entry'),
            ('elle', 'website_entry')
        ]

    }
}


'''
SKELETON dictionary is the bridge between
the item in Kodi and the real folder location on disk
'''
FOLDERS = {
    'live_tv': 'channels',
    'replay': 'channels'
}


'''
CHANNELS dictionary is the bridge between
the channel name and his corresponding python file
'''
CHANNELS = {
    'auvio': 'rtbf',
    'brf': 'brf',
    'rtltvi': 'rtl',
    'plugrtl': 'rtl',
    'clubrtl': 'rtl',
    'vrt': 'vrt',
    'telemb': 'telemb',
    'rtc': 'rtc',
    'tv5': 'tv5',
    'unis': 'tv5',
    'yestv': 'yestv',
    'telequebec': 'telequebec',
    'rts': 'srgssr',
    'rsi': 'srgssr',
    'srf': 'srgssr',
    'rtr': 'srgssr',
    'swissinfo': 'srgssr',
    'rougetv': 'rougetv',
    'tf1': 'tf1',
    'france2': 'pluzz',
    'france3': 'pluzz',
    'canalplus': 'mycanal',
    'france5': 'pluzz',
    'm6': '6play',
    'c8': 'mycanal',
    'w9': '6play',
    'tmc': 'tf1',
    'tfx': 'tf1',
    'nrj12': 'nrj',
    'france4': 'pluzz',
    'bfmtv': 'bfmtv',
    'bfmparis': 'bfmtv',
    'cnews': 'cnews',
    'cstar': 'mycanal',
    'gulli': 'gulli',
    'franceo': 'pluzz',
    'tf1-series-films': 'tf1',
    'lequipe': 'lequipe',
    '6ter': '6play',
    'numero23': 'numero23',
    'cherie25': 'nrj',
    'la_1ere': 'pluzz',
    'franceinfo': 'pluzz',
    'bfmbusiness': 'bfmtv',
    'rmc': 'bfmtv',
    '01net': 'bfmtv',
    'tfou': 'tf1',
    'xtra': 'tf1',
    'lci': 'tf1',
    'lcp': 'lcp',
    'rmcdecouverte': 'bfmtv',
    'stories': '6play',
    'bruce': '6play',
    'crazy_kitchen': '6play',
    'home': '6play',
    'styles': '6play',
    'comedy': '6play',
    'publicsenat': 'publicsenat',
    'france3regions': 'pluzz',
    'francetvsport': 'pluzz',
    'histoire': 'tf1thematiques',
    'tvbreizh': 'tf1thematiques',
    'ushuaiatv': 'tf1thematiques',
    'studio-4': 'pluzz',
    'irl': 'pluzz',
    'seasons': 'mycanal',
    'comedie': 'mycanal',
    'les-chaines-planete': 'mycanal',
    'golfplus': 'mycanal',
    'cineplus': 'mycanal',
    'infosportplus': 'mycanal',
    'gameone': 'gameone',
    'francetveducation': 'pluzz',
    'gong': 'gong',
    'nhknews': 'nhk',
    'nhklifestyle': 'nhk',
    'tbsnews': 'tbs',
    'blaze': 'blaze',
    'dave': 'uktvplay',
    'really': 'uktvplay',
    'yesterday': 'uktvplay',
    'drama': 'uktvplay',
    'skynews': 'sky',
    'skysports': 'sky',
    'tv5mondeafrique': 'tv5monde',
    'arte': 'arte',
    'euronews': 'euronews',
    'france24': 'france24',
    'nhkworld': 'nhkworld',
    'tv5monde': 'tv5monde',
    'tivi5monde': 'tv5monde',
    'bvn': 'bvn',
    'icitelevision': 'icitelevision',
    'mtv': 'mtv',
    'arirang': 'arirang',
    'dw': 'dw',
    'ntv': 'tver',
    'ex': 'tver',
    'tbs': 'tver',
    'tx': 'tver',
    # 'cx': 'tver', (Protected by DRM)
    'mbs': 'tver',
    'abc': 'tver',
    'ytv': 'tver'
}

'''
LABELS dict is only used to retrieve correct element in english strings.po
'''
LABELS = {

    # root
    'live_tv': 'Live TV',
    'replay': 'Catch-up TV',
    'websites': 'Websites',

    # Countries
    'be': 'Belgium',
    'fr': 'France',
    'jp': 'Japan',
    'ch': 'Switzerland',
    'uk': 'United Kingdom',
    'wo': 'International',
    'ca': 'Canada',

    # Belgium channels / live TV
    'auvio': 'RTBF Auvio (La Une, La deux, La Trois, ...)',
    'brf': 'BRF Mediathek',
    'rtltvi': 'RTL-TVI',
    'plugrtl': 'PLUG RTL',
    'clubrtl': 'CLUB RTL',
    'vrt': 'VRT NU',
    'telemb': 'Télé MB',
    'rtc': 'RTC Télé Liège',

    # Canadian channels / live TV
    'tv5': 'TV5',
    'unis': 'UNIS',
    'yestv': 'YES TV',
    'telequebec': 'Télé-Québec',

    # Switzerland channels / live TV
    'rts': 'RTS',
    'rsi': 'RSI',
    'srf': 'SRF',
    'rtr': 'RTR',
    'swissinfo': 'SWISSINFO',
    'rougetv': 'Rouge TV',

    # French channels / live TV
    'tf1': 'TF1',
    'france2': 'France 2',
    'france3': 'France 3',
    'canalplus': 'Canal +',
    'france5': 'France 5',
    'm6': 'M6',
    'c8': 'C8',
    'w9': 'W9',
    'tmc': 'TMC',
    'tfx': 'TFX',
    'nrj12': 'NRJ 12',
    'france4': 'France 4',
    'bfmtv': 'BFM TV',
    'bfmparis': 'BFM Paris',
    'cnews': 'CNews',
    'cstar': 'CStar',
    'gulli': 'Gulli',
    'franceo': 'France Ô',
    'tf1-series-films': 'TF1 Séries Films',
    'lequipe': 'L\'Équipe',
    '6ter': '6ter',
    'numero23': 'Numéro 23',
    'cherie25': 'Chérie 25',
    'la_1ere': 'La 1ère (Outre-Mer)',
    'franceinfo': 'France Info',
    'bfmbusiness': 'BFM Business',
    'rmc': 'RMC',
    '01net': '01Net TV',
    'tfou': 'Tfou (MYTF1)',
    'xtra': 'Xtra (MYTF1)',
    'lci': 'LCI',
    'lcp': 'LCP Assemblée Nationale',
    'rmcdecouverte': 'RMC Découverte HD24',
    'stories': 'Stories (6play)',
    'bruce': 'Bruce (6play)',
    'crazy_kitchen': 'Crazy Kitchen (6play)',
    'home': 'Home Time (6play)',
    'styles': 'Sixième Style (6play)',
    'comedy': 'Comic (6play)',
    'publicsenat': 'Public Sénat',
    'france3regions': 'France 3 Régions',
    'francetvsport': 'France TV Sport (francetv)',
    'histoire': 'Histoire',
    'tvbreizh': 'TV Breizh',
    'ushuaiatv': 'Ushuaïa TV',
    'studio-4': 'Studio 4 (francetv)',
    'irl': 'IRL (francetv)',
    'seasons': 'Seasons',
    'comedie': 'Comédie +',
    'les-chaines-planete': 'Les chaînes planètes +',
    'golfplus': 'Golf +',
    'cineplus': 'Ciné +',
    'infosportplus': 'INFOSPORT+',
    'gameone': 'Game One',
    'francetveducation': 'France TV Education (francetv)',
    'gong': 'Gong',

    # Japan channels / live TV
    'nhknews': 'NHK ニュース',
    'nhklifestyle': 'NHKらいふ',
    'tbsnews': 'TBS ニュース',
    'ntv': '日テレ',
    'ex': 'テレビ朝日',
    'tbs': 'TBSテレビ',
    'tx': 'テレビ東京',
    # 'cx': 'フジテレビ', (Protected by DRM)
    'mbs': 'MBSテレビ',
    'abc': '朝日放送株式会社',
    'ytv': '読売テレビ',

    # United Kingdom channels / live TV
    'blaze': 'Blaze',
    'dave': 'Dave',
    'really': 'Really',
    'yesterday': 'Yesterday',
    'drama': 'Drama',
    'skynews': 'Sky News',
    'skysports': 'Sky Sports',

    # International channels / live TV
    'tv5mondeafrique': 'TV5Monde Afrique',
    'arte': 'Arte',
    'euronews': 'Euronews',
    'france24': 'France 24',
    'nhkworld': 'NHK World',
    'tv5monde': 'TV5Monde',
    'tivi5monde': 'Tivi 5Monde',
    'bvn': 'BVN',
    'icitelevision': 'ICI Télévision',
    'mtv': 'MTV',
    'arirang': 'Arirang (아리랑)',
    'dw': 'DW',

    # Websites
    'allocine': 'Allociné',
    'tetesaclaques': 'Au pays des Têtes à claques',
    'taratata': 'Taratata',
    'noob': 'Noob TV',
    'culturepub': 'Culturepub',
    'autoplus': 'Auto Plus',
    'notrehistoirech': 'Notre Histoire',
    '30millionsdamis': '30 Millions d\'Amis',
    'elle': 'Elle'
}

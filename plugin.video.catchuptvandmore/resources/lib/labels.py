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

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from codequick import Script, utils

import resources.lib.mem_storage as mem_storage

"""
LABELS dict is only used to
retrieve correct element in strings.po.
If the item has no translation just use a string.
"""

s = mem_storage.MemStorage('cutv_labels')


def save_labels_in_mem_storage():
    """Evaluate LABELS dict and save it in mem storage

    Returns:
        dict: LABELS dict
    """
    LABELS = {
        # Settings
        'Main menu':
        30000,
        'Countries':
        30001,
        'Quality and content':
        30002,
        'Downloads':
        30003,
        'Accounts':
        30004,
        'Advanced settings':
        30005,
        'Channels':
        30006,
        'Websites':
        30007,
        'Hide main menu categories':
        30010,
        'Hide channels':
        30011,
        'To configure YTDL go settings of script.module.youtube.dl':
        30012,
        'Hide countries':
        30013,
        'Hide websites':
        30014,

        # Root menu
        'live_tv':
        30030,
        'replay':
        30031,
        'websites':
        30032,

        # Countries
        'fr_replay':
        30050,
        'fr_live':
        30050,
        'ch_replay':
        30051,
        'ch_live':
        30051,
        'uk_replay':
        30052,
        'uk_live':
        30052,
        'wo_replay':
        30053,
        'wo_live':
        30053,
        'be_replay':
        30054,
        'be_live':
        30054,
        'jp_replay':
        30055,
        'jp_live':
        30055,
        'ca_replay':
        30056,
        'ca_live':
        30056,
        'us_replay':
        30057,
        'us_live':
        30057,
        'pl_replay':
        30058,
        'pl_live':
        30058,
        'es_replay':
        30059,
        'es_live':
        30059,
        'tn_replay':
        30060,
        'tn_live':
        30060,
        'it_replay':
        30061,
        'it_live':
        30061,
        'nl_replay':
        30062,
        'nl_live':
        30062,
        'cn_replay':
        30063,
        'cn_live':
        30063,
        'cm_replay':
        30064,
        'cm_live':
        30064,
        'French channels':
        30080,
        'Belgian channels':
        30081,
        'Japanese channels':
        30082,
        'Switzerland channels':
        30083,
        'United Kingdom channels':
        30084,
        'International channels':
        30085,
        'Canadian channels':
        30086,
        'United States channels':
        30087,
        'Polish channels':
        30088,
        'Spanish channels':
        30089,
        'Tunisia channels':
        30090,
        'Italian channels':
        30091,
        'Dutch channels':
        30092,
        'Chinese channels':
        30093,
        'Cameroon channels':
        30094,

        # Settings again
        'Video quality':
        30150,
        'Video quality (BEST|DEFAULT|DIALOG)':
        30151,
        'Contents':
        30152,
        'Arte: Choose Channel':
        30153,
        'France 24: Choose Channel':
        30154,
        'Euronews: Choose Channel':
        30155,
        'MTV: Choose Channel':
        30156,
        'DW: Choose Channel':
        30157,
        'France 3 Régions: Choose region':
        30158,
        'La 1ère: Choose region':
        30159,
        'Bein Sports: Choose Channel':
        30160,
        'QVC: Choose Channel':
        30161,
        'NHK World: Choose Country':
        30162,
        'CGTN: Choose Channel':
        30163,
        'Paramount Channel: Choose Channel':
        30164,
        'Realmadrid TV: Choose Channel':
        30165,
        'Yes TV: Choose region':
        30166,
        'TVP 3: Choose region':
        30167,
        'Folder to Download':
        30200,
        'Quality of the video to download':
        30201,
        'Download in background':
        30202,
        'NRJ Login':
        30240,
        'NRJ Password':
        30241,
        'VRT NU Login':
        30242,
        'VRT NU Password':
        30243,
        '6play Login':
        30244,
        '6play Password':
        30245,
        'RTLplay Login':
        30246,
        'RTLplay Password':
        30247,


        # Menus settings
        'Restore default order of all menus':
        30400,
        'Unmask all hidden items':
        30401,
        'Select item to unmask':
        30406,
        'Default order of all menus have been restored':
        30407,
        'All hidden items have been unmasked':
        30408,

        # Context menu
        'Clear cache':
        30370,
        'Cache cleared':
        30371,
        'Move down':
        30500,
        'Move up':
        30501,
        'Hide':
        30502,
        'Download':
        30503,
        'List Videos (type=extrait)':
        30504,
        'List Videos (type=episode)':
        30505,
        'Information':
        30600,
        'To re-enable hidden items go to the plugin settings':
        30601,
        'More videos...':
        30700,
        'All videos':
        30701,
        'DRM protected video':
        30702,
        'Search':
        30703,
        'Last videos':
        30704,
        'From A to Z':
        30705,
        'Ascending':
        30706,
        'Descending':
        30707,
        'More programs...':
        30708,
        'Choose video quality':
        30709,
        'Video stream no longer exists':
        30710,
        'Authentication failed':
        30711,
        'Video with an account needed':
        30712,
        'Geo-blocked video':
        30713,
        'Search videos':
        30714,
        'Search programs':
        30715,
        'Video stream is not available':
        30716,
        'All programs':
        30717,

        # Other
        'drm_notification':
        30702,
        'choose_video_quality':
        30709,
        'No videos found':
        30718,
        'Inputstream Adaptive is not enable':
        30719,
        'Kodi 17.6 or > is required':
        30720,
        'TV guide':
        30722,
        'An error occurred while getting TV guide':
        30723,

        # Favourites
        'Add to add-on favourites':
        30800,
        'Favorite name':
        30801,
        'Remove':
        30802,
        'favourites':
        30803,
        'Rename':
        30804,

        # HTTP codes
        'HTTP Error code':
        30890,

        'http_code_500':
        30891,

        'http_code_401':
        30892,

        'http_code_403':
        30893,

        'http_code_402':
        30894,

        'http_code_404':
        30895,

        # Belgium channels / live TV
        'auvio':
        'RTBF Auvio',
        'laune':
        'La Une',
        'ladeux':
        'La Deux',
        'latrois':
        'La Trois',
        'brf':
        'BRF Mediathek',
        'rtl_tvi':
        'RTL-TVI',
        'plug_rtl':
        'PLUG RTL',
        'club_rtl':
        'CLUB RTL',
        'vrt':
        'VRT NU',
        'telemb':
        'Télé MB',
        'rtc':
        'RTC Télé Liège',
        'tvlux':
        'TV Lux',
        'contact':
        'Contact',
        'bel_rtl':
        'BEL RTL',
        'rtl_info':
        'RTL INFO',
        'bx1':
        'BX1',
        'een':
        'Één',
        'canvas':
        'Canvas',
        'ketnet':
        'Ketnet',
        'nrjhitstvbe':
        'NRJ Hits TV',
        'rtl_sport':
        'RTL Sport',
        'tvcom':
        'TV Com',
        'canalc':
        'Canal C',
        'abxplore':
        'ABXPLORE',
        'ab3':
        'AB3',
        'ln24':
        'LN24',

        # Canadian channels / live TV
        'tv5unis':
        'TV5 Unis',
        'telequebec':
        'Télé-Québec',
        'tva':
        'TVA',
        'icitele':
        'ICI Télé (' +
        utils.ensure_unicode(Script.setting['icitele.language']) + ')',
        'ntvca':
        'NTV',
        'icitoutv':
        'ICI Tou.tv',
        'telemag':
        'Télé-Mag',
        'noovo':
        'NOOVO',
        'cbc':
        'CBC (' +
        utils.ensure_unicode(Script.setting['cbc.language']) + ')',
        'vtele':
        'V Télé',
        'lcn':
        'LCN',
        'yoopa':
        'Yoopa',

        # Switzerland channels / live TV
        'rts':
        'RTS',
        'rsi':
        'RSI',
        'srf':
        'SRF',
        'rtr':
        'RTR',
        'swissinfo':
        'SWISSINFO',
        'rougetv':
        'Rouge TV',
        'tvm3':
        'TVM3',
        'becurioustv':
        'BeCurious TV',
        'rtsun':
        'RTS Un',
        'rtsdeux':
        'RTS Deux',
        'rtsinfo':
        'RTS Info',
        'rtscouleur3':
        'RTS Couleur 3',
        'rsila1':
        'RSI La 1',
        'rsila2':
        'RSI La 2',
        'srf1':
        'SRF 1',
        'srfinfo':
        'SRF Info',
        'srfzwei':
        'SRF Zwei',
        'rtraufsrf1':
        'RTR auf SRF 1',
        'rtraufsrf2':
        'RTR auf SRF 2',
        'rtraufsrfinfo':
        'RTR auf SRF Info',
        'teleticino':
        'Teleticino',
        'lemanbleu':
        'Léman Bleu',
        'telem1':
        'Tele M1',

        # French channels / live TV
        'tf1':
        'TF1',
        'france-2':
        'France 2',
        'france-3':
        'France 3',
        'canalplus':
        'Canal +',
        'france-5':
        'France 5',
        'm6':
        'M6',
        'c8':
        'C8',
        'w9':
        'W9',
        'tmc':
        'TMC',
        'tfx':
        'TFX',
        'nrj12':
        'NRJ 12',
        'france-4':
        'France 4',
        'bfmtv':
        'BFM TV',
        'bfmparis':
        'BFM Paris',
        'cnews':
        'CNews',
        'cstar':
        'CStar',
        'gulli':
        'Gulli',
        'france-o':
        'France Ô',
        'tf1-series-films':
        'TF1 Séries Films',
        'lequipe':
        'L\'Équipe',
        '6ter':
        '6ter',
        'rmcstory':
        'RMC Story',
        'cherie25':
        'Chérie 25',
        'la_1ere':
        'La 1ère (' + utils.ensure_unicode(Script.setting['la_1ere.language']) +
        ')',
        'franceinfo':
        'France Info',
        'bfmbusiness':
        'BFM Business',
        'rmc':
        'RMC',
        '01net':
        '01Net TV',
        'tfou':
        'Tfou (MYTF1)',
        'lci':
        'LCI',
        'lcp':
        'LCP Assemblée Nationale',
        'rmcdecouverte':
        'RMC Découverte',
        'fun_radio':
        'Fun Radio',
        'publicsenat':
        'Public Sénat',
        'france3regions':
        'France 3 Régions (' +
        utils.ensure_unicode(Script.setting['france3regions.language']) + ')',
        'francetvsport':
        'France TV Sport (francetv)',
        'histoire':
        'Histoire',
        'tvbreizh':
        'TV Breizh',
        'ushuaiatv':
        'Ushuaïa TV',
        'seasons':
        'Seasons',
        'comedie':
        'Comédie +',
        'les-chaines-planete':
        'Les chaînes planètes +',
        'golfplus':
        'Golf +',
        'cineplus':
        'Ciné +',
        'infosportplus':
        'INFOSPORT+',
        'gameone':
        'Game One',
        'lumni':
        'Lumni (francetv)',
        'gong':
        'Gong',
        'onzeo':
        'Onzéo',
        'melodytv':
        'Melody TV',
        'slash':
        'France tv slash',
        'polar-plus':
        'Polar+',
        'francetvspectaclesetculture':
        'Spectacles et Culture (francetv)',
        'kto':
        'KTO',
        'antennereunion':
        'Antenne Réunion',
        'viaoccitanie':
        'viàOccitanie',
        'ouatchtv':
        'Ouatch TV',
        'canal10':
        'Canal 10',
        'rtl2':
        'RTL 2',
        'lachainemeteo':
        'La Chaîne Météo',
        'mb':
        'M6 Boutique',
        'j_one':
        'J-One',
        'viaatv':
        'viàATV',
        'viagrandparis':
        'viàGrandParis',
        'via93':
        'vià93',
        'jack':
        'Jack (mycanal)',
        'caledonia':
        'Caledonia',
        'tebeo':
        'Tébéo',
        'vialmtv':
        'viàLMTv Sarthe',
        'viamirabelle':
        'viàMirabelle',
        'viavosges':
        'viàVosges',
        'tl7':
        'Télévision Loire 7',
        'luckyjack':
        'Lucky Jack',
        'mblivetv':
        'Mont Blanc Live TV',
        'tv8montblanc':
        '8 Mont-Blanc',
        'luxetv':
        'Luxe.TV',
        'alsace20':
        'Alsace 20',
        'tvpifr':
        'TVPI télévision d\'ici',
        'cliquetv':
        'Clique TV',
        'piwiplus':
        'Piwi +',
        'teletoonplus':
        'TéléToon +',
        'paramountchannel_fr':
        'Paramount Channel (FR)',
        'mtv_fr':
        'MTV (FR)',
        'idf1':
        'IDF 1',
        'azurtv':
        'Azur TV',
        'biptv':
        'BIP TV',
        'bfmlille':
        'BFM Lille',
        'bfmgrandlittoral':
        'BFM Littoral',
        'lachainenormande':
        'La Chaine Normande',
        'sportenfrance':
        'Sport en France',
        'provenceazurtv':
        'Provence Azur TV',
        'tebesud':
        'TébéSud',
        'viamatele':
        'viàMaTélé',
        'telegrenoble':
        'TéléGrenoble',
        'telenantes':
        'TéléNantes',
        'bfmlyon':
        'BFM Lyon',
        'tlc':
        'TLC',
        'tvvendee':
        'TV Vendée',
        'tv7bordeaux':
        'TV7 Bordeaux',
        'tvt':
        'TVT Val de Loire',
        'tvr':
        'TVR',
        'weo':
        'Wéo TV',
        'dicitv':
        'DiCi TV',
        'franceinter':
        'France Inter',
        'enfants':
        'Okoo (France TV)',
        'rtl':
        'RTL',
        'courses':
        'M6 Courses (6play)',
        'europe1':
        'Europe 1',
        '100foot':
        '100% Foot (6play)',

        # Japan channels / live TV
        'nhknews':
        'NHK ニュース',
        'nhklifestyle':
        'NHKらいふ',
        'tbsnews':
        'TBS ニュース',
        'ntv':
        '日テレ',
        'ex':
        'テレビ朝日',
        'tbs':
        'TBSテレビ',
        'tx':
        'テレビ東京',
        # 'cx': 'フジテレビ', (Protected by DRM)
        'mbs':
        'MBSテレビ',
        'abc':
        '朝日放送株式会社',
        'ytv':
        '読売テレビ',
        'ntvnews24':
        '日テレ News24',
        'japanetshoppingdx':
        'ジャパネットチャンネルDX',
        'ktv':
        '関西テレビ',
        'weathernewsjp':
        '株式会社ウェザーニューズ',

        # United Kingdom channels / live TV
        'blaze':
        'Blaze',
        'dave':
        'Dave',
        'yesterday':
        'Yesterday',
        'drama':
        'Drama',
        'skynews':
        'Sky News',
        'skysports':
        'Sky Sports',
        'stv':
        'STV',
        'questod':
        'Quest OD',
        'questred':
        'Quest RED',
        'questtv':
        'Quest TV',
        'kerrang':
        'Kerrang',
        'magic':
        'Magic',
        'kiss':
        'Kiss',
        'the-box':
        'The Box',
        'box-upfront':
        'Box Upfront',
        'box-hits':
        'Box Hits',
        'uktvplay':
        'UKTV Play',
        'fiveusa':
        '5USA',
        'bristoltv':
        'Bristol TV',
        'freesports':
        'Free Sports',
        'stv_plusone':
        'STV+1',
        'edgesport':
        'EDGE Sport',

        # International channels / live TV
        'tv5mondeafrique':
        'TV5Monde Afrique',
        'arte':
        'Arte (' + Script.setting['arte.language'] + ')',
        'euronews':
        'Euronews (' + Script.setting['euronews.language'] + ')',
        'france24':
        'France 24 (' + Script.setting['france24.language'] + ')',
        'nhkworld':
        'NHK World (' + Script.setting['nhkworld.language'] + ')',
        'tv5monde':
        'TV5Monde',
        'tivi5monde':
        'Tivi 5Monde',
        'bvn':
        'BVN',
        'icitelevision':
        'ICI Télévision',
        'arirang':
        'Arirang (아리랑)',
        'dw':
        'DW (' + Script.setting['dw.language'] + ')',
        'beinsports':
        'Bein Sports',
        'qvc':
        'QVC (' + Script.setting['qvc.language'] + ')',
        'icirdi':
        'ICI RDI',
        'cgtn':
        'CGTN (' + Script.setting['cgtn.language'] + ')',
        'cgtndocumentary':
        'CGTN Documentary',
        'afriquemedia':
        'Afrique Media',
        'tv5mondefbs':
        'TV5Monde France Belgique Suisse',
        'tv5mondeinfo':
        'TV5Monde Info',
        'channelnewsasia':
        'Channel NewsAsia',
        'rt':
        'RT (' + Script.setting['rt.language'] + ')',
        'africa24':
        'Africa 24',

        # United State of America channels / live TV
        'cbsnews':
        'CBS News',
        'tbd':
        'TBD',
        'nycmedia':
        'NYC Media',
        'abcnews':
        'ABC News',
        'pbskids':
        'PBS Kids',

        # Poland channels / live TV
        'tvp':
        'TVP',
        'tvp3':
        'TVP 3 (' + utils.ensure_unicode(Script.setting['tvp3.language']) + ')',
        'tvpinfo':
        'TVP Info',
        'tvppolonia':
        'TVP Polonia',
        'tvppolandin':
        'TVP Poland IN',

        # Spanish channels / live TV
        'telecinco':
        'Telecinco',
        'cuatro':
        'Cuatro',
        'fdf':
        'Factoria de Ficcion',
        'boing':
        'Boing',
        'energy':
        'Energy TV',
        'divinity':
        'Divinity',
        'bemad':
        'Be Mad',
        'realmadridtv':
        'Realmadrid TV (' + Script.setting['realmadridtv.language'] + ')',
        'paramountchannel_es':
        'Paramount Channel (ES)',

        # Tunisia channels / live TV
        'watania1':
        'التلفزة التونسية الوطنية 1',
        'watania2':
        'التلفزة التونسية الوطنية 2',
        'nessma':
        'نسمة تي في',

        # Italian channels / live TV
        'la7':
        'La7',
        'rainews24':
        'Rai News 24',
        'rai1':
        'Rai 1',
        'rai2':
        'Rai 2',
        'rai3':
        'Rai 3',
        'rai4':
        'Rai 4',
        'rai5':
        'Rai 5',
        'raisportpiuhd':
        'Rai Sport',
        'raimovie':
        'Rai Movie',
        'raipremium':
        'Rai Premium',
        'raiyoyo':
        'Rai Yoyo',
        'raigulp':
        'Rai Gulp',
        'raistoria':
        'Rai Storia',
        'raiscuola':
        'Rai Scuola',
        'la7d':
        'La7d',
        'raiplay':
        'Rai Play',
        'paramountchannel_it':
        'Paramount Channel (IT)',

        # Netherlands channels / live TV
        'npo-1':
        'NPO 1',
        'npo-2':
        'NPO 2',
        'npo-zapp':
        'NPO Zapp',
        'npo-1-extra':
        'NPO 1 Extra',
        'npo-2-extra':
        'NPO 2 Extra',
        'npo-zappelin-extra':
        'NPO Zappelin Extra',
        'npo-nieuws':
        'NPO Nieuws',
        'npo-politiek':
        'NPO Politiek',
        'npo-start':
        'NPO Start',
        'at5':
        'AT5',

        # Chinese channels / live TV
        'cctv1':
        'CCTV-1 综合',
        'cctv2':
        'CCTV-2 财经',
        'cctv3':
        'CCTV-3 综艺',
        'cctv4':
        'CCTV-4 中文国际（亚）',
        'cctveurope':
        'CCTV-4 中文国际（欧）',
        'cctvamerica':
        'CCTV-4 中文国际（美）',
        'cctv5':
        'CCTV-5 体育',
        'cctv5plus':
        'CCTV-5+ 体育赛事',
        'cctv6':
        'CCTV-6 电影',
        'cctv7':
        'CCTV-7 军事农业',
        'cctv8':
        'CCTV-8 电视剧',
        'cctvjilu':
        'CCTV-9 纪录',
        'cctv10':
        'CCTV-10 科教',
        'cctv11':
        'CCTV-11 戏曲',
        'cctv12':
        'CCTV-12 社会与法',
        'cctv13':
        'CCTV-13 新闻',
        'cctvchild':
        'CCTV-14 少儿',
        'cctv15':
        'CCTV-15 音乐',

        # Cameroon channels / live TV
        'crtv':
        'CRTV',
        'crtvnews':
        'CRTV News',

        # Websites
        'allocine':
        'Allociné',
        'tetesaclaques':
        'Au pays des Têtes à claques',
        'taratata':
        'Taratata',
        'noob':
        'Noob TV',
        'culturepub':
        'Culturepub',
        'autoplus':
        'Auto Plus',
        'notrehistoirech':
        'Notre Histoire',
        '30millionsdamis':
        '30 Millions d\'Amis',
        'elle':
        'Elle',
        'nytimes':
        'New York Times',
        'fosdem':
        'Fosdem',
        'ina':
        'Ina',
        'onf':
        'Office National du Film du Canada',
        'nfb':
        'National Film Board Of Canada',
        'marmiton':
        'Marmiton',
        'lesargonautes':
        'Les Argonautes',
        'nationalfff':
        'National FFF',
        'philharmoniedeparis':
        'Philharmonie de Paris'
    }

    s['labels'] = LABELS

    return LABELS


LABELS = s['labels'] if 'labels' in s else save_labels_in_mem_storage()

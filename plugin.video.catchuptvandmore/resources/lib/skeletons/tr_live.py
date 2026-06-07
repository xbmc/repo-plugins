# -*- coding: utf-8 -*-
# Copyright: (c) 2022, itasli
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

# The following dictionaries describe
# the addon's tree architecture.
# * Key: item id
# * Value: item infos
#     - route (folder)/resolver (playable URL): Callback function to run once this item is selected
#     - thumb: Item thumb path relative to "media" folder
#     - fanart: Item fanart path relative to "media" folder

root = 'live_tv'

menu = {
    '24tv': {
        'resolver': '/resources/lib/channels/tr/24tv:get_live_url',
        'label': '24 TV',
        'thumb': 'channels/tr/24.png',
        'fanart': 'channels/tr/24_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    '360tv': {
        'resolver': '/resources/lib/channels/tr/360tv:get_live_url',
        'label': '360 TV',
        'thumb': 'channels/tr/360.png',
        'fanart': 'channels/tr/360_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'a2tv': {
        'resolver': '/resources/lib/channels/tr/turkuvaz:get_live_url',
        'label': 'a2',
        'thumb': 'channels/tr/a2.png',
        'fanart': 'channels/tr/a2_fanart.jpg',
        'enabled': True,
        'order': 3
    },
    'ahaberhd': {
        'resolver': '/resources/lib/channels/tr/turkuvaz:get_live_url',
        'label': 'A Haber',
        'thumb': 'channels/tr/ahaber.png',
        'fanart': 'channels/tr/ahaber_fanart.jpg',
        'enabled': True,
        'order': 4
    },
    'aparahd': {
        'resolver': '/resources/lib/channels/tr/turkuvaz:get_live_url',
        'label': 'A Para',
        'thumb': 'channels/tr/apara.png',
        'fanart': 'channels/tr/apara_fanart.jpg',
        'enabled': True,
        'order': 5
    },
    'asporhd': {
        'resolver': '/resources/lib/channels/tr/turkuvaz:get_live_url',
        'label': 'A Spor',
        'thumb': 'channels/tr/aspor.png',
        'fanart': 'channels/tr/aspor_fanart.jpg',
        'enabled': True,
        'order': 6
    },
    'atvhd': {
        'resolver': '/resources/lib/channels/tr/turkuvaz:get_live_url',
        'label': 'atv',
        'thumb': 'channels/tr/atv.png',
        'fanart': 'channels/tr/atv_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    'atvavrupa': {
        'resolver': '/resources/lib/channels/tr/turkuvaz:get_live_url',
        'label': 'atv Avrupa',
        'thumb': 'channels/tr/atvavrupa.png',
        'fanart': 'channels/tr/atvavrupa_fanart.jpg',
        'enabled': True,
        'order': 8
    },
    'beyaz': {
        'resolver': '/resources/lib/channels/tr/beyaz:get_live_url',
        'label': 'Beyaz TV',
        'thumb': 'channels/tr/beyaz.png',
        'fanart': 'channels/tr/beyaz_fanart.jpg',
        'enabled': True,
        'order': 9
    },
    'bloomberght': {
        'resolver': '/resources/lib/channels/tr/cinergroup:get_live_url',
        'label': 'Bloomberg HT',
        'thumb': 'channels/tr/bloomberght.png',
        'fanart': 'channels/tr/bloomberght_fanart.jpg',
        'enabled': True,
        'order': 10
    },
    'cine5': {
        'resolver': '/resources/lib/channels/tr/cine5:get_live_url',
        'label': 'Cine5',
        'thumb': 'channels/tr/cine5.png',
        'fanart': 'channels/tr/cine5_fanart.jpg',
        'enabled': True,
        'order': 11
    },
    'cnnturk': {
        'resolver': '/resources/lib/channels/tr/cnnturk:get_live_url',
        'label': 'CNN TURK',
        'thumb': 'channels/tr/cnnturk.png',
        'fanart': 'channels/tr/cnnturk_fanart.jpg',
        'enabled': True,
        'order': 12
    },
    'dmax': {
        'resolver': '/resources/lib/channels/tr/dogus:get_live_url',
        'label': 'DMAX',
        'thumb': 'channels/tr/dmax.png',
        'fanart': 'channels/tr/dmax_fanart.jpg',
        'enabled': True,
        'order': 13
    },
    'eurod': {
        'resolver': '/resources/lib/channels/tr/dogan:get_live_url',
        'label': 'Euro D',
        'thumb': 'channels/tr/eurod.png',
        'fanart': 'channels/tr/eurod_fanart.jpg',
        'enabled': True,
        'order': 14
    },
    'eurostar': {
        'resolver': '/resources/lib/channels/tr/eurostar:get_live_url',
        'label': 'Euro Star',
        'thumb': 'channels/tr/eurostar.png',
        'fanart': 'channels/tr/eurostar_fanart.jpg',
        'enabled': True,
        'order': 15
    },
    'fox': {
        'resolver': '/resources/lib/channels/tr/fox:get_live_url',
        'label': 'FOX',
        'thumb': 'channels/tr/fox.png',
        'fanart': 'channels/tr/fox_fanart.jpg',
        'enabled': True,
        'order': 16
    },
    'haberglobal': {
        'resolver': '/resources/lib/channels/tr/haberglobal:get_live_url',
        'label': 'Haber Global',
        'thumb': 'channels/tr/haberglobal.png',
        'fanart': 'channels/tr/haberglobal_fanart.jpg',
        'enabled': True,
        'order': 17
    },
    'haberturk': {
        'resolver': '/resources/lib/channels/tr/cinergroup:get_live_url',
        'label': 'Haber Türk',
        'thumb': 'channels/tr/haberturk.png',
        'fanart': 'channels/tr/haberturk_fanart.jpg',
        'enabled': True,
        'order': 18
    },
    'kanal7': {
        'resolver': '/resources/lib/channels/tr/kanal7:get_live_url',
        'label': 'Kanal 7',
        'thumb': 'channels/tr/kanal7.png',
        'fanart': 'channels/tr/kanal7_fanart.jpg',
        'enabled': True,
        'order': 19
    },
    'kanal7avrupa': {
        'resolver': '/resources/lib/channels/tr/kanal7:get_live_url',
        'label': 'Kanal 7 Avrupa',
        'thumb': 'channels/tr/kanal7avrupa.png',
        'fanart': 'channels/tr/kanal7avrupa_fanart.jpg',
        'enabled': True,
        'order': 20
    },
    'kanald': {
        'resolver': '/resources/lib/channels/tr/dogan:get_live_url',
        'label': 'Kanal D',
        'thumb': 'channels/tr/kanald.png',
        'fanart': 'channels/tr/kanald_fanart.jpg',
        'enabled': True,
        'order': 21
    },
    'minikagococuk': {
        'resolver': '/resources/lib/channels/tr/turkuvaz:get_live_url',
        'label': 'Minika Çocuk',
        'thumb': 'channels/tr/minikacocuk.png',
        'fanart': 'channels/tr/minikacocuk_fanart.jpg',
        'enabled': True,
        'order': 22
    },
    'minikago': {
        'resolver': '/resources/lib/channels/tr/turkuvaz:get_live_url',
        'label': 'Minika Go',
        'thumb': 'channels/tr/minikago.png',
        'fanart': 'channels/tr/minikago_fanart.jpg',
        'enabled': True,
        'order': 23
    },
    'ntv': {
        'resolver': '/resources/lib/channels/tr/ntv:get_live_url',
        'label': 'NTV',
        'thumb': 'channels/tr/ntv.png',
        'fanart': 'channels/tr/ntv_fanart.jpg',
        'enabled': True,
        'order': 24
    },
    'showtv': {
        'resolver': '/resources/lib/channels/tr/cinergroup:get_live_url',
        'label': 'Show TV',
        'thumb': 'channels/tr/show.png',
        'fanart': 'channels/tr/show_fanart.jpg',
        'enabled': True,
        'order': 25
    },
    'showmax': {
        'resolver': '/resources/lib/channels/tr/cinergroup:get_live_url',
        'label': 'Show MAX',
        'thumb': 'channels/tr/showmax.png',
        'fanart': 'channels/tr/showmax_fanart.jpg',
        'enabled': True,
        'order': 26
    },
    'showturk': {
        'resolver': '/resources/lib/channels/tr/cinergroup:get_live_url',
        'label': 'Show Türk',
        'thumb': 'channels/tr/showturk.png',
        'fanart': 'channels/tr/showturk_fanart.jpg',
        'enabled': True,
        'order': 27
    },
    'star': {
        'resolver': '/resources/lib/channels/tr/star:get_live_url',
        'label': 'Star TV',
        'thumb': 'channels/tr/star.png',
        'fanart': 'channels/tr/star_fanart.jpg',
        'enabled': True,
        'order': 28
    },
    'tele1': {
        'resolver': '/resources/lib/channels/tr/tele1:get_live_url',
        'label': 'Tele 1',
        'thumb': 'channels/tr/tele1.png',
        'fanart': 'channels/tr/tele1_fanart.jpg',
        'enabled': True,
        'order': 29
    },
    'teve2': {
        'resolver': '/resources/lib/channels/tr/teve2:get_live_url',
        'label': 'Teve2',
        'thumb': 'channels/tr/teve2.png',
        'fanart': 'channels/tr/teve2_fanart.jpg',
        'enabled': True,
        'order': 30
    },
    'tlc': {
        'resolver': '/resources/lib/channels/tr/dogus:get_live_url',
        'label': 'TLC',
        'thumb': 'channels/tr/tlc.png',
        'fanart': 'channels/tr/tlc_fanart.jpg',
        'enabled': True,
        'order': 31
    },
    'trt1': {
        'resolver': '/resources/lib/channels/tr/trt:get_live_url',
        'label': 'TRT 1',
        'thumb': 'channels/tr/trt1.png',
        'fanart': 'channels/tr/trt1_fanart.jpg',
        'enabled': True,
        'order': 32
    },
    'trt2': {
        'resolver': '/resources/lib/channels/tr/trt:get_live_url',
        'label': 'TRT 2',
        'thumb': 'channels/tr/trt2.png',
        'fanart': 'channels/tr/trt2_fanart.jpg',
        'enabled': True,
        'order': 33
    },
    'trtavaz': {
        'resolver': '/resources/lib/channels/tr/trt:get_live_url',
        'label': 'TRT Avaz',
        'thumb': 'channels/tr/trtavaz.png',
        'fanart': 'channels/tr/trtavaz_fanart.jpg',
        'enabled': True,
        'order': 34
    },
    'trtbelgesel': {
        'resolver': '/resources/lib/channels/tr/trt:get_live_url',
        'label': 'TRT Belgesel',
        'thumb': 'channels/tr/trtbelgesel.png',
        'fanart': 'channels/tr/trtbelgesel_fanart.jpg',
        'enabled': True,
        'order': 35
    },
    'trtcocuk': {
        'resolver': '/resources/lib/channels/tr/trt:get_live_url',
        'label': 'TRT Çocuk',
        'thumb': 'channels/tr/trtcocuk.png',
        'fanart': 'channels/tr/trtcocuk_fanart.jpg',
        'enabled': True,
        'order': 36
    },
    'trthaber': {
        'resolver': '/resources/lib/channels/tr/trt:get_live_url',
        'label': 'TRT Haber',
        'thumb': 'channels/tr/trthaber.png',
        'fanart': 'channels/tr/trthaber_fanart.jpg',
        'enabled': True,
        'order': 37
    },
    'tv5': {
        'resolver': '/resources/lib/channels/tr/tv5:get_live_url',
        'label': 'TV 5',
        'thumb': 'channels/tr/tv5.png',
        'fanart': 'channels/tr/tv5_fanart.jpg',
        'enabled': True,
        'order': 38
    },
    'tv8': {
        'resolver': '/resources/lib/channels/tr/tv8:get_live_url',
        'label': 'TV 8',
        'thumb': 'channels/tr/tv8.png',
        'fanart': 'channels/tr/tv8_fanart.jpg',
        'enabled': True,
        'order': 39
    },
    'tv8int': {
        'resolver': '/resources/lib/channels/tr/tv8:get_live_url',
        'label': 'TV 8 Int',
        'thumb': 'channels/tr/tv8int.png',
        'fanart': 'channels/tr/tv8int_fanart.jpg',
        'enabled': True,
        'order': 40
    },
    'tvnet': {
        'resolver': '/resources/lib/channels/tr/tvnet:get_live_url',
        'label': 'Tvnet',
        'thumb': 'channels/tr/tvnet.jpg',
        'fanart': 'channels/tr/tvnet_fanart.jpg',
        'enabled': True,
        'order': 41
    },
    'ulke': {
        'resolver': '/resources/lib/channels/tr/ulke:get_live_url',
        'label': 'Ulke TV',
        'thumb': 'channels/tr/ulke.png',
        'fanart': 'channels/tr/ulke_fanart.jpg',
        'enabled': True,
        'order': 42
    },
    'vavtv': {
        'resolver': '/resources/lib/channels/tr/turkuvaz:get_live_url',
        'label': 'Vav TV',
        'thumb': 'channels/tr/vav.png',
        'fanart': 'channels/tr/vav_fanart.jpg',
        'enabled': True,
        'order': 43
    },
}

# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
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
    'telequebec': {
        'resolver': '/resources/lib/channels/ca/telequebec:get_live_url',
        'label': 'Télé-Québec',
        'thumb': 'channels/ca/telequebec.png',
        'fanart': 'channels/ca/telequebec_fanart.jpg',
        'xmltv_id': 'I63040.json.schedulesdirect.org',
        'enabled': True,
        'order': 4
    },
    'tva': {
        'resolver': '/resources/lib/channels/ca/tva:get_live_url',
        'label': 'TVA',
        'thumb': 'channels/ca/tva.png',
        'fanart': 'channels/ca/tva_fanart.jpg',
        'xmltv_id': 'I72755.json.schedulesdirect.org',
        'enabled': True,
        'order': 5
    },
    'icitele': {
        'resolver': '/resources/lib/channels/ca/icitele:get_live_url',
        'label': 'ICI Télé',
        'thumb': 'channels/ca/icitele.png',
        'fanart': 'channels/ca/icitele_fanart.jpg',
        'available_languages': {
            'Vancouver': {'xmltv_id': 'I72984.json.schedulesdirect.org'},
            'Regina': {'xmltv_id': 'I15989.json.schedulesdirect.org'},
            'Toronto': {'xmltv_id': 'I10090.json.schedulesdirect.org'},
            'Edmonton': {'xmltv_id': 'I72972.json.schedulesdirect.org'},
            'Rimouski': {'xmltv_id': 'I18291.json.schedulesdirect.org'},
            'Québec': {'xmltv_id': 'I49584.json.schedulesdirect.org'},
            'Winnipeg': {'xmltv_id': 'I16731.json.schedulesdirect.org'},
            'Moncton': {'xmltv_id': 'I72974.json.schedulesdirect.org'},
            'Ottawa': {'xmltv_id': 'I52235.json.schedulesdirect.org'},
            'Sherbrooke': {'xmltv_id': 'I72980.json.schedulesdirect.org'},
            'Trois-Rivières': {'xmltv_id': 'I16831.json.schedulesdirect.org'},
            'Montréal': {'xmltv_id': 'I45867.json.schedulesdirect.org'}
        },
        'enabled': True,
        'order': 6
    },
    'icirdi': {
        'resolver': '/resources/lib/channels/ca/icirdi:get_live_url',
        'label': 'ICI RDI',
        'thumb': 'channels/ca/icirdi.png',
        'fanart': 'channels/ca/icirdi_fanart.jpg',
        'xmltv_id': 'I60327.json.schedulesdirect.org',
        'enabled': True,
        'order': 16
    },
    'ntvca': {
        'resolver': '/resources/lib/channels/ca/ntvca:get_live_url',
        'label': 'NTV',
        'thumb': 'channels/ca/ntvca.png',
        'fanart': 'channels/ca/ntvca_fanart.jpg',
        'xmltv_id': 'I14926.json.schedulesdirect.org',
        'enabled': True,
        'order': 7
    },
    'telemag': {
        'resolver': '/resources/lib/channels/ca/telemag:get_live_url',
        'label': 'Télé-Mag',
        'thumb': 'channels/ca/telemag.png',
        'fanart': 'channels/ca/telemag_fanart.jpg',
        'xmltv_id': 'I72595.json.schedulesdirect.org',
        'enabled': True,
        'order': 9
    },
    'noovo': {
        'resolver': '/resources/lib/channels/ca/noovo:get_live_url',
        'label': 'Noovo',
        'thumb': 'channels/ca/noovo.png',
        'fanart': 'channels/ca/noovo_fanart.jpg',
        'xmltv_id': 'I58688.json.schedulesdirect.org',
        'enabled': True,
        'order': 10
    },
    'cbc': {
        'resolver': '/resources/lib/channels/ca/cbc:get_live_url',
        'label': 'CBC',
        'thumb': 'channels/ca/cbc.png',
        'fanart': 'channels/ca/cbc_fanart.jpg',
        'available_languages': {
            'Ottawa': {'xmltv_id': 'I58494.json.schedulesdirect.org'},
            'Montreal': {'xmltv_id': 'I53502.json.schedulesdirect.org'},
            'Charlottetown': {'xmltv_id': 'I17398.json.schedulesdirect.org'},
            'Fredericton': {'xmltv_id': 'I16261.json.schedulesdirect.org'},
            'Halifax': {'xmltv_id': 'I72723.json.schedulesdirect.org'},
            'Windsor': {'xmltv_id': 'I10088.json.schedulesdirect.org'},
            'Yellowknife': {'xmltv_id': 'I17388.json.schedulesdirect.org'},
            'Winnipeg': {'xmltv_id': 'I72940.json.schedulesdirect.org'},
            'Regina': {'xmltv_id': 'I16001.json.schedulesdirect.org'},
            'Calgary': {'xmltv_id': 'I71729.json.schedulesdirect.org'},
            'Edmonton': {'xmltv_id': 'I71733.json.schedulesdirect.org'},
            'Vancouver': {'xmltv_id': 'I51981.json.schedulesdirect.org'},
            'Toronto': {'xmltv_id': 'I46245.json.schedulesdirect.org'},
            'St. John\'s': {'xmltv_id': 'I17400.json.schedulesdirect.org'}
        },
        'enabled': True,
        'order': 11
    },
    'lcn': {
        'resolver': '/resources/lib/channels/ca/tva:get_live_url',
        'label': 'LCN',
        'thumb': 'channels/ca/lcn.png',
        'fanart': 'channels/ca/lcn_fanart.jpg',
        'xmltv_id': 'I67231.json.schedulesdirect.org',
        'enabled': False,
        'order': 12
    },
    'yoopa': {
        'resolver': '/resources/lib/channels/ca/tva:get_live_url',
        'label': 'Yoopa',
        'thumb': 'channels/ca/yoopa.png',
        'fanart': 'channels/ca/yoopa_fanart.jpg',
        'xmltv_id': 'I67449.json.schedulesdirect.org',
        'enabled': False,
        'order': 13
    }
}

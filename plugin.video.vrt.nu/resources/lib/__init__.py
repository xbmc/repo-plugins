# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals

# Fallback list of categories so we don't depend on web scraping only
CATEGORIES = [
    dict(name='Audiodescriptie', id='met-audiodescriptie'),
    dict(name='Cultuur', id='cultuur'),
    dict(name='Docu', id='docu'),
    dict(name='Entertainment', id='entertainment'),
    dict(name='Films', id='films'),
    dict(name='Human interest', id='human-interest'),
    dict(name='Humor', id='humor'),
    dict(name='Kinderen', id='voor-kinderen'),
    dict(name='Koken', id='koken'),
    dict(name='Lifestyle', id='lifestyle'),
    dict(name='Muziek', id='muziek'),
    dict(name='Nieuws en actua', id='nieuws-en-actua'),
    dict(name='Series', id='series'),
    dict(name='Sport', id='sport'),
    dict(name='Talkshows', id='talkshows'),
    dict(name='Vlaamse Gebarentaal', id='met-gebarentaal'),
    dict(name='Wetenschap en natuur', id='wetenschap-en-natuur'),
]

CHANNELS = [
    dict(
        id='O8',
        name='een',
        label='Eén',
        studio='Een',
        live_stream='https://www.vrt.be/vrtnu/kanalen/een/',
        live_stream_id='vualto_een_geo',
    ),
    dict(
        id='1H',
        name='canvas',
        label='Canvas',
        studio='Canvas',
        live_stream='https://www.vrt.be/vrtnu/kanalen/canvas/',
        live_stream_id='vualto_canvas_geo',
    ),
    dict(
        id='O9',
        name='ketnet',
        label='Ketnet',
        studio='Ketnet',
        live_stream='https://www.vrt.be/vrtnu/kanalen/ketnet/',
        live_stream_id='vualto_ketnet_geo',
    ),
    dict(
        id='1H',
        name='ketnet-jr',
        label='Ketnet Junior',
        studio='Ketnet Junior',
        live_stream_id='ketnet_jr',
    ),
    dict(
        id='12',
        name='sporza',
        label='Sporza',
        studio='Sporza',
        live_stream_id='vualto_sporza_geo',
    ),
    dict(
        id='11',
        name='radio1',
        label='Radio 1',
        studio='Radio 1',
    ),
    dict(
        id='24',
        name='radio2',
        label='Radio 2',
        studio='Radio 2',
    ),
    dict(
        id='31',
        name='klara',
        label='Klara',
        studio='Klara',
    ),
    dict(
        id='41',
        name='stubru',
        label='Studio Brussel',
        studio='Studio Brussel',
        # live_stream='https://stubru.be/live',
        live_stream_id='vualto_stubru',
    ),
    dict(
        id='55',
        name='mnm',
        label='MNM',
        studio='MNM',
        # live_stream='https://mnm.be/kijk/live',
        live_stream_id='vualto_mnm',
    ),
    dict(
        id='',
        name='vrtnxt',
        label='VRT NXT',
        studio='VRT NXT',
    ),
    dict(
        id='13',
        name='vrtnws',
        label='VRT NWS',
        studio='VRT NWS',
        live_stream_id='vualto_nieuws',
        # live_stream_id='vualto_journaal',
    ),
]


class actions:
    ''' A list of add-on actions '''
    CLEAR_COOKIES = 'clearcookies'
    FOLLOW = 'follow'
    INSTALL_WIDEVINE = 'installwidevine'
    INVALIDATE_CACHES = 'invalidatecaches'
    LISTING_ALL_EPISODES = 'listingallepisodes'
    LISTING_AZ_TVSHOWS = 'listingaztvshows'
    LISTING_CATEGORIES = 'listingcategories'
    LISTING_CATEGORY_TVSHOWS = 'listingcategorytvshows'
    LISTING_CHANNELS = 'listingchannels'
    LISTING_EPISODES = 'listingepisodes'
    LISTING_FAVORITES = 'favorites'
    LISTING_LIVE = 'listinglive'
    LISTING_OFFLINE = 'listingoffline'
    LISTING_RECENT = 'listingrecent'
    LISTING_TVGUIDE = 'listingtvguide'
    PLAY = 'play'
    REFRESH_FAVORITES = 'refreshfavorites'
    SEARCH = 'search'
    UNFOLLOW = 'unfollow'

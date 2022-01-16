# -*- coding: utf-8 -*-
"""

    Copyright (C) 2018-2019 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmc  # pylint: disable=import-error
from six import PY3

from .constants import CONFIG
from .logger import Logger

__LOG = Logger()

STRINGS = {
    # core
    'Delete': 117,
    'Refresh': 184,
    'Subtitles': 287,
    'Audio': 292,
    'Update library': 653,
    'Mark as watched': 16103,
    'Mark as unwatched': 16104,
    # add-on
    'Confirm file delete?': 30000,
    'Delete this item? This action will delete media and associated data files.': 30001,
    'Plex Online': 30002,
    'About to install': 30003,
    'This plugin is already installed': 30004,
    'Switch Failed': 30005,
    'Sign Out': 30006,
    'To sign out you must be logged in as an admin user. Switch user and try again': 30007,
    'myPlex': 30008,
    'You are currently signed into myPlex. Are you sure you want to sign out?': 30009,
    'You are not currently logged into myPlex. Continue to sign in, or cancel to return': 30011,
    'To access these screens you must be logged in as an admin user. '
    'Switch user and try again': 30012,
    'All': 30013,
    'Unwatched': 30014,
    'Recently Aired': 30015,
    'Recently Added': 30016,
    'Recently Viewed Episodes': 30017,
    'Recently Viewed Shows': 30018,
    'On Deck': 30019,
    'By Collection': 30020,
    'By First Letter': 30021,
    'By Genre': 30022,
    'By Year': 30023,
    'By Content Rating': 30024,
    'By Folder': 30025,
    'Search Shows...': 30026,
    'Search Episodes...': 30027,
    'By Album': 30029,
    'Search Artists...': 30035,
    'Search Albums...': 30036,
    'Search Tracks...': 30037,
    'Recently Released': 30040,
    'Recently Viewed': 30042,
    'By Decade': 30047,
    'By Director': 30048,
    'By Starring Actor': 30049,
    'By Country': 30050,
    'By Rating': 30052,
    'By Resolution': 30053,
    'Search...': 30056,
    'Camera Make': 30060,
    'Camera Model': 30061,
    'Aperture': 30062,
    'Shutter Speed': 30063,
    'ISO': 30064,
    'Lens': 30065,
    'Library refresh started': 30068,
    'myPlex not configured': 30069,
    'Select media to play': 30071,
    'Select subtitle': 30072,
    'Select audio': 30073,
    'Select master server': 30074,
    'Known server list': 30075,
    'Switch User': 30076,
    'Enter PIN': 30077,
    'myPlex Queue': 30080,
    'Sign In': 30081,
    'Display Servers': 30082,
    'Refresh Data': 30083,
    'Channels': 30084,
    'Playlists': 30085,
    'Play Transcoded': 30086,
    'All episodes': 30087,
    'Season': 30088,
    'Search for': 30089,
    'Unplayed': 30090,
    'Server': 30516,
    'Kids': 30589,
    'Teens': 30590,
    'Adults': 30591,
    'Manage myPlex': 30605,
    'Refresh library section': 30616,
    'Username:': 30617,
    'Password:': 30618,
    'Cancel': 30619,
    'Submit': 30620,
    'Manual': 30621,
    'Use PIN': 30622,
    'Done': 30623,
    'Unable to sign in': 30624,
    'From your computer, go to %s and enter the code below': 30625,
    'Successfully signed in': 30626,
    'Sign in not successful': 30627,
    'Email:': 30628,
    'Plex Pass:': 30629,
    'Joined:': 30630,
    'Exit': 30631,
    'Enter your myPlex details below': 30634,
    'Unknown': 30636,
    'myPlex Login': 30637,
    'Enter search term': 30638,
    'Enter value': 30639,
    'Transcode Profiles': 30641,
    'Offline': 30642,
    'Remote': 30643,
    'Nearby': 30644,
    'SSL': 30645,
    'Not Secure': 30646,
    'Certificate Verification': 30647,
    'Message': 30648,
    'blank': 30649,
    'Server Discovery': 30650,
    'Please wait...': 30651,
    'myPlex discovery...': 30652,
    'GDM discovery...': 30653,
    'User provided...': 30654,
    'Caching results...': 30655,
    'Finished': 30656,
    'Found servers:': 30657,
    'No servers found': 30658,
    'installed': 30664,
    'Movies': 30665,
    'Music': 30666,
    'TV Shows': 30667,
    'Photos': 30668,
    'Go to': 30672,
    'Delete from the playlist?': 30673,
    'Confirm playlist item delete?': 30674,
    'Delete from playlist': 30675,
    'Select playlist': 30676,
    'Add to playlist': 30677,
    'Added to the playlist': 30678,
    'Failed to add to the playlist': 30679,
    'is already in the playlist': 30680,
    'has been removed the playlist': 30681,
    'Unable to remove from the playlist': 30682,
    'From your computer, go to [B]%s[/B] and enter the following code: [B]%s[/B]': 30690,
    'Widgets': 30692,
    'Clear Caches': 30694,
    'Movies on Deck': 30697,
    'TV Shows on Deck': 30698,
    'Recently Released Movies': 30699,
    'Recently Aired TV Shows': 30700,
    'Recently Added Movies': 30701,
    'Recently Added TV Shows': 30702,
    'Companion receiver is unable to start due to a port conflict': 30704,
    'Companion receiver has started': 30705,
    'Companion receiver has been stopped': 30706,
    'Create a playlist': 30722,
    'Enter a playlist title': 30723,
    'Delete playlist': 30724,
    'Confirm playlist delete?': 30725,
    'Are you sure you want to delete this playlist?': 30726,
    'Manage Servers': 30731,
    'Set as Master': 30732,
    'Connection Test Results': 30733,
    'Add custom access url': 30738,
    'Custom access urls': 30739,
    'Edit': 30740,
    'Edit custom access url': 30741,
    'Custom': 30742,
    'All Artists': 30743,
    'All Photos': 30744,
    'All Shows': 30745,
    'All Movies': 30746,
    'Plex powered by LyricFind': 30754,
    'All_': 30756,
    'All Servers: TV Shows On Deck': 30757,
    'All Servers: Movies On Deck': 30758,
    'Recently Added Episodes': 30759,
    'All Servers: Recently Added Episodes': 30760,
    'All Servers: Recently Added Movies': 30761,
    'Composite Playlist': 30765,
    'Generate a playlist from the information below': 30766,
    'Mixed': 30767,
    'Play': 30768,
    'Item Count': 30769,
    'All Servers': 30770,
    'Shuffle': 30771,
    'Source': 30772,
    'Generating Playlist': 30774,
    'This may take a while...': 30775,
    'Retrieving server list...': 30776,
    'Retrieving server sections...': 30777,
    'Retrieving content metadata...': 30778,
    'Retrieving final sample...': 30779,
    'Adding items to playlist...': 30780,
    'Adding %s to playlist...': 30781,
    'Completed.': 30782,
    'Checking section %s on %s...': 30783,
    'Retrieving %s from %s for sample...': 30784,
    'Retrieving %s episodes for sample...': 30785,
    'Creating samples...': 30786,
    'Retrieving metadata for %s...': 30787,
    'Server(s)': 30789,
    'Combined Sections': 30790,
    'Search Movies...': 30791,
    'Library - Movie Sections': 30794,
    'Library - TV Show Sections': 30795,
    'Configured library sections have been reset': 30799,
    'Continue Watching': 30800,
    'Detect Servers': 30801,
}


def decode_utf8(string):
    try:
        return string.decode('utf-8')
    except AttributeError:
        return string


def encode_utf8(string, py2_only=True):
    if py2_only and PY3:
        return string
    return string.encode('utf-8')


def i18n(string_id):
    mapped_string_id = STRINGS.get(string_id)
    if mapped_string_id:
        string_id = mapped_string_id

    try:
        core = int(string_id) < 30000
    except ValueError:
        __LOG.debug('Failed to map translation, returning id ...')
        return string_id

    if core:
        return encode_utf8(xbmc.getLocalizedString(string_id))

    return encode_utf8(CONFIG['addon'].getLocalizedString(string_id))


def directory_item_translate(title, thumb):
    translation_map = {}

    if thumb.endswith('show.png'):
        translation_map = {
            'All Shows': 'All Shows',
            'Unplayed': 'Unplayed',
            'Unwatched': 'Unwatched',
            'Recently Aired': 'Recently Aired',
            'Recently Added': 'Recently Added',
            'Recently Viewed Episodes': 'Recently Viewed Episodes',
            'Recently Viewed Shows': 'Recently Viewed Shows',
            'On Deck': 'On Deck',
            'By Collection': 'By Collection',
            'By First Letter': 'By First Letter',
            'By Genre': 'By Genre',
            'By Year': 'By Year',
            'By Content Rating': 'By Content Rating',
            'By Folder': 'By Folder',
            'Search Shows...': 'Search Shows...',
            'Search Episodes...': 'Search Episodes...',
            'Continue Watching': 'Continue Watching',
        }

    elif thumb.endswith('artist.png'):
        translation_map = {
            'All Artists': 'All Artists',
            'By Album': 'By Album',
            'By Genre': 'By Genre',
            'By Year': 'By Year',
            'By Collection': 'By Collection',
            'Recently Added': 'Recently Added',
            'By Folder': 'By Folder',
            'Search Artists...': 'Search Artists...',
            'Search Albums...': 'Search Albums...',
            'Search Tracks...': 'Search Tracks...',
        }

    elif thumb.endswith('movie.png') or thumb.endswith('video.png'):
        translation_map = {
            'All Movies': 'All Movies',
            'Unplayed': 'Unplayed',
            'Unwatched': 'Unwatched',
            'Recently Released': 'Recently Released',
            'Recently Added': 'Recently Added',
            'Recently Viewed': 'Recently Viewed',
            'On Deck': 'On Deck',
            'By Collection': 'By Collection',
            'By Genre': 'By Genre',
            'By Year': 'By Year',
            'By Decade': 'By Decade',
            'By Director': 'By Director',
            'By Starring Actor': 'By Starring Actor',
            'By Country': 'By Country',
            'By Content Rating': 'By Content Rating',
            'By Rating': 'By Rating',
            'By Resolution': 'By Resolution',
            'By First Letter': 'By First Letter',
            'By Folder': 'By Folder',
            'Search...': 'Search...',
            'Continue Watching': 'Continue Watching',
        }
        if thumb.endswith('video.png') and title.startswith('All '):
            return i18n('All_') % title.replace('All ', '')

    elif thumb.endswith('photo.png'):
        translation_map = {
            'All Photos': 'All Photos',
            'By Year': 'By Year',
            'Recently Added': 'Recently Added',
            'Camera Make': 'Camera Make',
            'Camera Model': 'Camera Model',
            'Aperture': 'Aperture',
            'Shutter Speed': 'Shutter Speed',
            'ISO': 'ISO',
            'Lens': 'Lens',
        }

    string = translation_map.get(title)
    if string:
        return i18n(string)

    return title


def item_translate(title, source, folder):
    translated_title = title

    if folder and source in ['tvshows', 'tvseasons']:
        if title == 'All episodes':
            translated_title = i18n('All episodes')
        elif title.startswith('Season '):
            translated_title = i18n('Season') + title[6:]

    return translated_title

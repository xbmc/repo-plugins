# -*- coding: utf-8 -*-
"""
    Copyright (C) 2016-2021 Team Catch-up TV & More
    This file is part of Catch-up TV & More.
    SPDX-License-Identifier: GPL-2.0-or-later
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

# Core imports
import importlib
import json
import os
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
import socket

# Kodi imports
from codequick import Script
from kodi_six import xbmcgui

# Local imports
from resources.lib.addon_utils import get_item_label, get_item_media_path
from resources.lib.xmltv import grab_programmes

PLUGIN_KODI_PATH = "plugin://plugin.video.catchuptvandmore"

# Json file that keeps user settings concerning Kodi Live TV integration made by IPTV Manager
TV_INTEGRATION_SETTINGS_FP = os.path.join(Script.get_info('profile'), "tv_integration_settings.json")


"""Utility functions to deal with user tv integration settings

"""


def get_tv_integration_settings():
    """Get tv integration settings dict from json file

    Returns:
        dict: Tv integration settings
    """
    try:
        with open(TV_INTEGRATION_SETTINGS_FP) as f:
            settings = json.load(f)
    except Exception:
        settings = {}
    if 'enabled_channels' not in settings:
        settings['enabled_channels'] = {}
    return settings


def save_tv_integration_settings(j):
    """Save tv integration settings dict in json file

    Args:
        j (dict): Tv integration dict to save
    """
    try:
        with open(TV_INTEGRATION_SETTINGS_FP, 'w') as f:
            json.dump(j, f, indent=4)
    except Exception as e:
        Script.notify(
            Script.localize(30270),
            Script.localize(30276))
        Script.log('Failed to save TV integration settings (%s)', e, lvl=Script.ERROR)


"""Settings callback functions


"""


def get_all_live_tv_channels():
    """Explore each live_tv skeleton files to retrieve all sorted live tv channels

    Returns:
        list: Format: (coutry_order, country_id, country_label, country_infos, [channels]),
                      Channel format: (channel_order, channel_id, channel_label, channel_infos)
    """
    country_channels = []
    live_tv_dict = importlib.import_module('resources.lib.skeletons.live_tv').menu
    for country_id, country_infos in live_tv_dict.items():
        channels = []
        channels_dict = importlib.import_module('resources.lib.skeletons.' + country_id).menu
        for channel_id, channel_infos in list(channels_dict.items()):
            # If this channel is disabled --> ignore this channel
            if not channel_infos.get('enabled', False):
                continue
            # If this channel is a folder (e.g. multi live) --> ignore this channel
            if 'resolver' not in channel_infos:
                continue
            channels.append((channel_infos['order'], channel_id, get_item_label(channel_id, channel_infos), channel_infos))
        channels = sorted(channels, key=lambda x: x[2])
        country_channels.append((country_infos['order'], country_id, get_item_label(country_id, country_infos), country_infos, sorted(channels, key=lambda x: x[0])))
    return sorted(country_channels, key=lambda x: x[2])


@Script.register
def select_channels(plugin):
    """Callback function of 'Select channels to enable' setting button

    Args:
        plugin (codequick.script.Script)
    """

    # Grab all live TV channels
    country_channels = get_all_live_tv_channels()

    # Grab current user settings
    tv_integration_settings = get_tv_integration_settings()

    # Build the multi-select dialog
    options = []
    preselect = []
    selected_channels_map = []
    cnt = 0
    for (country_order, country_id, country_label, country_infos, channels) in country_channels:
        if country_id not in tv_integration_settings['enabled_channels']:
            tv_integration_settings['enabled_channels'][country_id] = {}

        for (channel_order, channel_id, channel_label, channel_infos) in channels:
            if channel_id not in tv_integration_settings['enabled_channels'][country_id]:
                tv_integration_settings['enabled_channels'][country_id][channel_id] = {'enabled': False}

            label = country_label + ' - ' + channel_label
            options.append(label)
            selected_channels_map.append((country_id, channel_id))
            if tv_integration_settings['enabled_channels'][country_id][channel_id]['enabled']:
                preselect.append(cnt)
            cnt += 1

    # Show mulit-select dialog
    dialog = xbmcgui.Dialog()
    selected_channels = dialog.multiselect(Script.localize(30277), options, preselect=preselect)

    if selected_channels is None:
        return

    # By default, disable all channels in the setting file
    for country_id in tv_integration_settings['enabled_channels'].keys():
        for channel_id in tv_integration_settings['enabled_channels'][country_id].keys():
            tv_integration_settings['enabled_channels'][country_id][channel_id]['enabled'] = False

    # Apply user selection and save settings
    for selected_channel in selected_channels:
        (country_id, channel_id) = selected_channels_map[selected_channel]
        tv_integration_settings['enabled_channels'][country_id][channel_id]['enabled'] = True

    save_tv_integration_settings(tv_integration_settings)


"""Interface to IPTV Manager

"""


class IPTVManager:
    def __init__(self, port):
        """Initialize IPTV Manager object"""
        self.port = port

    def via_socket(func):
        """Send the output of the wrapped function to socket"""

        def send(self):
            """Decorator to send over a socket"""
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.port))
            try:
                sock.sendall(json.dumps(func(self)).encode())
            finally:
                sock.close()

        return send

    @via_socket
    def send_channels(self):
        """Return JSON-STREAMS formatted python datastructure to IPTV Manager"""
        channels_list = []

        # Grab all live TV channels
        country_channels = get_all_live_tv_channels()

        # Grab current user settings
        tv_integration_settings = get_tv_integration_settings()

        for (country_order, country_id, country_label, country_infos, channels) in country_channels:
            for (channel_order, channel_id, channel_label, channel_infos) in channels:
                if not tv_integration_settings['enabled_channels'].get(country_id, {}).get(channel_id, {}).get('enabled', False):
                    continue

                json_stream = {}
                json_stream['name'] = get_item_label(channel_id, channel_infos)
                resolver = channel_infos['resolver'].replace(':', '/')
                params = {
                    'item_id': channel_id
                }
                query = urlencode(params)
                json_stream['stream'] = PLUGIN_KODI_PATH + resolver + '/?' + query
                if 'xmltv_id' in channel_infos:
                    json_stream['id'] = channel_infos['xmltv_id']
                if 'm3u_order' in channel_infos:
                    json_stream['preset'] = channel_infos['m3u_order']
                json_stream['logo'] = get_item_media_path(channel_infos['thumb'])

                channels_list.append(json_stream)

        return dict(version=1, streams=channels_list)

    @via_socket
    def send_epg(self):
        """Return JSON-EPG formatted python data structure to IPTV Manager"""
        epg_channels = {}

        # Grab current user settings
        tv_integration_settings = get_tv_integration_settings()

        country_tv_guides = {}

        # Ierate over each country and enabled channels to grab needed programmes
        for country_id in tv_integration_settings['enabled_channels']:
            for channel_id in tv_integration_settings['enabled_channels'][country_id]:
                if not tv_integration_settings['enabled_channels'][country_id][channel_id]['enabled']:
                    continue

                # Check if we have programmes for this country
                if country_id in country_tv_guides:
                    continue

                programmes = []
                for day_delta in range(0, 4):
                    programmes.extend(grab_programmes(country_id, day_delta))
                country_tv_guides[country_id] = programmes

        # Send each programme
        for country_id, programmes in country_tv_guides.items():
            for p in programmes:
                epg = dict(
                    start=p.get('start'),
                    stop=p.get('stop'),
                    title=p.get('title'),
                    description=p.get('desc'),
                    subtitle=p.get('sub-title'),
                    episode=p.get('episode'),
                    genre=p.get('category'),
                    image=p.get('icon'),
                    # credits=p.get('credits'), TODO: fix this in programme_post_treatment_iptvmanager
                )
                if p['channel'] not in epg_channels:
                    epg_channels[p['channel']] = []
                epg_channels[p['channel']].append(epg)
        return dict(version=1, epg=epg_channels)


"""Functions called by IPTV Manager

"""


@Script.register
def channels(plugin, port):
    """ Generate channel data for the Kodi PVR integration.

    Args:
        plugin (codequick.script.Script)
        port (str): Socket port to use
    """
    plugin.log('IPTV Manager is grabbing channels data')
    IPTVManager(int(port)).send_channels()


@Script.register
def epg(plugin, port):
    """ Generate EPG data for the Kodi PVR integration.

    Args:
        plugin (codequick.script.Script)
        port (str): Socket port to use
    """
    plugin.log('IPTV Manager is grabbing EPG data')
    IPTVManager(int(port)).send_epg()

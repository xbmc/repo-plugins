#!/usr/bin/python
#
#
# Written by Ksosez, BlueCop, Romans I XVI, locomot1f, MetalChris, awaters1 (https://github.com/awaters1)
# Released under GPL(v2)

import base64
import json
import re
import time
import urllib
import urllib2
import urlparse


import xbmcgui
import xbmcplugin

from resources.lib import util
from resources.lib import adobe_activate_api
from resources.lib.globals import selfAddon, defaultlive, defaultreplay, defaultupcoming, defaultimage, defaultfanart, translation, pluginhandle, LOG_LEVEL, UA_PC
from resources.lib.constants import *
from resources.lib.addon_util import *

from resources.lib import legacy
from resources.lib import appletv
from resources.lib import tvos
from resources.lib import roku
from resources.lib import androidtv
from resources.lib import events

TAG = 'ESPN3: '

def ROOT_ITEM(refresh):
    if not adobe_activate_api.is_authenticated():
        addDir('[COLOR=FFFF0000]' + translation(30300) + '[/COLOR]',
               dict(MODE=AUTHENTICATE_MODE),
               defaultreplay)
    include_premium = adobe_activate_api.is_authenticated()
    channel_list = events.get_channel_list(include_premium)
    legacy_inst = legacy.Legacy()
    espn_url = list()
    espn_url.append(events.get_live_events_url(channel_list))
    legacy_inst.index_legacy_live_events(dict(ESPN_URL=espn_url))
    if selfAddon.getSetting('ShowAndroidTVMenu') == 'true':
        addDir(translation(30780),
               dict(MODE='/androidtv/'),
               defaultlive)
    if selfAddon.getSetting('ShowAppleTVMenu') == 'true':
        addDir(translation(30730),
               dict(MODE='/appletv/'),
               defaultlive)
    if selfAddon.getSetting('ShowLegacyMenu') == 'true':
        addDir(translation(30740),
               dict(MODE='/legacy/'),
               defaultlive)
    if selfAddon.getSetting('ShowRokuMenu') == 'true':
        addDir(translation(30760),
               dict(MODE='/roku/'),
               defaultlive)
    if selfAddon.getSetting('ShowTVOSMenu') == 'true':
        addDir(translation(30750),
               dict(MODE='/tvos/'),
               defaultlive)
    if adobe_activate_api.is_authenticated():
        addDir('[COLOR=FF00FF00]' + translation(30380) + '[/COLOR]',
           dict(MODE=AUTHENTICATION_DETAILS_MODE),
           defaultfanart)
    xbmcplugin.endOfDirectory(pluginhandle, updateListing=refresh)

def PLAY_ITEM(args):
    url = args.get(PLAYBACK_URL)[0]
    item = xbmcgui.ListItem(path=url)
    return xbmcplugin.setResolvedUrl(pluginhandle, True, item)

# Cookie is only needed when authenticating with espn broadband as opposed to uplynk
#ua UA_PC
#finalurl = finalurl + '|Connection=keep-alive&User-Agent=' + urllib.quote(ua) + '&Cookie=_mediaAuth=' + urllib.quote(base64.b64encode(pkan))
def PLAY_TV(args):

    resource = args.get(ADOBE_RSS, None)
    network_name = args.get(NETWORK_NAME)[0]
    if resource is None:
        event_name = args.get(EVENT_NAME)[0]
        event_guid = args.get(EVENT_GUID)[0]
        event_parental_rating = args.get(EVENT_PARENTAL_RATING)[0]
        resource = adobe_activate_api.get_resource(network_name, event_name, event_guid, event_parental_rating)
    else:
        resource = resource[0]

    requires_auth = does_requires_auth(network_name)

    if requires_auth:
        if not adobe_activate_api.is_authenticated():
            dialog = xbmcgui.Dialog()
            dialog.ok(translation(30037), translation(30410))
            return
        try:
            media_token = adobe_activate_api.get_short_media_token(resource)
        except urllib2.HTTPError as e:
            if e.code == 410:
                dialog = xbmcgui.Dialog()
                dialog.ok(translation(30037), translation(30840))
                adobe_activate_api.deauthorize()
                xbmcplugin.endOfDirectory(pluginhandle, succeeded=False, updateListing=True)
                return
            else:
                raise e

        token_type = 'ADOBEPASS'
    else:
        media_token = adobe_activate_api.get_device_id()
        token_type = 'DEVICE'


    # see aHR0cDovL2FwaS1hcHAuZXNwbi5jb20vdjEvd2F0Y2gvY2xpZW50cy93YXRjaGVzcG4tdHZvcw== for details
    # see aHR0cDovL2VzcG4uZ28uY29tL3dhdGNoZXNwbi9hcHBsZXR2L2ZlYXR1cmVk for details
    start_session_url = args.get(SESSION_URL)[0]
    params = urllib.urlencode({'partner':'watchespn',
                               'playbackScenario':'HTTP_CLOUD_HIGH',
                               'platform':'chromecast_uplynk',
                               'token':media_token,
                               'tokenType':token_type,
                               'resource':base64.b64encode(resource),
                               'v': '2.0.0'
                               })
    start_session_url += '&' + params

    xbmc.log('ESPN3: start_session_url: ' + start_session_url, LOG_LEVEL)

    session_json = util.get_url_as_json(start_session_url)
    if check_error(session_json):
        return

    playback_url = session_json['session']['playbackUrls']['default']
    xbmc.log(TAG + 'Playback url %s' % playback_url, LOG_LEVEL)
    stream_quality = str(selfAddon.getSetting('StreamQuality'))
    bitrate_limit = int(selfAddon.getSetting('BitrateLimit'))
    xbmc.log(TAG + 'Stream Quality %s' % stream_quality, LOG_LEVEL)
    try:
        m3u8_obj = m3u8.load(playback_url)
    except:
        playback_url += '|Connection=keep-alive&User-Agent=' + urllib.quote(UA_PC) + '&Cookie=_mediaAuth=' +\
                        urllib.quote(session_json['session']['token'])
        item = xbmcgui.ListItem(path=playback_url)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, item)

    success = True
    if m3u8_obj.is_variant:
        stream_options = list()
        bandwidth_key = 'bandwidth'
        m3u8_obj.playlists.sort(key=lambda playlist: playlist.stream_info.bandwidth, reverse=True)
        m3u8_obj.data['playlists'].sort(key=lambda playlist: int(playlist['stream_info'][bandwidth_key]), reverse=True)
        stream_quality_index = str(selfAddon.getSetting('StreamQualityIndex'))
        stream_index = None
        should_ask = False
        try:
            stream_index = int(stream_quality_index)
            if stream_index < 0 or stream_index >= len(m3u8_obj.playlists):
                should_ask = True
        except:
            should_ask = True
        if '0' == stream_quality: # Best
            stream_index = 0
            should_ask = False
            for playlist in m3u8_obj.data['playlists']:
                stream_info = playlist['stream_info']
                bandwidth = int(stream_info[bandwidth_key]) / 1024
                if bandwidth <= bitrate_limit:
                    break
                stream_index = stream_index + 1
        elif '2' == stream_quality: #Ask everytime
            should_ask = True
        if should_ask:
            for playlist in m3u8_obj.data['playlists']:
                stream_info = playlist['stream_info']
                resolution = stream_info['resolution']
                frame_rate = stream_info['frame_rate']
                bandwidth = int(stream_info[bandwidth_key]) / 1024
                if 'average_bandwidth' in stream_info:
                    xbmc.log(TAG + 'bandwidth: %s average bandwidth: %s' %
                             (stream_info['bandwidth'], stream_info['average_bandwidth']), LOG_LEVEL)
                stream_options.append(translation(30450) % (resolution,
                                                      frame_rate,
                                                      bandwidth))
            dialog = xbmcgui.Dialog()
            stream_index = dialog.select(translation(30440), stream_options)
            if stream_index < 0:
                success = False
            else:
                selfAddon.setSetting(id='StreamQualityIndex', value=str(stream_index))

        xbmc.log(TAG + 'Chose stream %d' % stream_index, LOG_LEVEL)
        item = xbmcgui.ListItem(path=m3u8_obj.playlists[stream_index].uri)
        return xbmcplugin.setResolvedUrl(pluginhandle, success, item)
    else:
        item = xbmcgui.ListItem(path=playback_url)
        return xbmcplugin.setResolvedUrl(pluginhandle, success, item)


def PLAY_LEGACY_TV(args):
    # check blackout differently for legacy shows
    event_id = args.get(EVENT_ID)[0]
    url = base64.b64decode('aHR0cDovL2Jyb2FkYmFuZC5lc3BuLmdvLmNvbS9lc3BuMy9hdXRoL3dhdGNoZXNwbi91dGlsL2lzVXNlckJsYWNrZWRPdXQ/ZXZlbnRJZD0=') + event_id
    xbmc.log(TAG + 'Blackout url %s' % url, LOG_LEVEL)
    blackout_data = util.get_url_as_json(url)
    blackout = blackout_data['E3BlackOut']
    if not blackout == 'true':
        blackout = blackout_data['LinearBlackOut']
    if blackout == 'true':
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30037), translation(30040))
        return
    PLAY_TV(args)


base_url = sys.argv[0]
xbmc.log(TAG + 'QS: %s' % sys.argv[2], LOG_LEVEL)
args = urlparse.parse_qs(sys.argv[2][1:])
xbmc.log('ESPN3: args %s' % args, LOG_LEVEL)
mode = args.get(MODE, None)

refresh = False
if mode is not None and mode[0] == AUTHENTICATE_MODE:
    xbmc.log('Authenticate Device', LOG_LEVEL)
    regcode = adobe_activate_api.get_regcode()
    dialog = xbmcgui.Dialog()
    ok = dialog.yesno(translation(30310),
                   translation(30320),
                   translation(30330) % regcode,
                   translation(30340),
                   translation(30360),
                   translation(30350))
    if ok:
        try:
            adobe_activate_api.authenticate()
            dialog.ok(translation(30310), translation(30370))
        except urllib2.HTTPError as e:
            dialog.ok(translation(30037), translation(30420) % e)
    mode = None
    refresh = True
elif mode is not None and mode[0] == AUTHENTICATION_DETAILS_MODE:
    dialog = xbmcgui.Dialog()
    ok = dialog.yesno(translation(30380),
                      translation(30390) % adobe_activate_api.get_authentication_expires(),
                      translation(30700) % (player_config.get_dma(), player_config.get_timezone()),
                      translation(30710) % (player_config.get_can_sso(), player_config.get_sso_abuse()),
                      nolabel = translation(30360),
                      yeslabel = translation(30430))
    if ok:
        adobe_activate_api.deauthorize()
    mode = None
    refresh = True


if mode is not None:
    paths = mode[0].split('/')
    if len(paths) > 2:
        root = paths[1]
        path = paths[2]
        xbmc.log(TAG + 'root: %s path: %s' % (root, path), xbmc.LOGDEBUG)
        for class_def in (appletv.AppleTV, legacy.Legacy, tvos.TVOS, roku.Roku, androidtv.AndroidTV):
            class_root = getattr(getattr(class_def, '__init__'), 'mode')
            xbmc.log(TAG + 'class root: %s' % class_root, xbmc.LOGDEBUG)
            if root == class_root:
                for method_name in dir(class_def):
                    method = getattr(class_def, method_name)
                    xbmc.log(TAG + 'Looking at method %s' % method_name, xbmc.LOGDEBUG)
                    if hasattr(method, 'mode'):
                        method_mode = getattr(method, 'mode')
                        xbmc.log(TAG + 'Found method with mode %s' % method_mode, xbmc.LOGDEBUG)
                        if method_mode == path:
                            xbmc.log(TAG + 'Executing method', xbmc.LOGDEBUG)
                            getattr(class_def(), method_name)(args)


if mode is None:
    adobe_activate_api.clean_up_authorization_tokens()
    xbmc.log("Generate Main Menu", LOG_LEVEL)
    ROOT_ITEM(refresh)
elif mode[0] == PLAY_MODE:
    PLAY_LEGACY_TV(args)
elif mode[0] == PLAY_ITEM_MODE:
    PLAY_ITEM(args)
elif mode[0] == PLAY_TV_MODE:
    PLAY_TV(args)
elif mode[0] == UPCOMING_MODE:
    xbmc.log("Upcoming", LOG_LEVEL)
    dialog = xbmcgui.Dialog()
    dialog.ok(translation(30035), translation(30036))
    xbmcplugin.endOfDirectory(pluginhandle, succeeded=False, updateListing=True)

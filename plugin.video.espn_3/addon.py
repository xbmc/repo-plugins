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
from resources.lib.globals import selfAddon, defaultlive, defaultreplay, defaultupcoming, defaultimage, defaultfanart, translation, pluginhandle, UA_PC
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
    current_time = time.strftime("%I:%M %p", time.localtime(time.time()))
    addDir(translation(30850) % current_time,
           dict(MODE=REFRESH_LIVE_MODE),
           defaultlive)
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
    xbmcplugin.endOfDirectory(pluginhandle, updateListing=refresh, cacheToDisc=False)

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
        channel_resource_id = args.get(CHANNEL_RESOURCE_ID)[0]
        resource = adobe_activate_api.get_resource(channel_resource_id, event_name, event_guid, event_parental_rating)
    else:
        resource = resource[0]

    requires_auth = does_requires_auth(network_name)
    if not requires_auth:
        xbmc.log(TAG + ' Forcing auth', xbmc.LOGDEBUG)
        requires_auth = adobe_activate_api.is_authenticated()

    if requires_auth:
        if not adobe_activate_api.is_authenticated():
            dialog = xbmcgui.Dialog()
            dialog.ok(translation(30037), translation(30410))
            return
        try:
            # testing code raise urllib2.HTTPError(url='test', code=403, msg='no', hdrs=dict(), fp=None)
            xbmc.log(TAG + ' getting media token for resource %s' % resource, xbmc.LOGDEBUG)
            media_token = adobe_activate_api.get_short_media_token(resource)
        except urllib2.HTTPError as http_exception:
            xbmc.log(TAG + ' error getting media token %s' % http_exception, xbmc.LOGDEBUG)
            if http_exception.code == 410 or http_exception.code == 404:
                dialog = xbmcgui.Dialog()
                dialog.ok(translation(30037), translation(30840))
                adobe_activate_api.deauthorize()
                xbmcplugin.endOfDirectory(pluginhandle, succeeded=False, updateListing=True)
                return
            elif http_exception.code == 403:
                # Check for blackout
                dialog = xbmcgui.Dialog()
                ok = dialog.yesno(translation(30037), translation(30900))
                if ok:
                    setting = get_setting_from_channel(network_name)
                    if setting is not None:
                        selfAddon.setSetting(setting, 'false')
                return
            else:
                raise http_exception

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

    xbmc.log('ESPN3: start_session_url: ' + start_session_url, xbmc.LOGDEBUG)

    try:
        session_json = util.get_url_as_json(start_session_url)
    except urllib2.HTTPError as exception:
        if exception.code == 403:
            session_json = json.load(exception)
            xbmc.log(TAG + 'checking for errors in %s' % session_json)
        else:
            raise exception

    if check_error(session_json):
        return

    playback_url = session_json['session']['playbackUrls']['default']
    xbmc.log(TAG + 'Playback url %s' % playback_url, xbmc.LOGDEBUG)
    stream_quality = str(selfAddon.getSetting('StreamQuality'))
    bitrate_limit = int(selfAddon.getSetting('BitrateLimit'))
    xbmc.log(TAG + 'Stream Quality %s' % stream_quality, xbmc.LOGDEBUG)
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
                stream_index += 1
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
                             (stream_info['bandwidth'], stream_info['average_bandwidth']), xbmc.LOGDEBUG)
                stream_options.append(translation(30450) % (resolution,
                                                      frame_rate,
                                                      bandwidth))
            dialog = xbmcgui.Dialog()
            stream_index = dialog.select(translation(30440), stream_options)
            if stream_index < 0:
                success = False
            else:
                selfAddon.setSetting(id='StreamQualityIndex', value=str(stream_index))

        xbmc.log(TAG + 'Chose stream %d' % stream_index, xbmc.LOGDEBUG)
        item = xbmcgui.ListItem(path=m3u8_obj.playlists[stream_index].uri)
        xbmcplugin.setResolvedUrl(pluginhandle, success, item)
    else:
        item = xbmcgui.ListItem(path=playback_url)
        xbmcplugin.setResolvedUrl(pluginhandle, success, item)

base_url = sys.argv[0]
xbmc.log(TAG + 'QS: %s' % sys.argv[2], xbmc.LOGDEBUG)
args = urlparse.parse_qs(sys.argv[2][1:])
xbmc.log('ESPN3: args %s' % args, xbmc.LOGDEBUG)
mode = args.get(MODE, None)

refresh = False
if mode is not None and mode[0] == AUTHENTICATE_MODE:
    xbmc.log('Authenticate Device', xbmc.LOGDEBUG)
    if adobe_activate_api.is_authenticated():
        xbmc.log('Device already authenticated, skipping authentication', xbmc.LOGDEBUG)
    else:
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
                      nolabel=translation(30360),
                      yeslabel=translation(30430))
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

if mode is not None and mode[0] == REFRESH_LIVE_MODE:
    mode = None
    refresh = True
    include_premium = adobe_activate_api.is_authenticated()
    channel_list = events.get_channel_list(include_premium)
    util.clear_cache(events.get_live_events_url(channel_list))

if mode is None:
    try:
        adobe_activate_api.clean_up_authorization_tokens()
    except:
        xbmc.log(TAG + 'Unable to clean up')
        adobe_activate_api.reset_settings()
    xbmc.log("Generate Main Menu", xbmc.LOGDEBUG)
    try:
        ROOT_ITEM(refresh)
    except IOError as exception:
        xbmc.log('SSL certificate failure %s' % exception, xbmc.LOGDEBUG)
        xbmc.log('%s-%s-%s' % (exception.errno, exception.message, exception.strerror), xbmc.LOGDEBUG)
        if '[SSL: CERTIFICATE_VERIFY_FAILED]' in str(exception.strerror):
            dialog = xbmcgui.Dialog()
            ok = dialog.yesno(translation(30037), translation(30910))
            if ok:
                selfAddon.setSetting('DisableSSL', 'true')
                ROOT_ITEM(refresh)
            else:
                raise exception
        else:
            raise exception

elif mode[0] == PLAY_ITEM_MODE:
    PLAY_ITEM(args)
elif mode[0] == PLAY_TV_MODE:
    PLAY_TV(args)
elif mode[0] == UPCOMING_MODE:
    xbmc.log("Upcoming", xbmc.LOGDEBUG)
    dialog = xbmcgui.Dialog()
    dialog.ok(translation(30035), translation(30036))
    xbmcplugin.endOfDirectory(pluginhandle, succeeded=False, updateListing=True)

#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson as json
import hashlib

from .app_common import get_data, settings, log
from .base import play_liveStream, get_InputStreamHelper


_config_url = 'https://config.native-player.p7s1.io/dcb397f1ce8c1badb4a87762c344ce96.json'


def play_livestream(livestream_id):

    if settings.useWidevine():
        protocol = 'dash:widevine'
        drm_name = 'widevine'
        drm = 'com.widevine.alpha'
    else:
        protocol = 'dash:playready'
        drm_name = 'playready'
        drm = 'com.microsoft.playready'
    log('selected drm: ' + drm)

    config = get_data(_config_url, forceFetch=True, noMatch=True)
    log(config, 'debug')

    mdslive = config.get('mdsclient').get('mdsLive')
    client_tkn = '01' + hashlib.sha1(('puls4-24x7' + mdslive.get('salt') + mdslive.get(
        'accessToken') + mdslive.get('clientLocation')).encode('utf-8')).hexdigest()
    protocols_url = mdslive.get('baseUrl') + 'live/1.0/getprotocols?' + \
        'access_token=' + mdslive.get('accessToken') + \
        '&client_location=' + mdslive.get('clientLocation') + \
        '&client_token=' + client_tkn + \
        '&property_name=puls4-24x7'

    protocols = get_data(protocols_url, forceFetch=True)
    log(protocols, 'debug')

    client_server_tkn = '01' + hashlib.sha1(('puls4-24x7' + mdslive.get('salt') + mdslive.get(
        'accessToken') + protocols.get('server_token') + mdslive.get('clientLocation') + protocol).encode('utf-8')).hexdigest()
    geturls_url = mdslive.get('baseUrl') + 'live/1.0/geturls?' + \
        'access_token=' + mdslive.get('accessToken') + \
        '&client_location=' + mdslive['clientLocation'] + \
        '&client_token=' + client_server_tkn + \
        '&property_name=puls4-24x7' + \
        '&protocols=' + protocol + \
        '&secure_delivery=true' + \
        '&server_token=' + protocols.get('server_token')

    urls = get_data(geturls_url, forceFetch=True)
    log(urls, 'debug')

    streamHelper = get_InputStreamHelper(drm)

    if streamHelper and streamHelper.check_inputstream():
        userAgent = '|User-Agent=Mozilla/5.0 (Linux; Android 8.0.0;) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.116 Mobile Safari/537.36'
        dash_drm = urls.get('urls').get('dash').get(drm_name)
        path = dash_drm.get('url') + userAgent
        tkn = dash_drm.get('drm').get('licenseAcquisitionUrl') + '?token=' + \
            dash_drm.get('drm').get('token') + userAgent + '|R{SSM}|'

        play_liveStream(path, streamHelper.inputstream_addon, drm, tkn)

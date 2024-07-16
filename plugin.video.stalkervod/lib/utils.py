"""Utility classes and methods"""
from __future__ import absolute_import, division, unicode_literals
import xbmc
import xbmcgui
import xbmcaddon
from .loggers import Logger

__addon__ = xbmcaddon.Addon()


def ask_for_input(category):
    """Input dialog box"""
    return xbmcgui.Dialog().input(
        defaultt='',
        heading='Search in ' + category,
        type=xbmcgui.INPUT_ALPHANUM) or None


def get_int_value(dictionary, key):
    """Helper method to get int value"""
    if key in dictionary:
        val = str(dictionary[key])
        if val.isnumeric():
            return int(val)
    return 0


def get_next_info_and_send_signal(params, next_episode_url):
    """Send a signal to Kodi using JSON RPC"""
    next_info = get_next_info(params, next_episode_url)
    upnext_signal(next_info)


def upnext_signal(next_info):
    """Send a signal to Kodi using JSON RPC"""
    from base64 import b64encode
    from json import dumps
    data = [to_unicode(b64encode(dumps(next_info).encode()))]
    notify(sender='plugin.video.stalkervod.SIGNAL', message='upnext_data', data=data)


def notify(sender, message, data):
    """Send a notification to Kodi using JSON RPC"""
    result = jsonrpc(method='JSONRPC.NotifyAll', params=dict(
        sender=sender,
        message=message,
        data=data,
    ))
    if result.get('result') != 'OK':
        Logger.warn('Failed to send notification: ' + result.get('error').get('message'))
        return False
    Logger.debug('Notification sent to upnext')
    return True


def jsonrpc(**kwargs):
    """Perform JSONRPC calls"""
    from json import dumps, loads
    if kwargs.get('id') is None:
        kwargs.update(id=0)
    if kwargs.get('jsonrpc') is None:
        kwargs.update(jsonrpc='2.0')
    return loads(xbmc.executeJSONRPC(dumps(kwargs)))


def to_unicode(text, encoding='utf-8', errors='strict'):
    """Force text to unicode"""
    if isinstance(text, bytes):
        return text.decode(encoding, errors=errors)
    return text


def get_next_info(params, next_episode_url):
    """Send a signal to Kodi using JSON RPC"""
    return dict(
        current_episode=dict(
            episodeid=params['video_id'] + str(get_int_value(params, 'series') - 1),
            tvshowid=params['video_id'],
            title=params['title'],
            art={
                'thumb': '',
                'tvshow.clearart': params.get('poster_url', ''),
                'tvshow.clearlogo': params.get('poster_url', ''),
                'tvshow.fanart': params.get('poster_url', ''),
                'tvshow.landscape': params.get('poster_url', ''),
                'tvshow.poster': params.get('poster_url', ''),
            },
            season=params['season_no'],
            episode=get_int_value(params, 'series') - 1,
            showtitle=params['title'],
            plot='',
            playcount=0,
            rating=None,
            firstaired=''
        ),
        next_episode=dict(
            episodeid=params['video_id'] + str(get_int_value(params, 'series')),
            tvshowid=params['video_id'],
            title=params['title'],
            art={
                'thumb': '',
                'tvshow.clearart': params.get('poster_url', ''),
                'tvshow.clearlogo': params.get('poster_url', ''),
                'tvshow.fanart': params.get('poster_url', ''),
                'tvshow.landscape': params.get('poster_url', ''),
                'tvshow.poster': params.get('poster_url', ''),
            },
            season=params['season_no'],
            episode=get_int_value(params, 'series'),
            showtitle=params['title'],
            plot='',
            playcount=0,
            rating=None,
            firstaired=''
        ),
        play_url=next_episode_url
    )

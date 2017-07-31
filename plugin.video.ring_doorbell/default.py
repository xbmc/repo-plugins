import sys
import urllib
import urllib2
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import json
import time
import uuid
import re

from ring_doorbell import Ring
from datetime import datetime
from dateutil import tz


base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
ADDON = xbmcaddon.Addon(id='plugin.video.ring_doorbell')

xbmcplugin.setContent(addon_handle, 'movies')
mode = args.get('mode', None)

def init():

    
    email = ADDON.getSetting('email')
    password = ADDON.getSetting('password')
    items = ADDON.getSetting('items')
    
    if len(email) <= 7: 
        return showModal(ADDON.getLocalizedString(30200))
    if not re.match(r'[\w.-]+@[\w.-]+.\w+', email):
        return showModal(ADDON.getLocalizedString(30200))
    if len(password) <= 3:
        return showModal(ADDON.getLocalizedString(30201))
    if items.isdigit() == False:
        return showModal(ADDON.getLocalizedString(30202))
    
    try:
        myring = Ring(email, password)
    except:
        return showModal(ADDON.getLocalizedString(30203))

    if mode is None:
        events = []
        for device in list(myring.stickup_cams + myring.doorbells):
            for event in device.history(limit=items):
                event['formatted'] = format_event(device, event)
                event['doorbell_id'] = device.id
                events.append(event)
        sorted_events = sorted(events, key=lambda k: k['id'], reverse=True) 
        for event in sorted_events:
            url = build_url({'mode': 'play', 'doorbell_id': event['doorbell_id'], 'video_id': event['id']})
            li = xbmcgui.ListItem(str(event['formatted']), iconImage='DefaultVideo.png')
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle)
    else: 
        if mode[0] == 'play':
            doorbell_id = args['doorbell_id'][0]
            video_id = args['video_id'][0]
            for doorbell in list(myring.stickup_cams + myring.doorbells):
                if doorbell.id == doorbell_id:
                    try:
                        url = doorbell.recording_url(video_id)
                        play_video(url)
                    except:
                        return showModal(ADDON.getLocalizedString(30204))

def play_video(path):
    if xbmc.Player().isPlaying():
        xbmc.Player().stop()

    play_item = xbmcgui.ListItem(path=path)
    xbmc.Player().play(item=path, listitem=play_item)

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def build_url2(query):
    return base_url + ', ' + urllib.urlencode(query)

def format_event(device, event):
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    utc = event['created_at'].replace(tzinfo=from_zone)
    local_time = utc.astimezone(to_zone)

    local_time_string = local_time.strftime('%I:%M %p ') 
    local_time_string += ADDON.getLocalizedString(30300) 
    local_time_string += local_time.strftime(' %A %b %d %Y')

    event_name = ''
    if event['kind'] == 'on_demand':
        event_name = ADDON.getLocalizedString(30301)
    if event['kind'] == 'motion':
        event_name = ADDON.getLocalizedString(30302)
    if event['kind'] == 'ding':
        event_name = ADDON.getLocalizedString(30303)

    return ' '.join([device.name, event_name, local_time_string])

def showModal(text):
    __addon__ = xbmcaddon.Addon()
    __addonname__ = __addon__.getAddonInfo('name')
    xbmcgui.Dialog().ok(__addonname__, text)

init()
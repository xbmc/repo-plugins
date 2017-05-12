#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2014 Julien Gormotte (jgormotte@ate.info)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.

from xbmcswift2 import Plugin
from resources.lib.api import nocoApi
import re, time

plugin = Plugin()
api = nocoApi()

@plugin.route('/')
def index():
    if plugin.get_setting('username') == '' or plugin.get_setting('password') == '':
        plugin.open_settings()
    if plugin.get_setting('username') == '' or plugin.get_setting('password') == '':
        error=plugin.get_string('30050')
        plugin.notify(msg=error, delay=10000)
    else:
        token = getToken()
        partners = [{
            'label': partner['partner_name'],
            'icon': partner['icon_1024x576'],
            'path': plugin.url_for('indexMenu', partner=partner['partner_key'])
            } for partner in api.get_partners(token['token'])]
        partners.append({'label': plugin.get_string('30067'), 'path': plugin.url_for('indexPlaylists')})
        partners.append({'label': plugin.get_string('30063'), 'path': plugin.url_for('search')})
        return plugin.finish(partners)


@plugin.route('/partners/<partner>')
def indexMenu(partner):
    index = [
        {'label': plugin.get_string('30060'),
        'path': plugin.url_for('indexLast', partner=partner)},
        {'label': plugin.get_string('30066'),
        'path': plugin.url_for('indexAll', partner=partner)},
        {'label': plugin.get_string('30061'), 
        'path': plugin.url_for('indexPartner', partner=partner)},
        {'label': plugin.get_string('30065'), 
        'path': plugin.url_for('indexTypes', partner=partner)},
        {'label': plugin.get_string('30062'),
        'path': plugin.url_for('indexPopular', partner=partner)},
        ]
    return plugin.finish(index)

@plugin.route('/partners/<partner>/last')
def indexLast(partner):
    token = getToken()
    videos = []
    num_last = str(plugin.get_setting('show_last'))
    for video in api.get_last(partner, token['token'], num_last):
        videos.append(getVideoInfos(video))
    return plugin.finish(videos)

@plugin.route('/partners/<partner>/popular')
def indexPopular(partner):
    token = getToken()
    videos = []
    num_last = str(plugin.get_setting('show_last'))
    for video in api.get_popular(partner, token['token'], num_last):
        videos.append(getVideoInfos(video))
    return plugin.finish(videos)

@plugin.route('/partners/<partner>/all')
def indexAll(partner):
    token = getToken()
    res = []
    shows = [{
        'icon': fam['icon_1024x576'],
        'label': fam['family_TT'],
        'path': plugin.url_for('indexFamily', partner=partner, theme=fam['theme_key'], family=fam['family_key'])
        } for fam in api.get_all(partner, token['token'])]
    return plugin.finish(shows)

@plugin.route('/partners/<partner>/themes')
def indexPartner(partner):
    token = getToken()
    res = []
    themes = [{
        'icon': theme['icon'],
        'label': theme['theme_name'],
        'path': plugin.url_for('indexThemes', partner=partner, theme=theme['theme_key'])
        } for theme in api.get_themes(partner, token['token'])]
    return plugin.finish(themes)

@plugin.route('/partners/<partner>/types')
def indexTypes(partner):
    token = getToken()
    res = []
    alltypes = [{
        'icon': ty['icon'],
        'label': ty['type_name'],
        'path': plugin.url_for('indexByType', partner=partner, typename=ty['type_key'])
        } for ty in api.get_types(partner, token['token'])]
    return plugin.finish(alltypes)

@plugin.route('/search')
def search():
    token = getToken()
    videos = []
    query = plugin.keyboard(heading=plugin.get_string('30064'))
    try:
        for video in api.search(query, token['token']):
            videos.append(getVideoInfos(video))
        return plugin.finish(videos)
    except:
        error=plugin.get_string('30051').encode('utf-8')
        plugin.notify(msg=error, delay=5000)


@plugin.route('/playlists')
def indexPlaylists():
    token = getToken()
    playlists = [{
        'label': playlist['playlist_title'],
        'context_menu': [(plugin.get_string('30042'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('queuePlaylist', playlist=playlist['playlist'])))],
        'path': plugin.url_for('indexPlaylist', playlist=playlist['playlist'])
        } for playlist in api.get_playlists(token['token'])]
    return plugin.finish(playlists)

@plugin.route('/playlists/<playlist>')
def indexPlaylist(playlist):
    token = getToken()
    videos = []
    for video in playlist.split(','):
        v = api.get_videodata(token['token'], video)
        videos.append(getVideoInfos(v))
    return plugin.finish(filterSeenVideos(videos))

@plugin.route('/partners/<partner>/themes/<theme>')
def indexThemes(partner, theme):
    token = getToken()
    families = [{
        'icon': family['icon_1024x576'],
        'label': family['family_OT'],
        'path': plugin.url_for('indexFamily', partner=partner, theme=theme, family=family['family_key'])
        } for family in api.get_families(partner, theme, token['token'])]
    return plugin.finish(families)

@plugin.route('/partners/<partner>/types/<typename>')
def indexByType(partner, typename):
    token = getToken()
    families = [{
        'icon': family['icon_1024x576'],
        'label': family['family_OT'],
        'path': plugin.url_for('indexFamType', partner=partner, typename=typename, family=family['family_key'])
        } for family in api.get_fambytype(partner, typename, token['token'])]
    return plugin.finish(families)

@plugin.route('/partners/<partner>/themes/<theme>/families/<family>')
def indexFamily(partner, theme, family):
    token = getToken()
    videos = []
    num_video = str(plugin.get_setting('show_n'))
    for video in api.get_videos(partner, family, token['token'], num_video):
        videos.append(getVideoInfos(video))
    if plugin.get_setting('random') == "true":
        rand = { 'label': plugin.get_string('30040'), 'path': plugin.url_for('playVideo', partner=partner, family=family, video='RANDOM'), 'is_playable': True}
        videos.insert(0, rand)
    return plugin.finish(videos)

@plugin.route('/partners/<partner>/types/<typename>/families/<family>')
def indexFamType(partner, typename, family):
    token = getToken()
    videos = []
    num_video = str(plugin.get_setting('show_n'))
    for video in api.get_videos(partner, family, token['token'], num_video):
        videos.append(getVideoInfos(video))
    if plugin.get_setting('random') == "true":
        rand = { 'label': plugin.get_string('30040'), 'path': plugin.url_for('playVideo', partner=partner, family=family, video='RANDOM'), 'is_playable': True}
        videos.insert(0, rand)
    return plugin.finish(videos)

@plugin.route('/queue/<video>')
def queueVideo(video):
    token = getToken()
    quality = getQuality()
    v = api.get_videodata(token['token'], video)
    item = getVideoInfos(v)
    item['path'] = api.get_video(video, token['token'], quality)
    item.pop('context_menu', None) # removing specific ctx menu (Queue item) from playlist item
    items = [item]
    plugin.add_to_playlist(items, 'video')

@plugin.route('/queue/playlist/<playlist>')
def queuePlaylist(playlist):
    token = getToken()
    quality = getQuality()
    items = []
    for video in playlist.split(','):
        v = api.get_videodata(token['token'], video)
        item = getVideoInfos(v)
        item['path'] = api.get_video(video, token['token'], quality)
        item.pop('context_menu', None) # removing specific ctx menu (Queue item) from playlist item
        items.append(item)
    items = filterSeenVideos(items)
    plugin.add_to_playlist(items, 'video')

@plugin.route('/partners/<partner>/families/<family>/<video>')
def playVideo(partner, family, video):
    token = getToken()
    quality = getQuality()
    if video == 'RANDOM':
        video = api.get_random(partner, family, token['token'], quality)
        if video == None:
            plugin.notify(msg=plugin.get_string('30052').encode('utf-8'), delay=10000)
        else:
            plugin.set_resolved_url(api.get_video(video, token['token'], quality))
    else: 
        plugin.set_resolved_url(api.get_video(video, token['token'], quality))

def getVideoInfos(video):
    if str(video['episode_number']) == '0':
        if video['show_TT'] == None:
            label = video['family_TT'].encode('utf-8')
        else:
            label = video['family_TT'].encode('utf-8')+' - '+unicode(video['show_TT']).encode('utf-8')
    else:
        if video['show_TT'] == None:
            label = video['family_TT'].encode('utf-8')+' - '+str(video['episode_number'])
        else:
            label = video['family_TT'].encode('utf-8')+' - '+str(video['episode_number']).encode('utf-8')+' - '+unicode(video['show_TT']).encode('utf-8')
    if video['show_resume'] == None and video['family_resume'] == None:
        resume = ''
    elif video['show_resume'] == None and video['family_resume'] != None:
        resume = video['family_resume']
    elif video['family_resume'] == None and video['show_resume'] != None:
        resume = video['show_resume']
    else:
        resume =  video['family_resume']+'\n\n'+video['show_resume']
    if video['mark_read'] == 1:
        read = '1'
    else:
        read = '0'
    aired = video['online_date_start_utc']
    infos = {
        'genre': video['type_name'],
        'episode': video['episode_number'],
        'season': video['season_number'],
        'title': label,
        'studio': video['partner_name'],
        'writer': video['partner_name'],
        'director': video['partner_name'],
        #'rating': video[''],
        'playcount': read,
        'plot': resume,
        'plotoutline': resume,
        'tvshowtitle': video['family_TT'],
        'aired': video['online_date_start_utc']
        }
    properties = {
        'fanart_image': video['banner_family']
    }
    if read == '0':
        totaltime  = unicode(video['duration_ms']/1000)
        resumetime = unicode(video['resume_play']/1000)
        properties['totaltime']  = totaltime
        properties['resumetime'] = resumetime
    stream_infos = {'video': {'duration': video['duration_ms']/1000 }}

    # Add specific ctx menu for queueing item
    # XBMC.Action(Queue) doesn't work on Android (tested with Kodi 17.1)
    ctx_items = [(plugin.get_string('30041'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('queueVideo', video=video['id_show'])))]

    v = {
        'label': label.decode("utf-8"),
        'icon': video['screenshot_512x288'],
        'thumbnail': video['screenshot_512x288'],
        'info': infos,
        'properties': properties,
        'stream_info': stream_infos,
        'path': plugin.url_for('playVideo', partner=video['partner_key'], family=video['family_TT'].encode('utf-8'), video=video['id_show']),
        'context_menu': ctx_items,
        'is_playable': True
        }

    return v

def getToken():
    token = plugin.get_storage('token')
    username = plugin.get_setting('username')
    password = plugin.get_setting('password')
    if 'token' in token:
        if float(token['expire']) < ( time.time() + 600 ):
            #token['token'], token['expire'], token['renew'] = api.renew_token(token['renew'])
            token['token'], token['expire'], token['renew'] = api.get_token(username, password)
    else:
        token['token'], token['expire'], token['renew'] = api.get_token(username, password)
    return token

def getQuality():
    quality = plugin.get_setting('quality')
    if quality == "0": 
        quality = 'LQ' 
    if quality == "1": 
        quality = 'HQ' 
    if quality == "2": 
        quality = 'TV' 
    if quality == "3": 
        quality = 'HD_720' 
    if quality == "4": 
        quality = 'HD_1080' 
    return quality

def filterSeenVideos(videos):
    if plugin.get_setting('showseen') == 'true':
        return videos
    else:
        vid = []
        for v in videos:
            if v['info']['playcount'] == "0":
                vid.append(v)
        return vid

if __name__ == '__main__':
    plugin.run()

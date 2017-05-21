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

from xbmcswift2 import Plugin, xbmcgui
from resources.lib.api import nocoApi
from datetime import datetime
import re, time

plugin = Plugin()
api = nocoApi()

@plugin.route('/')
def index():
    plugin.set_content('files')
    guest = isGuestMode()
    if (plugin.get_setting('username') == '' or plugin.get_setting('password') == '') and not guest:
        plugin.open_settings()
        guest = isGuestMode()
    if (plugin.get_setting('username') == '' or plugin.get_setting('password') == '') and not guest:
        error=plugin.get_string('30250')
        plugin.notify(msg=error, delay=10000)
    else:
        token = getToken()
        
        if guest:
            rootMenuItems = [{
                'label': partner['partner_name'],
                'icon': partner['icon_1024x576'],
                'path': plugin.url_for('indexLast', partner=partner['partner_key'], guest_free='1')
                } for partner in GuestPartners()]
        else:        
            if plugin.get_setting('folder.playlist') == "true":
                noco_playlists = initNocoPlaylists()
    
            rootMenuItems = [{
                'label': partner['partner_name'],
                'icon': partner['icon_1024x576'],
                'path': plugin.url_for('indexPartner', partner=partner['partner_key'])
                } for partner in SubscribedPartners()]
                
            if plugin.get_setting('folder.playlist') == "true":
                rootMenuItems.append({
                    'label': plugin.get_string('30067'),
                    'path': plugin.url_for('indexPlaylists')})

            if plugin.get_setting('folder.favorite') == "true":
                rootMenuItems.append({
                    'label': plugin.get_string('30068'),
                    'context_menu': [(plugin.get_string('30082'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('clearFavorite')))],
                    'path': plugin.url_for('indexFavorites')})

            if plugin.get_setting('folder.history') == "true":
                rootMenuItems.append({
                    'label': plugin.get_string('30069'),
                    'path': plugin.url_for('indexHistory')})

            if plugin.get_setting('folder.free_content') == "true":
                rootMenuItems.append({
                    'label': plugin.get_string('30064'),
                    'path': plugin.url_for('indexUserFreePartners')})

            rootMenuItems.append({
                'label': plugin.get_string('30063'),
                'path': plugin.url_for('search')})

        return plugin.finish(rootMenuItems)


@plugin.route('/partners/<partner>')
def indexPartner(partner):
    plugin.set_content('files')
    if 'guest_free' in plugin.request.args:
        index = [
            {'label': plugin.get_string('30060'),
            'path': plugin.url_for('indexLast', partner=partner, guest_free='1')},
            ]
    elif 'user_free' in plugin.request.args:
        index = [
            {'label': plugin.get_string('30060'),
            'path': plugin.url_for('indexLast', partner=partner, user_free='1')},
            ]
    else:
        index = [
            {'label': plugin.get_string('30060'),
            'path': plugin.url_for('indexLast', partner=partner)},
            {'label': plugin.get_string('30066'),
            'path': plugin.url_for('indexAll', partner=partner)},
            {'label': plugin.get_string('30061'), 
            'path': plugin.url_for('indexThemes', partner=partner)},
            {'label': plugin.get_string('30065'), 
            'path': plugin.url_for('indexTypes', partner=partner)},
            ]
        if plugin.get_setting('folder.popular') == "true":
            index.append({'label': plugin.get_string('30062'),
                'path': plugin.url_for('indexPopulars', partner=partner)})
        if plugin.get_setting('folder.top_rated') == "true":
            index.append({'label': plugin.get_string('30070'),
                'path': plugin.url_for('indexTopRateds', partner=partner)})
                    
    return plugin.finish(index)

@plugin.route('/partners/<partner>/last')
@plugin.route('/partners/<partner>/last/<page>', name='last_page')
def indexLast(partner, page=None):
    plugin.set_content('videos')
    token = getToken()
    videos = []
    guest_free='1' if 'guest_free' in plugin.request.args and plugin.request.args['guest_free'][0]=='1' else ''  
    user_free='1' if 'user_free' in plugin.request.args and plugin.request.args['user_free'][0]=='1' else ''  
    num_page = 0 if page == None else int(page)
    show_per_page = int(plugin.get_setting('show_per_page'))
    hasNextPage, last = api.get_last(partner, token['token'], show_per_page, num_page, guest_free=(guest_free=='1'), user_free=(user_free=='1'))
    videos = [getVideoInfos(video) for video in last]
    
    UpdateTemporaryCache(videos)

    # pagination list items
    AddNavigation(videos, num_page, hasNextPage, 'last_page', partner=partner, guest_free=guest_free, user_free=user_free)

    update_listing = page is not None
    return plugin.finish(videos, update_listing=update_listing)

@plugin.route('/partners/<partner>/populars')
def indexPopulars(partner):
    plugin.set_content('files')
    index = [
        {'label': plugin.get_string('30046'),
        'path': plugin.url_for('indexPopular', partner=partner, period='this_week')},
        {'label': plugin.get_string('30047'),
        'path': plugin.url_for('indexPopular', partner=partner, period='this_month')},
        {'label': plugin.get_string('30048'),
        'path': plugin.url_for('indexPopular', partner=partner, period='all_time')},
        ]
    return plugin.finish(index)

@plugin.route('/partners/<partner>/popular/<period>')
@plugin.route('/partners/<partner>/popular/<period>/<page>', name='popular_page')
def indexPopular(partner, period, page=None):
    plugin.set_content('videos')
    token = getToken()
    videos = []
    num_page = 0 if page == None else int(page)
    show_per_page = int(plugin.get_setting('show_per_page'))
    hasNextPage, popular = api.get_popular(partner, token['token'], show_per_page, num_page, period)
    videos = [getVideoInfos(video) for video in popular]

    UpdateTemporaryCache(videos)

    # pagination list items
    AddNavigation(videos, num_page, hasNextPage, 'popular_page', partner=partner, period=period)

    update_listing = page is not None
    return plugin.finish(videos, update_listing=update_listing)


@plugin.route('/partners/<partner>/toprateds')
def indexTopRateds(partner):
    plugin.set_content('files')
    index = [
        {'label': plugin.get_string('30046'),
        'path': plugin.url_for('indexTopRated', partner=partner, period='this_week')},
        {'label': plugin.get_string('30047'),
        'path': plugin.url_for('indexTopRated', partner=partner, period='this_month')},
        {'label': plugin.get_string('30048'),
        'path': plugin.url_for('indexTopRated', partner=partner, period='all_time')},
        ]
    return plugin.finish(index)


@plugin.route('/partners/<partner>/toprated/<period>')
@plugin.route('/partners/<partner>/toprated/<period>/<page>', name='toprated_page')
def indexTopRated(partner, period, page=None):
    plugin.set_content('videos')
    token = getToken()
    videos = []
    num_page = 0 if page == None else int(page)
    show_per_page = int(plugin.get_setting('show_per_page'))
    hasNextPage, toprated = api.get_toprated(partner, token['token'], show_per_page, num_page, period)
    videos = [getVideoInfos(video) for video in toprated]

    UpdateTemporaryCache(videos)

    # pagination list items
    AddNavigation(videos, num_page, hasNextPage, 'toprated_page', partner=partner, period=period)

    update_listing = page is not None
    return plugin.finish(videos, update_listing=update_listing)


@plugin.route('/history')
@plugin.route('/history/<page>', name='history_page')
def indexHistory(page=None):
    plugin.set_content('videos')
    token = getToken()
    videos = []
    num_page = 0 if page == None else int(page)
    show_per_page = int(plugin.get_setting('show_per_page'))
    hasNextPage, history = api.get_history(token['token'], show_per_page, num_page)
    videos = [getVideoInfos(video) for video in history]

    UpdateTemporaryCache(videos)

    # pagination list items
    AddNavigation(videos, num_page, hasNextPage, 'history_page')

    update_listing = page is not None
    return plugin.finish(videos, update_listing=update_listing)

@plugin.route('/partners/<partner>/all')
def indexAll(partner):
    plugin.set_content('files')
    token = getToken()
    shows = [{
        'icon': fam['icon_1024x576'],
        'label': fam['family_TT'],
        'context_menu': [(plugin.get_string('30080'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('addtoFavorites', family=str(fam['id_family']))))] if plugin.get_setting('noco_favorite') == "true" else [],
        'path': plugin.url_for('indexFamily', partner=partner, theme=fam['theme_key'], family=fam['family_key'])
        } for fam in api.get_all(partner, token['token'])]
    return plugin.finish(shows)

@plugin.route('/partners/<partner>/themes')
def indexThemes(partner):
    plugin.set_content('files')
    token = getToken()
    themes = [{
        'icon': theme['icon'],
        'label': theme['theme_name'],
        'path': plugin.url_for('indexTheme', partner=partner, theme=theme['theme_key'])
        } for theme in api.get_themes(partner, token['token'])]
    return plugin.finish(themes)

@plugin.route('/partners/<partner>/types')
def indexTypes(partner):
    plugin.set_content('files')
    token = getToken()
    alltypes = [{
        'icon': ty['icon'],
        'label': ty['type_name'],
        'path': plugin.url_for('indexByType', partner=partner, typename=ty['type_key'])
        } for ty in api.get_types(partner, token['token'])]
    return plugin.finish(alltypes)

@plugin.route('/search')
@plugin.route('/search/<query>/<page>', name='search_page')
def search(query=None, page=None):
    plugin.set_content('videos')
    token = getToken()
    videos = []
    num_page = 0 if page == None else int(page)
    show_per_page = int(plugin.get_setting('show_per_page'))
    if query == None:
        query = plugin.keyboard(heading=plugin.get_string('30045'))
    if query == None:
        return

    hasNextPage, search = api.search(query, token['token'], show_per_page, num_page)

    if num_page == 0 and not len(search):
        error=plugin.get_string('30251').encode('utf-8')
        plugin.notify(msg=error, delay=5000)
        return
     
    videos = [getVideoInfos(video) for video in search]

    UpdateTemporaryCache(videos)

    # pagination list items
    AddNavigation(videos, num_page, hasNextPage, 'search_page', query=query)

    update_listing = page is not None
    return plugin.finish(videos, update_listing=update_listing)


@plugin.route('/playlists')
def indexPlaylists():
    plugin.set_content('files')
    noco_playlists = plugin.get_storage('noco_playlists')
    token = getToken()
    playlists = [{
        'label': playlist,
        'context_menu': [(plugin.get_string('30042'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('queuePlaylist', playlist=playlist))),
                         (plugin.get_string('30082'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('clearPlaylist', playlist=playlist)))],
        'path': plugin.url_for('indexPlaylist', playlist=playlist)
        } for playlist in sorted(noco_playlists.keys())]
    return plugin.finish(playlists)


@plugin.route('/playlists/<playlist>')
def indexPlaylist(playlist):
    plugin.set_content('videos')
    noco_playlists = plugin.get_storage('noco_playlists')
    videos = noco_playlists[playlist]

    UpdateTemporaryCache(videos)
        
    return plugin.finish(filterSeenVideos(videos))


@plugin.route('/favorites')
def indexFavorites():
    plugin.set_content('files')
    token = getToken()
    shows = []
    favorites = api.get_favorites(token['token'])

    if favorites['favorites']: 
        fids = [int(fid) for fid in str(favorites['favorites']).split(',')]
        shows = [{
            'icon': fam['icon_1024x576'],
            'label': fam['family_TT'],
            'context_menu': [(plugin.get_string('30081'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('delfromFavorites', family=str(fam['id_family']))))],
            'path': plugin.url_for('indexFamily', partner=str(fam['id_partner']), theme=fam['theme_key'], family=fam['family_key'])
            } for fam in api.get_fambyids(token['token'], fids)]
    return plugin.finish(shows)


@plugin.route('/partners/<partner>/themes/<theme>')
def indexTheme(partner, theme):
    plugin.set_content('files')
    token = getToken()
    families = [{
        'icon': family['icon_1024x576'],
        'label': family['family_OT'],
        'context_menu': [(plugin.get_string('30080'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('addtoFavorites', family=str(family['id_family']))))] if plugin.get_setting('noco_favorite') == "true" else [],
        'path': plugin.url_for('indexFamily', partner=partner, theme=theme, family=family['family_key'])
        } for family in api.get_families(partner, theme, token['token'])]
    return plugin.finish(families)


@plugin.route('/partners/<partner>/types/<typename>')
def indexByType(partner, typename):
    plugin.set_content('files')
    token = getToken()
    families = [{
        'icon': family['icon_1024x576'],
        'label': family['family_OT'],
        'context_menu': [(plugin.get_string('30080'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('addtoFavorites', family=str(family['id_family']))))] if plugin.get_setting('noco_favorite') == "true" else [],
        'path': plugin.url_for('indexFamType', partner=partner, typename=typename, family=family['family_key'])
        } for family in api.get_fambytype(partner, typename, token['token'])]
    return plugin.finish(families)


@plugin.route('/partners/<partner>/themes/<theme>/families/<family>')
@plugin.route('/partners/<partner>/themes/<theme>/families/<family>/<page>', name='family_page')
def indexFamily(partner, theme, family, page=None):
    plugin.set_content('videos')
    token = getToken()
    videos = []
    num_page = 0 if page == None else int(page)
    show_per_page = int(plugin.get_setting('show_per_page'))
    hasNextPage, shows = api.get_videos(partner, family, token['token'], show_per_page, num_page)
    videos = [getVideoInfos(video) for video in shows]

    UpdateTemporaryCache(videos)
        
    # pagination list items
    AddNavigation(videos, num_page, hasNextPage, 'family_page', partner=partner, theme=theme, family=family)

    if plugin.get_setting('random') == "true":
        rand = { 'label': plugin.get_string('30040'),
                 'properties': {'totaltime': unicode(1),'resumetime': unicode(0)},
                 'path': plugin.url_for('playVideo', partner=partner, family=family, video='RANDOM'),
                 'is_playable': True}
        videos.insert(0, rand)

    update_listing = page is not None
    return plugin.finish(videos, update_listing=update_listing)

@plugin.route('/partners/<partner>/types/<typename>/families/<family>')
@plugin.route('/partners/<partner>/types/<typename>/families/<family>/<page>', name='famtype_page')
def indexFamType(partner, typename, family, page=None):
    plugin.set_content('videos')
    token = getToken()
    videos = []
    num_page = 0 if page == None else int(page)
    show_per_page = int(plugin.get_setting('show_per_page'))
    hasNextPage, shows = api.get_videos(partner, family, token['token'], show_per_page, num_page)
    videos = [getVideoInfos(video) for video in shows]

    UpdateTemporaryCache(videos)

    # pagination list items
    AddNavigation(videos, num_page, hasNextPage, 'famtype_page', partner=partner, typename=typename, family=family)

    if plugin.get_setting('random') == "true":
        rand = { 'label': plugin.get_string('30040'),
                 'properties': {'totaltime': unicode(1),'resumetime': unicode(0)},
                 'path': plugin.url_for('playVideo', partner=partner, family=family, video='RANDOM'),
                 'is_playable': True}
        videos.insert(0, rand)

    update_listing = page is not None
    return plugin.finish(videos, update_listing=update_listing)

@plugin.route('/queue/<video>')
def queueVideo(video):
    token = getToken()
    guest = isGuestMode()
    quality = getQuality()
    v = api.get_videodata(token['token'], [int(video)])
    item = getVideoInfos(v[0])
    item['path'] = api.get_video(video, token['token'], quality)
    if not guest:
        item['context_menu'] = [item['context_menu'][1]] # Keep Rate context item
    else:
        item.pop('context_menu', None) # removing specific ctx menu (Queue item) from playlist item
    items = [item]
    plugin.add_to_playlist(items, 'video')

@plugin.route('/queue/playlist/<playlist>')
def queuePlaylist(playlist):
    token = getToken()
    quality = getQuality()
    items = []
    noco_playlists = plugin.get_storage('noco_playlists')
    for item in noco_playlists[playlist]:
        item['path'] = api.get_video(item['properties']['id_show'], token['token'], quality)
        item.pop('context_menu', None) # removing specific ctx menu (Queue item) from playlist item
        items.append(item)
    items = filterSeenVideos(items)
    plugin.add_to_playlist(items, 'video')

@plugin.route('/clear/playlist/<playlist>')
def clearPlaylist(playlist):
    token = getToken()
    api.clear_playlist(token['token'])
    noco_playlists = plugin.get_storage('noco_playlists')
    noco_playlists[playlist] = []
    noco_playlists.sync()

@plugin.route('/clear/favorite')
def clearFavorite():
    token = getToken()
    api.clear_playlist(token['token'])


@plugin.route('/addtoplaylist/<playlist>/<video>')
def addtoPlaylist(playlist, video):
    noco_playlists = plugin.get_storage('noco_playlists')
    token = getToken()
    temp_items = plugin.get_storage('temp_items')
    temp_item = temp_items[video]
    temp_item['context_menu'] = temp_item['context_menu'][0:2] # Keep only Queue and Rate item
    temp_item['context_menu'].append((plugin.get_string('30081'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('delfromPlaylist', playlist=playlist, video=video))))
    temp_item['context_menu'].append((plugin.get_string('30092'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('moveupinPlaylist', playlist=playlist, video=video))))
    temp_item['context_menu'].append((plugin.get_string('30093'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('movedowninPlaylist', playlist=playlist, video=video))))
    temp_item['context_menu'].append((plugin.get_string('30095'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('moveinPlaylist', playlist=playlist, video=video))))
    playlist_vids = [int(item['properties']['id_show']) for item in noco_playlists[playlist]]
    vid = int(video)
    if not vid in playlist_vids:
        # upd noco queuelist
        playlist_vids.append(vid)
        api.set_playlist(token['token'], playlist_vids)
        # upd noco_playlists obj 
        noco_playlists[playlist].append(temp_item)
        noco_playlists.sync()


@plugin.route('/delfromplaylist/<playlist>/<video>')
def delfromPlaylist(playlist, video):
    noco_playlists = plugin.get_storage('noco_playlists')
    token = getToken()
    # remove matching indexes
    match_indexes = [idx for idx,item in enumerate(noco_playlists[playlist]) if item['properties']['id_show'] == video]
    for i in reversed(match_indexes):
        del noco_playlists[playlist][i]    

    playlist_vids = [int(item['properties']['id_show']) for item in noco_playlists[playlist]]
    api.set_playlist(token['token'], playlist_vids)
    noco_playlists.sync()
    xbmc.executebuiltin('Container.Refresh')


@plugin.route('/moveupinPlaylist/<playlist>/<video>')
def moveupinPlaylist(playlist, video):
    noco_playlists = plugin.get_storage('noco_playlists')
    token = getToken()
    # search index to move
    for idx,item in enumerate(noco_playlists[playlist]):
        if item['properties']['id_show'] == video:
            if idx > 0: # do not move up 1st item
                noco_playlists[playlist][idx-1], noco_playlists[playlist][idx] = noco_playlists[playlist][idx], noco_playlists[playlist][idx-1]
            break

    playlist_vids = [int(item['properties']['id_show']) for item in noco_playlists[playlist]]
    api.set_playlist(token['token'], playlist_vids)
    noco_playlists.sync()
    xbmc.executebuiltin('Container.Refresh')


@plugin.route('/movedowninPlaylist/<playlist>/<video>')
def movedowninPlaylist(playlist, video):
    noco_playlists = plugin.get_storage('noco_playlists')
    token = getToken()
    # search index to move
    for idx,item in enumerate(noco_playlists[playlist]):
        if item['properties']['id_show'] == video:
            if idx < len(noco_playlists[playlist])-1: # do not move down last item
                noco_playlists[playlist][idx+1], noco_playlists[playlist][idx] = noco_playlists[playlist][idx], noco_playlists[playlist][idx+1]
            break

    playlist_vids = [int(item['properties']['id_show']) for item in noco_playlists[playlist]]
    api.set_playlist(token['token'], playlist_vids)
    noco_playlists.sync()
    xbmc.executebuiltin('Container.Refresh')


@plugin.route('/moveinPlaylist/<playlist>/<video>')
def moveinPlaylist(playlist, video):
    token = getToken()
    noco_playlists = plugin.get_storage('noco_playlists')
    # search index to move
    for idx,item in enumerate(noco_playlists[playlist]):
        if item['properties']['id_show'] == video:
            idx_from = idx
            break
    # switch context menu to target
    for idx,item in enumerate(noco_playlists[playlist]):
        ctx_items = []
        if not idx == idx_from:
            ctx_items.append((plugin.get_string('30097'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('movehereinPlaylist', playlist=playlist, from_idx=str(idx_from), to_idx=str(idx)))))
        ctx_items.append((plugin.get_string('30096'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('cancelmoveinPlaylist', playlist=playlist))))
        noco_playlists[playlist][idx]['context_menu'] = ctx_items
    noco_playlists.sync()
    xbmc.executebuiltin('Container.Refresh')


@plugin.route('/cancelmoveinPlaylist/<playlist>')
def cancelmoveinPlaylist(playlist):
    noco_playlists = plugin.get_storage('noco_playlists')
    # switch context menu back to normal
    for idx,item in enumerate(noco_playlists[playlist]):
        vid = item['properties']['id_show']
        ctx_items = [(plugin.get_string('30041'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('queueVideo', video=vid)))]
        ctx_items.append((plugin.get_string('30081'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('delfromPlaylist', playlist=playlist, video=vid))))
        ctx_items.append((plugin.get_string('30092'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('moveupinPlaylist', playlist=playlist, video=vid))))
        ctx_items.append((plugin.get_string('30093'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('movedowninPlaylist', playlist=playlist, video=vid))))
        ctx_items.append((plugin.get_string('30095'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('moveinPlaylist', playlist=playlist, video=vid))))
        noco_playlists[playlist][idx]['context_menu'] = ctx_items
    noco_playlists.sync()
    xbmc.executebuiltin('Container.Refresh')


@plugin.route('/movehereinPlaylist/<playlist>/<from_idx>/<to_idx>')
def movehereinPlaylist(playlist, from_idx, to_idx):
    token = getToken()
    noco_playlists = plugin.get_storage('noco_playlists')
    noco_playlists[playlist].insert(int(to_idx), noco_playlists[playlist].pop(int(from_idx)))
    # switch context menu back to normal
    for idx,item in enumerate(noco_playlists[playlist]):
        vid = item['properties']['id_show']
        ctx_items = [(plugin.get_string('30041'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('queueVideo', video=vid)))]
        ctx_items.append((plugin.get_string('30081'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('delfromPlaylist', playlist=playlist, video=vid))))
        ctx_items.append((plugin.get_string('30092'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('moveupinPlaylist', playlist=playlist, video=vid))))
        ctx_items.append((plugin.get_string('30093'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('movedowninPlaylist', playlist=playlist, video=vid))))
        ctx_items.append((plugin.get_string('30095'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('moveinPlaylist', playlist=playlist, video=vid))))
        noco_playlists[playlist][idx]['context_menu'] = ctx_items
    playlist_vids = [int(item['properties']['id_show']) for item in noco_playlists[playlist]]
    api.set_playlist(token['token'], playlist_vids)
    noco_playlists.sync()
    xbmc.executebuiltin('Container.Refresh')


@plugin.route('/addtoFavorites/<family>')
def addtoFavorites(family):
    token = getToken()
    favorites = api.get_favorites(token['token'])
    fids = []
    if favorites['favorites']: 
        fids = [int(fid) for fid in str(favorites['favorites']).split(',')]
    fids.append(int(family))
    api.set_favorite(token['token'], fids)


@plugin.route('/delfromFavorites/<family>')
def delfromFavorites(family):
    token = getToken()
    favorites = api.get_favorites(token['token'])
    if favorites['favorites']: 
        fids = [int(fid) for fid in str(favorites['favorites']).split(',')]

    # remove matching indexes
    match_indexes = [idx for idx,fid in enumerate(fids) if fid == int(family)]
    for i in reversed(match_indexes):
        del fids[i]    
    api.set_favorite(token['token'], fids)
    xbmc.executebuiltin('Container.Refresh')


@plugin.route('/userfreepartners')
def indexUserFreePartners():
    plugin.set_content('files')
    token = getToken()
    menu = [{
        'label': partner['partner_name'],
        'icon': partner['icon_1024x576'],
        'path': plugin.url_for('indexLast', partner=partner['partner_key'], user_free='1')
        } for partner in UserFreePartners()]
    return plugin.finish(menu)


@plugin.route('/rate/<video>')
def rateVideo(video):
    temp_items = plugin.get_storage('temp_items')
    temp_item = temp_items[video]
    current_rating = 0 if not 'userrating' in temp_item['info'] else int(temp_item['info']['userrating'])
    rating_items = []
    for rating in [5, 4, 3, 2, 1]:
        rating_items.append('[COLOR yellow]' + '*'*rating + '[/COLOR]')

    dialog = xbmcgui.Dialog()
    result = dialog.select(plugin.get_string('30049'), rating_items)
    if not result == -1:
        token = getToken()
        api.set_rating(token['token'], video, 5-result)
        if plugin.get_setting('folder.playlist') == "true":
            UpdateUserRatingInPlaylist(video, 5-result)
        xbmc.executebuiltin("Container.Refresh")


@plugin.route('/partners/<partner>/families/<family>/<video>')
def playVideo(partner, family, video):
    token = getToken()
    quality = getQuality()
    if video == 'RANDOM':
        rating_csa, video = api.get_random(partner, family, token['token'], quality)
        if not len(video):
            plugin.notify(msg=plugin.get_string('30252').encode('utf-8'), delay=10000)
        else:
            csaAdvisedNotfound = True
            for idx in range(len(video)):
                if isAdvisedByCSA(rating_csa[idx]):
                    csaAdvisedNotfound = False
                    plugin.set_resolved_url(api.get_video(video[idx], token['token'], quality))
                    break
            if csaAdvisedNotfound:
                plugin.notify(msg=plugin.get_string('30253').encode('utf-8'), delay=10000)
        
    else:
        plugin.set_resolved_url(api.get_video(video, token['token'], quality))

@plugin.route('/notadvised/<rate>')
def notAdvised(rate):
    plugin.notify(msg=plugin.get_string('30253').encode('utf-8'), delay=10000)

def getVideoInfos(video):
    guest = isGuestMode()
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
        resume = video['family_resume']+'\n\n'+video['show_resume']

    if not guest and video['mark_read'] == 1:
        read = '1'
    else:
        read = '0'

    infos = {
        'genre': video['type_name'],
        'episode': video['episode_number'],
        'season': video['season_number'],
        'title': label,
        'studio': video['partner_name'],
        'writer': video['partner_name'],
        'director': video['partner_name'],
        'playcount': read,
        'plot': resume,
        'plotoutline': resume,
        'tvshowtitle': video['family_TT'],
        'date': datetime(*(time.strptime(video['broadcast_date_utc'], '%Y-%m-%d %H:%M:%S')[0:6])).strftime('%d.%m.%Y'),
        'aired': video['broadcast_date_utc'],
        'mpaa': getMpaaFromCSA(video['rating_fr']),
        'duration': str(video['duration_ms']/1000),
        'mediatype': 'video'
        }
    properties = {
        'fanart_image': video['banner_family'],
        'id_show': unicode(video['id_show']) # this tag is only for this plugin
    }
    if read == '0':
        totaltime  = unicode(video['duration_ms']/1000)
        if not guest:
            resumetime = unicode(video['resume_play']/1000)
        else:
            resumetime = unicode(0)
        properties['totaltime']  = totaltime
        properties['resumetime'] = resumetime
    stream_infos = {
        'video': {'duration': video['duration_ms']/1000}}

    if not video['rated_all_time'] is None: 
        infos['rating'] = float(video['rated_all_time'])*2.0

    if not guest and  not video['rating_user'] is None: 
        infos['userrating'] = int(video['rating_user'])*2

    # Add specific ctx menu for queueing item and adding to Noco playlist
    ctx_items = [(plugin.get_string('30041'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('queueVideo', video=str(video['id_show']))))]
    if not guest:
        ctx_items = ctx_items + [(plugin.get_string('30049'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('rateVideo', video=str(video['id_show']))))]
        if plugin.get_setting('folder.playlist') == "true":
            noco_playlists = plugin.get_storage('noco_playlists')
            ctx_items = ctx_items + [(plugin.get_string('30090') % name, 'XBMC.RunPlugin(%s)' % (plugin.url_for('addtoPlaylist', playlist=name, video=str(video['id_show'])))) for name in noco_playlists.keys()]

    advised = isAdvisedByCSA(video['rating_fr'])
    
    v = {
        'label': label.decode("utf-8"),
        'icon': video['screenshot_512x288'],
        'thumbnail': video['screenshot_512x288'],
        'info': infos,
        'properties': properties,
        'stream_info': stream_infos,
        'path':  plugin.url_for('playVideo', partner=video['partner_key'], family=video['family_TT'].encode('utf-8'), video=video['id_show']) if advised else plugin.url_for('notAdvised', rate=video['rating_fr']), 
        'context_menu': ctx_items if advised else [],
        'is_playable': advised
        }

    return v

def getToken():
    token = plugin.get_storage('token')
    guest = isGuestMode()

    if 'token' in token:
        # detect switch guest/user mode
        switchMode = (guest == (not 'guest' in token)) 
        if not switchMode and float(token['expire']) > time.time() + 600 :
            return token
        
    if not guest:
        username = plugin.get_setting('username')
        password = plugin.get_setting('password')
        #token['token'], token['expire'], token['renew'] = api.renew_token(token['renew'])
        token['token'], token['expire'], token['renew'] = api.get_token(username, password)
        token.pop('guest', None)
    else:
        token['token'], token['expire'] = api.get_guest_token()
        token['guest'] = 1
    return token

def initNocoPlaylists():
    plist = plugin.get_storage('noco_playlists')
    token = getToken()
    for playlist in api.get_playlists(token['token']):
        videos = []
        if not playlist['playlist'] == '': 
            vids = api.get_videodata(token['token'], eval('['+str(playlist['playlist'])+']'))
            for video in vids:
                item = getVideoInfos(video)
                item['context_menu'] = item['context_menu'][0:2] # Keep only Queue and Rate items
                item['context_menu'].append((plugin.get_string('30081'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('delfromPlaylist', playlist=playlist['playlist_title'], video=video['id_show']))))
                item['context_menu'].append((plugin.get_string('30092'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('moveupinPlaylist', playlist=playlist['playlist_title'], video=video['id_show']))))
                item['context_menu'].append((plugin.get_string('30093'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('movedowninPlaylist', playlist=playlist['playlist_title'], video=video['id_show']))))
                item['context_menu'].append((plugin.get_string('30095'), 'XBMC.RunPlugin(%s)' % (plugin.url_for('moveinPlaylist', playlist=playlist['playlist_title'], video=video['id_show']))))
                videos.append(item)
        plist[playlist['playlist_title']] = videos
    return plist

def UpdateTemporaryCache(videos):
    # Each time we show a listing with playable items, we store the items in
    # temporary storage. Then, if a user add the item to a playlist or rate it, we already
    # have all the metadata available.
    temp_items = plugin.get_storage('temp_items')
    temp_items.clear()

    # Need to use the same referenced dict object for the cache, so we call
    # update() instead of assigning to a new dict.
    temp_items.update((item['properties']['id_show'], item) for item in videos)

def UpdateUserRatingInPlaylist(vid, userrating):
    noco_playlists = plugin.get_storage('noco_playlists')
    needSync = False
    for playlist in sorted(noco_playlists.keys()):
        match_indexes = [idx for idx,item in enumerate(noco_playlists[playlist]) if item['properties']['id_show'] == vid]
        for i in reversed(match_indexes):
            needSync = True
            noco_playlists[playlist][idx]['info']['userrating'] = userrating*2
    if needSync:
        noco_playlists.sync()
            

def AddNavigation(videos, num_page, hasNextPage, endpoint, **items):
    _before = num_page - 1 if num_page > 0 else None 
    _after = num_page + 1 if hasNextPage else None
    if not _after == None:
        videos.append( {
            'label': u'...' + plugin.get_string('30043') + ' (' + str(_after+1) + ')' + u' \u00BB',
            'path': plugin.url_for(endpoint, **dict( items.items() + {'page':str(_after)}.items()))
        })

    if not _before == None:
        videos.insert(0, {
            'label': u'\u00AB ' + '(' + str(_before+1)  + ') ' + plugin.get_string('30044') + u'...',
            'path': plugin.url_for(endpoint, **dict( items.items() + {'page':str(_before)}.items()))
        })

# Cache to not always loop on partners and check for free contents (to avoid too many requests)
def UserFreePartners():
    partners = plugin.get_storage('noco_partners',TTL=24*60)
    if not 'user_free' in partners:
        token = getToken()
        partners['user_free'] = api.get_user_free_partners(token['token'])
    return partners['user_free']

def GuestPartners():
    partners = plugin.get_storage('noco_partners',TTL=24*60)
    if not 'guest' in partners:
        token = getToken()
        partners['guest'] = api.get_guest_partners(token['token'])
    return partners['guest']

def SubscribedPartners():
    partners = plugin.get_storage('noco_partners',TTL=24*60)
    if not 'subscribed' in partners:
        token = getToken()
        partners['subscribed'] = api.get_subscribed_partners(token['token'])
    return partners['subscribed']

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

def getMpaaFromCSA(rating_fr):
    if not isinstance(rating_fr, int):
        return "France:U"
    if rating_fr == 0: 
        return "France:U"
    elif rating_fr == 10: 
        return "France:-10"
    elif rating_fr == 12: 
        return "France:-12"
    elif rating_fr == 16: 
        return "France:-16"
    elif rating_fr == 18: 
        return "France:-18"
    return "France:U"

def isAdvisedByCSA(rating_fr):
    if not isinstance(rating_fr, int):
        return True 
    csa = plugin.get_setting('csa')
    if csa == "4": 
        return True 
    elif csa == "0" and rating_fr < 10: 
        return True 
    elif csa == "1" and rating_fr < 12:
        return True 
    elif csa == "2" and rating_fr < 16: 
        return True 
    elif csa == "3"  and rating_fr < 18: 
        return True 
    return False

def isGuestMode():
    return True if plugin.get_setting('guest') == "true" else False

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

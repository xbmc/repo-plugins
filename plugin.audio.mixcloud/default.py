# -*- coding: utf-8 -*-

'''
@author: jackyNIX

Copyright (C) 2011-2020 jackyNIX

This file is part of KODI MixCloud Plugin.

KODI MixCloud Plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

KODI MixCloud Plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with KODI MixCloud Plugin.  If not, see <http://www.gnu.org/licenses/>.
'''



import sys,time
import xbmc,xbmcgui,xbmcplugin,xbmcaddon
import urllib,urllib2
import base64
import simplejson as json
import re
import sys
import os
from itertools import cycle, izip



URL_PLUGIN=         'plugin://music/MixCloud/'
URL_MIXCLOUD=       'https://www.mixcloud.com/'
URL_API=            'http://api.mixcloud.com/'
URL_CATEGORIES=     'http://api.mixcloud.com/categories/'
URL_HOT=            'http://api.mixcloud.com/popular/hot/'
URL_SEARCH=         'http://api.mixcloud.com/search/'
URL_FEED=           'https://api.mixcloud.com/me/feed/'
URL_FAVORITES=      'https://api.mixcloud.com/me/favorites/'
URL_FOLLOWINGS=     'https://api.mixcloud.com/me/following/'
URL_FOLLOWERS=      'https://api.mixcloud.com/me/followers/'
URL_LISTENS=        'https://api.mixcloud.com/me/listens/'
URL_UPLOADS=        'https://api.mixcloud.com/me/cloudcasts/'
URL_LISTENLATER=    'https://api.mixcloud.com/me/listen-later/'
URL_PLAYLISTS=      'https://api.mixcloud.com/me/playlists/'
URL_JACKYNIX=       'http://api.mixcloud.com/jackyNIX/'
URL_STREAM=         'http://www.mixcloud.com/api/1/cloudcast/{0}.json?embed_type=cloudcast'
URL_FAVORITE=       'https://api.mixcloud.com{0}favorite/'
URL_FOLLOW=         'https://api.mixcloud.com{0}/follow/'
URL_ADDLISTENLATER= 'https://api.mixcloud.com{0}listen-later/'
URL_TOKEN=          'https://www.mixcloud.com/oauth/access_token'



MODE_HOME=           0
MODE_FEED=          10
MODE_FAVORITES=     11
MODE_FOLLOWINGS=    12
MODE_HOT=           13
MODE_HISTORY=       14
MODE_JACKYNIX=      15
MODE_FOLLOWERS=     16
MODE_LISTENS=       17
MODE_UPLOADS=       18
MODE_PLAYLISTS=     19
MODE_CATEGORIES=    20
MODE_USERS=         21
MODE_LISTENLATER=   22
MODE_LOGIN=         23
MODE_LOGOFF=        24
MODE_SEARCH=        30
MODE_PLAY=          40
MODE_ADDFAVORITE=   50
MODE_DELFAVORITE=   51
MODE_ADDFOLLOWING=  52
MODE_DELFOLLOWING=  53
MODE_ADDLISTENLATER=54
MODE_DELLISTENLATER=55



STR_ACCESS_TOKEN=   u'access_token'
STR_ARTIST=         u'artist'
STR_AUDIOFORMATS=   u'audio_formats'
STR_AUDIOLENGTH=    u'audio_length'
STR_CLIENTID=       u'Vef7HWkSjCzEFvdhet'
STR_CLIENTSECRET=   u'VK7hwemnZWBexDbnVZqXLapVbPK3FFYT'
STR_CLOUDCAST=      u'cloudcast'
STR_CLOUDCASTLOOKUP=u'cloudcastLookup'
STR_COUNT=          u'count'
STR_COMMENT=        u'comment'
STR_CREATEDTIME=    u'created_time'
STR_DASHURL=        u'dashUrl'
STR_DATA=           u'data'
STR_DATE=           u'date'
STR_DESCRIPTION=    u'description'
STR_DURATION=       u'duration'
STR_GENRE=          u'genre'
STR_HISTORY=        u'history'
STR_HLSURL=         u'hlsUrl'
STR_ID=             u'id'
STR_IMAGE=          u'image'
STR_ISEXCLUSIVE=    u'isExclusive'
STR_FORMAT=         u'format'
STR_KEY=            u'key'
STR_LIMIT=          u'limit'
STR_MAGICSTRING=    u'IFYOUWANTTHEARTISTSTOGETPAIDDONOTDOWNLOADFROMMIXCLOUD'
STR_MESSAGE=        u'message'
STR_MODE=           u'mode'
STR_MP3=            u'mp3'
STR_NAME=           u'name'
STR_OFFSET=         u'offset'
STR_PAGELIMIT=      u'page_limit'
STR_PICTURES=       u'pictures'
STR_Q=              u'q'
STR_QUERY=          u'query'
STR_RESULT=         u'result'
STR_STREAMURL=      u'stream_url'
STR_STREAMINFO=     u'streamInfo'
STR_SUCCESS=        u'success'
STR_TAG=            u'tag'
STR_TAGS=           u'tags'
STR_THUMBNAIL=      u'thumbnail'
STR_TITLE=          u'title'
STR_TRACK=          u'track'
STR_TRACKNUMBER=    u'tracknumber'
STR_TYPE=           u'type'
STR_URL=            u'url'
STR_USER=           u'user'
STR_YEAR=           u'year'
STR_REDIRECTURI=    u'http://forum.kodi.tv/showthread.php?tid=116386'

STR_THUMB_SIZES=    {0:u'small',1:u'thumbnail',2:u'medium',3:u'large',4:u'extra_large'}



class Resolver:
    auto=0
    local=1
    offliberty=2
    m4a=3
    mixclouddownloader1=4
    mixclouddownloader2=5

resolver_order=[Resolver.local,
                Resolver.mixclouddownloader1,
                Resolver.offliberty,
                Resolver.mixclouddownloader2]



plugin_handle=int(sys.argv[1])
__addon__ =xbmcaddon.Addon('plugin.audio.mixcloud')

__ICON__ = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'icon.png')


debugenabled=     (__addon__.getSetting('debug')=='true')
limit=            (1+int(__addon__.getSetting('page_limit')))*10
thumb_size=       STR_THUMB_SIZES[int(__addon__.getSetting('thumb_size'))]
resolverid_orig=  int(__addon__.getSetting('resolver'))
resolverid_curr=  int(__addon__.getSetting('resolver'))
oath_code=        __addon__.getSetting('oath_code')
access_token=     __addon__.getSetting('access_token')
ext_info=        (__addon__.getSetting('ext_info')=='true')



STRLOC_COMMON_MORE=               __addon__.getLocalizedString(30001)
STRLOC_COMMON_RESOLVER_ERROR=     __addon__.getLocalizedString(30002)
STRLOC_COMMON_TOKEN_ERROR=        __addon__.getLocalizedString(30003)
STRLOC_COMMON_AUTH_CODE=          __addon__.getLocalizedString(30004)
STRLOC_MAINMENU_HOT=              __addon__.getLocalizedString(30100)
STRLOC_MAINMENU_FAVORITES=        __addon__.getLocalizedString(30101)
STRLOC_MAINMENU_FOLLOWINGS=       __addon__.getLocalizedString(30102)
STRLOC_MAINMENU_CATEGORIES=       __addon__.getLocalizedString(30103)
STRLOC_MAINMENU_SEARCH=           __addon__.getLocalizedString(30104)
STRLOC_MAINMENU_HISTORY=          __addon__.getLocalizedString(30105)
STRLOC_MAINMENU_JACKYNIX=         __addon__.getLocalizedString(30106)
STRLOC_MAINMENU_FEED=             __addon__.getLocalizedString(30107)
STRLOC_MAINMENU_FOLLOWERS=        __addon__.getLocalizedString(30108)
STRLOC_MAINMENU_LISTENS=          __addon__.getLocalizedString(30109)
STRLOC_MAINMENU_UPLOADS=          __addon__.getLocalizedString(30113)
STRLOC_MAINMENU_PLAYLISTS=        __addon__.getLocalizedString(30114)
STRLOC_MAINMENU_LISTENLATER=      __addon__.getLocalizedString(30115)
STRLOC_MAINMENU_LOGIN=            __addon__.getLocalizedString(30116)
STRLOC_MAINMENU_LOGOFF=           __addon__.getLocalizedString(30117)

STRLOC_SEARCHMENU_CLOUDCASTS=     __addon__.getLocalizedString(30200)
STRLOC_SEARCHMENU_USERS=          __addon__.getLocalizedString(30201)
STRLOC_SEARCHMENU_HISTORY=        __addon__.getLocalizedString(30202)

STRLOC_CONTEXTMENU_ADDFAVORITE=   __addon__.getLocalizedString(30300)
STRLOC_CONTEXTMENU_DELFAVORITE=   __addon__.getLocalizedString(30301)
STRLOC_CONTEXTMENU_ADDFOLLOWING=  __addon__.getLocalizedString(30302)
STRLOC_CONTEXTMENU_DELFOLLOWING=  __addon__.getLocalizedString(30303)
STRLOC_CONTEXTMENU_ADDLISTENLATER=__addon__.getLocalizedString(30304)
STRLOC_CONTEXTMENU_DELLISTENLATER=__addon__.getLocalizedString(30305)



def add_audio_item(infolabels,parameters={},img='',total=0):
    listitem=xbmcgui.ListItem(infolabels[STR_TITLE],infolabels[STR_ARTIST],iconImage=img,thumbnailImage=img)
    listitem.setInfo('Music',infolabels)
    listitem.setProperty('IsPlayable','true')
    url=sys.argv[0]+'?'+urllib.urlencode(parameters)
    if access_token!='':
        commands=[]
        if mode==MODE_FAVORITES:
            commands.append((STRLOC_CONTEXTMENU_DELFAVORITE,"XBMC.RunPlugin(%s?mode=%d&key=%s)"%(sys.argv[0],MODE_DELFAVORITE,parameters.get(STR_KEY,""))))
        else:
            commands.append((STRLOC_CONTEXTMENU_ADDFAVORITE,"XBMC.RunPlugin(%s?mode=%d&key=%s)"%(sys.argv[0],MODE_ADDFAVORITE,parameters.get(STR_KEY,""))))
        if mode==MODE_LISTENLATER:
            commands.append((STRLOC_CONTEXTMENU_DELLISTENLATER,"XBMC.RunPlugin(%s?mode=%d&key=%s)"%(sys.argv[0],MODE_DELLISTENLATER,parameters.get(STR_KEY,""))))
        else:
            commands.append((STRLOC_CONTEXTMENU_ADDLISTENLATER,"XBMC.RunPlugin(%s?mode=%d&key=%s)"%(sys.argv[0],MODE_ADDLISTENLATER,parameters.get(STR_KEY,""))))
        commands.append((STRLOC_CONTEXTMENU_ADDFOLLOWING,"XBMC.RunPlugin(%s?mode=%d&key=%s)"%(sys.argv[0],MODE_ADDFOLLOWING,parameters.get(STR_USER,""))))
        listitem.addContextMenuItems(commands)       
    xbmcplugin.addDirectoryItem(plugin_handle,url,listitem,isFolder=False,totalItems=total)



def add_folder_item(name,infolabels={},parameters={},img=''):
    if not infolabels:
        infolabels={STR_TITLE:name}
    listitem=xbmcgui.ListItem(name,name,iconImage=img,thumbnailImage=img)
    listitem.setInfo('Music',infolabels)
    url=sys.argv[0]+'?'+urllib.urlencode(parameters)
    if access_token!='':
        commands=[]
        if mode==MODE_FOLLOWINGS:
            commands.append((STRLOC_CONTEXTMENU_DELFOLLOWING,"XBMC.RunPlugin(%s?mode=%d&key=%s)"%(sys.argv[0],MODE_DELFOLLOWING,parameters.get(STR_KEY,""))))
        elif (mode==MODE_FOLLOWERS) or (mode==MODE_USERS):
            commands.append((STRLOC_CONTEXTMENU_ADDFOLLOWING,"XBMC.RunPlugin(%s?mode=%d&key=%s)"%(sys.argv[0],MODE_ADDFOLLOWING,parameters.get(STR_KEY,""))))
        listitem.addContextMenuItems(commands)       
    return xbmcplugin.addDirectoryItem(plugin_handle,url,listitem,isFolder=True)



def show_home_menu():
    if access_token!='':
        add_folder_item(name=STRLOC_MAINMENU_FOLLOWINGS,parameters={STR_MODE:MODE_FOLLOWINGS},img=get_icon('yourfollowings.png'))
        add_folder_item(name=STRLOC_MAINMENU_FOLLOWERS,parameters={STR_MODE:MODE_FOLLOWERS},img=get_icon('yourfollowers.png'))
        add_folder_item(name=STRLOC_MAINMENU_FAVORITES,parameters={STR_MODE:MODE_FAVORITES},img=get_icon('yourfavorites.png'))
        add_folder_item(name=STRLOC_MAINMENU_LISTENS,parameters={STR_MODE:MODE_LISTENS},img=get_icon('yourlistens.png'))
        add_folder_item(name=STRLOC_MAINMENU_UPLOADS,parameters={STR_MODE:MODE_UPLOADS},img=get_icon('youruploads.png'))
        add_folder_item(name=STRLOC_MAINMENU_PLAYLISTS,parameters={STR_MODE:MODE_PLAYLISTS},img=get_icon('yourplaylists.png'))
        add_folder_item(name=STRLOC_MAINMENU_LISTENLATER,parameters={STR_MODE:MODE_LISTENLATER},img=get_icon('listenlater.png'))
        add_folder_item(name=STRLOC_MAINMENU_LOGOFF+'...',parameters={STR_MODE:MODE_LOGOFF})
    else:
        add_folder_item(name=STRLOC_MAINMENU_LOGIN,parameters={STR_MODE:MODE_LOGIN})
    add_folder_item(name=STRLOC_MAINMENU_CATEGORIES,parameters={STR_MODE:MODE_CATEGORIES,STR_OFFSET:0},img=get_icon('categories.png'))
    add_folder_item(name=STRLOC_MAINMENU_SEARCH,parameters={STR_MODE:MODE_SEARCH},img=get_icon('search.png'))
    add_folder_item(name=STRLOC_MAINMENU_HISTORY,parameters={STR_MODE:MODE_HISTORY},img=get_icon('history.png'))
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def show_feed_menu(offset):
    if check_profile_state():
        found=get_cloudcasts(URL_FEED,{STR_ACCESS_TOKEN:access_token,STR_LIMIT:limit,STR_OFFSET:offset})
        if found==limit:
            add_folder_item(name=STRLOC_COMMON_MORE,parameters={STR_MODE:MODE_FEED,STR_OFFSET:offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def show_favorites_menu(offset):
    if check_profile_state():
        found=get_cloudcasts(URL_FAVORITES,{STR_ACCESS_TOKEN:access_token,STR_LIMIT:limit,STR_OFFSET:offset})
        if found==limit:
            add_folder_item(name=STRLOC_COMMON_MORE,parameters={STR_MODE:MODE_FAVORITES,STR_OFFSET:offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def show_followings_menu(offset):
    if check_profile_state():
        found=get_users(URL_FOLLOWINGS,{STR_ACCESS_TOKEN:access_token,STR_LIMIT:limit,STR_OFFSET:offset})
        if found==limit:
            add_folder_item(name=STRLOC_COMMON_MORE,parameters={STR_MODE:MODE_FOLLOWINGS,STR_KEY:key,STR_OFFSET:offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def show_hot_menu(offset):
    found=get_cloudcasts(URL_HOT,{STR_LIMIT:limit,STR_OFFSET:offset})
    if found==limit:
        add_folder_item(name=STRLOC_COMMON_MORE,parameters={STR_MODE:MODE_HOT,STR_OFFSET:offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def show_categories_menu(key,offset):
    if key=='':
        get_categories(URL_CATEGORIES)
    else:
        found=get_cloudcasts(URL_API+key[1:len(key)-1]+'/cloudcasts/',{STR_LIMIT:limit,STR_OFFSET:offset})
        if found==limit:
            add_folder_item(name=STRLOC_COMMON_MORE,parameters={STR_MODE:MODE_CATEGORIES,STR_KEY:key,STR_OFFSET:offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def show_followers_menu(offset):
    if check_profile_state():
        found=get_users(URL_FOLLOWERS,{STR_ACCESS_TOKEN:access_token,STR_LIMIT:limit,STR_OFFSET:offset})
        if found==limit:
            add_folder_item(name=STRLOC_COMMON_MORE,parameters={STR_MODE:MODE_FOLLOWERS,STR_KEY:key,STR_OFFSET:offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def show_listens_menu(offset):
    if check_profile_state():
        found=get_cloudcasts(URL_LISTENS,{STR_ACCESS_TOKEN:access_token,STR_LIMIT:limit,STR_OFFSET:offset})
        if found==limit:
            add_folder_item(name=STRLOC_COMMON_MORE,parameters={STR_MODE:MODE_LISTENS,STR_OFFSET:offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def show_uploads_menu(offset):
    if check_profile_state():
        found=get_cloudcasts(URL_UPLOADS,{STR_ACCESS_TOKEN:access_token,STR_LIMIT:limit,STR_OFFSET:offset})
        if found==limit:
            add_folder_item(name=STRLOC_COMMON_MORE,parameters={STR_MODE:MODE_UPLOADS,STR_OFFSET:offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def show_listenlater_menu(offset):
    if check_profile_state():
        found=get_cloudcasts(URL_LISTENLATER,{STR_ACCESS_TOKEN:access_token,STR_LIMIT:limit,STR_OFFSET:offset})
        if found==limit:
            add_folder_item(name=STRLOC_COMMON_MORE,parameters={STR_MODE:MODE_LISTENLATER,STR_OFFSET:offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def show_playlists_menu(key,offset):
    if key=="":
        if check_profile_state():
            found=get_playlists(URL_PLAYLISTS,{STR_ACCESS_TOKEN:access_token,STR_LIMIT:limit,STR_OFFSET:offset})
            if found==limit:
                add_folder_item(name=STRLOC_COMMON_MORE,parameters={STR_MODE:MODE_PLAYLISTS,STR_OFFSET:offset+limit})
    else:
        found=get_cloudcasts(URL_API+key[1:len(key)-1]+'/cloudcasts/',{STR_LIMIT:limit,STR_OFFSET:offset})
        if found==limit:
            add_folder_item(name=STRLOC_COMMON_MORE,parameters={STR_MODE:MODE_PLAYLISTS,STR_KEY:key,STR_OFFSET:offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def show_users_menu(key,offset):
    found=get_cloudcasts(URL_API+key[1:len(key)-1]+'/cloudcasts/',{STR_LIMIT:limit,STR_OFFSET:offset})
    if found==limit:
        add_folder_item(name=STRLOC_COMMON_MORE,parameters={STR_MODE:MODE_USERS,STR_KEY:key,STR_OFFSET:offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def show_search_menu(key,query,offset):
    if key=='':
        add_folder_item(name=STRLOC_SEARCHMENU_CLOUDCASTS,parameters={STR_MODE:MODE_SEARCH,STR_KEY:STR_CLOUDCAST,STR_OFFSET:0})
        add_folder_item(name=STRLOC_SEARCHMENU_USERS,parameters={STR_MODE:MODE_SEARCH,STR_KEY:STR_USER,STR_OFFSET:0})
        add_folder_item(name=STRLOC_SEARCHMENU_HISTORY,parameters={STR_MODE:MODE_SEARCH,STR_KEY:STR_HISTORY,STR_OFFSET:0})
        xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)
    else:
        if key==STR_HISTORY:
            show_history_search_menu(offset)
        else:
            if query=='':
                query=get_query()
            else:
                query=urllib.unquote_plus(query)
            if query!='':
                found=0
                if key==STR_CLOUDCAST:
                    found=get_cloudcasts(URL_SEARCH,{STR_Q:query,STR_TYPE:key,STR_LIMIT:limit,STR_OFFSET:offset})
                elif key==STR_USER:
                    found=get_users(URL_SEARCH,{STR_Q:query,STR_TYPE:key,STR_LIMIT:limit,STR_OFFSET:offset})
                if found==limit:
                    add_folder_item(name=STRLOC_COMMON_MORE,parameters={STR_MODE:MODE_SEARCH,STR_KEY:key,STR_QUERY:query,STR_OFFSET:offset+limit})
                add_to_settinglist('search_history_list',urllib.urlencode({key:query}),'search_history_max')
                xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def show_history_menu(offset):
    playhistmax=(1+int(__addon__.getSetting('play_history_max')))*10
    if __addon__.getSetting('play_history_list'):
        playhistlist=__addon__.getSetting('play_history_list').split(', ')
        while len(playhistlist)>playhistmax:
            playhistlist.pop()
        index=1
        total=len(playhistlist)
        while len(playhistlist)>0:
            key=playhistlist.pop(0)
            if get_cloudcast(URL_API+key[1:len(key)],{},index,total):
                index=index+1
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def check_profile_state():
    global oath_code
    global access_token

    # ask for code if no token provided yet
    if not access_token:
        log_if_debug('No access_token found')
        ask=True
        while ask:
            ask=xbmcgui.Dialog().yesno('Mixcloud', STRLOC_COMMON_TOKEN_ERROR, STRLOC_COMMON_AUTH_CODE)
            if ask:
                oath_code=get_query(oath_code)
                __addon__.setSetting('oath_code',oath_code)
                __addon__.setSetting('access_token','')
                if oath_code!='':
                    try:
                        values={
                                'client_id' : STR_CLIENTID,
                                'redirect_uri' : STR_REDIRECTURI,
                                'client_secret' : STR_CLIENTSECRET,
                                'code' : oath_code
                               }
                        headers={
                                 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.27 Safari/537.36',
                                 'Referer' : 'https://www.mixcloud.com/'
                                }
                        postdata = urllib.urlencode(values)
                        log_if_debug('Getting access token ' + URL_TOKEN + '?' + postdata)
                        request = urllib2.Request('https://www.mixcloud.com/oauth/access_token', postdata, headers, 'https://www.mixcloud.com/')
                        h = urllib2.urlopen(request)
                        content=h.read()
                        json_content=json.loads(content)
                        if STR_ACCESS_TOKEN in json_content and json_content[STR_ACCESS_TOKEN] :
                            log_if_debug('Access_token received')
                            access_token=json_content[STR_ACCESS_TOKEN]
                            __addon__.setSetting('access_token',access_token)
                        else:
                            log_if_debug('No access_token received')
                            log_if_debug(json_content)
                    except:
                        log_always('oath_code failed error=%s' % (sys.exc_info()[1]))

                ask=((oath_code!='') and (access_token==''))

    return access_token!=''



def logoff():
    global oath_code
    global access_token
    if xbmcgui.Dialog().yesno('Mixcloud', STRLOC_MAINMENU_LOGOFF + '?'):
        oath_code=''
        access_token=''
        __addon__.setSetting('oath_code','')
        __addon__.setSetting('access_token','')



def show_jackynix_menu(offset):
    show_users_menu('/jackyNIX/',0)



def show_history_search_menu(offset):
    searchhistmax=(1+int(__addon__.getSetting('search_history_max')))*10
    if __addon__.getSetting('search_history_list'):
        searchhistlist=__addon__.getSetting('search_history_list').split(', ')
        while len(searchhistlist)>searchhistmax:
            searchhistlist.pop()
        total=len(searchhistlist)
        while len(searchhistlist)>0:
            pair=searchhistlist.pop(0).split('=')
            key=urllib.unquote_plus(pair[0])
            query=urllib.unquote_plus(pair[1])
            add_folder_item(name=key+' = "'+query+'"',parameters={STR_MODE:MODE_SEARCH,STR_KEY:key,STR_QUERY:query,STR_OFFSET:0})
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def play_cloudcast(key):
    url=get_stream(key)
    if url:
        _infolabels=get_cloudcast(URL_API[:-1]+key,{},True)
        _listitem=xbmcgui.ListItem(label=_infolabels[STR_TITLE],label2=_infolabels[STR_ARTIST],path=url)
        _listitem.setInfo(type='Music',infoLabels=_infolabels)
        xbmcplugin.setResolvedUrl(handle=plugin_handle,succeeded=True,listitem=_listitem)
        add_to_settinglist('play_history_list',key,'play_history_max')
        log_if_debug('Playing '+url)
    else:
        log_if_debug('Stop player')
        xbmcplugin.setResolvedUrl(handle=plugin_handle,succeeded=False,listitem=xbmcgui.ListItem())



def get_cloudcasts(url,parameters):
    found=0
    if len(parameters)>0:
        url=url+'?'+urllib.urlencode(parameters)
    log_if_debug('Get cloudcasts '+url)
    h=urllib2.urlopen(url)
    content=h.read()
    json_content=json.loads(content)
    if STR_DATA in json_content and json_content[STR_DATA] :
        json_data=json_content[STR_DATA]
        total=len(json_data)+1
        json_tracknumber=0
        if STR_OFFSET in parameters:
            json_tracknumber=parameters[STR_OFFSET]
        else:
            json_tracknumber=0
        for json_cloudcast in json_data:
            json_tracknumber=json_tracknumber+1
            if ext_info:
                infolabels = get_cloudcast(URL_API[:-1]+json_cloudcast[STR_KEY],{},json_tracknumber,total)
            else:
                infolabels = add_cloudcast(json_tracknumber,json_cloudcast,total)
            if len(infolabels)>0:
                found=found+1
    return found



def get_cloudcast(url,parameters,index=1,total=0,forinfo=False):
    if len(parameters)>0:
        url=url+'?'+urllib.urlencode(parameters)
    log_if_debug('Get cloudcast '+url)
    try:
        h=urllib2.urlopen(url)
        content=h.read()
        json_cloudcast=json.loads(content)
        return add_cloudcast(index,json_cloudcast,total,forinfo)
    except:
        log_always('Get cloudcast failed error=%s' % (sys.exc_info()[1]))
    return {}



def add_cloudcast(index,json_cloudcast,total,forinfo=False):
    if STR_NAME in json_cloudcast and json_cloudcast[STR_NAME]:
        json_name=json_cloudcast[STR_NAME]
        json_key=''
        json_year=0
        json_date=''
        json_length=0
        json_userkey=''
        json_username=''
        json_image=''
        json_comment=''
        json_genre=''
        if STR_KEY in json_cloudcast and json_cloudcast[STR_KEY]:
            json_key=json_cloudcast[STR_KEY]
        if STR_CREATEDTIME in json_cloudcast and json_cloudcast[STR_CREATEDTIME]:
            json_created=json_cloudcast[STR_CREATEDTIME]
            json_structtime=time.strptime(json_created[0:10],'%Y-%m-%d')
            json_year=int(time.strftime('%Y',json_structtime))
            json_date=time.strftime('%d/%m/Y',json_structtime)
        if STR_AUDIOLENGTH in json_cloudcast and json_cloudcast[STR_AUDIOLENGTH]:
            json_length=json_cloudcast[STR_AUDIOLENGTH]
        if STR_USER in json_cloudcast and json_cloudcast[STR_USER]:
            json_user=json_cloudcast[STR_USER]
            if STR_KEY in json_user and json_user[STR_KEY]:
                json_userkey=json_user[STR_KEY]
            if STR_NAME in json_user and json_user[STR_NAME]:
                json_username=json_user[STR_NAME]
        if STR_PICTURES in json_cloudcast and json_cloudcast[STR_PICTURES]:
            json_pictures=json_cloudcast[STR_PICTURES]
            if thumb_size in json_pictures and json_pictures[thumb_size]:
                json_image=json_pictures[thumb_size]
        if STR_DESCRIPTION in json_cloudcast and json_cloudcast[STR_DESCRIPTION]:
            json_comment=json_cloudcast[STR_DESCRIPTION].encode('ascii', 'ignore')
        if STR_TAGS in json_cloudcast and json_cloudcast[STR_TAGS]:
            json_tags=json_cloudcast[STR_TAGS]
            for json_tag in json_tags:
                if STR_NAME in json_tag and json_tag[STR_NAME]:
                    if json_genre!='':
                        json_genre=json_genre+', '
                    json_genre=json_genre+json_tag[STR_NAME]
        infolabels = {STR_COUNT:index,STR_TRACKNUMBER:index,STR_TITLE:json_name,STR_ARTIST:json_username,STR_DURATION:json_length,STR_YEAR:json_year,STR_DATE:json_date,STR_COMMENT:json_comment,STR_GENRE:json_genre}
        if not forinfo:
            add_audio_item(infolabels,
                           {STR_MODE:MODE_PLAY,STR_KEY:json_key,STR_USER:json_userkey},
                           json_image,
                           total)

        return infolabels
    else:
        return {}



def get_stream_offliberty(cloudcast_key):
    ck=URL_MIXCLOUD[:-1]+cloudcast_key
    log_if_debug('Resolving offliberty cloudcast stream for '+ck)
    for retry in range(1, 2):
        try:
            values={
                    'track' : ck,
                    'refext' : 'https://www.google.com/'
                   }
            headers={
                     'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.27 Safari/537.36',
                     'Referer' : 'http://offliberty.com/'
                    }
            postdata = urllib.urlencode(values)
            request = urllib2.Request('http://offliberty.com/off04.php', postdata, headers, 'http://offliberty.com/')
            response = urllib2.urlopen(request)
            data=response.read()
            match=re.search('href="(.*)" class="download"', data)
            if match:
                return match.group(1)
            else:
                log_if_debug('Wrong response try=%s code=%s len=%s, trying again...' % (retry, response.getcode(), len(data)))
        except:
            log_always('Unexpected error try=%s error=%s, trying again...' % (retry, sys.exc_info()[0]))



def get_stream_local(cloudcast_key):
    ck=URL_MIXCLOUD[:-1]+cloudcast_key
    log_if_debug('Locally resolving cloudcast stream for '+ck)
    try:
        headers={
                 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.27 Safari/537.36',
                 'Referer' : URL_MIXCLOUD
                }
        request = urllib2.Request(ck, headers=headers, origin_req_host=URL_MIXCLOUD)
        response = urllib2.urlopen(request)
        data=response.read()
        match=re.search('<script id="relay-data" type="text/x-mixcloud">\[(.*)', data)
        if match:
            match=re.search('(.*)\]</script>', match.group(1))
            if match:
                decoded=match.group(1).replace('&quot;','"')
                json_content=json.loads(decoded)
                json_isexclusive=False
                json_url=None
                for json_item in json_content:
                    if STR_CLOUDCASTLOOKUP in json_item and json_item[STR_CLOUDCASTLOOKUP]:
                        json_cloudcastLookupA = json_item[STR_CLOUDCASTLOOKUP]
                        if STR_DATA in json_cloudcastLookupA and json_cloudcastLookupA[STR_DATA]:
                            json_data = json_cloudcastLookupA[STR_DATA]
                            if STR_CLOUDCASTLOOKUP in json_data and json_data[STR_CLOUDCASTLOOKUP]:
                                json_cloudcastLookupB = json_data[STR_CLOUDCASTLOOKUP]
                                if STR_ISEXCLUSIVE in json_cloudcastLookupB and json_cloudcastLookupB[STR_ISEXCLUSIVE]:
                                    json_isexclusive = json_cloudcastLookupB[STR_ISEXCLUSIVE]
                                if STR_STREAMINFO in json_cloudcastLookupB and json_cloudcastLookupB[STR_STREAMINFO]:
                                    json_streaminfo = json_cloudcastLookupB[STR_STREAMINFO]
                                    if STR_URL in json_streaminfo and json_streaminfo[STR_URL]:
                                        json_url = json_streaminfo[STR_URL]
                                    elif STR_HLSURL in json_streaminfo and json_streaminfo[STR_HLSURL]:
                                        json_url = json_streaminfo[STR_HLSURL]
                                    elif STR_DASHURL in json_streaminfo and json_streaminfo[STR_DASHURL]:
                                        json_url = json_streaminfo[STR_DASHURL]
                    if json_url:
                        break

                if json_url:
                    log_if_debug('encoded url: '+json_url)
                    decoded_url=base64.b64decode(json_url)
                    url=''.join(chr(ord(a) ^ ord(b)) for a,b in zip(decoded_url,cycle(STR_MAGICSTRING)))
                    log_if_debug('url: '+url)
                    return url
                elif json_isexclusive:
                    log_if_debug('Cloudcast is exclusive')
                    return STR_ISEXCLUSIVE
                else:
                    log_if_debug('Unable to find url in json')
            else:
                log_if_debug('Unable to resolve (match 2)')
        else:
            log_if_debug('Unable to resolve (match 1)')
    except Exception as e:
        log_if_debug('Unable to resolve: ' + str(e))



def get_stream_m4a(cloudcast_key):
    ck=URL_MIXCLOUD[:-1]+cloudcast_key
    log_if_debug('Resolving m4a cloudcast stream for '+ck)
#    headers={
#             'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.27 Safari/537.36',
#             'Referer' : URL_MIXCLOUD
#            }
#    request = urllib2.Request(ck, headers=headers, origin_req_host=URL_MIXCLOUD)
#    response = urllib2.urlopen(request)
#    data=response.read()
#    match=re.search('m-preview="(.*)" m-preview-light', data)
#    if match:
#        try:
#            log_if_debug('m-preview = '+match.group(1))
#            m4aurl=match.group(1).replace('audiocdn','stream')
#            m4aurl=m4aurl.replace('https/','http')
#            m4aurl=m4aurl.replace('/previews/','/secure/c/m4a/64/')
#            m4aurl=m4aurl.replace('mp3','m4a?sig=***TODO***')
#            log_if_debug('m4a url = '+m4aurl)
#            return m4aurl
#        except:
#            log_always('Unexpected error resolving m4a error=%s' % (sys.exc_info()[0]))
#    else:
#        log_if_debug('Unable to resolve (match)')



def get_stream_mixclouddownloader(cloudcast_key,linknr):
    ck=URL_MIXCLOUD[:-1]+cloudcast_key
    log_if_debug('Resolving mixcloud-downloader cloudcast stream for '+ck)
    log_if_debug('Link version %d' % linknr)
    try:
        headers={
                    'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.27 Safari/537.36',
                    'Referer' : 'http://www.mixcloud-downloader.com/'
                }

        values={
                    'url' : ck,
               }
        postdata = urllib.urlencode(values)
        request = urllib2.Request('http://www.mixcloud-downloader.com/download/', postdata, headers, 'http://www.mixcloud-downloader.com/')
        response = urllib2.urlopen(request)
        data=response.read()
        if linknr==1:
            match=re.search('a class="btn btn-secondary btn-sm"(.*)', data, re.DOTALL)
            if match:
                match=re.search('href="(.*)"', match.group(1))
        if linknr==2:
            match=re.search('URL from Mixcloud: <br /> <a href="(.*)"', data)
        if match:
            log_if_debug('match found ' + match.group(1))
            return match.group(1)
        else:
            log_if_debug('Wrong response code=%s len=%s' % (response.getcode(), len(data)))
    except Exception as e:
        log_if_debug('Unable to resolve: ' + str(e))



def get_stream_mixclouddownloader1(cloudcast_key):
    return get_stream_mixclouddownloader(cloudcast_key,1)



def get_stream_mixclouddownloader2(cloudcast_key):
    return get_stream_mixclouddownloader(cloudcast_key,2)



def get_stream(cloudcast_key):
    global resolverid_curr
    global resolverid_orig

    if not resolverid_curr in resolver_order:
        resolverid_curr=resolver_order[0]

    resolver_functions={Resolver.local : get_stream_local,
                        Resolver.offliberty : get_stream_offliberty,
                        Resolver.m4a : get_stream_m4a,
                        Resolver.mixclouddownloader1 : get_stream_mixclouddownloader1,
                        Resolver.mixclouddownloader2 : get_stream_mixclouddownloader2}

    strm_url=None
    strm_isexclusive=False
    while not (strm_url or xbmc.Monitor().abortRequested()):
        strm_url=resolver_functions[resolverid_curr](cloudcast_key)

        # local resolver can detect exclusive cloudcasts
        if strm_url==STR_ISEXCLUSIVE:
            if resolverid_orig==Resolver.local:
                strm_isexclusive=True
            strm_url=None

        # resolver failed
        if not strm_url:
            if (resolverid_orig!=Resolver.auto) and (resolverid_curr==resolverid_orig) and (not strm_isexclusive):
                dialog=xbmcgui.Dialog()
                if not dialog.yesno('MixCloud',STRLOC_COMMON_RESOLVER_ERROR):
                    break

            # try next resolver
            resolverid_index=resolver_order.index(resolverid_curr)+1
            if resolverid_index>=len(resolver_order):
                resolverid_index=0
            resolverid_curr=resolver_order[resolverid_index]

            # stop when tried all
            if resolverid_curr==resolverid_orig:
                break
        else:
            if (resolverid_orig!=Resolver.auto) and (resolverid_curr!=resolverid_orig) and (not strm_isexclusive):
                __addon__.setSetting('resolver',str(resolverid_curr))
                resolverid_orig=resolverid_curr
            

    return strm_url



def get_playlists(url,parameters):
    found=0
    if len(parameters)>0:
        url=url+'?'+urllib.urlencode(parameters)
    h=urllib2.urlopen(url)
    content=h.read()
    json_content=json.loads(content)
    if STR_DATA in json_content and json_content[STR_DATA]:
        json_data=json_content[STR_DATA]
        for json_category in json_data:
            if STR_NAME in json_category and json_category[STR_NAME]:
                json_name=json_category[STR_NAME]
                json_key=''
                if STR_KEY in json_category and json_category[STR_KEY]:
                    json_key=json_category[STR_KEY]
                add_folder_item(name=json_name,parameters={STR_MODE:MODE_PLAYLISTS,STR_KEY:json_key})
                found=found+1
    return found



def get_categories(url):
    h=urllib2.urlopen(url)
    content=h.read()
    json_content=json.loads(content)
    if STR_DATA in json_content and json_content[STR_DATA]:
        json_data=json_content[STR_DATA]
        for json_category in json_data:
            if STR_NAME in json_category and json_category[STR_NAME]:
                json_name=json_category[STR_NAME]
                json_key=''
                json_format=''
                json_thumbnail=''
                if STR_KEY in json_category and json_category[STR_KEY]:
                    json_key=json_category[STR_KEY]
                if STR_FORMAT in json_category and json_category[STR_FORMAT]:
                    json_format=json_category[STR_FORMAT]
                if STR_PICTURES in json_category and json_category[STR_PICTURES]:
                    json_pictures=json_category[STR_PICTURES]
                    if thumb_size in json_pictures and json_pictures[thumb_size]:
                        json_thumbnail=json_pictures[thumb_size]
                add_folder_item(name=json_name,parameters={STR_MODE:MODE_CATEGORIES,STR_KEY:json_key},img=json_thumbnail)



def get_users(url,parameters):
    found=0
    if len(parameters)>0:
        url=url+'?'+urllib.urlencode(parameters)
    h=urllib2.urlopen(url)
    content=h.read()
    json_content=json.loads(content)
    if STR_DATA in json_content and json_content[STR_DATA]:
        json_data=json_content[STR_DATA]
        for json_user in json_data:
            if STR_NAME in json_user and json_user[STR_NAME]:
                json_name=json_user[STR_NAME]
                json_key=''
                json_thumbnail=''
                if STR_KEY in json_user and json_user[STR_KEY]:
                    json_key=json_user[STR_KEY]
                if STR_PICTURES in json_user and json_user[STR_PICTURES]:
                    json_pictures=json_user[STR_PICTURES]
                    if thumb_size in json_pictures and json_pictures[thumb_size]:
                        json_thumbnail=json_pictures[thumb_size]
                add_folder_item(name=json_name,parameters={STR_MODE:MODE_USERS,STR_KEY:json_key},img=json_thumbnail)
                found=found+1
    return found



def favoritefollow(urltmp,key,action):
    url=urltmp.replace('{0}',key)+"?"+urllib.urlencode({STR_ACCESS_TOKEN:access_token})
    log_if_debug(action + ': ' + url)
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    request = urllib2.Request(url, data='none')
    request.get_method = lambda: action
    response = urllib2.urlopen(request)
    data = response.read()
    json_data=json.loads(data)
    json_info=''
    if STR_RESULT in json_data and json_data[STR_RESULT]:
        json_result=json_data[STR_RESULT]
        if STR_MESSAGE in json_result and json_result[STR_MESSAGE]:
            json_info=json_result[STR_MESSAGE]
            if not((STR_SUCCESS in json_result) and (json_result[STR_SUCCESS]==True)):
                json_info=json_info+'\nFAILED!'
    if json_info=='':
        json_info='Unknown error occured.'
        log_if_debug(data)
    xbmcgui.Dialog().ok('Mixcloud',json_info)
    return ''



def get_query(query=''):
    keyboard=xbmc.Keyboard(query)
    keyboard.doModal()
    if keyboard.isConfirmed():
        query=keyboard.getText()
    else:
        query=''
    return query;
    


def get_icon(iconname):
    return xbmc.translatePath( os.path.join( __addon__.getAddonInfo('path').decode("utf-8"), 'resources', 'icons', iconname ).encode("utf-8") ).decode("utf-8")



def parameters_string_to_dict(parameters):
    paramDict={}
    if parameters:
        paramPairs=parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits=paramsPair.split('=')
            if len(paramSplits)==2:
                paramDict[paramSplits[0]]=paramSplits[1]
    return paramDict



def add_to_settinglist(name,value,maxname):
    max=(1+int(__addon__.getSetting(maxname)))*10
    settinglist=[]
    if __addon__.getSetting(name):
        settinglist=__addon__.getSetting(name).split(', ')
    while settinglist.count(value)>0:
        settinglist.remove(value)
    settinglist.insert(0,value)
    while len(settinglist)>max:
        settinglist.pop()
    __addon__.setSetting(name,', '.join(settinglist))



def log_if_debug(message):
    if debugenabled:
        xbmc.log(msg='MIXCLOUD '+message,level=xbmc.LOGNOTICE)



def log_always(message):
    xbmc.log(msg='MIXCLOUD '+message,level=xbmc.LOGERROR)



params=parameters_string_to_dict(urllib.unquote(sys.argv[2]))
mode=int(params.get(STR_MODE,"0"))
offset=int(params.get(STR_OFFSET,"0"))
key=params.get(STR_KEY,"")
query=params.get(STR_QUERY,"")

log_if_debug("##########################################################")
log_if_debug("Mode: %s" % mode)
log_if_debug("Offset: %s" % offset)
log_if_debug("Key: %s" % key)
log_if_debug("Query: %s" % query)
log_if_debug("##########################################################")
	
if not sys.argv[2] or mode==MODE_HOME:
    ok=show_home_menu()
elif mode==MODE_LOGIN:
    check_profile_state()
    ok=show_home_menu()
elif mode==MODE_LOGOFF:
    logoff()
    ok=show_home_menu()
elif mode==MODE_FEED:
    ok=show_feed_menu(offset)
elif mode==MODE_FAVORITES:
    ok=show_favorites_menu(offset)
elif mode==MODE_FOLLOWINGS:
    ok=show_followings_menu(offset)
elif mode==MODE_FOLLOWERS:
    ok=show_followers_menu(offset)
elif mode==MODE_LISTENS:
    ok=show_listens_menu(offset)
elif mode==MODE_UPLOADS:
    ok=show_uploads_menu(offset)
elif mode==MODE_LISTENLATER:
    ok=show_listenlater_menu(offset)
elif mode==MODE_PLAYLISTS:
    ok=show_playlists_menu(key,offset)
elif mode==MODE_HOT:
    ok=show_hot_menu(offset)
elif mode==MODE_CATEGORIES:
    ok=show_categories_menu(key,offset)
elif mode==MODE_USERS:
    ok=show_users_menu(key,offset)
elif mode==MODE_SEARCH:
    ok=show_search_menu(key,query,offset)
elif mode==MODE_HISTORY:
    ok=show_history_menu(offset)
elif mode==MODE_JACKYNIX:
    ok=show_jackynix_menu(offset)
elif mode==MODE_PLAY:
    ok=play_cloudcast(key)
elif mode==MODE_ADDFAVORITE:
    ok=favoritefollow(URL_FAVORITE,key,'POST')
elif mode==MODE_DELFAVORITE:
    ok=favoritefollow(URL_FAVORITE,key,'DELETE')
    xbmc.executebuiltin("Container.Refresh")
elif mode==MODE_ADDFOLLOWING:
    ok=favoritefollow(URL_FOLLOW,key,'POST')
elif mode==MODE_DELFOLLOWING:
    ok=favoritefollow(URL_FOLLOW,key,'DELETE')
    xbmc.executebuiltin("Container.Refresh")
elif mode==MODE_ADDLISTENLATER:
    ok=favoritefollow(URL_ADDLISTENLATER,key,'POST')
elif mode==MODE_DELLISTENLATER:
    ok=favoritefollow(URL_ADDLISTENLATER,key,'DELETE')
    xbmc.executebuiltin("Container.Refresh")


# -*- coding: utf-8 -*-

'''
@author: jackyNIX

Copyright (C) 2011-2014 jackyNIX

This file is part of XBMC MixCloud Plugin.

XBMC MixCloud Plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

XBMC MixCloud Plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with XBMC MixCloud Plugin.  If not, see <http://www.gnu.org/licenses/>.
'''



import sys,time
import xbmc,xbmcgui,xbmcplugin,xbmcaddon
import urllib,urllib2
import base64
import simplejson as json
import re
import sys
from itertools import cycle, izip



URL_PLUGIN=    'plugin://music/MixCloud/'
URL_MIXCLOUD=  'http://www.mixcloud.com/'
URL_API=       'http://api.mixcloud.com/'
URL_CATEGORIES='http://api.mixcloud.com/categories/'
URL_HOT=       'http://api.mixcloud.com/popular/hot/'
URL_NEW=       'http://api.mixcloud.com/new/'
URL_POPULAR=   'http://api.mixcloud.com/popular/'
URL_SEARCH=    'http://api.mixcloud.com/search/'
URL_STREAM=    'http://www.mixcloud.com/api/1/cloudcast/{0}.json?embed_type=cloudcast'



MODE_HOME=       0
MODE_HOT=       10
MODE_NEW=       11
MODE_POPULAR=   12
MODE_HISTORY=   13
MODE_CATEGORIES=20
MODE_USERS=     21
MODE_SEARCH=    30
MODE_PLAY=      40



STR_ARTIST=      u'artist'
STR_AUDIOFORMATS=u'audio_formats'
STR_AUDIOLENGTH= u'audio_length'
STR_CLOUDCAST=   u'cloudcast'
STR_COUNT=       u'count'
STR_CREATEDTIME= u'created_time'
STR_DATA=        u'data'
STR_DATE=        u'date'
STR_DURATION=    u'duration'
STR_HISTORY=     u'history'
STR_ID=          u'id'
STR_FORMAT=      u'format'
STR_KEY=         u'key'
STR_LIMIT=       u'limit'
STR_MODE=        u'mode'
STR_MP3=         u'mp3'
STR_NAME=        u'name'
STR_OFFSET=      u'offset'
STR_PAGELIMIT=   u'page_limit'
STR_PICTURES=    u'pictures'
STR_Q=           u'q'
STR_QUERY=       u'query'
STR_TAG=         u'tag'
STR_TAGS=        u'tags'
STR_TITLE=       u'title'
STR_TRACK=       u'track'
STR_TRACKNUMBER= u'tracknumber'
STR_TYPE=        u'type'
STR_USER=        u'user'
STR_YEAR=        u'year'
STR_IMAGE=       u'image'
STR_THUMBNAIL=   u'thumbnail'
STR_STREAMURL=   u'stream_url'

STR_THUMB_SIZES= {0:u'small',1:u'thumbnail',2:u'medium',3:u'large',4:u'extra_large'}



class Resolver:
    local=0
    offliberty=1



plugin_handle=int(sys.argv[1])
__addon__ =xbmcaddon.Addon('plugin.audio.mixcloud')



debugenabled=(__addon__.getSetting('debug')=='true')
limit=       (1+int(__addon__.getSetting('page_limit')))*10
thumb_size=  STR_THUMB_SIZES[int(__addon__.getSetting('thumb_size'))]
resolver=    int(__addon__.getSetting('resolver'))



STRLOC_COMMON_MORE=          __addon__.getLocalizedString(30001)
STRLOC_MAINMENU_HOT=         __addon__.getLocalizedString(30100)
STRLOC_MAINMENU_NEW=         __addon__.getLocalizedString(30101)
STRLOC_MAINMENU_POPULAR=     __addon__.getLocalizedString(30102)
STRLOC_MAINMENU_CATEGORIES=  __addon__.getLocalizedString(30103)
STRLOC_MAINMENU_SEARCH=      __addon__.getLocalizedString(30104)
STRLOC_MAINMENU_HISTORY=     __addon__.getLocalizedString(30105)
STRLOC_SEARCHMENU_CLOUDCASTS=__addon__.getLocalizedString(30110)
STRLOC_SEARCHMENU_USERS=     __addon__.getLocalizedString(30111)
STRLOC_SEARCHMENU_HISTORY=   __addon__.getLocalizedString(30112)



def add_audio_item(infolabels,parameters={},img='',total=0):
    listitem=xbmcgui.ListItem(infolabels[STR_TITLE],infolabels[STR_ARTIST],iconImage=img,thumbnailImage=img)
    listitem.setInfo('Music',infolabels)
    listitem.setProperty('IsPlayable','true')
    url=sys.argv[0]+'?'+urllib.urlencode(parameters)
    xbmcplugin.addDirectoryItem(plugin_handle,url,listitem,isFolder=False,totalItems=total)



def add_folder_item(name,infolabels={},parameters={},img=''):
    if not infolabels:
        infolabels={STR_TITLE:name}
    listitem=xbmcgui.ListItem(name,iconImage=img,thumbnailImage=img)
    listitem.setInfo('Music',infolabels)
    url=sys.argv[0]+'?'+urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=plugin_handle,url=url,listitem=listitem,isFolder=True)



def show_home_menu():
    add_folder_item(name=STRLOC_MAINMENU_HOT,parameters={STR_MODE:MODE_HOT,STR_OFFSET:0})
    add_folder_item(name=STRLOC_MAINMENU_NEW,parameters={STR_MODE:MODE_NEW,STR_OFFSET:0})
    add_folder_item(name=STRLOC_MAINMENU_POPULAR,parameters={STR_MODE:MODE_POPULAR,STR_OFFSET:0})
    add_folder_item(name=STRLOC_MAINMENU_CATEGORIES,parameters={STR_MODE:MODE_CATEGORIES,STR_OFFSET:0})
    add_folder_item(name=STRLOC_MAINMENU_SEARCH,parameters={STR_MODE:MODE_SEARCH})
    add_folder_item(name=STRLOC_MAINMENU_HISTORY,parameters={STR_MODE:MODE_HISTORY})
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def show_hot_menu(offset):
    found=get_cloudcasts(URL_HOT,{STR_LIMIT:limit,STR_OFFSET:offset})
    if found==limit:
        add_folder_item(name=STRLOC_COMMON_MORE,parameters={STR_MODE:MODE_HOT,STR_OFFSET:offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def show_new_menu(offset):
    found=get_cloudcasts(URL_NEW,{STR_LIMIT:limit,STR_OFFSET:offset})
    if found==limit:
        add_folder_item(name=STRLOC_COMMON_MORE,parameters={STR_MODE:MODE_NEW,STR_OFFSET:offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)



def show_popular_menu(offset):
    found=get_cloudcasts(URL_POPULAR,{STR_LIMIT:limit,STR_OFFSET:offset})
    if found==limit:
        add_folder_item(name=STRLOC_COMMON_MORE,parameters={STR_MODE:MODE_POPULAR,STR_OFFSET:offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle,succeeded=True)    



def show_categories_menu(key,offset):
    if key=='':
        get_categories(URL_CATEGORIES)
    else:
        found=get_cloudcasts(URL_API+key[1:len(key)-1]+'/cloudcasts/',{STR_LIMIT:limit,STR_OFFSET:offset})
        if found==limit:
            add_folder_item(name=STRLOC_COMMON_MORE,parameters={STR_MODE:MODE_CATEGORIES,STR_KEY:key,STR_OFFSET:offset+limit})
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
        infolabels=get_cloudcast(URL_API[:-1]+key,{},True)
        listitem=xbmcgui.ListItem(label=infolabels[STR_TITLE],label2=infolabels[STR_ARTIST],iconImage=infolabels[STR_THUMBNAIL],thumbnailImage=infolabels[STR_THUMBNAIL],path=url)
        listitem.setInfo(type='Music',infoLabels=infolabels)
        xbmcplugin.setResolvedUrl(handle=plugin_handle,succeeded=True,listitem=listitem)
        add_to_settinglist('play_history_list',key,'play_history_max')
        if debugenabled:
            print('MIXCLOUD playing '+url)
    else:
        xbmcplugin.setResolvedUrl(handle=plugin_handle,succeeded=False,listitem=xbmcgui.ListItem())



def get_cloudcasts(url,parameters):
    found=0
    if len(parameters)>0:
        url=url+'?'+urllib.urlencode(parameters)
    if debugenabled:
        print('MIXCLOUD '+'get cloudcasts '+url)
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
            infolabels = add_cloudcast(json_tracknumber,json_cloudcast,total);
            if len(infolabels)>0:
                found=found+1
    return found



def get_cloudcast(url,parameters,index=1,total=0,forinfo=False):
    if len(parameters)>0:
        url=url+'?'+urllib.urlencode(parameters)
    if debugenabled:
        print('MIXCLOUD '+'get cloudcast '+url)
    h=urllib2.urlopen(url)
    content=h.read()
    json_cloudcast=json.loads(content)
    return add_cloudcast(index,json_cloudcast,total,forinfo)



def add_cloudcast(index,json_cloudcast,total,forinfo=False):
    if STR_NAME in json_cloudcast and json_cloudcast[STR_NAME]:
        json_name=json_cloudcast[STR_NAME]
        json_key=''
        json_year=0
        json_date=''
        json_length=0
        json_username=''
        json_image=''
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
            if STR_NAME in json_user and json_user[STR_NAME]:
                json_username=json_user[STR_NAME]
        if STR_PICTURES in json_cloudcast and json_cloudcast[STR_PICTURES]:
            json_pictures=json_cloudcast[STR_PICTURES]
            if thumb_size in json_pictures and json_pictures[thumb_size]:
                json_image=json_pictures[thumb_size]
        infolabels = {STR_COUNT:index,STR_TRACKNUMBER:index,STR_TITLE:json_name,STR_ARTIST:json_username,STR_DURATION:json_length,STR_YEAR:json_year,STR_DATE:json_date,STR_THUMBNAIL:json_image}
        if not forinfo:
            add_audio_item(infolabels,
                           {STR_MODE:MODE_PLAY,STR_KEY:json_key},
                           infolabels[STR_THUMBNAIL],
                           total)

        return infolabels
    else:
        return {}



def get_stream_offliberty(cloudcast_key):
    ck=URL_MIXCLOUD[:-1]+cloudcast_key
    if debugenabled:
        print('MIXCLOUD '+'resolving cloudcast stream for '+ck)
    for retry in range(1, 10):
        try:
#        request = urllib2.Request('http://offliberty.com/off.php', 'track=%s&refext=' % ck)
#        request = urllib2.Request('http://offliberty.com/off54.php', 'track=%s&refext=' % ck)
#        request.add_header('Referer', 'http://offliberty.com/')
            values={
                    'track' : ck,
                    'refext' : ''
                   }
            headers={
                     'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.27 Safari/537.36',
                     'Referer' : 'http://offliberty.com/'
                    }
            postdata = urllib.urlencode(values)
            request = urllib2.Request('http://offliberty.com/off54.php', postdata, headers, 'http://offliberty.com/')
            response = urllib2.urlopen(request)
            data=response.read()
            match=re.search('HREF="(.*)" class="download"', data)
            if match:
                return match.group(1)
            elif debugenabled:
                print('wrong response try=%s code=%s len=%s, trying again...' % (retry, response.getcode(), len(data)))
        except:
            if debugenabled:
                print('unexpected error try=%s error=%s, trying again...' % (retry, sys.exc_info()[0]))



def get_stream_local(cloudcast_key):
    ck=URL_MIXCLOUD[:-1]+cloudcast_key
    if debugenabled:
        print('MIXCLOUD '+'locally resolving cloudcast stream for '+ck)
    headers={
             'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.27 Safari/537.36',
             'Referer' : URL_MIXCLOUD
            }
    request = urllib2.Request(ck, headers=headers, origin_req_host=URL_MIXCLOUD)
    response = urllib2.urlopen(request)
    data=response.read()
    match=re.search('m-p-ref="x_cloudcast_page" m-play-info="(.*)" m-preview', data)
    if match:
        playInfo=base64.b64decode(match.group(1))
        magicString=base64.b64decode('cGxlYXNlZG9udGRvd25sb2Fkb3VybXVzaWN0aGVhcnRpc3Rzd29udGdldHBhaWQ=')
        playInfoJSON=''.join(chr(ord(a) ^ ord(b)) for a,b in zip(playInfo,cycle(magicString)))
        json_content=json.loads(playInfoJSON)
        if STR_STREAMURL in json_content and json_content[STR_STREAMURL]:
            return json_content[STR_STREAMURL]
        elif debugenabled:
            print('unable to resolve')
    elif debugenabled:
        print('unable to resolve')



def get_stream(cloudcast_key):
    resolvers={Resolver.local : get_stream_local,
               Resolver.offliberty : get_stream_offliberty}
    return resolvers[resolver](cloudcast_key)



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



def get_query(query=''):
    keyboard=xbmc.Keyboard(query)
    keyboard.doModal()
    if keyboard.isConfirmed():
        query=keyboard.getText()
    else:
        query=''
    return query;
    


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



params=parameters_string_to_dict(urllib.unquote(sys.argv[2]))
mode=int(params.get(STR_MODE,"0"))
offset=int(params.get(STR_OFFSET,"0"))
key=params.get(STR_KEY,"")
query=params.get(STR_QUERY,"")

if debugenabled:
    print('MIXCLOUD '+"##########################################################")
    print('MIXCLOUD '+"Mode: %s" % mode)
    print('MIXCLOUD '+"Offset: %s" % offset)
    print('MIXCLOUD '+"Key: %s" % key)
    print('MIXCLOUD '+"Query: %s" % query)
    print('MIXCLOUD '+"##########################################################")

if not sys.argv[2] or mode==MODE_HOME:
    ok=show_home_menu()
elif mode==MODE_HOT:
    ok=show_hot_menu(offset)
elif mode==MODE_NEW:
    ok=show_new_menu(offset)
elif mode==MODE_POPULAR:
    ok=show_popular_menu(offset)
elif mode==MODE_CATEGORIES:
    ok=show_categories_menu(key,offset)
elif mode==MODE_USERS:
    ok=show_users_menu(key,offset)
elif mode==MODE_SEARCH:
    ok=show_search_menu(key,query,offset)
elif mode==MODE_HISTORY:
    ok=show_history_menu(offset)
elif mode==MODE_PLAY:
    ok=play_cloudcast(key)

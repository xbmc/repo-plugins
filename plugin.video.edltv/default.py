# -*- coding: utf-8 -*-
# Module: default
# Author: Kritsana Punyaporn
# Created on: 01.03.2017
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import json
import sys
import os
import socket
import filecmp
from urllib import urlencode
from urlparse import parse_qsl
import xbmcgui
import xbmcplugin
import xbmcvfs
import xbmcaddon

_url = sys.argv[0]
_handle = int(sys.argv[1])
cloud_path = ""
string = ""
word_list = []
study_time = []
addon         = xbmcaddon.Addon('plugin.video.edltv')
__language__  = addon.getLocalizedString

def check_internet_connected () :
    for timeout in [1,5,10,15]:
        try:
            xbmc.log("checking internet connection..")
            socket.setdefaulttimeout(timeout)
            host = socket.gethostbyname("www.google.com")
            s = socket.create_connection((host, 80), 2)
            s.close()
            return True
        except Exception,e:
            xbmc.log(str(e))
    return False

def set_period(code) :
    with open(database_path) as database:
        data = json.load(database)
        my_list = list(filter(lambda d: code.decode('utf8') == d['parent'], data['edltv']))
        for item in my_list :
            study_time.append(item['code'])
        if study_time :
            maxstudy_time = study_time[-1][8:9]
            if maxstudy_time == "0" :
                list_videos(study_time[-1][0:9])
            else :
                for i in range(1,int(maxstudy_time)+1) :
                    data = __language__(33040).encode('utf8') + str(i)
                    class_code = code + str(i)
                    list_item = xbmcgui.ListItem(label=data)
                    list_item.setInfo('videos', {'mediatype' : 'video'})
                    url = get_url(action='listing', category=class_code, hasfolder='no')
                    is_folder = True
                    xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
                xbmcplugin.endOfDirectory(_handle)
        else :
            dialog = xbmcgui.Dialog()
            ok = dialog.ok('eDLTV', __language__(33031).encode('utf8'))

def set_class(code=None):
    category = [__language__(33007).encode('utf8'), __language__(33008).encode('utf8'),
                __language__(33009).encode('utf8'), __language__(33010).encode('utf8'),
                __language__(33011).encode('utf8'), __language__(33012).encode('utf8')]
    if code == None:
        list_item = xbmcgui.ListItem(label=__language__(33000).encode('utf8'))
        list_item.setInfo('videos', {'mediatype' : 'video'})
        url = get_url(action='search', hasfolder='yes')
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

        for data in category :
            list_item = xbmcgui.ListItem(label=data)
            list_item.setInfo('videos', {'mediatype' : 'video'})
            url = get_url(action='listing', category=data, hasfolder='yes')
            is_folder = True
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def get_data(code,head=None):
    print "code data"
    print code
    with open(database_path) as database:
        data = json.load(database)
        if head != None:
            my_list = list(filter(lambda d: code.decode('utf8') in d['description'] and d['parent'] == 'NULL', data['edltv']))
            return my_list
        else:
            if len(code) == 9 :
                my_list = list(filter(lambda d: code.decode('utf8') in d['code'], data['edltv']))
                return my_list
            else :
                my_list = list(filter(lambda d: code.decode('utf8') == d['parent'], data['edltv']))
                return my_list

def list_categories(category):
    header = False
    item_code = 0
    for i in range(33001,33012) :
        if category == __language__(i).encode('utf8') :
            header = True
            break;

    if header :
        classes = get_data(category,0)
        for data in classes:
            list_item = xbmcgui.ListItem(label=data['name'])
            list_item.setInfo('videos', {'mediatype' : 'video'})
            url = get_url(action='listing', category=data['code'], hasfolder='yes')
            is_folder = True
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        xbmcplugin.endOfDirectory(_handle)
    else :    
        if len(category) == 8 :
            set_period(category)
        else :
            lessons = get_data(category,None)
            for data in lessons:
                list_item = xbmcgui.ListItem(label=data['name'])
                list_item.setInfo('videos', {'mediatype' : 'video'})
                url = get_url(action='listing', category=data['code'], hasfolder='yes')
                is_folder = True
                xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
            xbmcplugin.endOfDirectory(_handle)

def list_videos(category) :
    cloud_path = get_socket_data ()
    cloud_path = "smb://" + str(cloud_path) + "/Public/edltv/eDLTVA/htdocs/"
    lessons = get_data(category,None)
    print "test data"
    print lessons
    if xbmcvfs.exists(cloud_path) :
        for data in lessons :
            list_item = xbmcgui.ListItem(label=data['name'])
            list_item.setInfo('video', {'title': data['name'],'mediatype' : 'video'})
            list_item.setProperty('IsPlayable', 'true')
            url = get_url(action='play', video=cloud_path+data['location'].encode('utf8'))
            is_folder = False
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        xbmcplugin.endOfDirectory(_handle)
    elif check_internet_connected() :
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('eDLTV', __language__(33033).encode('utf8'))
        for data in lessons :
            list_item = xbmcgui.ListItem(label=data['name'])
            list_item.setInfo('video', {'title': data['name'],'mediatype' : 'video'})
            list_item.setProperty('IsPlayable', 'true')
            url = get_url(action='play', video=data['url'].encode('utf8'))
            is_folder = False
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        xbmcplugin.endOfDirectory(_handle)
    else :
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('eDLTV', __language__(33030).encode('utf8'))

def play_video(path):
    play_item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

def set_search_list (l) :
    cloud_path = get_socket_data ()
    cloud_path = "smb://" + str(cloud_path) + "/Public/edltv/eDLTVA/htdocs/"
    if xbmcvfs.exists(cloud_path) :
        for data in l :
            list_item = xbmcgui.ListItem(label=data['name'].encode('utf8'))
            list_item.setInfo('video', {'title': data['name'].encode('utf8'),'mediatype' : 'video'})
            list_item.setProperty('IsPlayable', 'true')
            url = get_url(action='play', video=cloud_path+data['location'].encode('utf8'))
            is_folder = False
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        xbmcplugin.endOfDirectory(_handle)
    elif check_internet_connected() :
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('eDLTV', __language__(33033).encode('utf8'))
        for data in l :

            list_item = xbmcgui.ListItem(label=data['name'].encode('utf8'))
            list_item.setInfo('video', {'title': data['name'].encode('utf8'),'mediatype' : 'video'})
            list_item.setProperty('IsPlayable', 'true')
            url = get_url(action='play', video=data['url'].encode('utf8'))
            is_folder = False
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        xbmcplugin.endOfDirectory(_handle)
    else :
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('eDLTV', __language__(33030).encode('utf8'))

def query_data (l) :
    my_list = []
    buffer_list = []
    remove_list = filter(lambda d: "-" in d[0], l)
    select_list = [x for x in l if '-' not in x[0]]
    with open(database_path) as database:
        data = json.load(database)
        for item in select_list :
            my_list = my_list + list(filter(lambda d: item.decode('utf-8').lower() in d["name"].lower() and d['filename'] != "NULL" and d not in my_list, data['edltv']))
        for item in remove_list :
            buffer_list = buffer_list + list(filter(lambda d: item[1:].decode('utf-8').lower() in d["name"].lower() and d['filename'] != "NULL" and d not in buffer_list, data['edltv']))
        for item in buffer_list :
            if item in my_list :
                my_list.remove(item)
    return my_list

def remove_minus (l) :
    sql = ''
    buffer_l = []
    buffer_l.extend(l)
    for i in l :
        if i == '-' :
            buffer_l.remove(i)
        else :
            buffer_l[buffer_l.index(i)] = i.rstrip('-')
    buffer_l = filter(None, buffer_l)
    
    return query_data (buffer_l)

def check_one_word (l) :
    with open(database_path) as database:
        data = json.load(database)
        if len(l[0]) > 1 :        
            if l[0][0] != '-' :
                data_list = filter(lambda d: l[0].decode('utf8').lower() in d["name"].lower() and d['filename'] != "NULL", data['edltv'])
        elif len(l[0]) == 1 :
            if l[0][0] == '-' or l[0][0] == '+' :
                data_list = filter(lambda d: l[0].decode('utf8').lower() in d["name"].lower() and d['filename'] != "NULL", data['edltv'])
    return data_list

def set_word_list (l) :
    globals()['word_list'] = l

def get_word_list () :
    return globals()['word_list']

def set_string (s) :
    globals()['string'] = s

def get_string () :
    return globals()['string']

def replace_and_split (string,symbol='+',to_symbol=' ') :
    buffer_word_list = []
    string = string.replace(symbol,to_symbol)
    buffer_word_list = string.split()
    set_word_list(buffer_word_list)
    buffer_word_list = []

def word_function (data) :
    r = []
    set_string(data)
    if len(get_string()) == 1 and get_string()[0] == '+' :
        replace_and_split (get_string(),' ')
    else :
        replace_and_split (get_string())
        
    if len(get_word_list()) == 1 :
        r = check_one_word(get_word_list())
    elif len(get_word_list()) > 1 :
        r = remove_minus(get_word_list())
    if r :
        set_search_list (r)
    else :
        return True
    return False

def search_function () :
    kb = xbmc.Keyboard(None,__language__(33000).encode('utf8'))
    kb.doModal()
    if (kb.isConfirmed()):
        error = word_function (kb.getText())
        if error :
            dialog = xbmcgui.Dialog()
            ok = dialog.ok('eDLTV', __language__(33032).encode('utf8'))

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'listing':
            if params['hasfolder'] == 'yes':
                list_categories(params['category'])
            else :
                list_videos(params['category'])
        elif params['action'] == 'search':
            search_function()
        elif params['action'] == 'play':
            play_video(params['video'])
        else:
           raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        set_class()

def get_socket_data () :
    msg = \
        'M-SEARCH * HTTP/1.1\r\n' \
        'HOST:239.255.255.250:1900\r\n' \
        'ST:upnp:rootdevice\r\n' \
        'MX:2\r\n' \
        'MAN:"ssdp:discover"\r\n'
    web_socket = ""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.settimeout(2)
    s.sendto(msg, ('239.255.255.250', 1900) )
    try:
        while True:
            data, addr = s.recvfrom(65507)
            return addr[0]
    except socket.timeout,e:
        xbmc.log(str(e))

if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    folder_path = addon.getAddonInfo('profile')
    database_path = xbmc.translatePath(os.path.join(folder_path,"database.json"))
    db_path = xbmc.translatePath(os.path.join(dir_path,"database.json"))
    if not xbmcvfs.exists(folder_path) :
        xbmcvfs.mkdir(folder_path)
    if not xbmcvfs.exists(database_path) :
        xbmcvfs.copy(db_path, database_path)
    elif not filecmp.cmp(db_path,database_path) :
        xbmcvfs.copy(db_path, database_path)
    router(sys.argv[2][1:])
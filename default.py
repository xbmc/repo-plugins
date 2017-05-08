# -*- coding: utf-8 -*-
# Module: default
# Author: Roman V. M.
# Created on: 28.11.2014
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import sqlite3
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

_url = sys.argv[0]
_handle = int(sys.argv[1])
string = ""
word_list = []

def check_internet_connected () :
    for timeout in [1,5,10,15]:
        try:
            print "checking internet connection.."
            socket.setdefaulttimeout(timeout)
            host = socket.gethostbyname("www.google.com")
            s = socket.create_connection((host, 80), 2)
            s.close()
            return True
        except Exception,e:
            print e
    return False

def set_period(code) :
    rows = c.execute('SELECT * FROM edltv WHERE parent LIKE ?',(code,))
    for row in rows :
        period.append(row[0])
    if period :
        maxperiod = str(max(period))[7:8]
        if maxperiod == "0":
            list_videos(str(max(period))[0:8])
        else :
            for i in range(1, int(maxperiod)+1) :
                data = 'คาบที่ '+str(i)
                period_code = code+str(i)
                list_item = xbmcgui.ListItem(label=data)
                url = get_url(action='listing', category=period_code, hasfolder='no')
                is_folder = True
                xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
            xbmcplugin.endOfDirectory(_handle)
    else :
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('eDLTV', 'ขออภัย หัวข้อนี้ไม่มีวิดีโอ')

def set_class(code=None):
    category = ['ค้นหา',
                'ชั้นมัธยมศึกษาปีที่ 1', 'ชั้นมัธยมศึกษาปีที่ 2',
                'ชั้นมัธยมศึกษาปีที่ 3', 'ชั้นมัธยมศึกษาปีที่ 4',
                'ชั้นมัธยมศึกษาปีที่ 5', 'ชั้นมัธยมศึกษาปีที่ 6']
    if code == None:
        for data in category :
            list_item = xbmcgui.ListItem(label=data)
            url = get_url(action='listing', category=data, hasfolder='yes')
            is_folder = True
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def get_data(code,head=None):
    if head != None:
        rows = c.execute('SELECT * FROM edltv WHERE LENGTH(code) <= 3 AND code LIKE ?',("%"+code,))
        rows = c.fetchall()
        return rows
    else:
        if len(code) == 8 :
            rows = c.execute('SELECT * FROM edltv WHERE code LIKE ?',(code+'%',))
            rows = c.fetchall()
            return rows
        else :
            rows = c.execute('SELECT * FROM edltv WHERE parent LIKE ?',(code,))
            rows = c.fetchall()
            return rows

def list_categories(category):
    if len(category) > 10 :
        classes = get_data(category[-1:],0)
        for data in classes:
            list_item = xbmcgui.ListItem(label=data[1])
            url = get_url(action='listing', category=data[0], hasfolder='yes')
            is_folder = True
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        xbmcplugin.endOfDirectory(_handle)
    elif len(category) == 7 :
        set_period(category)
    else :
        lessons = get_data(category,None)
        for data in lessons:
            list_item = xbmcgui.ListItem(label=data[1])
            url = get_url(action='listing', category=data[0], hasfolder='yes')
            is_folder = True
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        xbmcplugin.endOfDirectory(_handle)

def list_videos(category) :
    cloud_path = get_socket_data ()
    if cloud_path :
        cloud_path = cloud_path + '/Public/edltv/eDLTVA/htdocs/'
        host_path = "smb://"
    lessons = get_data(category,None)
    if cloud_path :
        for data in lessons :
            list_item = xbmcgui.ListItem(label=data[1])
            list_item.setInfo('video', {'title': data[1]})
            list_item.setProperty('IsPlayable', 'true')
            url = get_url(action='play', video=host_path+cloud_path+data[4])
            is_folder = False
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        xbmcplugin.endOfDirectory(_handle)
    elif check_internet_connected() :
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('eDLTV', 'ขั้นตอนนี้อาจมีค่าใช้บริการเมื่อต้องการเล่นวิดีโอ เนื่องจากมีการเชื่อมต่ออินเทอร์เน็ต')
        for data in lessons :
            list_item = xbmcgui.ListItem(label=data[1])
            list_item.setInfo('video', {'title': data[1]})
            list_item.setProperty('IsPlayable', 'true')
            url = get_url(action='play', video=data[7])
            is_folder = False
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        xbmcplugin.endOfDirectory(_handle)
    else :
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('eDLTV', 'ไม่สามารถติดต่อกับเซิฟเวอร์ได้เนื่องจากไม่ได้เชื่อมต่อเครือข่ายหรือไม่มีการเชื่อมต่ออินเทอร์เน็ต')

def play_video(path):
    play_item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

def set_search_list (l) :
    cloud_path = get_socket_data ()
    if cloud_path :
        cloud_path = cloud_path + '/Public/edltv/eDLTVA/htdocs/'
        host_path = "smb://"
    
    if cloud_path :
        for data in l :
            list_item = xbmcgui.ListItem(label=data[1])
            list_item.setInfo('video', {'title': data[1]})
            list_item.setProperty('IsPlayable', 'true')
            url = get_url(action='play', video=host_path+cloud_path+data[3])
            is_folder = False
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        xbmcplugin.endOfDirectory(_handle)
    elif check_internet_connected() :
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('eDLTV', 'ขั้นตอนนี้อาจมีค่าใช้บริการเมื่อต้องการเล่นวิดีโอ เนื่องจากมีการเชื่อมต่ออินเทอร์เน็ต')
        for data in l :
            list_item = xbmcgui.ListItem(label=data[1])
            list_item.setInfo('video', {'title': data[1]})
            list_item.setProperty('IsPlayable', 'true')
            url = get_url(action='play', video=data[4])
            is_folder = False
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        xbmcplugin.endOfDirectory(_handle)
    else :
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('eDLTV', 'ไม่สามารถติดต่อกับเซิฟเวอร์ได้เนื่องจากไม่ได้เชื่อมต่อเครือข่ายหรือไม่มีการเชื่อมต่ออินเทอร์เน็ต')

def query_data (l) :
    check_except = ''
    l.sort()
    l.reverse()
    sql = 'SELECT code, name, parent, location, url FROM edltv WHERE'
    for i in l :
        if i[0] != '-' :
            sql = sql + ' name like "%' + i + '%" OR'
        else :
            if not check_except :
                sql = sql.rstrip('OR')
                sql = sql + 'EXCEPT SELECT code, name, parent, location, url FROM edltv WHERE filename IS NULL'
                check_except = True
            sql = sql + ' OR name like "%' + i[1:] + '%"'
    sql = sql.rstrip(' OR')
    sql = sql + 'EXCEPT SELECT code, name, parent, location, url FROM edltv where length(code) < 10'
    rows = c.execute(sql)
    rows = c.fetchall()
    return rows

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
    sql = ''
    if len(l[0]) > 1 :        
        if l[0][0] != '-' :
            sql = 'SELECT code, name, parent, location, url FROM edltv WHERE name like "%'+l[0]+'%" AND filename IS NOT NULL'
    elif len(l[0]) == 1 :
        if l[0][0] == '-' or l[0][0] == '+' :
            sql = 'SELECT code, name, parent, location, url FROM edltv WHERE name like "%'+l[0]+'%" AND filename IS NOT NULL'
    sql = sql + ' EXCEPT SELECT code, name, parent, location, url FROM edltv where length(code) < 10 ORDER BY code'
    rows = c.execute(sql)
    rows = c.fetchall()
    return rows

def set_word_list (l) :
    global word_list
    word_list = l

def get_word_list () :
    global word_list
    return word_list

def set_string (s) :
    global string
    string = s

def get_string () :
    global string
    return string

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
    kb = xbmc.Keyboard(None,'Search')
    kb.doModal()
    if (kb.isConfirmed()):
        error = word_function (kb.getText())
        if error :
            ok = dialog.ok('eDLTV Error', 'ไม่พบข้อมูลที่ต้องการค้นหา')

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'listing':
            if params['category'] == 'ค้นหา':
                search_function()
            elif params['hasfolder'] == 'yes':
                list_categories(params['category'])
            else :
                list_videos(params['category'])
        elif params['action'] == 'play':
            play_video(params['video'])
        else:
           raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        get_socket_data()
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
        print e

if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    #database_path = dir_path[:dir_path.find("addons")] + "userdata/Database/edltv.db"
    folder_path = dir_path[:dir_path.find("addons")] + "userdata/addon_data/plugin.video.edltv/"
    database_path = folder_path + "edltv.db"
    db_path = dir_path+'/edltv.db'
    if not xbmcvfs.exists(folder_path) :
        xbmcvfs.mkdir(folder_path)
    if not xbmcvfs.exists(database_path) :
        xbmcvfs.copy(db_path, database_path)
    elif not filecmp.cmp(db_path,database_path) :
        xbmcvfs.copy(db_path, database_path)
    conn = sqlite3.connect(database_path)
    c = conn.cursor()
    period = []
    router(sys.argv[2][1:])
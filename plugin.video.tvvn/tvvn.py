# -*- coding: UTF-8 -*-
#---------------------------------------------------------------------
# File:    tvvn.py
# Version: 0.9.21
# By:      Binh Nguyen <b@zecoj.com>
#---------------------------------------------------------------------
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#---------------------------------------------------------------------

import os, re, sys, gzip, urllib, string, json, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
from io import BytesIO
from http.cookiejar import CookieJar

addon = xbmcaddon.Addon('plugin.video.tvvn')
mysettings = xbmcaddon.Addon(id='plugin.video.tvvn')
profile = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
home = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path'))
fanart = xbmcvfs.translatePath(os.path.join(home, 'fanart.jpg'))
datafile = xbmcvfs.translatePath(os.path.join(home, 'data.json'))

data = json.loads(open(datafile,"r",encoding="utf8").read())

mode=None

def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]

    return param

params=get_params()

try: chn=params["chn"]
except: pass
try: src=params["src"]
except: pass
try: mode=int(params["mode"])
except: pass

def construct_menu(namex):
    name = data['directories'][namex]['title']
    lmode = '2'
    iconimage = ''
    desc = data['directories'][namex]['desc']

    menu_items = data['directories'][namex]['content']
    for menu_item in menu_items:
        #type == channel
        if (menu_item['type'] == "chn"):
            add_chn_link (menu_item['id'])
        #type == directory
        if (menu_item['type'] == "dir"):
            add_dir_link (menu_item['id'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    return

def add_chn_link (namex):
    ok = True
    title = data['channels'][namex]['title']
    name = title
    iconimage = data['channels'][namex]['logo']
    desc = data['channels'][namex]['desc']
    ref = data['channels'][namex]['src']['referer']
    stream_name = data['channels'][namex]['src']['playpath']
    src = data['channels'][namex]['src']['id']

    if (iconimage == ''):
        iconimage = 'default.png'
    if (mysettings.getSetting('descriptions')=='true' and desc != ''):
        if mysettings.getSetting('descriptions_on_right') == 'false':
            name = desc+"    "+name
        else:
            name = name+"    "+desc

    give_url = sys.argv[0]+"?mode=1&chn="+namex+"&src="+src
    liz = xbmcgui.ListItem(name)
    liz.setInfo(type="video", infoLabels={"title": name, "mediatype": "video"})
    liz.setArt({
        "icon": xbmcvfs.translatePath(os.path.join(home, 'resources', 'logos', iconimage)),
        "thumb": xbmcvfs.translatePath(os.path.join(home, 'resources', 'logos', iconimage)),
        "fanart": fanart
    })
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=give_url,listitem=liz)

def add_dir_link (namex):
    name = '['+data['directories'][namex]['title']+']'
    desc = data['directories'][namex]['desc']
    iconimage = data['directories'][namex]['logo']
    if (iconimage == ''):
        iconimage = 'default.png'
    if (mysettings.getSetting('descriptions')=='true' and desc != ''):
        if mysettings.getSetting('descriptions_on_right') == 'false':
            name = desc+"    "+name
        else:
            name = name+"    "+desc
    li = xbmcgui.ListItem(name)
    li.setInfo(type="video", infoLabels={"title": name, "mediatype": "video"})
    li.setArt({
        "icon": xbmcvfs.translatePath(os.path.join(home, 'resources', 'logos', iconimage)),
        "thumb": xbmcvfs.translatePath(os.path.join(home, 'resources', 'logos', iconimage)),
        "fanart": fanart
    })
    give_url = sys.argv[0]+"?mode=2&chn="+namex
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=give_url, listitem=li, isFolder=True)

def update_chn_list():
    url = mysettings.getSetting('json_url')
    request = urllib.request.Request(url)
    request.add_header('Accept-encoding', 'gzip')
    url_error = "no"
    try:
        response = urllib.request.urlopen(request)
    except (urllib.error.URLError, e):
        url_error = "yes"

    if (url_error == "no"):
        buf = BytesIO(response.read())
        f = gzip.GzipFile(fileobj=buf)
        ff=f.read()
        r_data=json.loads(ff)
        if (data['timestamp'] < r_data['timestamp']):
            day_diff = str((int(r_data['timestamp']) - int(data['timestamp'])) /60/60/24)
            dialog = xbmcgui.Dialog()
            ack = dialog.yesno(addon.getLocalizedString(30005), addon.getLocalizedString(30006)+" "+day_diff+" day(s) old",addon.getLocalizedString(30007))
            if ack:
                d_progress = xbmcgui.DialogProgress()
                d_progress.create(addon.getLocalizedString(30008), addon.getLocalizedString(30009))
                d = open(datafile, 'w')
                d.seek(0)
                d.write(ff)
                d.close()
                construct_menu("root")
                d_progress.close()
                d_ok = xbmcgui.Dialog().ok(addon.getLocalizedString(30008),addon.getLocalizedString(30010))
 
def play_link(chn, src):
    item = xbmcgui.ListItem(chn)
    d_progress = xbmcgui.DialogProgress()
    d_progress.create("", addon.getLocalizedString(30009))

    cj = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    #login if required
    if src in data['sources'] and 'login' in data['sources'][src] and data['sources'][src]['login'] == "true":
        url = data['sources'][src]['url']
        values = data['sources'][src]['post']
        post_data = urllib.urlencode(values)
        response = opener.open(url, post_data)
        the_page = response.read()

    #m3u8 url from fpt
    if data['channels'][chn]['src']['playpath'] == "m3u8_fpt":
        url = 'http://fptplay.net/show/getlinklivetv'
        page_id = data['channels'][chn]['src']['page_id']
        page_q = data['channels'][chn]['src']['page_q']
        values={'id': page_id, 'type': 'newchannel', 'quality': page_q, 'mobile': 'web'}
        post_data = urllib.urlencode(values)
        header = {'Content-Type': 'application/x-www-form-urlencoded', 'Host':'fptplay.net','Origin':'http://fptplay.net','X-Requested-With':'XMLHttpRequest', 'Referer':'http://fptplay.net/livetv'}
        req = urllib.request.Request(url, post_data, header)
        response = urllib.request.urlopen(req)
        the_page = response.read()
        the_data = json.loads(the_page)
        full_url=the_data['stream']

    #m3u8 url from tvnet
    elif data['channels'][chn]['src']['playpath'] == "m3u8_tvnet":
        url = 'http://au.tvnet.gov.vn/kenh-truyen-hinh/'+data['channels'][chn]['src']['page_id']
        stringA = opener.open(url).read().decode('utf-8')
        stringB = 'data-file="'
        stringC = '"'
        url = re.search(stringB+"(.*?)"+re.escape(stringC),stringA).group(1)
        
        stringA = opener.open(url).read().decode('utf-8')
        stringB = '"url": "'
        stringC = '"'
        full_url_BC = re.search(stringB+"(.*?)"+re.escape(stringC),stringA).group(1)
        full_url = full_url_BC

    #m3u8 url from vtvgo
    elif data['channels'][chn]['src']['playpath'] == "m3u8_vtvgo":
        url = data['channels'][chn]['src']['page_url']
        stringA = opener.open(url).read().decode('utf-8')
        stringB = "var link = '"
        stringC = "'" 
        full_url = re.search(re.escape(stringB)+"(.*?)"+re.escape(stringC),stringA).group(1) + '|Referer=http%3A%2F%2Fvtvgo.vn%2F'

    #m3u8 url using before & after marker
    elif data['channels'][chn]['src']['playpath'] == "m3u8_bau":
        if data['channels'][chn]['src'].get('header'):
            header=(data['channels'][chn]['src']['header'])
        else:
            header=None
        if data['channels'][chn]['src'].get('post'):
            post=data['channels'][chn]['src']['post']
        else:
            post=None

        if header==None:
            req = urllib.request.Request(data['channels'][chn]['src']['page_url'], post)
        else:
            req = urllib.request.Request(data['channels'][chn]['src']['page_url'], post, header)

        response = urllib.request.urlopen(req)
        the_page = response.read()

        stringA=the_page
        stringB=(data['channels'][chn]['src']['url_before'])
        stringC=(data['channels'][chn]['src']['url_after'])
        full_url=re.search(re.escape(stringB)+"(.*?)"+re.escape(stringC),stringA).group(1)

    #traditional rtmp(e)
    else:
        videoUrl = data['sources'][src]['url']
        playpath = data['channels'][chn]['src']['playpath']
        if (playpath != ''):
            videoUrl = videoUrl+"/"+playpath

        url_protocol = videoUrl.split(':')[0]
        if (url_protocol == "http"):
            full_url = videoUrl
        elif (url_protocol in ["rtmp", "rtmpe"]):
            swfUrl = data['sources'][src]['swfurl']
            pageUrl = data['sources'][src]['pageurl']
            if (data['channels'][chn]['src']['referer'] != ''):
                    pageUrl = pageUrl+"/"+data['channels'][chn]['src']['referer']
            flashVer = 'LNX_11,2,202,233'
            token = data['sources'][src]['token']
            app = data['sources'][src]['app']

        full_url = videoUrl+' swfVfy=1 live=1 token='+token+' playpath='+playpath+' flashVer='+flashVer+' pageUrl='+pageUrl+' tcUrl='+videoUrl+' swfUrl='+swfUrl

    d_progress.close()
    xbmc.Player().play(full_url)
    return

def Init():
    construct_menu("root")
    if (mysettings.getSetting('json_url_auto_update')=='true' and mysettings.getSetting('json_url')!=''):
        update_chn_list()

if mode==None:
    Init()
elif mode==1:
    play_link(chn, src)
elif mode==2:
    construct_menu(chn)

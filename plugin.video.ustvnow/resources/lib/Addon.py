'''
    ustvnow XBMC Plugin
    Copyright (C) 2015 t0mm0, Lunatixz

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import urllib, pickle, cgi
import os, sys, re
import time, datetime, calendar
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs

from xml.dom import minidom
from xml.etree import ElementTree as ET
from datetime import date
from datetime import timedelta

addon = xbmcaddon.Addon(id='plugin.video.ustvnow')
plugin_path = addon.getAddonInfo('path')
ICON = os.path.join(plugin_path, 'icon.png')
FANART = os.path.join(plugin_path, 'fanart.jpg')

def log(msg, err=False):
    if err:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg.encode('utf-8'), 
                 xbmc.LOGERROR)    
    else:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg.encode('utf-8'), 
                    xbmc.LOGDEBUG)    
          
def ascii(string):
    if isinstance(string, basestring):
        if isinstance(string, unicode):
           string = string.encode('ascii', 'ignore')
    return string
    
def getProperty(str):
    return xbmcgui.Window(10000).getProperty(str)

def setProperty(str1, str2):
    xbmcgui.Window(10000).setProperty(str1, str2)

def clearProperty(str):
    xbmcgui.Window(10000).clearProperty(str)
    
def cleanChanName(string):
    string = string.strip()
    string = string.replace('WLYH','CW').replace('WHTM','ABC').replace('WPMT','FOX').replace('WPSU','PBS').replace('WHP','CBS').replace('WGAL','NBC').replace('WHVLLD','MY9').replace('AETV','AE')
    string = string.replace('APL','Animal Planet').replace('TOON','Cartoon Network').replace('DSC','Discovery').replace('Discovery ','Discovery').replace('BRAVO','Bravo').replace('SYFY','Syfy').replace('HISTORY','History').replace('NATIONAL GEOGRAPHIC','National Geographic')
    string = string.replace('COMEDY','Comedy Central').replace('FOOD','Food Network').replace('NIK','Nickelodeon').replace('LIFE','Lifetime').replace('SPIKETV','SPIKE TV').replace('FNC','Fox News').replace('NGC','National Geographic').replace('Channel','')
    return cleanChannel(string)
          
def cleanChannel(string):
    string = string.replace('WLYH','CW').replace('WHTM','ABC').replace('WPMT','FOX').replace('WPSU','PBS').replace('WHP','CBS').replace('WGAL','NBC').replace('My9','MY9').replace('AETV','AE').replace('USA','USA Network').replace('Channel','').replace('Network Network','Network')
    return string.strip()
      
def readXMLTV(filename, type='channels', name=''): 
    try:
        cached_readXMLTV = []
        channels = []
        now = datetime.datetime.now()
        f = open(filename, "r")
        context = ET.iterparse(f, events=("start", "end"))
        context = iter(context)
        event, root = context.next()
        for event, elem in context:
            if event == "end":
                if type == 'channels':
                    if elem.tag == "channel":
                        id = ascii(elem.get("id"))
                        for title in elem.findall('display-name'):
                            title = cleanChanName(title.text)
                            channels.append(ascii(title.replace('<display-name>','').replace('</display-name>','')))
                            break
                elif type == 'programs':
                    if elem.tag == "programme":
                        channel = elem.get("channel")
                        channel = channel.upper()
                        if name.lower() == channel.lower():
                            showtitle = elem.findtext('title')
                            description = elem.findtext("desc")
                            subtitle = elem.findtext("sub-title")
                            icon = None
                            iconElement = elem.find("icon")
                            if iconElement is not None:
                                icon = iconElement.get("src") 
                            genre = 'Unknown'
                            categories = ''
                            categoryList = elem.findall("category")
                            for cat in categoryList:
                                categories += ', ' + cat.text
                                if (cat.text).lower() == 'movie':
                                    movie = True
                                    genre = cat.text
                                elif (cat.text).lower() == 'tvshow':
                                    genre = cat.text
                                elif (cat.text).lower() == 'sports':
                                    genre = cat.text
                                elif (cat.text).lower() == 'children':
                                    genre = 'Kids'
                                elif (cat.text).lower() == 'kids':
                                    genre = cat.text
                                elif (cat.text).lower() == 'news':
                                    genre = cat.text
                                elif (cat.text).lower() == 'comedy':
                                    genre = cat.text
                                elif (cat.text).lower() == 'drama':
                                    genre = cat.text 
                            offset = ((time.timezone / 3600) - 5 ) * -1
                            stopDate = parseXMLTVDate(elem.get('stop'), 0)
                            startDate = parseXMLTVDate(elem.get('start'), 0)
                            if (((now > startDate and now <= stopDate) or (now < startDate))):
                                cached_readXMLTV.append([cleanChanName(channel), startDate, showtitle, description, subtitle, genre, icon])
        if type == 'channels':
            return channels
        elif type == 'programs':
            return cached_readXMLTV
        else:
            return []
    except Exception,e:
        return ['XMLTV ERROR']
            
def parseXMLTVDate(dateString, offset=0):
    if dateString is not None:
        if dateString.find(' ') != -1:
            # remove timezone information
            dateString = dateString[:dateString.find(' ')]
        t = time.strptime(dateString, '%Y%m%d%H%M%S')
        d = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
        d += datetime.timedelta(hours = offset)
        return d
    else:
        return None
        
def makeM3U(links):
    log('makeM3U')
    STRM_CACHE_LOC = xbmc.translatePath(get_setting('write_folder'))
    if not xbmcvfs.exists(STRM_CACHE_LOC):
        xbmcvfs.mkdir(STRM_CACHE_LOC)
        
    flepath = os.path.join(STRM_CACHE_LOC,'ustvnow.m3u')
    if xbmcvfs.exists(flepath):
        xbmcvfs.delete(flepath)
        
    playlist = open(flepath,'w')
    #Extended M3U format used here
    playlist.write('#EXTM3U'+'\n')
    if links:
        for l in links:
            #Add name based filename
            if int(get_setting('write_type')) == 3:
                playlist.write('#EXTINF:-1, tvg-id="'+l['name']+'" tvg-logo="'+l['name']+'" tvg-name="'+l['name']+'"  group-title="USTVnow",'+l['name']+'\n')
            else:
                playlist.write('#EXTINF:'+l['name']+'\n')
            #Write relative location of file
            playlist.write(l['url']+'\n')
    playlist.close()
                    
def makeSTRM(name, link):  
    log('makeSTRM')
    STRM_CACHE_LOC = xbmc.translatePath(get_setting('write_folder'))
    try:
        if not xbmcvfs.exists(STRM_CACHE_LOC):
            xbmcvfs.mkdir(STRM_CACHE_LOC)
            
        filepath = os.path.join(STRM_CACHE_LOC,name + '.strm')
        if xbmcvfs.exists(filepath):
            return True
        else:
            fle = open(filepath, "w")
            fle.write("%s" % link)
            fle.close()
            log('writing item: %s' % (filepath))
            return True
        return False
    except:
        return False

def makeXMLTV(data, filepath):
    log('makeXMLTV, filepath = ' + ascii(filepath))
    finished = False
    try:
        if not xbmcvfs.exists(os.path.dirname(filepath)):
            xbmcvfs.mkdir(os.path.dirname(filepath))
        if xbmcvfs.exists(filepath):
            xbmcvfs.delete(filepath)
        fle = open(filepath, "w")
        try:
            xml = data.toxml(encoding='utf-8');
        except Exception as e:
            xml  = '<?xml version="1.0" encoding="ISO-8859-1"?>'
            xml += '<error>' + str(e) + '</error>';
        xmllst = xml.replace('><','>\n<')
        xmllst = cleanChanName(xmllst)
        fle.write("%s" % xmllst) 
        fle.close()
        log('writing item: %s' % (filepath))
        if xbmcvfs.exists(filepath):
            finished = True
    except:
        pass
    return finished
       
def show_error(details):
    show_dialog(details, get_string(30000), True)

def show_dialog(details, title='USTVnow', is_error=False):
    error = ['', '', '']
    text = ''
    for k, v in enumerate(details):
        error[k] = v
        text += v + ' '
    log(text, is_error)
    dialog = xbmcgui.Dialog()
    ok = dialog.ok(title, error[0], error[1], error[2])
    
def get_setting(setting):
    return addon.getSetting(setting)
    
def set_setting(setting, string):
    return addon.setSetting(setting, string)
    
def get_string(string_id):
    return addon.getLocalizedString(string_id)   

def add_video_item(url, infolabels, img=ICON, fanart=FANART, total_items=0, 
                   cm=[], cm_replace=False, HD='Low', playable=True):
    infolabels = decode_dict(infolabels)
    if url.find('://') == -1:
        url = build_plugin_url({'play': url})
    listitem = xbmcgui.ListItem(infolabels['title'], iconImage=img, 
                                thumbnailImage=img)
    listitem.setInfo('video', infolabels)
    if playable:
        listitem.setProperty('IsPlayable', 'true')
        log('Item playable: %s' % (infolabels['title']))
    else:
        listitem.setProperty('IsPlayable', 'false')
        log('Item unplayable: %s' % (infolabels['title']))
    listitem.setArt({'fanart': fanart, 'icon': img})
    if HD == 'High':
        listitem.addStreamInfo('video', { 'width':1280 ,'height' : 720 })
    if HD == 'Medium':
        listitem.addStreamInfo('video', { 'width':640 ,'height' : 480 })
    else:
        listitem.addStreamInfo('video', { 'width':600 ,'height' : 320 })
    if cm:
        listitem.addContextMenuItems(cm, cm_replace)
    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem, 
                                isFolder=False, totalItems=total_items)

def add_directory(url_queries, title, img=ICON, fanart=FANART, total_items=0):
    url = build_plugin_url(url_queries)
    log('adding dir: %s' % (title))
    listitem = xbmcgui.ListItem(decode(title), iconImage=img, thumbnailImage=img)
    if not fanart:
        fanart = addon.getAddonInfo('path') + '/fanart.jpg'
    listitem.setProperty('fanart_image', fanart)
    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem, 
                                isFolder=True, totalItems=total_items)

def resolve_url(stream_url):
    xbmcplugin.setResolvedUrl(plugin_handle, True, 
                              xbmcgui.ListItem(path=stream_url))

def end_of_directory():
    xbmcplugin.endOfDirectory(plugin_handle)

def build_query(queries):
    return '&'.join([k+'='+urllib.quote(str(v)) for (k,v) in queries.items()])
                                
def build_plugin_url(queries):
    url = plugin_url + '?' + build_query(queries)
    return url

def parse_query(query, clean=True):
    queries = cgi.parse_qs(query)
    q = {}
    for key, value in queries.items():
        q[key] = value[0]
    if clean:
        q['mode'] = q.get('mode', 'main')
        q['play'] = q.get('play', '')
    return q

def show_settings():
    addon.openSettings()

def get_input(title='', default=''):
    kb = xbmc.Keyboard(default, title, False)
    kb.doModal()
    if (kb.isConfirmed()):
        return kb.getText()
    else:
        return False

#http://stackoverflow.com/questions/1208916/decoding-html-entities-with-python/1208931#1208931
def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id

def decode(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data).strip()

def decode_dict(data):
    for k, v in data.items():
        if type(v) is str or type(v) is unicode:
            data[k] = decode(v)
    return data
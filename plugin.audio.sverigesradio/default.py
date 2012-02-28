# coding: latin-1                                                                                                      
import urllib2

import xbmcgui
import xbmcplugin
import xbmcaddon

from xml.dom.minidom import parse, parseString

CHANNEL_URL = "http://api.sr.se/api/channels/channels.aspx"
PROGRAM_LIST_URL = "http://api.sr.se/api/program/programfeed.aspx"
PROGRAM_DETAIL_URL = "http://api.sr.se/api/program/broadcastfeed.aspx?unitid="
BASE_URL = "http://sr.se"

__settings__ = xbmcaddon.Addon(id='plugin.audio.sverigesradio')

def list_channels():
    doc, state = load_xml(CHANNEL_URL)
    if doc and not state:
        for channel in doc.getElementsByTagName("channel"):
            title = channel.getAttribute("name").encode('utf_8')
            originaltitle = title
            logo = get_node_value(channel, "logo")
            description = get_node_value(channel, "tagline")
            if description:
                description = description.encode('utf_8')
                title = title + " - " + description
            else:
                description = ''
            streamingurl = channel.getElementsByTagName("streamingurl")
            for url in streamingurl[0].getElementsByTagName("url"):
                type = url.getAttribute("type")
                protocol = url.getAttribute("protocol")
                quality = url.getAttribute("quality")
                playlist = url.getAttribute("playlist")
                stream = url.childNodes[0].data
                if type == "m4a" and quality == "high":
                    if logo:
                        add_posts(title, stream, description, logo, album = originaltitle, artist = 'Sveriges Radio')
                    else:
                        add_posts(title, stream, description, album = originaltitle, artist = 'Sveriges Radio')
    else:
        if state == "site":
            xbmc.executebuiltin('Notification("Sveriges Radio","Site down")')
        else:
            xbmc.executebuiltin('Notification("Sveriges Radio","Malformed result")')
    xbmcplugin.endOfDirectory(HANDLE)

def list_programs(url):
    doc, state = load_xml(PROGRAM_LIST_URL)
    if doc and not state:
        for program in doc.getElementsByTagName("item"):
            title = get_node_value(program, "title").encode('utf_8')
            description = get_node_value(program, "description")
            if description:
                description = description.encode('utf_8')
                title = title + " - " + description
            else:
                description = ''
            unitid = ""
            unitid = get_node_value(program, "unitid").encode('utf_8')
            add_posts(title, url + unitid + "/", isFolder=True)
    else:
        if state == "site":
            xbmc.executebuiltin('Notification("Sveriges Radio","Site down")')
        else:
            xbmc.executebuiltin('Notification("Sveriges Radio","Malformed result")')
    xbmcplugin.endOfDirectory(HANDLE)

def list_program(unitid):
    doc, state = load_xml(PROGRAM_DETAIL_URL+unitid)
    if doc and not state:
        urlset = doc.getElementsByTagName("urlset")[0]
        base = ""                                                                         
        for url in urlset.getElementsByTagName("url"):
            type = url.getAttribute("type")
            protocol = url.getAttribute("protocol")
            quality = url.getAttribute("quality")
            if type == "m4a" and protocol == "http" and quality == "high":
                base = url.childNodes[0].data
        if base == "":
            base = "http://sverigesradio.se/topsy/ljudfil/utan/statistik/[broadcastid].m4a"
            xbmc.log("Couldn't find url template, go with known (" + base + ")")
        for audio in doc.getElementsByTagName("item"):
            for ondemand in audio.getElementsByTagName("ondemand"):
                title = ondemand.getAttribute("mainbroadcasttitle").encode('utf_8')
                originaltitle = title
                description = ondemand.getAttribute("mainbroadcastdescription").encode('utf_8')
                if description:
                    title = description
                else:
                    description = ''
                date = ondemand.getAttribute("mainbroadcastdate").encode('utf_8')
                if date:
                    title = title + " - " + date
                else:
                    date = ''
                thumb = ondemand.getAttribute("image").encode('utf_8')
                if thumb:
                    thumb = BASE_URL + thumb
                else:
                    thumb = ''
                for broadcast in ondemand.getElementsByTagName("broadcastfilename"):
                    broadcastid = broadcast.getAttribute("broadcastid").encode('utf_8')                               
                    # broadcastname = broadcast.childNodes[0].data.encode('utf_8')
                    url = base.replace("[broadcastid]", broadcastid)
                    add_posts(title, url, description, thumb, artist='Sveriges Radio', album=originaltitle)
    else:
        if state == "site":
            xbmc.executebuiltin('Notification("Sveriges Radio","Site down")')
        else:
            xbmc.executebuiltin('Notification("Sveriges Radio","Malformed result")')
    xbmcplugin.endOfDirectory(HANDLE)


def add_posts(title, url, description='', thumb='', isPlayable='true', isLive='true', isFolder=False, artist='',\
              album=''):
    title = title.replace("\n", " ")
    listitem=xbmcgui.ListItem(title, iconImage=thumb)
    listitem.setInfo(type='music', infoLabels={'title': title, 'artist': artist, 'album': album})
    listitem.setProperty('IsPlayable', isPlayable)
    listitem.setProperty('IsLive', isLive)
    listitem.setPath(url)
    return xbmcplugin.addDirectoryItem(HANDLE, url=url, listitem=listitem, isFolder=isFolder)

def add_main_menu():
    listitem=xbmcgui.ListItem("Kanaler")
    listitem.setInfo(type='music', infoLabels={ 'Title': "Kanaler"})
    listitem.setPath('channels')
    u = sys.argv[0] + "channels/"
    xbmcplugin.addDirectoryItem(HANDLE, url=u, listitem=listitem, isFolder=True)
    listitem=xbmcgui.ListItem("Program A-Ö")
    listitem.setInfo(type='music', infoLabels={ 'Title': "Program A-Ö"})
    listitem.setPath('program')
    u = sys.argv[0] + "programs/"
    xbmcplugin.addDirectoryItem(HANDLE, url=u, listitem=listitem, isFolder=True)
    return xbmcplugin.endOfDirectory(HANDLE)


def get_node_value(parent, name, ns=""):
    if ns:
        if parent.getElementsByTagNameNS(ns, name) and \
                parent.getElementsByTagNameNS(ns, name)[0].childNodes:
            return parent.getElementsByTagNameNS(ns, name)[0].childNodes[0].data
    else:
        if parent.getElementsByTagName(name) and \
                parent.getElementsByTagName(name)[0].childNodes:
            return parent.getElementsByTagName(name)[0].childNodes[0].data
    return None

def load_xml(url):
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
    except:
        xbmc.log("plugin.audio.sverigesradio: unable to load url: " + url)
        return None, "site"
    xml = response.read()
    response.close()
    try:
        out = parseString(xml)
    except:
        xbmc.log("plugin.audio.sverigesradio: malformed xml from url: " + url)
        return None, "xml"
    return out, None


if (__name__ == "__main__" ):
    MODE=sys.argv[0]
    HANDLE=int(sys.argv[1])
    modes = MODE.split('/')
    activemode =  modes[len(modes) - 2]
    parentmode =  modes[len(modes) - 3]
    if activemode == "programs" :
        list_programs(MODE)
    elif activemode == "channels" :
        list_channels()
    elif parentmode == "programs" :
        list_program(activemode)
    else :
        add_main_menu()



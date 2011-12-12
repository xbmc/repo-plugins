import urllib2

import xbmcgui
import xbmcplugin

from xml.dom.minidom import parse, parseString

MAIN_URL = "http://api.sr.se/api/channels/channels.aspx"

def list_channels():
    doc, state = load_xml(MAIN_URL)
    if doc and not state:
        for channel in doc.getElementsByTagName("channel"):
            title = channel.getAttribute("name").encode('utf_8')
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
                        add_posts(title, stream, description, logo)
                    else:
                        add_posts(title, stream, description)
    else:
        if state == "site":
            xbmc.executebuiltin('Notification("Sveriges Radio","Site down")')
        else:
            xbmc.executebuiltin('Notification("Sveriges Radio","Malformed result")')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def add_posts(title, url, description='', thumb=''):
    listitem=xbmcgui.ListItem(title, iconImage=thumb)
    listitem.setInfo(type='music', infoLabels={ 'Title': title})
    listitem.setProperty('IsPlayable', 'true')
    listitem.setProperty('IsLive', 'true')
    listitem.setPath(url)
    return xbmcplugin.addDirectoryItem(HANDLE, url, listitem)


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
    HANDLE=int(sys.argv[1])
    list_channels()


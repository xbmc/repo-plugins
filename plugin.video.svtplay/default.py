# -*- coding: utf-8 -*-
import urllib2
import sys
import xbmc
import xbmcgui
import xbmcplugin
import os

from xml.dom.minidom import parseString, parse

if False:
    req = urllib2.Request("http://svtplay.se/mobil/deviceconfiguration.xml")
    res = urllib2.urlopen(req)
    dat = res.read();
    document = parseString(dat)
else:
    document = parse(open(os.getcwd() + "/deviceconfiguration.xml"))

url    = sys.argv[0].split("/")
target = "/".join(url[3:])

def HasElement(root, name):
    for child in root.childNodes:
        if child.nodeType == child.ELEMENT_NODE and child.nodeName == name:
            return True;
    return False;
    
def ProcessElement(root, name, func, path):
    for child in root.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            if child.nodeName == name:
                func(child, path)
    

def HandleOutline(outline, path):
    text = outline.getAttribute("text")
    type = outline.getAttribute("type")
    thum = outline.getAttributeNS("http://xml.svtplay.se/ns/playopml", "thumbnail")

    # Annoying site lists some menu's as rss's
    menu = HasElement(outline, "outline") and (type == "rss" or type == "menu")

    if path == target:
        # These are just pointless, so ignore them
        if path + text == U"Karusellen" \
        or path + text == U"Sök" \
        or path + text == U"Hjälpmeny":
            return

        if menu:
            listitem = xbmcgui.ListItem( label = text )
            listitem.setThumbnailImage( thum );            
            url = sys.argv[0] + text + "/"
            xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), url=url, listitem=listitem, isFolder=True ) 

        elif type == "rss":
            #print "RSS" + path + text
            listitem = xbmcgui.ListItem( label = text )
            listitem.setThumbnailImage( thum );
            url = outline.getAttribute("xmlUrl")
            if url.startswith("http://"):
                url = "rss://" + url[7:]
            xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), url=url, listitem=listitem, isFolder=True )    

    else:
        if menu and target.startswith(path + text + "/"):
            ProcessElement(outline, "outline", HandleOutline, path + text + "/")
        

def HandleBody(body, path):
    ProcessElement(body, "outline", HandleOutline, path)



ProcessElement(document.documentElement, "body", HandleBody, "")

xbmcplugin.endOfDirectory(int(sys.argv[1]))



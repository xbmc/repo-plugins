import sys
import os
import xbmc
import xbmcgui
import xbmcplugin

import time
import re
import urllib
import utils

BASE_CURRENT_SOURCE_PATH = os.path.join( xbmc.translatePath( "special://profile/" ), "addon_data", os.path.basename( os.getcwd() ), "shows.xml")
            
            
class Main:


    def __init__( self ):
        key = utils.Key( sys.argv[2] )
        self._load_shows(self.get_xml_source())
        
        
            
        if key.action == 'add':
            self._add_show(key.name, key.id, key.thumb)
        elif key.action == 'remove':
            self._remove_show(key.name, key.id)
        else:
            if (not self._get_shows()):
                xbmcplugin.endOfDirectory( handle=int(sys.argv[1]), succeeded=False , cacheToDisc=False)
    
    
    def _add_show(self, name, id, thumb):
        xbmc.log('Add %s to favorites' % name, xbmc.LOGNOTICE)
        xbmc.executebuiltin("Notification(Added to favorites,%s)" % name)
        showdata = {}
        showdata["name"]  = name
        showdata["thumb"] = thumb
        showdata["id"]    = id

        self.shows[name] = showdata
        self._save_shows()
            
             
    def _remove_show(self, showName, showId):
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno('Sletting...', 'Vil du fjerne "%s" fra favoritter?' % showName)
        if (ret):
            self.shows.pop(showName)
            self._save_shows()
            
            if len(self.shows) > 0:
                self._url = utils.Key.build_url('favorites')
            else:
                self._url = sys.argv[0]
            xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._url))
            
                
    def get_xml_source( self ):
        try:
            usock = open( BASE_CURRENT_SOURCE_PATH, "r" )
            # read source
            xmlSource = usock.read()
            # close socket
            usock.close()
            ok = True
        except:
            ok = False
        if ( ok ):
            # return the xml string without \n\r (newline)
            return xmlSource.replace("\n","").replace("\r","")
        else:
            return ""
            
    
    def _save_shows (self):
        # make settings directory if doesn't exists
        if (not os.path.isdir(os.path.dirname(BASE_CURRENT_SOURCE_PATH))):
            os.makedirs(os.path.dirname(BASE_CURRENT_SOURCE_PATH));
        
        if len(self.shows) <= 0:
            os.remove(BASE_CURRENT_SOURCE_PATH) 
            return
               
        usock = open( BASE_CURRENT_SOURCE_PATH, "w" )
        usock.write("<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>\n")
        usock.write("<shows>\n")
        for showIndex in self.shows:
            show = self.shows[showIndex]
            usock.write("\t<show>\n")
            usock.write("\t\t<name>"+show["name"]+"</name>\n")
            usock.write("\t\t<thumb>"+show["thumb"]+"</thumb>\n")
            usock.write("\t\t<id>"+str(show["id"])+"</id>\n")
            usock.write("\t</show>\n")            
        usock.write("</shows>")
        usock.close()
        
                           
    def _load_shows( self , xmlSource):
        shows = re.findall( "<show>(.*?)</show>", xmlSource )
        print "Show: found %d shows" % ( len(shows) )
        self.shows = {}
        for show in shows:
            name = re.findall( "<name>(.*?)</name>", show )
            thumb = re.findall( "<thumb>(.*?)</thumb>", show )
            id = re.findall( "<id>(.*?)</id>", show )

            if len(name) > 0 : name = name[0]
            else: name = "unknown"

            if len(thumb) > 0: thumb = thumb[0]
            else: thumb = ""
            
            if len(id) > 0: id = id[0]
            else: id = ""
            
            showdata = {}
            showdata["name"] = name
            showdata["thumb"] = thumb
            showdata["id"] = id

            self.shows[name] = showdata
    
    
    def _get_shows( self ):
        if (len(self.shows) > 0):
            for index in self.shows:
                show = self.shows[index]
                self._add_show_to_dir(show["name"], show['id'], show["thumb"], len(self.shows))
            xbmcplugin.endOfDirectory( handle=int(sys.argv[1]), succeeded=True, cacheToDisc=False )
            return True   
        else:
            return False

            
    def _add_show_to_dir(self, name, id, thumb, total) :
        commands = []
        #commands.append(('Gi nytt navn', "XBMC.RunPlugin(%s)" % (utils.Key.build_url('favorites', name=name, id=id, action='rename')) , ))
        commands.append(('Slett', "XBMC.RunPlugin(%s)" % (utils.Key.build_url('favorites', name=name, id=id, action='remove')) , ))
        folder = True
        icon   = "DefaultVideo.png"    
              
        if (thumb): thumbnail = thumb
        else: thumbnail = ''
            
        if (thumbnail):
            li = xbmcgui.ListItem( name, iconImage=icon, thumbnailImage=thumbnail)
        else:
            li = xbmcgui.ListItem( name, iconImage=icon )
            
        li.addContextMenuItems( commands, True )
        
        url = utils.Key.build_url('program', type='prosjekt', title=name, id=id, image=thumb)
        xbmcplugin.addDirectoryItem( handle=int(sys.argv[1]), url=url, listitem=li, isFolder=folder, totalItems=total)
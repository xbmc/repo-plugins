#!/usr/bin/python
# -*- coding: utf8 -*-

""" 
Copyright (C) 2012 Xycl

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import xbmc, xbmcgui
import common
from urllib2 import Request, urlopen
from urllib import urlencode
from os.path import join,isfile,basename
import os
from traceback import print_exc

LABEL_TEXT         = 100
BUTTON_CLOSE       = 101
BUTTON_ZOOM_IN     = 102
BUTTON_ZOOM_OUT    = 103
GOOGLE_MAP         = 200

CANCEL_DIALOG      = ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, )
ACTION_SELECT_ITEM = 7
ACTION_MOUSE_START = 100
ACTION_TAB         = 18
SELECT_ITEM = (ACTION_SELECT_ITEM, ACTION_MOUSE_START)
ACTION_DOWN = [4]
ACTION_UP = [3]

class GoogleMap( xbmcgui.WindowXMLDialog ):
    
    def __init__( self, xml, cwd, default):
        xbmcgui.WindowXMLDialog.__init__(self)


    def onInit( self ):  
        self.setup_all('')


    def onAction( self, action ):
        # Close
        if ( action.getId() in CANCEL_DIALOG or self.getFocusId() == BUTTON_CLOSE and action.getId() in SELECT_ITEM ):
            self.close()

        # Zoom in
        elif ( action.getId() in SELECT_ITEM and self.getFocusId() == BUTTON_ZOOM_IN or action in ACTION_UP):
            self.zoom('+')

        # Zoom out
        elif ( action.getId() in SELECT_ITEM and self.getFocusId() == BUTTON_ZOOM_OUT or action in ACTION_DOWN):
            self.zoom('-')


    def set_file(self, filename):
        self.filename = filename


    def set_place(self, place):
        self.place = place


    def set_datapath(self, datapath):
        self.datapath = datapath


    def set_pic(self, pic):
        pass
    
    
    def set_map(self, mapfile):
        self.getControl( GOOGLE_MAP ).setImage(mapfile)
    
    
    def setup_all( self, filtersettings = ""):
        self.getControl( LABEL_TEXT ).setLabel( common.getstring(30220) )
        
        self.getControl( BUTTON_CLOSE ).setLabel( common.getstring(30224) )
        self.getControl( BUTTON_ZOOM_IN ).setLabel( common.getstring(30225) )
        self.getControl( BUTTON_ZOOM_OUT ).setLabel(  common.getstring(30226) )  
        self.zoomlevel = 15
        self.zoom_max = 21
        self.zoom_min = 0
        self.load_map()


    def zoom(self,way,step=1):
        if way=="+":
            self.zoomlevel = self.zoomlevel + step
        elif way=="-":
            self.zoomlevel = self.zoomlevel - step
        else:
            self.zoomlevel = step
        if self.zoomlevel > self.zoom_max: self.zoomlevel = self.zoom_max
        elif self.zoomlevel < self.zoom_min: self.zoomlevel = self.zoom_min
        self.load_map()


    def load_map(self):
        #google geolocalisation
        static_url = "http://maps.google.com/maps/api/staticmap?"
        param_dic = {#location parameters (http://gmaps-samples.googlecode.com/svn/trunk/geocoder/singlegeocode.html)
                     "center":"",       #(required if markers not present)
                     "zoom":self.zoomlevel,         # 0 to 21+ (req if no markers
                     #map parameters
                     "size":"640x640",  #widthxheight (required)
                     "format":"jpg",    #"png8","png","png32","gif","jpg","jpg-baseline" (opt)
                     "maptype":"hybrid",      #"roadmap","satellite","hybrid","terrain" (opt)
                     "language":"",
                     #Feature Parameters:
                     "markers" :"color:red|label:P|%s",#(opt)
                                        #markers=color:red|label:P|lyon|12%20rue%20madiraa|marseille|Lille
                                        #&markers=color:blue|label:P|Australie
                     "path" : "",       #(opt)
                     "visible" : "",    #(opt)
                     #Reporting Parameters:
                     "sensor" : "false" #is there a gps on system ? (req)
                     }

        param_dic["markers"]=param_dic["markers"]%self.place

        request_headers = { 'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10' }
        request = Request(static_url+urlencode(param_dic), None, request_headers)
        try:
            urlfile = urlopen(request)
        except:
            dialog = xbmcgui.Dialog()
            dialog.ok('XBMC Network Error', 'Google maps is not reachable')
            self.close()
            return
            
        extension = urlfile.info().getheader("Content-Type","").split("/")[1]
        filesize = int(urlfile.info().getheader("Content-Length",""))

        mappath = xbmc.translatePath(self.datapath)
        mapfile = join(self.datapath,basename(self.filename).split(".")[0]+"_maps%s."%self.zoomlevel+extension)

        mapfile = xbmc.translatePath(mapfile)

        # test existence of path
        if not os.path.exists(mappath):
            os.makedirs(mappath)
        
        label = self.getControl( LABEL_TEXT )
        if not isfile(mapfile):
            #mapfile is not downloaded yet, download it now...
            try:
                #f=open(unicode(mapfile, 'utf-8'),"wb")
                f=open(common.smart_unicode(mapfile), "wb")
            except:
                try:
                    f=open(common.smart_utf8(mapfile), "wb")
                except:
                    print_exc()
                #print "GEO Exception: "+mapfile
            for i in range(1+(filesize/10)):
                f.write(urlfile.read(10))
                label.setLabel(common.getstring(30221)%(100*(float(i*10)/filesize)))#getting map... (%0.2f%%)
            urlfile.close()
            #pDialog.close()
            try:
                f.close()
            except:
                print_exc()
        self.set_pic(self.filename)
        self.set_map(mapfile)
        label.setLabel(common.getstring(30222)%int(100*(float(self.zoomlevel)/self.zoom_max)))#Zoom level %s

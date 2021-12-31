#   Copyright (C) 2021 Evinr
#
#
# This file is part of NASA APOD ScreenSaver.
#
# NASA APOD ScreenSaver is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NASA APOD ScreenSaver is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NASA APOD ScreenSaver.  If not, see <http://www.gnu.org/licenses/>.

import json, os, random, datetime, requests, itertools, re, random, time
from datetime import datetime
from datetime import timedelta

from kodi_six      import xbmc, xbmcaddon, xbmcplugin, xbmcgui


# Plugin Info
ADDON_ID       = 'screensaver.nasa.apod'
REAL_SETTINGS  = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME     = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC   = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH     = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION  = REAL_SETTINGS.getAddonInfo('version')
ICON           = REAL_SETTINGS.getAddonInfo('icon')
FANART         = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE       = REAL_SETTINGS.getLocalizedString
KODI_MONITOR   = xbmc.Monitor()

# Global Info
# TODO: Update base mapping
BASE_URL       = 'https://apod.nasa.gov'
NEXT_JSON      = '/apod/%s.html'
# REAL_SETTINGS.getSetting("Last") seems to be stuck on the default error image (yellowstone)
BASE_API       = NEXT_JSON%('astropix')#(REAL_SETTINGS.getSetting("Last") or NEXT_JSON%('astropix'))
# TODO: get the settings working for these values
TIMER          = 120#int(REAL_SETTINGS.getSetting("RotateTime"))
# TODO: Determine what these id's relate to
IMG_CONTROLS   = [30000,30100]
# TODO: Determine what this is
CYC_CONTROL    = itertools.cycle(IMG_CONTROLS).__next__ #py3
# user agent needs to get updated regularly to align with 
# https://techblog.willshouse.com/2012/01/03/most-common-user-agents/
HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'}


class GUI(xbmcgui.WindowXMLDialog):
    def __init__( self, *args, **kwargs ):
        self.isExiting = False
        # used to call the HTML site that will be parsed
        self.baseAPI   = BASE_API
        # Get the first image or like the last set images HTML
        self.results = ''
        # stores the parsed JPG from HTML                    
        self.prefetchedImagePath = '~/.kodi/addons/screensaver.nasa.apod/resources/images/fanart.jpg'
        
        
    def log(self, msg, level=xbmc.LOGDEBUG):
        xbmc.log('%s-%s-%s'%(ADDON_ID,ADDON_VERSION,msg),level)
            
            
    def notificationDialog(self, message, header=ADDON_NAME, sound=False, time=4000, icon=ICON):
        try: xbmcgui.Dialog().notification(header, message, icon, time, sound=False)
        except Exception as e:
            self.log(f"notificationDialog Failed! {e}", xbmc.LOGERROR)
            xbmc.executebuiltin("Notification(%s, %s, %d, %s)" % (header, message, time, icon))
        return True
         
         
    def onInit(self):
        # TODO: determine what other animations can be done and why these work, but not the timer
        self.winid = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId())
        self.winid.setProperty('earth_animation', 'okay' if REAL_SETTINGS.getSetting("Animate") == 'true' else 'nope')
        self.winid.setProperty('earth_time'     , 'okay' if REAL_SETTINGS.getSetting("Time") == 'true' else 'nope')
        self.winid.setProperty('earth_overlay'  , 'okay' if REAL_SETTINGS.getSetting("Overlay") == 'true' else 'nope')
        self.startRotation()


    def openURL(self, url):
        try:
            self.results = requests.get(url, headers=HEADERS)
        except Exception as e:
            self.log(f"openURL Failed: {e}", xbmc.LOGERROR)
            self.results = False
        
        
    def findNextRandomImage(self):
        try: 
            #grab from the random URL
            then = datetime(1995, 5, 20)        # Date of first stable APODs # TODO: make this a dynamic setting
            now  = datetime.now()                         # Now
            duration = now - then                         # For build-in functions
            duration_in_s = duration.total_seconds()      # Total number of seconds between
            random_offset_from_apod_creation = datetime.fromtimestamp(random.randrange(int(duration_in_s)))
            random_apod = now - random_offset_from_apod_creation
            nextImage = "ap" + datetime.fromtimestamp(random_apod.total_seconds()).strftime("%y%m%d")
            return nextImage   
        except Exception as e:
            self.log(f"findNextImage threw an exception: {e}", xbmc.LOGERROR)
            # TODO: hardcode the default image
            return 'ap210817'
            
            
    def parseJPG(self, response):
        if response:
            try:
                match = re.findall(r"image/.*?\"", response.text) 
                if match:
                    self.prefetchedImagePath = str("/" + match[0][:-1])
                else:
                    self.log(f"parseJPG could not find a JPG in HTML response. Returning from static list.", xbmc.LOGDEBUG)
                    # if no match is found then return static images
                    self.prefetchedImagePath = random.choice(['/image/2012/Neyerm63_l2.jpg', '/image/2012/EagleNebula_Paladini_2854.jpg', '/image/2107/Walk_Milkyway.jpg', '/image/2108/Luna-Tycho-Clavius-high.jpg', '/image/2108/m74_APOD.jpg', '/image/2107/sh2_101_04.jpg'])
            except Exception as e:
                self.log(f"parseJPG Failed: {e}", xbmc.LOGERROR)
                # the parseJPG visial failure is the one that looks like yellowstone
                self.prefetchedImagePath = '/image/1912/NGC6744_FinalLiuYuhang.jpg'
        else: 
            # When the response failed setting it to the forest
            # TODO: Either a subset of images for this condition or a function that has a large enough variety to not notice
            self.prefetchedImagePath = '/image/2107/ForestWindow_Godward_2236.jpg'
    
    
    def parseLabels(self,response):
         self.log(f"parseLabels: {self.prefetchedImagePath}", xbmc.LOGDEBUG)
         #  TODO: Parse the lable/title/contents
         
         
    def setImage(self, id):
        try:            
            # Sets the actual image 
            self.getControl(id).setImage('%s%s'%(BASE_URL,self.prefetchedImagePath))
            # Sets the labels 
            # self.getControl(id+1).setLabel(('%s, %s'%(results.get('region',' '),results.get('country',''))).strip(' ,'))
            # Sets up the path for the next image
            nextAPOD = self.findNextRandomImage()
            # Create new string for URL path for next lookup
            baseAPI = NEXT_JSON%(nextAPOD)
            # get the JPG from HTML                    
            self.parseJPG(self.results)
            # get the HTML for the next image
            self.openURL('%s%s'%(BASE_URL,baseAPI))
            
        except Exception as e:
            self.log("setImage Failed: " + str(e), xbmc.LOGERROR)
            # TODO: hardcode the default image rather than it being scrapped on failure
            baseAPI = NEXT_JSON%('ap210817')
        # set the global path to the next images URL
        self.baseAPI = baseAPI
    
          
    def startRotation(self):
        # these ID relate to the screen/viewport that is being 
        self.currentID = IMG_CONTROLS[0]
        self.nextID    = IMG_CONTROLS[1]
        
        # Get the first image or like the last set images HTML
        self.openURL('%s%s'%(BASE_URL,self.baseAPI))
        # wait for response from initialization request to come back
        # time.sleep(15) # Cannot do sleep as the script will get killed after 5 seconds
        self.log(f"results from openURL: {self.results}", xbmc.LOGDEBUG)
        # Parse the JPG from the HTML
        self.parseJPG(self.results)
        
        # screensaver is running loop
        while not KODI_MONITOR.abortRequested():
            # self.log("settings RotateTime: " + REAL_SETTINGS.getSetting("RotateTime"), xbmc.LOGDEBUG)
            
            # set the image once we are in the loop
            self.log(f"prefetchedImagePath: {self.prefetchedImagePath}", xbmc.LOGDEBUG)
            self.setImage(self.nextID)
            # allow for the image to load
                        
            #TODO: trigger the image to be downloaded before being made visible to reduce black screen flashing for large images 
            # handles the swapping out of images cleanly
            self.getControl(self.nextID).setVisible(True)
            self.getControl(self.currentID).setVisible(False)
            self.nextID    = self.currentID 
            self.currentID = CYC_CONTROL()
            
            # stops the screensaver or triggers the next image due to timer
            # TODO: Fix the TIMER value to pickup from the settings. 0 in the settings and not defaulting to a value in the list.
            if KODI_MONITOR.waitForAbort(TIMER) == True or self.isExiting == True: break
            
        # # sets the last image as the cached result to pick up where we left off
        REAL_SETTINGS.setSetting("Last",self.baseAPI)

                     
    def onAction(self, action):
        # called when exiting due to interaction
        self.log("exiting", xbmc.LOGDEBUG)
        self.isExiting = True
        self.close()
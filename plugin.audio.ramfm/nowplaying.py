
import xbmcgui
import utils
import xbmc

from threading import Timer 

import ramfm
import random

import os
import sys

path = utils.getAddonPath()
sys.path.insert(0, os.path.join(path, 'lib'))

import LastFM


ACTION_PARENT_DIR    = 9
ACTION_PREVIOUS_MENU = 10
ACTION_BACK          = 92

CR  = '[CR]'

URL = 'http://ramfm.org/ram.pls'

#http://wiki.xbmc.org/?title=XBMC_Skinning_Manual

class NowPlaying(xbmcgui.WindowXMLDialog):
    def __new__(cls):
        return super(NowPlaying, cls).__new__(cls, 'main.xml', utils.getAddonPath())


    def __init__(self): 
        self.init       = False
        self.RAMFMLOGO  = 5001
        self.STRAPLINE  = 5002
        self.NP_IMAGE   = 5003
        self.NP_TEXT    = 5004
        self.NP_FORMAT  = 5005
        self.NP_ARTIST  = 5006
        self.NP_TRACK   = 5007
        self.NP_YEAR    = 5008
        self.NP_LAST    = 5009
        self.NP_REQUEST = 5010
        self.NP_ROTATE  = 5011
        self.BIO        = 5020
        super(NowPlaying, self).__init__()


    def onInit(self):
        if self.init:
            return

        self.playStream()
        self.images       = None
        self.refreshImage = 0
        self.index        = 0
        self.init         = True
        self.artist       = ''
        self.timer        = Timer(0, self.onTimer)
        self.timer.start()


    def run(self):
        self.doModal()

              
    def OnClose(self):
        try:
            self.timer.cancel()
            del self.timer
        except Exception, e:
            utils.log(e)

        #self.stopStream()        
        self.close()


    #def onFocus(self, controlId):
    #    pass


    def onAction(self, action):
        actionID = action.getId()
        buttonID = action.getButtonCode()

        if actionID in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, ACTION_BACK]:
            self.OnClose()
            
                                 
    def onClick(self, controlId):
        pass



    def IsPlayingRAM(self):
        if not xbmc.Player().isPlayingAudio():
            return False

        pl         = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        label      = pl[0].getLabel().upper()
        return label == 'RAM FM EIGHTIES HIT RADIO'


    def playStream(self):
        if self.IsPlayingRAM():
            return

        pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        pl.clear()    
        pl.add(URL)
        xbmc.Player().play(pl)


    def stopStream(self):
        xbmc.Player().stop()


    def getArtist(self):
        artist = ''
        try:
            artist = xbmc.Player().getMusicInfoTag().getArtist()
        except:
            xbmc.sleep(1000)
            try:
                artist = xbmc.Player().getMusicInfoTag().getArtist()
            except:
                pass

        try:
            if len(artist) < 1:
                artist = xbmc.Player().getMusicInfoTag().getTitle().split(' - ')[0]
        except:
            pass

        return artist


    def onTimer(self):
        if not self.IsPlayingRAM():
            self.OnClose()
            return

        self.timer = Timer(1, self.onTimer)
        self.timer.start()

        artist = self.getArtist()
        if self.artist != artist:
            self.Refresh(artist)

        if not self.images:
            return

        self.refreshImage += 1
        if self.refreshImage < 5:
            return

        self.refreshImage = 0

        self.index  += 1
        if self.index < 0:
            return

        if self.index == len(self.images):
            self.index = 0

        self.setControlImage(self.NP_IMAGE, self.images[self.index])


    def updateStrapline(self, text):
        self.setControlText(self.STRAPLINE, text)


    def updateRamFMLogo(self, logo):
        self.setControlImage(self.RAMFMLOGO, logo)


    def updateNowPlaying(self, np):
        if self.images and len(self.images) > 0:
            self.setControlImage(self.NP_IMAGE,   self.images[0])
        self.setControlImage(self.NP_FORMAT,  np['format'])
        self.setControlText( self.NP_ARTIST,  np['artist'])
        self.setControlText( self.NP_TRACK,   np['track'])
        self.setControlText( self.NP_YEAR,    np['year'])
        self.setControlText( self.NP_REQUEST, np['request'])
        self.setControlText( self.NP_ROTATE,  np['rotation'])

        lastPlay = np['last'].split(' ')
        hour     = int(lastPlay[3].split(':')[0])
        ampm     = 'AM' if hour < 12 else 'PM'
        lastPlay = lastPlay[0] + CR + lastPlay[1] + ' ' + lastPlay[2] + CR + ampm + ' ' + lastPlay[3]
        self.setControlText(self.NP_LAST, lastPlay)

        if np['mode'] == 'NowPlaying':
            self.setControlText(self.NP_TEXT, utils.getString(30011))
        else:
            self.setControlText(self.NP_TEXT, utils.getString(30012))


    def updateBiography(self, bio):
        text = ''

        for item in bio:
            text += item
            text += CR
            text += CR

        self.setControlText(self.BIO, text)
        

    def setControlText(self, id, text):
        control = self.getControl(id)
        if not control:
            return

        try:
            control.setText(text)
            return
        except:
            pass

        try:
            control.setLabel(text)
            return
        except:
            pass


    def setControlImage(self, id, image):
        if image == None:
            return

        control = self.getControl(id)
        if not control:
            return

        if 'http' in image:
            image = image.replace(' ', '%20')

        try:    control.setImage(image)
        except: pass  


    def ValidImage(self, image):
        if not image :
            return False

        if image == '':
            return False

        if image == 'http://ramfm.org/artistpic/na.gif':
            return False

        return True


    def Refresh(self, artist):
        try:
            self.artist = artist

            html      = ramfm.GetHTML(artist=artist)
            strapline = ramfm.GetStrapline(html)
            logo      = ramfm.GetMainLogo(html)
            np        = ramfm.GetNowPlaying(html)

            search = ''
            bio    = ''
            try:
                #bio    = ramfm.GetBiography('http://www.last.fm/music/Shalamar/+wiki')
                bio    = ramfm.GetBiography(np['wiki'])            
                search = np['wiki'].split('/')[4]
            except:
                pass

            self.images       = LastFM.GetImages(search)
            self.index        = 0
            self.refreshImage = 0

            random.shuffle(self.images)

            if len(self.images) == 0 or self.ValidImage(np['image']):
                self.images.insert(0, np['image'])

            self.updateRamFMLogo(logo)
            self.updateStrapline(strapline)
            self.updateNowPlaying(np)
            self.updateBiography(bio)        
        except Exception, e:
            print "Error in NowPlaying.Refresh " + str(e)
            self.images = None
            self.artist = 'ERROR'
            raise
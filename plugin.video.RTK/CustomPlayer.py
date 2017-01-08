# -*- coding: utf-8 -*-
import xbmc


class MyXBMCPlayer(xbmc.Player):
    def __init__( self, *args, **kwargs ):
        self.is_active = True
        self.urlplayed = False
        self.pdialogue=None
        print "#XBMCPlayer#"
    
    #def play(self, url, listitem):
    #   print 'Now im playing... %s' % url
    #    self.is_active = False
    #    self.urlplayed = False
    #    xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(url, listitem)

	#def setdialogue( self, pdialogue ):
	#	self.pdialogue=pdialogue
		
    def onPlayBackStarted( self ):
        print "#Playback Started#"
        try:
            print "#Im playing :: " 
        except:
            print "#I failed get what Im playing#"
        if (self.pdialogue):
            self.pdialogue.close()
        self.urlplayed = True
            
    def onPlayBackEnded( self ):
        print "#Playback Ended#"
        self.is_active = False
        
    def onPlayBackStopped( self ):
        print "## Playback Stopped ##"
        self.is_active = False


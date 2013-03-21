# from frost

# Modules general
import os

# Modules XBMC
import xbmc
import xbmcgui
from traceback import print_exc
import common

# constants
ADDON_NAME = common.getaddon_name()
ADDON_DIR  = common.getaddon_path()


class Viewer:
    # constants
    WINDOW = 10147
    CONTROL_LABEL = 1
    CONTROL_TEXTBOX = 5

    def __init__( self, *args, **kwargs ):
        # activate the text viewer window
        xbmc.executebuiltin( "ActivateWindow(%d)" % ( self.WINDOW, ) )
        # get window
        self.window = xbmcgui.Window( self.WINDOW )
        # give window time to initialize
        xbmc.sleep( 100 )
        
        if "text" in kwargs:
            self.text = kwargs["text"]
        else:
            self.text = ""
            
        if "header" in kwargs:
            self.header = kwargs["header"]
        else:
            self.header = "Readme"           

        # set controls
        self.setControls()

    def setControls( self ):
        #get header, text
        heading, text = self.getText()
        # set heading
        self.window.getControl( self.CONTROL_LABEL ).setLabel( "%s - %s" % ( heading, ADDON_NAME, ) )
        # set text
        self.window.getControl( self.CONTROL_TEXTBOX ).setText( text )

    def getText( self ):
        try:
            if self.text == "":
                txt = open( os.path.join( ADDON_DIR, "Readme.txt" ) ).read()
            else:
                txt = self.text

            return self.header, txt
        except:
            print_exc()
        return "", ""


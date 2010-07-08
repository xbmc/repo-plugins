""" helper functions """
try:
    import xbmc
    import xbmcgui
    import xbmcaddon
    DEBUG = False
except:
    DEBUG = True

import os
import sys

if ( not DEBUG ):
    # get the addon info method from Addons class
    Addon = xbmcaddon.Addon( id=os.path.basename( os.getcwd() ) )

    def LOG( text, level=xbmc.LOGNOTICE, heading=False ):
        # log a heading
        if ( heading ):
            xbmc.log( "-" * 70, level )
        # log message
        xbmc.log( text, level )
        # log a footer
        if ( heading ):
            xbmc.log( "-" * 70, level )

    def check_compatible():
        # check compatible
        try:
            # get xbmc revision
            xbmc_rev = int( xbmc.getInfoLabel( "System.BuildVersion" ).split( " r" )[ -1 ][ : 5 ] )
            # compatible?
            ok = 2 #xbmc_rev >= Addon.getAddonInfo( "XBMC_MinRevision" )
        except:
            # error, so unknown, allow to run
            xbmc_rev = 0
            ok = 2
        # spam scripts statistics to log
        LOG( "=" * 80, xbmc.LOGNOTICE )
        LOG( "[ADD-ON] - %s initialized!" % ( Addon.getAddonInfo( "Name" ), ), xbmc.LOGNOTICE )
        LOG( "           Id: %s - Type: %s - Version: %s" % ( Addon.getAddonInfo( "Id" ), Addon.getAddonInfo( "Type" ), Addon.getAddonInfo( "Version" ).replace( "$", "" ).replace( "Revision", "" ).strip() ), xbmc.LOGNOTICE )
        LOG( "=" * 80, xbmc.LOGNOTICE )
        #return result
        return ok

    def get_keyboard( default="", heading="", hidden=False ):
        """ shows a keyboard and returns a value """
        # show keyboard for input
        keyboard = xbmc.Keyboard( default, heading, hidden )
        keyboard.doModal()
        # return user input unless canceled
        if ( keyboard.isConfirmed() ):
            return keyboard.getText()
        # user canceled, return None
        return None

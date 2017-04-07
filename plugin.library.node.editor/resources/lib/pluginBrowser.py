# coding=utf-8
import sys
import xbmc, xbmcaddon, xbmcgui
import json

ADDON        = xbmcaddon.Addon()
ADDONID      = ADDON.getAddonInfo('id').decode( 'utf-8' )
LANGUAGE     = ADDON.getLocalizedString
ADDONNAME    = ADDON.getAddonInfo('name').decode("utf-8")
ltype        = sys.modules[ '__main__' ].ltype

def log(txt):
    if isinstance (txt,str):
        txt = txt.decode('utf-8')
    message = u'%s: %s' % (ADDONID, txt)
    xbmc.log(msg=message.encode('utf-8'), level=xbmc.LOGDEBUG)

def getPluginPath( location = None ):
    listings = []
    listingsLabels = []

    if location is not None:
        # If location given, add 'create' item
        listings.append( "::CREATE::" )
        listingsLabels.append( LANGUAGE( 30411 ) )
    else:
        # If no location, build default
        if location is None:
            if ltype.startswith( "video" ):
                location = "addons://sources/video"
            else:
                location = "addons://sources/audio"

    # Show a waiting dialog, then get the listings for the directory
    dialog = xbmcgui.DialogProgress()
    dialog.create( ADDONNAME, LANGUAGE( 30410 ) )
    
    json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Files.GetDirectory", "params": { "properties": ["title", "file", "thumbnail", "episode", "showtitle", "season", "album", "artist", "imdbnumber", "firstaired", "mpaa", "trailer", "studio", "art"], "directory": "' + location + '", "media": "files" } }')
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    json_response = json.loads(json_query)
        
    # Add all directories returned by the json query
    if json_response.has_key('result') and json_response['result'].has_key('files') and json_response['result']['files']:
        json_result = json_response['result']['files']
        
        for item in json_result:
            if item[ "file" ].startswith( "plugin://" ):
                listings.append( item[ "file" ] )
                listingsLabels.append( "%s >" %( item[ "label" ] ) )
        
    # Close progress dialog
    dialog.close()

    selectedItem = xbmcgui.Dialog().select( LANGUAGE( 30309 ), listingsLabels )

    if selectedItem == -1:
        # User cancelled
        return None
    
    selectedAction = listings[ selectedItem ]
    if selectedAction == "::CREATE::":
        return location
    else:
        # User has chosen a sub-level to display, add details and re-call this function
        return getPluginPath( selectedAction )

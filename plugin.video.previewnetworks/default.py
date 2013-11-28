"""
    Plugin for streaming Preview network
"""

# main imports
import sys
import os
import xbmc
import urllib
import urllib2
import re
import xbmcplugin
import xbmcgui
import cgi
import socket
import xbmcaddon

# plugin constants
__plugin__ = "plugin.video.previewnetworks"
__author__ = "nmazz64"
__url__ = "http://code.google.com/p/previewnetworks-xbmc-plugin"
__svn_url__ = "http://previewnetworks-xbmc-plugin.googlecode.com/svn/trunk/plugin.video.previewnetworks/"
__useragent__ = "QuickTime/7.6.5 (qtver=7.6.5;os=Windows NT 5.1Service Pack 3)"
__version__ = "2.3.4"
__svn_revision__ = "$Revision: 0$"
__XBMC_Revision__ = "31633"
__Channel_ID__ = "391100379-1"

url_source=None

def check_compatible():
    try:
        # get xbmc revision
        xbmc_rev = int( xbmc.getInfoLabel( "System.BuildVersion" ).split( " r" )[ -1 ] )
        # compatible?
        ok = xbmc_rev >= int( __XBMC_Revision__ )
    except:
        # error, so unknown, allow to run
        xbmc_rev = 0
        ok = 2
    # spam revision info
    if ( not ok ):
        import xbmcgui
        xbmcgui.Dialog().ok( "%s - %s: %s" % ( __plugin__, xbmc.getLocalizedString( 30700 ), __version__, ), xbmc.getLocalizedString( 30701 ) % ( __plugin__, ), xbmc.getLocalizedString( 30702 ) % ( __XBMC_Revision__, ), xbmc.getLocalizedString( 30703 ) )
    #return result
    return ok

def categories(root):
    icona = os.path.join(Addon.getAddonInfo('path'),'resources','images','list.png')
    new_icon = os.path.join(Addon.getAddonInfo('path'), 'resources','images', 'new.png')
    now_icon = os.path.join(Addon.getAddonInfo('path'), 'resources','images', 'now.png')
    next_icon = os.path.join(Addon.getAddonInfo('path'), 'resources','images', 'next.png')
    genre_icon = os.path.join(Addon.getAddonInfo('path'), 'resources','images', 'genre.png')
    search_icon = os.path.join(Addon.getAddonInfo('path'), 'resources','images', 'search.png')
    #baseurl="http://%s.feed.previewnetworks.com/v3.1/%s/"
    #baseurl="http://%s.hdplus.previewnetworks.com/v3.1/%s/"
    baseurl="http://%s.%s.previewnetworks.com/v3.1/%s/"

    if root:
        addDir(Addon.getLocalizedString(30301),baseurl+'now-%s/%s',1,now_icon)
        addDir(Addon.getLocalizedString(30302),baseurl+'coming-%s/%s',2,next_icon)
        addDir(Addon.getLocalizedString(30303),baseurl+'newest-%s/%s',3,new_icon)
        addDir(Addon.getLocalizedString(30300),'genre:',0,genre_icon)
        addDir(Addon.getLocalizedString(30340),baseurl+'search-%s/%s/?search_field=product_title&search_query=%s',99,search_icon)
    else:
        addDir(Addon.getLocalizedString(30304),baseurl+'CinemaAction-%s/%s',10,icona)
        addDir(Addon.getLocalizedString(30305),baseurl+'CinemaAdventure-%s/%s',11,icona)
        addDir(Addon.getLocalizedString(30306),baseurl+'CinemaAnimation-%s/%s',12,icona)
        addDir(Addon.getLocalizedString(30307),baseurl+'CinemaBiography-%s/%s',13,icona)
        addDir(Addon.getLocalizedString(30308),baseurl+'CinemaComedy-%s/%s',14,icona)
        addDir(Addon.getLocalizedString(30309),baseurl+'CinemaCrime-%s/%s',15,icona)
        addDir(Addon.getLocalizedString(30310),baseurl+'CinemaDocumentary-%s/%s',16,icona)
        addDir(Addon.getLocalizedString(30311),baseurl+'CinemaDrama-%s/%s',17,icona)
        addDir(Addon.getLocalizedString(30312),baseurl+'CinemaFamily-%s/%s',18,icona)
        addDir(Addon.getLocalizedString(30313),baseurl+'CinemaFantasy-%s/%s',19,icona)
        addDir(Addon.getLocalizedString(30314),baseurl+'CinemaFilmNoir-%s/%s',20,icona)
        addDir(Addon.getLocalizedString(30315),baseurl+'CinemaGameShow-%s/%s',21,icona)
        addDir(Addon.getLocalizedString(30316),baseurl+'CinemaHistory-%s/%s',22,icona)
        addDir(Addon.getLocalizedString(30317),baseurl+'CinemaHorror-%s/%s',23,icona)
        addDir(Addon.getLocalizedString(30318),baseurl+'CinemaMusic-%s/%s',24,icona)
        addDir(Addon.getLocalizedString(30319),baseurl+'CinemaMusical-%s/%s',25,icona)
        addDir(Addon.getLocalizedString(30320),baseurl+'CinemaMystery-%s/%s',26,icona)
        addDir(Addon.getLocalizedString(30321),baseurl+'CinemaNews-%s/%s',27,icona)
        addDir(Addon.getLocalizedString(30322),baseurl+'CinemaRealityTV-%s/%s',28,icona)
        addDir(Addon.getLocalizedString(30323),baseurl+'CinemaRomance-%s/%s',29,icona)
        addDir(Addon.getLocalizedString(30324),baseurl+'CinemaSciFi-%s/%s',30,icona)
        addDir(Addon.getLocalizedString(30325),baseurl+'CinemaShort-%s/%s',31,icona)
        addDir(Addon.getLocalizedString(30326),baseurl+'CinemaSport-%s/%s',32,icona)
        addDir(Addon.getLocalizedString(30327),baseurl+'CinemaTalkShow-%s/%s',33,icona)
        addDir(Addon.getLocalizedString(30328),baseurl+'CinemaThriller-%s/%s',34,icona)
        addDir(Addon.getLocalizedString(30329),baseurl+'CinemaWar-%s/%s',35,icona)
        addDir(Addon.getLocalizedString(30330),baseurl+'CinemaWestern-%s/%s',36,icona)
        addDir(Addon.getLocalizedString(30331),baseurl+'CinemaChildrenMovie-%s/%s',37,icona)

def addDir(name,url,item,iconimage,parametri={},info={}):
    standardParams={'url':url,'item':item}
    parametri.update(standardParams)
    u=sys.argv[0]+"?"+urllib.urlencode(parametri)
    ok=True
    info.update({ "Titolo": name })
    liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels=info )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    return ok

def get(params,name):
    return params[name][0]

url_source=None
name=None
item=None

Addon = xbmcaddon.Addon( id=__plugin__)
BASE_CURRENT_SOURCE_PATH = xbmc.translatePath( Addon.getAddonInfo( "Profile" ) )

if sys.argv[ 2 ] == "":
    if ( check_compatible() ) == False:
        Return
    else:
        categories(True)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif ( __name__ == "__main__" ):
    if ( sys.argv[ 2 ].find( "Download_Trailer" ) > 0 ):
        import resources.lib.download as download
        download.Main()
    elif ( sys.argv[ 2 ].startswith( "?OpenSettings" ) ):
        xbmcaddon.Addon( id=__plugin__).openSettings()
        xbmc.executebuiltin( "Container.Refresh" )
    elif ( sys.argv[ 2 ].find("url") > 0 ):
        paramstring=sys.argv[2]
        if len(paramstring)>0 :
            print "paramstring %s" % paramstring
            params=cgi.parse_qs(paramstring[ 1 : ],True)
            item=str(get(params,"item"))
            if item == '0':
                categories(False)
                xbmcplugin.endOfDirectory(int(sys.argv[1]))
            else:
                url_source=get(params,"url")
                import resources.lib.trailers as plugin
                plugin.Main(url_source,item)
                del plugin

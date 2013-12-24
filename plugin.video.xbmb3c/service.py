import xbmc, xbmcgui, xbmcaddon, urllib, httplib, os, time, requests
__settings__ = xbmcaddon.Addon(id='plugin.video.xbmb3c')
__cwd__ = __settings__.getAddonInfo('path')
BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )
PLUGINPATH=xbmc.translatePath( os.path.join( __cwd__) )

sDto='{http://schemas.datacontract.org/2004/07/MediaBrowser.Model.Dto}'
sEntities='{http://schemas.datacontract.org/2004/07/MediaBrowser.Model.Entities}'
sArrays='{http://schemas.microsoft.com/2003/10/Serialization/Arrays}'

sys.path.append(BASE_RESOURCE_PATH)
playTime=0
def markWatched (url):
    headers={'Accept-encoding': 'gzip','Authorization' : 'MediaBrowser', 'Client' : 'Dashboard', 'Device' : "Chrome 31.0.1650.57", 'DeviceId' : "f50543a4c8e58e4b4fbb2a2bcee3b50535e1915e", 'Version':"3.0.5070.20258", 'UserId':"ff"}
    resp = requests.post(url, data='', headers=headers)

def setPosition (url,method):
    WINDOW = xbmcgui.Window( 10000 )
    userid=WINDOW.getProperty("userid")
    authString='MediaBrowser UserId=\"' + userid + '\",Client=\"XBMC\",Device=\"XBMB3C\",DeviceId=\"42\",Version=\"0.6.5\"'
    headers={'Accept-encoding': 'gzip','Authorization' : authString}
    xbmc.log('Setting position via: ' + url)
    if method=='POST':
        resp = requests.post(url, data='', headers=headers)
    elif method=='DELETE':
        resp = requests.delete(url, data='', headers=headers)
    
class Service( xbmc.Player ):

    def __init__( self, *args ):
        xbmc.log("starting monitor service")
        pass

    def onPlayBackStarted( self ):
        # Will be called when xbmc starts playing a file
        WINDOW = xbmcgui.Window( 10000 )
        if WINDOW.getProperty("watchedurl")!="":
            positionurl=WINDOW.getProperty("positionurl")
            setPosition(positionurl + '/Progress?PositionTicks=0','POST')

    def onPlayBackEnded( self ):
        # Will be called when xbmc stops playing a file
        WINDOW = xbmcgui.Window( 10000 )
        if WINDOW.getProperty("watchedurl")!="":
            watchedurl=WINDOW.getProperty("watchedurl")
            positionurl=WINDOW.getProperty("positionurl")
            setPosition(positionurl +'?PositionTicks=' + str(int(playTime*10000000)),'DELETE')
            xbmc.log ("runtimeticks:" + WINDOW.getProperty("runtimeticks"))
            percentComplete=(playTime*10000000)/int(WINDOW.getProperty("runtimeticks"))
            xbmc.log ("Percent complete:" + str(percentComplete))
            if ((playTime*10000000)/(int(WINDOW.getProperty("runtimeticks")))) > 0.95:
                markWatched(watchedurl)
            WINDOW.setProperty("watchedurl","")
            WINDOW.setProperty("positionurl","")
            WINDOW.setProperty("runtimeticks","")
            xbmc.log("stopped at time:" + str(playTime))

    def onPlayBackStopped( self ):
        # Will be called when user stops xbmc playing a file
        WINDOW = xbmcgui.Window( 10000 )
        if WINDOW.getProperty("watchedurl")!="":
            watchedurl=WINDOW.getProperty("watchedurl")
            positionurl=WINDOW.getProperty("positionurl")
            setPosition(positionurl +'?PositionTicks=' + str(int(playTime*10000000)),'DELETE')
            xbmc.log ("runtimeticks:" + WINDOW.getProperty("runtimeticks"))
            percentComplete=(playTime*10000000)/int(WINDOW.getProperty("runtimeticks"))
            xbmc.log ("Percent complete:" + str(percentComplete))
            if ((playTime*10000000)/(int(WINDOW.getProperty("runtimeticks")))) > 0.95:
                markWatched(watchedurl)
            WINDOW.setProperty("watchedurl","")
            WINDOW.setProperty("positionurl","")
            WINDOW.setProperty("runtimeticks","")
            xbmc.log("stopped at time:" + str(playTime))

montior=Service()        
while not xbmc.abortRequested:
    if xbmc.Player().isPlaying():
        try:
            playTime=xbmc.Player().getTime()
        except:
            pass
        xbmc.sleep(100)
    else:
        xbmc.sleep(1000)
    
xbmc.log("Service shutting down")

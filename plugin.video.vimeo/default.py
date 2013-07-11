import sys
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcvfs
import xbmcgui
import urllib2
import cookielib

# plugin constants
version = "3.5.2"
plugin = "Vimeo-" + version
author = "TheCollective"
url = "www.xbmc.com"

# xbmc hooks
settings = xbmcaddon.Addon(id='plugin.video.vimeo')
language = settings.getLocalizedString
dbg = settings.getSetting("debug") == "true"
dbglevel = 3

# plugin structure
scraper = ""
feeds = ""
core = ""
storage = ""
navigation = ""
client = ""
cache = ""
utils = ""
login = ""
common = ""
download = ""
player = ""

cookiejar = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
urllib2.install_opener(opener)

if (__name__ == "__main__" ):
    if dbg:
        print plugin + " ARGV: " + repr(sys.argv)
    else:
        print plugin

    try:
        import StorageServer
        cache = StorageServer.StorageServer("Vimeo")
    except:
        import storageserverdummy as StorageServer
        cache = StorageServer.StorageServer("Vimeo")

    import vimeo
    if len(settings.getSetting("oauth_token_secret")) > 0 and len(settings.getSetting("oauth_token")) > 0:
        client = vimeo.VimeoClient(token=settings.getSetting("oauth_token"), token_secret=settings.getSetting("oauth_token_secret"))
    else:
        client = vimeo.VimeoClient()

    import CommonFunctions as common
    common.plugin = plugin

    import SimpleDownloader as downloader
    downloader = downloader.SimpleDownloader()

    import VimeoUtils
    utils = VimeoUtils.VimeoUtils()

    import VimeoLogin
    login = VimeoLogin.VimeoLogin()

    import VimeoStorage
    storage = VimeoStorage.VimeoStorage()

    import VimeoCore
    core = VimeoCore.VimeoCore()

    import VimeoPlayer
    player = VimeoPlayer.VimeoPlayer()

    import VimeoFeeds
    feeds = VimeoFeeds.VimeoFeeds()

    import VimeoPlaylistControl
    playlist = VimeoPlaylistControl.VimeoPlaylistControl()

    import VimeoNavigation
    navigation = VimeoNavigation.VimeoNavigation()

    if (not settings.getSetting("firstrun")):
        settings.setSetting("firstrun", '1')
        login.login()

    if (not sys.argv[2]):
        navigation.listMenu()
    else:
        params = common.getParameters(sys.argv[2])
        get = params.get
        if (get("action")):
            navigation.executeAction(params)
        elif (get("path")):
            navigation.listMenu(params)

import sys
import xbmc
import xbmcgui
import xbmcvfs
import xbmcplugin
import xbmcaddon

settings = xbmcaddon.Addon()
language = settings.getLocalizedString
plugin = settings.getAddonInfo('id')

if __name__ == '__main__':
    import resources.lib.common as common
    common.log('ARGV: ' + repr(sys.argv), common.INFO)

    try:
        import StorageServer
        cache = StorageServer.StorageServer(common.plugin,
            int(settings.getSetting('cache_time')))
    except ImportError:
        common.log("Common Plugin Cache isn't installed, using dummy class.")
        import storageserverdummy
        cache = storageserverdummy.StorageServer(common.plugin)

    from resources.lib.api import Api
    api = Api()

    import resources.lib.nav as nav
    nav.list_menu()

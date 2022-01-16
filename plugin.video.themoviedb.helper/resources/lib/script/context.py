# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import sys


def importcontext(module_name, import_attr, context_property):
    from json import loads
    from resources.lib.addon.modimp import importmodule
    func = importmodule(module_name, import_attr=import_attr)
    func(**loads(sys.listitem.getProperty(context_property)))


def context_playusing():
    import xbmc
    xbmc.executebuiltin(f'RunPlugin({sys.listitem.getProperty("tmdbhelper.context.playusing")})')


def router(route):
    routes = {
        'playusing':
            lambda: context_playusing(),
        'trakt':
            lambda: importcontext('resources.lib.script.sync', 'sync_trakt_item', 'tmdbhelper.context.trakt'),
        'addlibrary':
            lambda: importcontext('resources.lib.update.library', 'add_to_library', 'tmdbhelper.context.addlibrary'),
        'artwork':
            lambda: importcontext('resources.lib.script.method', 'manage_artwork', 'tmdbhelper.context.artwork'),
        'refresh':
            lambda: importcontext('resources.lib.script.method', 'refresh_details', 'tmdbhelper.context.refresh'),
        'related':
            lambda: importcontext('resources.lib.script.method', 'related_lists', 'tmdbhelper.context.related'),
        'sorting':
            lambda: importcontext('resources.lib.script.method', 'sort_list', 'tmdbhelper.context.sorting')
    }
    routes[route]()

import pickle
import os
import sys

import xbmc
import xbmcgui
import xbmcaddon

import api
import ui

print "DRNU: %s" % sys.argv

ADDON = xbmcaddon.Addon(id = 'plugin.video.drnu')

def addFavorite(slug):
    if os.path.exists(FAVORITES_PATH):
        favorites = pickle.load(open(FAVORITES_PATH, 'rb'))
    else:
        favorites = list()

    if not favorites.count(slug):
        favorites.append(slug)
    pickle.dump(favorites, open(FAVORITES_PATH, 'wb'))

    xbmcgui.Dialog().ok(ADDON.getLocalizedString(30008), ADDON.getLocalizedString(30009))

def delFavorite(slug):
    if os.path.exists(FAVORITES_PATH):
        favorites = pickle.load(open(FAVORITES_PATH, 'rb'))
        favorites.remove(slug)
        pickle.dump(favorites, open(FAVORITES_PATH, 'wb'))

    xbmcgui.Dialog().ok(ADDON.getLocalizedString(30008), ADDON.getLocalizedString(30010))

def updateRecentlyWatched(slug):
    if os.path.exists(RECENT_PATH):
        recent = pickle.load(open(RECENT_PATH, 'rb'))
    else:
        recent = list()

    if recent.count(slug):
        recent.remove(slug)
    recent.insert(0, slug)

    recent = recent[0:10] # Limit to ten items
    pickle.dump(recent, open(RECENT_PATH, 'wb'))

def parseParams(input):
    params = {}
    for pair in input.split('&'):
        if pair.find('=') >= 0:
            keyvalue = pair.split('=', 1)
            params[keyvalue[0]] = keyvalue[1]
        else:
            params[pair] = None

    return params
    

if __name__ == '__main__':
    dataPath = xbmc.translatePath(ADDON.getAddonInfo("Profile"))
    api = api.DrNuApi(dataPath, 60)
    ui = ui.DRnuUI(api, int(sys.argv[1]), sys.argv[0])

    FAVORITES_PATH = os.path.join(dataPath, 'favorites.pickle')
    RECENT_PATH = os.path.join(dataPath, 'recent.pickle')
    
    params = parseParams(sys.argv[2][1:])

    if params.has_key('slug'):
        updateRecentlyWatched(params['slug'])
        ui.listVideos(api.getProgramSeriesVideos(params['slug']), False)

    elif params.has_key('newest'):
        ui.listVideos(api.getNewestVideos(), False)

    elif params.has_key('spot'):
        ui.listVideos(api.getSpotlightVideos(), True)

    elif params.has_key('search'):
        ui.searchVideos()

    elif params.has_key('id'):
        ui.playVideo(params['id'])

    elif params.has_key('all'):
        ui.getProgramSeries()

    elif params.has_key('addfavorite'):
        addFavorite(params['addfavorite'])

    elif params.has_key('delfavorite'):
        delFavorite(params['delfavorite'])

    elif params.has_key('favorites'):
        favorites = list()
        if os.path.exists(FAVORITES_PATH):
            favorites = pickle.load(open(FAVORITES_PATH, 'rb'))
        ui.getProgramSeries(favorites, False)

    elif params.has_key('recentlywatched'):
        recent = list()
        if os.path.exists(RECENT_PATH):
            recent = pickle.load(open(RECENT_PATH, 'rb'))
        ui.getProgramSeries(recent)

    else:
        ui.getMainMenu()


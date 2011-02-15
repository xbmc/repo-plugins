import pickle
import os
import sys

import xbmcgui

import danishaddons
import danishaddons.web
import danishaddons.info

import api
import ui

print "DRNU: %s" % sys.argv

def addFavorite(slug):
    if os.path.exists(FAVORITES_PATH):
        favorites = pickle.load(open(FAVORITES_PATH, 'rb'))
    else:
        favorites = list()

    if not favorites.count(slug):
        favorites.append(slug)
    pickle.dump(favorites, open(FAVORITES_PATH, 'wb'))

    xbmcgui.Dialog().ok(danishaddons.msg(30008), danishaddons.msg(30009))

def delFavorite(slug):
    if os.path.exists(FAVORITES_PATH):
        favorites = pickle.load(open(FAVORITES_PATH, 'rb'))
        favorites.remove(slug)
        pickle.dump(favorites, open(FAVORITES_PATH, 'wb'))

    xbmcgui.Dialog().ok(danishaddons.msg(30008), danishaddons.msg(30010))

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



if __name__ == '__main__':
    danishaddons.init(sys.argv)
    api = api.DRnuApi(60)
    ui = ui.DRnuUI(api)

    FAVORITES_PATH = os.path.join(danishaddons.ADDON_DATA_PATH, 'favorites.pickle')
    RECENT_PATH = os.path.join(danishaddons.ADDON_DATA_PATH, 'recent.pickle')

    if danishaddons.ADDON_PARAMS.has_key('slug'):
        updateRecentlyWatched(danishaddons.ADDON_PARAMS['slug'])
        ui.listVideos(api.getProgramSeriesVideos(danishaddons.ADDON_PARAMS['slug']), False)

    elif danishaddons.ADDON_PARAMS.has_key('newest'):
        ui.listVideos(api.getNewestVideos(), False)

    elif danishaddons.ADDON_PARAMS.has_key('spot'):
        ui.listVideos(api.getSpotlightVideos(), True)

    elif danishaddons.ADDON_PARAMS.has_key('search'):
        ui.searchVideos()

    elif danishaddons.ADDON_PARAMS.has_key('id'):
        ui.playVideo(danishaddons.ADDON_PARAMS['id'])

    elif danishaddons.ADDON_PARAMS.has_key('all'):
        ui.getProgramSeries()

    elif danishaddons.ADDON_PARAMS.has_key('addfavorite'):
        addFavorite(danishaddons.ADDON_PARAMS['addfavorite'])

    elif danishaddons.ADDON_PARAMS.has_key('delfavorite'):
        delFavorite(danishaddons.ADDON_PARAMS['delfavorite'])

    elif danishaddons.ADDON_PARAMS.has_key('favorites'):
        favorites = list()
        if os.path.exists(FAVORITES_PATH):
            favorites = pickle.load(open(FAVORITES_PATH, 'rb'))
        ui.getProgramSeries(favorites, False)

    elif danishaddons.ADDON_PARAMS.has_key('recentlywatched'):
        recent = list()
        if os.path.exists(RECENT_PATH):
            recent = pickle.load(open(RECENT_PATH, 'rb'))
        ui.getProgramSeries(recent)

    else:
        ui.getMainMenu()


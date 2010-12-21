import sys
import xbmc, xbmcgui, xbmcplugin
import urllib
from iqueue import *

# plugin modes
MODE1 = 10
MODE1a = 11
MODE1b = 12
MODE2 = 20
MODE3 = 30
MODE4 = 40
MODE5 = 50
MODE6 = 60
MODE6a = 61
MODE6b = 62
MODE6c = 63
MODE6d = 64
MODE6e = 65
MODE6f = 66
MODE6g = 67
MODE6h = 68
MODE6i = 69
MODE6j = 70
MODE6k = 71
MODE6l = 72
MODE7 = 80
MODE7a = 81
MODE7b = 82
MODE7c = 83
MODE7d = 84
MODE7e = 85
MODE7f = 86
MODE7g = 87
MODE7h = 88
MODE7i = 89
MODE7j = 90
MODE7k = 91
MODE7l = 92
MODE7m = 93
MODE7n = 94
MODE7o = 95
MODE7p = 96
MODE7q = 97
MODE7r = 98
MODE7s = 99
MODE7t = 100

# parameter keys
PARAMETER_KEY_MODE = "mode"

# menu item names
SUBMENU1 = "My Instant Queue - ALL"
SUBMENU1a = "My Instant Queue - Movies"
SUBMENU1b = "My Instant Queue - TV Shows"
SUBMENU2 = "Recommended (Filtered for Instant Watch)"
SUBMENU3 = "All New Movies & Shows"
SUBMENU4 = "Search..."
SUBMENU5 = "Top 25 New Movies & Shows"
SUBMENU6 = "By Genre"
SUBMENU6a = "Action & Adventure"
SUBMENU6b = "Children & Family"
SUBMENU6c = "Classics"
SUBMENU6d = "Comedy"
SUBMENU6e = "Documentary"
SUBMENU6f = "Drama"
SUBMENU6g = "Foreign"
SUBMENU6h = "Horror"
SUBMENU6i = "Romance"
SUBMENU6j = "Sci-Fi & Fantasy"
SUBMENU6k = "Television"
SUBMENU6l = "Thrillers"
##Top 25 by Genre
SUBMENU7 = "Top 10 By Genre"
SUBMENU7a = "Action & Adventure"
SUBMENU7b = "Anime & Animation"
SUBMENU7c = "Blu-ray"
SUBMENU7d = "Children & Family"
SUBMENU7e = "Classics"
SUBMENU7f = "Comedy"
SUBMENU7g = "Documentary"
SUBMENU7h = "Drama"
SUBMENU7i = "Faith & Spirituality"
SUBMENU7j = "Foreign"
SUBMENU7k = "Gay & Lesbian"
SUBMENU7l = "Horror"
SUBMENU7m = "Independent"
SUBMENU7n = "Music & Musicals"
SUBMENU7o = "Romance"
SUBMENU7p = "Sci-Fi & Fantasy"
SUBMENU7q = "Special Interest"
SUBMENU7r = "Sports & Fitness"
SUBMENU7s = "Television"
SUBMENU7t = "Thrillers"

# plugin handle
handle = int(sys.argv[1])

# utility functions
def parameters_string_to_dict(parameters):
   ''' Convert parameters encoded in a URL to a dict. '''
   paramDict = {}
   if parameters:
       paramPairs = parameters[1:].split("&")
       for paramsPair in paramPairs:
           paramSplits = paramsPair.split('=')
           if (len(paramSplits)) == 2:
               paramDict[paramSplits[0]] = paramSplits[1]
   return paramDict

def addDirectoryItem(name, isFolder=True, parameters={}, thumbnail=None):
   ''' Add a list item to the XBMC UI.'''
   if thumbnail:
      li = xbmcgui.ListItem(name, thumbnailImage=thumbnail)
   else:
      li = xbmcgui.ListItem(name)
   url = sys.argv[0] + '?' + urllib.urlencode(parameters)
   return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url, listitem=li, isFolder=isFolder)


# UI builder functions
def show_root_menu():
   ''' Show the plugin root menu. '''
   addDirectoryItem(name=SUBMENU1, parameters={ PARAMETER_KEY_MODE:MODE1 }, isFolder=True, thumbnail="special://home/addons/plugin.video.xbmcflicks/resources/images/iqueue_all.png")
   addDirectoryItem(name=SUBMENU1a, parameters={ PARAMETER_KEY_MODE:MODE1a }, isFolder=True, thumbnail="special://home/addons/plugin.video.xbmcflicks/resources/images/iqueue_movies.png")
   addDirectoryItem(name=SUBMENU1b, parameters={ PARAMETER_KEY_MODE:MODE1b }, isFolder=True, thumbnail="special://home/addons/plugin.video.xbmcflicks/resources/images/iqueue_tv.png")

   addDirectoryItem(name=SUBMENU2, parameters={ PARAMETER_KEY_MODE:MODE2 }, isFolder=True, thumbnail="special://home/addons/plugin.video.xbmcflicks/resources/images/recog.png")
   addDirectoryItem(name=SUBMENU5, parameters={ PARAMETER_KEY_MODE:MODE5 }, isFolder=True, thumbnail="special://home/addons/plugin.video.xbmcflicks/resources/images/new_top25.png")
   addDirectoryItem(name=SUBMENU3, parameters={ PARAMETER_KEY_MODE:MODE3 }, isFolder=True, thumbnail="special://home/addons/plugin.video.xbmcflicks/resources/images/new_all.png")
   addDirectoryItem(name=SUBMENU4, parameters={ PARAMETER_KEY_MODE:MODE4 }, isFolder=True, thumbnail="special://home/addons/plugin.video.xbmcflicks/resources/images/search.png")
   #addDirectoryItem(name=SUBMENU6, parameters={ PARAMETER_KEY_MODE:MODE6 }, isFolder=True)
   xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_SUBMENU1():
   ''' Show first submenu. '''
   for i in range(0, 5):
       name = "%s Item %d" % (SUBMENU1, i)
       addDirectoryItem(name, isFolder=False)
   xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_SUBMENU2():
   ''' Show second submenu. '''
   for i in range(0, 10):
       name = "%s Item %d" % (SUBMENU2, i)
       addDirectoryItem(name, isFolder=False)
   xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_SUBMENU6():
   #add in the genre folders
   addDirectoryItem(name=SUBMENU6a, parameters={ PARAMETER_KEY_MODE:
MODE6a }, isFolder=True)
   addDirectoryItem(name=SUBMENU6b, parameters={ PARAMETER_KEY_MODE:
MODE6b }, isFolder=True)
   addDirectoryItem(name=SUBMENU6c, parameters={ PARAMETER_KEY_MODE:
MODE6c }, isFolder=True)
   addDirectoryItem(name=SUBMENU6d, parameters={ PARAMETER_KEY_MODE:
MODE6d }, isFolder=True)
   addDirectoryItem(name=SUBMENU6e, parameters={ PARAMETER_KEY_MODE:
MODE6e }, isFolder=True)
   addDirectoryItem(name=SUBMENU6f, parameters={ PARAMETER_KEY_MODE:
MODE6f }, isFolder=True)
   addDirectoryItem(name=SUBMENU6g, parameters={ PARAMETER_KEY_MODE:
MODE6g }, isFolder=True)
   addDirectoryItem(name=SUBMENU6h, parameters={ PARAMETER_KEY_MODE:
MODE6h }, isFolder=True)
   addDirectoryItem(name=SUBMENU6i, parameters={ PARAMETER_KEY_MODE:
MODE6i }, isFolder=True)
   addDirectoryItem(name=SUBMENU6j, parameters={ PARAMETER_KEY_MODE:
MODE6j }, isFolder=True)
   addDirectoryItem(name=SUBMENU6k, parameters={ PARAMETER_KEY_MODE:
MODE6k }, isFolder=True)
   addDirectoryItem(name=SUBMENU6l, parameters={ PARAMETER_KEY_MODE:
MODE6l }, isFolder=True)
   xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_SUBMENU7():
   #add in the genre folders for the Top 25 items
   addDirectoryItem(name=SUBMENU7a, parameters={ PARAMETER_KEY_MODE:MODE7a }, isFolder=True)
   addDirectoryItem(name=SUBMENU7b, parameters={ PARAMETER_KEY_MODE:MODE7b }, isFolder=True)
   addDirectoryItem(name=SUBMENU7c, parameters={ PARAMETER_KEY_MODE:MODE7c }, isFolder=True)
   addDirectoryItem(name=SUBMENU7d, parameters={ PARAMETER_KEY_MODE:MODE7d }, isFolder=True)
   addDirectoryItem(name=SUBMENU7e, parameters={ PARAMETER_KEY_MODE:MODE7e }, isFolder=True)
   addDirectoryItem(name=SUBMENU7f, parameters={ PARAMETER_KEY_MODE:MODE7f }, isFolder=True)
   addDirectoryItem(name=SUBMENU7g, parameters={ PARAMETER_KEY_MODE:MODE7g }, isFolder=True)
   addDirectoryItem(name=SUBMENU7h, parameters={ PARAMETER_KEY_MODE:MODE7h }, isFolder=True)
   addDirectoryItem(name=SUBMENU7i, parameters={ PARAMETER_KEY_MODE:MODE7i }, isFolder=True)
   addDirectoryItem(name=SUBMENU7j, parameters={ PARAMETER_KEY_MODE:MODE7j }, isFolder=True)
   addDirectoryItem(name=SUBMENU7k, parameters={ PARAMETER_KEY_MODE:MODE7k }, isFolder=True)
   addDirectoryItem(name=SUBMENU7l, parameters={ PARAMETER_KEY_MODE:MODE7l }, isFolder=True)
   addDirectoryItem(name=SUBMENU7m, parameters={ PARAMETER_KEY_MODE:MODE7m }, isFolder=True)
   addDirectoryItem(name=SUBMENU7n, parameters={ PARAMETER_KEY_MODE:MODE7n }, isFolder=True)
   addDirectoryItem(name=SUBMENU7o, parameters={ PARAMETER_KEY_MODE:MODE7o }, isFolder=True)
   addDirectoryItem(name=SUBMENU7p, parameters={ PARAMETER_KEY_MODE:MODE7p }, isFolder=True)
   addDirectoryItem(name=SUBMENU7q, parameters={ PARAMETER_KEY_MODE:MODE7q }, isFolder=True)
   addDirectoryItem(name=SUBMENU7r, parameters={ PARAMETER_KEY_MODE:MODE7r }, isFolder=True)
   addDirectoryItem(name=SUBMENU7s, parameters={ PARAMETER_KEY_MODE:MODE7s }, isFolder=True)
   addDirectoryItem(name=SUBMENU7t, parameters={ PARAMETER_KEY_MODE:MODE7t }, isFolder=True)
   xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
   


# parameter values
params = parameters_string_to_dict(sys.argv[2])
mode = int(params.get(PARAMETER_KEY_MODE, "0"))
print "##########################################################"
print("Mode: %s" % mode)
print("Arg1: %s" % sys.argv[1])
print("Arg2: %s" % sys.argv[2])
print "##########################################################"

# Depending on the mode, call the appropriate function to build the UI.
if not sys.argv[2]:
   # new start
   ok = show_root_menu()
elif mode == MODE1:
   getInstantQueue()
elif mode == MODE1a:
   getInstantQueue(1)
elif mode == MODE1b:
   getInstantQueue(2)
elif mode == MODE2:
    getRecommendedQueue()
elif mode == MODE3:
    getNewToWatchInstant()
elif mode == MODE4:
    keyboard = xbmc.Keyboard()
    keyboard.doModal()
    if (keyboard.isConfirmed()):
      arg = keyboard.getText()
      #print "keyboard returned: " + keyboard.getText()
      doSearch(arg)
    else:
      print "user canceled"
elif mode == MODE5:
   getNewToWatchInstantTopX()

elif mode == MODE6:
   ok = show_SUBMENU6()
elif mode == MODE6a:
   ok = show_SUBMENU6()
elif mode == MODE6b:
   ok = show_SUBMENU6()
elif mode == MODE6c:
   ok = show_SUBMENU6()
elif mode == MODE6d:
   ok = show_SUBMENU6()
elif mode == MODE6e:
   ok = show_SUBMENU6()
elif mode == MODE6f:
   ok = show_SUBMENU6()
elif mode == MODE6g:
   ok = show_SUBMENU6()
elif mode == MODE6h:
   ok = show_SUBMENU6()
elif mode == MODE6i:
   ok = show_SUBMENU6()
elif mode == MODE6j:
   ok = show_SUBMENU6()
elif mode == MODE6k:
   ok = show_SUBMENU6()
elif mode == MODE6l:
   ok = show_SUBMENU6()
elif mode == MODE7:
   ok = show_SUBMENU7()
elif mode == MODE7a:
  getTop25Feed("296")
elif mode == MODE7b:
  getTop25Feed("623")
elif mode == MODE7c:
  getTop25Feed("2444")
elif mode == MODE7d:
  getTop25Feed("302")
elif mode == MODE7e:
  getTop25Feed("306")
elif mode == MODE7f:
  getTop25Feed("307")
elif mode == MODE7g:
  getTop25Feed("864")
elif mode == MODE7h:
  getTop25Feed("315")
elif mode == MODE7i:
  getTop25Feed("2108")
elif mode == MODE7j:
  getTop25Feed("2514")
elif mode == MODE7k:
  getTop25Feed("330")
elif mode == MODE7l:
  getTop25Feed("338")
elif mode == MODE7m:
  getTop25Feed("343")
elif mode == MODE7n:
  getTop25Feed("2310")
elif mode == MODE7o:
  getTop25Feed("371")
elif mode == MODE7p:
  getTop25Feed("373")
elif mode == MODE7q:
  getTop25Feed("2223")
elif mode == MODE7r:
  getTop25Feed("2190")
elif mode == MODE7s:
  getTop25Feed("2197")
elif mode == MODE7t:
  getTop25Feed("387")

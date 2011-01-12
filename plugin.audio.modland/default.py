import sys, os
import urllib, cgi, re, htmlentitydefs, xml.dom.minidom
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

# plugin constants
__plugin__     = "Modland"
__author__     = "BuZz [buzz@exotica.org.uk] / http://www.exotica.org.uk"
__svn_url__    = "http://xbmc-addons.googlecode.com/svn/trunk/plugins/music/modland"
__version__    = "0.10"

__settings__ = xbmcaddon.Addon('plugin.audio.modland')
__language__ = __settings__.getLocalizedString

MODLAND_URL = "http://www.exotica.org.uk/mediawiki/extensions/ExoticASearch/Modland_xbmc.php"
#MODLAND_URL = 'http://exotica.travelmate/mediawiki/extensions/ExoticASearch/Modland_xbmc.php'

# try and get xbmc revision
rev_re = re.compile('r(\d+)')
try:
  xbmc_rev = int(rev_re.search(xbmc.getInfoLabel( 'System.BuildVersion' )).group(1))
except:
  xbmc_rev = 0

PLUGIN_DATA = __settings__.getAddonInfo('profile')
SEARCH_FILE = os.path.join(PLUGIN_DATA, "search.txt")

if not os.path.isdir(PLUGIN_DATA):
  try:
    os.makedirs(PLUGIN_DATA)
  except IOError, e:
    xbmc.log("Unable to make plugin folder: %s" % PLUGIN_DATA, xbmc.LOGERROR)
    raise

if not os.path.isfile(SEARCH_FILE):
  try:
    open(SEARCH_FILE, 'wb').close() 
  except IOError, e:
    xbmc.log("Unable to open search file: %s" % SEARCH_FILE, xbmc.LOGERROR)
    raise

handle = int(sys.argv[1])

def get_params(defaults):
  new_params = defaults
  params = cgi.parse_qs(sys.argv[2][1:])
  for key, value in params.iteritems():
    new_params[key] = urllib.unquote_plus(params[key][0])
  return new_params

def show_options():
  url =  sys.argv[0] + '?' + urllib.urlencode( { 'mode': "search" } )
  li = xbmcgui.ListItem(__language__(30000))
  ok = xbmcplugin.addDirectoryItem(handle, url, listitem = li, isFolder = True)

  # get list of saved searches
  search_list = load_list(SEARCH_FILE)
  for search in search_list:
    li = xbmcgui.ListItem(search)
    url = sys.argv[0] + '?' + urllib.urlencode( { 'mode': "search", 'search': search } )
    cmd = "XBMC.RunPlugin(%s?mode=deletesearch&search=%s)" % (sys.argv[0], urllib.quote_plus(search) )
    li.addContextMenuItems( [ (__language__(30001), cmd) ] )
    ok = xbmcplugin.addDirectoryItem(handle, url, listitem = li, isFolder = True)

  xbmcplugin.endOfDirectory(handle, succeeded = True, updateListing = False, cacheToDisc = False )

def get_search():
  kb = xbmc.Keyboard("", __language__(30002))
  kb.doModal()
  if not kb.isConfirmed():
    return None
  search = kb.getText()
  search_list = load_list(SEARCH_FILE)
  search_list.append(search)
  save_list(SEARCH_FILE, search_list)
  return search

def get_results(search):

  url = MODLAND_URL + '?' + urllib.urlencode( { 'qs': search } )

  response = urllib.urlopen(url)
  resultsxml = response.read()
  response.close

  dom = xml.dom.minidom.parseString(resultsxml)
  items = dom.getElementsByTagName('item')
  count = items.length
  for item in items:
    title = item.getElementsByTagName('title')[0].firstChild.data
    artist = item.getElementsByTagName('author')[0].firstChild.data
    format = item.getElementsByTagName('format')[0].firstChild.data
    if item.getElementsByTagName('collect')[0].firstChild == None:
      collect = ''
    else:
      collect = item.getElementsByTagName('collect')[0].firstChild.data
    
    stream_url = item.getElementsByTagName('url')[0].firstChild.data
    
    label = title + ' - ' + artist + ' - ' + format

    li = xbmcgui.ListItem( label )
    li.setInfo( type = 'music', infoLabels = { 'title': label, 'genre': format, 'artist': artist, 'album': collect } )
    li.setProperty('mimetype', 'audio/ogg')

    # revision 26603 adds my patch with support for ogg mime types for paplayer so we can pass
    # the url directly, otherwise we pass back to the plugin and force an alternative player
    if xbmc_rev >= 26603:
      url = stream_url
    else:
      url = sys.argv[0] + '?'
      url += urllib.urlencode( { 'mode': 'play', 'title': title, 'artist': artist, 'genre': format, 'album': collect, 'url': stream_url } )

    ok = xbmcplugin.addDirectoryItem(handle, url, listitem = li, isFolder = False, totalItems = count)

  xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_TITLE)
  xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_ARTIST)
  xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_GENRE)
  xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_ALBUM)
  xbmcplugin.endOfDirectory(handle = handle, succeeded = True)

def play_stream(url, title, info):
  listitem = xbmcgui.ListItem(title)
  listitem.setInfo ( 'music', info )
  player = xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER)
  player.play(url, listitem)

# load a list from a file, removing any duplicates and stripped wihtespace/linefeeds
def load_list(file):
  li = open(file, 'rb').readlines()
  # remove duplicates
  li = list(set(li))
  # remove whitespace
  li = ([x.strip() for x in li])
  # and sort
  li.sort()
  return li

# save a list to a file
def save_list(file, li):
  file = open(file, 'wb')
  for item in li:
    if item:
      file.write(item + "\n")
  file.close()

params = get_params( { 'mode': None, 'search': None } )
mode = params['mode']
search = params['search']

if mode == None:
  show_options()

elif mode == 'deletesearch':
  search_list = load_list(SEARCH_FILE)
  search_list.remove(search)
  save_list(SEARCH_FILE, search_list)
  xbmc.executebuiltin('Container.Refresh')

elif mode == 'search':

  if search == None:
    search = get_search()
  else:
    search = params['search']

  if search != None and len(search) >= 3:
    get_results(search)
  else:
    show_options()

elif mode == 'play':
  title = urllib.unquote_plus(params['title'])
  artist = urllib.unquote_plus(params['artist'])
  genre = urllib.unquote_plus(params['genre'])
  album = urllib.unquote_plus(params['album'])
  url = urllib.unquote_plus(params['url'])

  info = { 'title': title, 'artist': artist, 'genre': genre, 'album': album }
  play_stream(url, title, info)

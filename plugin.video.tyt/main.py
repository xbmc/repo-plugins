import os, sys, xbmcgui, xbmcplugin, xbmcaddon, json
import httplib
from resources.lib.modules import logon
from resources.lib.modules import scrape
from urlparse import parse_qsl
from urllib2 import unquote 

PLUGIN_ID = 'plugin.video.tyt'
addon = xbmcaddon.Addon(PLUGIN_ID)
_handle = int(sys.argv[1])
_url = sys.argv[0]
__language__ = addon.getLocalizedString
xbmcplugin.setContent(_handle, 'tvshows')
addon_folder = os.path.join(xbmc.translatePath( "special://profile/addon_data/" ), PLUGIN_ID)
changelog = os.path.join(xbmc.translatePath( "special://home/addons/" ), PLUGIN_ID + "/changelog.txt")
settings = xbmcaddon.Addon(id=PLUGIN_ID)
user_name = settings.getSetting("username")
user_pwd = settings.getSetting("password")

cookie = {}

def show_changelog():
  with open(changelog) as f:
    text = f.read()
  dialog = xbmcgui.Dialog()
  label = '%s - %s' % (xbmc.getLocalizedString(24054), settings.getAddonInfo('name'))
  dialog.textviewer(label, text)

def sendResponse(cookies, pagename):
  conn = httplib.HTTPSConnection("tyt.com")
  conn.request("GET", pagename, "", cookies)
  response = conn.getresponse()
  page = response.read()
  import HTMLParser
  page = unquote(page).decode('utf8')
  page = HTMLParser.HTMLParser().unescape(page).encode('utf8')
  conn.close()
  return page

    
def login():

  loggedin, cookie = logon.logon(user_name, user_pwd)
  xbmc.log('Logon Successful' if loggedin == 201 else 'Logon Failed')
  if loggedin != 201:
    return False
  with open(addon_folder + '/cookies.txt', 'w') as f:
    json.dump(cookie, f)
  return True
      
def get_cookie():
#  global cookie
  with open(addon_folder + '/cookies.txt') as f:
    cookie = json.load(f)
  return cookie

def list_episodes(page, showurl, pagenum):
#    hosts[x] = {"host": host,
#                "info": host_info
#               }
#    show[i] = {"date" : date,
#               "title": title,
#               "link": link,
#               "description": description,
#               "hosts" : hosts
#              }
#
  listing = []
  episodes = scrape.Get_Show_Episodes(page)
  for episode in episodes:
    list_item = xbmcgui.ListItem(label=episodes[episode]["title"])
    list_item.setInfo('video', {'title': episodes[episode]['title'], 'genre': 'news', 'aired': episodes[episode]['date'], 'plot': episodes[episode]['description'], 'mediatype': 'tvshow'}) 
    art = episodes[episode]['image']
    list_item.setArt({'thumb': art, 'icon': art, 'fanart': art})
    list_item.setProperty('IsPlayable', 'true')
    url = '{0}?action=play&video={1}'.format(_url, episodes[episode]['link'])
    is_folder = False
    listing.append((url, list_item, is_folder))

  xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_DATE)
  xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
  xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)

  list_item = xbmcgui.ListItem(label='Next')
  list_item.setProperty('IsPlayable', 'false')
  url = '{0}?action=episodes&show={1}&page={2}'.format(_url, showurl, str(int(pagenum)+1))
  is_folder = True
  listing.append((url, list_item, is_folder))

  xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
  xbmcplugin.endOfDirectory(_handle)
                 
  
def list_shows(page):
  listing = []
  shows = scrape.List_Shows(page)
  for show in shows:
    list_item = xbmcgui.ListItem(label=shows[show]["show"])
   
    list_item.setArt({'thumb': shows[show]["avatar"],
                      'fanart': shows[show]["background"],
                      'banner': shows[show]["banner"],
                      'icon': shows[show]["avatar"]})
    is_folder = True
    list_item.setProperty('IsPlayable', 'false')
    url = '{0}?action=episodes&show={1}&page={2}'.format(_url, shows[show]['link'], '1')
    listing.append((url, list_item, is_folder))

  xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
  xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
  xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
  xbmcplugin.endOfDirectory(_handle)
                 
    
def popup(text):
  xbmcgui.Dialog().ok(PLUGIN_ID, text)
    
def play_video(path):
  # Create a playable item with a path to play.
  play_item = xbmcgui.ListItem(path=path)
  # Pass the item to the Kodi player.
  xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
       
def router(paramstring):
  if settings.getSetting("version") != settings.getAddonInfo('version'):
    show_changelog()
    settings.setSetting(id="version", value=settings.getAddonInfo('version'))
  params = dict(parse_qsl(paramstring))
  if params:
    if params['action'] == 'episodes':
      page = sendResponse(cookie, params['show'] + "?page=" + params['page'])
      list_episodes(page, params['show'], params['page'])
    elif params['action'] == 'play':
      page = sendResponse(get_cookie(), params['video'])
#      with open('main_show_episode.html', 'w') as f:
#        f.write(page)
#      hd, sd = scrape.Watch_Episode(page)
      episode_url = scrape.Watch_Episode(page, params['video'].rsplit('/',1)[1])
      if episode_url is not None:
          play_video(episode_url)
      else:
        popup(__language__(30004)) # "Video doesn't exist on website."
  else:
    login()
#    page = sendResponse(get_cookie(), "/live/streams/1260")
#    page = sendResponse2(get_cookie(), "/api/v1/live/streams/1260")
#    with open('1260_cookie.html', 'w') as f:
#      f.write(page)    
    list_shows(sendResponse(get_cookie(), "/shows"))    
if __name__ == '__main__':
  router(sys.argv[2][1:])

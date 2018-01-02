import os, sys, xbmcgui, xbmcplugin, xbmcaddon, json
import httplib
import urllib2
from resources.lib.modules import logon
from resources.lib.modules import type1
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

murder_url        = "/category/murder-with-friends/"
murder_thumb      = "murder.jpg"
ap_url            = "/category/aggressive-progressives-membership/"
ap_thumb          = "ap.png"
rebelhq_url       = "/category/membership/rebel-headquarters-on-demand/"
rebelhq_thumb     = "rebelhq.jpg"
hour1_url         = "/category/membership/main-show-hour-1/"
hour1_thumb       = "hour1.png"
hour2_url         = "/category/membership/main-show-hour-2/"
hour2_thumb       = "hour2.png"
pg_url            = "/category/membership/post-game/"
pg_thumb          = "pg.png"
oldschool_url     = "/category/membership/tyt-old-school-on-demand/"
oldschool_thumb   = "oldschool.png"
bts_url           = "/category/membership/behind-the-scenes/"
bts_thumb         = "bts.png"
tytclassics_url   = "/category/membership/tytclassics/"
tytclassics_thumb = "tytc.png"
thinktank_url     = "plugin://plugin.video.youtube/user/tytuniversity/"
thinktank_thumb   = "think_tank.jpg"
tytsports_url     = "plugin://plugin.video.youtube/user/tytsports/"
tytsports_thumb   = "tytsports.jpg"
tytpolitics_url   = "plugin://plugin.video.youtube/channel/UCuMo0RRtnNDuMB8DV5stEag/"
tytpolitics_thumb = "tytpolitics.jpg"
wtf_url           = "plugin://plugin.video.youtube/user/whattheflickshow/"
wtf_thumb         = "wtf.jpg"
pop_url           = "plugin://plugin.video.youtube/user/popcultured/"
pop_thumb         = "pop.jpg"
tytint_url        = "plugin://plugin.video.youtube/user/tytinterviews/"
tytint_thumb      = "tytint.jpg"
nerd_url          = "plugin://plugin.video.youtube/user/nerdalert/"
nerd_thumb        = "nerd.jpg"
sec_url           = "plugin://plugin.video.youtube/user/seculartalk/"
sec_thumb         = "sec.jpg"
sam_url           = "plugin://plugin.video.youtube/user/samseder/"
sam_thumb         = "sam.jpg"
point_url         = "plugin://plugin.video.youtube/user/townsquare/"
point_thumb       = "point.jpg"
tytlive_url       = "/live/"
tytlive_thumb     = "tytlive.jpg"
members_live_url  = "/memberslive/"
members_live_thumb = "tytlive.jpg"
special_events_url = "/category/membership/specialevents/"
special_events_thumb = "tytlive.jpg"
allstar_url       = "/category/membership/all-star-tuesdays-membership/"
allstar_thumb     = "allstar.jpg"
members_cat = {"Hour 1":            {"url":hour1_url, "thumb":hour1_thumb, "type":"members"},
               "Hour 2":            {"url":hour2_url, "thumb":hour2_thumb, "type":"members"},
               "Aggressive Progressives" : {"url":ap_url, "thumb":ap_thumb, "type":"members"},
               "Rebel Headquarters" : {"url":rebelhq_url, "thumb":rebelhq_thumb, "type":"members"},
               "Post Game":         {"url":pg_url, "thumb":pg_thumb, "type":"members"},
               "Old School":        {"url":oldschool_url, "thumb":oldschool_thumb, "type":"members"},
               "TYT Classics":      {"url":tytclassics_url, "thumb":tytclassics_thumb, "type":"members"},
               "Murder with Friends": {"url":murder_url, "thumb":murder_thumb, "type":"members"},
               "Special Events":    {"url":special_events_url, "thumb":special_events_thumb, "type":"members"},
               "Members LIVE show": {"url":members_live_url, "thumb":members_live_thumb, "type":"members_live"},
               "Behind The Scenes": {"url":bts_url, "thumb":bts_thumb, "type":"members"}}
              

main_cat = {   "Members Only":      {"menu":"members", "thumb":hour1_thumb, "type":"members_menu"},
               "TYT Sports":        {"url":tytsports_url, "thumb":tytsports_thumb, "type":"youtube_channel"},
               "TYT Politics":      {"url":tytpolitics_url, "thumb":tytpolitics_thumb, "type":"youtube_channel"},
               "What The Flick?!":  {"url":wtf_url, "thumb":wtf_thumb, "type":"youtube_channel"},
               "Pop Trigger":       {"url":pop_url, "thumb":pop_thumb, "type":"youtube_channel"},
               "TYT Interviews":    {"url":tytint_url, "thumb":tytint_thumb, "type":"youtube_channel"},
               "Nerd Alert":        {"url":nerd_url, "thumb":nerd_thumb, "type":"youtube_channel"},
               "Secular Talk":      {"url":sec_url, "thumb":sec_thumb, "type":"youtube_channel"},
               "The Point with Ana Kasparian": {"url":point_url, "thumb":point_thumb, "type":"youtube_channel"},
               "The Majority Report with Sam Seder": {"url":sam_url, "thumb":sam_thumb, "type":"youtube_channel"},
               "TYT Live Stream":   {"url":tytlive_url, "thumb":tytlive_thumb, "type":"youtube_video"},
               "ThinkTank":         {"url":thinktank_url, "thumb":thinktank_thumb, "type":"youtube_channel"}}
menus = {"main":main_cat,"members":members_cat}

def show_changelog():
  #with open(settings.getAddonInfo('changelog')) as f:
  with open(changelog) as f:
    text = f.read()
  dialog = xbmcgui.Dialog()
  label = '%s - %s' % (xbmc.getLocalizedString(24054), settings.getAddonInfo('name'))
  dialog.textviewer(label, text)

def jw_website(page):
  f = urllib2.urlopen(page)
  return f.read()
  
def sendResponse(cookies, pagename): 
  conn = httplib.HTTPSConnection("tytnetwork.com")
  conn.request("GET", pagename, "", cookies)
  response = conn.getresponse()   
  page = response.read()     	
  import HTMLParser
  page = unquote(page).decode('utf8')
  page = HTMLParser.HTMLParser().unescape(page).encode('utf8')
  conn.close()
  return page
    
def login():
  loggedin, cookies = logon.logon(user_name, user_pwd)
  xbmc.log('Logon Successful' if loggedin == 302 else 'Logon Failed')
  if loggedin != 302:
    return False
  global cookie 
  cookie = cookies
  with open(addon_folder + '/cookies.txt', 'w') as f:
    json.dump(cookies, f)
  return True
      
def get_cookie():
  global cookie
  with open(addon_folder + '/cookies.txt') as f:
    cookie = json.load(f)

        
def list_categories(menu):
  listing = []
  MEDIA_URL = 'special://home/addons/{0}/resources/images/'.format(PLUGIN_ID)
  for category in menu:#categories:
    list_item = xbmcgui.ListItem(label=category)
    list_item.setArt({'thumb': (MEDIA_URL + menu[category]['thumb']),
                      'icon': (MEDIA_URL + menu[category]['thumb']),
                      'fanart': settings.getAddonInfo('fanart')})
    list_item.setInfo('video', {'title': category, 'genre': 'News'}) 

    if   menu[category]['type'] is 'members_menu':                            #if selection is for members area
      url = '{0}?action=menu&menu={1}'.format(_url, menu[category]['menu'])
      is_folder = True

    elif menu[category]['type'] is 'youtube_video':                           #if selection is tytlive
      scrape = sendResponse(cookie, tytlive_url)
      link = type1.get_live(scrape)
      url = 'plugin://plugin.video.youtube/play/?video_id=%s' % (link)
      list_item.setProperty('IsPlayable', 'true')
      is_folder = False      

    elif menu[category]['type'] is 'members':                                 #if selection is in members area
      url = '{0}?action=listing&category={1}'.format(_url, category)
      is_folder = True

    elif menu[category]['type'] is 'members_live':
      scrape = sendResponse(cookie, members_live_url)
      link = type1.get_members_live(scrape)
      url = 'plugin://plugin.video.youtube/play/?video_id=%s' % (link)
      list_item.setProperty('IsPlayable', 'true')
      is_folder = False
    
    elif menu[category]['type'] is 'youtube_channel':                         #If selection is a youtube channel
      url = main_cat[category]['url'] 
      is_folder = True

    listing.append((url, list_item, is_folder))
  xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
  xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
  xbmcplugin.endOfDirectory(_handle)
    
def popup(text):
  xbmcgui.Dialog().ok(PLUGIN_ID, text)
    
def list_videos(category, url=None):
  listing = []
  if url is None:
      page = sendResponse(cookie, members_cat[category]['url'])
  else:
      page = sendResponse(cookie, url) 
  videos = type1.get_links(page)
  MEDIA_URL = 'special://home/addons/{0}/resources/images/'.format(PLUGIN_ID)
  thumb = (MEDIA_URL + members_cat[category]['thumb'])        
         

  for video in videos:
    # Create a list item with a text label and a thumbnail image.
    list_item = xbmcgui.ListItem(label=video['name'])
    # Set additional info for the list item.
    list_item.setInfo('video', {'title': video['name'], 'genre': video['genre'], 'aired': video['aired'], 'plot': video['plot'], 'mediatype': video['mediatype']})
    list_item.setArt({'thumb': thumb, 'icon': thumb, 'fanart': thumb})
    list_item.setProperty('IsPlayable', 'true')
    # Create a URL for the plugin recursive callback.
    # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/vids/crab.mp4
    url = '{0}?action=play&video={1}'.format(_url, video['video'])
    is_folder = False
    listing.append((url, list_item, is_folder))
  list_item = xbmcgui.ListItem(label='Next')
  list_item.setProperty('IsPlayable', 'false')
  url = '{0}?action=listing&category={1}&url={2}'.format(_url, category, type1.page_info(page))
  is_folder = True
  listing.append((url, list_item, is_folder))
  
  # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
  # instead of adding one by ove via addDirectoryItem
  xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
  xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
  xbmcplugin.endOfDirectory(_handle)
  
def play_video(path):
  # Create a playable item with a path to play.
  play_item = xbmcgui.ListItem(path=path)
  # Pass the item to the Kodi player.
  xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
       
def router(paramstring):
  # Parse a URL-encoded paramstring to the dictionary of
  # {<parameter>: <value>} elements  
  if settings.getSetting("version") != settings.getAddonInfo('version'):
    show_changelog()
    settings.setSetting(id="version", value=settings.getAddonInfo('version'))
  params = dict(parse_qsl(paramstring))
  if params:
    if params['action'] == 'listing':
      if 'url' in params.keys():
        list_videos(params['category'], params['url'])
      else: #list videos in member section
        get_cookie()
        list_videos(params['category'])
    elif params['action'] == 'menu':
      if params['menu'] == 'members':
        if login():
          list_categories(menus[params['menu']])
        else:
          popup(__language__(30003))#"Members Only is for paid members of TYTNetwork.com.  Please check username/password in plugin settings")
      else:
        list_categories(menus[params['menu']])
    elif params['action'] == 'play':              
      vid = params['video'].split("https://tytnetwork.com",1)[1]
      get_cookie()
      page = sendResponse(cookie,vid)
      video_url = type1.get_video(page)
      if video_url is not None:
        #play_video(type1.get_video(sendResponse(cookie, vid)))
        if video_url[0] == "/":
          page = jw_website("http:" + video_url)
          video_url = type1.get_jw(page)
        play_video(video_url)
      else:
        popup(__language__(30004)) # "Video doesn't exist on website."
  else:
    list_categories(main_cat)

if __name__ == '__main__':
  router(sys.argv[2][1:])

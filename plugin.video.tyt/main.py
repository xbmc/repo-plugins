import os, sys, xbmcgui, xbmcplugin, xbmcaddon, json
import httplib

from resources.lib.modules import logon
from resources.lib.modules import type1
from urlparse import parse_qsl

PLUGIN_ID = 'plugin.video.tyt'
_handle = int(sys.argv[1])
_url = sys.argv[0]
xbmcplugin.setContent(_handle, 'tvshows')
addon_folder = os.path.join(xbmc.translatePath( "special://profile/addon_data/" ), PLUGIN_ID)

settings = xbmcaddon.Addon(id=PLUGIN_ID)
user_name = settings.getSetting("username")
user_pwd = settings.getSetting("password")
cookie = {}
hour1url  = "/category/membership/main-show-hour-1/"
hour2url  = "/category/membership/main-show-hour-2/"
pgurl     = "/category/membership/post-game/"
oldschool = "/category/membership/oldschool/"
bts       = "/category/membership/behind-the-scenes/"
tytclassics = "/category/membership/tytclassics/"
hour1thumb = "hour1.png"
hour2thumb = "hour2.png"
pgthumb = "pg.png"
oldschoolthumb = "oldschool.png"
btsthumb = "bts.png"
tytclassicsthumb = "tctc.png"

categories = {"Hour 1": hour1url, "Hour 2": hour2url, "Post Game": pgurl, "Old School": oldschool, "Behind The Scenes": bts}#, "TYT Classics": tytclassics}
thumbs = {"Hour 1": hour1thumb, "Hour 2": hour2thumb, "Post Game": pgthumb, "Old School": oldschoolthumb, "Behind The Scenes": btsthumb, "TYT Classics": tytclassicsthumb}

def sendResponse(cookies, pagename): 
    conn = httplib.HTTPSConnection("tytnetwork.com")
    conn.request("GET", pagename, "", cookies)
    response = conn.getresponse()   
    page = response.read()     	
    import urllib2, HTMLParser
    page = urllib2.unquote(page).decode('utf8')
    page = HTMLParser.HTMLParser().unescape(page).encode('utf8')
    conn.close()
    with open(addon_folder + '/input.html', 'w') as file_:
        file_.write(page)
    return page
    
def login():
    loggedin, cookies = logon.logon(user_name, user_pwd)
    xbmc.log('Logon Successful' if loggedin == 302 else 'Logon Failed')
    global cookie 
    cookie = cookies
    with open(addon_folder + '/cookies.txt', 'w') as f:
        json.dump(cookies, f)
        
def get_cookie():
    global cookie
    with open(addon_folder + '/cookies.txt') as f:
        cookie = json.load(f)

        
def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    # Get video categories
    # Create a list for our items.
    listing = []
    # Iterate through categories
    MEDIA_URL = 'special://home/addons/{0}/resources/images/'.format(PLUGIN_ID)

    for category in categories:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=category)
        list_item.setArt({'thumb': (MEDIA_URL + thumbs[category]),
                          'icon': (MEDIA_URL + thumbs[category]),
                          'fanart': settings.getAddonInfo('fanart')})
        # http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
        list_item.setInfo('video', {'title': category, 'genre': category})
        # Create a URL for the plugin recursive callback.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = '{0}?action=listing&category={1}'.format(_url, category)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the listing as a 3-element tuple.
        listing.append((url, list_item, is_folder))
    # Add our listing to Kodi.
    # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
    # instead of adding one by ove via addDirectoryItem.
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)
    
def popup(text):

    xbmcgui.Dialog().ok(PLUGIN_ID, text)
    
    
def list_videos(category):
    """
    Create the list of playable videos in the Kodi interface.

    :param category: str
    """
    # Get the list of videos in the category.
    #videos = get_videos(category)
    # Create a list for our items.
    listing = []
    # Iterate through videos.
    
#    if category in ('Hour 1', 'Hour 2', 'Post Game'):       
    page = sendResponse(cookie, categories[category])           
    videos = type1.get_links(page)
    MEDIA_URL = 'special://home/addons/{0}/resources/images/'.format(PLUGIN_ID)
    thumb = (MEDIA_URL + thumbs[category])        
           

    for video in videos:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=video['name'])
        # Set additional info for the list item.
        list_item.setInfo('video', {'title': video['name'], 'genre': video['genre'], 'plot': video['plot'], 'mediatype': video['mediatype']})
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': thumb, 'icon': thumb, 'fanart': thumb})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for the plugin recursive callback.
        # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/vids/crab.mp4
        url = '{0}?action=play&video={1}'.format(_url, video['video'])
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the listing as a 3-element tuple.
        listing.append((url, list_item, is_folder))
    # Add our listing to Kodi.
    # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
    # instead of adding one by ove via addDirectoryItem.
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)
  
def play_video(path):
    """
    Play a video by the provided path.

    :param path: str
    """
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
       
def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring:
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements  
    #cookie = params['login']
    params = dict(parse_qsl(paramstring))
    if params:
        get_cookie()
        if params['action'] == 'listing':
            list_videos(params['category'])
        elif params['action'] == 'play':              
            vid = params['video'].split("https://tytnetwork.com",1)[1]     
            video_url = type1.get_video(sendResponse(cookie,vid))
            if video_url is not None:
                play_video(type1.get_video(sendResponse(cookie, vid)))
            else:
                popup("Video doesn't exist on website")      
    else:

        login()
        list_categories()

if __name__ == '__main__':
    router(sys.argv[2][1:])



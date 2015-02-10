import urllib
import urllib2
import simplejson
import xbmcaddon
import xbmcplugin
import xbmcgui

API_PATH = 'http://api.animevice.com'
API_KEY = '13309fcce038ef04a05f2a5e2203b52ed3d47592' # Default API key
my_addon = xbmcaddon.Addon('plugin.video.animevice')

def CATEGORIES():
    account_linked = False
    user_api_key = my_addon.getSetting('api_key')
    if user_api_key:
        response = urllib2.urlopen(API_PATH + '/chats/?api_key=' + user_api_key + '&format=json')
        data = simplejson.loads(response.read())
        if data['status_code'] == 100:
            # Revert to the default key
            my_addon.setSetting('api_key', '')
        else:
            global API_KEY
            API_KEY = user_api_key
            account_linked = True

    response = urllib2.urlopen(API_PATH + '/video_types/?api_key=' + API_KEY + '&format=json')
    category_data = simplejson.loads(response.read())['results']
    response.close()

    name = 'Latest'
    url = API_PATH + '/videos/?api_key=' + API_KEY + '&sort=-publish_date&format=json'
    iconimage = ''
    addDir(name, url, 2, '')

    for cat in category_data:
        name = cat['name']
        url = API_PATH + '/videos/?api_key=' + API_KEY + '&video_type=' + str(cat['id']) + '&sort=-publish_date&format=json'
        iconimage = ''
        addDir(name, url, 2, '')

    name = 'Search'
    iconimage = ''
    addDir(name, 'search', 1, '')

    if not account_linked:
        name = 'Link Account'
        iconimage = ''
        addDir(name, 'link', 1, '')

def GET_API_KEY(link_code):
    if link_code and len(link_code) == 6:
        try:
            response = urllib2.urlopen(API_PATH + '/validate?link_code=' + link_code + '&format=json')
            data = simplejson.loads(response.read())
            new_api_key = data['api_key']
            my_addon.setSetting('api_key', new_api_key)
            return True
        except:
            return False
    else:
        return False

def INDEX(url):
    if my_addon.getSetting('api_key'):
        API_KEY = my_addon.getSetting('api_key')

    if url == 'search':
        keyboard = xbmc.Keyboard("", 'Search', False)
        keyboard.doModal()
        if keyboard.isConfirmed():
            query = keyboard.getText().replace(' ', '%20')
            url = API_PATH + '/search/?api_key=' + API_KEY + '&resources=video&query=' + query + '&format=json'
            VIDEOLINKS(url, 'search')

    elif url == 'link':
        dialog = xbmcgui.Dialog()
        ok = dialog.ok("Let's do this.", "To link your account, visit", "www.animevice.com/xbmc to get a link code.", "Enter this code on the next screen.")

        keyboard = xbmc.Keyboard("", 'Enter your link code.', False)
        keyboard.doModal()
        if keyboard.isConfirmed():
            link_code = keyboard.getText().upper()
            if GET_API_KEY(link_code):
                ok = dialog.ok("Success!", "Your account is now linked!", "If you are a premium member,", "you should now have premium privileges.")
            else:
                ok = dialog.ok("We're really sorry, but...", "We could not link your account.", "Make sure the code you entered is correct", "and try again.")
            CATEGORIES()

def VIDEOLINKS(url, name):
    if my_addon.getSetting('api_key'):
        API_KEY = my_addon.getSetting('api_key')

    q_setting = int(my_addon.getSetting('quality'))
    quality = None
    if q_setting == 1:
        quality = 'low_url'
    elif q_setting == 2:
        quality = 'high_url'

    response = urllib2.urlopen(url)
    video_data = simplejson.loads(response.read())['results']
    response.close()

    for vid in video_data:
        name = vid['name']
        if not quality:
            if 'hd_url' in vid:
                url = vid['hd_url'] + '&api_key=' + API_KEY
            else:
                url = vid['high_url']
        else:
            url = vid[quality]
        thumbnail = vid['image']['super_url']
        addLink(name,url,thumbnail)

def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]

    return param

def addLink(name, url, iconimage):
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    liz.setProperty("fanart_image", my_addon.getAddonInfo('path') + "/fanart.jpg")
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
    return ok

def addDir(name, url, mode, iconimage):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    liz.setProperty("fanart_image", my_addon.getAddonInfo('path') + "/fanart.jpg")
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    return ok

params=get_params()
url=None
name=None
mode=None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None or url==None or len(url)<1:
    print ""
    CATEGORIES()

elif mode==1:
    print ""+url
    INDEX(url)

elif mode==2:
    print ""+url
    VIDEOLINKS(url,name)

xbmcplugin.endOfDirectory(int(sys.argv[1]))

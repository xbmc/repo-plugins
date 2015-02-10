import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import threading
import urllib
import urllib2
from urlparse import urlparse
from BeautifulSoup import BeautifulStoneSoup

# plugin constants
plugin_handle = int(sys.argv[1])
plugin_id = 'plugin.video.radbox'
plugin_settings = xbmcaddon.Addon(id=plugin_id)

#constansts for supported services
SERVICE_YOUTUBE = 'youtube'
SERVICE_VIMEO = 'vimeo'
SERVICE_COLLEGEHUMOR = 'collegehumor'

PATH_BASED_SERVICES = [SERVICE_YOUTUBE, SERVICE_VIMEO]
QUERY_STRING_SERVICES = [SERVICE_COLLEGEHUMOR]
SUPPORTED_SERVICES = []

#constants for Feed urls
FEED_URL_VIDEO = 'http://api.radbox.me/feed/video'
FEED_URL_LISTS = 'http://api.radbox.me/feed/lists'
MARK_VIDEO_URL = 'http://api.radbox.me/watch/mark_video'

def show_error(msg):
    """
    display errors to user
    """
    dialog = xbmcgui.Dialog()
    ok = dialog.ok('Radbox', msg)

def check_addon(addon_id):
    """
    checks whether given addon is installed
    """
    value = False
    try:
        addon = xbmcaddon.Addon(id=addon_id)
        if addon:
            value = True
    except:
        pass

    return value

def manage_settings():
    """
    manages whether to show addon settings to user or not
    """
    youtube = check_addon('plugin.video.youtube')
    vimeo = check_addon('plugin.video.vimeo')
    collegehumor = check_addon('plugin.video.collegehumor')
    
    if not youtube:
        plugin_settings.setSetting("youtube", str(youtube).lower())
    
    if not vimeo:
        plugin_settings.setSetting("vimeo", str(vimeo).lower())
    
    if not collegehumor:
        plugin_settings.setSetting("collegehumor", str(collegehumor).lower())
    
    # set version setting, useful if settings are changed in future versions
    # set currVersion incase there are no changes in settings
    currVersion = plugin_settings.getSetting("currVersion") 
    addonVersion = plugin_settings.getAddonInfo('version')
    if ( not currVersion or currVersion < addonVersion):
        plugin_settings.openSettings()
        plugin_settings.setSetting("currVersion", addonVersion)
    return

def get_params(param_str):
    """
    converts the parameter string passed to plugin into dict
    """
    if not param_str or str(param_str).strip() == '':
        return {}

    params = {}
    try:
        #try iterative way (assertive way not no work in python 2.4)
        param_list = param_str.lstrip('?').split('&')
        for param in param_list:
            k,v = param.split('=')
            params[urllib.unquote_plus(k)] = urllib.unquote_plus(v)
    except Exception, e:
        #print 'get_params - ', e
        pass

    return params

def update_supported_services():
    """
    updates supported services depending upon addon settings
    """
    global SUPPORTED_SERVICES
   
    if (plugin_settings.getSetting("youtube") == 'true'):
        SUPPORTED_SERVICES.append(SERVICE_YOUTUBE)

    if (plugin_settings.getSetting("vimeo") == 'true'):
        SUPPORTED_SERVICES.append(SERVICE_VIMEO)

    if (plugin_settings.getSetting("collegehumor") == 'true'):
        SUPPORTED_SERVICES.append(SERVICE_COLLEGEHUMOR)
    
    return

def get_list_item(title='', thumbnail='', plot='', url='', is_folder=False, is_video=False, vid=-1):
    """
    creates a new listitem
    """
    icon_image="DefaultFolder.png"
    if is_video:
        icon_imgae = "DefaultVideo.png"
        #params = {'action': 'play_video', 'vid': vid, 'vidurl' : url}
        liurl =  url
    else:
        params = {'action': 'play_list', 'plist': title}
        liurl =  sys.argv[0] + '?' + urllib.urlencode(params)

    try:
        listitem = xbmcgui.ListItem(label=title, iconImage=icon_image, thumbnailImage=thumbnail)
        listitem.setInfo(type="video", infoLabels={'Title': title, 'Plot': plot})
        if not is_folder:
            listitem.setProperty("IsPlayable", "true")

        return (listitem, liurl)
    except Exception, e:
        #print 'add item - error %s' %e
        pass

def add_item(title='', thumbnail='', plot='', url='', is_folder=False, is_video=False, vid=-1):
    """
    adds a new list item to xbmc virtual directory
    """
    listitem, liurl = get_list_item(title=title, thumbnail=thumbnail, plot=plot, url=url
                                    ,is_folder=is_folder, is_video=is_video, vid=vid) or (None, '')

    if listitem:
        xbmcplugin.addDirectoryItem(handle=plugin_handle, listitem=listitem, url=liurl, isFolder=is_folder)
    
    return

def fetch_feed(uid, lists=False, listname='home'):
    """
    fetches user feeds based on quick url as user identifier
    feed url is of format http://radbox.me/feed/video?uid=%s' %uid 
    """
    if not uid:
        show_error(plugin_settings.getLocalizedString(33001))
        return

    try:
        feed_params = dict(uid=uid)
        if lists:
            feed_url = FEED_URL_LISTS
        else:
            feed_url = FEED_URL_VIDEO
            feed_params.update({'l': listname})
        
        feed_url += '?' + urllib.urlencode(feed_params)
        feeds = urllib2.urlopen(feed_url).read()
        feeds = BeautifulStoneSoup(feeds)
        
        if not feeds:
            show_error(plugin_settings.getLocalizedString(33002))
            return
        
        # check whether there was any error returned from feeds
        errors = feeds.findAll('error')
        if len(errors) > 0:
            try:
                show_error(errors[0].contents[0])
            except Exception, err:
                #print err
                pass
            return

        return feeds
    except:
        xbmc.log("Unable to fetch feed - %s" %feed_url)

def get_playable_data(url):
    """
    checks whether video can be played in xbmc and returns plugin url to invoke service plugin to play video
    returns a dict
        url - playable xbmc url
        can_play - does our plugin support this url yet?
    """
    if not url:
        return

    url_parts = urlparse(url)
    #xbmc uses python 2.4 which returns url parts as tuple (scheme, netloc, path, params, query, fragment)
    try:
        if isinstance(url_parts, type(())):
            netloc = url_parts[1]
        else:
            netloc = url_parts.netloc
        service = netloc.split('.')[-2].lower()
    except Exception,e:
        # unable to find service, return from here
        #print e
        return
    
    if not service in SUPPORTED_SERVICES:
        # video is not in supported services
        return

    can_play = False
    # for youtube and vimeo we get video id from url path component and as last element
    if service in PATH_BASED_SERVICES:
        if isinstance(url_parts, type(())):
            path = url_parts[2]
        else:
            path = str(url_parts.path).strip()
        
        if path and str(path).strip() != '':
            #look for last '/' /<video_key> in path
            video_id = path.split('/')[-1]
            if video_id and video_id.strip() != '': 
                can_play = True
                if service == SERVICE_YOUTUBE:
                    url = "plugin://plugin.video.youtube/?action=play_video&videoid=%s" %video_id
                elif service == SERVICE_VIMEO:
                    url = "plugin://plugin.video.vimeo/?action=play_video&videoid=%s" %video_id

    elif service in QUERY_STRING_SERVICES:
        # for collegehumor we get video id from query string component as clip_id
        if isinstance(url_parts, type(())):
            qs = url_parts[4]
        else:
            qs = str(url_parts.qs).strip()
        
        if qs and str(qs).strip() != '':
            # python 2.4 urlparse does not have parse_qs api, cgi.parse_qs is deprecated in later release
            params = dict([s.split('=') for s in qs.split('&') if s.strip() != ''])
            
            if service == SERVICE_COLLEGEHUMOR:
                video_id = params['clip_id']
                if video_id and video_id.strip() != '': 
                    try:
                        #for plugin to work, we need complete url, else page redirects to itself resulting in a loop
                        page = urllib2.urlopen('http://collegehumor.com/video/%s' %video_id)
                        full_url = page.geturl()
                        # extract video url from urlparse
                        full_url_parts = urlparse(full_url)
                        if isinstance(full_url_parts, type(())):
                            video_url = full_url_parts[2][1:]
                        else:
                            video_url = str(full_url_parts.path)[1:]
                        url = "plugin://plugin.video.collegehumor/watch/%s/" %urllib.quote_plus(video_url)
                        can_play = True
                    except:
                        pass
                # creating own dict for now
    return dict(can_play=can_play, url=url)

def mark_video(uid, vid):
    """
    marks video as opened
    """
    if not uid or not vid:
        return

    url = MARK_VIDEO_URL
    params = {'vid': vid, 'uid': uid}
    url += '?' + urllib.urlencode(params)
    urllib2.urlopen(url)
    return

def play_video(uid, vid, url):
    """
    plays a video
    """
    #mark video in a separate thread
    #threading.Thread(target=mark_video, args=(uid, vid)).start()
    
    mark_video(uid, vid)
    xbmc.executebuiltin("xbmc.PlayMedia("+url+")")
    return

def play_list(uid, listname=''):
    """
    displays videos contained in playlist
    """
    autoplay = (plugin_settings.getSetting("autoplay") == 'true')
    update_supported_services()

    if not listname or str(listname).strip() == '':
        return

    feeds = fetch_feed(uid, listname=listname)
    
    #create a new playlist only for autoplay setting
    if autoplay:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
    
    try:
        items = feeds.findAll('item')
        for item in items:
            try:
                can_play = False
                try:
                    title = item.title.contents[0]
                except:
                    title = ""

                try:
                    description = item.description.contents[0]
                except:
                    description = ""

                try:
                    url = item.find('media:content')['url']
                    playable_data = get_playable_data(url)
                    #print playable_data
                    if playable_data:
                        url = playable_data['url']
                        can_play = playable_data['can_play']
                except:
                    url = None
                    can_play = False

                try:
                    thumbnail = item.find('media:thumbnail')['url']
                except:
                    thumbnail = "DefaultFolder.png"

                try:
                    vid = (item.find('guid').contents[0]).split('/')[-1]
                except:
                    vid = -1

                if can_play:
                    if autoplay:
                        listitem, liurl = get_list_item(title=title, thumbnail=thumbnail, plot=description, url=url, is_video=True, vid=vid) or (None, '')
                        if listitem:
                            playlist.add(url=liurl, listitem=listitem)
                    else:
                        add_item(title=title, thumbnail=thumbnail, plot=description, url=url, is_video=True, vid=vid)

            except Exception, err:
                #print err
                pass
    
        # for autoplay, we will not display directory listing.
        if not autoplay:
            # we are done adding items to directory 
            xbmcplugin.endOfDirectory(handle = plugin_handle)
        else:
            # start playing
            if playlist.size() > 0:
                # try using player
                # seems like there is a bug in xbmc 10 - on using player for playlist of plugin urls xbmc hangs
                # playlist works fine with player in Eden beta
                # http://forum.xbmc.org/showthread.php?p=973023
                #xbmc.Player().play(item=playlist)
                
                #start playing
                xbmc.executebuiltin('playlist.playoffset(video , 0)')
                
    except Exception, e:
        #print 'play_list error - %s' %e
        pass
    
def playlists(uid):
    """
    fetches and displays users playlist
    """
    feed = fetch_feed(uid, lists=True)

    #iterate over each item in feed and create a list item
    try:
        items = feed.findAll("item")
        for item in items:
            try:
                title = item.find('name').contents[0]
                add_item(title=title, is_folder=True)
            except Exception, e:
                #print e
                pass
    except:
        pass

def home(uid):
    """
    this api is called when plugin is launched first.
    """
    if not uid:
        show_error(plugin_settings.getLocalizedString(33001))
        return
    
    playlists(uid)

    # we are done adding items to directory 
    xbmcplugin.endOfDirectory(handle = plugin_handle)

if (__name__ == "__main__"):

    uid = plugin_settings.getSetting("uid")
    manage_settings()
    if (not sys.argv[2]):
        home(uid)
    else:
        # initiate params dict with default values, update it with params received from request
        # this will make sure KeyError is not raised
        params = {'action': None, 'plist': None, 'vidurl': None, 'vid': None}
        params.update(get_params(sys.argv[2]))
        
        action = params['action']
        if action == 'play_list':
            play_list(uid, listname=params['plist'])
        elif action == 'play_video':
            play_video(uid, url=params['vidurl'], vid=params['vid'])
        else:
            home(uid)

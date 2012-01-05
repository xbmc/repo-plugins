import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import urllib
import urllib2
from urlparse import urlparse
from BeautifulSoup import BeautifulStoneSoup

# plugin constants
plugin_handle = int(sys.argv[1])
plugin_id = 'plugin.video.radbox.me'
plugin_settings = xbmcaddon.Addon(id=plugin_id)

#constansts for supported services
SERVICE_YOUTUBE = 'youtube'
SERVICE_VIMEO = 'vimeo'
SERVICE_COLLEGEHUMOR = 'collegehumor'

PATH_BASED_SERVICES = [SERVICE_YOUTUBE, SERVICE_VIMEO]
QUERY_STRING_SERVICES = [SERVICE_COLLEGEHUMOR]
SUPPORTED_SERVICES = [SERVICE_YOUTUBE, SERVICE_VIMEO, SERVICE_COLLEGEHUMOR]

def show_error(msg):
    """
    display errors to user
    """
    dialog = xbmcgui.Dialog()
    ok = dialog.ok('Radbox', msg)

def fetch_feed(uid):
    """
    fetches user feeds based on quick url as user identifier
    feed url is of format http://radbox.me/feed/video?uid=%s' %uid 
    """
    if not uid:
        show_error('Invalid value for user id.')
        return
    try:
        feed_url = 'http://radbox.me/feed/video?uid=%s' %uid
        feeds = urllib2.urlopen(feed_url).read()
        return BeautifulStoneSoup(feeds)
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

def play_user_feed(uid):
    """
    fetches feed from user's radbox account, creates a playlist of all playable videos and starts playing
    """
    if not uid:
        show_error('Invalid value for user id.')
        return

    feeds = fetch_feed(uid)

    if not feeds:
        show_error('Unable to fetch feeds.')
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

    # We have valid feed

    #create a new playlist,
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()

    #fetch all feed items
    items = feeds.findAll("item")
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
                if playable_data:
                    url = playable_data['url']
                    can_play = playable_data['can_play']
            except:
                url = None
                can_play = False

            try:
                thumbnail = item.find('media:thumbnail')['url']
            except:
                thumbnail = ""
            
            if can_play:
                listitem = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail)
                listitem.setInfo(type="video", infoLabels={"Title" : title, "Plot" : description})
                playlist.add(url=url, listitem=listitem)
        except Exception, err:
            #print err
            pass

    if playlist.size() > 0:
        # try using player
        # seems like there is a bug in xbmc 10 - on using player for playlist of plugin urls xbmc hangs
        # playlist works fine with player in Eden beta
        # http://forum.xbmc.org/showthread.php?p=973023
        #xbmc.Player().play(item=playlist)
        
        #start playing
        xbmc.executebuiltin('playlist.playoffset(video , 0)')

    return
            
if (__name__ == "__main__"):
    if ( not plugin_settings.getSetting("firstrun")):
        plugin_settings.openSettings()
        plugin_settings.setSetting("firstrun", '1')
    if (not sys.argv[2]):
        uid = plugin_settings.getSetting("uid")
        play_user_feed(uid)

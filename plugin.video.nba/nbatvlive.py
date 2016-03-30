import urllib,urllib2
import xbmc,xbmcplugin,xbmcgui,xbmcaddon
from xml.dom.minidom import parseString
import re

from common import *
from utils import *
import vars

def playLiveTV():
    if not vars.cookies:
        login()
    if not vars.cookies:
        return

    failsafe = True;

    url = 'http://watch.nba.com/nba/servlets/publishpoint'
    headers = { 
        'Cookie': vars.cookies, 
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'iPad' if failsafe 
            else "Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0",
    }
    body = {
        'id': "0", 
        'type': 'channel',
        'plid': vars.player_id,
    }
    if not failsafe:
        body['isFlex'] = 'true'
    else:
        body['nt'] = '1'
    body = urllib.urlencode(body)

    log("nba tv live: the body of publishpoint request is: %s" % body, xbmc.LOGDEBUG)

    try:
        request = urllib2.Request(url, body, headers)
        response = urllib2.urlopen(request)
        content = response.read()
    except urllib2.HTTPError as e:
        log("nba live tv: failed getting url: %s %s" % (url, e.read()), xbmc.LOGDEBUG)
        littleErrorPopup( xbmcaddon.Addon().getLocalizedString(50020) )
        return

    # Get the adaptive video url
    xml = parseString(str(content))
    video_temp_url = xml.getElementsByTagName("path")[0].childNodes[0].nodeValue
    log("nba live tv: temp video url is %s" % video_temp_url, xbmc.LOGDEBUG)

    video_url = ""
    if failsafe:
        # transform the link
        match = re.search('http://([^:]+)/([^?]+?)\?(.+)$', video_temp_url)
        domain = match.group(1)
        arguments = match.group(2)
        querystring = match.group(3)

        livecookies = "nlqptid=%s" % (querystring)
        livecookiesencoded = urllib.quote(livecookies)
        log("live cookie: %s %s" % (querystring, livecookies), xbmc.LOGDEBUG)

        video_url = "http://%s/%s?%s|Cookie=%s" % (domain, arguments, querystring, livecookiesencoded)
    else:
        # Transform the link from adaptive://domain/url?querystring to
        # http://domain/play?url=url&querystring
        match = re.search('adaptive://([^/]+)(/[^?]+)\?(.+)$', video_adaptive_url)
        domain = match.group(1)
        path = urllib.quote_plus(str(match.group(2)))
        querystring = match.group(3)
        video_play_url = "http://%s/play?url=%s&%s" % (domain, path, querystring)
        log("nba live tv: play url is %s" % video_play_url, xbmc.LOGDEBUG)

        # Get the video play url (which will return different urls for
        # different bitrates)
        try:
            request = urllib2.Request(video_play_url, None, {'Cookie': vars.cookies})
            response = urllib2.urlopen(request)
            content = response.read()
        except urllib2.HTTPError as e:
            log("nba live tv: failed getting url: %s %s" % (video_play_url, e.read()))
            littleErrorPopup( xbmcaddon.Addon().getLocalizedString(50023) )
            return

        if not content:
            log("nba live tv: empty response from video play url")
            littleErrorPopup('Failed to get a video URL (response was empty)')
            return
        else:
            log("nba live tv: parsing response: %s" % content, xbmc.LOGDEBUG)

            # Parse the xml to find different bitrates
            xml = parseString(str(content))
            streamdata_list = xml.getElementsByTagName("streamData")
            video_url = ''
            for streamdata in streamdata_list:
                video_height = streamdata.getElementsByTagName("video")[0].attributes["height"].value

                if int(video_height) == vars.target_video_height:
                    selected_video_path = streamdata.attributes["url"].value
                    http_servers = streamdata.getElementsByTagName("httpserver")

                    for http_server in http_servers:
                        server_name = http_server.attributes["name"].value
                        server_port = http_server.attributes["port"].value

                        # Construct the video url directly in m3u8
                        m3u8_video_url = "http://%s:%s%s.m3u8" % (server_name, server_port, selected_video_path)
                        
                        # Test if the video is actually available. If it is not available go to the next server.
                        if urllib.urlopen(m3u8_video_url).getcode() == 200:
                            video_url = m3u8_video_url

                            # Get the cookies from the xml tag <encryption>
                            video_cookies = streamdata.getElementsByTagName("encryption")[0].attributes['token'].value
                            video_cookies = video_cookies.replace(';', '; ')
                            video_cookies_encoded = urllib.quote(video_cookies)
                            log("nba live tv: live cookie: %s" % video_cookies, xbmc.LOGDEBUG)
                            break

                        log("no working url found for this server, moving to the next", xbmc.LOGDEBUG)

                    # break from the video quality loop
                    break

        # Add the cookies in the format "videourl|Cookie=[cookies]""
        video_url = "%s?%s|Cookie=%s" % (video_url, querystring, video_cookies_encoded)

    item = xbmcgui.ListItem("NBA TV Live", path=video_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

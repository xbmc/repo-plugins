import json
import datetime
import urllib,urllib2
import xbmc,xbmcaddon
import re
from xml.dom.minidom import parseString

import vars
from utils import *

def updateFavTeam():
    vars.fav_team = None

    settings = xbmcaddon.Addon( id=vars.__addon_id__)
    fav_team_name = settings.getSetting( id="fav_team")
    if fav_team_name:
        for abbr, name in vars.config['teams'].items():
            if fav_team_name == name:
                vars.fav_team = abbr
                xbmc.log(msg="fav_team set to %s" % (vars.fav_team), level=xbmc.LOGWARNING)

def getGameUrlWithBitrate(url, video_type):
    # Force the bitrate by modifying the HLS url and adding the bitrate
    available_bitrates = [
        (72060, 6000),
        (720, 3000),
        (540, 1600),
        (432, 1200),
        (360, 800),
    ]

    #"video" video_type starts from 3000k as bitrate
    if video_type == "video":
        available_bitrates.pop(0)

    #Get the chosen bitrate, and all the bitrates after that one
    target_bitrates = [item[1] for item in available_bitrates if item[0] <= vars.target_video_height]
    log('target_bitrates: %s' % target_bitrates, xbmc.LOGDEBUG)

    regex_pattern = 'whole_([0-9])_ipad'
    regex_replacement_format = r'whole_\1_%s_ipad'
    if video_type == "condensed":
        regex_pattern = 'condensed_([0-9])_ipad'
        regex_replacement_format = r'condensed_\1_%s_ipad'
    elif video_type == "live":
        regex_pattern = '([a-z]+)_hd_ipad'
        regex_replacement_format = r'\1_hd_%s_ipad'
    elif video_type == "video":
        regex_pattern = '1_([0-9]+)\.mp4'
        regex_replacement_format = r'1_%s.mp4'

    #Try the target bitrate, and if it doesn't exists, try every bitrate lower than the chosen one
    #(eg: if you chouse 3000k as bitrate, it will try 3000k, then 1600k, then 1200k, 
    #and so on)
    selected_video_url = ""
    for target_bitrate in target_bitrates:
        selected_video_url = re.sub(regex_pattern, regex_replacement_format % target_bitrate, url)

        #The "video" url is rtmp:// so i can't test it with urlopen().getcode(),
        #so break on first iteration of the loop
        if video_type == "video":
            break

        #If video is found, break
        if urllib.urlopen(selected_video_url).getcode() == 200:
            break

        log("video of bitrate %d not found, trying with next height" % target_bitrate, xbmc.LOGDEBUG)

    return "%s|User-Agent=%s" % (selected_video_url, vars.useragent)

def getFanartImage():
    # get the feed url
    feed_url = "http://smb.cdnak.neulion.com/fs/nba/feeds/common/dl.js"
    req = urllib2.Request(feed_url, None);
    response = str(urllib2.urlopen(req).read())
    
    try:
        # Parse
        js = json.loads(response[response.find("{"):])
        dl = js["dl"]

        # for now only chose the first fanart
        first_id = dl[0]["id"]
        fanart_image = ("http://smb.cdnllnwnl.neulion.com/u/nba/nba/thumbs/dl/%s_pc.jpg" % first_id)
        vars.settings.setSetting("fanart_image", fanart_image)
    except:
        #I don't care
        pass

def getDate( default= '', heading='Please enter date (YYYY/MM/DD)', hidden=False ):
    now = datetime.datetime.now()
    default = "%04d" % now.year + '/' + "%02d" % now.month + '/' + "%02d" % now.day
    keyboard = xbmc.Keyboard( default, heading, hidden )
    keyboard.doModal()
    ret = datetime.date.today()
    if ( keyboard.isConfirmed() ):
        sDate = unicode( keyboard.getText(), "utf-8" )
        temp = sDate.split("/")
        ret = datetime.date(int(temp[0]),  int(temp[1]), int(temp[2]))
    return ret

def login():
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    try:
        body = urllib.urlencode({
            'username': vars.settings.getSetting( id="username"), 
            'password': vars.settings.getSetting( id="password")
        })

        request = urllib2.Request(vars.config['login_endpoint'], body, headers)
        response = urllib2.urlopen(request)
        content = response.read()
    except urllib2.HTTPError as e:
        log("Login failed with code: %d and content: %s" % (e.getcode(), e.read()))
        littleErrorPopup( xbmcaddon.Addon().getLocalizedString(50022) )
        return ''

    # Check the response xml
    xml = parseString(str(content))
    if xml.getElementsByTagName("code")[0].firstChild.nodeValue == "loginlocked":
        littleErrorPopup( xbmcaddon.Addon().getLocalizedString(50021) )
        return ''
    else:
        # logged in
        vars.cookies = response.info().getheader('Set-Cookie').partition(';')[0]

    """try:
        body = urllib.urlencode({
            'format': 'json'
        })

        request = urllib2.Request('https://watch.nba.com/account/subscriptions?', body, headers)
        subscriptions = urllib2.urlopen(request).read()
    except urllib2.HTTPError as e:
        log("Login failed with code: %d and content: %s" % (e.getcode(), e.read()))
        littleErrorPopup( xbmcaddon.Addon().getLocalizedString(50022) )
        return ''

    subscription_json = json.loads(subscriptions)
    log("Subscription json: %s" % (subscription_json), xbmc.LOGNOTICE)
    if subscription_json['code'] != "noaccess":
        subscription_sku = subscription_json["subs"][0]["sku"]
        log("Subscription sku: %s" % (subscription_sku), xbmc.LOGNOTICE)
        if subscription_sku == "LPP2015":
            vars.subscriptions = ["season", "playoffs", "nbatvlive"]"""

    return vars.cookies

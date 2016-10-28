import json
import datetime, time
from datetime import timedelta
import urllib,urllib2
import xbmc,xbmcplugin,xbmcgui,xbmcaddon
from xml.dom.minidom import parseString
import re

from utils import *
from common import *
import vars

def videoDateMenu():
    video_tag = vars.params.get("video_tag")
    
    dates = []
    current_date = datetime.date.today() - timedelta(days=1)
    last_date = current_date - timedelta(days=7)
    while current_date - timedelta(days=1) > last_date:
        dates.append(current_date)
        current_date = current_date - timedelta(days=1)

    for date in dates:
        params = {'date': date, 'video_tag': video_tag}
        addListItem(name=str(date), url='', mode='videolist', iconimage='', 
            isfolder=True, customparams=params)
    xbmcplugin.endOfDirectory(handle = int(sys.argv[1]))

def videoMenu():
    addListItem('Top Plays', '', 'videodate', '', True, customparams={'video_tag':'top_plays'})
    addListItem('Shaqtin\' a fool', '', 'videolist', '', True, customparams={
        'video_tag': 'shaqtin', 
        'video_query': "shaqtin",
        'pagination': True
    })
    addListItem('The starters', '', 'videolist', '', True, customparams={
        'video_tag': 'starters', 
        'video_query': "starters",
        'pagination': True
    })
    addListItem('Highlights', '', 'videolist', '', True, customparams={
        'video_tag': 'recap', 
        'pagination': True
    })
    addListItem('Smitty\'s top plays under the rim', '', 'videolist', '', True, customparams={
        'video_query': 'smitty -gametime -inside',
        'pagination': True
    })

def videoListMenu():
    date = vars.params.get("date");
    video_tag = vars.params.get("video_tag")
    video_query = vars.params.get("video_query")
    page = int(vars.params.get("page", 0))
    per_page = 20

    if video_query:
        video_query = urllib.unquote_plus(video_query)

    log("videoListMenu: date requested is %s, tag is %s, query is %s, page is %d" % (date, video_tag, video_query, page), xbmc.LOGDEBUG)

    if date:
        selected_date = None
        try:
            selected_date = datetime.datetime.strptime(date, "%Y-%m-%d" )
        except:
            selected_date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(date, "%Y-%m-%d")))

    query = []
    if video_tag:
        query.append("tags:%s" % video_tag)
    if video_query:
        query.append("(%s)" % video_query)
    query = " OR ".join(query)

    #Add the date if passed from the menu
    if date:
        query += " AND releaseDate:[%s TO %s]" % (
            selected_date.strftime('%Y-%m-%dT00:00:00.000Z'), 
            selected_date.strftime('%Y-%m-%dT23:59:59.000Z')
        )

    base_url = "http://smbsolr.cdnak.neulion.com/solr_nbav6/nba/nba/usersearch/?"
    params = urllib.urlencode({
        "wt": "json",
        "json.wrf": "updateVideoBoxCallback",
        "q": query,
        "sort": "releaseDate desc",
        "start": page * per_page,
        "rows": per_page
    })

    url = base_url + params;
    log("videoListMenu: %s: url of date is %s" % (video_tag, url), xbmc.LOGDEBUG)

    response = urllib2.urlopen(url).read()
    response = response[response.find("{"):response.rfind("}")+1]
    log("videoListMenu: response: %s" % response, xbmc.LOGDEBUG)

    jsonresponse = json.loads(response)

    for video in jsonresponse['response']['docs']:
        name = video['name']

        #Parse release date - nba uses different formats :facepalm:
        date_formats = ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"]
        try:
            for date_format in date_formats:
                try:
                    release_date = datetime.datetime.strptime(video['releaseDate'], date_format)
                except ValueError:
                    pass
        except:
            for date_format in date_formats:
                try:
                    release_date = datetime.datetime.fromtimestamp(
                        time.mktime(time.strptime(video['releaseDate'], date_format)))
                except ValueError:
                    pass

        release_date = release_date.strftime('%d/%m/%Y')

        #Runtime formatting
        minutes, seconds = divmod(video['runtime'], 60)
        hours, minutes = divmod(minutes, 60)
        runtime = "%02d:%02d" % (minutes, seconds)

        if not date:
            if video['runtime']:
                name = "%s (%s) - %s" % (name, runtime, release_date)
            else:
                name = "%s - %s" % (name, release_date)
        else:
            name = "%s (%s)" % (name, runtime)

        addListItem(url=str(video['sequence']), name=name, mode='videoplay', iconimage='')

    if vars.params.get("pagination"):
        next_page_name = xbmcaddon.Addon().getLocalizedString(50008)

        #Add "next page" link
        custom_params={
            'video_tag': video_tag, 
            'video_query': video_query,
            'page': page + 1,
            'pagination': True
        }
        if date:
            custom_params['date'] = date

        addListItem(next_page_name, '', 'videolist', '', True, customparams=custom_params)

    xbmcplugin.endOfDirectory(handle = int(sys.argv[1]))

def videoPlay():
    video_id = vars.params.get("url")

    url = 'https://watch.nba.com/service/publishpoint'
    headers = { 
        'Cookie': vars.cookies, 
        'Content-type': 'application/x-www-form-urlencoded',
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0",
    }
    body = urllib.urlencode({
        'id': str(video_id), 
        'bitrate': 800,
        'type': 'video',
        'plid': vars.player_id,
        'isFlex:': 'true',
    })

    try:
        request = urllib2.Request(url, headers=headers)
        response = urllib2.urlopen(request, body)
        content = response.read()
    except urllib2.HTTPError as e:
        logHttpException(e, url, body)
        littleErrorPopup("Failed to get video url. Please check log for details")
        return ''

    xml = parseString(str(content))
    video_url = xml.getElementsByTagName("path")[0].childNodes[0].nodeValue
    video_url = getGameUrlWithBitrate(video_url, "video")
    log("videoPlay: video url is %s" % video_url, xbmc.LOGDEBUG)

    #remove query string
    video_url = re.sub("\?[^?]+$", "", video_url)

    item = xbmcgui.ListItem(path=video_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

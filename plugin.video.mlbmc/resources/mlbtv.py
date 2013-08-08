import os
import re
import sys
import cookielib
import urllib
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import StorageServer
from mlb_common import TeamCodes, addon_log, coloring, getRequest
from BeautifulSoup import BeautifulStoneSoup, BeautifulSoup

addon = xbmcaddon.Addon(id='plugin.video.mlbmc')
profile = xbmc.translatePath(addon.getAddonInfo('profile'))
home = xbmc.translatePath(addon.getAddonInfo('path'))
language = addon.getLocalizedString
icon = os.path.join(home, 'icon.png')
cookie_file = os.path.join(profile, 'cookie_file')
cookie_jar = cookielib.LWPCookieJar(cookie_file)
cache = StorageServer.StorageServer("mlbmc", 2)
debug = addon.getSetting('debug')
if debug == 'true':
    cache.dbg = True
fanart1 = 'http://mlbmc-xbmc.googlecode.com/svn/icons/fanart1.jpg'

SOAPCODES = {
    "1"    : "OK",
    "-1000": "Requested Media Not Found",
    "-1500": "Other Undocumented Error",
    "-2000": "Authentication Error",
    "-2500": "Blackout Error",
    "-3000": "Identity Error",
    "-3500": "Sign-on Restriction Error",
    "-4000": "System Error",
    }


def mlb_login():
    addon_log('Login to get cookies!')
    # Get the cookie first
    url = 'https://secure.mlb.com/enterworkflow.do?flowId=registration.wizard&c_id=mlb'
    headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:19.0) Gecko/20100101 Firefox/19.0'}
    login = getRequest(url,None,headers)

    # now authenticate
    url = 'https://secure.mlb.com/authenticate.do'
    headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:19.0) Gecko/20100101 Firefox/19.0',
               'Referer' : 'https://secure.mlb.com/enterworkflow.do?flowId=registration.wizard&c_id=mlb'}
    values = {'uri' : '/account/login_register.jsp',
              'registrationAction' : 'identify',
              'emailAddress' : addon.getSetting('email'),
              'password' : addon.getSetting('password')}
    login = getRequest(url,urllib.urlencode(values),headers)
    cookie_jar.load(cookie_file, ignore_discard=False, ignore_expires=False)
    cookies = {}
    addon_log('These are the cookies we have received from authenticate.do:')
    for i in cookie_jar:
        cookies[i.name] = i.value
        addon_log('%s: %s' %(i.name, i.value))

    pattern = re.compile(r'Welcome to your personal (MLB|mlb).com account.')
    try:
        loggedin = re.search(pattern, login).groups()
        addon_log( "Logged in successfully!" )
    except:
        addon_log("Login Failed!")
        try:
            soup = BeautifulSoup(login)
            addon_log(str(soup.head.title))
        except: pass
        xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30042)+",5000,"+icon+")")

    if cookies.has_key('ipid') and cookies.has_key('fprt'):
        return True
    else:
        return False


def mlbGame(event_id, full_count=False):
    if not full_count:
        # Check if cookies have expired.
        cookie_jar.load(cookie_file, ignore_discard=True, ignore_expires=False)
        cookies = {}
        addon_log('These are the cookies we have in the cookie file:')
        for i in cookie_jar:
            cookies[i.name] = i.value
            addon_log('%s: %s' %(i.name, i.value))
        if cookies.has_key('ipid') and cookies.has_key('fprt'):
            addon_log('We have valid cookies')
            login = 'old'
        else:
            login = mlb_login()

        if not login:
            addon_log( "Seems to ba a cookie problem" )
            xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30043)+",10000,"+icon+")")
            return

        if login == 'old':
            # lets see if we get new cookies
            addon_log('old cookies: ipid - %s , fprt - %s' %(cookies['ipid'], cookies['fprt']))
            url = 'http://mlb.mlb.com/enterworkflow.do?flowId=media.media'
            data = getRequest(url,None,None)
            addon_log('These are the cookies we have after enterworkflow.do?flowId=media.media:')

        cookie_jar.load(cookie_file, ignore_discard=True, ignore_expires=True)
        cookies = {}
        for i in cookie_jar:
            cookies[i.name] = i.value
            addon_log('%s: %s' %(i.name, i.value))
        session = None
        if cookies.has_key('ftmu'):
            addon_log("cookies.has_key('ftmu')")
            session = urllib.unquote(cookies['ftmu'])
        
        values = {
            'eventId': event_id,
            'sessionKey': session,
            'fingerprint': urllib.unquote(cookies['fprt']),
            'identityPointId': cookies['ipid'],
            'subject':'LIVE_EVENT_COVERAGE',
            'platform':'WEB_MEDIAPLAYER'
            }
    else:
        values = {
            'platform':'WEB_MEDIAPLAYER',
            'eventId':event_id,
            'subject':'MLB_FULLCOUNT'
            }
    url = 'https://mlb-ws.mlb.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.3?'
    headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:19.0) Gecko/20100101 Firefox/19.0',
               'Referer' : 'http://mlb.mlb.com/shared/flash/mediaplayer/v4.3/R1/MediaPlayer4.swf?v=14'}
    data = getRequest(url,urllib.urlencode(values),headers)
    if debug == "true":
        addon_log(data)
    soup = BeautifulStoneSoup(data)
    status = soup.find('status-code').string
    if status != "1":
        try:
            error_str = SOAPCODES[status]
        except:
            error_str = 'Unknown Error'
        addon_log(error_str)
        if not full_count:
            if login == 'old':
                cookie_jar.clear()
                login = mlb_login()
            if not login:
                xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30044)+error_str+",10000,"+icon+")")
                return
            else:
                cookie_jar.load(cookie_file, ignore_discard=True, ignore_expires=True)
                cookies = {}
                for i in cookie_jar:
                    cookies[i.name] = i.value
                    addon_log('%s: %s' %(i.name, i.value))
                session = None
                if cookies.has_key('ftmu'):
                    addon_log("cookies.has_key('ftmu')")
                    session = urllib.unquote(cookies['ftmu'])

                values = {
                    'eventId': event_id,
                    'sessionKey': session,
                    'fingerprint': urllib.unquote(cookies['fprt']),
                    'identityPointId': cookies['ipid'],
                    'subject':'LIVE_EVENT_COVERAGE',
                    'platform':'WEB_MEDIAPLAYER'
                    }
                data = getRequest(url,urllib.urlencode(values),headers)
        else:
            return
    cookie_jar.load(cookie_file, ignore_discard=True, ignore_expires=True)
    cookies = {}
    addon_log('These are the cookies we have after UserVerifiedEvent request 1:')
    for i in cookie_jar:
        cookies[i.name] = i.value
        addon_log('%s: %s' %(i.name, i.value))
    try:
        session_key = soup.find('session-key').string
    except AttributeError:
        session_key = None
    if session_key:
        session = session_key

    event_id = soup.find('event-id').string
    items = soup.findAll('user-verified-content')
    verified_content = {'video': [], 'audio': []}
    for item in items:
        audio = False
        if item.state.string == 'MEDIA_ARCHIVE':
            if int(event_id.split('-')[2]) < 2012:
                scenario = addon.getSetting('archive_scenario')
            else:
                scenario = 'FMS_CLOUD'
            live = False
        else:
            scenario = 'FMS_CLOUD'
            live = True
        content_id = item('content-id')[0].string
        if full_count:
            name = 'full_count'
            session = ''
            return getGameURL(name,event_id,content_id,session,None,None,scenario,True)
        else:
            blackout_status = item('blackout-status')[0]
            try:
                blackout = item('blackout')[0].string.replace('_',' ')
            except:
                blackout = language(30031)

            try:
                call_letters = item('domain-attribute', attrs={'name' : "call_letters"})[0].string
            except:
                call_letters = ''

            if item('domain-attribute', attrs={'name' : "home_team_id"})[0].string == item('domain-attribute', attrs={'name' : "coverage_association"})[0].string:
                coverage = TeamCodes[item('domain-attribute', attrs={'name' : "home_team_id"})[0].string][0]+' Coverage'
            elif item('domain-attribute', attrs={'name' : "away_team_id"})[0].string == item('domain-attribute', attrs={'name' : "coverage_association"})[0].string:
                coverage = TeamCodes[item('domain-attribute', attrs={'name' : "away_team_id"})[0].string][0]+' Coverage'
            else:
                coverage = ''

            if 'successstatus' in str(blackout_status):
                name = coverage+' - '+call_letters
            else:
                name = coverage+' '+call_letters+' '+blackout

            if item.type.string == 'audio':
                audio = True
                name += ' Gameday Audio'
                scenario = 'AUDIO_FMS_32K'

            name = name.replace('.','').rstrip(' ')

            if item.state.string == 'MEDIA_OFF':
                addon_log('MEDIA_OFF: %s' %name)
                continue

            else:
                if audio:
                    verified_content['audio'].append((name,event_id,content_id,session,cookies['ipid'],cookies['fprt'],scenario,live))
                else:
                    verified_content['video'].append((name,event_id,content_id,session,cookies['ipid'],cookies['fprt'],scenario,live))

    index = 0
    name_list = []
    sorted_content = {}
    for i in verified_content['video'] + verified_content['audio']:
        sorted_content[index] = i
        name_list.append(i[0])
        index += 1

    dialog = xbmcgui.Dialog()
    ret = dialog.select(language(30033), name_list)
    if ret >= 0:
        addon_log('Selected: %s' %name_list[ret])
        addon_log('content: %s' %sorted_content[ret][0])
        getGameURL(*sorted_content[ret])


def getGameURL(name,event,content,session,cookieIp,cookieFp,scenario,live):
    if name == 'full_count':
        subject = 'MLB_FULLCOUNT'
        url = 'https://mlb-ws.mlb.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.3?'
    else:
        subject = 'LIVE_EVENT_COVERAGE'
        url = 'https://secure.mlb.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.1?'
    
    try:
        cookieFp = urllib.unquote(cookieFp)
    except AttributeError:
        pass
    values = {
        'subject': subject,
        'sessionKey': session,
        'identityPointId': cookieIp,
        'contentId': content,
        'playbackScenario': scenario,
        'eventId': event,
        'fingerprint': cookieFp,
        'platform':'WEB_MEDIAPLAYER'
        }

    data = getRequest(url,urllib.urlencode(values),None)
    if debug == "true":
        addon_log(data)
    soup = BeautifulStoneSoup(data, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
    try:
        new_fprt = soup.find('updated-fingerprint').string
        if len(new_fprt) > 0:
            addon_log('New Fingerprint: %s' %new_fprt)
            new_cookie = cookielib.Cookie(
                version=0, name='fprt', value=new_fprt, port=None, port_specified=False,
                domain='.mlb.com', domain_specified=False, domain_initial_dot=False,
                path='/', path_specified=True, secure=False, expires=None, discard=True,
                comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
            cookie_jar.load(cookie_file, ignore_discard=True, ignore_expires=True)
            cookie_jar.set_cookie(new_cookie)
            cookie_jar.save(cookie_file, ignore_discard=True, ignore_expires=True)
            cookieFp = new_fprt
    except AttributeError:
        addon_log('No New Fingerprint')
        
    status = soup.find('status-code').string
    if status != "1":
        try:
            error_str = SOAPCODES[status]
            xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30044)+error_str+",10000,"+icon+")")
        except:
            addon_log ( 'Unknown status-code: '+status )
            xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30046)+status+",10000,"+icon+")")
        return

    elif soup.find('state').string == 'MEDIA_OFF':
        addon_log( 'Status : Media Off' )
        try:
            preview = soup.find('preview-url').contents[0]
            if re.search('innings-index',str(preview)):
                if debug == "true":
                    addon_log( 'No preview' )
                raise Exception
            else:
                xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30045)+language(30047)+",10000,"+icon+")")
                item = xbmcgui.ListItem(path=preview)
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
        except:
            xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30045)+",5000,"+icon+")")
            return

    elif not 'successstatus' in str(soup.find('blackout-status')):
        addon_log( 'Status : Blackout' )
        try:
            blackout = item('blackout')[0].string.replace('_',' ')
        except:
            blackout = 'Blackout'
        try:
            preview = soup.find('preview-url').contents[0]
            if re.search('innings-index',str(preview)):
                if debug == "true":
                    addon_log( 'No preview' )
                raise Exception
            else:
                xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30044)+blackout+language(30047)+",15000,"+icon+")")
                item = xbmcgui.ListItem(path=preview)
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
        except:
            xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30044)+blackout+language(30047)+",5000,"+icon+")")
            return

    elif 'notauthorizedstatus' in str(soup.find('auth-status')):
        addon_log( 'Status : Not Authorized' )
        try:
            preview = soup.find('preview-url').contents[0]
            if re.search('innings-index',str(preview)):
                if debug == "true":
                    addon_log( 'No preview' )
                raise Exception
            else:
                xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30048)+language(30047)+",15000,"+icon+")")
                item = xbmcgui.ListItem(path=preview)
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
        except:
            xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30048)+",5000,"+icon+")")
            return

    else:
        try:
            game_url = soup.findAll('user-verified-content')[0]('user-verified-media-item')[0]('url')[0].string
            if debug == "true":
                addon_log( 'game_url = '+game_url )
        except:
            addon_log( 'game_url not found' )
            xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30049)+",5000,"+icon+")")
            return

        if game_url.startswith('rtmp'):
            if re.search('ondemand', game_url):
                rtmp = game_url.split('ondemand/')[0]+'ondemand?_fcs_vhost=cp65670.edgefcs.net&akmfv=1.6&'+game_url.split('?')[1]
                playpath = ' Playpath='+game_url.split('ondemand/')[1]
            if re.search('live/', game_url):
                rtmp = game_url.split('mlb_')[0]
                playpath = ' Playpath=mlb_'+game_url.split('mlb_')[1]
        else:
            smil = get_smil(game_url.split('?')[0])
            rtmp = smil[0]
            playpath = ' Playpath='+smil[1]+'?'+game_url.split('?')[1]


        if name == 'full_count':
            pageurl = (' pageUrl=http://mlb.mlb.com/shared/flash/mediaplayer/v4.4/R3/MP4.jsp?calendar_event_id=%s'
                       '&content_id=&media_id=&view_key=&media_type=&source=FULLCOUNT&sponsor=FULLCOUNT&clickOrigin=&affiliateId='
                       % soup.find('event-id').string)
        elif 'mp3:' in game_url:
            pageurl = (' pageUrl=http://mlb.mlb.com/shared/flash/mediaplayer/v4.4/R1/MP4.jsp?calendar_event_id='
                       '%s&content_id=%s&media_id=&view_key=&media_type=audio&source=MLB&sponsor=MLB&'
                       'clickOrigin=Media+Grid&affiliateId=Media+Grid&feed_code=h&team=mlb'
                       %(soup.find('event-id').string, content))
        else:
            pageurl = (' pageUrl=http://mlb.mlb.com/shared/flash/mediaplayer/v4.4/R4/MP4.jsp?calendar_event_id=%s&content_id='
                       '&media_id=&view_key=&media_type=video&source=MLB&sponsor=MLB&clickOrigin=&affiliateId=&team=mlb'
                       % soup.find('event-id').string)
        swfurl = ' swfUrl=http://mlb.mlb.com/shared/flash/mediaplayer/v4.4/R4/MediaPlayer4.swf swfVfy=1'
        if live:
            swfurl += ' live=1'
        final_url = rtmp+playpath+pageurl+swfurl
        if debug == "true":
            addon_log( 'Name: '+name )
            addon_log( 'final url: '+final_url )
        item = xbmcgui.ListItem(path=final_url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def get_smil(url):
    soup = BeautifulStoneSoup(getRequest(url))
    base = soup.meta['base']
    scenario = addon.getSetting('scenario')
    for i in soup('video'):
        if i['system-bitrate'] == scenario.replace('K','000'):
            path = i['src']
            return (base, path)
        else: continue


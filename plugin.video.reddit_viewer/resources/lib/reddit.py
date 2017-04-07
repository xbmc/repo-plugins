# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import sys
import urllib2, urllib
import re
import os

from default import addon, subredditsFile, urlMain, itemsPerPage,subredditsPickle,REQUEST_TIMEOUT
from utils import log, translation,xbmc_notify
from default import reddit_clientID, reddit_userAgent, reddit_redirect_uri


reddit_refresh_token =addon.getSetting("reddit_refresh_token")
reddit_access_token  =addon.getSetting("reddit_access_token") #1hour token

def reddit_request( url, data=None ):

    if reddit_refresh_token:
        url=url.replace('www.reddit.com','oauth.reddit.com' )
        url=url.replace( 'np.reddit.com','oauth.reddit.com' )
        url=url.replace(       'http://',        'https://' )
        log( "  replaced reqst." + url + " + access token=" + reddit_access_token)

    req = urllib2.Request(url)

    req.add_header('User-Agent', reddit_userAgent)   #userAgent = "XBMC:"+addonID+":v"+addon.getAddonInfo('version')+" (by /u/gsonide)"

    if reddit_refresh_token:
        req.add_header('Authorization','bearer '+ reddit_access_token )

    try:
        page = urllib2.urlopen(req,data=data, timeout=20)
        response=page.read();page.close()
        return response

    except urllib2.HTTPError, err:
        if err.code in [403,401]:  #401 Unauthorized, 403 forbidden. access tokens expire in 1 hour. maybe we just need to refresh it
            log("    attempting to get new access token")
            if reddit_get_access_token():
                log("      Success: new access token "+ reddit_access_token)
                req.add_header('Authorization','bearer '+ reddit_access_token )
                try:
                    log("      2nd attempt:"+ url)
                    page = urllib2.urlopen(req)   #it has to be https:// not http://
                    response=page.read();page.close()
                    return response

                except urllib2.HTTPError, err:
                    xbmc.executebuiltin('XBMC.Notification("%s %s", "%s" )' %( err.code, err.msg, url)  )
                    log( err.reason )
                except urllib2.URLError, err:
                    log( err.reason )
            else:
                log( "*** failed to get new access token - don't know what to do " )

        xbmc_notify("%s %s" %( err.code, err.msg), url)
    except urllib2.URLError, err: # Not an HTTP-specific error (e.g. connection refused)
        xbmc_notify(err.reason, url)
    except :
        pass

def reddit_get_refresh_token(url, name, type_):

    code = addon.getSetting("reddit_code")


    if reddit_refresh_token and code:

        dialog = xbmcgui.Dialog()
        if dialog.yesno(translation(30411), translation(30412), translation(30413), translation(30414) ):
            pass
        else:
            return

    try:
        log( "Requesting a reddit permanent token with code=" + code )

        req = urllib2.Request('https://www.reddit.com/api/v1/access_token')

        data = urllib.urlencode({'grant_type'  : 'authorization_code'
                                ,'code'        : code                     #'woX9CDSuw7XBg1MiDUnTXXQd0e4'
                                ,'redirect_uri': reddit_redirect_uri})    #http://localhost:8090/

        import base64
        base64string = base64.encodestring('%s:%s' % (reddit_clientID, '')).replace('\n', '')
        req.add_header('Authorization',"Basic %s" % base64string)
        req.add_header('User-Agent', reddit_userAgent)

        page = urllib2.urlopen(req, data=data)
        response=page.read();page.close()
        log( response )

        status=reddit_set_addon_setting_from_response(response)

        if status=='ok':
            r1="Click 'OK' when done"
            r2="Settings will not be saved"
            xbmc.executebuiltin("XBMC.Notification(%s, %s)"  %( r1, r2)  )
        else:
            r2="Requesting a reddit permanent token"
            xbmc.executebuiltin("XBMC.Notification(%s, %s)"  %( status, r2)  )


    except urllib2.HTTPError, err:
        xbmc_notify(err.code, err.msg)
    except urllib2.URLError, err: # Not an HTTP-specific error (e.g. connection refused)
        xbmc_notify('get_refresh_token',err.reason)

def reddit_get_access_token(url="", name="", type_=""):
    try:
        log( "Requesting a reddit 1-hour token" )
        req = urllib2.Request('https://www.reddit.com/api/v1/access_token')

        data = urllib.urlencode({'grant_type'    : 'refresh_token'
                                ,'refresh_token' : reddit_refresh_token })

        import base64
        base64string = base64.encodestring('%s:%s' % (reddit_clientID, '')).replace('\n', '')
        req.add_header('Authorization',"Basic %s" % base64string)
        req.add_header('User-Agent', reddit_userAgent)

        page = urllib2.urlopen(req, data=data)
        response=page.read();page.close()

        status=reddit_set_addon_setting_from_response(response)

        if status=='ok':
            return True
        else:
            r2="Requesting 1-hour token"
            xbmc.executebuiltin("XBMC.Notification(%s, %s)"  %( status, r2)  )

    except urllib2.HTTPError, err:
        xbmc_notify(err.code, err.msg)
    except urllib2.URLError, err: # Not an HTTP-specific error (e.g. connection refused)
        xbmc_notify('get_access_token',err.reason)

    return False

def reddit_set_addon_setting_from_response(response):
    import time, json
    from utils import convert_date
    global reddit_access_token    #specify "global" if you want to change the value of a global variable
    global reddit_refresh_token
    try:
        response = json.loads(response.replace('\\"', '\''))
        log( json.dumps(response, indent=4) )

        if 'error' in response:

            return response['error']
        else:
            if 'refresh_token' in response:  #refresh_token only returned when getting reddit_get_refresh_token. it is a one-time step
                reddit_refresh_token = response['refresh_token']
                addon.setSetting('reddit_refresh_token', reddit_refresh_token)

            reddit_access_token = response['access_token']
            addon.setSetting('reddit_access_token', reddit_access_token)


            addon.setSetting('reddit_access_token_scope', response['scope'])

            unix_time_now = int(time.time())
            unix_time_now += int( response['expires_in'] )
            addon.setSetting('reddit_access_token_expires', convert_date(unix_time_now))

    except Exception as e:
        log("  parsing reddit token response EXCEPTION:="+ str( sys.exc_info()[0]) + "  " + str(e) )
        return str(e)

    return "ok"

def reddit_revoke_refresh_token(url, name, type_):
    global reddit_access_token    #specify "global" if you wanto to change the value of a global variable
    global reddit_refresh_token
    try:
        log( "Revoking refresh token " )

        req = urllib2.Request('https://www.reddit.com/api/v1/revoke_token')

        data = urllib.urlencode({'token'          : reddit_refresh_token
                                ,'token_type_hint': 'refresh_token'       })

        import base64
        base64string = base64.encodestring('%s:%s' % (reddit_clientID, '')).replace('\n', '')
        req.add_header('Authorization',"Basic %s" % base64string)
        req.add_header('User-Agent', reddit_userAgent)

        page = urllib2.urlopen(req, data=data)
        response=page.read();page.close()

        log( "response:" + response )


        addon.setSetting('reddit_refresh_token', "")
        addon.setSetting('reddit_access_token', "")
        addon.setSetting('reddit_access_token_scope', "")
        addon.setSetting('reddit_access_token_expires', "")
        reddit_refresh_token=""
        reddit_access_token=""

        r2="Revoking refresh token"
        xbmc.executebuiltin("XBMC.Notification(%s, %s)"  %( 'Token revoked', r2)  )

    except urllib2.HTTPError, err:
        xbmc_notify(err.code, err.msg)
    except Exception as e:
        xbmc_notify('Revoking refresh token', str(e))

def reddit_save(api_method, post_id, type_):

    url=urlMain+api_method
    data = urllib.urlencode({'id'  : post_id })

    response=reddit_request( url,data )
    log(repr(response))
    if response=='{}':
        xbmc_notify(api_method, 'Success')
        if api_method=='/api/unsave/':
            xbmc.executebuiltin('XBMC.Container.Refresh')
    else:
        xbmc_notify(api_method, response)

def create_default_subreddits():

    with open(subredditsFile, 'a') as fh:

        fh.write('/user/sallyyy19/m/video[%s]\n' %(translation(30006)))  # user   http://forum.kodi.tv/member.php?action=profile&uid=134499
        fh.write('Documentaries+ArtisanVideos+lectures+LearnUselessTalents\n')
        fh.write('Stop_Motion+FrameByFrame+Brickfilms+Animation\n')
        fh.write('random\n')

        fh.write('[Frontpage]\n')
        fh.write('popular\n')
        fh.write('gametrailers+tvtrailers+trailers\n')
        fh.write('music+listentothis+musicvideos\n')
        fh.write('site:youtube.com\n')
        fh.write('videos\n')

        fh.write('woahdude+interestingasfuck+shittyrobots\n')

def format_multihub(multihub):

    t = multihub

    ls = t.split('/')

    for idx, word in enumerate(ls):
        if word.lower()=='user':ls[idx]='user'
        if word.lower()=='m'   :ls[idx]='m'

    return "/".join(ls)

def this_is_a_multireddit(subreddit):

    subreddit=subreddit.lower()
    return subreddit.startswith(('user/','/user/')) #user can enter multihub with or without the / in the beginning

def this_is_a_user_saved_list(subreddit):

    subreddit=subreddit.lower()
    return (subreddit.startswith(('user/','/user/')) and subreddit.endswith('/saved') )

def parse_subreddit_entry(subreddit_entry_from_file):


    subreddit, alias, viewid = subreddit_alias( subreddit_entry_from_file )

    entry_type='subreddit'

    description=subreddit

    a=[':','/domain/']
    if any(x in subreddit for x in a):  #search for ':' or '/domain/'
        entry_type='domain'

        domain=re.findall(r'(?::|\/domain\/)(.+)',subreddit)[0]
        description=translation(30008) % domain            #"Show %s links"

    if '+' in subreddit:
        entry_type='combined'
        description=subreddit.replace('+','[CR]')

    if this_is_a_multireddit(subreddit):
        entry_type='multireddit'
        description=translation(30007)  #"Custom Multireddit"


    return entry_type, subreddit, alias, description

def subreddit_alias( subreddit_entry_from_file ):


    a=re.compile(r"(\[[^\]]*\])") #this regex only catches the []

    alias=""
    viewid=""

    subreddit = a.sub("",subreddit_entry_from_file).strip()

    try:viewid= subreddit[subreddit.index("(") + 1:subreddit.rindex(")")]
    except (ValueError,TypeError):viewid=""


    if viewid:

        subreddit=subreddit.replace( "(%s)"%viewid, "" )

    a= a.findall(subreddit_entry_from_file)
    if a:
        alias=a[0]

    else:
        alias = subreddit

    return subreddit, alias, viewid

def assemble_reddit_filter_string(search_string, subreddit, skip_site_filters="", domain="" ):


    url = urlMain      # global variable urlMain = "http://www.reddit.com"

    if subreddit.startswith('?'):

        url+='/search.json'+subreddit
        return url

    a=[':','/domain/']
    if any(x in subreddit for x in a):  #search for ':' or '/domain/'

        domain=re.findall(r'(?::|\/domain\/)(.+)',subreddit)[0]


    if domain:

        url+= "/domain/%s/.json?" %(domain)   #/domain doesn't work with /search?q=
    else:
        if this_is_a_multireddit(subreddit):

            if subreddit.startswith('/'):

                url+=subreddit  #user can enter multihub with or without the / in the beginning
            else: url+='/'+subreddit
        else:
            if subreddit:
                url+= "/r/"+subreddit


        if search_string:
            search_string = urllib.unquote_plus(search_string)
            url+= "/search.json?q=" + urllib.quote_plus(search_string)
        elif skip_site_filters:
            url+= "/.json?"
        else:

            url+= "/.json?"

    url += "&limit="+str(itemsPerPage)

    return url

def has_multiple(tag, content_data_children):

    s=""
    for entry in content_data_children:
        try:
            if s:
                if s!=entry['data'][tag]:
                    return True
            else:
                s=entry['data'][tag]
        except KeyError:
            continue
    return False

def collect_thumbs( entry ):

    dictList = []
    keys=['thumb','width','height']
    e=[]

    try:
        e=[ entry['data']['media']['oembed']['thumbnail_url'].encode('utf-8')
           ,entry['data']['media']['oembed']['thumbnail_width']
           ,entry['data']['media']['oembed']['thumbnail_height']
           ]

        dictList.append(dict(zip(keys, e)))
    except (ValueError,TypeError,AttributeError):

        pass

    try:
        e=[ entry['data']['preview']['images'][0]['source']['url'].encode('utf-8')
           ,entry['data']['preview']['images'][0]['source']['width']
           ,entry['data']['preview']['images'][0]['source']['height']
           ]

        dictList.append(dict(zip(keys, e)))
    except(ValueError,TypeError,AttributeError):
        pass

    try:
        e=[ entry['data']['thumbnail'].encode('utf-8')        #thumbnail is always in 140px wide (?)
           ,140
           ,0
           ]

        dictList.append(dict(zip(keys, e)))
    except (ValueError,TypeError,AttributeError):
        pass

    return

def determine_if_video_media_from_reddit_json( data ):
    from utils import clean_str

    is_a_video=False

    media_url=clean_str(data,['media','oembed','url'],'')
    if media_url=='':
        media_url=clean_str(data,['url'])


    media_url=media_url.split('?')[0] #get rid of the query string
    try:
        zzz = data['media']['oembed']['type']

        if zzz == None:   #usually, entry['data']['media'] is null for not videos but it is also null for gifv especially nsfw
            if ".gifv" in media_url.lower():  #special case for imgur
                is_a_video=True
            else:
                is_a_video=False
        elif zzz == 'video':
            is_a_video=True
        else:
            is_a_video=False
    except (KeyError,TypeError,AttributeError):
        is_a_video=False

    return is_a_video

def get_subreddit_info( subreddit ):
    import requests

    subs_dict={}

    headers = {'User-Agent': reddit_userAgent}
    req='https://www.reddit.com/r/%s/about.json' %subreddit

    r = requests.get( req, headers=headers, timeout=REQUEST_TIMEOUT )
    if r.status_code == requests.codes.ok:
        j=r.json()

        j=j.get('data')
        if 'display_name' in j:
            subs_dict.update( {'entry_name':subreddit.lower(),
                               'display_name':j.get('display_name'),
                               'banner_img': j.get('banner_img'),
                               'icon_img': j.get('icon_img'),
                               'header_img': j.get('header_img'), #not used? usually similar to with icon_img
                               'title':j.get('title'),
                               'header_title':j.get('header_title'),
                               'public_description':j.get('public_description'),
                               'subreddit_type':j.get('subreddit_type'),
                               'subscribers':j.get('subscribers'),
                               'created':j.get('created'),        #public, private
                               'over18':j.get('over18'),
                               } )

            return subs_dict

        else:
            log('    No data for (%s)'%subreddit)
    else:
        log( '    getting subreddit (%s) info:%s' %(subreddit, r.status_code) )

subreddits_dlist=[]
def ret_sub_info( subreddit_entry ):

    import random
    from utils import load_dict
    global subreddits_dlist #we make sure we only load the subredditsPickle file once for this instance
    try:
        if not subreddits_dlist:
            if os.path.exists(subredditsPickle):
                subreddits_dlist=load_dict(subredditsPickle)

        subreddit_search=subreddit_entry.lower()
        if '/' in subreddit_search:
            subreddit_search=subreddit_search.split('/')[0]

        if '+' in subreddit_search:
            subreddit_search=random.choice(subreddit_search.split('+'))

        for sd in subreddits_dlist:

            if sd.get('entry_name')==subreddit_search:
                return sd
    except:

        pass

def ret_sub_icon(subreddit):
    sub_info=ret_sub_info(subreddit)

    if sub_info:

        return next((item for item in [sub_info.get('icon_img'),sub_info.get('banner_img'),sub_info.get('header_img')] if item ), '')


subredditsFile_entries=[]
def load_subredditsFile():
    global subredditsFile_entries
    if not subredditsFile_entries:
        if os.path.exists(subredditsFile):  #....\Kodi\userdata\addon_data\plugin.video.reddit_viewer\subreddits
            with open(subredditsFile, 'r') as fh:
                content = fh.read()
            spl = content.split('\n')

            for i in range(0, len(spl), 1):
                if spl[i]:
                    subreddit = spl[i].strip()

                    subredditsFile_entries.append(subreddit )
    return subredditsFile_entries

def subreddit_in_favorites( subreddit ):
    sub_favorites=load_subredditsFile()
    for entry in sub_favorites:
        if subreddit.lower() == entry.lower():
            return True
        if '+' in entry:
            spl=entry.split('+')
            for s in spl:
                if subreddit.lower() == s.lower():
                    return True


if __name__ == '__main__':
    pass

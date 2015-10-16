import cookielib
import urllib2
import time
import calendar

import xbmcgui
from resources.lib.globals import *
from resources.lib.thumbnailgenerator import *


def cdnServer(feed_url):
    modified_feed_url = feed_url
    if CDN_SERVER != DEFAULT_CDN_SERVER:
         modified_feed_url = feed_url.replace(DEFAULT_CDN_SERVER,CDN_SERVER)
         print "CDN Server Changed to: " + CDN_SERVER
	 
    return modified_feed_url

def login(): 
     #Create Profile Folder if necessary
    if not os.path.exists(ADDON_PATH_PROFILE):
        os.makedirs(ADDON_PATH_PROFILE)
    #Login
    cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    opener.addheaders = [('Content-type', 'application/x-www-form-urlencoded')]
    if ROGERSLOGIN == 'true':
        login_data = urllib.urlencode({'username': USERNAME, 'password': PASSWORD, 'rogers': 'true', 'cookielink': 'false'})
    else:
        login_data = urllib.urlencode({'username': USERNAME, 'password': PASSWORD})
    r=opener.open('https://gamecenter.nhl.com/nhlgc/secure/login', login_data)    

    print r.getcode()
    print r.info()
    print "URL"
    print r.geturl()
    print r.info().getheaders('Set-Cookie')
    # A valid login has at least 4 cookies that are set. 
    if len(r.info().getheaders('Set-Cookie')) < 4:
        #os.remove(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        #print "cookies removed"        
        dialog = xbmcgui.Dialog()
        dialog.ok('Login failed', 'Check your login credentials')
        sys.exit()
        #xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),succeeded=False)
        #return None
    else:
        #Save the cookie
        cj.save(ignore_discard=True);


def checkLogin():    
    expired_cookies = True
    try:
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        at_least_one_expired = False
        for cookie in cj:                
            #if cookie.name == 'gcsub':
            print cookie.name
            print cookie.expires
            print cookie.is_expired()
            if cookie.is_expired():
                at_least_one_expired = True
                break

        if not at_least_one_expired:
            expired_cookies = False
            
    except:
        pass

   
    if expired_cookies:
        login()
    '''
    try:
        #Get the last time the file was modified
        file_modified = time.localtime(os.path.getmtime(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')))
        print "Cookies file was last modified " + str(time.strftime('%m/%d/%Y %H:%M', file_modified)) 
        now = time.time()
        exp_cut_off = now - 60*60*12 # Number of seconds in twelve hours

        if calendar.timegm(file_modified) < exp_cut_off:
            print "Cookies are more than 12hrs old"
            login()
        else:
            print "Still Good"
    except:
        #Cookie file / folder not found. Call login to create them
        login()
    '''

    



def downloadFile(url,values):
    
    downloadedFile = ''

    for i in range(1, 3):
        print "Download: " + str(i) + ". try"
        
        #Setup the request
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [('Host', 'gamecenter.nhl.com'),
                             ('User-Agent', 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'),
                             ('Accept', '*/*'),
                             ('Referer', 'http://gamecenter.nhl.com/nhlgc/console.jsp'),
                             ('Accept-Language', 'de-de'),
                             ('Accept-Encoding', 'gzip, deflate'),
                             ('Connection', 'keep-alive'),
                             ('Content-Type', 'application/x-www-form-urlencoded')]
        login_data = urllib.urlencode(values)
    
        #Download the file
        response = opener.open(url, login_data)
        downloadedFile = response.read().strip()
        
        #Try to login again if File not accessible
        if "<code>noaccess</code>" in downloadedFile:
            print "No access to XML file"
            checkLogin()
            continue
        else:
            print "Download successful"
            break
    else:
        print "Login failed. Check your login credentials."

    return downloadedFile
    

def updateThumbs():
    #Show progressbar
    i = 0
    steps = 0.0
    progress = xbmcgui.DialogProgress()
    
    if DELETETHUMBNAILS == 'true':
        steps = steps + 1
    if GENERATETHUMBNAILS == 'true':
        steps = steps + 1
    if (THUMBFORMAT != THUMBFORMATOSD) or (BACKGROUND != BACKGROUNDOSD):
        steps = steps + 1
    
    progress.create(LOCAL_STRING(31300), '')
    percent = int( ( i / steps ) * 100)
    message = LOCAL_STRING(31350)
    progress.update( percent, "", message, "" )
    i = i + 1
    print percent, steps
    
    #Delete thumbnails
    if DELETETHUMBNAILS == 'true':
        deleteThumbnails(ADDON_PATH_PROFILE)

        #Reset setting
        ADDON.setSetting(id='delete_thumbnails', value='false')

        #Update progressbar
        percent = int( ( i / steps ) * 100)
        message = LOCAL_STRING(31350)
        progress.update( percent, "", message, "" )
        i = i + 1
        print percent, steps

    #Create thumbnails
    if GENERATETHUMBNAILS == 'true':
        createThumbnails(ADDON_PATH,ADDON_PATH_PROFILE,THUMBFORMAT,BACKGROUND)

        #Update progress
        percent = int( ( i / steps ) * 100)
        message = LOCAL_STRING(31350)
        progress.update( percent, "", message, "" )
        i = i + 1
        print percent, steps
    
        if (THUMBFORMAT != THUMBFORMATOSD) or (BACKGROUND != BACKGROUNDOSD):
            createThumbnails(ADDON_PATH,ADDON_PATH_PROFILE,THUMBFORMATOSD,BACKGROUNDOSD)

            #Update progress
            percent = int( ( i / steps ) * 100)
            message = LOCAL_STRING(31350)
            progress.update( percent, "", message, "" )
            i = i + 1
            print percent, steps
    
        #Reset setting
        ADDON.setSetting(id='generate_thumbnails', value='false')

    #Close progressbar
    progress.close()

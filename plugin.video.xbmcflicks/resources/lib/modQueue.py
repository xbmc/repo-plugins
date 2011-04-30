from Netflix import *
import getopt
import time 
import re
import xbmcplugin, xbmcaddon, xbmcgui, xbmc
import urllib
import webbrowser
from xinfo import *

MY_USER = {
        'request': {
             'key': '',
             'secret': ''
        },
        'access': {
            'key': '',
            'secret': ''
        }
}

def __init__(self):
    self.data = []

# AUTH 
def getAuth(netflix, verbose):
    print ".. getAuth called .."
    print "OSX Setting is set to: " + str(OSX)
    netflix.user = NetflixUser(MY_USER,netflix)
    print ".. user configured .."

    #handles all the initial auth with netflix
    if MY_USER['request']['key'] and not MY_USER['access']['key']:
        tok = netflix.user.getAccessToken( MY_USER['request'] )
        if(VERBOSE_USER_LOG):
            print "now put this key / secret in MY_USER.access so you don't have to re-authorize again:\n 'key': '%s',\n 'secret': '%s'\n" % (tok.key, tok.secret)
        MY_USER['access']['key'] = tok.key
        MY_USER['access']['secret'] = tok.secret
        saveUserInfo()
        dialog = xbmcgui.Dialog()
        dialog.ok("Settings completed", "You must restart the xbmcflicks plugin")
        print "Settings completed", "You must restart the xbmcflicks plugin"
        sys.exit(1)

    elif not MY_USER['access']['key']:
        (tok, url) = netflix.user.getRequestToken()
        if(VERBOSE_USER_LOG):
            print "Authorize user access here: %s" % url
            print "and then put this key / secret in MY_USER.request:\n 'key': '%s',\n 'secret': '%s'\n" % (tok.key, tok.secret)
            print "and run again."
        #open web page with urllib so customer can authorize the app

        if(OSX):
            startBrowser(url)
        else:
            webbrowser.open(url)
            
        #display click ok when finished adding xbmcflicks as authorized app for your netflix account
        dialog = xbmcgui.Dialog()
        ok = dialog.ok("After you have linked xbmcflick in netflix.", "Click OK after you finished the link in your browser window.")
        MY_USER['request']['key'] = tok.key
        MY_USER['request']['secret'] = tok.secret
        #now run the second part, getting the access token
        tok = netflix.user.getAccessToken( MY_USER['request'] )
        if(VERBOSE_USER_LOG):
            print "now put this key / secret in MY_USER.access so you don't have to re-authorize again:\n 'key': '%s',\n 'secret': '%s'\n" % (tok.key, tok.secret)
        MY_USER['access']['key'] = tok.key
        MY_USER['access']['secret'] = tok.secret
        #now save out the settings
        saveUserInfo()
        #exit script, user must restart
        dialog.ok("Settings completed", "You must restart the xbmcflicks plugin")
        print "Settings completed", "You must restart the xbmcflicks plugin"
        exit
        sys.exit(1)

    return netflix.user

def saveUserInfo():
    #create the file
    f = open(os.path.join(str(USERINFO_FOLDER), 'userinfo.txt'),'w+')
    setting ='requestKey=' + MY_USER['request']['key'] + '\n' + 'requestSecret=' + MY_USER['request']['secret'] + '\n' +'accessKey=' + MY_USER['access']['key']+ '\n' + 'accessSecret=' + MY_USER['access']['secret']
    f.write(setting)
    f.close()

# END AUTH

def initApp():
    global APP_NAME
    global API_KEY
    global API_SECRET
    global CALLBACK
    global user
    global counter
    global ROOT_FOLDER
    global WORKING_FOLDER
    global LINKS_FOLDER
    global REAL_LINK_PATH
    global IMAGE_FOLDER
    global USERINFO_FOLDER
    global VERBOSE_USER_LOG
    global DEBUG
    global OSX
    
    APP_NAME = 'xbmcflix'
    API_KEY = 'gnexy7jajjtmspegrux7c3dj'
    API_SECRET = '179530/200BkrsGGSgwP6446x4x22astmd5118'
    CALLBACK = ''
    VERBOSE_USER_LOG = False
    DEBUG = False
    OSX = False

    #get addon info
    __settings__ = xbmcaddon.Addon(id='plugin.video.xbmcflicks')
    ROOT_FOLDER = __settings__.getAddonInfo('path')
    RESOURCE_FOLDER = os.path.join(str(ROOT_FOLDER), 'resources')
    LIB_FOLDER = os.path.join(str(RESOURCE_FOLDER), 'lib')
    WORKING_FOLDER = xbmc.translatePath(__settings__.getAddonInfo("profile"))
    LINKS_FOLDER = os.path.join(str(WORKING_FOLDER), 'links')
    REAL_LINK_PATH = os.path.join(str(WORKING_FOLDER), 'links')
    USERINFO_FOLDER = WORKING_FOLDER
    XBMCPROFILE = xbmc.translatePath('special://profile')
    
    reobj = re.compile(r"200(.{10}).*?644(.*?)4x2(.).*?5118")
    match = reobj.search(API_SECRET)
    if match:
        result = match.group(1)
        API_SECRET = result

    #ensure we have a links folder in addon_data
    if not os.path.exists(LINKS_FOLDER):
        os.makedirs(LINKS_FOLDER)
    
    #get user info
    userInfoFileLoc = os.path.join(str(USERINFO_FOLDER), 'userinfo.txt')
    print "USER INFO FILE LOC: " + userInfoFileLoc
    havefile = os.path.isfile(userInfoFileLoc)
    if(not havefile):
        f = open(userInfoFileLoc,'w+')
        f.write("")
        f.close()

    userstring = open(str(userInfoFileLoc),'r').read()
        
    reobj = re.compile(r"requestKey=(.*)\nrequestSecret=(.*)\naccessKey=(.*)\naccessSecret=(.*)")
    match = reobj.search(userstring)
    if match:
        print "matched file contents, it is in the correct format"
        MY_USER['request']['key'] = match.group(1).strip()
        MY_USER['request']['secret'] = match.group(2).strip()
        MY_USER['access']['key'] = match.group(3).strip()
        MY_USER['access']['secret'] = match.group(4).strip()
        print "finished loading up user information from file"
    else:
        #no match, need to fire off the user auth from the start
        print "couldn't load user information from userinfo.txt file"
    #auth the user
    netflixClient = NetflixClient(APP_NAME, API_KEY, API_SECRET, CALLBACK, VERBOSE_USER_LOG)
    user = getAuth(netflixClient,VERBOSE_USER_LOG)
    if(not user):
        exit

if __name__ == '__main__':
    initApp()
    if ( len( sys.argv ) > 1 ):
        print str(len(sys.argv))
        print str(sys.argv[0])
        print str(sys.argv[1])

    strArgs = str(sys.argv[1])
    movieid = ""
    action = ""
    actionParams = ""
    verboseAction = ""
    verboseDirection = ""
    details = ""
    position = ""
    discQueue = False
    
    match = re.search(r"(.*?)(delete|post|discdelete|discpost|disctoppost)", strArgs, re.IGNORECASE)
    if match:
        movieid = match.group(1)
        print movieid
        action = match.group(2)
        actionParams = match.group(2)
        print action
    else:
        "print unable to parse action item, exiting"
        exit

    if(action == "post"):
        verboseAction = "Add"
        verboseDirection = "to"
    elif(action == "delete"):
        verboseAction = "Remove"
        verboseDirection = "from"
    elif(action == "discpost"):
        action = "post"
        verboseAction = "Add"
        verboseDirection = "to"
        discQueue = True
    elif(action == "disctoppost"):
        action = "post"
        verboseAction = "Add"
        verboseDirection = "to"
        discQueue = True
        position = "1"
    elif(action == "discdelete"):
        action = "delete"
        verboseAction = "Remove"
        verboseDirection = "from"
        discQueue = True

    netflixClient = NetflixClient(APP_NAME, API_KEY, API_SECRET, CALLBACK, VERBOSE_USER_LOG)
    #auth the user
    user = getAuth(netflixClient,VERBOSE_USER_LOG)

    #if we have a user, do the action
    if user:
        if(not discQueue):         
            result = user.modifyQueue(str(movieid), str(action))
            matchr = re.search(r"'message': u'(.*?)'", str(result), re.IGNORECASE)
            if matchr:
                details = matchr.group(1)
            else:
                details = str(result)
            dialog = xbmcgui.Dialog()
            ok = dialog.ok("Instant Queue: " + verboseAction + " " + movieid, details)
        if(discQueue):
            if(position == ""):
                result = user.modifyQueueDisc(str(movieid), str(action))
            else:
                result = user.modifyQueueDisc(str(movieid), str(action), position)
            matchr = re.search(r"'message': u'(.*?)'", str(result), re.IGNORECASE)
            if matchr:
                details = matchr.group(1)
            else:
                details = str(result)
            dialog = xbmcgui.Dialog()
            ok = dialog.ok("Disc Queue: " + verboseAction + " " + movieid, details)
         
        #refresh UI on delete, disc delete, or move to top
        if(actionParams == "delete"):
            xbmc.executebuiltin("Container.Refresh")
        elif(actionParams == "discdelete"):
            xbmc.executebuiltin("Container.Refresh")
        elif(actionParams == "disctoppost"):
            xbmc.executebuiltin("Container.Refresh")
    else:
        print "Failed to get user information from main init of modQueue script"

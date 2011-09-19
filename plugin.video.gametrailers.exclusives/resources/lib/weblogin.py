"""

Module:   weblogin.py
Author:   Anarchintosh @ xbmcforums
          AssChin79 @ xbmcforums (minor tweaks)
License:  Copyleft (GNU GPL v3) 2011 onwards
Date:     9/13/2011
Summary:  This example is configured for gametrailers.com login. See for the full guide please visit:
          http://forum.xbmc.org/showthread.php?p=772597#post772597
USAGE:
 In your addon default.py put:

 import weblogin
 logged_in = weblogin.doLogin('a-path-to-save-the-cookie-to','the-username','the-password')
 logged_in will then be either True or False depending on whether the login was successful.

"""

import os,os.path
import re
import time
import urllib,urllib2
import cookielib

#<summary>
# Test Settings: these will only be used when running this file independent of your addon.
# Remember to clear these after you are finished testing, so that your sensitive details are not in your source code.
# These are only used in the:  if __name__ == "__main__" mechanism at the bottom of this script.
#</summary>
myusername = ''
mypassword = ''


#<summary>
# Validates whether a login attempt was successful.
#</summary>
#<param name="source">The HTML source to search in</param>
#<param name="username">The username to find in the source (Optional)</param>
def check_login(source,username):
    
    # The string you will use to check if the login is successful.
    logged_in_string = 'newestlist'

    # Search for the string in the html, without caring about upper or lower case
    if re.search(logged_in_string,source,re.IGNORECASE):
        return True
    else:
        return False

#<summary>
# Deletes cookies older than 24 hours.
#</summary>
#<param name="threshold">The frequency in seconds that the cookie should be deleted</param>
#<param name="cookie_file">The full path to the cookie file</param>
def wipeOldCookies(threshold,cookie_file):
    if os.path.exists(cookie_file) == True:
        ftime = os.path.getmtime(cookie_file)
        curtime = time.time()
        difftime = curtime - ftime
        if difftime > threshold:
            os.unlink(cookie_file)
            return True
        else:
            return False        
    else:
        return False
         
#<summary>
# Login to the web site and save the cookie file locally.
#</summary>
#<param name="cookiepath">The full path to the cookie file</param>
#<param name="username">The user name</param>
#<param name="password">The user's password</param>
def doLogin(cookiepath, username, password):

    cookiepath = os.path.join(cookiepath,'cookies.lwp')
    
    if os.path.exists(cookiepath) == True:
        # delete cookie older than 24 hours old
        if wipeOldCookies(86400, cookiepath) == False:
            # don't create a new cookie if a good one is lying around
            return True

    if username and password:

        #the url you will request to.
        login_url = 'http://www.gametrailers.com/login.php'

        #the header used to pretend you are a browser
        header_string = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

        #build the form data necessary for the login
        login_data = urllib.urlencode({'username':username, 'password':password, 'try':1})

        #build the request we will make
        req = urllib2.Request(login_url, login_data)
        req.add_header('User-Agent',header_string)

        #initiate the cookielib class
        cj = cookielib.LWPCookieJar()

        #install cookielib into the url opener, so that cookies are handled
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

        #do the login and get the response
        response = opener.open(req)
        source = response.read()
        response.close()

        #check the received html for a string that will tell us if the user is logged in
        #pass the username, which can be used to do this.
        login = check_login(source,username)

        #if login suceeded, save the cookiejar to disk
        if login == True:
            cj.save(cookiepath)

        #return whether we are logged in or not
        return login
    
    else:
        return False

#code to enable running the .py independent of addon for testing
if __name__ == "__main__":
    if myusername is '' or mypassword is '':
        print 'YOU HAVE NOT SET THE USERNAME OR PASSWORD!'
    else:
        logged_in = doLogin(os.getcwd(),myusername,mypassword)
        print 'LOGGED IN:',logged_in

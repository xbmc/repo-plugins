import urllib2
from urlparse import urljoin
import cookielib
import mechanize
from mechanize import HTTPCookieProcessor
from xbmc import log, LOGDEBUG
import os
import re

"""
Utiltiy http handling.  Opens a url with Mechanize, fills in log in credentials
through form.  Checks for successful login and resolves relative urls to
absolute ones.

"""

def openUrl(url, cookie=None, login=False):
    """
    Opens a given url through mechanize. 

    If there is no cookie (string path) passed in or if there is a cooke path
    passed in but the login parameter is False (signifying to open the url with
    cookie saved in the cookie path), the html from the opened url is returned
    as a string.

    If a cookie path is passed in and the login parameter is True, then the
    Mechanize.Broswer object is returned to perform a yogaglo login through
    a form submission.

    """
    browser = mechanize.Browser()
    browser.addheaders = [
        ('User-Agent',
         'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:24.0) Gecko/20100101 Firefox/24.0'),
        ('Accept',
         'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
        ('Accept-Language', 'en-gb,en;q=0.5'),
        ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
        ('Keep-Alive', '115'),
        ('Connection', 'keep-alive'),
        ('Cache-Control', 'max-age=0'),
    ]

    #Experimental?
    # browser.set_handle_gzip(True)
    browser.set_handle_redirect(True)
    browser.set_handle_referer(True)
    browser.set_handle_robots(False)
    browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time = 1)
    
    if not cookie is None:
	cj = cookielib.LWPCookieJar()
	browser.set_cookiejar(cj)
	opener = mechanize.build_opener(HTTPCookieProcessor(cj))
	mechanize.install_opener(opener)
	
	# trying to login, no cookie, must return browser so it can follow the
	# login url
	if login is True:
		browser.open(url)
		return browser
		
	# can't set to expire, can't read when this particular cookie expires
	cj.load(cookie , ignore_discard=True)

    return browser.open(url).read()


def login(cookiePath, username, password, signinUrl):
    """
    Logs in to yogaglo.com with credentials username and password through the
    url signinUrl, saving the return cookie to cookiePath.

    Returns a boolean of True(success)/False(failed) log on to the site.

    NOTE:
    Mechanize wasn't posting the hidden form field right as of 5/15/2014, so I
    had to un-hide all form fields and manually set it to the correct value the
    PHP controller on the server is expecting, or else it wouldn't log on at all.

    """
    if os.path.exists(cookiePath): #delete any old version of the cookie file
	log("cookie %s exists, deleting to aquire new cookie" % (cookiePath), LOGDEBUG)
        os.remove(cookiePath)

    browser = openUrl(signinUrl, cookiePath, True)
    browser.select_form(name="do_User__eventCheckIdentification")
    browser.form.set_all_readonly(False) # yg and mechanize not playing nice, need this
    browser['fields[password]'] = password
    browser['fields[email]'] = username
    browser['mydb_events[210]'] = 'do_User->eventSetSessionVariable' # not set right in post, forcing it now
    submit = browser.submit()
    homepage = submit.read()

    #if login suceeded, save the cookiejar to disk, no expiration to set
    if check_login(homepage) == True:
        browser._ua_handlers['_cookies'].cookiejar.save(cookiePath, ignore_discard=True)
        return True

    # failed login
    return False

def check_login(source):
    """
    Checks for a successful logon to yogaglo.com by checking the HTML source for
    a particular string.  In this case, it is "Welcome Back".  For the yogaglo
    site, the string "Welcome, Guest" will be present if the credentials are
    wrong or missing.

    Returns a boolean of True(success)/False(failed) log on to the site.

    """
    logged_in_string = 'Welcome Back'

    #search for the string in the html, without caring about upper or lower case
    # if string is found, log in successful
    if re.search(logged_in_string, source, re.IGNORECASE):
	log("YogaGlo -- logged in to yogaglo!", LOGDEBUG)
	return True

    return False

def convert_relative_to_absolute_url(base_url, relative_url):
    """
    Converts a relative_url to an aboslute one based on the yogaglo.com
    base_url.

    Returns the absolute url.

    relative_url may be unicode, so convert all to utf-8
    relative_url may have percent encoded portions, so use urlib2's quote method
    to make sure this is a url then can be opened by mechanize.

    """
    utf8_relative_url = relative_url.encode('utf-8')
    url_encoded_relative_url = urllib2.quote(utf8_relative_url)
    return urljoin(base_url, url_encoded_relative_url)


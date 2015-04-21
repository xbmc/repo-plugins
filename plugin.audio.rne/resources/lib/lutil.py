# _*_ coding: utf-8 _*_

'''
   lutil: library functions for KODI media add-ons.
   Copyright (C) 2015 José Antonio Montes (jamontes)

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.
   
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   
   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

   Description:
   These funtions are called from the main plugin module, aimed to ease
   and simplify the plugin development process.
   Release 0.1.9
'''

# First of all We must import all the libraries used for plugin development.
import re, urllib, urllib2
from datetime import date

debug_enable = False # The debug logs are disabled by default.

def set_debug_mode(debug_flag):
    """This function sets the debug_enable var to log everything if debug option is true."""
    global debug_enable
    debug_enable = debug_flag in ("true", True)


def log(message):
    """This function logs the messages into the main KODI log file. Called from main plugin module."""
    if debug_enable:
        print "%s" % message


def _log(message):
    """This function logs the messages into the main KODI log file. Called from the libraries module by other functions."""
    if debug_enable:
        print "lutils.%s" % message


def get_url_decoded(url):
    """This function returns the URL decoded."""
    _log('get_url_decoded URL: "%s"' % url)
    return urllib.unquote_plus(url)


def get_url_encoded(url):
    """This function returns the URL encoded."""
    _log('get_url_encoded URL: "%s"' % url)
    return urllib.quote_plus(url)


def get_parms_encoded(**kwars):
    """This function returns the params encoded to form an URL or data post."""
    param_list = urllib.urlencode(kwars)
    _log('get_parms_encoded params: "%s"' % param_list)  
    return param_list


def carga_web(url):
    """This function loads the html code from a webserver and returns it into a string."""
    _log("carga_web " + url)

    MiReq = urllib2.Request(url) # We use the Request method because we need to add a header into the HTTP GET to the web site.
    # We have to tell the web site we are using a real browser.
    MiReq.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0') # This is a true Firefox header.
    MiConex = urllib2.urlopen(MiReq) # We open the HTTP connection to the URL.
    MiHTML = MiConex.read() # We load all the HTML contents from the web page and store it into a var.
    MiConex.close() # We close the HTTP connection as we have all the info required.

    return MiHTML


def carga_web_cookies(url, headers=''):
    """This function loads the html code from a webserver passsing the headers into the GET message
    and returns it into a string along with the cookies collected from the website."""
    _log("carga_web_cookies " + url)

    MiReq = urllib2.Request(url) # We use the Request method because we need to add a header into the HTTP GET to the web site.
    # We have to tell the web site we are using a real browser.
    MiReq.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0') # This is a true Firefox header.
    for key in headers:
        MiReq.add_header(key, headers[key])
    MiConex = urllib2.urlopen(MiReq) # We open the HTTP connection to the URL.
    MiHTML = MiConex.read() # We load all the HTML contents from the web page and store it into a var.
    server_info = "%s" % MiConex.info()
    my_cookie_pattern = re.compile('Set-Cookie: ([^;]+);')
    my_cookies = ''
    pcookie = ''
    for lcookie in my_cookie_pattern.findall(server_info):
        if (lcookie != pcookie):
            my_cookies = "%s %s;" % (my_cookies, lcookie)
            pcookie = lcookie

    MiConex.close() # We close the HTTP connection as we have all the info required.

    _log("carga_web Cookie:%s" % my_cookies)
    return MiHTML, my_cookies


def send_post_data(url, headers='', data=''):
    """This function sends an HTTP POST request with theirr corresponding headers and data to a webserver
    and returns the html code into a string along with the cookies collected from the website."""
    _log("send_post_data " + url)

    MiReq = urllib2.Request(url, data) # We use the Request method because we need to send a HTTP POST to the web site.
    # We have to tell the web site we are using a real browser.
    MiReq.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0') # This is a true Firefox header.
    for key in headers:
        MiReq.add_header(key, headers[key])
    MiConex = urllib2.urlopen(MiReq) # We open the HTTP connection to the URL.
    MiHTML = MiConex.read() # We load all the HTML contents from the web page and store it into a var.
    server_info = "%s" % MiConex.info()
    my_cookie_pattern = re.compile('Set-Cookie: ([^;]+);')
    my_cookies = ''
    pcookie = ''
    for lcookie in my_cookie_pattern.findall(server_info):
        if (lcookie != pcookie):
            my_cookies = "%s %s;" % (my_cookies, lcookie)
            pcookie = lcookie

    MiConex.close() # We close the HTTP connection as we have all the info required.

    _log("carga_web Cookie:%s" % my_cookies)
    return MiHTML, my_cookies


def get_redirect(url):
    """This function returns the redirected URL from a 30X response received from the webserver."""
    _log("get_redirect " + url)

    MiConex = urllib.urlopen(url) # Opens the http connection to the URL.
    MiHTML = MiConex.geturl() # Gets the URL redirect link and stores it into MiHTML.
    MiConex.close() # Close the http connection as we get what we need.

    return MiHTML


def find_multiple(text,pattern):
    """This function allows us to find multiples matches from a regexp into a string."""

    pat_url_par = re.compile(pattern, re.DOTALL)
   
    return pat_url_par.findall(text)


def find_first(text,pattern):
    """This function gets back the first match from a regexp into a string."""

    pat_url_par = re.compile(pattern, re.DOTALL)
    try:
        return  pat_url_par.findall(text)[0]
    except:
        return ""


def get_this_year():
    """This function gets the current year. Useful to fill the Year infolabel whenever it isn't available"""

    return date.today().year



# _*_ coding: utf-8 _*_

'''
   lutil: library functions for XBMC video plugins.
   Copyright (C) 2013 José Antonio Montes (jamontes)

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
   Release 0.1.6
'''

# First of all We must import all the libraries used for plugin development.
import re, urllib, urllib2

debug_enable = False # The debug logs are disabled by default.

def set_debug_mode(debug_flag):
    """This function sets the debug_enable var to log everything if debug option is true."""
    global debug_enable
    debug_enable = debug_flag in ("true", True)


def log(message):
    """This function logs the messages into the main XBMC log file. Called from main plugin module."""
    if debug_enable:
        print "%s" % message


def _log(message):
    """This function logs the messages into the main XBMC log file. Called from the libraries module by other functions."""
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


def find_multiple(text,pattern):
    """This function allows us to find multiples matches from a regexp into a string."""
    #_log("find_multiple pattern=" + pattern)

    pat_url_par = re.compile(pattern, re.DOTALL)
   
    return pat_url_par.findall(text)


def find_first(text,pattern):
    """This function gets back the first match from a regexp into a string."""
    #_log("find_first pattern=" + pattern)

    pat_url_par = re.compile(pattern, re.DOTALL)
    try:
        return  pat_url_par.findall(text)[0]
    except:
        return ""

#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import StringIO
import gzip
import httplib
import urllib
import urllib2
import xbmc

from tweakers_const import ADDON, SETTINGS, LANGUAGE, DATE, VERSION


#
#
#
class HTTPCommunicator:
    #
    # POST
    #
    def __init__(self):
        pass

    @staticmethod
    def post(host, url, params):
        parameters = urllib.urlencode(params)
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain",
                   "Accept-Encoding": "gzip",
                   "X-Cookies-Accepted": "1"}
        connection = httplib.HTTPConnection("%s:80" % host)

        connection.request("POST", url, parameters, headers)
        response = connection.getresponse()

        # Compressed (gzip) response...
        if response.getheader("content-encoding") == "gzip":
            html_gzipped_data = response.read()
            string_io = StringIO.StringIO(html_gzipped_data)
            gzipper = gzip.GzipFile(fileobj=string_io)
            html_data = gzipper.read()
        # Plain text response...
        else:
            html_data = response.read()

        # Cleanup
        connection.close()

        # Return value
        return html_data

    #
    # GET
    #
    @staticmethod
    def get(url):
        xbmc_version = xbmc.getInfoLabel("System.BuildVersion")
        user_agent = "Kodi Mediaplayer %s / Tweakers Addon %s" % (xbmc_version, VERSION)

        values = {}
        headers = {"User-Agent": user_agent,
                   "Accept-Encoding": "gzip",
                   "X-Cookies-Accepted": "1"}

        data = urllib.urlencode(values)
        req = urllib2.Request(url, data, headers)
        f = urllib2.urlopen(req)

        # Compressed (gzip) response
        if f.headers.get("content-encoding") == "gzip":
            html_gzipped_data = f.read()
            string_io = StringIO.StringIO(html_gzipped_data)
            gzipper = gzip.GzipFile(fileobj=string_io)
            html_data = gzipper.read()

        # Plain text response
        else:
            html_data = f.read()

        # Cleanup
        f.close()

        # Return value
        return html_data

    #
    # Check if URL exists
    #
    @staticmethod
    def exists(url):
        try:
            request = urllib2.Request(url)
            request.get_method = lambda: 'HEAD'
            response = urllib2.urlopen(request)
            response.close()
            return True
        except:
            return False

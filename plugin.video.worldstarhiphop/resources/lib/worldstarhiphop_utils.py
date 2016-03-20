#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import httplib
import urllib
import urllib2
import gzip
import StringIO


#
#
#
class HTTPCommunicator:
    #
    # POST
    #
    def post(self, host, url, params):
        parameters = urllib.urlencode(params)
        # headers     = { "Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain", "Accept-Encoding" : "gzip", "Cookie": "WSHHAdultOk=true" }
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain",
                   "Accept-Encoding": "gzip"}
        connection = httplib.HTTPConnection("%s:80" % host)

        connection.request("POST", url, parameters, headers)
        response = connection.getresponse()

        # Compressed (gzip) response...
        if response.getheader("content-encoding") == "gzip":
            htmlGzippedData = response.read()
            stringIO = StringIO.StringIO(htmlGzippedData)
            gzipper = gzip.GzipFile(fileobj=stringIO)
            htmlData = gzipper.read()
        # Plain text response...
        else:
            htmlData = response.read()

        # Cleanup
        connection.close()

        # Return value
        return htmlData

    #
    # GET
    #
    def get(self, url):
        user_agent = "Mozilla/5.0 (Linux; Android 4.3; Nexus 7 Build/JSS15Q) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.72 Safari/537.36"
        values = {}
        # headers = { "User-Agent"      : user_agent , "Accept-Encoding" : "gzip", "Cookie" : "WSHHAdultOk=true" }
        headers = {"User-Agent": user_agent, "Accept-Encoding": "gzip"}
        data = urllib.urlencode(values)
        req = urllib2.Request(url, data, headers)
        f = urllib2.urlopen(req)

        # Compressed (gzip) response
        if f.headers.get("content-encoding") == "gzip":
            htmlGzippedData = f.read()
            stringIO = StringIO.StringIO(htmlGzippedData)
            gzipper = gzip.GzipFile(fileobj=stringIO)
            htmlData = gzipper.read()

            # Debug
            # print "[HTTP Communicator] GET %s" % url
            # print "[HTTP Communicator] Result size : compressed [%u], decompressed [%u]" % ( len( htmlGzippedData ), len ( htmlData ) )

        # Plain text response
        else:
            htmlData = f.read()

        # Cleanup
        f.close()

        # Return value
        return htmlData

    #
    # Check if URL exists
    #
    def exists(self, url):
        try:
            request = urllib2.Request(url)
            request.get_method = lambda: "HEAD"
            response = urllib2.urlopen(request)
            response.close()
            return True
        except:
            return False

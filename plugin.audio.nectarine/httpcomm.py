import zlib
import httplib
import urllib
import urllib2
import gzip
import StringIO
import cookielib
import socket


class HTTPComm:
    cj = None
    curlinstance = None

    def __init__(self):
        self.cj = cookielib.CookieJar()
        self.curlinstance = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))

    def request(self, url, mode, postdata=None):
        timeout = 10
        socket.setdefaulttimeout(timeout)

        self.curlinstance.addheaders = [
            ('User-Agent', 'XBMC Nectarine Plugin (https://github.com/vidarw/xbmc.plugin.audio.nectarine)'),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ('Accept-Language', 'en-gb,en;q=0.5'),
            ('Accept-Encoding', 'gzip,deflate'),
            ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
            ('Keep-Alive', '115'),
            ('Connection', 'keep-alive'),
            ('Cache-Control', 'max-age=0'),
        ]

        try:
            if mode=='get':
                resp = self.curlinstance.open(url)
            elif mode is 'post' and postdata:
                resp = self.curlinstance.open(url, postdata)
            else:
                return False

            # decompress if gzipped response...
            if resp.headers.get("content-encoding") == "gzip":
                htmlGzippedData = resp.read()
                stringIO = StringIO.StringIO(htmlGzippedData)
                gzipper = gzip.GzipFile(fileobj=stringIO)
                data = gzipper.read()
            else:
                data = resp.read()

            resp.close()

            # Return response data
            return data
        except Exception:
            return False

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

        # Add useragent and tries to look like a real browser, as the site doesn't like to interact with scripts
        self.curlinstance.addheaders = [
            ('User-Agent',
             'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:26.0) Gecko/20100101 Firefox/26.0'),
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

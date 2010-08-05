import sys
import urllib
import httplib
import time
import re
import os
import settings
from misc import _get_path

class CookieFetcher:
    def _fetch(self):
        session = self._get_sessid()
        postdata = 'NzbSessionID=%s; NzbSmoke=%s' % (session['NzbSessionID'],session['NzbSmoke'])
        return postdata
    
    def _find_chunk(self, text, start, end, pos=None):
        """ Search through text, finding the chunk between start and end.
        """
        # Can we find the start?
        if pos is None:
            startpos = text.find(start)
        else:
            startpos = text.find(start, pos)
    
        if startpos < 0:
            return None
    
        startspot = startpos + len(start)
    
        # Can we find the end?
        endpos = text.find(end, startspot)
        if endpos <= startspot:
            return None
    
        # Ok, we have some text now
        chunk = text[startspot:endpos]
        if len(chunk) == 0:
            return None
    
        # Return!
        if pos is None:
            return chunk
        else:
            return (endpos+len(end), chunk)


    def _find_chunks(self, text, start, end, limit=0):
        """ As above, but return all matches. Poor man's regexp :)
        """
        chunks = []
        n = 0

        while 1:
            result = self._find_chunk(text, start, end, n)
            if result is None:
                return chunks
            else:
                chunks.append(result[1])
                if limit and len(chunks) == limit:
                    return chunks
                n = result[0]


    def _check_cookie(self, cookie):
        """ Check our cookie, possibly returning the session id
        """
        expiretime = self._find_chunk(cookie, 'expires=', ' GMT')
        dict = {}

        print 'sabnzbd-xbmc timecheck'
        try:
            # Day, dd-mmm-yyyy hh:mm:ss
            t = time.strptime(expiretime, '%a, %d-%b-%Y %H:%M:%S')
        except ValueError:
            # Day, dd mmm yyyy hh:mm:ss
            print 'sabnzbd-xbmc timecheck failed!'
            t = time.strptime(expiretime, '%a, %d %b %Y %H:%M:%S')

        print 'sabnzbd-xbmc checking if expired!'
        now = time.gmtime()
        # Woops, expired
        if now > t: 
            print 'sabnzbd-xbmc expired!'
            return {}

        else:
            print 'sabnzbd-xbmc extract session from cookie!'
            dict['NzbSessionID'] = self._find_chunk(cookie, 'NzbSessionID=', ';')
            dict['NzbSmoke'] = self._find_chunk(cookie, 'NzbSmoke=', ';')
            print 'sabnzbd-xbmc return session info!'
            return dict



    def _fetch_cookie(self, username_newzbin, password_newzbin):
        """ Get the cookie
        """
        try:
            headers = {
                'Referer': 'https://www.newzbin.com',
                'User-Agent': 'SABnzbd XBMC Plugin',
            }

            print 'sabnzbd-xbmc connecting to newzbin.com'
            conn = httplib.HTTPConnection('www.newzbin.com')
            print 'sabnzbd-xbmc connected'

            postdata = urllib.urlencode({'username': username_newzbin,
                                         'password': password_newzbin})
            print 'sabnzbd-xbmc: user/pass:%s' % postdata
            headers['Content-type'] = 'application/x-www-form-urlencoded'
            print 'sabnzbd-xbmc request login'
            conn.request('POST', '/account/login/', postdata, headers)

            print 'sabnzbd-xbmc read response'
            response = conn.getresponse()
            print response.getheader('Set-Cookie')

            #logging.debug("[%s] Response: %s", __NAME__, response.read())

            # Try getting our cookie
            print 'sabnzbd-xbmc try getting our cookie'
            try:
                cookie = response.getheader('Set-Cookie')
            except KeyError:
                print 'sabnzbd-xbmc Login failed1!'
                return None

            # Follow the redirect
            del headers['Content-type']

            print 'sabnzbd-xbmc cookie1: %s' % cookie
            return cookie

        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            return None


    def _get_sessid(self):
        """ Get PHP Session ID
        """
        try:
            cookie_data = self.args.cookie
            dict = {}

            print 'sabnzbd-xbmc Getting SessionInfo'

            if not cookie_data:
                cookie_data = self._get_cookie()

            if cookie_data:
                print 'sabnzbd-xbmc checking cookie!'
                dict = self._check_cookie(cookie_data)
                if not dict:
                    cookie_data = self._get_cookie(check_file=False)
                    dict = self._check_cookie(cookie_data)
                print 'sabnzbd-xbmc checked cookie!'

            return dict

        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            return {}

    def _get_cookie(self, check_file=True):
        cookie_data = None
        cookie_path = _get_path('newzbin_cookie2.txt')

        if check_file and os.access(cookie_path, os.F_OK):
            f = open(cookie_path, 'rb')
            cookie_data = f.read()
            f.close()

        if not cookie_data:
            print 'sabnzbd-xbmc existing cookie not found, requesting new one'
            cookie_data = self._fetch_cookie(username_newzbin, password_newzbin)
            f = open(cookie_path, 'wb')
            f.write(cookie_data)
            f.close()
        else:
            print 'sabnzbd-xbmc existing cookie found!'
        return cookie_data
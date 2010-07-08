# -*- mode: python -*-
"""
    Youtube api client module
"""
import sys
import os
from urllib import urlencode, unquote_plus, quote_plus
import urllib2
import cookielib
import re
import xbmc


class YoutubeClient:
    BASE_STANDARD_URL = 'http://gdata.youtube.com/feeds/api/standardfeeds/%s?%s'
    BASE_SEARCH_URL = 'http://gdata.youtube.com/feeds/api/%s?%s'
    BASE_USERS_URL = 'http://gdata.youtube.com/feeds/api/%s?%s'
    BASE_VIDEO_URL = 'http://www.youtube.com/get_video.php?video_id=%s&t=%s&fmt=35'
    BASE_VIDEO_TOKEN_URL = 'http://www.youtube.com/get_video_info.php?video_id=%s'
    BASE_ID_URL = 'http://www.youtube.com/watch?v=%s'
    BASE_MIDDIO_RANDOM_URL = 'http://middio.com/random'
    BASE_VIDEO_COMMENTS_FEED = 'http://gdata.youtube.com/feeds/api/videos/%s/comments?%s'
    BASE_VIDEO_DETAILS_URL = 'http://gdata.youtube.com/feeds/api/videos/%s?%s'
    BASE_RELATED_URL = 'http://gdata.youtube.com/feeds/api/videos/%s/related?%s'
    BASE_AUTHENTICATE_URI = 'https://www.google.com/youtube/accounts/ClientLogin'
    BASE_LOGIN_URL = 'http://www.youtube.com/signup?hl=en_US&warned=&nomobiletemp=1&next=/&action_login'
    YOUTUBE_CLIENT_ID = ""

    YOUTUBE_DEVELOPER_KEY = "AI39si6yG-eiaR__nzUV-RhgtOr1-0oP6pehRxCEceixhR33P5Qxi05-ZyM_spQ81HpY4qKOfUycwzChhPVESUUbcedlLDI2Xw"

    BASE_COOKIE_PATH = os.path.join( xbmc.translatePath( "special://profile/" ), "addon_data", os.path.basename( os.getcwd() ), 'cookie.txt')
    def __init__(self, base_url = None, authkey = None, email = None):
        self._install_opener()
        self.base_url = base_url
        self.authkey = authkey
        self.email = email

    def _install_opener(self):
        self.cookie_jar = cookielib.LWPCookieJar()
        if os.path.isfile(self.BASE_COOKIE_PATH):
            self.cookie_jar.load(self.BASE_COOKIE_PATH)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie_jar))
        urllib2.install_opener(opener)

    def __getattr__(self, feeds):

        def feeds(_feeds = feeds, **params):
            try:
                true = True
                false = False
                null = None
                if _feeds.startswith('my_') or _feeds.startswith('add_'):
                    _feeds = 'users/default/%s' % (_feeds.split('_')[1],)
                _feeds = _feeds.replace('__', '/%s/')
                if _feeds.startswith('users/%s/'):
                    _feeds = _feeds % (params['author'],)
                    del params['author']
                if _feeds.startswith('related'):
                    _feeds = params['related']
                    del params['related']
                fparams = {}
                for (key, value) in params.items():
                    if value:
                        if (key == 'region_id'):
                            _feeds = '%s/%s' % (value, _feeds)
                        else:
                            fparams[key.replace('__', '-')] = value
                fparams['alt'] = 'json'
                fparams['client'] = self.YOUTUBE_CLIENT_ID
                fparams['key'] = self.YOUTUBE_DEVELOPER_KEY
                if (self.email is not None):
                    fparams['Email'] = self.email
                request = urllib2.Request(self.base_url % (_feeds, urlencode(fparams)))
                if (self.authkey is not None) and (self.authkey != ''):
                    request.add_header('Authorization', 'GoogleLogin auth=%s' % self.authkey)
                usock = urllib2.urlopen(request)
                jsonSource = usock.read()
                usock.close()
                return eval(jsonSource.replace('\\/', '/'))
            except:
                print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
                 , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
                return {}
        return feeds

    def add_favorites(self, video_id):
        try:
            add_request = '<?xml version="1.0" encoding="UTF-8"?><entry xmlns="http://www.w3.org/2005/Atom"><id>%s</id></entry>' % (video_id,)
            request = urllib2.Request(self.base_url % ('users/default/favorites/', ''), add_request)
            if (self.authkey is not None) and (self.authkey != ''):
                request.add_header('Authorization', 'GoogleLogin auth=%s' % self.authkey)
            request.add_header('X-GData-Client', self.YOUTUBE_CLIENT_ID)
            request.add_header('X-GData-Key', 'key=%s' % self.YOUTUBE_DEVELOPER_KEY)
            request.add_header('Content-Type', 'application/atom+xml')
            request.add_header('Content-Length', str(len(add_request)))
            usock = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            if (str(e) == 'HTTP Error 201: Created'):
                return True
        return False

    def delete_favorites(self, delete_url):
        try:
            if (self.authkey is None) or (self.authkey == ''):
                return False
            headers = {}
            headers['Authorization'] = 'GoogleLogin auth=%s' % (self.authkey,)
            headers['X-GData-Client'] = self.YOUTUBE_CLIENT_ID
            headers['X-GData-Key'] = 'key=%s' % self.YOUTUBE_DEVELOPER_KEY
            headers['Content-Type'] = 'application/atom+xml'
            headers['Host'] = 'gdata.youtube.com'
            headers['GData-Version'] = '1'
            import httplib
            conn = httplib.HTTPConnection('gdata.youtube.com')
            conn.request('DELETE', delete_url, headers=headers)
            response = conn.getresponse()
            if (response.status == 200):
                return True
        except:
            print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
             , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
        return False

    def get_comments(self, video_id, **params):
        try:
            true = True
            false = False
            null = None
            fparams = {}
            for (key, value) in params.items():
                if value:
                    fparams[key.replace('__', '-')] = value
            fparams['alt'] = 'json'
            fparams['client'] = self.YOUTUBE_CLIENT_ID
            fparams['key'] = self.YOUTUBE_DEVELOPER_KEY
            request = urllib2.Request(self.BASE_VIDEO_DETAILS_URL % (video_id, urlencode(fparams)))
            #request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)')
            if (self.authkey is not None) and (self.authkey != ''):
                request.add_header('Authorization', 'GoogleLogin auth=%s' % self.authkey)
            usock = urllib2.urlopen(request)
            jsonSource = usock.read()
            usock.close()
            comments = eval(jsonSource.replace('\\/', '/'))
            return comments['feed']['entry']
        except:
            print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
             , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
            return []

    def get_details(self, video_id, **params):
        try:
            true = True
            false = False
            null = None
            fparams = {}
            for (key, value) in params.items():
                if value:
                    fparams[key.replace('__', '-')] = value
            fparams['alt'] = 'json'
            fparams['client'] = self.YOUTUBE_CLIENT_ID
            fparams['key'] = self.YOUTUBE_DEVELOPER_KEY
            request = urllib2.Request(self.BASE_VIDEO_DETAILS_URL % (video_id, urlencode(fparams)))
            if (self.authkey is not None) and (self.authkey != ''):
                request.add_header('Authorization', 'GoogleLogin auth=%s' % self.authkey)
            usock = urllib2.urlopen(request)
            jsonSource = usock.read()
            usock.close()
            details = eval(jsonSource.replace('\\/', '/'))
            encoding = details['encoding']
            exec 'title = u"%s"' % (
             unicode(details['entry']['title']['$t'].replace('"', '\\"'), encoding, 'replace'),)
            exec 'author = u"%s"' % (
             unicode(details['entry']['author'][0]['name']['$t'].replace('"', '\\"'), encoding, 'replace'),)
            genre = details['entry']['media$group']['media$category'][0]['$t']
            try:
                rating = float(details['entry']['gd$rating']['average'])
            except:
                rating = 0.0
            runtime = int(details['entry']['media$group']['yt$duration']['seconds'])
            if runtime:
                runtime = '%02d:%02d' % (int(runtime / 60), runtime % 60)
            else:
                runtime = ''
            try:
                count = int(details['entry']['yt$statistics']['viewCount'])
            except:
                count = 0
            date = '%s-%s-%s' % (details['entry']['updated']['$t'][8:10]
             , details['entry']['updated']['$t'][5:7], details['entry']['updated']['$t'][:4])
            thumbnail_url = details['entry']['media$group']['media$thumbnail'][-1]['url']
            plot = ''
            if ('media$description' in details['entry']['media$group']):
                exec 'plot = u"%s"' % (
                 unicode(details['entry']['media$group']['media$description']['$t'].replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r'), encoding, 'replace'),)
            return (title, author, genre, rating, runtime, count, date
             , thumbnail_url, plot)
        except:
            print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
             , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
            return [''] * 9

    def construct_video_url_keepvid(self, url, quality = 18, encoding = 'utf-8'):
        try:
            url = unquote_plus(url)
            video_id = url.split('v=')[1]
            url = 'http://keepvid.com/?url=' + quote_plus(url)
            xbmc.log("[PLUGIN] '%s: version %s' - (quality=%d, video url=%s)" % (sys.modules['__main__'].__plugin__
                 , sys.modules['__main__'].__version__, quality, url), xbmc.LOGDEBUG)
            request = urllib2.Request(url)
            #request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)')
            opener = urllib2.urlopen(request)
            htmlSource = opener.read()
            opener.close()
            video_url = unquote_plus(re.findall('<a href="/save-video.mp4?(.+?)"', htmlSource)[0])[1:]
            (title, author, genre, rating, runtime, count, date, thumbnail_url, plot) = self.get_details(video_id)
            return (video_url, title, author, genre, rating, runtime, count, date
             , thumbnail_url, plot, video_id)
        except:
            print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
             , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
            return [''] * 11

    def construct_video_url(self, url, quality = 18, encoding = 'utf-8'):
        try:
            video_url = self.BASE_VIDEO_TOKEN_URL % (unquote_plus(url).split('v=')[1],)
            xbmc.log("[PLUGIN] '%s: version %s' - (quality=%d, video url=%s)" % (sys.modules['__main__'].__plugin__, sys.modules['__main__'].__version__, quality, url), xbmc.LOGDEBUG)
            request = urllib2.Request(video_url)
            #request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)')
            opener = urllib2.urlopen(request)
            htmlSource = opener.read()
            opener.close()
            video_url = None
            if htmlSource.startswith('status=fail&errorcode=150'):
                request = urllib2.Request(url)
                #request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)')
                opener = urllib2.urlopen(request)
                htmlSource = opener.read()
                opener.close()
                video_id = re.findall('"video_id": "([^"]+)"', htmlSource)[0]
                try:
                    fmt_url_map = unquote_plus(re.findall('"fmt_url_map": "([^"]+)"', htmlSource)[0]).split(',')
                except:
                    token = re.findall('"t": "([^"]+)"', htmlSource)[0]
                    video_url = self.BASE_VIDEO_URL % (video_id, token)
            else:
                video_id = re.findall('&video_id=([^&]+)', htmlSource)[0]
                fmt_url_map = unquote_plus(re.findall('&fmt_url_map=([^&]+)', htmlSource)[0]).split(',')
            if (video_url is None):
                for url in fmt_url_map:
                    if (quality == 22) and url.startswith('22|'):
                            video_url = url.split('|')[1]
                            break
                    elif (url.startswith('35|')
                          or url.startswith('34|') or url.startswith('18|')):
                        video_url = url.split('|')[1]
                        break
            (title, author, genre, rating, runtime, count, date, thumbnail_url, plot) = self.get_details(video_id)
            return (video_url, title, author, genre, rating, runtime, count, date
                     , thumbnail_url, plot, video_id)
        except:
            print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
             , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
            return [''] * 11

    def get_random_middio_video(self, quality = 0):
        try:
            request = urllib2.Request(self.BASE_MIDDIO_RANDOM_URL)
            opener = urllib2.urlopen(request)
            htmlSource = opener.read()
            opener.close()
            id_start = htmlSource.find('http://www.youtube.com/watch?v=')
            id_end = htmlSource.find('"', id_start + 1)
            video_id = htmlSource[id_start + 1:id_end].split('=')[1]
            (url, title, author, genre, rating, runtime, count, date, thumbnail_url, plot, vidoe_id) = self.construct_video_url(self.BASE_ID_URL % (video_id,), quality)
            return (url, title, author, genre, rating, runtime, count, date, thumbnail_url
             , plot)
        except:
            print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
             , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
            return [''] * 10

    def authenticate(self, user_id, user_password):
        try:
            auth_request = {'Email': user_id,
             'Passwd': user_password,
             'service': 'youtube',
             'source': 'You Tube plugin'}
            request = urllib2.Request(self.BASE_AUTHENTICATE_URI, urlencode(auth_request))
            request.add_header('Content-Type', 'application/x-www-form-urlencoded')
            opener = urllib2.urlopen(request)
            data = opener.read()
            opener.close()
            authkey = re.findall('Auth=(.+)', data)[0]
            userid = re.findall('YouTubeUser=(.+)', data)[0]
            self._login(user_id, user_password)
            return (authkey, userid)
        except:
            print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
             , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
            return ('', '')

    def _login(self, user_id, user_password):
        try:
            login_request = {'current_form': 'loginForm',
             'username': user_id,
             'password': user_password,
             'action_login': 'Log In'}
            request = urllib2.Request(self.BASE_LOGIN_URL, urlencode(login_request))
            #request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)')
            opener = urllib2.urlopen(request)
            data = opener.read()
            opener.close()
            self.cookie_jar.save(self.BASE_COOKIE_PATH)
        except:
            print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
             , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])


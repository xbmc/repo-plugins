# -*- encoding: utf-8 -*-

import sys

import cookielib
import gzip
try:
    import hashlib
except:
    import md5 as hashlib
import os, os.path
import tempfile
import time
import urllib
import urllib2
import shutil
import StringIO
import socket
socket.setdefaulttimeout(15)

try:
    import json
except:
    import simplejson as json


class SoapException(Exception):
    pass


class SoapCache(object):
    def __init__(self, path, lifetime=30):
        self.path = os.path.join(path, "cache")
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        self.lifetime = lifetime

    def get(self, cache_id, use_lifetime=True):
        filename = os.path.join(self.path, str(cache_id))
        if not os.path.exists(filename) or not os.path.isfile(filename):
            return False

        max_time = time.time() - self.lifetime * 60
        if use_lifetime and self and os.path.getmtime(filename) <= max_time:
            return False

        with open(filename, "r") as f:
            return f.read()

    def set(self, cache_id, text):
        filename = os.path.join(self.path, str(cache_id))
        with open(filename, "w") as f:
            f.write(text)


class SoapApi(object):

    HOST = "http://soap4.me"

    def __init__(self, path=None, auth=None):
        if path == "__init__":
            path = tempfile.gettempdir()
            path = os.path.join(path, 'soap4kobi')
            if not os.path.exists(path):
                os.makedirs(path)
        self.path = path
        self.token = None
        self.auth = auth
        self.till_days = None

        if path is not None:
            self.cache = SoapCache(path, 15)
            self.CJ = cookielib.CookieJar()
        else:
            self.cache = None
            self.CJ = None

    def _cookies_init(self):
        if self.CJ is None:
            return

        urllib2.install_opener(
            urllib2.build_opener(
                urllib2.HTTPCookieProcessor(self.CJ)
            )
        )

        self.cookie_path = os.path.join(self.path, 'cookies')
        if not os.path.exists(self.cookie_path):
            os.makedirs(self.cookie_path)
            #print '[%s]: os.makedirs(cookie_path=%s)' % (addon_id, cookie_path)

    def _cookies_load(self, req):
        if self.CJ is None:
            return

        cookie_send = {}
        for cookie_fname in os.listdir(self.cookie_path):
            cookie_file = os.path.join(self.cookie_path, cookie_fname)
            if os.path.isfile(cookie_file):
                cf = open(cookie_file, 'r')
                cookie_send[os.path.basename(cookie_file)] = cf.read()
                cf.close()
            #else: print '[%s]: NOT os.path.isfile(cookie_file=%s)' % (addon_id, cookie_file)

        cookie_string = urllib.urlencode(cookie_send).replace('&','; ')
        req.add_header('Cookie', cookie_string)

    def _cookies_save(self):
        if self.CJ is None:
            return

        for Cook in self.CJ:
            cookie_file = os.path.join(self.cookie_path, Cook.name)
            cf = open(cookie_file, 'w')
            cf.write(Cook.value)
            cf.close()

    def _request(self, url, post=None, use_token=True):
        if not isinstance(post, dict):
            post = None

        self._cookies_init()

        req = urllib2.Request(url)
        req.add_header('User-Agent', 'xbmc for soap')
        req.add_header('Accept-encoding', 'gzip')
        req.add_header('x-im-raspberry', 'yes')

        if use_token and self.token is not None:
            req.add_header('x-api-token', self.token)

        if post is not None:
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')

        if use_token:
            self._cookies_load(req)

        post_data = None
        if post is not None:
            post_data = urllib.urlencode(post)

        response = urllib2.urlopen(req, post_data)

        self._cookies_save()

        text = None
        if response.info().get('Content-Encoding') == 'gzip':
            buffer = StringIO.StringIO(response.read())
            fstream = gzip.GzipFile(fileobj=buffer)
            text = fstream.read()
        else:
            text = response.read()
            response.close()

        return text

    def delete_token(self):
        self._save_token({'token': '', 'till': 0})

    def _save_token(self, data):
        token_path = os.path.join(self.path, "token")
        with open(token_path, "w") as f:
            f.write(json.dumps(data))

    def _load_token(self, from_login=False):

        def load():
            token_path = os.path.join(self.path, "token")
            if not os.path.exists(token_path):
                return False

            if os.path.getmtime(token_path) + 86400 * 7 < time.time():
                return False

            with open(token_path, "r") as f:
                dump = f.read()
                data = json.loads(dump)

            if data.get('token') is None or data.get('till', time.time() + 10) <= time.time():
                return False

            self.token = data.get('token')
            self.till_days = int((int(data.get('till')) - time.time()) / 86400)
            return True

        if not load():
            if from_login or self.auth is None:
                raise SoapException("Bad authorization. Token process.")

            self.delete_token()
            self.login()

    @classmethod
    def check_login(cls, username=None, password=None):
        s = cls()
        try:
            return s.login(username, password, only_check=True)
        except SoapException as e:
            return False

    def login(self, username=None, password=None, only_check=False):
        if username is None and password is None and self.auth is not None \
                and 'username' in self.auth and 'password' in self.auth:
            username = self.auth['username']
            password = self.auth['password']

        if username is None or password is None:
            raise SoapException("Bad authorization. Login process.")


        text = self._request(
            self.HOST + "/login/",
            post={"login": username, "password": password},
            use_token=False
        )

        data = json.loads(text)

        if not isinstance(data, dict) or data.get('ok') != 1:
            raise SoapException("Bad authorization. Soap4.me process.")

        if only_check:
            return True

        self._save_token(data)
        self._load_token(True)

    def list(self, sfilter="all", sid=None):
        def request():
            self._load_token()

            if sid is None:
                if sfilter == "my":
                    url = "/api/soap/my/"
                else:
                    url = "/api/soap/"
            else:
                url = "/api/episodes/{0}/".format(sid)

            cache_id = filter(lambda c: c not in ",./", url)
            text = self.cache.get(cache_id)

            if text != False:
                return text

            text = self._request(self.HOST + url)
            self.cache.set(cache_id, text)

            return text

        text = request()
        data = json.loads(text)

        if isinstance(data, dict) \
                and data.get('ok', 'None') == 0 \
                and data.get('error', '') != '':
            self.delete_token()
            text = request()
            data = json.loads(text)

        return data

    def time_position_save(self, eid, position):
        if self.cache:
            self.cache.set("pos_{0}".format(eid), position)

    def time_position_delete(self, eid):
        if self.cache:
            self.cache.set("pos_{0}".format(eid), "")

    def time_position_get(self, eid):
        if self.cache:
            pos = self.cache.get("pos_{0}".format(eid), use_lifetime=False)
            if pos is False or pos is "":
                return

            return pos

    def mark_watched(self, eid):
        self._load_token()

        text = self._request(self.HOST + "/callback/", {
            "what": "mark_watched",
            "eid": str(eid),
            "token": self.token
        })
        data = json.loads(text)

        return isinstance(data, dict) and data.get('ok', 0) == 1

    def list_all(self):
        return self.list("all")

    def list_my(self):
        return self.list("my")

    def list_episodes(self, row=None, sid=None,):
        if sid is None and (row is None or 'sid' not in row):
            raise SoapException("Bad serial row.")

        return self.list(sid=sid or row['sid'])

    def _get_video(self, sid, eid, ehash):
        self._load_token()
        myhash = hashlib.md5(
            str(self.token) + \
            str(eid) + \
            str(sid) + \
            str(ehash)
        ).hexdigest()

        data = {
            "what": "player",
            "do": "load",
            "token": self.token,
            "eid": eid,
            "hash": myhash
        }
        url = self.HOST + "/callback/"
        result = self._request(url, data)

        data = json.loads(result)
        if not isinstance(data, dict) or data.get("ok", 0) == 0:
            raise SoapException("Bad getting videolink")

        return "http://%s.soap4.me/%s/%s/%s/" % (data['server'], self.token, eid, myhash)

    def get_video(self, row):
        if 'sid' not in row or 'eid' not in row or 'hash' not in row:
            raise SoapException("Bad episode row.")

        return self._get_video(row['sid'], row['eid'], row['hash'])

    def get_till_days(self):
        self._load_token()
        return self.till_days

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Use: python soapapi.py <login> <password>"
        exit(0)

    path = os.path.abspath(".")
    path = os.path.join(path, "soap4_data")
    #if os.path.exists(path):
    #    shutil.rmtree(path)
    #os.makedirs(path)

    s = SoapApi(path, auth={
        "username": sys.argv[1],
        "password": sys.argv[2]
    })
    data = s.list_all()
    print len(data)

    data = s.list_episodes(data[4])

    print len(data)
    print s.get_video(data[2])
    print s.get_till_days()

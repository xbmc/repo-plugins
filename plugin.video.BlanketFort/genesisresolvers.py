# -*- coding: utf-8 -*-

'''
    Genesis Add-on
    Copyright (C) 2015 lambda

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
'''

import urllib,urllib2,urlparse,re,os,sys,xbmc,xbmcgui,xbmcaddon,xbmcvfs

try:
    import CommonFunctions as common
except:
    import commonfunctionsdummy as common
try:
    import json
except:
    import simplejson as json


class get(object):
    def __init__(self, url):
        self.result = self.worker(url)

    def worker(self, url):
        try:
            pz = premiumize().resolve(url)
            if not pz == None: return pz
            rd = realdebrid().resolve(url)
            if not rd == None: return rd

            if url.startswith('rtmp'):
                if len(re.compile('\s*timeout=(\d*)').findall(url)) == 0: url += ' timeout=10'
                return url

            u = urlparse.urlparse(url).netloc
            u = u.replace('www.', '').replace('embed.', '')
            u = u.lower()

            import sys, inspect
            r = inspect.getmembers(sys.modules[__name__], inspect.isclass)
            r = [i for i in r if hasattr(i[1], 'info') and u in eval(i[0])().info()['netloc']][0][0]
            r = eval(r)().resolve(url)

            if r == None: return r
            elif type(r) == list: return r
            elif not r.startswith('http'): return r

            try: h = dict(urlparse.parse_qsl(r.rsplit('|', 1)[1]))
            except: h = dict('')
            h.update({'Referer': url, 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:34.0) Gecko/20100101 Firefox/34.0'})

            r = '%s|%s' % (r.split('|')[0], urllib.urlencode(h))
            return r
        except:
            return url


class getUrl(object):
    def __init__(self, url, close=True, proxy=None, post=None, headers=None, mobile=False, referer=None, cookie=None, output='', timeout='10'):
        handlers = []
        if not proxy == None:
            handlers += [urllib2.ProxyHandler({'http':'%s' % (proxy)}), urllib2.HTTPHandler]
            opener = urllib2.build_opener(*handlers)
            opener = urllib2.install_opener(opener)
        if output == 'cookie' or not close == True:
            import cookielib
            cookies = cookielib.LWPCookieJar()
            handlers += [urllib2.HTTPHandler(), urllib2.HTTPSHandler(), urllib2.HTTPCookieProcessor(cookies)]
            opener = urllib2.build_opener(*handlers)
            opener = urllib2.install_opener(opener)
        try:
            if sys.version_info < (2, 7, 9): raise Exception()
            import ssl; ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            handlers += [urllib2.HTTPSHandler(context=ssl_context)]
            opener = urllib2.build_opener(*handlers)
            opener = urllib2.install_opener(opener)
        except:
            pass
        try: headers.update(headers)
        except: headers = {}
        if 'User-Agent' in headers:
            pass
        elif not mobile == True:
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; rv:34.0) Gecko/20100101 Firefox/34.0'
        else:
            headers['User-Agent'] = 'Apple-iPhone/701.341'
        if 'referer' in headers:
            pass
        elif referer == None:
            headers['referer'] = url
        else:
            headers['referer'] = referer
        if not 'Accept-Language' in headers:
            headers['Accept-Language'] = 'en-US'
        if 'cookie' in headers:
            pass
        elif not cookie == None:
            headers['cookie'] = cookie
        request = urllib2.Request(url, data=post, headers=headers)
        response = urllib2.urlopen(request, timeout=int(timeout))
        if output == 'cookie':
            result = []
            for c in cookies: result.append('%s=%s' % (c.name, c.value))
            result = "; ".join(result)
        elif output == 'geturl':
            result = response.geturl()
        else:
            result = response.read()
        if close == True:
            response.close()
        self.result = result

class captcha:
    def worker(self, data):
        self.captcha = {}

        self.solvemedia(data)
        if not self.type == None: return self.captcha

        self.recaptcha(data)
        if not self.type == None: return self.captcha

        self.capimage(data)
        if not self.type == None: return self.captcha

        self.numeric(data)
        if not self.type == None: return self.captcha

    def solvemedia(self, data):
        try:
            url = common.parseDOM(data, "iframe", ret="src")
            url = [i for i in url if 'api.solvemedia.com' in i]

            if len(url) > 0: self.type = 'solvemedia'
            else: self.type = None ; return

            result = getUrl(url[0], referer='').result

            response = common.parseDOM(result, "iframe", ret="src")
            response += common.parseDOM(result, "img", ret="src")
            response = [i for i in response if '/papi/media' in i][0]
            response = 'http://api.solvemedia.com' + response
            response = self.keyboard(response)

            post = {}
            f = common.parseDOM(result, "form", attrs = { "action": "verify.noscript" })[0]
            k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post.update({'adcopy_response': response})

            getUrl('http://api.solvemedia.com/papi/verify.noscript', post=urllib.urlencode(post)).result

            self.captcha.update({'adcopy_challenge': post['adcopy_challenge'], 'adcopy_response': 'manual_challenge'})
        except:
            pass

    def recaptcha(self, data):
        try:
            url = []
            if data.startswith('http://www.google.com'): url += [data]
            url += common.parseDOM(data, "script", ret="src", attrs = { "type": "text/javascript" })
            url = [i for i in url if 'http://www.google.com' in i]

            if len(url) > 0: self.type = 'recaptcha'
            else: self.type = None ; return

            result = getUrl(url[0]).result
            challenge = re.compile("challenge\s+:\s+'(.+?)'").findall(result)[0]
            response = 'http://www.google.com/recaptcha/api/image?c=' + challenge
            response = self.keyboard(response)

            self.captcha.update({'recaptcha_challenge_field': challenge, 'recaptcha_challenge': challenge, 'recaptcha_response_field': response, 'recaptcha_response': response})
        except:
            pass

    def capimage(self, data):
        try:
            url = common.parseDOM(data, "img", ret="src")
            url = [i for i in url if 'captcha' in i]

            if len(url) > 0: self.type = 'capimage'
            else: self.type = None ; return

            response = self.keyboard(url[0])
            self.captcha.update({'code': response})
        except:
            pass

    def numeric(self, data):
        try:
            url = re.compile("left:(\d+)px;padding-top:\d+px;'>&#(.+?);<").findall(data)

            if len(url) > 0: self.type = 'numeric'
            else: self.type = None ; return

            result = sorted(url[0], key=lambda ltr: int(ltr[0]))
            response = ''.join(str(int(num[1])-48) for num in result)

            self.captcha.update({'code': response})
        except:
            pass

    def keyboard(self, response):
        try:
            dataPath = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo("profile"))
            i = os.path.join(dataPath.decode("utf-8"),'img')
            f = xbmcvfs.File(i, 'w')
            f.write(getUrl(response).result)
            f.close()
            f = xbmcgui.ControlImage(450,5,375,115, i)
            d = xbmcgui.WindowDialog()
            d.addControl(f)
            xbmcvfs.delete(i)
            d.show()
            xbmc.sleep(3000)
            t = 'Type the letters in the image'
            c = common.getUserInput(t, '')
            d.close()
            return c
        except:
            return

class regex:
    def worker(self, data):
        try:
            data = str(data).replace('\r','').replace('\n','').replace('\t','')

            url = re.compile('(.+?)<regex>').findall(data)[0]
            regex = re.compile('<regex>(.+?)</regex>').findall(data)
        except:
            return

        for x in regex:
            try:
                name = re.compile('<name>(.+?)</name>').findall(x)[0]

                expres = re.compile('<expres>(.+?)</expres>').findall(x)[0]

                referer = re.compile('<referer>(.+?)</referer>').findall(x)[0]
                referer = urllib.unquote_plus(referer)
                referer = common.replaceHTMLCodes(referer)
                referer = referer.encode('utf-8')

                page = re.compile('<page>(.+?)</page>').findall(x)[0]
                page = urllib.unquote_plus(page)
                page = common.replaceHTMLCodes(page)
                page = page.encode('utf-8')

                result = getUrl(page, referer=referer).result
                result = str(result).replace('\r','').replace('\n','').replace('\t','')
                result = str(result).replace('\/','/')

                r = re.compile(expres).findall(result)[0]
                url = url.replace('$doregex[%s]' % name, r)
            except:
                pass

        url = common.replaceHTMLCodes(url)
        url = url.encode('utf-8')
        return url

class unwise:
    def worker(self, str_eval):
        page_value=""
        try:        
            ss="w,i,s,e=("+str_eval+')' 
            exec (ss)
            page_value=self.__unwise(w,i,s,e)
        except: return
        return page_value

    def __unwise(self,  w, i, s, e):
        lIll = 0;
        ll1I = 0;
        Il1l = 0;
        ll1l = [];
        l1lI = [];
        while True:
            if (lIll < 5):
                l1lI.append(w[lIll])
            elif (lIll < len(w)):
                ll1l.append(w[lIll]);
            lIll+=1;
            if (ll1I < 5):
                l1lI.append(i[ll1I])
            elif (ll1I < len(i)):
                ll1l.append(i[ll1I])
            ll1I+=1;
            if (Il1l < 5):
                l1lI.append(s[Il1l])
            elif (Il1l < len(s)):
                ll1l.append(s[Il1l]);
            Il1l+=1;
            if (len(w) + len(i) + len(s) + len(e) == len(ll1l) + len(l1lI) + len(e)):
                break;
            
        lI1l = ''.join(ll1l)
        I1lI = ''.join(l1lI)
        ll1I = 0;
        l1ll = [];
        for lIll in range(0,len(ll1l),2):
            ll11 = -1;
            if ( ord(I1lI[ll1I]) % 2):
                ll11 = 1;
            l1ll.append(chr(    int(lI1l[lIll: lIll+2], 36) - ll11));
            ll1I+=1;
            if (ll1I >= len(l1lI)):
                ll1I = 0;
        ret=''.join(l1ll)
        if 'eval(function(w,i,s,e)' in ret:
            ret=re.compile('eval\(function\(w,i,s,e\).*}\((.*?)\)').findall(ret)[0] 
            return self.worker(ret)
        else:
            return ret

class js:
    def worker(self, script):
        aSplit = script.split(";',")
        p = str(aSplit[0])
        aSplit = aSplit[1].split(",")
        a = int(aSplit[0])
        c = int(aSplit[1])
        k = aSplit[2].split(".")[0].replace("'", '').split('|')
        e = ''
        d = ''

        sUnpacked = str(self.__unpack(p, a, c, k, e, d))
        sUnpacked = sUnpacked.replace('\\', '')

        url = self.__parse(sUnpacked)
        return url

    def __unpack(self, p, a, c, k, e, d):
        while (c > 1):
            c = c -1
            if (k[c]):
                p = re.sub('\\b' + str(self.__itoa(c, a)) +'\\b', k[c], p)
        return p

    def __itoa(self, num, radix):
        result = ""
        while num > 0:
            result = "0123456789abcdefghijklmnopqrstuvwxyz"[num % radix] + result
            num /= radix
        return result

    def __parse(self, sUnpacked):
        url = re.compile("'file' *, *'(.+?)'").findall(sUnpacked)
        url += re.compile("file *: *[\'|\"](.+?)[\'|\"]").findall(sUnpacked)
        url += re.compile("playlist=(.+?)&").findall(sUnpacked)
        url += common.parseDOM(sUnpacked, "embed", ret="src")

        url = [i for i in url if not i.endswith('.srt')]

        url = 'http://' + url[-1].split('://', 1)[-1]
        return url


class premiumize:
    def __init__(self):
        self.user = xbmcaddon.Addon().getSetting("premiumize_user")
        self.password = xbmcaddon.Addon().getSetting("premiumize_password")

    def info(self):
        return {
            'netloc': ['bitshare.com', 'filefactory.com', 'k2s.cc', 'oboom.com', 'rapidgator.net', 'uploaded.net'],
            'host': ['Bitshare', 'Filefactory', 'K2S', 'Oboom', 'Rapidgator', 'Uploaded'],
            'quality': 'High',
            'captcha': False,
            'a/c': True
        }

    def status(self):
        if (self.user == '' or self.password == ''): return False
        else: return True

    def hosts(self):
        try:
            if self.status() == False: raise Exception()

            url = 'http://api.premiumize.me/pm-api/v1.php?method=hosterlist&params[login]=%s&params[pass]=%s' % (self.user, self.password)

            result = getUrl(url).result

            pz = json.loads(result)['result']['hosterlist']
            pz = [i.rsplit('.' ,1)[0].lower() for i in pz]
            return pz
        except:
            return

    def resolve(self, url):
        try:
            if self.status() == False: raise Exception()

            url = 'http://api.premiumize.me/pm-api/v1.php?method=directdownloadlink&params[login]=%s&params[pass]=%s&params[link]=%s' % (self.user, self.password, urllib.quote_plus(url))

            result = getUrl(url, close=False).result

            url = json.loads(result)['result']['location']
            return url
        except:
            return

class realdebrid:
    def __init__(self):
        self.user = xbmcaddon.Addon().getSetting("realdedrid_user")
        self.password = xbmcaddon.Addon().getSetting("realdedrid_password")

    def info(self):
        return {
            'netloc': ['bitshare.com', 'filefactory.com', 'k2s.cc', 'oboom.com', 'rapidgator.net', 'uploaded.net'],
            'host': ['Bitshare', 'Filefactory', 'K2S', 'Oboom', 'Rapidgator', 'Uploaded'],
            'quality': 'High',
            'captcha': False,
            'a/c': True
        }

    def status(self):
        if (self.user == '' or self.password == ''): return False
        else: return True

    def hosts(self):
        try:
            if self.status() == False: raise Exception()

            url = 'http://real-debrid.com/api/hosters.php'

            result = getUrl(url).result

            rd = json.loads('[%s]' % result)
            rd = [i.rsplit('.' ,1)[0].lower() for i in rd]
            return rd
        except:
            return

    def resolve(self, url):
        try:
            if self.status() == False: raise Exception()

            login_data = urllib.urlencode({'user' : self.user, 'pass' : self.password})
            login_link = 'http://real-debrid.com/ajax/login.php?%s' % login_data
            result = getUrl(login_link, close=False).result
            result = json.loads(result)
            error = result['error']
            if not error == 0: raise Exception()

            url = 'http://real-debrid.com/ajax/unrestrict.php?link=%s' % url
            url = url.replace('filefactory.com/stream/', 'filefactory.com/file/')
            result = getUrl(url).result
            result = json.loads(result)
            url = result['generated_links'][0][-1]
            return url
        except:
            return


class _180upload:
    def info(self):
        return {
            'netloc': ['180upload.com'],
            'host': ['180upload'],
            'quality': 'High',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://180upload.com/embed-%s.html' % url

            result = getUrl(url).result

            post = {}
            f = common.parseDOM(result, "form", attrs = { "id": "captchaForm" })[0]
            k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post = urllib.urlencode(post)

            result = getUrl(url, post=post).result

            result = re.compile('(eval.*?\)\)\))').findall(result)[-1]
            url = js().worker(result)
            return url
        except:
            return

class allmyvideos:
    def info(self):
        return {
            'netloc': ['allmyvideos.net'],
            'host': ['Allmyvideos'],
            'quality': 'Medium',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://allmyvideos.net/embed-%s.html' % url

            result = getUrl(url, mobile=True).result
            url = re.compile('"file" *: *"(http.+?)"').findall(result)[-1]
            return url
        except:
            return

class bestreams:
    def info(self):
        return {
            'netloc': ['bestreams.net'],
            'host': ['Bestreams'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://bestreams.net/embed-%s.html' % url

            result = getUrl(url, mobile=True).result
            url = re.compile('file *: *"(http.+?)"').findall(result)[-1]
            return url
        except:
            return

class clicknupload:
    def info(self):
        return {
            'netloc': ['clicknupload.com'],
            'host': ['Clicknupload'],
            'quality': 'High',
            'captcha': True,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url).result

            post = {}
            f = common.parseDOM(result, "Form", attrs = { "action": "" })
            k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post.update({'method_free': 'Free Download'})
            post = urllib.urlencode(post)

            result = getUrl(url, post=post).result

            post = {}
            f = common.parseDOM(result, "Form", attrs = { "action": "" })
            k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post.update({'method_free': 'Free Download'})
            post.update(captcha().worker(result))
            post = urllib.urlencode(post)

            result = getUrl(url, post=post).result

            url = common.parseDOM(result, "a", ret="onClick")
            url = [i for i in url if i.startswith('window.open')][0]
            url = re.compile('[\'|\"](.+?)[\'|\"]').findall(url)[0]
            return url
        except:
            return

class cloudzilla:
    def info(self):
        return {
            'netloc': ['cloudzilla.to'],
            'host': ['Cloudzilla'],
            'quality': 'Medium',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/share/file/', '/embed/')
            result = getUrl(url).result
            url = re.compile('var\s+vurl *= *"(http.+?)"').findall(result)[0]
            return url
        except:
            return

class coolcdn:
    def info(self):
        return {
            'netloc': ['movshare.net', 'novamov.com', 'nowvideo.sx', 'videoweed.es'],
            'host': ['Movshare', 'Novamov', 'Nowvideo', 'Videoweed'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            netloc = urlparse.urlparse(url).netloc
            netloc = netloc.replace('www.', '').replace('embed.', '')
            netloc = netloc.lower()

            id = re.compile('//.+?/.+?/([\w]+)').findall(url)
            id += re.compile('//.+?/.+?v=([\w]+)').findall(url)
            id = id[0]

            url = 'http://embed.%s/embed.php?v=%s' % (netloc, id)

            result = getUrl(url).result

            key = re.compile('flashvars.filekey=(.+?);').findall(result)[-1]
            try: key = re.compile('\s+%s="(.+?)"' % key).findall(result)[-1]
            except: pass

            url = 'http://www.%s/api/player.api.php?key=%s&file=%s' % (netloc, key, id)
            result = getUrl(url).result

            url = re.compile('url=(.+?)&').findall(result)[0]
            return url
        except:
            return

class daclips:
    def info(self):
        return {
            'netloc': ['daclips.in'],
            'host': ['Daclips'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url, mobile=True).result
            url = re.compile('file *: *"(http.+?)"').findall(result)[-1]
            return url
        except:
            return

class datemule:
    def info(self):
        return {
            'netloc': ['datemule.com']
        }

    def resolve(self, url):
        try:
            result = getUrl(url, mobile=True).result
            url = re.compile('file *: *"(http.+?)"').findall(result)[0]
            return url
        except:
            return

class fastvideo:
    def info(self):
        return {
            'netloc': ['fastvideo.in', 'faststream.in'],
            'host': ['Fastvideo', 'Faststream'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://fastvideo.in/embed-%s.html' % url

            result = getUrl(url, mobile=True).result
            url = re.compile('file *: *"(http.+?)"').findall(result)[-1]
            return url
        except:
            return

class filehoot:
    def info(self):
        return {
            'netloc': ['filehoot.com'],
            'host': ['Filehoot'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://filehoot.com/embed-%s.html' % url

            result = getUrl(url, mobile=True).result
            url = re.compile('file *: *"(http.+?)"').findall(result)[0]
            return url
        except:
            return

class filenuke:
    def info(self):
        return {
            'netloc': ['filenuke.com', 'sharesix.com'],
            'host': ['Filenuke', 'Sharesix'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url).result
            post = {}
            try: f = common.parseDOM(result, "form", attrs = { "method": "POST" })[0]
            except: f = ''
            k = common.parseDOM(f, "input", ret="name")
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post = urllib.urlencode(post)

            result = getUrl(url, post=post).result

            url = re.compile("var\s+lnk\d* *= *'(http.+?)'").findall(result)[0]
            return url
        except:
            return

class googledocs:
    def info(self):
        return {
            'netloc': ['docs.google.com', 'drive.google.com']
        }

    def resolve(self, url):
        try:
            url = url.split('/preview', 1)[0]
            url = url.replace('drive.google.com', 'docs.google.com')

            result = getUrl(url).result
            result = re.compile('"fmt_stream_map",(".+?")').findall(result)[0]

            u = json.loads(result)
            u = [i.split('|')[-1] for i in u.split(',')]
            u = sum([self.tag(i) for i in u], [])

            url = []
            try: url += [[i for i in u if i['quality'] == '1080p'][0]]
            except: pass
            try: url += [[i for i in u if i['quality'] == 'HD'][0]]
            except: pass
            try: url += [[i for i in u if i['quality'] == 'SD'][0]]
            except: pass

            if url == []: return
            return url
        except:
            return

    def tag(self, url):
        quality = re.compile('itag=(\d*)').findall(url)
        quality += re.compile('=m(\d*)$').findall(url)
        try: quality = quality[0]
        except: return []

        if quality in ['37', '137', '299', '96', '248', '303', '46']:
            return [{'quality': '1080p', 'url': url}]
        elif quality in ['22', '84', '136', '298', '120', '95', '247', '302', '45', '102']:
            return [{'quality': 'HD', 'url': url}]
        elif quality in ['35', '44', '135', '244', '94']:
            return [{'quality': 'SD', 'url': url}]
        elif quality in ['18', '34', '43', '82', '100', '101', '134', '243', '93']:
            return [{'quality': 'SD', 'url': url}]
        elif quality in ['5', '6', '36', '83', '133', '242', '92', '132']:
            return [{'quality': 'SD', 'url': url}]
        else:
            return []

class googleplus:
    def info(self):
        return {
            'netloc': ['plus.google.com', 'picasaweb.google.com']
        }

    def resolve(self, url):
        try:
            if 'picasaweb' in url.lower():
                result = getUrl(url).result
                aid = re.compile('aid=(\d*)').findall(result)[0]

                pid = urlparse.urlparse(url).fragment
                oid = re.compile('/(\d*)/').findall(urlparse.urlparse(url).path)[0]
                key = urlparse.parse_qs(urlparse.urlparse(url).query)['authkey'][0]

                url = 'http://plus.google.com/photos/%s/albums/%s/%s?authkey=%s' % (oid, aid, pid, key)

            result = getUrl(url, mobile=True).result

            u = re.compile('"(http[s]*://.+?videoplayback[?].+?)"').findall(result)[::-1]
            u = [i.replace('\\u003d','=').replace('\\u0026','&') for i in u]
            u = sum([self.tag(i) for i in u], [])

            url = []
            try: url += [[i for i in u if i['quality'] == '1080p'][0]]
            except: pass
            try: url += [[i for i in u if i['quality'] == 'HD'][0]]
            except: pass
            try: url += [[i for i in u if i['quality'] == 'SD'][0]]
            except: pass

            if url == []: return
            return url
        except:
            return

    def tag(self, url):
        quality = re.compile('itag=(\d*)').findall(url)
        quality += re.compile('=m(\d*)$').findall(url)
        try: quality = quality[0]
        except: return []

        if quality in ['37', '137', '299', '96', '248', '303', '46']:
            return [{'quality': '1080p', 'url': url}]
        elif quality in ['22', '84', '136', '298', '120', '95', '247', '302', '45', '102']:
            return [{'quality': 'HD', 'url': url}]
        elif quality in ['35', '44', '135', '244', '94']:
            return [{'quality': 'SD', 'url': url}]
        elif quality in ['18', '34', '43', '82', '100', '101', '134', '243', '93']:
            return [{'quality': 'SD', 'url': url}]
        elif quality in ['5', '6', '36', '83', '133', '242', '92', '132']:
            return [{'quality': 'SD', 'url': url}]
        else:
            return []

class gorillavid:
    def info(self):
        return {
            'netloc': ['gorillavid.com', 'gorillavid.in'],
            'host': ['Gorillavid'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://gorillavid.in/embed-%s.html' % url

            result = getUrl(url, mobile=True).result
            url = re.compile('file *: *"(http.+?)"').findall(result)[-1]

            request = urllib2.Request(url)
            response = urllib2.urlopen(request, timeout=30)
            response.close()

            type = str(response.info()["Content-Type"])
            if type == 'text/html': raise Exception()

            return url
        except:
            return

class grifthost:
    def info(self):
        return {
            'netloc': ['grifthost.com'],
            'host': ['Grifthost'],
            'quality': 'High',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://grifthost.com/embed-%s.html' % url

            result = getUrl(url).result

            try:
                post = {}
                f = common.parseDOM(result, "Form", attrs = { "method": "POST" })[0]
                f = f.replace('"submit"', '"hidden"')
                k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
                for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
                post = urllib.urlencode(post)
                result = getUrl(url, post=post).result
            except:
                pass

            result = re.compile('(eval.*?\)\)\))').findall(result)[-1]
            url = js().worker(result)
            return url
        except:
            return

class hugefiles:
    def info(self):
        return {
            'netloc': ['hugefiles.net'],
            'host': ['Hugefiles'],
            'quality': 'High',
            'captcha': True,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url).result

            post = {}
            f = common.parseDOM(result, "Form", attrs = { "action": "" })
            f += common.parseDOM(result, "form", attrs = { "action": "" })
            k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post.update({'method_free': 'Free Download'})
            post.update(captcha().worker(result))
            post = urllib.urlencode(post)

            result = getUrl(url, post=post).result

            url = re.compile('fileUrl\s*=\s*[\'|\"](.+?)[\'|\"]').findall(result)[0]
            return url
        except:
            return

class ipithos:
    def info(self):
        return {
            'netloc': ['ipithos.to'],
            'host': ['Ipithos'],
            'quality': 'High',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://ipithos.to/embed-%s.html' % url

            result = getUrl(url, mobile=True).result

            result = re.compile('(eval.*?\)\)\))').findall(result)[-1]
            url = js().worker(result)
            return url
        except:
            return

class ishared:
    def info(self):
        return {
            'netloc': ['ishared.eu'],
            'host': ['iShared'],
            'quality': 'High',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url).result
            url = re.compile('path *: *"(http.+?)"').findall(result)[-1]
            return url
        except:
            return

class kingfiles:
    def info(self):
        return {
            'netloc': ['kingfiles.net'],
            'host': ['Kingfiles'],
            'quality': 'High',
            'captcha': True,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url).result

            post = {}
            f = common.parseDOM(result, "Form", attrs = { "action": "" })[0]
            k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post.update({'method_free': ' '})
            post = urllib.urlencode(post)

            result = getUrl(url, post=post).result

            post = {}
            f = common.parseDOM(result, "Form", attrs = { "action": "" })[0]
            k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post.update({'method_free': ' '})
            post.update(captcha().worker(result))
            post = urllib.urlencode(post)

            result = getUrl(url, post=post).result

            url = re.compile("var\s+download_url *= *'(.+?)'").findall(result)[0]
            return url
        except:
            return

class mailru:
    def info(self):
        return {
            'netloc': ['mail.ru', 'my.mail.ru', 'videoapi.my.mail.ru']
        }

    def resolve(self, url):
        try:
            usr = re.compile('/mail/(.+?)/').findall(url)[0]
            vid = re.compile('(\d*)[.]html').findall(url)[0]
            url = 'http://videoapi.my.mail.ru/videos/mail/%s/_myvideo/%s.json?ver=0.2.60' % (usr, vid)

            import requests
            result = requests.get(url).content
            cookie = requests.get(url).headers['Set-Cookie']

            u = json.loads(result)['videos']
            h = "|Cookie=%s" % urllib.quote(cookie)

            url = []
            try: url += [[{'quality': '1080p', 'url': i['url'] + h} for i in u if i['key'] == '1080p'][0]]
            except: pass
            try: url += [[{'quality': 'HD', 'url': i['url'] + h} for i in u if i['key'] == '720p'][0]]
            except: pass
            try: url += [[{'quality': 'SD', 'url': i['url'] + h} for i in u if not (i['key'] == '1080p' or i ['key'] == '720p')][0]]
            except: pass

            if url == []: return
            return url
        except:
            return

class mightyupload:
    def info(self):
        return {
            'netloc': ['mightyupload.com'],
            'host': ['Mightyupload'],
            'quality': 'High',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://www.mightyupload.com/embed-%s.html' % url

            result = getUrl(url, mobile=True).result

            url = re.compile("file *: *'(.+?)'").findall(result)
            if len(url) > 0: return url[0]

            result = re.compile('(eval.*?\)\)\))').findall(result)[-1]
            url = js().worker(result)
            return url
        except:
            return

class mooshare:
    def info(self):
        return {
            'netloc': ['mooshare.biz'],
            'host': ['Mooshare'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://mooshare.biz/embed-%s.html?play=1&confirm=Close+Ad+and+Watch+as+Free+User' % url

            result = getUrl(url).result
            url = re.compile('file *: *"(http.+?)"').findall(result)[-1]
            return url
        except:
            return

class movdivx:
    def info(self):
        return {
            'netloc': ['movdivx.com'],
            'host': ['Movdivx'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://www.movdivx.com/%s' % url
     
            result = getUrl(url).result

            post = {}
            f = common.parseDOM(result, "Form", attrs = { "action": "" })[0]
            k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post.update({'method_free': 'Free Download'})
            post = urllib.urlencode(post)

            result = getUrl(url, post=post).result

            result = re.compile('(eval.*?\)\)\))').findall(result)[-1]
            url = js().worker(result)
            return url
        except:
            return

class movpod:
    def info(self):
        return {
            'netloc': ['movpod.net', 'movpod.in'],
            'host': ['Movpod'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = url.replace('/vid/', '/')

            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://movpod.in/embed-%s.html' % url

            result = getUrl(url).result
            url = re.compile('file *: *"(http.+?)"').findall(result)[-1]

            request = urllib2.Request(url)
            response = urllib2.urlopen(request, timeout=30)
            response.close()

            type = str(response.info()["Content-Type"])

            if type == 'text/html': raise Exception()
            return url
        except:
            return

class movreel:
    def info(self):
        return {
            'netloc': ['movreel.com'],
            'host': ['Movreel'],
            'quality': 'High',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            user = xbmcaddon.Addon().getSetting("movreel_user")
            password = xbmcaddon.Addon().getSetting("movreel_password")

            login = 'http://movreel.com/login.html'
            post = {'op': 'login', 'login': user, 'password': password, 'redirect': url}
            post = urllib.urlencode(post)
            result = getUrl(url, close=False).result
            result += getUrl(login, post=post, close=False).result

            post = {}
            f = common.parseDOM(result, "Form", attrs = { "name": "F1" })[-1]
            k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post.update({'method_free': '', 'method_premium': ''})
            post = urllib.urlencode(post)

            import time
            request = urllib2.Request(url, post)

            for i in range(0, 3):
                try:
                    response = urllib2.urlopen(request, timeout=10)
                    result = response.read()
                    response.close()
                    url = re.compile('(<a .+?</a>)').findall(result)
                    url = [i for i in url if 'Download Link' in i][-1]
                    url = common.parseDOM(url, "a", ret="href")[0]
                    return url
                except:
                    time.sleep(1)
        except:
            return

class mrfile:
    def info(self):
        return {
            'netloc': ['mrfile.me'],
            'host': ['Mrfile'],
            'quality': 'High',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url).result

            post = {}
            f = common.parseDOM(result, "Form", attrs = { "name": "F1" })[-1]
            k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post.update({'method_free': '', 'method_premium': ''})
            post = urllib.urlencode(post)

            result = getUrl(url, post=post).result

            url = re.compile('(<a\s+href=.+?>Download\s+.+?</a>)').findall(result)[-1]
            url = common.parseDOM(url, "a", ret="href")[0]
            return url
        except:
            return

class mybeststream:
    def info(self):
        return {
            'netloc': ['mybeststream.xyz']
        }

    def resolve(self, url):
        try:
            referer = urlparse.parse_qs(urlparse.urlparse(url).query)['referer'][0]
            page = url.replace(referer, '').replace('&referer=', '').replace('referer=', '')

            result = getUrl(url, referer=referer).result
            result = re.compile("}[(]('.+?' *, *'.+?' *, *'.+?' *, *'.+?')[)]").findall(result)[-1]
            result = unwise().worker(result)

            strm = re.compile("file *: *[\'|\"](.+?)[\'|\"]").findall(result)
            strm = [i for i in strm if i.startswith('rtmp')][0]
            url = '%s pageUrl=%s live=1 timeout=10' % (strm, page)
            return url
        except:
            return

class nosvideo:
    def info(self):
        return {
            'netloc': ['nosvideo.com'],
            'host': ['Nosvideo'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url).result

            post = {}
            f = common.parseDOM(result, "Form", attrs = { "method": "POST" })[0]
            k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post.update({'method_free': 'Free Download'})
            post = urllib.urlencode(post)

            result = getUrl(url, post=post).result

            result = re.compile('(eval.*?\)\)\))').findall(result)[0]
            url = js().worker(result)

            result = getUrl(url).result
            url = common.parseDOM(result, "file")[0]
            return url
        except:
            return

class openload:
    def info(self):
        return {
            'netloc': ['openload.io'],
            'host': ['Openload'],
            'quality': 'High',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url).result

            url = common.parseDOM(result, "span", attrs = { "id": "realdownload" })[0]
            url = common.parseDOM(url, "a", ret="href")[0]
            return url
        except:
            return

class played:
    def info(self):
        return {
            'netloc': ['played.to'],
            'host': ['Played'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = url.replace('//', '/')
            url = re.compile('/.+?/([\w]+)').findall(url)[0]
            url = 'http://played.to/embed-%s.html' % url

            result = getUrl(url, mobile=True).result
            url = re.compile('file *: *"(http.+?)"').findall(result)[-1]
            return url
        except:
            return

class primeshare:
    def info(self):
        return {
            'netloc': ['primeshare.tv'],
            'host': ['Primeshare'],
            'quality': 'High',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url, mobile=True).result

            url = common.parseDOM(result, "video")[0]
            url = common.parseDOM(url, "source", ret="src", attrs = { "type": ".+?" })[0]
            return url
        except:
            return

class sharerepo:
    def info(self):
        return {
            'netloc': ['sharerepo.com'],
            'host': ['Sharerepo'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url).result
            url = re.compile("file *: *'(http.+?)'").findall(result)[-1]
            return url
        except:
            return

class stagevu:
    def info(self):
        return {
            'netloc': ['stagevu.com'],
            'host': ['StageVu'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url).result

            url = common.parseDOM(result, "embed", ret="src", attrs = { "type": "video.+?" })[0]
            return url
        except:
            return

class streamcloud:
    def info(self):
        return {
            'netloc': ['streamcloud.eu'],
            'host': ['Streamcloud'],
            'quality': 'Medium',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://streamcloud.eu/%s' % url
     
            result = getUrl(url).result

            post = {}
            f = common.parseDOM(result, "form", attrs = { "class": "proform" })[0]
            k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post = urllib.urlencode(post)
            post = post.replace('op=download1', 'op=download2')

            result = getUrl(url, post=post).result

            url = re.compile('file *: *"(http.+?)"').findall(result)[-1]
            return url
        except:
            return

class streamin:
    def info(self):
        return {
            'netloc': ['streamin.to'],
            'host': ['Streamin'],
            'quality': 'Medium',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://streamin.to/embed-%s.html' % url

            result = getUrl(url, mobile=True).result
            url = re.compile("file *: *[\'|\"](http.+?)[\'|\"]").findall(result)[-1]
            return url
        except:
            return

class thefile:
    def info(self):
        return {
            'netloc': ['thefile.me'],
            'host': ['Thefile'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://thefile.me/embed-%s.html' % url

            result = getUrl(url, mobile=True).result

            result = re.compile('(eval.*?\)\)\))').findall(result)[-1]
            url = js().worker(result)
            return url
        except:
            return

class thevideo:
    def info(self):
        return {
            'netloc': ['thevideo.me'],
            'host': ['Thevideo'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://thevideo.me/embed-%s.html' % url

            result = getUrl(url).result
            result = result.replace('\n','')

            import ast
            url = re.compile("'sources' *: *(\[.+?\])").findall(result)[-1]
            url = ast.literal_eval(url)
            url = url[-1]['file']
            return url
        except:
            return

class tusfiles:
    def info(self):
        return {
            'netloc': ['tusfiles.net'],
            'host': ['Tusfiles'],
            'quality': 'High',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url).result

            result = re.compile('(eval.*?\)\)\))').findall(result)[-1]
            url = js().worker(result)
            return url
        except:
            return

class uploadc:
    def info(self):
        return {
            'netloc': ['uploadc.com', 'zalaa.com'],
            'host': ['Uploadc', 'Zalaa'],
            'quality': 'High',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://uploadc.com/embed-%s.html' % url

            result = getUrl(url, mobile=True).result

            url = re.compile("'file' *, *'(.+?)'").findall(result)
            if len(url) > 0: return url[0]

            result = re.compile('(eval.*?\)\)\))').findall(result)[-1]
            url = js().worker(result)
            return url
        except:
            return

class uploadrocket:
    def info(self):
        return {
            'netloc': ['uploadrocket.net'],
            'host': ['Uploadrocket'],
            'quality': 'High',
            'captcha': True,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url).result
            result = result.decode('iso-8859-1').encode('utf-8')

            post = {}
            f = common.parseDOM(result, "Form", attrs = { "name": "freeorpremium" })[0]
            k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post.update({'method_isfree': 'Click for Free Download'})
            post = urllib.urlencode(post)

            result = getUrl(url, post=post).result
            result = result.decode('iso-8859-1').encode('utf-8')

            post = {}
            f = common.parseDOM(result, "Form", attrs = { "name": "F1" })[0]
            k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post.update(captcha().worker(result))
            post = urllib.urlencode(post)

            result = getUrl(url, post=post).result
            result = result.decode('iso-8859-1').encode('utf-8')

            url = common.parseDOM(result, "a", ret="href", attrs = { "onclick": "DL.+?" })[0]
            return url
        except:
            return

class uptobox:
    def info(self):
        return {
            'netloc': ['uptobox.com'],
            'host': ['Uptobox'],
            'quality': 'High',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url).result

            post = {}
            f = common.parseDOM(result, "form", attrs = { "name": "F1" })[0]
            k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post = urllib.urlencode(post)

            result = getUrl(url, post=post).result

            url = common.parseDOM(result, "div", attrs = { "align": ".+?" })
            url = [i for i in url if 'button_upload' in i][0]
            url = common.parseDOM(url, "a", ret="href")[0]
            url = ['http' + i for i in url.split('http') if 'uptobox.com' in i][0]
            return url
        except:
            return

class v_vids:
    def info(self):
        return {
            'netloc': ['v-vids.com'],
            'host': ['V-vids'],
            'quality': 'High',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url).result

            post = {}
            f = common.parseDOM(result, "Form", attrs = { "name": "F1" })[0]
            k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post.update({'method_free': '', 'method_premium': ''})
            post = urllib.urlencode(post)

            result = getUrl(url, post=post).result

            url = common.parseDOM(result, "a", ret="href", attrs = { "id": "downloadbutton" })[0]
            return url
        except:
            return

class veehd:
    def info(self):
        return {
            'netloc': ['veehd.com'],
        }

    def resolve(self, url):
        try:
            result = getUrl(url, close=False).result
            result = result.replace('\n','')

            url = re.compile('function\s*load_download.+?src\s*:\s*"(.+?)"').findall(result)[0]
            url = urlparse.urljoin('http://veehd.com', url)

            result = getUrl(url, close=False).result

            i = common.parseDOM(result, "iframe", ret="src")
            if len(i) > 0:
                i = urlparse.urljoin('http://veehd.com', i[0])
                getUrl(i, close=False).result
                result = getUrl(url).result

            url = re.compile('href *= *"([^"]+(?:mkv|mp4|avi))"').findall(result)
            url += re.compile('src *= *"([^"]+(?:divx|avi))"').findall(result)
            url += re.compile('"url" *: *"(.+?)"').findall(result)
            url = urllib.unquote(url[0])
            return url
        except:
            return

class vidbull:
    def info(self):
        return {
            'netloc': ['vidbull.com'],
            'host': ['Vidbull'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url, mobile=True).result
            url = common.parseDOM(result, "source", ret="src", attrs = { "type": "video.+?" })[0]
            return url
        except:
            return

class videomega:
    def info(self):
        return {
            'netloc': ['videomega.tv']
        }

    def resolve(self, url):
        try:
            url = urlparse.urlparse(url).query
            url = urlparse.parse_qsl(url)[0][1]
            url = 'http://videomega.tv/cdn.php?ref=%s' % url

            result = getUrl(url, mobile=True).result

            url = common.parseDOM(result, "source", ret="src", attrs = { "type": "video.+?" })[0]
            return url
        except:
            return

class vidplay:
    def info(self):
        return {
            'netloc': ['vidplay.net'],
            'host': ['Vidplay'],
            'quality': 'High',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            u = 'http://vidplay.net/vidembed-%s' % url

            url = getUrl(u, output='geturl').result
            if u == url: raise Exception()
            return url
        except:
            return

class vidspot:
    def info(self):
        return {
            'netloc': ['vidspot.net'],
            'host': ['Vidspot'],
            'quality': 'Medium',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://vidspot.net/embed-%s.html' % url

            result = getUrl(url, mobile=True).result
            url = re.compile('"file" *: *"(http.+?)"').findall(result)[-1]

            query = urlparse.urlparse(url).query
            url = url[:url.find('?')]
            url = '%s?%s&direct=false' % (url, query)
            return url
        except:
            return

class vidto:
    def info(self):
        return {
            'netloc': ['vidto.me'],
            'host': ['Vidto'],
            'quality': 'Medium',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://vidto.me/embed-%s.html' % url

            result = getUrl(url).result

            result = re.compile('(eval.*?\)\)\))').findall(result)[-1]
            result = re.sub(r'(\',\d*,\d*,)', r';\1', result)
            url = js().worker(result)
            return url
        except:
            return

class vidzi:
    def info(self):
        return {
            'netloc': ['vidzi.tv'],
            'host': ['Vidzi'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url, mobile=True).result
            result = result.replace('\n','')
            result = re.compile('sources *: *\[.+?\]').findall(result)[-1]
            result = re.compile('file *: *"(http.+?)"').findall(result)

            url = [i for i in result if '.m3u8' in i]
            if len(url) > 0: return url[0]
            url = [i for i in result if not '.m3u8' in i]
            if len(url) > 0: return url[0]
        except:
            return

class vimeo:
    def info(self):
        return {
            'netloc': ['vimeo.com']
        }

    def resolve(self, url):
        try:
            url = [i for i in url.split('/') if i.isdigit()][-1]
            url = 'http://player.vimeo.com/video/%s/config' % url

            result = getUrl(url).result
            result = json.loads(result)
            u = result['request']['files']['h264']

            url = None
            try: url = u['hd']['url']
            except: pass
            try: url = u['sd']['url']
            except: pass

            return url
        except:
            return

class vk:
    def info(self):
        return {
            'netloc': ['vk.com']
        }

    def resolve(self, url):
        try:
            url = url.replace('https://', 'http://')
            result = getUrl(url).result

            u = re.compile('url(720|540|480|360|240)=(.+?)&').findall(result)

            url = []
            try: url += [[{'quality': 'HD', 'url': i[1]} for i in u if i[0] == '720'][0]]
            except: pass
            try: url += [[{'quality': 'SD', 'url': i[1]} for i in u if i[0] == '540'][0]]
            except: pass
            try: url += [[{'quality': 'SD', 'url': i[1]} for i in u if i[0] == '480'][0]]
            except: pass
            if not url == []: return url
            try: url += [[{'quality': 'SD', 'url': i[1]} for i in u if i[0] == '360'][0]]
            except: pass
            if not url == []: return url
            try: url += [[{'quality': 'SD', 'url': i[1]} for i in u if i[0] == '240'][0]]
            except: pass

            if url == []: return
            return url
        except:
            return

class vodlocker:
    def info(self):
        return {
            'netloc': ['vodlocker.com'],
            'host': ['Vodlocker'],
            'quality': 'Low',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://vodlocker.com/embed-%s.html' % url

            result = getUrl(url, mobile=True).result
            url = re.compile('file *: *"(http.+?)"').findall(result)[-1]
            return url
        except:
            return

class xfileload:
    def info(self):
        return {
            'netloc': ['xfileload.com'],
            'host': ['Xfileload'],
            'quality': 'High',
            'captcha': True,
            'a/c': False
        }

    def resolve(self, url):
        try:
            result = getUrl(url, close=False).result

            post = {}
            f = common.parseDOM(result, "Form", attrs = { "action": "" })
            k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
            for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
            post.update(captcha().worker(result))
            post = urllib.urlencode(post)

            import time
            request = urllib2.Request(url, post)

            for i in range(0, 5):
                try:
                    response = urllib2.urlopen(request, timeout=10)
                    result = response.read()
                    response.close()
                    if 'download2' in result: raise Exception()
                    url = common.parseDOM(result, "a", ret="href", attrs = { "target": "" })[0]
                    return url
                except:
                    time.sleep(1)
        except:
            return

class xvidstage:
    def info(self):
        return {
            'netloc': ['xvidstage.com'],
            'host': ['Xvidstage'],
            'quality': 'Medium',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://xvidstage.com/embed-%s.html' % url

            result = getUrl(url, mobile=True).result

            result = re.compile('(eval.*?\)\)\))').findall(result)[-1]
            url = js().worker(result)
            return url
        except:
            return

class youtube:
    def info(self):
        return {
            'netloc': ['youtube.com'],
            'host': ['Youtube'],
            'quality': 'Medium',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            id = url.split("?v=")[-1].split("/")[-1].split("?")[0].split("&")[0]
            result = getUrl('http://www.youtube.com/watch?v=%s' % id).result

            message = common.parseDOM(result, "div", attrs = { "id": "unavailable-submessage" })
            message = ''.join(message)

            alert = common.parseDOM(result, "div", attrs = { "id": "watch7-notification-area" })

            if len(alert) > 0: raise Exception()
            if re.search('[a-zA-Z]', message): raise Exception()

            url = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' % id
            return url
        except:
            return

class zettahost:
    def info(self):
        return {
            'netloc': ['zettahost.tv'],
            'host': ['Zettahost'],
            'quality': 'High',
            'captcha': False,
            'a/c': False
        }

    def resolve(self, url):
        try:
            url = url.replace('/embed-', '/')
            url = re.compile('//.+?/([\w]+)').findall(url)[0]
            url = 'http://zettahost.tv/embed-%s.html' % url

            result = getUrl(url, mobile=True).result

            result = re.compile('(eval.*?\)\)\))').findall(result)[-1]
            url = js().worker(result)
            return url
        except:
            return



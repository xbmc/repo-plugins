# -*- coding: utf-8 -*-

'''
    Genesis Add-on
    Copyright (C) 2014 lambda

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

import urllib,urllib2,re,os,xbmc,xbmcgui,xbmcaddon,xbmcvfs

try:
    import CommonFunctions as common
except:
    import commonfunctionsdummy as common
try:
    import json
except:
    import simplejson as json


def get(url):
    print url
    pz = premiumize(url)
    if not pz == None: return pz
    rd = realdebrid(url)
    if not rd == None: return rd

    try:
        u = None
        import urlparse
        u = urlparse.urlparse(url).netloc
        u = u.replace('www.', '')
        print 'common resolver',u
    except:
        pass

    if u == 'vk.com': url = vk(url)
    elif u == 'docs.google.com': url = googledocs(url)
    elif u == 'youtube.com': url = youtube(url)
    elif u == 'videomega.tv': url = videomega(url)
    elif u == 'movreel.com': url = movreel(url)
    elif u == 'billionuploads.com': url = billionuploads(url)
    elif u == 'v-vids.com': url = v_vids(url)
    elif u == 'vidbull.com': url = vidbull(url)
    elif u == '180upload.com': url = _180upload(url)
    elif u == 'hugefiles.net': url = hugefiles(url)
    elif u == 'filecloud.io': url = filecloud(url)
    elif u == 'uploadrocket.net': url = uploadrocket(url)
    elif u == 'kingfiles.net': url = kingfiles(url)
    elif u == 'streamin.to': url = streamin(url)
    elif u == 'grifthost.com': url = grifthost(url)
    elif u == 'ishared.eu': url = ishared(url)
    elif u == 'cloudyvideos.com': url = cloudyvideos(url)
    elif u == 'mrfile.me': url = mrfile(url)
    elif u == 'datemule.com': url = datemule(url)
    elif u == 'vimeo.com': url = vimeo(url)
    elif u == 'odnoklassniki.ru': url = odnoklassniki(url)
    elif u == 'videoapi.my.mail.ru': url = mailru(url)
    elif u == 'my.mail.ru': url = mailru(url)
    elif u == 'mail.ru': url = mailru(url)

    else:
        try:
            import urlresolver
            host = urlresolver.HostedMediaFile(url)
            if host: resolver = urlresolver.resolve(url)
            else: return url
            if not resolver.startswith('http://'): return
            if not resolver == url: return resolver
        except:
            pass

    return url


class getUrl(object):
    def __init__(self, url, close=True, proxy=None, post=None, mobile=False, referer=None, cookie=None, output='', timeout='10'):
        if not proxy == None:
            proxy_handler = urllib2.ProxyHandler({'http':'%s' % (proxy)})
            opener = urllib2.build_opener(proxy_handler, urllib2.HTTPHandler)
            opener = urllib2.install_opener(opener)
        if output == 'cookie' or not close == True:
            import cookielib
            cookie_handler = urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar())
            opener = urllib2.build_opener(cookie_handler, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())
            opener = urllib2.install_opener(opener)
        if not post == None:
            request = urllib2.Request(url, post)
        else:
            request = urllib2.Request(url,None)
        if mobile == True:
            request.add_header('User-Agent', 'Mozilla/5.0 (iPhone; CPU; CPU iPhone OS 4_0 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7')
        else:
            request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0')
        if not referer == None:
            request.add_header('Referer', referer)
        if not cookie == None:
            request.add_header('cookie', cookie)
        response = urllib2.urlopen(request, timeout=int(timeout))
        if output == 'cookie':
            result = str(response.headers.get('Set-Cookie'))
        elif output == 'geturl':
            result = response.geturl()
        else:
            result = response.read()
        if close == True:
            response.close()
        self.result = result

def cloudflare(url):
    try:
        import urlparse,cookielib

        class NoRedirection(urllib2.HTTPErrorProcessor):    
            def http_response(self, request, response):
                return response

        def parseJSString(s):
            try:
                offset=1 if s[0]=='+' else 0
                val = int(eval(s.replace('!+[]','1').replace('!![]','1').replace('[]','0').replace('(','str(')[offset:]))
                return val
            except:
                pass

        agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'
        cj = cookielib.CookieJar()

        opener = urllib2.build_opener(NoRedirection, urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [('User-Agent', agent)]
        response = opener.open(url)
        result = response.read()

        jschl = re.compile('name="jschl_vc" value="(.+?)"/>').findall(result)[0]

        init = re.compile('setTimeout\(function\(\){\s*.*?.*:(.*?)};').findall(result)[0]
        builder = re.compile(r"challenge-form\'\);\s*(.*)a.v").findall(result)[0]
        decryptVal = parseJSString(init)
        lines = builder.split(';')

        for line in lines:
            if len(line)>0 and '=' in line:
                sections=line.split('=')

                line_val = parseJSString(sections[1])
                decryptVal = int(eval(str(decryptVal)+sections[0][-1]+str(line_val)))

        answer = decryptVal + len(urlparse.urlparse(url).netloc)

        query = '%s/cdn-cgi/l/chk_jschl?jschl_vc=%s&jschl_answer=%s' % (url, jschl, answer)

        opener = urllib2.build_opener(NoRedirection, urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [('User-Agent', agent)]
        response = opener.open(query)
        cookie = str(response.headers.get('Set-Cookie'))
        response.close()

        return cookie
    except:
        return

def jsunpack(script):
    def __itoa(num, radix):
        result = ""
        while num > 0:
            result = "0123456789abcdefghijklmnopqrstuvwxyz"[num % radix] + result
            num /= radix
        return result

    def __unpack(p, a, c, k, e, d):
        while (c > 1):
            c = c -1
            if (k[c]):
                p = re.sub('\\b' + str(__itoa(c, a)) +'\\b', k[c], p)
        return p

    aSplit = script.split(";',")
    p = str(aSplit[0])
    aSplit = aSplit[1].split(",")
    a = int(aSplit[0])
    c = int(aSplit[1])
    k = aSplit[2].split(".")[0].replace("'", '').split('|')
    e = ''
    d = ''
    sUnpacked = str(__unpack(p, a, c, k, e, d))
    return sUnpacked.replace('\\', '')

def captcha(data):
    try:
        captcha = {}

        def get_response(response):
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

        solvemedia = common.parseDOM(data, "iframe", ret="src")
        solvemedia = [i for i in solvemedia if 'api.solvemedia.com' in i]

        if len(solvemedia) > 0:
            url = solvemedia[0]
            result = getUrl(url).result
            challenge = common.parseDOM(result, "input", ret="value", attrs = { "id": "adcopy_challenge" })[0]
            response = common.parseDOM(result, "iframe", ret="src")
            response += common.parseDOM(result, "img", ret="src")
            response = [i for i in response if '/papi/media' in i][0]
            response = 'http://api.solvemedia.com' + response
            response = get_response(response)
            captcha.update({'adcopy_challenge': challenge, 'adcopy_response': response})
            return captcha

        recaptcha = []
        if data.startswith('http://www.google.com'): recaptcha += [data]
        recaptcha += common.parseDOM(data, "script", ret="src", attrs = { "type": "text/javascript" })
        recaptcha = [i for i in recaptcha if 'http://www.google.com' in i]

        if len(recaptcha) > 0:
            url = recaptcha[0]
            result = getUrl(url).result
            challenge = re.compile("challenge\s+:\s+'(.+?)'").findall(result)[0]
            response = 'http://www.google.com/recaptcha/api/image?c=' + challenge
            response = get_response(response)
            captcha.update({'recaptcha_challenge_field': challenge, 'recaptcha_challenge': challenge, 'recaptcha_response_field': response, 'recaptcha_response': response})
            return captcha

        numeric = re.compile("left:(\d+)px;padding-top:\d+px;'>&#(.+?);<").findall(data)

        if len(numeric) > 0:
            result = sorted(numeric, key=lambda ltr: int(ltr[0]))
            response = ''.join(str(int(num[1])-48) for num in result)
            captcha.update({'code': response})
            return captcha

    except:
        return captcha


def vk(url):
    try:
        url = url.replace('http://', 'https://')
        result = getUrl(url).result

        u = re.compile('url(720|540|480)=(.+?)&').findall(result)

        url = []
        try: url += [[{'quality': 'HD', 'url': i[1]} for i in u if i[0] == '720'][0]]
        except: pass
        try: url += [[{'quality': 'SD', 'url': i[1]} for i in u if i[0] == '540'][0]]
        except: pass
        try: url += [[{'quality': 'SD', 'url': i[1]} for i in u if i[0] == '480'][0]]
        except: pass

        if url == []: return
        return url
    except:
        return

def google(url):
    try:
        if any(x in url for x in ['&itag=37&', '&itag=137&', '&itag=299&', '&itag=96&', '&itag=248&', '&itag=303&', '&itag=46&']): quality = '1080p'
        elif any(x in url for x in ['&itag=22&', '&itag=84&', '&itag=136&', '&itag=298&', '&itag=120&', '&itag=95&', '&itag=247&', '&itag=302&', '&itag=45&', '&itag=102&']): quality = 'HD'
        else: raise Exception()

        url = [{'quality': quality, 'url': url}]
        return url
    except:
        return

def googledocs(url):
    try:
        url = url.split('/preview', 1)[0]

        result = getUrl(url).result
        result = re.compile('"fmt_stream_map",(".+?")').findall(result)[0]
        result = json.loads(result)

        u = [i.split('|')[-1] for i in result.split(',')]

        url = []
        try: url += [[{'quality': '1080p', 'url': i} for i in u if any(x in i for x in ['&itag=37&', '&itag=137&', '&itag=299&', '&itag=96&', '&itag=248&', '&itag=303&', '&itag=46&'])][0]]
        except: pass
        try: url += [[{'quality': 'HD', 'url': i} for i in u if any(x in i for x in ['&itag=22&', '&itag=84&', '&itag=136&', '&itag=298&', '&itag=120&', '&itag=95&', '&itag=247&', '&itag=302&', '&itag=45&', '&itag=102&'])][0]]
        except: pass

        if url == []: return
        return url
    except:
        return

def youtube(url):
    try:
        id = url.split("?v=")[-1].split("/")[-1].split("?")[0].split("&")[0]
        result = getUrl('http://gdata.youtube.com/feeds/api/videos/%s?v=2' % id).result

        state, reason = None, None
        try: state = common.parseDOM(result, "yt:state", ret="name")[0]
        except: pass
        try: reason = common.parseDOM(result, "yt:state", ret="reasonCode")[0]
        except: pass
        if state == 'deleted' or state == 'rejected' or state == 'failed' or reason == 'requesterRegion' : return

        url = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' % id
        return url
    except:
        return

def premiumize(url):
    try:
        user = xbmcaddon.Addon().getSetting("premiumize_user")
        password = xbmcaddon.Addon().getSetting("premiumize_password")

        if (user == '' or password == ''): raise Exception()

        url = 'https://api.premiumize.me/pm-api/v1.php?method=directdownloadlink&params[login]=%s&params[pass]=%s&params[link]=%s' % (user, password, url)

        result = getUrl(url, close=False).result
        url = json.loads(result)['result']['location']
        return url
    except:
        return

def premiumize_hosts():
    try:
        user = xbmcaddon.Addon().getSetting("premiumize_user")
        password = xbmcaddon.Addon().getSetting("premiumize_password")

        if (user == '' or password == ''): raise Exception()

        pz = getUrl('https://api.premiumize.me/pm-api/v1.php?method=hosterlist&params[login]=%s&params[pass]=%s' % (user, password)).result
        pz = json.loads(pz)['result']['hosterlist']
        pz = [i.rsplit('.' ,1)[0].lower() for i in pz]
        return pz
    except:
        return

def realdebrid(url):
    try:
        user = xbmcaddon.Addon().getSetting("realdedrid_user")
        password = xbmcaddon.Addon().getSetting("realdedrid_password")

        if (user == '' or password == ''): raise Exception()

        login_data = urllib.urlencode({'user' : user, 'pass' : password})
        login_link = 'https://real-debrid.com/ajax/login.php?%s' % login_data
        result = getUrl(login_link, close=False).result
        result = json.loads(result)
        error = result['error']
        if not error == 0: raise Exception()

        url = 'https://real-debrid.com/ajax/unrestrict.php?link=%s' % url
        url = url.replace('filefactory.com/stream/', 'filefactory.com/file/')
        result = getUrl(url).result
        result = json.loads(result)
        url = result['generated_links'][0][-1]
        return url
    except:
        return

def realdebrid_hosts():
    try:
        rd = getUrl('https://real-debrid.com/api/hosters.php').result
        rd = json.loads('[%s]' % rd)
        rd = [i.rsplit('.' ,1)[0].lower() for i in rd]
        return rd
    except:
        return

def videomega(url):
    try:
        url = url.replace('/?ref=', '/iframe.php?ref=')
        result = getUrl(url).result
        url = re.compile('document.write.unescape."(.+?)"').findall(result)[0]
        url = urllib.unquote_plus(url)
        url = re.compile('file: "(.+?)"').findall(url)[0]
        return url
    except:
        return

def movreel(url):
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

        result = getUrl(url, post=post).result

        url = re.compile('(<a .+?</a>)').findall(result)
        url = [i for i in url if 'Download Link' in i][-1]
        url = common.parseDOM(url, "a", ret="href")[0]
        return url
    except:
        return

def billionuploads(url):
    try:
        import cookielib
        cj = cookielib.CookieJar()

        agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'
        base = 'http://billionuploads.com'

        class NoRedirection(urllib2.HTTPErrorProcessor):
            def http_response(self, request, response):
                return response

        opener = urllib2.build_opener(NoRedirection, urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [('User-Agent', agent)]
        response = opener.open(base)
        response = opener.open(base)
        result = response.read()

        z = []
        decoded = re.compile('(?i)var z="";var b="([^"]+?)"').findall(result)[0]
        for i in range(len(decoded)/2): z.append(int(decoded[i*2:i*2+2],16))
        decoded = ''.join(map(unichr, z))

        incapurl = re.compile('(?i)"GET","(/_Incapsula_Resource[^"]+?)"').findall(decoded)[0]
        incapurl = base + incapurl

        response = opener.open(incapurl)
        response = opener.open(url)
        result = response.read()

        post = {}
        f = common.parseDOM(result, "Form", attrs = { "name": "F1" })[0]

        enc_input = re.compile('decodeURIComponent\("(.+?)"\)').findall(result)
        if enc_input: f += urllib2.unquote(enc_input[0])

        extra = re.compile("append\(\$\(document.createElement\('input'\)\).attr\('type','hidden'\).attr\('name','(.*?)'\).val\((.*?)\)").findall(result)
        for i, k in extra:
            try:
                k = re.compile('<textarea[^>]*?source="self"[^>]*?>([^<]*?)<').findall(result)[0].strip("'")
                post.update({i: k})
            except:
                pass

        k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
        for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})

        post.update({'submit_btn': ''})

        k = re.findall('\'input\[name="([^"]+?)"\]\'\)\.remove\(\)', result)
        for i in k: del post[i]

        post = urllib.urlencode(post)

        response = opener.open(url, post)
        result = response.read()
        response.close()

        def custom_range(start, end, step):
            while start <= end:
                yield start
                start += step

        def checkwmv(e):
            s = ""
            i=[]
            u=[[65,91],[97,123],[48,58],[43,44],[47,48]]
            for z in range(0, len(u)):
                for n in range(u[z][0],u[z][1]):
                    i.append(chr(n))
            t = {}
            for n in range(0, 64): t[i[n]]=n
            for n in custom_range(0, len(e), 72):
                a=0
                h=e[n:n+72]
                c=0
                for l in range(0, len(h)):            
                    f = t.get(h[l], 'undefined')
                    if f == 'undefined': continue
                    a = (a<<6) + f
                    c = c + 6
                    while c >= 8:
                        c = c - 8
                        s = s + chr( (a >> c) % 256 )
            return s

        try:
            url = common.parseDOM(result, "input", ret="value", attrs = { "id": "dl" })[0]
            url = url.split('GvaZu')[1]
            url = checkwmv(url)
            url = checkwmv(url)
            return url
        except:
            pass

        try:
            url = common.parseDOM(result, "source", ret="src")[0]
            return url
        except:
            pass
    except:
        return

def v_vids(url):
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

def vidbull(url):
    try:
        result = getUrl(url, mobile=True).result
        url = common.parseDOM(result, "source", ret="src", attrs = { "type": "video.+?" })[0]
        return url
    except:
        return

def _180upload(url):
    try:
        u = re.compile('//.+?/([\w]+)').findall(url)[0]
        u = 'http://180upload.com/embed-%s.html' % u

        result = getUrl(u).result

        post = {}
        f = common.parseDOM(result, "form", attrs = { "id": "captchaForm" })[0]
        k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
        for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
        post = urllib.urlencode(post)

        result = getUrl(u, post=post).result

        result = re.compile('id="player_code".*?(eval.*?\)\)\))').findall(result)[0]
        result = jsunpack(result)

        u = re.compile('name="src"0="([^"]+)"/>').findall(result)[0]
        return u
    except:
        pass

    try:
        result = getUrl(url).result

        post = {}
        f = common.parseDOM(result, "Form", attrs = { "name": "F1" })[0]
        k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
        for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
        post.update(captcha(result))
        post = urllib.urlencode(post)

        result = getUrl(url, post=post).result

        url = common.parseDOM(result, "a", ret="href", attrs = { "id": "lnk_download" })[0]
        return url
    except:
        return

def hugefiles(url):
    try:
        result = getUrl(url).result

        post = {}
        f = common.parseDOM(result, "Form", attrs = { "action": "" })
        k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
        for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
        post.update({'method_free': 'Free Download'})
        post.update(captcha(result))
        post = urllib.urlencode(post)

        result = getUrl(url, post=post).result

        post = {}
        f = common.parseDOM(result, "Form", attrs = { "action": "" })
        k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
        for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
        post.update({'method_free': 'Free Download'})
        post = urllib.urlencode(post)

        u = getUrl(url, output='geturl', post=post).result
        if not url == u: return u
    except:
        return

def filecloud(url):
    try:
        result = getUrl(url, close=False).result
        result = getUrl('http://filecloud.io/download.html').result

        url = re.compile("__requestUrl\s+=\s+'(.+?)'").findall(result)[0]

        ukey = re.compile("'ukey'\s+:\s+'(.+?)'").findall(result)[0]
        __ab1 = re.compile("__ab1\s+=\s+(\d+);").findall(result)[0]
        ctype = re.compile("'ctype'\s+:\s+'(.+?)'").findall(result)[0]

        challenge = re.compile("__recaptcha_public\s+=\s+'(.+?)'").findall(result)[0]
        challenge = 'http://www.google.com/recaptcha/api/challenge?k=' + challenge

        post = {'ukey': ukey, '__ab1': str(__ab1), 'ctype': ctype}
        post.update(captcha(challenge))
        post = urllib.urlencode(post)

        result = getUrl(url, post=post).result
        result = getUrl('http://filecloud.io/download.html').result

        url = common.parseDOM(result, "a", ret="href", attrs = { "id": "downloadBtn" })[0]
        return url
    except:
        return

def uploadrocket(url):
    try:
        result = getUrl(url).result

        post = {}
        f = common.parseDOM(result, "Form", attrs = { "name": "freeorpremium" })[0]
        k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
        for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
        post.update({'method_free': 'Free Download'})
        post = urllib.urlencode(post)

        result = getUrl(url, post=post).result

        post = {}
        f = common.parseDOM(result, "Form", attrs = { "name": "F1" })[0]
        k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
        for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
        post.update(captcha(result))
        post = urllib.urlencode(post)

        result = getUrl(url, post=post).result

        url = common.parseDOM(result, "a", ret="href", attrs = { "onclick": "window[.]open.+?" })[0]
        return url
    except:
        return

def kingfiles(url):
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
        post.update(captcha(result))
        post = urllib.urlencode(post)

        result = getUrl(url, post=post).result

        url = re.compile("var download_url = '(.+?)'").findall(result)[0]
        return url
    except:
        return

def streamin(url):
    try:
        url = url.replace('streamin.to/', 'streamin.to/embed-')
        if not url.endswith('.html'): url = url + '.html'
        result = getUrl(url, mobile=True).result
        url = re.compile("file:'(.+?)'").findall(result)[0]
        return url
    except:
        return

def grifthost(url):
    try:
        url = url.replace('/embed-', '/').split('-')[0]
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

        result = re.compile('(eval.*?\)\)\))').findall(result)[0]
        result = jsunpack(result)

        url = re.compile("file:'(.+?)'").findall(result)[0]
        return url
    except:
        return

def ishared(url):
    try:
        result = getUrl(url).result
        url = re.compile('path:"(.+?)"').findall(result)[0]
        return url
    except:
        return

def cloudyvideos(url):
    try:
        result = getUrl(url).result

        post = {}
        f = common.parseDOM(result, "Form", attrs = { "name": "F1" })[-1]
        k = common.parseDOM(f, "input", ret="name", attrs = { "type": "hidden" })
        for i in k: post.update({i: common.parseDOM(f, "input", ret="value", attrs = { "name": i })[0]})
        post.update({'method_free': '', 'method_premium': ''})
        post = urllib.urlencode(post)

        import time
        request = urllib2.Request(url, post)

        for i in range(0, 4):
            try:
                response = urllib2.urlopen(request, timeout=5)
                result = response.read()
                response.close()
                btn = common.parseDOM(result, "input", ret="value", attrs = { "class": "graybt.+?" })[0]
                url = re.compile('href=[\'|\"](.+?)[\'|\"]><input.+?class=[\'|\"]graybt.+?[\'|\"]').findall(result)[0]
                return url
            except:
                time.sleep(1)
    except:
        return

def mrfile(url):
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

def datemule(url):
    try:
        url += '&mode=html5'
        result = getUrl(url).result
        url = re.compile('file:\s+"(.+?)"').findall(result)[0]
        return url
    except:
        return

def vimeo(url):
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

def odnoklassniki(url):
    try:
        url = [i for i in url.split('/') if i.isdigit()][-1]
        url = 'http://www.odnoklassniki.ru/dk?cmd=videoPlayerMetadata&mid=%s' % url

        result = getUrl(url).result
        result = json.loads(result)

        a = "&start=0|User-Agent=%s" % urllib.quote_plus('Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.57 Safari/537.36')
        u = result['videos']

        url = []
        try: url += [[{'quality': 'HD', 'url': i['url'] + a} for i in u if i['name'] == 'hd'][0]]
        except: pass
        try: url += [[{'quality': 'SD', 'url': i['url'] + a} for i in u if i['name'] == 'sd'][0]]
        except: pass

        if url == []: return
        return url
    except:
        return

def mailru(url):
    try:
        url = url.replace('/my.mail.ru/video/', '/api.video.mail.ru/videos/embed/')
        url = url.replace('/videoapi.my.mail.ru/', '/api.video.mail.ru/')
        result = getUrl(url).result

        url = re.compile('metadataUrl":"(.+?)"').findall(result)[0]
        cookie = getUrl(url, output='cookie').result
        h = "|Cookie=%s" % urllib.quote(cookie)

        result = getUrl(url).result
        result = json.loads(result)
        result = result['videos']

        url = []
        url += [{'quality': '1080p', 'url': i['url'] + h} for i in result if i['key'] == '1080p']
        url += [{'quality': 'HD', 'url': i['url'] + h} for i in result if i['key'] == '720p']
        url += [{'quality': 'SD', 'url': i['url'] + h} for i in result if not (i['key'] == '1080p' or i ['key'] == '720p')]

        if url == []: return
        return url
    except:
        return



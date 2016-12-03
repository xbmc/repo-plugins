import urllib, urllib2, re
from cookies import Cookies
from urlparse import urlparse

class ShawGo:
    """
    @class ShawGo 
    
    MSO class to handle authorization with the Shaw MSO
    """

    @staticmethod
    def getID():
        return 'ShawGo'


    @staticmethod
    def authorize(streamProvider, username, password):
        """
        Perform authorization with ShawGo

        @param streamProvider the stream provider object. Needs to handle the 
                              getAuthURI.
        @param username the username to authenticate with
        @param password the password to authenticate with
        """

        uri = streamProvider.getAuthURI('ShawGo')

        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))#,
                                      #urllib2.HTTPHandler(debuglevel=1),
                                      #urllib2.HTTPSHandler(debuglevel=1))

        try:
            resp = opener.open(uri)
        except:
            print "Unable get OAUTH location"
            return None
        Cookies.saveCookieJar(jar)

        html = resp.read()

        action = re.search('<form.*?action=\"(.*?)"', html, re.MULTILINE)
        if not action:
            print "Unable to find action form"
            return None
        action = action.group(1)

        saml = re.search('<input.*?name=\"SAMLRequest\".*?value=\"(.*?)\"', html, re.MULTILINE)
        if not saml:
            print "Unable to find SAMLRequest."
            return None
        saml = saml.group(1)

        relay = re.search('<input.*?name=\"RelayState\".*?value=\"(.*?)\"', html, re.MULTILINE)
        if not relay:
            print "Unable to find relay state."
            return None
        relay = relay.group(1)

        return ShawGo.getAuthn(username, password, saml, relay, action)


    @staticmethod
    def getAuthn(username, password, saml, relay, url):
        """
        Perform OAuth
        @param username the username
        @param password the password
        @param saml the SAML request (form data)
        @param relay the relay state (form data)
        @param url the entitlement URL
        """
        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        values = {'SAMLRequest' : saml,
                  'RelayState' : relay }

        try:
            resp = opener.open(url, urllib.urlencode(values))
        except urllib2.URLError, e:
            print e.args
            return None
        Cookies.saveCookieJar(jar)

        html = resp.read()

        action = re.search('<form.*?action=\"(.*?)".*?id=\"form3">', html, re.MULTILINE)
        if not action:
            print "Unable to find action form"
            return None
        action = action.group(1)

        # ooc is username, email is shawemail, account number is shawdirect
        idp = 'shawocc'
        if username.isdigit():
            idp = 'shawdirect'
        elif "@" in username:
            idp = 'shawemail'

        # rejig the URL
        o = urlparse(url)
        newurl = o.scheme + "://" + o.netloc + action

        return ShawGo.getEntitlement(username.translate(None, "-"), password, saml, relay, idp, newurl)


    @staticmethod
    def getEntitlement(username, password, saml, relay, idp, url):
        """
        Get entitlement
        @param username the username
        @param password the password
        @param saml the SAML request (form data)
        @param relay the relay state (form data)
        @param idp the logon type (form data)
        @param url the entitlement URL
        """
        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        values = {'pf.username' : username,
                  'selectedPCV': 'ShawDirect',
                  'pf.pass' : password,
                  'pf.ok' : '',
                  'pf.cancel': ''}

        try:
            resp = opener.open(url, urllib.urlencode(values))
        except urllib2.URLError, e:
            print e.args
        Cookies.saveCookieJar(jar)

        html = resp.read()

        action = re.search('<form.*?action=\"(.*?)"', html, re.MULTILINE)
        if not action:
            print "Unable to find action form"
            return None
        action = action.group(1)

        relay = re.search('<input.*?name=\"RelayState\".*?value=\"(.*?)\"', html, re.MULTILINE)
        if not relay:
            print "Unable to find relay state."
            return None
        relay = relay.group(1)

        # this is stupid -- you should use beautiful soup or something
        idx = html.find("name=\"SAMLResponse\"")
        html = html[idx:len(html)]
        idx = html.find("value=\"") + 7
        html = html[idx:len(html)]
        idx = html.find("\"")
        saml = html[0:idx].replace('\n', '')

        return ShawGo.getSAMLAssertionConsumer(saml, relay, action)


    @staticmethod
    def getSAMLAssertionConsumer(saml, relay, url): 

        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        values = {'SAMLResponse' : saml,
                  'RelayState' : relay }

        try:
            resp = opener.open(url, urllib.urlencode(values))
        except urllib2.URLError, e:
            print e.args
        Cookies.saveCookieJar(jar)

        return ShawGo.completeBackgroundLogin()

    @staticmethod
    def completeBackgroundLogin():
        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        try:
            resp = opener.open('https://sp.auth.adobe.com/adobe-services/completeBackgroundLogin')
        except urllib2.URLError, e:
            print e.args
        Cookies.saveCookieJar(jar)

        return True

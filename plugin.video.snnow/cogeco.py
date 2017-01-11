import urllib, urllib2, re
from cookies import Cookies

class Cogeco:
    """
    @class Cogeco
    
    MSO class to handle authorization with the Cogeco MSO
    """

    @staticmethod
    def getID():
        return 'Cogeco'

    @staticmethod
    def authorize(streamProvider, username, password):
        """
        Perform authorization with Cogeco

        @param streamProvider the stream provider object.
        @param username the username to authenticate with
        @param password the password to authenticate with
        """

        uri =  streamProvider.getAuthURI("Cogeco")

        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))#,
                                      #urllib2.HTTPHandler(debuglevel=1),
                                      #urllib2.HTTPSHandler(debuglevel=1))

        # TODO: move this into a method that can be reused.. multiple calls..
        try:
            resp = opener.open(uri)
        except:
            print "Unable to redirect to auth page."
            return None
        Cookies.saveCookieJar(jar)

        html = resp.read()

        # TODO: this could be made a function to to parse and return the value based on an expression
        action = re.search('<form.*?action=\"(.*?)"', html, re.MULTILINE)
        if not action:
            print "Unable to find action form"
            return None
        action = action.group(1)

        saml = re.search('<input.*?name=\"SAMLRequest\".*?value=\"(.*?)\"', html, re.MULTILINE)
        if not saml:
            print "Unable to find SAML request."
            return None
        saml = saml.group(1)

        relay = re.search('<input.*?name=\"RelayState\".*?value=\"(.*?)\"', html, re.MULTILINE)
        if not relay:
            print "Unable to find relay state."
            return None
        relay = relay.group(1)

        return Cogeco.postAuthSaml(username, password, saml, relay, action)


    @staticmethod
    def postAuthSaml(username, password, saml, relay, url):
        
        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        values = {
            'SAMLRequest' : saml, 
            'RelayState' : relay 
        }

        try:
            resp = opener.open(url, urllib.urlencode(values))
        except urllib2.URLError, e:
            print e.args
            return None
        Cookies.saveCookieJar(jar)

        html = resp.read()

        action = re.search('<form.*?action=\"(.*?)"', html, re.MULTILINE)
        if not action:
            print "Unable to find action form"
            return None

        action = "https://customer-services.cogeco.com" + action.group(1)

        return Cogeco.postLogin(username, password, action)


    @staticmethod
    def postLogin(username, password, url):
        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        values = {
            'username' : username, 
            'password' : password 
        }

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

        saml = re.search('<input.*?name=\"SAMLResponse\".*?value=\"(.*?)\"', html, re.MULTILINE)
        if not saml:
            print "Unable to find SAML response."
            return None
        saml = saml.group(1)

        relay = re.search('<input.*?name=\"RelayState\".*?value=\"(.*?)\"', html, re.MULTILINE)
        if not relay:
            print "Unable to find relay state."
            return None
        relay = relay.group(1)

        return Cogeco.getSAMLAssertionConsumer(saml, relay, action)
        

    @staticmethod
    def getSAMLAssertionConsumer(saml, relay, url): 
        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        values = {
            'SAMLResponse' : saml,
            'RelayState' : relay 
        }

        try:
            resp = opener.open(url, urllib.urlencode(values))
        except urllib2.URLError, e:
            print e.args
        Cookies.saveCookieJar(jar)

        return Cogeco.completeBackgroundLogin()


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

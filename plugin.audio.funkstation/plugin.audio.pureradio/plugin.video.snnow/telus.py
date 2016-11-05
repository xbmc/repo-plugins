import urllib, urllib2, re
from cookies import Cookies
from urlparse import urlparse


def parseForm(inputs, html):
    """
    Return a dictionary containing the inputs and values of a form. If there is
    a form action then it is included as an element with key 'action'
    @param html the html to parse
    @return the form parameters and action (if present)
    """
    values = {}
    action = re.search('<form.*?action=\"(.*?)"', html, re.MULTILINE)
    if action:
        values['action'] = action.group(1)

    for field in inputs:
        result = re.search('<(input|button).*?name=\"' + field + '\".*?value=\"(.*?)\"', html, re.MULTILINE)
        if result:
            values[field] = result.group(2)
    return values


class Telus:
    """
    @class Telus 
    
    MSO class to handle authorization with the Shaw MSO.
    
    IMPORTANT (if you are ever trying to figure out what goes on here). The
    telus authentication does a really weird thing (well, its weird to me, but
    I'm not a webdev -- maybe this isn't weird. If you aren't me and you are 
    reading this, do you think its weird? let me know in the comments -- don't
    forget to subscribe) where it calls the SOS page, then the bookend page
    twice. Then, it calls SOS again, and then bookend twice again. Finally,
    on that fourth call to bookend, we are sent to the logon page. 
    """

    @staticmethod
    def getID():
        return 'telus_auth-gateway_net'


    @staticmethod
    def authorize(streamProvider, username, password):
        """
        Perform authorization with Telus

        @param streamProvider the stream provider object. Needs to handle the 
                              getAuthURI.
        @param username the username to authenticate with
        @param password the password to authenticate with
        """

        uri = streamProvider.getAuthURI('telus_auth-gateway_net')

        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        try:
            resp = opener.open(uri)
        except:
            print "Unable get Telus OAUTH location"
            return None
        Cookies.saveCookieJar(jar)

        html = resp.read()

        values = parseForm(['SAMLRequest', 'RelayState'], html)
        action = values.pop('action')
        if values == None:
            print "Form parsing failed in authorize"
            return None

        return Telus.getBookend(username, password, values, action)


    @staticmethod
    def getBookend(username, password, values, url):
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

        try:
            resp = opener.open(url, urllib.urlencode(values))
        except urllib2.URLError, e:
            print e.args
            return None
        Cookies.saveCookieJar(jar)

        html = resp.read()
        values = parseForm(['AuthState', 'id', 'coeff'], html)
        if values == None:
            print "Form parsing failed in getBookend"
            return None
        values['history'] = '2'

        return Telus.getBookendAgain(username, password, values,
                                     resp.url.split('?')[0])


    @staticmethod
    def getBookendAgain(username, password, values, url):
        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        values = urllib.urlencode(values)
        url += '?' + values

        try:
            resp = opener.open(url, values)
        except urllib2.URLError, e:
            print e.args
            return None
        Cookies.saveCookieJar(jar)

        html = resp.read()

        # we might have been redirected to the login
        if resp.url.find('login.php') > 0:
            return Telus.login(username, password, html)

        # if login was previously successful we might just get sent off to  
        url = re.search('location\.href.*?=.*?\"(.*?)\"', html, re.MULTILINE)
        if url:
            url = url.group(1)
            return Telus.discoveryAssociations(url)

        values = parseForm(['AuthState', 'id', 'coeff'], html)
        if values == None:
            print "Form parsing failed in getBookendAgain"
            return None
        values['history'] = '7'

        return Telus.getBookendAgain(username, password, values,
                                     resp.url.split('?')[0])


    @staticmethod
    def login(username, password, html):

        values = parseForm(['login_type', 'remember_me', 'source',
                                  'source_button'], html)
        if values == None:
            print "Form parsing failed in login"
            return None
        action = values.pop('action', None)
        values['username'] = username
        values['password'] = password

        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        try:
            resp = opener.open(action, urllib.urlencode(values))
        except urllib2.URLError, e:
            print e.args
            return None
        Cookies.saveCookieJar(jar)

        html = resp.read()

        url = re.search('location\.href.*?=.*?\"(.*?)\"', html, re.MULTILINE)
        if not url:
            print "Unable to parse URL from login result"
            return None
        url = url.group(1)

        return Telus.discoveryAssociations(url)


    @staticmethod
    def discoveryAssociations(url):
        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        values = { 'AuthState' : url[url.find('='):] }

        try:
            resp = opener.open(url, urllib.urlencode(values))
        except urllib2.URLError, e:
            print e.args
            return None
        Cookies.saveCookieJar(jar)
        html = resp.read()

        values = parseForm(['AuthState', 'id', 'coeff'], html)
        if values == None:
            print "Form parsing failed in getBookendAgain"
            return None

        return Telus.lastBookend(values, resp.url.split('?')[0])

    @staticmethod
    def lastBookend(values, url):
        """
        Make the lastBookend call
        """
        values['history'] = '7'
        url = url + '?' + urllib.urlencode(values)

        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        try:
            resp = opener.open(url)
        except urllib2.URLError, e:
            print e.args
            return None
        Cookies.saveCookieJar(jar)

        html = resp.read()

        values = parseForm(['SAMLResponse', 'RelayState'], html)
        if values == None:
            print "Failed to parse last bookend"
            return None
        action = values.pop('action')

        # note, the action could be either
        # - https://adobe.auth-gateway.net/saml/module.php/saml/sp/saml2-acs.php/proxy_telus.auth-gateway.net
        # - https://sp.auth.adobe.com/sp/saml/SAMLAssertionConsumer
        return Telus.authGateway(values, action)


    @staticmethod
    def authGateway(values, url):
        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        try:
            resp = opener.open(url, urllib.urlencode(values))
        except urllib2.URLError, e:
            if e.reason[1] == "No address associated with hostname":
                return True
            return None
        Cookies.saveCookieJar(jar)

        html = resp.read()

        url = re.search('location\.href.*?=.*?\"(.*?)\"', html, re.MULTILINE)
        if not url:
            print "Unable to parse auth gateway return"
            return None
        url = url.group(1)

        return Telus.discoveryAssociations(url)

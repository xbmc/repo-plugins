import urllib, urllib2, time, json, re
from cookies import Cookies

class Sportsnet:
    """
    @class Sportsnet
    
    MSO class to handle authorization with the Sportsnet MSO
    """
    
    USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.2 Safari/537.36'

    @staticmethod
    def getID():
        return 'Sportsnet'

    @staticmethod
    def authorize(streamProvider, username, password):
        """
        Perform authorization with Sportsnet

        @param streamProvider the stream provider object. Needs to handle the 
                              getAuthURI.
        @param username the username to authenticate with
        @param password the password to authenticate with
        """

        if not Sportsnet.mvpd():
            return False

        if not Sportsnet.signinmvpd():
            return False

        if not Sportsnet.callback(username, password):
            return False

        return True

    @staticmethod
    def mvpd():
        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        opener.addheaders = [('User-Agent', urllib.quote(Sportsnet.USER_AGENT))]

        values = { 'id' : 'myrogers',
                   'format' : 'json',
                   'callback' : 'listenRogersSigninCallback',
                   't' : str(int(time.time())) }

        try:
            resp = opener.open('http://now.sportsnet.ca/mvpd?',
                               urllib.urlencode(values))
        except:
            print "Unable to login with mvpd"
            return False

        res = resp.read()

        return True


    @staticmethod
    def signinmvpd():
        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        opener.addheaders = [('User-Agent', urllib.quote(Sportsnet.USER_AGENT))]

        values = { 'id' : 'myrogers' }
        try:
            resp = opener.open('https://now.sportsnet.ca/signinmvpd?',
                               urllib.urlencode(values))
        except:
            print "Unable to login with signinmvpd"
            return False

        res = resp.read()

        return True

    @staticmethod
    def callback(username, password):
        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        opener.addheaders = [('User-Agent', urllib.quote(Sportsnet.USER_AGENT))]

        values = { 'callback' : 'mvpdSignInCallback',
                   'username' :  username,
                   'password' : password,
                   't' : str(int(time.time())) }
        try:
            resp = opener.open('https://now.sportsnet.ca/secure/mvpd/myrogers?'+urllib.urlencode(values))
        except:
            print "Unable to login with signinmvpd"
            return False

        res = resp.read()
        json_data  = re.search('mvpdSignInCallback\((.*?)\)', res, re.MULTILINE)
        if not json_data:
            return False

        jsres = json.loads(json_data.group(1))

        if not 'code' in jsres.keys():
            return True

        if jsres['code'] != 'loginsuccess':
            return False

        return True

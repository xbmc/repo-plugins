import urllib, urllib2, random, adobe, json
from msofactory import MSOFactory
from cookies import Cookies
from settings import Settings

class SportsnetNow:

    def __init__(self):
        """
        Initialize the sportsnet class
        """
        self.CONFIG_URI = 'http://nlmobile.cdnak.neulion.com/sportsnetnow/config/config_ios_r3.xml'
        self.CHANNELS_URI = 'http://now.sportsnet.ca/service/channels?format=json'
        self.AUTHORIZED_MSO_URI = 'https://sp.auth.adobe.com/adobe-services/1.0/config/SportsnetNow'
        self.PUBLISH_POINT = 'http://now.sportsnet.ca/service/publishpoint?format=json'
        self.USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Mobile/12F69 ipad sn now 4.0912'

    @staticmethod
    def instance():
        return SportsnetNow()


    def name(self):
        return "Sportsnet Now"


    def getCategories(self):
        return [ 'live' ]


    def getRequestorID(self):
        return "SportsnetNow"


    def getSignedRequestorID(self):
        return 'HR4BsuvUHVRcLrqOpFrm0ZI6oXXWEMH0HJc9NeoXSDFn80xaMuZP9TR5uBVX4C3NrrbNmHRElI0vSYr9OMMCh+ttUvYsU5zBfpCnJYyND5ivjYT6x7eBRKo1+dUQvLSqzCP5VtR4AtbWEgJYnZmokDhLdwn43TpY9QJWW5SDYfPDagG3X5GIVX1THiJOGdbQ2J3T/+3hppkvkZ0dncO6k7kQRhjBJl82huECAJo2QhxqP3OrpfHC2fi3TdPioCig+kS/USGje4kHK2Lu0eb/RsT3HpmTlybrMlU43Yd9tBg4r3yr9Apwra07g6hv/Cd3iHkUkUE6AAJi1GsGpGE6BVb1qNtQYfWIq2AGS9cyh6eVkJeUjWIaleSQKkpzITT89osu2gfgeW5qtywJvfS8wf1IRQT5vqx4jXS1MQwlaznVY4qpWmtH0RCZfww/jIYMwLLI4L4CtwtH8V8jIesYkrwICn/YxC4QSeRLhFMMWyWPmc0E0KXYspv19wX/XJFlhTTSPKtVRAN1kxuq26W9PNPsGonq3ebuFNb4Jgld4k4VTlTLOGg7CEEj09TTTnAx2Der5jegn3B+uPs5/cb64+LWbR9z7GxDRSGvR7rSCczrurNgTVfDopYiRZr8vbHDIaTMXyupuEmt4IH8TxXfowu9vsAlfEdNv1PIdI2uHco='


    def getDeviceID(self):
        #return 64 hex characters
        settings = Settings.instance().get(self.getRequestorID())
        dev_id = ''
        if not settings:
            dev_id = ''
        elif 'DEV_ID' in settings.keys():
            dev_id = settings['DEV_ID']

        if not dev_id:
            print "id is empty joining crap"
            dev_id = ''.join(random.choice('0123456789abcdef') for _ in range(64))
            Settings.instance().store(self.getRequestorID(), 'DEV_ID', dev_id)

        return dev_id


    def getAuthURI(self, mso):
        """
        Get the Sportsnet Now OAuth URI. This is going to be called by the MSO
        class to get the authorization URI for hte specific provider

        @param mso the multi-system operator (eg: Rogers)
        """
        return 'https://sp.auth.adobe.com/adobe-services/1.0/authenticate/saml?domain_name=adobe.com&noflash=true&mso_id=' + mso + '&requestor_id=SportsnetNow&no_iframe=true&client_type=iOS&client_version=1.8&redirect_url=http://adobepass.ios.app/'


    def checkMSOs(self):
        """
        Check the available MSOs. We don't actually use anything from this
        request other than the cookies returned.
        """
        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        opener.addheaders = [('User-Agent', urllib.quote(self.USER_AGENT))]

        try:
            resp = opener.open(self.AUTHORIZED_MSO_URI)
        except:
            print "Unable get OAUTH location"
            return None
        Cookies.saveCookieJar(jar)

        mso_xml = resp.read()
        return None


    def getChannels(self):
        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        opener.addheaders = [('User-Agent', urllib.quote(self.USER_AGENT))]

        try:
            resp = opener.open(self.CHANNELS_URI)
        except urllib2.URLError, e:
            print e.args
            return None
        Cookies.saveCookieJar(jar)

        channels = json.loads(resp.read())

        for channel in channels:
            abbr = 'SN' + channel['seoName'][10:].capitalize()
            channel['abbr'] = abbr

        Settings.instance().store(self.getRequestorID(), 'CHANNELS', channels)

        return channels


    def authorize(self, username, password, msoName='Rogers'):
        """
        Authorize with the MSO credentials
        @param username the username
        @param password the password
        @param the MSO (eg: Rogers)
        """

        # Get the MSO class from the 
        mso = MSOFactory.getMSO(msoName)

        # Authorize with the MSO
        mso.authorize(self, username, password)

        ap = adobe.AdobePass()
        ap.sessionDevice(self)

        settings = Settings.instance().get(self.getRequestorID())

        result = ap.preAuthorize(self, ['SNEast', 'SNOne', 'SNOntario', 'SNWest',
                                        'SNPacific', 'SN360', 'SNWorld'])


    def getChannel(self, id, name, msoName='Rogers'):

        ap = adobe.AdobePass()
        if not ap.authorizeDevice(self, msoName, name):
            return None
        token = ap.deviceShortAuthorize(self, msoName)

        stream_uri = self.getPublishPoint(id, name, token)
        return stream_uri


    def getPublishPoint(self, id, name, token):
        """
        Get the stream address.
        @param name the channel name
        @param token the token to authorize the stream
        """
        values = { 'id' : id,
                   'type' : 'channel',
                   'nt' : '1',
                   'aprid' : name,
                   'aptoken' : token }

        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        opener.addheaders = [('User-Agent', urllib.quote(self.USER_AGENT))]

        try:
            resp = opener.open(self.PUBLISH_POINT, urllib.urlencode(values))
        except urllib2.URLError, e:
            print e.args
            return ''
        Cookies.saveCookieJar(jar)

        result = json.loads(resp.read())
        return result['path']


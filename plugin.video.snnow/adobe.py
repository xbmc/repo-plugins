import urllib, urllib2, xml.dom.minidom, settings, uuid
from settings import Settings
from cookies import Cookies

class AdobePass:


    def __init__(self):
        """
        Initialise the adobe pass.
        """
        self.SESSION_DEVICE_URI = 'https://sp.auth.adobe.com/adobe-services/1.0/sessionDevice'
        self.PREAUTHORIZE_URI = 'https://sp.auth.adobe.com/adobe-services/1.0/preauthorize'
        self.AUTHORIZE_URI = 'https://sp.auth.adobe.com/adobe-services/1.0/authorizeDevice'
        self.DEVICE_SHORT_AUTHORIZE = 'https://sp.auth.adobe.com/adobe-services/1.0/deviceShortAuthorize'
        self.USER_AGENT = 'AdobePassNativeClient/1.8 (iPad; U; CPU iPad OS 8.3 like Mac OS X; en-us)'


    def sessionDevice(self, streamProvider):
        """
        Session Device.
        """
        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))#,
                                      #urllib2.HTTPHandler(debuglevel=1),
                                      #urllib2.HTTPSHandler(debuglevel=1))


        values = { 'requestor_id' : streamProvider.getRequestorID(),
                   'signed_requestor_id' : streamProvider.getSignedRequestorID(),
                   '_method' : 'GET',
                   'device_id' : streamProvider.getDeviceID()}

        opener.addheaders = [('User-Agent', urllib.quote(self.USER_AGENT))]


        try:
            resp = opener.open(self.SESSION_DEVICE_URI, urllib.urlencode(values))
        except urllib2.URLError, e:
            print e.args
            return False
        Cookies.saveCookieJar(jar)

        resp_xml = resp.read()

        dom = xml.dom.minidom.parseString(resp_xml)

        result_node = dom.getElementsByTagName('result')[0]
        tok_node = result_node.getElementsByTagName('authnToken')[0]
        meta_node = result_node.getElementsByTagName('userMeta')[0]

        token = tok_node.firstChild.nodeValue
        meta = meta_node.firstChild.nodeValue
        
        s = Settings.instance()
        s.store('adobe', 'AUTHN_TOKEN', token)
        s.store('adobe', 'USER_META', meta)

        return True



    def preAuthorize(self, streamProvider, resource_ids):
        """
        Pre-authroize.  This _should_ get a list of authorised channels.

        @param streamProvider the stream provider (eg: the SportsnetNow
                              instance)
        @param resource_ids a list of resources to preauthorise
        @return a dictionary with each resource id as a key and boolean value
                indicating if the resource could be authorised
        """
        settings = Settings.instance().get('adobe')

        values = { 'authentication_token' : settings['AUTHN_TOKEN'],
                   'requestor_id' : streamProvider.getRequestorID() }

        value_str = urllib.urlencode(values)
        for k in resource_ids.keys():
            value_str += '&' + urllib.urlencode({ 'resource_id' : resource_ids[k] })

        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        opener.addheaders = [('User-Agent', urllib.quote(self.USER_AGENT))]

        try:
            resp = opener.open(self.PREAUTHORIZE_URI, value_str)
        except urllib2.URLError, e:
            print e.args
            return None
        Cookies.saveCookieJar(jar)

        resp_xml = resp.read()
        dom = xml.dom.minidom.parseString(resp_xml)

        resources = {}
        resources_node = dom.getElementsByTagName('resources')[0]
        for resource_node in resources_node.getElementsByTagName('resource'):
            id_node = resource_node.getElementsByTagName('id')[0]
            auth_node = resource_node.getElementsByTagName('authorized')[0]

            id_str = id_node.firstChild.nodeValue
            auth = (auth_node.firstChild.nodeValue.lower() == 'true')
            resources[id_str] = auth

        return resources


    def authorizeDevice(self, streamProvider, mso_id, channel):
        """
        Authorise the device for a particular channel.

        @param streamProvider the stream provider (eg: the SportsnetNow
                              instance)
        @param mso_id the MSO identifier (eg: 'Rogers')
        @param channel the channel identifier
        """
        settings = Settings.instance().get('adobe')

        values = { 'resource_id' : channel,
                   'requestor_id' : streamProvider.getRequestorID(),
                   'signed_requestor_id' : streamProvider.getSignedRequestorID(),
                   'mso_id' : mso_id,
                   'authentication_token' : settings['AUTHN_TOKEN'],
                   'device_id' : streamProvider.getDeviceID(),
                   'userMeta' : '1' }

        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        opener.addheaders = [('User-Agent', urllib.quote(self.USER_AGENT))]

        try:
            resp = opener.open(self.AUTHORIZE_URI, urllib.urlencode(values))
        except urllib2.URLError, e:
            print e.args
            return False
        Cookies.saveCookieJar(jar)

        resp_xml = resp.read()
        if resp_xml.find('notAuthorized') >= 0:
            print "Unable to authorise for channel '" + channel + "'"
            return False

        try:
            dom = xml.dom.minidom.parseString(resp_xml)
        except:
            print "Unable to parse device authorization xml."
            return False

        result_node = dom.getElementsByTagName('result')[0]
        tok_node = result_node.getElementsByTagName('authzToken')[0]

        token = tok_node.firstChild.nodeValue

        s = Settings.instance()
        s.store('adobe', 'AUTHZ_TOKEN', token)

        return True


    def deviceShortAuthorize(self, streamProvider, mso_id):
        """
        Authorise for a particular channel... a second time.
        @param streamProvider the stream provider (eg: the SportsnetNow
                              instance)
        @param mso_id the MSO identifier (eg: 'Rogers')
        @return the session token required to authorise video the stream
        """
        settings = Settings.instance().get('adobe')

        values = { 'requestor_id' : streamProvider.getRequestorID(),
                   'signed_requestor_id' : streamProvider.getSignedRequestorID(),
                   'session_guid' : uuid.uuid4(),
                   'hashed_guid' : 'false',
                   'authz_token' : settings['AUTHZ_TOKEN'],
                   'mso_id' : mso_id,
                   'device_id' : streamProvider.getDeviceID() }

        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        opener.addheaders = [('User-Agent', urllib.quote(self.USER_AGENT))]

        try:
            resp = opener.open(self.DEVICE_SHORT_AUTHORIZE, urllib.urlencode(values))
        except urllib2.URLError, e:
            print e.args
            return ''
        Cookies.saveCookieJar(jar)

        resp_xml = resp.read()

        return resp_xml

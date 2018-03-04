import requests, uuid
from xml.dom.minidom import *
import xml.etree.ElementTree as ET

from utils import saveCookies, loadCookies, saveAuthorization, log
from operator import itemgetter

class CBC:

    def __init__(self):
        self.IDENTITIES_URL='https://api-cbc.cloud.clearleap.com/cloffice/client/identities'
        self.DEVICE_XML_FMT = """<device>
<deviceId>{}</deviceId>
<type>flounder</type>
<deviceModel>Nexus 9</deviceModel>
<deviceName>Nexus 9</deviceName>
</device>"""
        # Create requests session object
        self.session = requests.Session()
        session_cookies = loadCookies()
        if not session_cookies == None: 
            self.session.cookies = session_cookies 


    def getRegistrationURL(self):
        r = self.session.get(self.IDENTITIES_URL)
        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(self.IDENTITIES_URL, r.status_code), True)
            return None
        saveCookies(self.session.cookies)

        dom = parseString(r.content)
        url = dom.getElementsByTagName('registerDeviceUrl')[0]
        return url.firstChild.nodeValue


    def registerDevice(self, url):
        xml = self.DEVICE_XML_FMT.format(str(uuid.uuid4()))
        r = self.session.post(url, data=xml)
        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None
        saveCookies(self.session.cookies)

        # Parse the authorization response
        dom = parseString(r.content)
        status = dom.getElementsByTagName('status')[0].firstChild.nodeValue
        if status != "Success":
            log('Error: Unable to authorize device', True)
            return False
        auth = {
            'id': dom.getElementsByTagName('deviceId')[0].firstChild.nodeValue,
            'token': dom.getElementsByTagName('deviceToken')[0].firstChild.nodeValue
        }
        saveAuthorization(auth)
        return True


    def getImage(self, item):
        # ignore 'cbc$liveImage' - the pix don't make sense after the first load
        if 'defaultThumbnailUrl' in item:
            return item['defaultThumbnailUrl']
        elif 'cbc$staticImage' in item:
            return item['cbc$staticImage']
        elif 'cbc$featureImage' in item:
            return item['cbc$featureImage']
        return None


    def getLabels(self, item):
        # https://codedocs.xyz/xbmc/xbmc/group__python__xbmcgui__listitem.html#ga0b71166869bda87ad744942888fb5f14
        """
         'media:keywords'
        """
        labels = {
            'studio': 'Canadian Broadcasting Corporation',
            'country': 'Canada'
        }
        if 'cbc$callSign' in item:
            labels['ChannelName'] = item['cbc$callSign']
            labels['title'] = '{} {}'.format(item['cbc$callSign'], item['title'])
        else:
            labels['title'] = item['title'].encode('utf-8')

        if 'cbc$show' in item:
            labels['tvshowtitle'] = item['cbc$show']
        elif 'clearleap:series' in item:
            labels['tvshowtitle'] = item['clearleap:series']

        if 'description' in item:
            labels['plot'] = item['description'].encode('utf-8')
            labels['plotoutline'] = item['description'].encode('utf-8')

        if 'cbc$liveDisplayCategory' in item:
            labels['genre'] = item['cbc$liveDisplayCategory']
        elif 'media:keywords' in item:
            labels['genre'] = item['media:keywords']

        if 'clearleap:season' in item:
            labels['season'] = item['clearleap:season']

        if 'clearleap:episodeInSeason' in item:
            labels['episode'] = item['clearleap:episodeInSeason']

        if 'media:rating' in item:
            labels['mpaa'] =  item['media:rating']

        if 'premiered' in item:
            labels['premiered'] = item['premiered']

        return labels


    def parseSmil(self, smil):
        r = self.session.get(smil)

        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None
        saveCookies(self.session.cookies)

        dom = parseString(r.content)
        seq = dom.getElementsByTagName('seq')[0]
        video = seq.getElementsByTagName('video')[0]
        src = video.attributes['src'].value
        title = video.attributes['title'].value
        abstract = video.attributes['abstract'].value
        return src

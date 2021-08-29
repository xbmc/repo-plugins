import requests, urllib.request, urllib.parse, urllib.error
from xml.dom.minidom import *
from .utils import saveCookies, loadCookies, loadAuthorization, log

class CBCAuthError(Exception):
    def __init__(self, value, payment):
        self.value = value
        self.payment = payment
    def __str__(self):
        return repr(self.value)


class Shows:

    def __init__(self):
        """
        Init constants
        """
        self.SHOW_LIST_URL = 'https://api-cbc.cloud.clearleap.com/cloffice/client/web/browse/babb23ae-fe47-40a0-b3ed-cdc91e31f3d6'
        self.IMAGE_PROFILES = [ 'CBC-POSTER-1X', 'CBC-BANNER-1X' ]
        self.SHOW_TAGS = [ 'title', 'clearleap:series', 'clearleap:season',
                           'clearleap:episodeInSeason', 'media:keywords',
                           'media:rating']
        # Create requests session object
        self.session = requests.Session()
        session_cookies = loadCookies()
        if not session_cookies == None:
            self.session.cookies = session_cookies


    def getHeaders(self):
        auth = loadAuthorization()
        return None if auth == None else {
            'X-Clearleap-DeviceToken': auth['token'],
            'X-Client-Version': '9.99.99',
            'X-Client-Name': 'Android',
            'X-Clearleap-DeviceId': auth['devid']
        }


    def getShow(self, item):
        """
        Parse show XML
        """
        tags = {}
        tags['guid'] = item.getElementsByTagName('guid')[0].firstChild.nodeValue
        tags['title'] = item.getElementsByTagName('title')[0].firstChild.nodeValue
        descriptions = item.getElementsByTagName('description')
        tags['description'] = '' if len(descriptions) == 0 else descriptions[0].firstChild.nodeValue
        image = None

        # figure out where the thumbnails are
        thumbnails = item
        if len(item.getElementsByTagName('media:group')) > 0:
            thumbnails = item.getElementsByTagName('media:group')[0]

        for thumb in thumbnails.getElementsByTagName('media:thumbnail'):
            if thumb.attributes['profile'].value in self.IMAGE_PROFILES:
                tags['image'] = thumb.attributes['url'].value
                break

        # <media:credit role="releaseDate">2017-08-07T00:00:00</media:credit>
        for credit in item.getElementsByTagName('media:credit'):
            #if 'role' in credit.attributes:
            if credit.attributes['role'] == 'releaseDate':
                tags['premiered'] = credit.attributes['role'].values

        content_type = item.getElementsByTagName('clearleap:itemType')[0].firstChild.nodeValue
        if content_type == 'media':
            tag = item.getElementsByTagName('media:content')[0]
            tags['url'] = tag.attributes['url'].value
            tags['duration'] = tag.attributes['duration'].value
            tags['video'] = True
            for tag in self.SHOW_TAGS:
                tag_nodes = item.getElementsByTagName(tag)
                if len(tag_nodes) > 0:
                    tags[tag] = tag_nodes[0].firstChild.nodeValue
        else:
            # even though its a list of links, there should only be one
            links = item.getElementsByTagName('link')
            tags['url'] = links[0].firstChild.nodeValue if len(links) > 0 else None

        return tags


    def getShows(self, url = None, offset = 0, progress_callback = None):
        """
        Get a list of all shows. Actual shows (not menus) will be items with a
        <clearleap:itemType>media</clearleap:itemType> tag. Menus are itemType
        LEAF.
        """
        headers = self.getHeaders()
        show_url = self.SHOW_LIST_URL if url is None else url
        if offset > 0:
            show_url += '?offset={}'.format(offset)

        r = self.session.get(show_url, headers=headers)

        if r.status_code == 401 or r.status_code == 500:
            log('({}) {} returns {} status. Signaling authorization failure'\
                .format('getShows', show_url, r.status_code), True)
            raise CBCAuthError('getShows', False)
        elif not r.status_code == 200:
            log('(getShows) {} returns {} status: "{}"'.format(url, r.status_code, r.content), True)
            return None
        saveCookies(self.session.cookies)
        dom = parseString(r.content)
        statuses = dom.getElementsByTagName('status')

        if len(statuses) > 0:
            if not statuses[0].firstChild.nodeValue == 'success':
                log('Error: unsuccessful retrieval of media', True)
                return None
            return dom.getElementsByTagName('url')[0].firstChild.nodeValue

        results = []
        items = dom.getElementsByTagName('item')
        for item in items:
            tags = self.getShow(item)
            results.append(tags)

        # figure out how many pages
        total = dom.getElementsByTagName('clearleap:totalResults')
        progress = len(results) + offset
        if len(total) > 0:
            total_shows = int(total[0].firstChild.nodeValue)
            if progress_callback:
                progress_callback((100*progress) // total_shows)
            if  total_shows > len(results) + offset:
                next_results = self.getShows(url, offset + len(results),
                                             progress_callback)
                results.extend(next_results)

        return results


    def getStream(self, url):
        headers = self.getHeaders()
        r = self.session.get(url, headers = headers)

        if r.status_code == 500:
            log('({}) {} returns {} status. Signaling authorization failure'\
                .format('getStream', url, r.status_code), True)
            raise CBCAuthError('getStream', False)
        elif r.status_code == 401:
            raise CBCAuthError('getStream', False)
        elif r.status_code == 402:
            raise CBCAuthError('getStream', True)
        elif not r.status_code == 200:
            log('(getStream) {} returns {} status code'.format(url, r.status_code), True)
            return None
        saveCookies(self.session.cookies)

        dom = parseString(r.content)
        status = dom.getElementsByTagName('status')[0].firstChild.nodeValue
        if not status == 'success':
            log('ERROR: {} has status of {}'.format(url, status), True)
            return None

        return {
            'url': dom.getElementsByTagName('url')[0].firstChild.nodeValue
        }

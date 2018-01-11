import re, urllib2, os
import resources.lib.utils as utils

class RedbullTVClient(object):
    REDBULL_API = "https://appletv.redbull.tv/"
    ROOT_MENU = [
        {"title": "Discover", "url": REDBULL_API + "products/discover", "is_content":False},
        {"title": "TV", "url": REDBULL_API + "products/tv", "is_content":False},
        {"title": "Channels", "url": REDBULL_API + "products/channels", "is_content":False},
        {"title": "Calendar", "url": REDBULL_API + "products/calendar", "is_content":False},
        {"title": "Search", "url": REDBULL_API + "search?q=", "is_content":False},
    ]

    def __init__(self, resolution=None):
        self.resolution = resolution

    @staticmethod
    def get_resolution_code(video_resolution_id):
        return {
            "0" : "320x180",
            "1" : "426x240",
            "2" : "640x360",
            "3" : "960x540",
            "4" : "1280x720",
        }.get(video_resolution_id, "1920x1080")

    def get_stream_details(self, element):
        name = element.findtext("title")
        description = element.findtext("description")
        image = element.find("image").get("src1080")
        url = element.findtext("mediaURL")
        base_url = ''

        # Try find the specific stream based on the users preferences
        try:
            response = urllib2.urlopen(url)
            # Required to get base url in case of a redirect, to use for relative paths
            base_url = response.geturl()
            playlists = response.read()

            resolution = self.get_resolution_code(self.resolution)
            media_url = re.search(
                "RESOLUTION=" + resolution + ".*\n(.*)",
                playlists).group(1)
        except Exception:
            pass
        else:
            url = media_url

        # if url is relative, add the base path
        if base_url != '' and not url.startswith('http'):
            url = os.path.dirname(base_url) + '/' + url

        return {"title":name, "url":url, "summary":description, "image": image, "is_stream":True}

    def get_element_details(self, element, url=None):
        details = {"url":url, "is_content":False}
        subtitle = element.findtext('.//subtitle') or element.findtext('.//label2') or ""
        details["title"] = (element.get("accessibilityLabel") or element.findtext('.//label')) + ((" - " + subtitle) if subtitle else "")
        details["summary"] = element.findtext('.//summary')
        details["image"] = element.find('.//image').get('src1080') if element.find('.//image') is not None else None
        details["event_date"] = element.findtext('.//rightLabel')

        # Get url of item, or name of selected category
        if "onSelect" in element.attrib:
            details["url"] = utils.strip_url(element.get("onSelect"))
            details["is_content"] = re.search(self.REDBULL_API + "(content|linear_stream)", details["url"]) is not None
        elif not details["event_date"]:
            details["category"] = details["title"]

        # Strip out any keys with empty values
        return {k:v for k, v in details.iteritems() if v is not None}

    def get_items(self, url=None, category=None):
        # If no url is specified, return the root menu
        if url is None:
            return self.ROOT_MENU

        xml = utils.get_xml(url)
        items = []

        # if the current url is a media stream
        if xml.find('.//httpLiveStreamingVideoAsset') is not None:
            items.append(self.get_stream_details(xml.find('.//httpLiveStreamingVideoAsset')))
        # if no category is specified, find the categories or item collection
        elif category is None:
            data = {
                "collectionDividers": xml.findall('.//collectionDivider'),
            }
            # Show Categories if relevant
            if data["collectionDividers"]:
                items += self.generate_items(
                    xml.findall('.//showcase') +
                    data["collectionDividers"],
                    url)
            else:
                items += self.generate_items(
                    xml.findall('.//twoLineMenuItem') +
                    xml.findall('.//twoLineEnhancedMenuItem') +
                    xml.findall('.//sixteenByNinePoster') +
                    xml.findall('.//actionButton'),
                    url)
        # if a category is specified, find the items for the specified category
        elif category is not None:
            if category == 'Featured':
                items += self.generate_items(xml.findall('.//showcasePoster'))
            else:
                collections = xml.iterfind(".//collectionDivider/../*")
                for collection in collections:
                    if collection.tag == 'collectionDivider' and collection.get("accessibilityLabel") == category:
                        items += self.generate_items(collections.next().find('.//items').getchildren())

        return items

    def generate_items(self, xml_elements, url=None):
        items = []
        for item in xml_elements:
            items.append(self.get_element_details(item, url))
        return items

__author__ = 'bromix'

import re
from io import BytesIO
import xml.etree.ElementTree as ET

# nightcrawler
from resources.lib import nightcrawler


class Client(nightcrawler.HttpClient):
    def __init__(self):
        nightcrawler.HttpClient.__init__(self)
        self._default_header = {'Host': 'video.golem.de',
                                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36',
                                'DNT': '1',
                                'Referer': 'http://www.golem.de/',
                                'Accept-Encoding': 'gzip, deflate',
                                'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'}
        pass

    def get_videos(self, limit=None):
        xml_data = self._request(url='http://video.golem.de/feeds/golem.de_video.xml')

        result = {'items': []}

        rss_stream = BytesIO(xml_data.text)
        for event, item in ET.iterparse(rss_stream):
            if item.tag == 'item':
                # title
                video_item = {'title': nightcrawler.utils.strings.to_unicode(item.find('title').text),
                              'images': {}}

                # plot
                plot = nightcrawler.utils.strings.to_unicode(item.find('description').text)
                if not plot:
                    plot = u''
                    pass
                plot = nightcrawler.utils.xml.decode(plot)
                video_item['plot'] = plot

                enclosure = item.find('enclosure')
                if enclosure is not None:
                    thumbnail = enclosure.get('url')
                    if thumbnail:
                        thumbnail = thumbnail.replace('thumb-medium-156/', '')
                        video_item['images']['thumbnail'] = thumbnail
                        pass
                    pass
                video_item['uri'] = nightcrawler.utils.strings.to_unicode(item.find('guid').text)
                pass

                datetime = nightcrawler.utils.datetime.parse(
                    nightcrawler.utils.strings.to_unicode(item.find('pubDate').text))

                video_item['published'] = str(datetime)
                video_item['format'] = 'golem.de'

                result['items'].append(video_item)

                # basically for tests
                if limit and len(result['items']) == limit:
                    break
                pass
            pass

        return result

    def get_video_stream(self, url, quality='high'):
        video_id = re.search(r'(?P<video_id>\d+)', url)
        if video_id:
            video_id = video_id.group('video_id')
            pass
        else:
            video_id = 'NOTFOUND'
            pass

        download_url = 'http://video.golem.de/download/%s?q=%s&rd=%s&start=0&paused=0&action=init' % (
            video_id, quality, url)

        headers = {'Referer': url}
        data = self._request(download_url, headers=headers, allow_redirects=False)
        url = data.headers.get('location', '')
        if not url:
            return None

        quality_map = {'medium': 360, 'high': 720}
        return {'title': '%s (%dp)' % (quality.title(), quality_map[quality]),
                'sort': [quality_map[quality]],
                'video': {'height': quality_map[quality]},
                'uri': url}

    def get_video_streams(self, url):
        streams = []
        for quality in ['medium', 'high']:
            stream = self.get_video_stream(url, quality=quality)
            if stream:
                streams.append(stream)
                pass
            pass

        return streams

    pass
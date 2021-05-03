
import m3u8
from urllib.parse import urlparse

from .model.subtitles_scraper import Subtitles
from .model import talk_scraper

class TedTalks:

    def __init__(self, fetcher, logger):
        self.fetcher = fetcher
        self.logger = logger

    def get_video_details(self, url, subs_language=None):
        talk_html = self.fetcher.get_HTML(url)
        try:
            m3u8_url, title, speaker, plot, talk_json = talk_scraper.get_talk(talk_html, self.logger)
        except Exception as e:
            raise type(e)(e.message + "\nfor url '%s'" % (url))

        playlist = self.__process_m3u8__(m3u8_url)

        subs = None
        if subs_language:
            subs = Subtitles(self.fetcher, self.logger).get_subtitles_for_talk(talk_json, subs_language)

        return playlist, title, subs, {'Director':speaker, 'Genre':'TED', 'Plot':plot, 'PlotOutline':plot}

    def __process_m3u8__(self, m3u8_url):
        r = self.fetcher.get(m3u8_url)
        playlist = m3u8.loads(r.text)
        parsed_url = urlparse(r.url)
        root_url = parsed_url.scheme + '://' + parsed_url.netloc       
        path = parsed_url.path.rsplit('/', 1)[0] + '/'

        for x in [x for x in playlist.media]:
            if x.type == 'SUBTITLES':
                playlist.media.remove(x)
            else:
                x.uri = self.__resolve__(root_url, path, x.uri)
        for x in playlist.playlists:
            x.uri =  self.__resolve__(root_url, path, x.uri)
            for y in [y for y in x.media]:
                if y.type == 'SUBTITLES':
                    x.media.remove(y)
        for x in playlist.iframe_playlists:
            x.uri =  self.__resolve__(root_url, path, x.uri)
        
        return playlist.dumps()

    def __resolve__(self, root_url, path, url):
        parsed_url = urlparse(url)
        if parsed_url.scheme:
            return url
        if not url.startswith('/'):
            root_url = root_url + path
        return root_url + url

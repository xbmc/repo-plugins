import model.subtitles_scraper as subtitles_scraper
import model.talk_scraper as talk_scraper

# MAIN URLS
URLSPEAKERS = 'http://www.ted.com/speakers/atoz/page/'
URLSEARCH = 'http://www.ted.com/search?q=%s/page/'


class TedTalks:

    def __init__(self, getHTML, logger):
        self.getHTML = getHTML
        self.logger = logger

    def getVideoDetails(self, url, video_quality, subs_language=None):
        talk_html = self.getHTML(url)
        try:
            video_url, title, speaker, plot, talk_json = talk_scraper.get(talk_html, video_quality)
        except Exception, e:
            raise type(e)(e.message + "\nfor url '%s'" % (url))

        subs = None
        if subs_language:
            subs = subtitles_scraper.get_subtitles_for_talk(talk_json, subs_language, self.logger)

        return title, video_url, subs, {'Director':speaker, 'Genre':'TED', 'Plot':plot, 'PlotOutline':plot}

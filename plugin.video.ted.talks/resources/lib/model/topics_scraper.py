from url_constants import URLTED, URLTOPICS
# Custom xbmc thing for fast parsing. Can't rely on lxml being available as of 2012-03.
import CommonFunctions as xbmc_common

class Topics:

    def __init__(self, get_HTML, logger):
        self.get_HTML = get_HTML
        self.logger = logger

    def get_topics(self):
        html = self.get_HTML(URLTOPICS)
        for topic_div in xbmc_common.parseDOM(html, 'div', {'class':'topics__list__topic'}):
            title = xbmc_common.parseDOM(topic_div, 'a')[0]
            link = xbmc_common.parseDOM(topic_div, 'a', ret='href')[0]
            topic = link.split('/')[-1]
            yield title, topic


    def get_talks(self, topic):
        page = 0

        while True:
            page += 1
            url = URLTED + '/talks?page={page}&topics%5B%5D={topic}'.format(page=page, topic=topic)
            html = self.get_HTML(url)
            talks = xbmc_common.parseDOM(html, 'div', {'class':'talk-link'})
            if not talks:
                self.logger('Empty page requested? Please report this message.')
                break

            for talk in talks:
                link = [href for href in xbmc_common.parseDOM(talk, 'a', ret='href') if '/talks' in href][0]
                title = img = speaker = None
                description = xbmc_common.parseDOM(talk, 'div', {'class':'media__message'})
                if description:
                    anchors = xbmc_common.parseDOM(description, 'a')
                    if anchors:
                        title = anchors[0]
                    speakers = xbmc_common.parseDOM(description, 'h4', {'class':'[^\'"]*talk-link__speaker[^\'"]*'})
                    if speakers:
                        speaker = speakers[0]
                    imgs = [src for src in xbmc_common.parseDOM(talk, 'img', ret='src') if 'images/ted' in src]
                    if imgs:
                        img = imgs[0]

                yield title, URLTED + link, img, speaker

            next_link = xbmc_common.parseDOM(html, 'span', {'class':'[^\'"]*pagination__next[^\'"]*'}, ret='class')
            if next_link:
                if 'disabled' in next_link[0]:
                    # On last page, stop loop.
                    return

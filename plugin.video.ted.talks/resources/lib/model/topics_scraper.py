import html
import html5lib

from .url_constants import URLTED

__url_topics__ = URLTED + '/watch/topics'

class Topics:

    def __init__(self, get_HTML, logger):
        self.get_HTML = get_HTML
        self.logger = logger

    def get_topics(self):
        topics_content = self.get_HTML(__url_topics__)
        dom = html5lib.parse(topics_content, namespaceHTMLElements=False)
        for li in dom.findall(".//li[@class='d:b']"):
            link = li.find('.//a[@href]')
            link = link.attrib['href'] if link else None
            if link and link.startswith('/topics/'):
                title = li.find('.//span').text.strip()
                topic = link[len('/topics/'):]
                yield title, topic


    def get_talks(self, topic):
        page = 0
        while True:
            page += 1
            url = URLTED + '/talks?page={page}&topics%5B%5D={topic}'.format(page=page, topic=topic)
            dom = html5lib.parse(self.get_HTML(url), namespaceHTMLElements=False)
            talks = dom.findall(".//div[@class='talk-link']")
            if not talks:
                if dom.find(".//div[@class='browse__no-results']") is not None:
                    # Some topics e.g. "advertising, at the time of writing, have no results.
                    return
                msg = "Cannot parse talks for topic '%s'." % (topic)
                self.logger(msg, friendly_message=msg)
                return

            failed_talks = 0
            for talk in talks:
                anchors = [x for x in talk.findall('.//a[@href]') if '/talks/' in x.attrib['href']]
                media_message = talk.find(".//div[@class='media__message']")
                title_container = media_message.find('.//a') if media_message else None
                if not anchors or title_container is None:
                    failed_talks += 1
                    continue
                
                speaker = img = None
                link = anchors[0].attrib['href']
                title = html.unescape(title_container.text.strip())
                speakers_container = [x for x in talk.findall('.//h4[@class]') if 'talk-link__speaker' in x.attrib['class']]
                if speakers_container is not None:
                    speaker = speakers_container[0].text.strip()
                img = talk.find('.//img[@src]')
                if img is not None:
                    img = img.attrib['src']

                yield title, URLTED + link, img, speaker

            pagination_div = dom.find(".//div[@class='pagination']")
            pagination_next = [x for x in pagination_div.findall('.//*[@class]') if 'pagination__next' in x.attrib['class']] if pagination_div else None
            if pagination_next is None:
                msg = "Cannot page talks for topic '%s'." % (topic)
                self.logger(msg, friendly_message=msg)
                return

            if 'disabled' in pagination_next[0].attrib['class']:
                # On last page, stop loop.
                if failed_talks:
                    msg = "Problem parsing {} talks for topic '{}'".format(failed_talks, topic)
                    self.logger(msg, friendly_message=msg)
                return

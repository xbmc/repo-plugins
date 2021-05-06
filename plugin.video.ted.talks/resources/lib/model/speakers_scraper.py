import html5lib

from .url_constants import URLTED

__url_speakers__ = URLTED + '/people/speakers?page=%s'

class Speakers:

    def __init__(self, get_HTML):
        self.get_HTML = get_HTML

    def __get_speaker_page__(self, index):
        return html5lib.parse(self.get_HTML(__url_speakers__ % (index)), namespaceHTMLElements=False)

    def __get_speaker_page_count__(self, dom):
        pagination_links = dom.findall(".//a[@class='pagination__item pagination__link']")
        return int(pagination_links[-1].text)

    def get_speaker_page_count(self):
        html = self.__get_speaker_page__(1)
        return self.__get_speaker_page_count__(html)

    def get_speakers_for_pages(self, pages):
        '''
        First yields the number of pages of speakers.
        After that yields tuples of title, link, img.
        '''

        returned_count = False
        for page in pages:
            dom = self.__get_speaker_page__(page)
            if not returned_count:
                returned_count = True
                yield self.__get_speaker_page_count__(dom)

            results = dom.findall(".//a[@class='results__result media media--sm-v m4']")

            for result in results:
                url = URLTED + result.attrib['href']
                title_heading = result.find('.//h4')
                title = title_heading.text + ' '.join([(str(x.text or '') + ' ' + str(x.tail or '')) for x in title_heading.findall('.//*')])
                title = ' '.join(title.split()) # Normalize whitespace.
                img = result.findall('.//img[@src]')
                img = img[0].attrib['src'] if img else None # Missing images?
                yield title, url, img

    def get_talks_for_speaker(self, url):
        '''
        Yields tuples of title, link, img.
        '''
        html = self.get_HTML(url)
        for result in html5lib.parse(html, namespaceHTMLElements=False).findall(".//div[@class='talk-link']"):
            link = result.find('.//a[@href]').attrib['href']
            img = result.find('.//img[@src]').attrib['src']
            title = result.find(".//div[@class='media__message']//a").text.strip()

            yield title, URLTED + link, img

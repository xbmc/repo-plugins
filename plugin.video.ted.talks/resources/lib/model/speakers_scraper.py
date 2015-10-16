from url_constants import URLTED
# Custom xbmc thing for fast parsing. Can't rely on lxml being available as of 2012-03.
import CommonFunctions as xbmc_common


__url_speakers__ = URLTED + '/people/speakers?page=%s'

class Speakers:

    def __init__(self, get_HTML):
        self.get_HTML = get_HTML

    def get_speaker_page_count(self):
        html = self.__get_speaker_page__(1)
        return self.__get_speaker_page_count__(html)

    def __get_speaker_page__(self, index):
        return self.get_HTML(__url_speakers__ % (index))

    def __get_speaker_page_count__(self, html):
        pages = xbmc_common.parseDOM(html, 'a', attrs={'class':'pagination__item pagination__link'})
        return int(pages[-1])

    def get_speakers_for_pages(self, pages):
        '''
        First yields the number of pages of speakers.
        After that yields tuples of title, link, img.
        '''

        returned_count = False
        for page in pages:
            html = self.__get_speaker_page__(page)
            if not returned_count:
                returned_count = True
                yield self.__get_speaker_page_count__(html)

            attrs = {'class': 'results__result media media--sm-v m4'}
            hrefs = xbmc_common.parseDOM(html, 'a', attrs, ret='href')
            content = xbmc_common.parseDOM(html, 'a', attrs)

            for result in zip(hrefs, content):
                url = URLTED + result[0]
                header = xbmc_common.parseDOM(result[1], 'h4')[0]
                title = ' '.join(header.replace('<br>', ' ').split())
                img = xbmc_common.parseDOM(result[1], 'img', ret='src')[0]
                yield title, url, img

    def get_talks_for_speaker(self, url):
        '''
        Yields tuples of title, link, img.
        '''
        html = self.get_HTML(url)
        for talk in xbmc_common.parseDOM(html, 'div', {'class':'talk-link'}):
            link = xbmc_common.parseDOM(talk, 'a', ret='href')[0]
            img = xbmc_common.parseDOM(talk, 'img', ret='src')[0]
            div = xbmc_common.parseDOM(talk, 'div', {'class':'media__message'})[0]
            title = xbmc_common.parseDOM(div, 'a')[0]

            yield title, URLTED + link, img

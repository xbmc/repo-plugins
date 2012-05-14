from url_constants import URLSPEAKERS
from BeautifulSoup import SoupStrainer, MinimalSoup
import re
from resources.lib.model.url_constants import URLTED


class Speakers:

    def __init__(self, get_HTML):
        self.get_HTML = get_HTML

    def get_speakers_for_letter(self, char):
        '''
        First yields the speaker count, or 0 if unknown.
        After that yields tuples of title, link, img.
        '''
        found_titles = set()
        page_index = 1
        found_on_last_page = 0
        html = self.get_HTML(URLSPEAKERS % (page_index, char))

        speaker_count = 0
        for h2 in MinimalSoup(html, SoupStrainer(name='h2')):
            if h2.findAll(text=re.compile('speakers whose Last Name begins with')):
                spans = h2.findAll(name='span')
                if spans:
                    try:
                        speaker_count = int(spans[-1].text.strip())
                    except ValueError:
                        pass

        yield speaker_count

        while True:
            containers = SoupStrainer(name='a', attrs={'href':re.compile('/speakers/.+\.html')})
            found_on_this_page = 0
            for speaker in MinimalSoup(html, parseOnlyThese=containers):
                if speaker.img:
                    title = speaker.img['alt'].strip()
                    if title not in found_titles:
                        found_titles.add(title)
                        found_on_this_page += 1
                        link = speaker['href']
                        img = speaker.img['src']
                        yield title, URLTED + link, img

            if found_on_this_page and found_on_this_page >= found_on_last_page:
                page_index += 1
                found_on_last_page = found_on_this_page
                html = self.get_HTML(URLSPEAKERS % (page_index, char))
            else:
                break

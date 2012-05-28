from url_constants import URLTED, URLTHEMES
from util import resizeImage
from BeautifulSoup import MinimalSoup, SoupStrainer
import re

class Themes:

    def __init__(self, get_HTML):
        self.get_HTML = get_HTML

    def get_themes(self):
        html = self.get_HTML(URLTHEMES)
        themeContainers = SoupStrainer(name='a', attrs={'href':re.compile('/themes/\S.+?.html')})
        # Duplicates due to themes scroll/banner at top
        seen_titles = set()
        for theme in MinimalSoup(html, parseOnlyThese=themeContainers):
            if theme.img:
                title = theme['title']
                if title not in seen_titles:
                    seen_titles.add(title)
                    link = URLTED + theme['href']
                    thumb = theme.img['src']
                    yield title, link, thumb

    def get_talks(self, url):
        url = url + "?page=%s"
        page_index = 1
        # Have to know when to stop paging, see condition for loop exit below.
        found_titles = set()
        found_on_last_page = 0

        html = self.get_HTML(url % (page_index))

        while True:
            containers = SoupStrainer('dl', {'class':re.compile('talkMedallion')})
            found_on_this_page = 0

            for talk in MinimalSoup(html, parseOnlyThese=containers):
                a_tag = talk.dt.a
                title = a_tag['title'].strip()
                if title not in found_titles:
                    found_titles.add(title)
                    found_on_this_page += 1
                    link = a_tag['href']
                    img_tag = a_tag.find('img', {'src':re.compile('http://images\.ted\.com/')})
                    img = img_tag['src']
                    yield title, URLTED + link, resizeImage(img)

            # Results on last page == results on (last page + 1), _not_ 0 as you might hope.
            # The second clause allows us to skip looking at last page + 1 if the last page contains
            # fewer results than that before it; which is usually but not always the case.
            if found_on_this_page and found_on_this_page >= found_on_last_page:
                page_index += 1
                found_on_last_page = found_on_this_page
                html = self.get_HTML(url % (page_index))
            else:
                break

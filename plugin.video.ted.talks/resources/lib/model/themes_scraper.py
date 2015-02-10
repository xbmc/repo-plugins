from url_constants import URLTED, URLTHEMES
# Custom xbmc thing for fast parsing. Can't rely on lxml being available as of 2012-03.
import CommonFunctions as xbmc_common

class Themes:

    def __init__(self, get_HTML):
        self.get_HTML = get_HTML

    def get_themes(self):
        html = self.get_HTML(URLTHEMES)
        themes_div = xbmc_common.parseDOM(html, 'div', {'class':'box themes'})[0]
        # Duplicates due to themes scroll/banner at top
        seen_titles = []
        for theme_li in xbmc_common.parseDOM(themes_div, 'li'):
            title = xbmc_common.parseDOM(theme_li, 'a', ret='title')[0]
            if title not in seen_titles:
                seen_titles.append(title)
                link = xbmc_common.parseDOM(theme_li, 'a', ret='href')[0]
                img_link = xbmc_common.parseDOM(theme_li, 'img', ret='src')[0]
                talk_count_p = xbmc_common.parseDOM(theme_li, 'p', {'class':'talk_count'})[0]
                talk_count = xbmc_common.parseDOM(talk_count_p, 'span')[0]
                yield title, URLTED + link, img_link, int(talk_count.strip())

    def get_talks(self, url):
        url = url + "?page=%s"
        page_index = 1
        html = self.get_HTML(url % (page_index))
        
        # Have to know when to stop paging, see condition for loop exit below.
        found_titles = set()
        found_on_last_page = 0

        while True:
            talk_list = xbmc_common.parseDOM(html, 'div', {'id':'talkList'})[0]
            found_before = len(found_titles)
            for dl in xbmc_common.parseDOM(talk_list, 'dl'):
                dt = xbmc_common.parseDOM(dl, 'dt')[0]
                title = xbmc_common.parseDOM(dt, 'a', ret='title')[0].strip()
                if title not in found_titles:
                    found_titles.add(title)
                    link = xbmc_common.parseDOM(dt, 'a', ret='href')[0]
                    for img_link in xbmc_common.parseDOM(dt, 'img', ret='src'):
                        if 'images.ted.com' in img_link:
                            yield title, URLTED + link, img_link
                            break

            # Results on last page == results on (last page + 1), _not_ 0 as you might hope.
            # The second clause allows us to skip looking at last page + 1 if the last page contains
            # fewer results than that before it; which is usually but not always the case.
            found_on_this_page = len(found_titles) - found_before
            if found_on_this_page and found_on_this_page >= found_on_last_page:
                page_index += 1
                found_on_last_page = found_on_this_page
                html = self.get_HTML(url % (page_index))
            else:
                break

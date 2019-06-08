import HTMLParser
import re
import urllib

import CommonFunctions as xbmc_common

from url_constants import URLTED, URLSEARCH

__results_count_re__ = re.compile(r'.*?\d+ - (\d+) of (\d+) results.*') # "331 - 360 of 333 results"
__result_count_re__ = re.compile(r'.*?\d+ +results?.*') # Two spaces at the moment i.e. "1  result"

class Search:

    def __init__(self, get_HTML):
        self.get_HTML = get_HTML

    def get_talks_for_search(self, search_string, page_index):
        '''
        Yields number of results left to show after this page,
        then tuples of title, link, img for results on this page.
        '''

        # TODO yield speakers, topics

        search_string = urllib.quote_plus(search_string)
        html = self.get_HTML(URLSEARCH % (search_string, page_index))

        results = xbmc_common.parseDOM(html, 'article', {'class': 'm1 search__result'})
        yield self._results_remaining(html, len(results)) 

        html_parser = HTMLParser.HTMLParser()
        for result in results:
            header = xbmc_common.parseDOM(result, 'h3')[0]
            url = xbmc_common.parseDOM(header, 'a', ret='href')[0]
            if not url.startswith('/talks/'):
                continue
            url = URLTED + url
            title = html_parser.unescape(xbmc_common.parseDOM(header, 'a')[0].strip())
            img = xbmc_common.parseDOM(result, 'img', ret='src')[0]
            yield title, url, img

    def _results_remaining(self, html, results):
        results_count_matches = __results_count_re__.findall(html)
        if results_count_matches:
            match = results_count_matches[0]
            last_on_page = int(match[0])
            total_results = int(match[1])
            return max(0, total_results - last_on_page)
        if __result_count_re__.findall(html):
            return 0  # All results on this page
        return 1 # We don't know so just make sure that it is positive so that we keep paging.

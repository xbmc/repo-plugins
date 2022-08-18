import html
import html5lib
import re
import urllib.parse

from .url_constants import URLTED


__url_search__ = URLTED + '/search?cat=videos&q=%s&page=%s'
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

        search_string = urllib.parse.quote_plus(search_string)
        search_url = __url_search__ % (search_string, page_index)
        search_content = self.get_HTML(search_url)

        results = html5lib.parse(search_content, namespaceHTMLElements=False).findall(".//article[@class='m1 search__result']")
        yield self._results_remaining(search_content, len(results)) 

        import xml.etree.ElementTree as ElementTree
        for result in results:
            url = result.find('.//a[@href]').attrib['href']
            if not url.startswith('/talks/'):
                continue
            url = URLTED + url
            title = html.unescape(result.find('.//h3/a').text.strip())
            img = result.find('.//img[@src]').attrib['src']
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

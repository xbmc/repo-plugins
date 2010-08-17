# Copyright 2010 Jonathan Beluch. 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import re
from urllib import unquote_plus
from beautifulsoup import BeautifulSoup as BS, SoupStrainer as SS
from resources.lib.xbmcvideoplugin import (XBMCVideoPlugin, DialogProgress,
    urlread, async_urlread, parse_qs)

"""Currently doesn't support all lectures on the website.  Some lectures
use a third party video hosting site (which are currently working) and
some lectures use embedded youtube videos (which are not currently 
supported)."""

IGNORE_LIST = ['Online Bachelor\'s Degrees',
               'Online Courses for Credit',
               'Online Master\'s Degrees',
               'Online Professional Certificates',
               'Courses for Credit',
               'Online Degrees']

class AcademicEarth(XBMCVideoPlugin):
    base_url = 'http://academicearth.org'
    subjects_url = '%s/subjects' % base_url

    def display_subjects(self, url):
        """Takes a url and displays subjects."""
        html = urlread(url)
        div_tags = BS(html, 
                      parseOnlyThese=SS('div', {'class': 'institution-list'}))
        #Build the list of subjects.  Sometimes there is more than one div_tag,
        #so loop through each div_tag, and then for each div_tag, loop through
        #all the <a> tags and parse the subject information.
        dirs = [{'name': a.text,
                 'url': self._urljoin(a['href']),
                 'mode': '1'}
                 for div in div_tags for a in div('a')]
        #Filter out the paid courses subjects
        dirs = [d for d in dirs if d['name'] not in IGNORE_LIST]
        self.add_dirs(dirs)

    def display_topics(self, url):
        """Takes a subject url and displays a list of all topics on the page"""
        html = urlread(url)
        #get the div which contains all of the topic <a> tags
        div_topics = BS(html, 
                        parseOnlyThese=SS('div', {'class': 'results-side'}))
        #create the list of dirs by parsing all the a tags in the div
        dirs = [{'name': a.text, 'url': self._urljoin(a['href']), 'mode': '2'} 
                for a in div_topics('a')]
        #filter out paid courses and the 'All' listing, since we build our own
        dirs = [d for d in dirs if d['name'].startswith('Online') == False and
                'Courses for Credit' not in d['name'] and
                d['name'].startswith('All') == False]
        #make the first choice on the list = 'View All'
        dirs.insert(0, {'name': self.getString(30100), 
                        'url': url, 'mode': '4'})
        self.add_dirs(dirs)

    def display_courses(self, url):
        """Takes a topic url and displays all courses"""
        html = urlread(url)
        courses, lectures = self._get_courses_lectures(html)
        #add listings to UI, courses first, lectures at the bottom.
        self.add_dirs(courses, end=False)
        self.add_videos(lectures)

    def display_lectures(self, url):
        """displays the lectures for a given course url"""
        html = urlread(url)
        #get the div which contains all of the <li> lecture tags
        div_tag = BS(html, parseOnlyThese=SS('div', {'class': 'results-list'}))
        #parse the name, url, desc, tn for each lecture
        dirs = [{'name': li.h4.a.text,
                 'htmlurl': self._urljoin(li.h4.a['href']),
                 'info': {'plot': li.p.text, 'title': li.h4.a.text},
                 'tn':self._urljoin(
                    li.find('img', {'class': 'thumb-144'})['src'])}
                 for li in div_tag('li')]
        #for each dir, download the lecture's html page and parse the video url
        self.dp = DialogProgress(self.getString(30000),
                                 line1=self.getString(30101),
                                 num_steps=(len(dirs)))
        urls = [d['htmlurl'] for d in dirs]
        responses = async_urlread(urls, self.dp)
        [d.update({'url': self._get_video_url(response)}) 
            for d, response in zip(dirs, responses)]
        #filter out lectures that don't have urls, currently a fix for a chem
        #course which contains a bad link to a lecture
        dirs = filter(lambda d: d['url'] != None, dirs)
        self.dp.update(100)
        self.dp.close()
        self.add_videos(dirs)

    def display_allresults(self, url):
        """displays all results for a given url, used on a subject page t lis
        all video results without having to drill down into each category"""
        #dp = self.xbmcgui.DialogProgress()
        html = urlread(url)
        #get the div which contains all of the topic <a> tags
        div_topics = BS(html, 
                        parseOnlyThese=SS('div', {'class': 'results-side'}))
        #create a list of urls for all topics
        topic_urls = [self._urljoin(a['href']) for a in div_topics('a')
            if a.text.startswith('Online') == False and
            'Credit' not in a.text and not a.text.startswith('All')]
        self.dp = DialogProgress(self.getString(30000),
                                 line1=self.getString(30102),
                                 num_steps=(2 * len(topic_urls)))
        topic_htmls = async_urlread(topic_urls, self.dp)
        courses, lectures = self._get_courses_lectures(topic_htmls)
        self.dp.update(100)
        self.dp.close()
        courses = sorted(courses, key=lambda c: c['name'])
        lectures = sorted(lectures, key=lambda l: l['name'])
        self.add_dirs(courses, end=False)
        self.add_videos(lectures)

    def _get_courses_lectures(self, htmls):
        """returns a tuple of lists: (courses_list, lectures_list).  It takes
        the html source(s) of a topic page and parses all results by visiting 
        each page of results"""
        if type(htmls).__name__ == 'str': htmls = [htmls]
        #Each topic page displays only 12 results to a page.  So to get all
        #results for a topic, parse all page results urls from the topic page,
        #then download each of the extra pages of results, then parse the video
        #results.
        pagination_urls = [url for html in htmls
                           for url in self._get_pagination_urls(html)]
        #Download every pagination page.  If a dialog progress box exists,
        #update the step for each increment.  Allocate 50% of the bar for
        #downloading the pagination urls.  The other 50% is allocated to
        #downloading all of the topic pages when choosing 'View All' for a
        #subject.
        if self.dp and len(pagination_urls) != 0:
            self.dp.step = int(50 / len(pagination_urls))
            page_htmls = async_urlread(pagination_urls, self.dp)
        else:
            page_htmls = async_urlread(pagination_urls)

        #extend the list of pagination htmls with the given htmls
        page_htmls.extend(htmls)
        #get a complete list of video results by parsing results from all pages
        results = self._get_video_results(page_htmls)
        #filter courses and lectures so they can be displayed in groups
        courses = filter(lambda r: '/courses/' in r['url'], results)
        lectures = filter(lambda r: '/lectures/' in r['url'], results)
        #add mode argument to courses, lectures don't need it since they will
        #contain a direct url to the video
        [c.update({'mode': 3}) for c in courses]
        #get the actual URL for the video for each lecture, this ensures that
        #the display link plays a video, and doesn't go to another level of 
        #directory listings
        [l.update({'url': self._get_video_url(l['url']),
                   'name': self.getString(30103) + l['name']}) 
                  for l in lectures]
        #filter out lectures with no video url.  This is a result of bad regex
        #parsing, crappy fix...
        lectures = [l for l in lectures if l['url'] is not None]
        return courses, lectures

    def _get_video_url(self, html):
        """Takes html for a video page and returns the url of the video"""
        m = re.search(r'flashVars.flvURL = "(.+?)"', html)
        if m: return m.group(1)
        return None

    def _get_pagination_urls(self, html):
        """Returns a list of urls for other results pages for given html."""
        #get the pagination <ul> tags
        ul_tags = BS(html, parseOnlyThese=SS('ul', {'class': 'pagination'}))
        #choose the first pagination <ul> tag since both <ul>s are identical
        ul = ul_tags('ul', limit=1)[0]
        #return the complete url for each link in the <ul>, ignore the last 
        #url in the list because it is the next page link, so it is already 
        #included
        return [self._urljoin(a['href']) for a in ul('a')[:-1]]

    def _get_video_results(self, htmls):
        """takes an html source(s) and a list of video results""" 
        video_results = []
        #if htmls is only a single html page, then convert htmls to a list with
        #a single item, the given html string
        if type(htmls).__name__ == 'str': htmls = [htmls]
        for html in htmls:
            div_results = BS(html, 
                parseOnlyThese=SS('div', {'class': 'video-results'}))
            #filter out empty <li> tags that only contain '&nbsp;'
            lis = [li for li in div_results('li') 
                   if li.get('class') != 'break']
            #build the list of results, a dict for each results
            res = [{'name': li.h3.text, 
                    'url': self._urljoin(li.a['href']),
                    'tn': self._urljoin(
                        li.find('img', {'class': 'thumb-144'})['src'])}
                   for li in lis]
            video_results.extend(res)
        return video_results

    def run(self, mode, url):
        #must pass default values for mode and url, mode is '0', url is ''
        mode_functions = {'0': self.display_subjects,
                         '1': self.display_topics,
                         '2': self.display_courses,
                         '3': self.display_lectures,
                         '4': self.display_allresults}
        mode_functions[mode](url)

    
if __name__ == '__main__':
    #parse command line parameters into a dictionary
    params = parse_qs(sys.argv[2])
    
    #create new app
    app = AcademicEarth(sys.argv[0], sys.argv[1])
    
    #run the app
    app.run(params.get('mode', '0'),
            unquote_plus(params.get('url', app.subjects_url)))


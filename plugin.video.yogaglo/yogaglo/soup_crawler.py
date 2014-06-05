from BeautifulSoup import BeautifulSoup
from urllib import urlencode
from urlparse import urljoin
from os.path import join
import re

from http import openUrl, convert_relative_to_absolute_url

"""
Crawls HTML pages for yogaglo specific information

"""
class SoupCrawler(object):
    """
    SoupCrawler encapsluates a yoga_glo_base_url and a class description url.

    """
    def __init__(self, yoga_glo_url):
        self.yoga_glo_url = yoga_glo_url
        self.classDescriptionAjaxUrl = convert_relative_to_absolute_url(
            yoga_glo_url, "/_ajax_get_class_description.php")

    def get_yoga_glo_navigation_information(self, yoga_glo_category):
	"""
	Gets basic yogaglo.com navigation information, cueing off of Category
	inputs from the homepages navigation bar (Teacher, Style, Level,
	Duration).

	Returns list of dictionaries with keys
	- title
	- url
	- image_url (optional)

	"""
        menuList = [] # list of dictionaries to return
        yogaglo = openUrl(self.yoga_glo_url)
        soup = BeautifulSoup(''.join(yogaglo))
        navInfo = soup.find('li', id=yoga_glo_category).findAll('a')
        
        for info in navInfo:
            infoTitle = info.contents[0]
            info_url = convert_relative_to_absolute_url(self.yoga_glo_url,
                                                        info['href'])
            # Looking at teachers, need images
            if yoga_glo_category == "2":
                teacherImageUrl = self.get_teacher_image_url(info_url)
                menu = {'title' : infoTitle, 'url' : info_url,
                        'image_url' : teacherImageUrl }
                menuList.append(menu)
                continue

            menu = {'title' : infoTitle, 'url' : info_url}
            menuList.append(menu)

        return menuList

    def get_teacher_image_url(self, teacher_url):
	"""
	Gets a yogaglo.com teacher's image url from the teacher_url to display
	on the screen.

	Returns aboslute url to teacher image.

	"""
        teacher_page = openUrl(teacher_url)
        soup = BeautifulSoup(teacher_page)
        img_section = soup.find('section', attrs={'class': 'cf'}).div.img
        return convert_relative_to_absolute_url(self.yoga_glo_url,
                                                img_section['src'])

    def crawl_videos(self, url):
	"""
	Crawls for yogaglo.com yoga videos information from the url.
	
	Opens url, and crawls the HTML returned.

	Returns a list of yoga videos HTML div elements, to further extract data
	from.  If there are no div tags, None is returned.

	"""
        html = openUrl(url)
        soup = BeautifulSoup(html)
        possible_video_sections = soup.findAll('section', attrs={'class':'cf'})
        for video_section in possible_video_sections:
            yoga_glo_classes_divs = video_section.findAll('div',
                                                 id=re.compile('^[0-9]+'))
            if yoga_glo_classes_divs:
                return yoga_glo_classes_divs

    def get_classes(self, url):
	"""
	Gets the yogaglo.com yoga classes information from the HTML div tags
	present on the page.

	Returns a list of dictionaries with class information

	"""
        classes = [] # return array of dictionaries
        video_divs = self.crawl_videos(url)
        for video_div in video_divs:
            class_cover_picture_url = video_div.a.img['src'].encode('utf-8')
            class_url = convert_relative_to_absolute_url(self.yoga_glo_url,
                                                         video_div.a['href'])
            class_length = video_div.findAll('div')[3].contents[0]
            class_id = video_div['id']
            class_information = self.get_yoga_class_description(class_id)
            class_information['url'] = class_url
            class_information['coverPicUrl'] = class_cover_picture_url
            class_information['duration'] = int(class_length.split(" ")[0])
            classes.append(class_information)

        return classes

    def get_yoga_class_description(self, class_id):
	"""
	Gets the class description for class_id from the ajax request on the
	site. I wish this was better formed HTML, but this is what you get --
	must comply.

	Returns a dictionary with class information.

	"""
        # AJAX query params to get description html
        query = urlencode({ 'id' : class_id, 't': 0 })
        url = urljoin(self.classDescriptionAjaxUrl, "?" + query)
        class_description = openUrl(url)
        soup = BeautifulSoup(class_description)
        style = soup.i.nextSibling
        # malformed HTML - sometimes missing a class title
        # default to the class style so you know this in xbmc menu
        # TODO something else here, like color it to make it different
        try:
            title = soup.b.contents[0]
        except:
            title = style

        level = soup.findAll('i')[1].nextSibling
        # any teachers from this ajax call are already expressed in unicode
        # not the \xe9, it takes percent encoded %C3%A9 to unicode \xc3\xa9
        teacher = soup.findAll('i')[2].nextSibling

        # Some class descriptions span multiple br's
        # key off the 'grayline' div and all text after that is a description
        fullDesc = ""
        grayline = soup.find('div', attrs={'class': 'grayline'})
        descriptionElements = grayline.findAllNext(text=True)
        for descElement in descriptionElements:
            fullDesc += descElement

        return {'title' : title,
                'secondLabel' :
                "Style: " + style + " Level: " + level,
                'plot' : fullDesc,
                'style' : style,
                'level' : level,
                'teacher' : teacher }

    def get_yogaglo_video_information(self, url, cookie_path):
	"""
	Gets the yogaglo.com video information from the url for streaming in the
	plugin (rtmp url, swf url, play path) from the javascript inside the
	sites page.

	This is the authorized video information (using a cookie), full length
	highest quality video available.

	Returns a dictionary of video information.

	"""
        html = openUrl(url, cookie_path)
        swf_url = re.compile(".*url: '([^']*)'").findall(html)[0]
        play_path = re.compile('url: "([^"]*)"').findall(html)[0]
        rtmp_base_url = re.compile(
            "netConnectionUrl:\s+'([^']*)'").findall(html)[0]
        # rtmp protocol won't join properl from urlparse.urljoin
        rtmp_url = join(rtmp_base_url, play_path)
        return {'swf_url': swf_url, 'rtmp_url': rtmp_url,
                'play_path': play_path}

    def get_yogaglo_preview_video_information(self, url):
	"""
	Gets the yogaglo.com video information from the url for streaming in the
	plugin (rtmp url, swf url, play path) from the javascript inside the
	sites page.

	This is the un-authorized video page, the 5-minute preview feed available.

	Returns a dictionary of video information.

	"""
        html = openUrl(url)
        play_path = re.compile("url: '(mp4[^']*)'").findall(html)[0]
        swf_url = re.compile("url:\s+'([^mp4]+[^']*)'").findall(html)[0]
        rtmp_base_url = re.compile(
            "netConnectionUrl:\s+'([^']*)'").findall(html)[0]
        # rtmp protocol won't join properl from urlparse.urljoin
        rtmp_url = join(rtmp_base_url, play_path)
        return {'swf_url': swf_url, 'rtmp_url': rtmp_url,
                'play_path': play_path}

    def get_yoga_of_the_day_title_and_info(self):
	"""
	Gets the yogaglo.com "Yoga of the Day" video information from the homepage.

	Returns a dictionary of yoga of the day information.

	"""
        url = openUrl(self.yoga_glo_url)
        yotd = BeautifulSoup(url)
        yotd_section = yotd.find('section', attrs={'class': 'home_vids'})
        yotd_info = yotd_section.findNext('p')

        return {'title' : yotd_section.h1.contents[0],
                'information' : yotd_info.contents[0].encode('utf-8') }


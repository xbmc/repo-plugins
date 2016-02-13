import requests
from BeautifulSoup import BeautifulSoup
from urlparse import urlparse


BASE_URL = 'https://www.thenewboston.com/videos.php'


def get_lesson_id(url):
    return int(url.split('=')[-1])


def get_categories():
    """Scrape categories from homepage."""
    page = requests.get(BASE_URL, verify=False)
    soup = BeautifulSoup(page.content)
    output = [{'title': u'Most Popular Courses'}]

    for c in (
        soup.find(id='content-wrapper').findAll('div', 'video-category-panel')
    ):
        output.append({'title': c.find('span', 'panel-title').text})

    return output


def get_topics(category):
    """Scrape topics from homepage."""
    page = requests.get(BASE_URL, verify=False)
    soup = BeautifulSoup(page.content)

    content = soup.find(id='content-wrapper')
    output = []

    if category == u'Most Popular Courses':
        courses = content.find('table', 'videos-top-courses')

        for item in courses.findAll('tr'):
            link = courses.findAll('tr')[0].a['href']
            thumbnail = item.find('img').get('src')
            title = item.h4.text.replace('&nbsp;', '').strip()

            output.append({
                'thumbnail': thumbnail,
                'title': title,
                'lesson_id': get_lesson_id(link)})

    for panel in content.findAll('div', 'video-category-panel'):
        found_category = panel.find('span', 'panel-title').text

        if found_category == category:
            for item in panel.find('div', 'list-group').findAll('a'):
                output.append({
                    'title': item.text,
                    'lesson_id': get_lesson_id(item['href'])})
            break

    return output


def get_lessons(lesson_id):
    """Retrieve lessons from the lesson pages."""
    url = '{0}?cat={1}'.format(BASE_URL, lesson_id)
    page = requests.get(url, verify=False)
    soup = BeautifulSoup(page.content)
    output = []

    for item in soup.find(id='main-menu').find('ul', 'navigation').findAll('li'):
        video_id = item.a['href'].split('=')[-1]
        title = item.a.text
        output.append({
            'title': title, 'lesson_id': lesson_id,
            'video_id': video_id})

    return output


def get_video(lesson_id, video_id):
    """Retrieve a Youtube id from a video page."""
    url = '{0}?cat={1}&video={2}'.format(BASE_URL, lesson_id, video_id)
    page = requests.get(url, verify=False)
    soup = BeautifulSoup(page.content)
    return urlparse(soup.find('iframe')['src']).path.split('/')[-1]

import requests
from BeautifulSoup import BeautifulSoup


BASE_URL = 'https://www.thenewboston.com/videos.php'


def get_categories():
    """Scrape categories from homepage."""
    page = requests.get(BASE_URL, verify=False)
    soup = BeautifulSoup(page.content)
    output = [{'title': 'Top 10 Courses'}]

    for c in soup.find(id='main_aside').findAll('h4'):
        output.append({'title': c.text})

    return output


def get_topics(category):
    """Scrape topics from homepage."""
    page = requests.get(BASE_URL, verify=False)
    soup = BeautifulSoup(page.content)
    output = []
    get_lesson_id = lambda url: url.split('=')[-1]

    if category == 'Top 10 Courses':
        playlist = soup.find(id='featured_playlists')
        for item in playlist.findAll('div', 'item'):
            link = item.find('a', 'featured-playlist-title')
            output.append({
                'thumbnail': item.find('img').get('src'),
                'title': link.text.replace('&nbsp;', '').strip(),
                'lesson_id': get_lesson_id(link['href'])})
    else:
        sidebar = soup.find(id='main_aside')
        for dl in sidebar.findAll('dl'):
            if dl.find('h4').text == category:
                for item in dl.findAll('dd'):
                    link = item.find('a', 'category-name')
                    output.append({
                        'title': link.getText(' '),
                        'lesson_id': get_lesson_id(link['href'])})

    return output


def get_lessons(lesson_id):
    """Retrieve lessons from the lesson pages."""
    url = '{0}?cat={1}'.format(BASE_URL, lesson_id)
    page = requests.get(url, verify=False)
    soup = BeautifulSoup(page.content)
    output = []

    for item in soup.find(id='playlist').findAll('dd'):
        video_id = item.find('a')['href'].split('=')[-1]
        title = item.find('a').text
        output.append({
            'title': title, 'lesson_id': lesson_id,
            'video_id': video_id})

    return output


def get_video(lesson_id, video_id):
    """Retrieve a Youtube id from a video page."""
    url = '{0}?cat={1}&video={2}'.format(BASE_URL, lesson_id, video_id)
    page = requests.get(url, verify=False)
    soup = BeautifulSoup(page.content)
    return soup.find('iframe')['src'].split('/')[-1]

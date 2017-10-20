import requests
from BeautifulSoup import BeautifulSoup
from dateutil.parser import parse as datetimeparse
import re
import json


quality_re = re.compile(r'\d+(?=p)')
nl_only_categories = [
    u'NOS Sportjournaal',
    u'NOS Studio Sport',
    u'NOS Studio Sport Eredivisie',
    u'NOS Studio Voetbal',
]


def index():
    data = []
    url = u'https://nos.nl/uitzendingen/'
    response = requests.request(
        method=u'GET',
        url=url,
    )
    soup = BeautifulSoup(response.content)
    categories_container = soup.findAll(id=u'programs')[0]
    categories = categories_container.findAll(u'li')
    for category in categories:
        category_anchor = category.findAll(u'a')[0]
        category_text = category_anchor.text
        category_url = category_anchor[u'href']
        if category_text in nl_only_categories:
            category_text = u'{category_text} (georestricted NL only)'.format(
                category_text=category_text
            )
        if category_url.startswith(u'/uitzending/'):
            data.append(
                {
                    u'label': category_text,
                    u'path': {
                        u'endpoint': u'show_category',
                        u'category_url': (
                            u'https://nos.nl{category_url}'
                            .format(category_url=category_url)
                        ),
                    },
                }
            )
    return data


def show_category(category_url):
    data = []
    response = requests.request(
        method=u'GET',
        url=category_url,
    )
    soup = BeautifulSoup(response.content)
    videos = soup.findAll(
        u'li',
        {u'class': u'broadcast-player__playlist__item'},
    )
    for video in videos:
        title = video.findAll(
            u'span',
            {u'class': u'broadcast-link__name '},
        )[0].text
        timecode = video.findAll(u'time')[0][u'datetime']
        parsed_timecode = datetimeparse(timecode)
        label = u'{title} {time}'.format(
            title=title,
            time=parsed_timecode.strftime(u'%Y-%m-%d %H:%M'),
        )
        video_url = video.findAll(u'a')[0][u'href']
        data.append(
            {
                u'label': label,
                u'path': {
                    u'endpoint': u'show_video',
                    u'video_url': u'https://nos.nl{video_url}'.format(
                        video_url=video_url,
                    ),
                },
                u'is_playable': True,
            }
        )
    return data


def video_url_to_file_url(video_url):
    response = requests.request(
        method=u'GET',
        url=video_url,
    )
    soup = BeautifulSoup(response.content)
    video = soup.findAll(u'video')[0]
    geoprotected = video.get(u'data-geoprotection', False)
    sources = video.findAll(u'source')
    sources = sorted(
        sources,
        key=lambda source: int(
            quality_re.search(source[u'data-label']).group(0)
        ),
        reverse=True,
    )
    preferred_source = sources[0]
    if geoprotected:
        url = None
        response = requests.request(
            method=u'POST',
            url=u'https://nos.nl/video/resolve/',
            data=json.dumps([{u'file': preferred_source[u'src']}]),
        ).json()
        url = response[0][u'file']
    else:
        url = preferred_source['src']
    return url

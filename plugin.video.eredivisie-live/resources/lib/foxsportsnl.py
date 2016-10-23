import requests
from BeautifulSoup import BeautifulStoneSoup


def index():
    url = 'http://mapi.foxsports.nl/api/mobile/v1/videos/home'
    response = requests.request(
        method='GET',
        url=url,
    ).json()
    response = sorted(
        response,
        key=lambda item: item['id'],
    )
    return [
        {
            'label': item['name'],
            'path': {
                'endpoint': 'show_category',
                'category_id': item['id'],
            },
        }
        for item in response
    ]


def show_category(category_id):
    url = 'http://mapi.foxsports.nl/api/mobile/v1/articles/category/{category_id}'.format(
        category_id=category_id,
    )

    response = requests.request(
        method='GET',
        url=url,
    ).json()

    return [
        {
            'label': item['title'],
            'thumbnail': item['image'].format(size='576x300'),
            'path': {
                'endpoint': 'show_video',
                'video_id': item['id'],
            },
            'is_playable': True,
        }
        for item in response
    ]


def video_id_to_playlist_url(video_id):
    url = 'http://www.foxsports.nl/divadata/Output/VideoData/{video_id}.xml'.format(
        video_id=video_id,
    )

    response = requests.request(
        method='GET',
        url=url,
    )

    soup = BeautifulStoneSoup(response.text)
    playlist_url = (
        soup
        .find(name='videosource', attrs={'format': 'HLS'})
        .find('uri')
        .text
    )
    return playlist_url

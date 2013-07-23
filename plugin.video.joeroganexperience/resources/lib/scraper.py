import urllib2
import json

from BeautifulSoup import BeautifulSoup


def get(url):
    """ Return the contents of the page as a string """
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    output = response.read()
    response.close()

    return output.decode('ascii', 'ignore')


def get_podcasts(html):
    """ Return a list of tuples like (name, slug, thumbnail)"""
    output = []

    soup = BeautifulSoup(html)
    podcasts = soup.findAll('div', 'episode')
    for podcast in podcasts:
        thumb_section = podcast.find('div', 'podcast-thumb')
        name = thumb_section.find('a', 'autoplay')['data-title']
        slug = thumb_section.find('a', 'autoplay')['data-slug']
        thumb = thumb_section.find('img')['src']
        output.append(
            (name, slug, thumb))

    return output


def get_video_id(content):
    """ Return a dictionary containing video information """
    data = json.loads(content)

    if 'response' in data:
        html = data['response']['html']
        soup = BeautifulSoup(html)
        link = soup.find('a', 'podcast-video-container')
        provider, vid_id = link['data-video-provider'], link['data-video-id']
        if not provider:
            audio_link = soup.find('a', 'download-episode')['href']
            provider = 'audio'
            vid_id = audio_link

        return {'provider': provider, 'id': vid_id}

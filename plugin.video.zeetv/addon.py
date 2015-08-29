from BeautifulSoup import BeautifulSoup
import os.path
import sys
import urlparse
import xbmcplugin
from resources.lib import helpers as h


def main_index():
    h.add_dir(addon_handle, base_url, 'Current Shows', SHOWS_URL, 'CurrentShows')
    h.add_dir(addon_handle, base_url, 'Archive Shows', SHOWS_URL, 'ArchiveShows')


def current_shows():
    url = h.extract_var(args, 'url')

    soup = BeautifulSoup(h.make_request(url, cookie_file, cookie_jar))

    h2s = h.bs_find_all_with_class(soup, 'h2', 'bubble-title')

    # XXX: If want sorted
    # import operator
    # shows = {}
    # shows[a_attrs['href']] = a_attrs['title']
    # shows = sorted(shows.items(), key=operator.itemgetter(1))

    # XXX: View mode thumbnail supported in xbmcswift2

    h2 = None
    for h2 in h2s:
        if h2.text == 'Current Shows':
            for li in h2.findNext('ul').findAll('li'):
                a = li.find('a')
                a_attrs = dict(a.attrs)
                img_src = dict(a.find('img').attrs)['src']
                h.add_dir(addon_handle, base_url, a_attrs['title'], a_attrs['href'], 'show', img_src, img_src)
            break


def archive_shows():
    url = h.extract_var(args, 'url')

    soup = BeautifulSoup(h.make_request(url, cookie_file, cookie_jar))

    ul = h.bs_find_with_class(soup, 'ul', 'archive-shows')

    for li in ul.findAll('li'):
        a = li.find('a')
        a_attrs = dict(a.attrs)
        h.add_dir(addon_handle, base_url, a_attrs['title'], a_attrs['href'], 'show')


def show():
    url = h.extract_var(args, 'url')

    url = '%svideo/' % (url)

    soup = BeautifulSoup(h.make_request(url, cookie_file, cookie_jar))

    info_div = h.bs_find_with_class(soup, 'div', 'video-n-info-wrap')

    pagination = h.bs_find_with_class(info_div, 'ul', 'pagination')
    pages = {
        'prev': [],
        'next': []
    }
    page_type = 'prev'
    if pagination:
        pages_li = pagination.findAll('li')[1:-1]
        for li in pages_li:
            attrs = dict(li.attrs)
            if 'class' in attrs and attrs['class'] == 'active':
                page_type = 'next'
            else:
                a = li.find('a')
                a_attrs = dict(a.attrs)
                pages[page_type].append({
                    'href': a_attrs['href'],
                    'page': a.text
                })

    for page in pages['prev']:
        h.add_dir(addon_handle, base_url, '<< Page %s' % page['page'], page['href'], 'show')

    related_div = h.bs_find_with_class(info_div, 'div', 'related-videos')
    ul = related_div.find('ul')
    for li in ul.findAll('li'):
        a = li.find('a')
        a_attrs = dict(a.attrs)
        href = a_attrs['href']
        # if href.endswith('-full-episode.html'):
        h.add_dir(addon_handle, base_url, a_attrs['title'], href, 'episode', dict(a.find('img').attrs)['src'])

    for page in pages['next']:
        h.add_dir(addon_handle, base_url, '>> Page %s' % page['page'], page['href'], 'show')


def episode():
    url = h.extract_var(args, 'url')

    name = h.extract_var(args, 'name')

    soup = BeautifulSoup(h.make_request(url, cookie_file, cookie_jar))

    div = h.bs_find_with_class(soup, 'div', 'video-player')
    script = div.find('script')
    url = ''
    if script:
        url = script.text.split('bigmumbai = ', 2)[2].split(';')[0][1:-1]
        plot = h.bs_find_with_class(soup, 'div', 'vp-info').find('span', {'itemprop': 'description'}).text
        thumbnail = soup.find('div', {'itemprop': 'video'}).find('meta', {'itemprop': 'thumbnailUrl'})['content']
        h.add_dir_video(addon_handle, name, url, thumbnail, plot)
    else:
        iframe = div.find('iframe')
        if iframe:
            attrs = dict(iframe.attrs)
            youtube_url = attrs['src']
            video_id = urlparse.urlparse(youtube_url).path.replace('/embed/', '')
            url = 'plugin://plugin.video.youtube/play/?video_id=%s' % video_id
            print url
            h.add_dir_video(addon_handle, name, url, '', '')


def not_implemented():
    pass

ZEETV_REFERRER = 'http://www.zeetv.com'
SHOWS_URL = '%s/shows/' % ZEETV_REFERRER

addon_id = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
cookie_file, cookie_jar = h.init_cookie_jar(addon_id)

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get('mode', ['', ])[0]

if mode == 'CurrentShows':
    current_shows()
elif mode == 'ArchiveShows':
    archive_shows()
elif mode == 'show':
    show()
elif mode == 'episode':
    episode()
elif mode == 'not_implemented':
    not_implemented()
else:
    main_index()

xbmcplugin.endOfDirectory(addon_handle)

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

    # XXX: If want sorted
    # import operator
    # shows = {}
    # shows[a_attrs['href']] = a_attrs['title']
    # shows = sorted(shows.items(), key=operator.itemgetter(1))

    # XXX: View mode thumbnail supported in xbmcswift2

    h2 = soup.findAll('h2')

    for h2 in soup.findAll('h2'):
        if h2.text == 'Shows':
            for li in h2.nextSibling.find('ul').findAll('li'):
                a = li.find('a')
                a_attrs = dict(a.attrs)
                title = '%s (%s)' % (h.bs_find_with_class(a, 'div', 'zc-show-title').text, h.bs_find_with_class(a, 'div', 'zc-air-time').text)
                img_src = dict(a.find('img').attrs)['src']
                h.add_dir(addon_handle, base_url, title, '%s/video/' % a_attrs['href'], 'show', img_src, img_src)
            break


def archive_shows():
    url = h.extract_var(args, 'url')

    soup = BeautifulSoup(h.make_request(url, cookie_file, cookie_jar))

    h2 = soup.findAll('h2')

    for h2 in soup.findAll('h2'):
        if h2.text == 'Archive Shows':
            for div in h.bs_find_all_with_class(h2.nextSibling, 'div', 'archive-show'):
                a = div.find('a')
                a_attrs = dict(a.attrs)
                h.add_dir(addon_handle, base_url, a_attrs['title'], '%s/video/' % a_attrs['href'], 'show')
            break


def show():
    url = h.extract_var(args, 'url')

    url = '%s%s' % (ZEEMARATHI_REFERRER, url)

    soup = BeautifulSoup(h.make_request(url, cookie_file, cookie_jar))

    ul = soup.find('ul', {'class': lambda x: x and 'show-videos-list' in x.split()})
    for li in ul:
        div = li.find('div', {'class': lambda x: x and 'video-watch' in x.split()})
        episode_url = div.find('a')['href']
        name = li.find('div', {'class': 'video-episode'}).text
        img_src = 'DefaultFolder.png'
        img = li.find('img')
        if img:
            img_src = img['src']

        h.add_dir(addon_handle, base_url, name, episode_url, 'episode', img_src, img_src)

    pager = soup.find('ul', {'class': lambda x: x and 'pager' in x.split()})
    if pager:
        next_link = pager.find('li', {'class': lambda x: x and 'pager-next' in x.split()})
        if next_link:
            next_url = next_link.find('a')['href']
            if next_url:
                h.add_dir(addon_handle, base_url, 'Next >>', next_url, 'show')


def episode():
    url = h.extract_var(args, 'url')

    name = h.extract_var(args, 'name')

    soup = BeautifulSoup(h.make_request(url, cookie_file, cookie_jar))

    script = soup.find('div', {'id': 'block-gec-videos-videopage-videos'}).find('script')

    master_m3u8 = script.text.split('babyenjoying = ', 2)[2].split(';')[0][1:-1]

    plot = soup.find('p', {'itemprop': 'description'}).text
    thumbnail = soup.find('meta', {'itemprop': 'thumbnailUrl'})['content']

    h.add_dir_video(addon_handle, name, master_m3u8, thumbnail, plot)


def not_implemented():
    pass

ZEEMARATHI_REFERRER = 'http://www.zeemarathi.com'
SHOWS_URL = '%s/shows/' % ZEEMARATHI_REFERRER

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

from BeautifulSoup import BeautifulSoup
import cookielib
import urllib
import urllib2
import urlparse
import operator
import os
import os.path
import sys
import xbmc
import xbmcgui
import xbmcplugin


USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.130 Safari/537.36'
ZEEMARATHI_REFERRER = 'http://www.zeemarathi.com'


def build_url(query):
    return base_url + '?' + urllib.urlencode(query)


def add_dir(name, url, mode, icon_image='DefaultFolder.png', is_folder=True, background=None):
    global addon_handle

    u = build_url({'url': urllib.quote(url, safe=''), 'mode': str(mode), 'name': urllib.quote(name, safe='')})
    liz = xbmcgui.ListItem(unicode(name), iconImage=icon_image, thumbnailImage=icon_image)

    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=is_folder)

    return ok


def make_request(url):
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
    request = urllib2.Request(url)
    request.add_header('User-Agent', USER_AGENT)
    response = opener.open(request)
    data = response.read()
    cookie_jar.save(cookie_file, ignore_discard=True)

    return data


def get_episodes(url):
    episodes = []
    data = make_request(url)

    soup = BeautifulSoup(data)

    ul = soup.find('ul', {'class': lambda x: x and 'show-videos-list' in x.split()})
    for li in ul:
        div = li.find('div', {'class': lambda x: x and 'videos' in x.split()})

        episode_url = li.find('div', {'class': lambda x: x and 'video-watch' in x.split()}).find('a')['href']
        name = li.find('div', {'class': 'video-episode'}).text
        img_src = 'DefaultFolder.png'
        img = li.find('img')
        if img:
            img_src = img['src']

        episodes.append({'name': name, 'url': episode_url, 'mode': 'episode', 'icon_image': img_src})

    pager = soup.find('ul', {'class': lambda x: x and 'pager' in x.split()})
    if pager:
        next_link = pager.find('li', {'class': lambda x: x and 'pager-next' in x.split()})
        if next_link:
            next_url = next_link.find('a')['href']
            episodes += get_episodes(ZEEMARATHI_REFERRER + next_url)

    return episodes

addon_id = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
print addon_id
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get('mode', [''])[0]

addon_data_dir = os.path.join(xbmc.translatePath('special://userdata/addon_data').decode('utf-8'), addon_id)
if not os.path.exists(addon_data_dir):
    os.makedirs(addon_data_dir)

cookie_file = os.path.join(addon_data_dir, 'cookies.lwp')

cookie_jar = cookielib.LWPCookieJar()
if os.path.exists(cookie_file):
    cookie_jar.load(cookie_file, ignore_discard=True)

if mode == 'show':
    # show_name = args['name'][0]

    url = '%s%s/video' % (ZEEMARATHI_REFERRER, urllib.unquote(args['url'][0]))
    episodes = get_episodes(url)

    for episode in episodes:
        add_dir(episode['name'], episode['url'], episode['mode'], episode['icon_image'])

elif mode == 'episode':
    url = urllib.unquote(args['url'][0])
    name = urllib.unquote(args['name'][0])

    data = make_request(url)

    soup = BeautifulSoup(data)

    script = soup.find('div', {'id': 'block-gec-videos-videopage-videos'}).find('script')

    master_m3u8 = script.text.split('babyenjoying = ', 2)[2].split(';')[0][1:-1]
    
    plot = soup.find('p', {'itemprop': 'description'}).text
    thumbnail = soup.find('meta', {'itemprop': 'thumbnailUrl'})['content']

    liz = xbmcgui.ListItem(name, iconImage='DefaultVideo.png', thumbnailImage=thumbnail)
    liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=master_m3u8, listitem=liz)

else:
    url = '%s/shows' % ZEEMARATHI_REFERRER
    data = make_request(url)

    soup = BeautifulSoup(data)

    shows = {}

    for h2 in soup.findAll('h2'):
        if h2.text == 'Shows':
            for li in h2.nextSibling.find('ul').findAll('li'):
                attrs = dict(li.find('a').attrs)
                shows[attrs['href']] = attrs['title']
        elif h2.text == 'Archive Shows':
            for div in h2.nextSibling.findAll('div', {'class': lambda x: x and 'archive-show' in x.split()}):
                attrs = dict(div.find('a').attrs)
                shows[attrs['href']] = attrs['title']

    shows = sorted(shows.items(), key=operator.itemgetter(1))

    for url, name in shows:
        add_dir(name, url, 'show')

xbmcplugin.endOfDirectory(addon_handle)

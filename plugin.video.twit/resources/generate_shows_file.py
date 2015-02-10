import urllib2
from bs4 import BeautifulSoup

thumbs = {
    'All About Android': 'http://feeds.twit.tv/coverart/aaa1400.jpg',
    'Android App Arena': 'http://feeds.twit.tv/coverart/arena1400.jpg',
    'Before You Buy': 'http://feeds.twit.tv/coverart/byb1400.jpg',
    'Coding 101': 'http://feeds.twit.tv/coverart/code1400.jpg',
    'FLOSS Weekly': 'http://feeds.twit.tv/coverart/floss1400.jpg',
    'Ham Nation': 'http://feeds.twit.tv/podcasts/coverart/hn1400.jpg',
    'Home Theater Geeks': 'http://feeds.twit.tv/coverart/htg1400.jpg',
    'iFive for the iPhone': 'http://feeds.twit.tv/coverart/ifive1400.jpg',
    'iPad Today': 'http://feeds.twit.tv/coverart/ipad1400.jpg',
    'Know How...': 'http://feeds.twit.tv/coverart/kh1400.jpg',
    'MacBreak Weekly': 'http://feeds.twit.tv/podcasts/coverart/mbw1400.jpg',
    'Marketing Mavericks': 'http://feeds.twit.tv/podcasts/coverart/mm1400.jpg',
    'OMGcraft': 'http://feeds.twit.tv/coverart/omgcraft1400.jpg',
    "Padre's Corner": 'http://feeds.twit.tv/coverart/padre1400.jpg',
    'redditUP': 'http://feeds.twit.tv/coverart/ru1400.jpg',
    'Security Now': 'http://feeds.twit.tv/coverart/sn1400.jpg',
    'Tech News Today': 'http://feeds.twit.tv/coverart/tnt1400.jpg',
    'Tech News 2Night': 'http://feeds.twit.tv/coverart/tn2n1400.jpg',
    'The Giz Wiz': 'http://feeds.twit.tv/coverart/dgw1400.jpg',
    'The Social Hour': 'http://feeds.twit.tv/coverart/tsh1400.jpg',
    'The Tech Guy': 'http://feeds.twit.tv/coverart/ttg1400.jpg',
    'This Week in Computer Hardware': 'http://feeds.twit.tv/coverart/twich1400.jpg',
    'This Week in Enterprise Tech': 'http://feeds.twit.tv/coverart/twiet1400.jpg',
    'This Week in Google': 'http://feeds.twit.tv/coverart/twig1400.jpg',
    'This Week in Law': 'http://feeds.twit.tv/coverart/twil1400.jpg',
    'This Week in Tech': 'http://feeds.twit.tv/coverart/twit1400.jpg',
    'Triangulation': 'http://feeds.twit.tv/coverart/tri1400.jpg',
    'TWiT Live Specials': 'http://feeds.twit.tv/podcasts/coverart/specials1400.jpg',
    'Windows Weekly': 'http://feeds.twit.tv/coverart/ww1400.jpg',
    'All TWiT Shows': 'http://feeds.twit.tv/coverart/all1400.jpg',
    'Radio Leo': 'http://feeds.twit.tv/coverart/radioleo1400.jpg',
    'TWiT Bits': 'http://feeds.twit.tv/coverart/bits1400.jpg',
    "Abby's Road": 'http://feeds.twit.tv/coverart/abby600.jpg',
    'Current Geek Weekly': 'http://feeds.twit.tv/coverart/cgw600.jpg',
    "Dr. Kiki's Science Hour": 'http://feeds.twit.tv/coverart/dksh600.jpg',
    'FourCast': 'http://feeds.twit.tv/coverart/fc600.jpg',
    'Frame Rate': 'http://feeds.twit.tv/coverart/fr1400.jpg',
    'Futures in Biotech': 'http://feeds.twit.tv/coverart/fib600.jpg',
    'Game On!': 'http://feeds.twit.tv/coverart/go600.jpg',
    'Green Tech Today': 'http://feeds.twit.tv/coverart/gtt600.jpg',
    'Jumping Monkeys': 'http://feeds.twit.tv/coverart/jm300.jpg',
    'The Laporte Report': 'http://feeds.twit.tv/coverart/tlr300.jpg',
    "Maxwell's House": 'http://feeds.twit.tv/coverart/mh600.jpg',
    'Munchcast': 'http://feeds.twit.tv/coverart/mc300.jpg',
    'NSFW': 'http://feeds.twit.tv/coverart/nsfw1400.jpg',
    'Roz Rows the Pacific': 'http://feeds.twit.tv/coverart/roz300.jpg',
    'Tech History Today': 'http://feeds.twit.tv/coverart/tht600.jpg',
    'This WEEK in FUN': 'http://feeds.twit.tv/coverart/twif600.jpg',
    'This Week in Radio Tech': 'http://feeds.twit.tv/coverart/twirt600.jpg',
    'This Week in YouTube': 'http://feeds.twit.tv/coverart/yt1400.jpg',
    "Trey's Variety Hour": 'http://feeds.twit.tv/coverart/tvh600.jpg',
    'TWiT Photo': 'http://feeds.twit.tv/coverart/photo600.jpg',
    }


def make_request(url, locate=False):
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        if locate:
            return response.geturl()
        return data
    except urllib2.URLError, e:
        print( 'We failed to open "%s".' %url)
        if hasattr(e, 'reason'):
            print('We failed to reach a server.')
            print('Reason: %s' %e.reason)
        if hasattr(e, 'code'):
            print('We failed with error code - %s.' %e.code)


shows_dict = {'active': {}, 'retired': {}}
count = 0
soup = BeautifulSoup(make_request('http://twit.tv/shows'), 'html.parser')
active_list = soup.findAll('div', attrs={'class' : 'item-list'})[2]('li')
retired_list = soup.findAll('div', attrs={'class' : 'item-list'})[3]('li')
for shows in [active_list, retired_list]:
    if shows is active_list:
        show_type = 'active'
    elif shows is retired_list:
        show_type = 'retired'
    for i in shows:
        count += 1
        name = i('a')[-1].string.encode('utf-8')
        if name == 'Radio Leo': continue

        location = make_request('http://twit.tv' + i('a')[-1]['href'], True)
        if name in["Padre's Corner"]:
            show_url = location.rsplit('-', 1)[0]
        else:
            show_url = location.rsplit('/', 1)[0]

        soup = BeautifulSoup(make_request(show_url), 'html.parser')
        desc = ''
        desc_tag = soup.find('div', attrs={'class': "field-content"})
        if desc_tag and desc_tag.getText():
            desc = desc_tag.getText()
        else:
            print 'No Description: %s' %name
        try:
            thumb = thumbs[name]
        except:
            try:
                thumb_tag = soup.find('div', class_='views-field views-field-field-cover-art-fid')
                if thumb_tag and thumb_tag.find('img'):
                    thumb = thumb_tag.img['src']
                else: raise
            except:
                thumb = 'None'
        shows_dict[show_type][name] = {'show_url': show_url, 'thumb': thumb, 'description': desc}

        print('%s - Show: %s, %s, %s, %s' %(count, name, show_url, thumb, desc))
        print
        print '####################################################################################'
        print




w = open('shows', 'w')
w.write(repr(shows_dict))
w.close()

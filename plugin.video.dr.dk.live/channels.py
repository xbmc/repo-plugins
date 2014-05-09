#
#      Copyright (C) 2014 Tommy Winther
#      http://tommy.winther.nu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import urllib2

CHANNELS = list()

CATEGORY_DR = 30201
CATEGORY_TV2_REG = 30202
CATEGORY_MISC = 30203
CATEGORIES = {CATEGORY_DR: [], CATEGORY_TV2_REG: [], CATEGORY_MISC: []}


class Channel(object):
    def __init__(self, channel_id, category, url, fanart=None):
        self.channel_id = channel_id
        self.category = category
        self.url = url
        self.fanart = fanart

        CHANNELS.append(self)
        CATEGORIES[category].append(self)

    def get_url(self):
        return self.url


class TV2RChannel(Channel):
    def get_url(self):
        url = super(TV2RChannel, self).get_url()
        if url is not None:
            return url.replace('<HOST>', self.get_host_ip())
        else:
            return None

    def get_host_ip(self):
        for attempt in range(0, 2):
            try:
                u = urllib2.urlopen('http://livestream2.fynskemedier.dk/loadbalancer')
                s = u.read()
                u.close()
                return s[9:]
            except Exception:
                pass  # probably timeout; retry
        return 'unable.to.get.host.from.loadbalancer'

# http://www.dr.dk/mu/Bundle?ChannelType=%24eq%28%22TV%22%29&BundleType=%24eq%28%22Channel%22%29&DrChannel=true&limit=0
# DR1
Channel(1, CATEGORY_DR,
        url='http://dr01-lh.akamaihd.net/i/dr01_0@147054/master.m3u8?b=100-2000',
        fanart='http://www.dr.dk/mu/Asset?Id=52d3f40f6187a2077cbac703')
# DR2
Channel(2, CATEGORY_DR,
        url='http://dr02-lh.akamaihd.net/i/dr02_0@147055/master.m3u8?b=100-2000',
        fanart='http://www.dr.dk/mu/Asset?Id=52d3f5e66187a2077cbac70c')
# DR 3
Channel(6, CATEGORY_DR,
        url='http://dr03-lh.akamaihd.net/i/dr03_0@147056/master.m3u8?b=100-1600',
        fanart='http://www.dr.dk/mu/Asset?Id=52d3f60da11f9d0f50f56fd3')
# DR Ultra
Channel(3, CATEGORY_DR,
        url='http://dr06-lh.akamaihd.net/i/dr06_0@147059/master.m3u8?b=100-1600',
        fanart='http://www.dr.dk/mu/bar/52d3f6c6a11f9d0f50f56fde')
# DR K
Channel(4, CATEGORY_DR,
        url='http://dr04-lh.akamaihd.net/i/dr04_0@147057/master.m3u8?b=100-1600',
        fanart='http://www.dr.dk/mu/Asset?Id=52d3f685a11f9d0f50f56fd6')
# DR Ramasjang
Channel(5, CATEGORY_DR,
        url='http://dr05-lh.akamaihd.net/i/dr05_0@147058/master.m3u8?b=100-1600',
        fanart='http://www.dr.dk/mu/bar/52d3f6aca11f9d0f50f56fdb')

# TV2 Fyn
TV2RChannel(100, CATEGORY_TV2_REG, 'rtmp://<HOST>:1935/live/_definst_/tv2fyn_2000 live=1')
# TV2 Lorry
TV2RChannel(101, CATEGORY_TV2_REG, 'rtmp://<HOST>:1935/live/_definst_/tv2lorry_2000 live=1')
# TV2 Syd
TV2RChannel(102, CATEGORY_TV2_REG, 'rtmp://<HOST>:1935/live/_definst_/tvsyd_2000 live=1')
# TV2 Midtvest
Channel(103, CATEGORY_TV2_REG, 'rtmp://live.tvmidtvest.dk/tvmv/live live=1')
# TV2 Nord
TV2RChannel(105, CATEGORY_TV2_REG, 'rtmp://<HOST>:1935/live/_definst_/tv2nord-plus_2000 live=1')
# TV2 East
Channel(106, CATEGORY_TV2_REG, 'http://tv2east.live-s.cdn.bitgravity.com/cdn-live-c1/_definst_/tv2east/live/feed01/playlist.m3u8')
# TV2 OJ
TV2RChannel(108, CATEGORY_TV2_REG, 'rtmp://<HOST>:1935/live/_definst_/tv2oj-plus_2000 live=1')
# TV2 Bornholm
Channel(109, CATEGORY_TV2_REG, 'rtmp://itv08.digizuite.dk/tv2b/ch1 live=1')

# http://ft.arkena.tv/xml/core_player_clip_data_v2_REAL.php?wtve=187&wtvl=2&wtvk=012536940751284&as=1
# Folketinget
Channel(201, CATEGORY_MISC, 'rtmp://ftflash.arkena.dk/webtvftlivefl/ playpath=mp4:live.mp4 pageUrl=http://www.ft.dk/webTV/TV_kanalen_folketinget.aspx live=1')
# kanalsport.dk
Channel(203, CATEGORY_MISC, 'http://lswb-de-08.servers.octoshape.net:1935/live/kanalsport_1000k/playlist.m3u8')

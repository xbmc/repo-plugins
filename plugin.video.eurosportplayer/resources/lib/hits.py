# -*- coding: utf-8 -*-

class Hits:

    def __init__(self, plugin, i, epg=False, event=False):
        self.item = {}
        self.plugin = plugin
        self.epg = epg
        self.event = event
        self.type = i['type']
        self.now = self.plugin.time_now()
        self.titles = i['titles']
        self.photos = i['photos']
        self.appears = i.get('appears', '')
        self.start = self.plugin.utc2local(i.get('startDate', ''))
        self.end = self.plugin.utc2local(i.get('endDate', ''))
        self.duration = self.plugin.runtime_to_seconds(i['runTime'])
        self.linear = False
        self.language = self.plugin.get_language()
        if self.type == 'Airing':
            self.airing(i)
        elif self.type == 'Video':
            self.video(i)

    def airing(self, i):
        self.channel = i['channel']
        self.playback = i['playbackUrls']
        self.config = i['mediaConfig']
        self.livebroadcast = i['liveBroadcast']
        self.linear = i['linear']
        self.airing_item()

    def airing_info(self):
        for i in self.titles:
            self.title = i['title']
            self.plot = i['descriptionLong']
            if i['language'] == self.language:
                break
        if not self.title:
            self.title = self.plot

    def airing_images(self):
        for i in self.photos:
            if i['width'] == 770 and i['height'] == 432:
                self.item['thumb'] = i['uri']
            if i['width'] == 1600:
                self.item['fanart'] = i['uri']

    def airing_item(self):
        self.airing_info()
        name = self.channel['callsign']
        producttype = self.config['productType']
        start = self.plugin.plot_time(self.start, self.event)
        end = self.plugin.plot_time(self.end, self.event)
        if producttype == 'LIVE' and self.livebroadcast and not self.epg and not self.event:
            self.title = '{0} [COLOR red]LIVE[/COLOR] [I]{1}[/I]'.format(self.plugin.utfenc(name), self.plugin.utfenc(self.title))
        elif self.epg or self.event:
            if not self.playback:
                self.title = '{0} [COLOR dimgray]{1} {2}[/COLOR]'.format(start, self.plugin.utfenc(name), self.plugin.utfenc(self.title))
            else:
                self.title = '{0} [COLOR dimgray]{1}[/COLOR] {2}'.format(start, self.plugin.utfenc(name), self.plugin.utfenc(self.title))
        else:
            self.title = '{0} [I]{1}[/I]'.format(self.plugin.utfenc(name), self.plugin.utfenc(self.title))
        if producttype == 'LIVE':
            self.plot = '{0} - {1}\n{2}'.format(start, end, self.plugin.utfenc(self.plot))
            if not self.epg:
                self.duration = self.plugin.get_duration(self.end, self.now)
        else:
            self.plot = self.plugin.utfenc(self.plot)
        self.airing_images()
        self.create_item()

    def video(self, i):
        media = i['media']
        self.playback = media[0]['playbackUrls']
        if self.appears and not self.start:
            self.start = self.plugin.utc2local(self.appears[:19] + 'Z')
        self.video_item()

    def video_info(self):
        for i in self.titles:
            self.title = i['title']
            self.plot = i['summaryLong']
            tags = i.get('tags', [])
            for t in tags:
                if t['type'] == 'language':
                    if t['value'] == self.language:
                        break
        if not self.title:
            self.title = self.plot

    def video_images(self):
        photos = self.photos[0]['photos']
        for i in photos:
            if i['width'] == 770 and i['height'] == 432:
                self.item['thumb'] = i['imageLocation']
            if i['width'] == 1600:
                self.item['fanart'] = i['imageLocation']

    def video_item(self):
        self.video_info()
        self.title = self.plugin.utfenc(self.title)
        self.plot = self.plugin.utfenc(self.plot)
        self.create_item()
        if self.photos:
            self.video_images()

    def playback_id(self):
        id_ = ''
        for i in self.playback:
            id_ = i['href']
            if self.linear and not self.epg and i['rel'] == 'linear':
                break
            elif self.epg and not i['rel'] == 'linear':
                break
        return id_

    def create_item(self):
        self.item['mode'] = 'play'
        self.item['title'] = self.title
        self.item['id'] = self.playback_id()
        self.item['plot'] = self.plot
        self.item['duration'] = self.duration
        if self.start:
            self.item['date'] = self.start[:10]

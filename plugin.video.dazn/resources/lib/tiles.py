# -*- coding: utf-8 -*-

class Tiles:

    def __init__(self, plugin, i):
        self.item = {}
        self.plugin = plugin
        self.title = self.plugin.utfenc(i['Title'])
        self.subtitle = i.get('SubTitle', '')
        self.description = self.plugin.utfenc(i['Description'])
        self.start = self.plugin.utc2local(i.get('Start', ''))
        self.end = self.plugin.utc2local(i.get('End', ''))
        self.now = self.plugin.time_now()
        self.sport = i.get('Sport', [])
        self.competition = i.get('Competition', [])
        self.type = i.get('Type', '')
        self.nav = i.get('NavigateTo', '')
        self.related = i.get('Related', [])
        if self.nav:
            self.mode = 'rails'
            self.id = i['NavigateTo']
            self.params = i['NavParams']
        else:
            self.mode = 'play'
            self.id = i['AssetId']
            self.params = i['EventId']
        self.update_item(i)

    def add_duration(self, i):
        if 'UpComing' in self.type:
            self.end = self.start
            self.start = self.now
        elif 'Live' in self.type:
            self.start = self.now
        if self.start and self.end:
            self.item['duration'] = self.plugin.timedelta_total_seconds(self.plugin.time_stamp(self.end)-self.plugin.time_stamp(self.start))

    def add_thumb(self, i):
        url = self.plugin.api_base+'v2/image?id={0}&Quality=95&Width={1}&Height={2}&ResizeAction=fill&VerticalAlignment=top&Format={3}'
        image = i.get('Image', '')
        if image:
            self.item['thumb'] = url.format(image['Id'], '720', '404', image['ImageMimeType'])
            self.item['fanart'] = url.format(image['Id'], '1280', '720', image['ImageMimeType'])
        background = i.get('BackgroundImage', '')
        if background:
            self.item['fanart'] = url.format(background['Id'], '1280', '720', background['ImageMimeType'])

    def update_item(self, i):
        self.item['mode'] = self.mode
        self.item['title'] = self.title
        self.item['plot'] = self.description
        self.item['id'] = self.id
        self.item['type'] = self.plugin.get_resource(self.type)

        if self.params:
            self.item['params'] = self.params

        if 'Epg' in i.get('Id', ''):
            if self.competition:
                competition = self.plugin.utfenc(self.competition['Title'])
            if self.sport:
                sport = self.plugin.utfenc(self.sport['Title'])
            time_ = self.start[11:][:5]
            if self.type == 'Live':
                self.item['title'] = '[COLOR red]{0}[/COLOR] [COLOR dimgray]{1}[/COLOR] {2} [COLOR dimgray]{3}[/COLOR]'.format(time_, sport, self.title, competition)
            else:
                self.item['title'] = '{0} [COLOR dimgray]{1}[/COLOR] {2} [COLOR dimgray]{3}[/COLOR]'.format(time_, sport, self.title, competition)

        elif (self.type == 'UpComing' or 'Scheduled' in i.get('Id', '')) or (self.type == 'Highlights'):
            if self.type == 'UpComing':
                day = self.plugin.get_resource(self.plugin.days(self.type, self.now, self.start))
                sub_title = '{0} {1}'.format(day, self.start[11:][:5])
            else:
                sub_title = self.plugin.get_resource(self.type)
            self.item['title'] = '{0} ({1})'.format(self.title, sub_title)

        if self.start:
            self.item['date'] = self.start[:10]

        self.item['related'] = self.related
        self.item['sport'] = self.sport
        self.item['competition'] = self.competition

        self.add_thumb(i)
        self.add_duration(i)

# -*- coding: utf-8 -*-

from items import Items
from hits import Hits
from sports import Sports
from events import Events
from context import Context

class Parser:

    def __init__(self, plugin):
        self.plugin = plugin
        self.items = Items(self.plugin)

    def channel(self, data):
        hits = data['data']['Airings']
        for i in hits:
            item = Hits(self.plugin, i).item
            if item.get('id'):
                self.items.add_item(item)
        date = self.plugin.epg_date()
        prev_date = self.plugin.get_prev_day(date)
        self.items.add_item(
            {
                'mode': 'epg',
                'title': self.plugin.get_string(30103),
                'plot': self.plugin.get_string(30103),
                'id': date.strftime(self.plugin.date_format),
                'params': prev_date.strftime(self.plugin.date_format)
            }
        )
        self.items.add_item(
            {
                'mode': 'sports',
                'title': self.plugin.get_string(30101),
                'plot': self.plugin.get_string(30102)
            }
        )
        self.items.add_item(
            {
                'mode': 'events',
                'title': self.plugin.get_string(30104),
                'plot': self.plugin.get_string(30104)
            }
        )
        self.items.list_items(sort=True)

    def sport(self, data):
        self.items.add_item(
            {
                'mode': 'all_sports',
                'title': self.plugin.get_string(30105).upper(),
                'plot': self.plugin.get_string(30105)
            }
        )
        hits = data['data']['sports_filter']['list']
        for i in hits:
            self.items.add_item(Sports(self.plugin, i).item)
        self.items.list_items(sort=True)

    def all_sports(self, data):
        hits = data['data']['CategoryAll']
        for i in hits:
            item = Sports(self.plugin, i).item
            if item.get('thumb') and item.get('id'):
                self.items.add_item(item)
        self.items.list_items(sort=True)

    def events(self, data):
        hits = data['data']['EventPageByLanguage']
        for i in hits:
            self.items.add_item(Events(self.plugin, i).item)
        self.items.list_items()

    def event(self, data):
        media = data['data']['EventPageByContentId']['media']
        for m in media:
            hits = m['videos']
            for i in hits:
                self.items.add_item(Hits(self.plugin, i, event=True).item)
        self.items.list_items()

    def video(self, data, id_):
        sport_id = 'sport_{0}'.format(id_)
        hits = data['data'][sport_id]['hits']
        for i in hits:
            hit = i['hit']
            item = Hits(self.plugin, hit).item
            if item.get('id'):
                self.items.add_item(item)
        self.items.list_items()

    def epg(self, data, prev_date, date):

        def date_item(params, id_):
            return {
                'mode': 'epg',
                'title': '{0} {1}'.format(self.plugin.get_resource(id_.strftime('%A')), id_.strftime(self.plugin.date_format)),
                'plot': '{0} {1}'.format(self.plugin.get_resource(self.plugin.epg_date(date).strftime('%A')), self.plugin.epg_date(date).strftime(self.plugin.date_format)),
                'id': id_.strftime(self.plugin.date_format),
                'params': params.strftime(self.plugin.date_format),
                'cm': cm
            }

        update = False if date == self.plugin.epg_date().strftime(self.plugin.date_format) else True
        cm = Context(self.plugin).epg_date()

        self.items.add_item(date_item(self.plugin.get_prev_day(self.plugin.epg_date(prev_date)), self.plugin.epg_date(prev_date)))
        hits = data['data']['Airings']
        hits = sorted(hits, key=lambda k: k.get('startDate'))
        for i in hits:
            self.items.add_item(Hits(self.plugin, i, epg=True).item)
        self.items.add_item(date_item(self.plugin.epg_date(date), self.plugin.get_next_day(self.plugin.epg_date(date))))
        self.items.list_items(upd=update, epg=True)

    def play(self, data):
        path = ''
        key = ''
        resolved = False
        if data.get('stream'):
            stream = data['stream']
            if stream.get('slide'):
                path = stream['slide']
            elif stream.get('complete'):
                path = stream['complete']
            if path:
                resolved = True
                path = path.replace('desktop','wired50')
                key = data['license_key']
        self.items.play_item(path, key, resolved)

    def license_renewal(self, license_key):
        self.items.add_token(license_key)

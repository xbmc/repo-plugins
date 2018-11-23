# -*- coding: utf-8 -*-

from .items import Items
from .rails import Rails
from .tiles import Tiles
from .playback import Playback
from .context import Context

class Parser:

    def __init__(self, plugin):
        self.plugin = plugin
        self.items = Items(self.plugin)

    def rails_items(self, data, id_):
        if id_ == 'home':
            epg = {
                'mode': 'epg',
                'title': self.plugin.get_resource('header_schedule'),
                'plot': 'Schedule',
                'params': 'today',
            }
            epg['cm'] = Context(self.plugin).highlights(epg, mode='epg_highlights')
            self.items.add_item(epg)
        for i in data.get('Rails', []):
            item = Rails(self.plugin, i).item
            if item.get('id', '') == 'CatchUp':
                item['cm'] = Context(self.plugin).highlights(item, mode='rail_highlights')
            self.items.add_item(item)
        self.items.list_items()

    def rail_items(self, data, mode, list_=True):
        highlights = True if 'highlights' in mode else False
        focus = data.get('StartPosition', False)
        for i in data.get('Tiles', []):
            item = Tiles(self.plugin, i).item
            if highlights:
                if item['type'] == 'Highlights':
                    item['cm'] = Context(self.plugin).goto(item)
                    self.items.add_item(item)
                elif item.get('related', []):
                    for i in item['related']:
                        context = Context(self.plugin)
                        if i.get('Videos', []):
                            _item = Tiles(self.plugin, i).item
                            _item['cm'] = context.goto(_item)
                            self.items.add_item(_item)
            else:
                context = Context(self.plugin)
                if item.get('related', []):
                    cm_items = []
                    for i in item['related']:
                        if i.get('Videos', []):
                            cm_items.append(Tiles(self.plugin, i).item)
                    context.related(cm_items)
                item['cm'] = context.goto(item)
                self.items.add_item(item)
        if list_:
            self.items.list_items(focus)

    def epg_items(self, data, params, mode):
        update = False if params == 'today' else True
        if data.get('Date'):
            date = self.plugin.epg_date(data['Date'])
            cm = Context(self.plugin).epg_date()

            def date_item(day):
                return {
                    'mode': mode,
                    'title': '{0} ({1})'.format(self.plugin.get_resource(day.strftime('%A'), prefix='calendar_'), day.strftime(self.plugin.date_format)),
                    'plot': '{0} ({1})'.format(self.plugin.get_resource(date.strftime('%A'), prefix='calendar_'), date.strftime(self.plugin.date_format)),
                    'params': day,
                    'cm': cm
                }

            self.items.add_item(date_item(self.plugin.get_prev_day(date)))
            self.rail_items(data, mode, list_=False)
            self.items.add_item(date_item(self.plugin.get_next_day(date)))
        self.items.list_items(upd=update, epg=True)

    def playback(self, data, name=False, context=False):
        self.items.play_item(Playback(self.plugin, data), name, context)

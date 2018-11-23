# -*- coding: utf-8 -*-

class Context:

    def __init__(self, plugin):
        self.cm = []
        self.plugin = plugin

    def epg_date(self):
        d = {
            'mode': 'epg',
            'id': 'date'
        }
        self.cm.append((self.plugin.get_string(30230), 'ActivateWindow(Videos, {0})'.format(self.plugin.build_url(d))))
        return self.cm

    def highlights(self, item, mode):
        d = {
            'mode': mode,
            'title': self.plugin.utfenc(item['title']),
            'id': item.get('id', ''),
            'params': item.get('params','')
        }
        self.cm.append((self.plugin.get_string(30231), 'Container.Update({0})'.format(self.plugin.build_url(d))))
        return self.cm

    def related(self, cm_items):
        for i in cm_items:
            type_ = self.plugin.get_resource('{0}{1}Title'.format(i['type'][0].lower(), i['type'][1:]), 'browseui_')
            if type_.endswith('Title'):
                type_ = i['type']
            d = {
                'mode': 'play_context',
                'title': self.plugin.utfenc(i['title']),
                'id': i.get('id', ''),
                'params': i.get('params','')
            }
            self.cm.append((type_, 'XBMC.RunPlugin({0})'.format(self.plugin.build_url(d))))
        return self.cm

    def goto(self, item):
        if item.get('sport', None):
            i = item['sport']
            d = {
                'mode': 'rails',
                'title': self.plugin.utfenc(i['Title']),
                'id': 'sport',
                'params': i['Id']
            }
            self.cm.append((self.plugin.get_string(30214), 'Container.Update({0})'.format(self.plugin.build_url(d))))

        if item.get('competition', None):
            i = item['competition']
            d = {
                'mode': 'rails',
                'title': self.plugin.utfenc(i['Title']),
                'id': 'competition',
                'params': i['Id']
            }
            self.cm.append((self.plugin.get_string(30215), 'Container.Update({0})'.format(self.plugin.build_url(d))))

        return self.cm

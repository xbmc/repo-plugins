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

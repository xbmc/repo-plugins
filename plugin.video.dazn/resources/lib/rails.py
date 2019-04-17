# -*- coding: utf-8 -*-

class Rails:

    def __init__(self, plugin, i):
        self.item = {}
        self.plugin = plugin
        id_ = self.plugin.utfenc(i['Id'])
        self.item['mode'] = 'rail'
        self.item['title'] = self.plugin.get_resource(id_, prefix='browseui_railHeader')
        self.item['id'] = id_
        self.item['plot'] = id_
        if i.get('Params', ''):
            self.item['params'] = i['Params']

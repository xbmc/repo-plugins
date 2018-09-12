# -*- coding: utf-8 -*-

class Rails:

    def __init__(self, plugin, i):
        self.item = {}
        self.plugin = plugin
        self.item['mode'] = 'rail'
        self.item['title'] = self.plugin.get_resource(i['Id'], prefix='browseui_railHeader')
        self.item['id'] = i['Id']
        self.item['plot'] = i['Id']
        if i.get('Params', ''):
            self.item['params'] = i['Params']

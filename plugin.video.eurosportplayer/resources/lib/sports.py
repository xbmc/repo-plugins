# -*- coding: utf-8 -*-

class Sports:

    def __init__(self, plugin, i):
        self.item = {}
        self.plugin = plugin
        self.item['mode'] = 'videos'
        self.item['title'] = self.plugin.utfenc(i['tags'][0]['displayName'])
        sport = i['sport']
        logo = i['logoImage']
        if logo and sport:
            if sport.isdigit():
                self.item['id'] = sport
            self.item['thumb'] = logo[0]['rawImage']

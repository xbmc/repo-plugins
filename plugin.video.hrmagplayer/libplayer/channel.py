#!/usr/bin/python
# -*- coding: utf-8 -*-

from libplayer.magazine import *
from libplayer.hessenschau import *
from libplayer.livestream import *
from libplayer.wdr3kochen import *
from libplayer.utils import *

class ChannelContext(dict):
    def __init__(self, addon):
        self['addon'] = addon
        self['showList'] = self.createShowList(addon)
        self['shows'] = self.createShows()
        self['charIndex'] = 0
        self['debug'] = False

    def createShowList(self, addon):
        # Create ordered list of shows for quick display
        # Localized titles (necessary?): self['add'].addon.getLocalizedString(30000)
        
        liveId = 'live'
        schauId = 'hessenschau'
        carteId = 'hessen-a-la-carte'
        herrId = 'herrliches-hessen'
        erlebId = 'erlebnis-hessen'
        reportId = 'hessenreporter'
        engelId = 'engel-fragt'
        reiseId = 'reise-reportagen'
        wdrId = 'wdr-kochen'
        
        # Maybe create this array of series thumbnails dynamically
        tNails = {liveId: 'https://www.hessenschau.de/tv-sendung/livestream-100~_t-1469711638787_v-1to1__medium.jpg',
                  schauId: 'https://www.hessenschau.de/tv-sendung/banner-hessenschau-100~_t-1508156576948_v-16to9__small.jpg',
                  carteId: 'https://www.hr-fernsehen.de/sendungen-a-z/hessen-a-la-carte/banner-hessenalacarte-100~_t-1505313904753_v-16to9__small.jpg',
                  herrId: 'https://www.hr-fernsehen.de/sendungen-a-z/herrliches-hessen/banner-herrliches-hessen-100~_t-1504541659007_v-16to9__small.jpg',
                  erlebId: 'https://www.hr-fernsehen.de/sendungen-a-z/erlebnis-hessen/banner-erlebnis-hessen-100~_t-1504529430759_v-16to9__small.jpg',
                  reportId: 'https://www.hr-fernsehen.de/sendungen-a-z/hessenreporter/banner-hessenreporter-100~_t-1505137253325_v-16to9__small.jpg',
                  engelId: 'https://www.hr-fernsehen.de/sendungen-a-z/engel-fragt/banner-engel-fragt-100~_t-1504627362788_v-16to9__small.jpg',
                  reiseId: 'https://www.hr-fernsehen.de/sendungen-a-z/reise-reportagen/banner-reisereportagen-100~_t-1505479140011_v-16to9__small.jpg',
                  wdrId: 'https://www1.wdr.de/fernsehen/kochen-mit-martina-und-moritz/sendungen/kochen-mit-martina-und-moritz-152~_v-gseaclassicxl.jpg'
                  }
        actives = None
        if addon != None:
            actives = {
                liveId: addon.getSetting(liveId) == 'true',
                schauId: addon.getSetting(schauId) == 'true',
                carteId: addon.getSetting(carteId) == 'true',
                herrId: addon.getSetting(herrId) == 'true',
                erlebId: addon.getSetting(erlebId) == 'true',
                reportId: addon.getSetting(reportId) == 'true',
                engelId: addon.getSetting(engelId) == 'true',
                reiseId: addon.getSetting(reiseId) == 'true',
                wdrId: addon.getSetting(wdrId) == 'true'
                }
        else:
            actives = {
                liveId: True,
                schauId: True,
                carteId: True,
                herrId: True,
                erlebId: True,
                reportId: True,
                engelId: True,
                reiseId: True,
                wdrId: True
                }

        shows = [
            {'name': 'Play Livestream', 'id': liveId, 'image': tNails[liveId], 'active': actives[liveId]},
            {'name': 'Hessenschau', 'id': schauId, 'image': tNails[schauId], 'active': actives[schauId]},
            {'name': 'Hessen à la carte', 'id': carteId, 'image': tNails[carteId], 'active': actives[carteId]},
            {'name': 'Herrliches Hessen', 'id': herrId, 'image': tNails[herrId], 'active': actives[herrId]},
            {'name': 'Erlebnis Hessen', 'id': erlebId, 'image': tNails[erlebId], 'active': actives[erlebId]},
            {'name': 'hessenreporter', 'id': reportId, 'image': tNails[reportId], 'active': actives[reportId]},
            {'name': 'Engel fragt', 'id': engelId, 'image': tNails[engelId], 'active': actives[engelId]},
            {'name': 'Reisereportage', 'id': reiseId, 'image': tNails[reiseId], 'active': actives[reiseId]},
            {'name': 'WDR - Kochen mit Martina und Moritz', 'id': wdrId, 'image': tNails[wdrId], 'active' : actives[wdrId]}
            ]
        return shows
    
    def createShows(self):
        # Create dict of shows for more detailed content
        shows = dict()
        for show in self['showList']:
            shows[show['id']] = {'date': ''}
            shows[show['id']]['url'] = self.getShowUrl(show['id'])
        return shows
    
    def getShowUrl(self, id):
        if id == 'hessenschau':
            return 'https://www.hessenschau.de/tv-sendung/sendungsarchiv/index.html'
        elif id == 'live':
            return 'https://www.hr-fernsehen.de/livestream/index.html'
        elif id == 'reise-reportagen':
            return 'https://www.hr-fernsehen.de/sendungen-a-z/' + id + '/index.html'
        elif id == 'wdr-kochen':
            return 'https://www1.wdr.de/fernsehen/kochen-mit-martina-und-moritz/sendungen/index.html'
        else:
            return 'https://www.hr-fernsehen.de/sendungen-a-z/' + id + '/sendungen/index.html'
    
class ChannelLoader:
    def __init(self):
        self.show = None
        
    def loadEpisodeList(self, context, index):
        id = getShowId(context, index)
        url = context['shows'][id]['url']
        
        http = HttpRetriever()
        page = http.get(url)
        
        show = None
        if index == 0:
            show = Livestream()
        elif index == 1:
            show = Hessenschau()
        elif index == 8:
            show = WdrShow()
        else:
            show = Show()
            
        episodeList = show.getEpisodes(context, id, page)
        return episodeList
        
    def resolveLiveUrl(self, context, url):
        # Get master file and resolve live stream URL
        http = HttpRetriever()
        page = http.get(url)
        url = None
        
        if isDebug(context):
            print('--- Live page ----')
            print page
            print('------------------')
            
        ix = page.find('1280x720')
        if ix != -1:
            ix = page.find('https', ix)
            if ix != -1:
                ex = page.find('rebase=on', ix)
                url = page[ix:ex+9]
        return url

        

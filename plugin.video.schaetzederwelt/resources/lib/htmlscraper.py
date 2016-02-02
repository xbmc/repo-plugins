#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013-2015 CHF (chrifri@gmx.de)
#     
#     This file is part of the XBMC Add-on: plugin.video.schaetzederwelt
#     
#     plugin.video.schaetzederwelt is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#     
#     plugin.video.schaetzederwelt is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#     
#     You should have received a copy of the GNU General Public License
#     along with plugin.video.schaetzederwelt. If not, see <http://www.gnu.org/licenses/>.
#     
#     Diese Datei ist Teil des XBMC Add-on: plugin.video.schaetzederwelt.
#     
#     plugin.video.schaetzederwelt ist Freie Software: Sie können es unter den Bedingungen
#     der GNU General Public License, wie von der Free Software Foundation,
#     Version 3 der Lizenz oder (nach Ihrer Wahl) jeder späteren
#     veröffentlichten Version, weiterverbreiten und/oder modifizieren.
#     
#     plugin.video.schaetzederwelt wird in der Hoffnung, dass es nützlich sein wird, aber
#     OHNE JEDE GEWÄHELEISTUNG, bereitgestellt; sogar ohne die implizite
#     Gewährleistung der MARKTFÄHIGKEIT oder EIGNUNG FÜR EINEN BESTIMMTEN ZWECK.
#     Siehe die GNU General Public License für weitere Details.
#     
#     Sie sollten eine Kopie der GNU General Public License zusammen mit diesem
#     Programm erhalten haben. Wenn nicht, siehe <http://www.gnu.org/licenses/>.
#
from urllib2 import urlopen, Request
import logging
import re
import socket
import json
import HTMLParser
import time

BASE_URL    = 'http://swrmediathek.de'
MAIN_URL    = "http://swrmediathek.de/tvshow.htm?show=945f9950-cc74-11df-9bbb-0026b975f2e6"
EKEY_URL    = "http://swrmediathek.de/AjaxEntry?ekey="
DIRECT_EKEY = "DIRECT-"
REQUEST_HEADERS = {"User-Agent" : "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)"}
SOCKET_TIMEOUT = 30
MAIN_PAGE_CACHE = None
MAX_TIMEOUT_RETRIES = 20
logger = logging.getLogger('plugin.video.schaetzederwelt')
kontinente_und_anderes = ['Europa', 'Afrika', 'Amerika', 'Australien', 'Asien', 'Pazifik']
groessenangaben = {'s':1, 'sm':2,  'm':2.5,  'ml':3,  'l':3.5,  'xl':4}
htmlParser = HTMLParser.HTMLParser()

schluesselwoerter_fuer_fehlende_laender = {
    "Maltas": "Malta",
    "Vatikanstadt": "Vatikanstadt",
    "Luxemburg": "Luxemburg", 
    "Völklinger": "Deutschland", 
    "Compostela": "Spanien", 
    "Liverpool": "Großbritannien", 
    "Mantua": "Italien", 
    "Norwegen": "Norwegen", 
    "Thingvellir": "Island", 
    "Zaren": "Russland", 
    "Sardinien": "Italien", 
    "Berlin": "Deutschland", 
    "Wilhelmshöhe": "Deutschland", 
    "Drakensberg": "Südafrika", 
    "Malakka": "Malaysia", 
    "Plitvicer": "Kroatien", 
    "Fagus-Werk": "Deutschland", 
    "Löwentempeln": "Sudan", 
    "australischen": "Australien", 
    "Nemrut Dai": "Türkei", 
    "Brügge": "Belgien", 
    "Al Ain": "Vereinigte Arabische Emirate", 
    "Täbriz": "Iran", 
    "Baikal": "Russland", 
    "Südwesten": "Deutschland", 
    "Pfahlbauten": "Alpenländer",
    "Wrangel Island": "Russland"
}
liste_falscher_laender = {
    "Rusland": "Russland", 
    "SambiaSimbabwe": "Sambia, Simbabwe", 
    "Tunesion": "Tunesien", 
    "Russische Föderation": "Russland", 
    "Tschechische Republik": "Tschechien", 
    "Slowakische Republik": "Slowakei", 
    "Indonesion": "Indonesien", 
    "Italien Vatikan": "Vatikanstadt",
    "GB": "Großbritannien", 
    "Deutschland Polen": "Deutschland, Polen", 
    "Deutschland-Niederlande": "Deutschland, Niederlande", 
    "niederländische Antillen Curacao": "Niederländische Antillen: Curacao", 
    "Korea": "Südkorea"
}
schluesselwoerter_fuer_falsche_laender = {
    "Simbabwe": "Simbabwe", 
    "Jerusalem": "Israel", 
    "Seychellen": "Seychellen", 
    "Kilimandjaro": "Tansania"
}
schluesselwoerter_fuer_falsche_angaben = {
    "Kaya": {"land": "Kenia",  "titel": "Kaya"}, 
    "Cidade Velha": {"land": "Kap Verde", "titel": "Cidade Velha"}, 
    "Ilha de Moçambique": {"land": "Mosambik", "titel": "Ilha de Moçambique"}, 
    "Bikini Atoll": {"land": "Marshallinseln",  "titel": "Bikini Atoll"}, 
    "Cidade Velha": {"land": "Kap Verde", "titel": "Cidade Velha"}, 
    "Xian": {"land": "China",  "titel": "Xian: Grabmal des ersten Kaisers von China, Qin Shi Huang"}, 
    "Felsen und Eisberge": {"titel": "Fjorde, Felsen und Eisberge - Europas Norden"}, 
    "Stahl und Kupfer": {"titel": "Kohle, Stahl und Kupfer...Denkmäler der Industriegeschichte"}, 
    "Kulturerbe Bauernland": {"titel": "Kulturerbe Bauernland - Essen, Trinken und Genießen als Kulturgut"}, 
    "Mythen und Legenden": {"titel": "Rätsel, Mythen und Legenden"},
    "Bewässrungssystem": {"land": "Oman", "titel": "Aflaj-Das Bewässerungssystem des Oman"}
}
schluesselwoerter_fuer_fehlende_folgen = {
    "Machu Picchu": 2, 
    "Willemstad": 262, 
    "Tongariro": 304, 
    "Cilento": 355, 
    "Melaka": 381, 
    "Kaya": 391, 
    "Cidade Velha": 395, 
    "Falun": 397, 
    "Mantua": 399, 
    "Al Ain": 409, 
    "Täbriz": 410, 
    "Baikal": 411, 
    "Wilhelmshöhe": 412, 
    "Sardinien": 413 
}
liste_falscher_folgen = {
    932 : 392
}
liste_fehlender_urls = {
    "83d05270-2bad-11e1-9ba3-0026b975f2e6": "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2011/12-25/505238.l.mp4",
    "05509130-3b89-11e1-944f-0026b975f2e6": "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2009/01-04/509057.l.mp4",
    "fa416e20-411b-11e1-9a84-0026b975f2e6": "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2012/01-15/509661.l.mp4",
    "83c68e70-2bad-11e1-9ba3-0026b975f2e6": "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2012/01-01/505242.l.mp4",
    "03f3e1f0-411c-11e1-9a84-0026b975f2e6": "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2012/01-08/509028.l.mp4",
    "59c06780-4599-11e1-b642-0026b975f2e6": "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2012/01-22/510882.l.mp4",
    "27884780-66b2-11e1-8a57-0026b975f2e6": "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2012/40-15/521576.l.mp4",
    "e5e12f90-48bb-11e1-a56b-0026b975f2e6": "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2012/01-31/512790.l.mp4",
    "e19a0400-f63d-11e0-8181-0026b975f2e6": "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2011/10-16/489336.l.mp4",
    "e1df9bc0-5243-11e1-b092-0026b975f2e6": "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2012/02-12/515622.l.mp4",
    "edfbd940-4b14-11e1-a25d-0026b975f2e6": "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2012/02-05/513278.l.mp4",
    "d1a03e50-11dd-11e1-a01f-0026b975f2e6": "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2011/11-20/496672.l.mp4",
    "50ef2bf0-4599-11e1-b642-0026b975f2e6": "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2012/01-22/511505.l.mp4",
    "f6f8c7b0-47fe-11e1-aacc-0026b975f2e6": "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2011/12-18/512690.l.mp4"
}
liste_versteckter_beitraege = [
    {"title": "Olympia: Das antike Olympia, Griechenland, Folge 301",
     "img":   "/img/5/2/8/52847f8c1e2725674358940af8db1ff3",
     "ekey":  "10a49920-11de-11e1-a01f-0026b975f2e6"},
    {"title": "Aflaj-Das Bewässrungssystem des Oman, Folge 349",
     "img":   "/img/e/d/f/edfd400675b07236d1d5ac282ebb7fd2",
     "ekey":  "11cc7750-11de-11e1-a01f-0026b975f2e6"},
    {"title": "Lwiw: Zentrum von Lwiw (Lemberg), Ukraine, Folge 366",
     "img":   "/img/8/e/8/8e85a7b0c928774146f298019fcc0eb6",
     "ekey":  "0a2e8ba0-11de-11e1-a01f-0026b975f2e6"},
    {"title": "Donaudelta, Rumänien, Folge 380",
     "img":   "/img/2/7/0/270a7ac93e9f520c29aedde2d71e4b5f",
     "ekey":  "058f2e10-5ea1-11e0-b83a-0026b975f2e6"}
]
liste_fehlender_beitraege = [
    {"title":     "Valletta, Malta, Folge 1",
     "icon":      "http://www.swr.de/-/id=7967574/property=thumbnail/pubVersion=4/width=316/13ewi21/index.jpg",
     "ekey":      "Folge-001",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/1995/04-01/833382.xl.mp4",
     "kontinent": "Europa"}, 
    {"title":     "Mont St. Michel, Frankreich, Folge 18",
     "icon":      "http://www.swr.de/-/id=6343768/property=thumbnail/pubVersion=7/width=316/25s3hk/Mont%20St.jpg",
     "ekey":      "Folge-018",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/1995/12-10/414953.l.mp4",
     "kontinent": "Europa"}, 
    {"title":     "Der Pekingmensch von Zhoukoudian, China, Folge 61",
     "icon":      "http://www.swr.de/-/id=8218972/property=thumbnail/pubVersion=3/width=316/1vgi5nh/index.jpg",
     "ekey":      "Folge-061",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/1997/01-05/412577.l.mp4",
     "kontinent": "Asien"}, 
    {"title":     "Sokkuram - Die Grotte der Erleuchtung, Südkorea, Folge 87",
     "icon":      "http://www.swr.de/-/id=6496208/property=thumbnail/pubVersion=5/width=316/1qs68ei/index.jpg",
     "ekey":      "Folge-087",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/1997/11-23/412033.l.mp4",
     "kontinent": "Asien"}, 
    {"title":     "Eisleben und Wittenberg, Deutschland, Folge 97",
     "icon":      "http://www.swr.de/-/id=8449760/property=thumbnail/pubVersion=4/width=316/1x1pze4/index.jpg",
     "ekey":      "Folge-097",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/1998/06-28/411987.l.mp4",
     "kontinent": "Europa"}, 
    {"title":     "Hallstatt - Drei Jahrtausende Salz, Österreich, Folge 109",
     "icon":      "http://www.swr.de/-/id=8339700/property=thumbnail/pubVersion=4/width=316/ve145q/index.jpg",
     "ekey":      "Folge-109",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/1999/06-06/411045.l.mp4",
     "kontinent": "Europa"}, 
    {"title":     "Mérida, Spanien, Folge 126",
     "icon":      "http://www.swr.de/-/id=8348450/property=thumbnail/pubVersion=4/width=316/wxr17c/index.jpg",
     "ekey":      "Folge-126",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2001/07-15/410471.l.mp4",
     "kontinent": "Europa"}, 
    {"title":     "Teruel, Spanien, Folge 127",
     "icon":      "http://www.swr.de/-/id=8310686/property=thumbnail/pubVersion=4/width=316/1vppq2z/index.jpg",
     "ekey":      "Folge-127",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2000/04-16/410469.l.mp4",
     "kontinent": "Europa"}, 
    {"title":     "Córdoba, Spanien, Folge 128",
     "icon":      "http://www.swr.de/-/id=8243476/property=thumbnail/pubVersion=4/width=316/181go50/index.jpg",
     "ekey":      "Folge-128",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2000/08-13/410433.l.mp4",
     "kontinent": "Europa"}, 
    {"title":     "Die Altstadt von Vilnius, Litauen, Folge 132",
     "icon":      "http://www.swr.de/-/id=6353902/property=thumbnail/pubVersion=4/width=316/1dxpom8/index.jpg",
     "ekey":      "Folge-132",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2001/07-22/410368.l.mp4",
     "kontinent": "Europa"}, 
    {"title":     "Quasr Amra, Jordanien, Folge 136",
     "icon":      "http://www.swr.de/-/id=8254204/property=thumbnail/pubVersion=4/width=316/wd4gez/index.jpg",
     "ekey":      "Folge-136",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/1999/11-28/410329.l.mp4",
     "kontinent": "Asien"}, 
    {"title":     "Edinburgh - Die Hauptstadt Schottlands, Großbritannien, Folge 139",
     "icon":      "http://www.swr.de/-/id=8449702/property=thumbnail/pubVersion=4/width=316/12ayg9i/index.jpg",
     "ekey":      "Folge-139",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2001/07-02/409839.l.mp4",
     "kontinent": "Europa"}, 
    {"title":     "Segovia, Spanien, Folge 141",
     "icon":      "http://www.swr.de/-/id=6357864/property=thumbnail/pubVersion=4/width=316/100pyuu/index.jpg",
     "ekey":      "Folge-141",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/1999/09-19/409836.l.mp4",
     "kontinent": "Europa"}, 
    {"title":     "Avila, Spanien, Folge 142",
     "icon":      "http://www.swr.de/-/id=6357992/property=thumbnail/pubVersion=4/width=316/fgioke/index.jpg",
     "ekey":      "Folge-142",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2000/04-30/409831.l.mp4",
     "kontinent": "Europa"}, 
    {"title":     "Weimar, Deutschland, Folge 143",
     "icon":      "http://www.swr.de/-/id=8446098/property=thumbnail/pubVersion=4/width=316/1hpyjm4/index.jpg",
     "ekey":      "Folge-143",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2000/09-03/409826.l.mp4",
     "kontinent": "Europa"}, 
    {"title":     "Petäjävesi - Blockhaus des Glaubens, Finnland, Folge 146",
     "icon":      "http://www.swr.de/-/id=8352756/property=thumbnail/pubVersion=4/width=316/1pmw8jz/index.jpg",
     "ekey":      "Folge-146",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2000/06-04/409800.l.mp4",
     "kontinent": "Europa"}, 
    {"title":     "Roskilde - Grablege der dänischen Könige, Dänemark, Folge 150",
     "icon":      "http://www.swr.de/-/id=8445976/property=thumbnail/pubVersion=4/width=316/1565yof/index.jpg",
     "ekey":      "Folge-150",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2000/06-18/417373.l.mp4",
     "kontinent": "Europa"}, 
    {"title":     "Persepolis, Iran, Folge 152",
     "icon":      "http://www.swr.de/-/id=8445290/property=thumbnail/pubVersion=4/width=316/11wbhyz/index.jpg",
     "ekey":      "Folge-152",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2000/02-13/409346.l.mp4",
     "kontinent": "Asien"}, 
    {"title":     "Gwynedd, Großbritannien, Folge 155",
     "icon":      "http://www.swr.de/-/id=8441440/property=thumbnail/pubVersion=2/width=316/e8y2ck/index.jpg",
     "ekey":      "Folge-155",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2000/03-05/409267.l.mp4",
     "kontinent": "Europa"}, 
    {"title":     "Ironbridge, Großbritannien, Folge 156",
     "icon":      "http://www.swr.de/-/id=8441024/property=thumbnail/pubVersion=4/width=316/1342lx/index.jpg",
     "ekey":      "Folge-156",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2000/01-16/409265.l.mp4",
     "kontinent": "Europa"}, 
    {"title":     "Monte Alban, Mexiko, Folge 158",
     "icon":      "http://www.swr.de/-/id=8440720/property=thumbnail/pubVersion=4/width=316/sm0b59/index.jpg",
     "ekey":      "Folge-158",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2000/07-09/408921.l.mp4",
     "kontinent": "Südamerika"}, 
    {"title":     "Tikal, Guatemala, Folge 159",
     "icon":      "http://www.swr.de/-/id=8293640/property=thumbnail/pubVersion=4/width=316/1py4wzu/index.jpg",
     "ekey":      "Folge-159",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2000/07-02/408897.l.mp4",
     "kontinent": "Südamerika"}, 
    {"title":     "Bethlehem, Palästina, Folge 406",
     "icon":      "http://www.swr.de/-/id=12404044/property=thumbnail/pubVersion=3/width=316/1lbt3t1/index.jpg",
     "ekey":      "Folge-406",
     "url":       "http://pd-ondemand.swr.de/3sat/schaetze-der-welt/2013/12-22/678649.l.mp4",
     "kontinent": "Asien"},
]


     
def build_menuitems(url_for, endpoint, localizer):
    
    # Anzahl Seiten ermitteln über die erste Seite, changelog, Versionswechsel, push, mail
    #log_info("Oeffne Seite ... 0")
    page = get_content_from_url(MAIN_URL + '&pc=0')

    #Ermittle Seitengesamtanzahl
    pattern = re.compile('<a title=\"letzte Seite\" href=\"/tvshow.htm\?show=945f9950-cc74-11df-9bbb-0026b975f2e6\&pc=(?P<maxPages>.*)\">\&gt;\&gt;</a>')
    m = pattern.search(page)
    maxPages = int(m.group('maxPages')) + 1
    log_info("Seitengesamtanzahl: " + str(maxPages))
    

    #log_info("Hole alle Ids der einzelnen Sendungen ...")
    pattern = regex_pattern_for_items()
    items = []
         
    for pc in range (0, maxPages):
        log_info("Oeffne Seite ..." + str(pc))
        page = get_content_from_url(MAIN_URL + '&pc=' + str(pc))
             
        for match in pattern.finditer(page):
            label, episode = enrich_title(match.group('title').decode('utf-8'), localizer)
            item = {'label' : label.strip(),
                    'thumbnail' : BASE_URL + match.group('img'),
                    'icon' : BASE_URL + match.group('img'),
                    'path' : url_for(endpoint, ekey=match.group('ekey')),
#                    'info' : {'title': label, 'episode': episode,  'plot': 'plot could be found using the entry_descl or entry_descs keys in the AJAX answer'},
                    'info' : {'title': label, 'episode': episode},
                    'context_menu' : [(localizer('toggle_watched'), 'XBMC.Action(ToggleWatched)')],
                    'is_playable' : True
                    }
            items.append(item)
    # Einige Beiträge sind falsch klassifiziert (als Einzelbeiträge). Diese fügenw wir auch noch hinzu
    for beitrag in liste_versteckter_beitraege:
        label, episode = enrich_title(beitrag['title'].decode('utf-8'), localizer)
        item = {'label' : label.strip(),
                'thumbnail' : BASE_URL + beitrag['img'],
                'icon' : BASE_URL + beitrag['img'],
                'path' : url_for(endpoint, ekey=beitrag['ekey']),
#                'info' : {'title': label, 'episode': episode,  'plot': 'plot could be found using the entry_descl or entry_descs keys in the AJAX answer'},
                'info' : {'title': label, 'episode': episode},
                'context_menu' : [(localizer('toggle_watched'), 'XBMC.Action(ToggleWatched)')],
                'is_playable' : True
                }
        items.append(item)
    # Einige Beiträge sind in der SWR Mediathek nicht verlinkt und nur über 'www.schaetze-der-welt-de' verfügbar. Diese fügen wir auch noch hinzu
    for beitrag in liste_fehlender_beitraege:
        label, episode = enrich_title(beitrag['title'].decode('utf-8'), localizer)
        item = {'label' : label.strip(),
                'thumbnail' : beitrag['icon'],
                'icon' : beitrag['icon'],
                'path' : url_for(endpoint, ekey=DIRECT_EKEY + beitrag['ekey']),
#                'info' : {'title': label, 'episode': episode,  'plot': 'plot could be found using the entry_descl or entry_descs keys in the AJAX answer'},
                'info' : {'title': label, 'episode': episode},
                'context_menu' : [(localizer('toggle_watched'), 'XBMC.Action(ToggleWatched)')],
                'is_playable' : True
                }
        items.append(item)

#    items.sort(key=lambda video: video['label'])
    items.sort(key=lambda video: video['info'])

# Debug log
    if (False):
        items.sort(key=lambda video: video['info'])
        tot_items  = len(items)
        tot_urls   = 0
        miss_items = 0
        miss_urls  = 0
        lastitem   = 0
        o = open('./schaetze-der-welt.txt', 'w')
        o.write("Übersicht Folgen 'Schätze der Welt'\n")
        o.write("===================================\n\n")
        for item in items:
            j = get_json_for_ekey(item['path'].split('/')[-1])
            if (item['info']['episode'] > lastitem + 1):
                for x in range (lastitem, item['info']['episode']-1):
                    miss_items += 1
                    o.write("%03d : FEHLENDE FOLGE!!\n\n" % (x + 1))
            lastitem = item['info']['episode']
            if (j['url'] == None):
                miss_urls += 1
                o.write("%03d : %s\n      KEINE URL GEFUNDEN!!\n\n" % (item['info']['episode'], item['label']))
            else:
                tot_urls += 1
                o.write("%03d : %s\n      %s\n\n" % (item['info']['episode'], item['label'], j['url'].encode('utf-8', 'ignore')))
            # A pause is needed as the SWR server protects against DOS attacks by refusing connections within too short time
            time.sleep(6)
        o.write("\nStatistik\n---------\n\n")
        o.write("\nTotal Folgen:    %3d" % (tot_items))
        o.write("\nTotal URLs:      %3d" % (tot_urls))
        o.write("\nFehlende URLs:   %3d" % (miss_urls))
        o.write("\nFehlende Folgen: %3d\n" % (miss_items))
        o.close()
# Debug log until here

    log_info("Anzahl Videos: " + str(len(items)))
    #log_info("Videos: " + str(items))
    return items


def regex_pattern_for_items():
    return re.compile('<a href=\"/player.htm\?show=(?P<ekey>[a-z0-9-]*)\" >[\n\t]*<img src=\"(?P<img>.*)\" class=\"img\" title=\"(?P<title>.*)\" alt=\".*\"/>')


def enrich_title(title, localizer):
    # Properly code the title string (remove HTML encoding and convert to ASCII
    title = htmlParser.unescape(title).encode('utf-8', 'ignore').strip()
    log_info("Neues Video: " + title)

    # Ermittle die Folge
    land    = ""
    folge   = 0
    s_folge = ""
    idxFolge = title.find("Folg")
    if (idxFolge == 0):
        # Die Folge steht am Anfang
        idxdigit = idxFolge + 4
        while (title[idxdigit].isdigit() or (title[idxdigit] == ' ') or ((idxdigit == idxFolge + 4) and (title[idxdigit] == 'e'))):
            idxdigit += 1
        s_folge = title[idxFolge+4:idxdigit]
        if (s_folge[0] == 'e'):
            s_folge = s_folge[1:]
        s_folge = s_folge.strip()
        s_rest  = title[idxdigit:].strip()
    elif (idxFolge > -1):
        # Die Folge steht (mehr oder weniger) am Schluss
        s_folge = title[idxFolge+4:]
        s_rest  = title[:idxFolge].strip()
        if (s_rest[-1] == ','):
            s_rest = s_rest[:-1]
        elif (s_rest[-2:] == ' ('):
            s_rest = s_rest[:-2]
    else:
        # Vielleicht fehlt ja einfach das Wort 'Folge'
        idxdigit = len(title)-1
        while (title[idxdigit].isdigit()):
            idxdigit -= 1
        if (idxdigit < (len(title)-1)):
            s_folge = title[idxdigit+1:]
            s_rest  = title[:idxdigit].strip()
            if (s_rest[-1] == ','):
                s_rest = s_rest[:-1]
        else:
            # Hopfen und Malz sind verloren - es gibt keine Angabe zur Folge :-(
            s_rest = title
    # Ermittle die Nummer der Folge
    if (s_folge <> ""):
        if (s_folge[0] == 'e'):
            s_folge = s_folge[1:]
        s_folge = s_folge.replace(')', '').replace(':', '').strip()
        if (s_folge.isdigit()):
            folge = int(s_folge)
            # Korrektur für die Folge über Reims
            if (folge == 932):
                folge = 392
        else:
            print "FEHLER (s_folge): " + s_folge

    # Manuelle Korrekturen:
    # Falls die Folge nicht ermittelt werden konnte:
    # Wissens-Datenbank zur Ermittlung der Folge ausprobieren
    if (folge == 0):
        found = False
        idxKey = 0
        while ((not found) and (idxKey < len(schluesselwoerter_fuer_fehlende_folgen))):
            if (s_rest.find(schluesselwoerter_fuer_fehlende_folgen.items()[idxKey][0]) > -1):
                folge = schluesselwoerter_fuer_fehlende_folgen.items()[idxKey][1]
                found = True
            idxKey += 1
    else:
        # Korrektur falscher Angaben der Folge:
        if (folge in liste_falscher_folgen.keys()):
            folge = liste_falscher_folgen[folge]

    # Ermittle das Land
    if (len(title) >= 100):
        print title
        # Ev. wurde ein Teil des Titels (z.B. die Folge) abgeschnitten
        if (s_rest[-7:] == ", Folge"):
            s_rest = s_rest[:-7]
        elif (s_rest[-6:] == ", Folg"):
            s_rest = s_rest[:-6]
        elif (s_rest[-5:] == ", Fol"):
            s_rest = s_rest[:-5]
        elif (s_rest[-4:] == ", Fo"):
            s_rest = s_rest[:-4]
        elif (s_rest[-3:] == ", F"):
            s_rest = s_rest[:-3]
        elif (s_rest[-2:] == " F"):
            s_rest = s_rest[:-2]
    if (s_rest[-1:] == (')')):
        s_rest = s_rest[:-1].strip()
    if (s_rest.rfind(',') > -1):
        land = s_rest[s_rest.rfind(',')+1:].strip()
        s_rest = s_rest[:s_rest.rfind(',')].strip()

    # Manuelle Korrekturen:
    # Falls das Land nicht ermittelt werden konnte:
    # Wissens-Datenbank zur Ermittlung des Landes ausprobieren
    if (land == ""):
        land   = localizer('unordered').encode('utf-8', 'ignore')
        found  = False
        idxKey = 0
        while ((not found) and (idxKey < len(schluesselwoerter_fuer_fehlende_laender))):
            if (s_rest.find(schluesselwoerter_fuer_fehlende_laender.items()[idxKey][0]) > -1):
                land = schluesselwoerter_fuer_fehlende_laender.items()[idxKey][1]
                found = True
            idxKey += 1      
    else:
        # Korrektur falscher Ermittlung des Landes:
        found  = False
        idxKey = 0
        while ((not found) and (idxKey < len(schluesselwoerter_fuer_falsche_laender))):
            if (s_rest.find(schluesselwoerter_fuer_falsche_laender.items()[idxKey][0]) > -1):
                land = schluesselwoerter_fuer_falsche_laender.items()[idxKey][1]
            idxKey += 1
        # Korrektur falscher Angaben des Landes:
        if (land in liste_falscher_laender.keys()):
            land = liste_falscher_laender[land]
        # Korrektur der Parser-Fehler
        found  = False
        idxKey = 0
        while ((not found) and (idxKey < len(schluesselwoerter_fuer_falsche_angaben))):
            if (title.find(schluesselwoerter_fuer_falsche_angaben.items()[idxKey][0]) > -1):
                if ("land" in schluesselwoerter_fuer_falsche_angaben.items()[idxKey][1].keys()):
                    land = schluesselwoerter_fuer_falsche_angaben.items()[idxKey][1]["land"]
                else:
                    land = localizer('unordered').encode('utf-8', 'ignore')
                if ("titel" in schluesselwoerter_fuer_falsche_angaben.items()[idxKey][1].keys()):
                    s_rest = schluesselwoerter_fuer_falsche_angaben.items()[idxKey][1]["titel"]
            idxKey += 1
    # Korrektur der Anfangsbuchstaben für korrekte Sortierung
    if (len(land.decode('utf-8')) > 0):
        if (land.decode('utf-8')[0] == u"Ä"):
            land = (u"Ae"+land.decode('utf-8')[1:]).encode('utf-8')
        elif (land.decode('utf-8')[0] == u"Ö"):
            land = (u"Oe"+land.decode('utf-8')[1:]).encode('utf-8')
        elif (land.decode('utf-8')[0] == u"Ü"):
            land = (u"Ue"+land.decode('utf-8')[1:]).encode('utf-8')

    if (folge == 0):
        log_info("Folge unbekannt für Titel '%s'" % (title))
    if (land == ""):
        log_info("Land unbekannt für Titel '%s'" % (title))

    #return '{0}: {1}'.format(land, title).encode('utf-8')
#    return "%03d: %s - %s" % (folge,  land,  s_rest)
#    return land + ' - ' + title
    if (folge == 0):
        return ("%s - %s" % (land, s_rest),  0)
    else:
        return ("%s - %s (%s %d)" % (land, s_rest, localizer('episode').encode('utf-8', 'ignore'), folge),  folge)
    
    
def get_json_for_ekey(ekey):
    # TODO: auf get_content_from_url umstellen, aber: return response.read() umstellen auf return response
    log_info("Lese ekey JSON: " + ekey)
    if (ekey[:len(DIRECT_EKEY)] == DIRECT_EKEY):
        kontinent   = None
        url         = None
        videosize   = 0
        json_object = {'attr': {'entry_title': "", 'entry_image_16_9': ""}}
        found       = False
        i           = 0
        while ((not found) and (i < len(liste_fehlender_beitraege))):
            beitrag = liste_fehlender_beitraege[i]
            if (beitrag['ekey'] == ekey[len(DIRECT_EKEY):]):
                found = True
                json_object['attr']['entry_title'] = beitrag['title'].decode('utf-8')
                kontinent = beitrag['kontinent']
                json_object['attr']['entry_image_16_9'] = beitrag['icon'],
                url = beitrag['url']
                try:
                    videosize = float(groessenangaben[url.split('.')[-2]])
                except:
                    pass
            i += 1
    else:
#        request = Request(EKEY_URL + ekey, headers = REQUEST_HEADERS)
        request = Request(EKEY_URL + ekey)
        log_info(EKEY_URL + ekey)
#        response = urlopen(request, timeout = SOCKET_TIMEOUT)
        response = urlopen(request)
        json_object = json.load(response)
        log_info("Title: " + str(json_object['attr']['entry_title'].encode('utf-8')))
        # desc: Regex: 'entry_descl'
        #log_info("descr: " + json_object['attr']['entry_descl'])
        # image: entry_image_16_9
        #log_info("img: " + json_object['attr']['entry_image_16_9'])    
        # url: {"val0":"h264","val1":"3" - hochauflösend bzw. regex: 'rmtp ... l.mp4'
        #url = re.match('.*(?P<url>rtmp.*\.l\.mp4)', str(json_object['sub']))
        #log_info("url: " + url.group('url'))
        
        # Listen durchsuchen: s.a. http://stackoverflow.com/questions/9542738/python-find-in-list
        # Kontinent:
        # Suche nach Europa, Amerika, Asien, Australien, Ozeanien, Afrika
        # Liste traversieren: Wenn Atrtribut name == entry_keywd
        kontinent = None
        url       = None
        videosize = 0
        for item in json_object['sub']:
            if(item['name'] == 'entry_keywd' and kontinent is None):
                #log_info("item['attr']['val']" + item['attr']['val'])
                if (item['attr']['val'] in kontinente_und_anderes):
                    kontinent = item['attr']['val']
            elif(item['name'] == 'entry_media'):            
                if (item['attr']['val0'] in ('h264', 'm3u8')):
                    urlparts = item['attr']['val2'].split('/')
                    if (urlparts[-1][-4:].lower() == ".mp4"):
                        # Direkter Link - SUPER!
                        try:
                            mp4link = urlparts[-1].split('.')
                            if (float(groessenangaben[mp4link[-2]]) >= float(videosize)):
                                url = item['attr']['val2']
                                videosize = float(groessenangaben[mp4link[-2]])
                        except:
                            log_info("Unerwartetes URL Format: " + urlparts[-4:])
                    elif (urlparts[-2][-4:].lower() == ".mp4"):
                        # Indirekter Link - Versuche, den direkten Link zu erraten
                        if ((urlparts[2] == "ios-ondemand.swr.de") and (urlparts[3] == 'i')):
                            try:
                                mp4link = urlparts[-2].split('.')
                                if (float(groessenangaben[mp4link[-2]]) > float(videosize)):
                                    url = "http://pd-ondemand.swr.de/" + '/'.join(urlparts[4:-1])
                                    videosize = float(groessenangaben[mp4link[-2]])
                            except:
                                log_info("Unerwartetes URL Format: " + urlparts[-2])
                        else:
                           log_info("Unerwartete Basis-URL: " + item['attr']['val2'])
                    else:
                       log_info("URL verweist auf keine MP4 Datei: " + item['attr']['val2'])
                else:
                    log_info("Unerwarteter Codec: " + item['attr']['val0'] + ", URL: " + item['attr']['val2'])

    if (kontinent is None):
        kontinent = ''
    if (url is None):
        # Falls die URL nicht ermittelt werden konnte:
        # Wissens-Datenbank zur Ermittlung der URL ausprobieren
        if (ekey in liste_fehlender_urls.keys()):
            url = liste_fehlender_urls[ekey]
        else:
            log_info("Keine URL bekannt für ekey '%s'" % ekey)
    log_info("Kontinent: " + kontinent)
    log_info("url: " + str(url))
    log_info("Groesse: " + str(videosize))
    
    # Land:
    # Suche in Titel nach 'Folge', davor kommt das Land, wenn nicht, dann leer lassen
    match = re.match('.* (?P<land>.*), Folge', str(json_object['attr']['entry_title'].encode('utf-8')))
    if (match is not None):
        land = match.group('land')
        log_info("Land: " + land)
    else:
        land = ''
    
    return {'ekey':ekey, 'label':json_object['attr']['entry_title'], 'url':url, 'land':land, 'kontinent':kontinent, 'img':json_object['attr']['entry_image_16_9']}

  

def get_content_from_url(url):
    request = Request(url, headers = REQUEST_HEADERS)
    #log_info("Timeout: " + str(socket.getdefaulttimeout()))
    sitereached = False
    timeoutcounter = 0
    while not sitereached and timeoutcounter < MAX_TIMEOUT_RETRIES:
        try:
            response = urlopen(request, timeout = SOCKET_TIMEOUT)
            sitereached = True
        except socket.timeout:
           log_info("Timeout (" + str(SOCKET_TIMEOUT) + " sec) reached accessing " + url)
           timeoutcounter+=1            
        except Exception,e:
            log_info("Exception " + str(e) + " accessing URL " + url)
            raise e
    if (timeoutcounter == MAX_TIMEOUT_RETRIES):
        log_info("Limit for retries after timeout reached: " + str(MAX_TIMEOUT_RETRIES))
        log_info("Site may be down?")
        raise socket.timeout        
                    
    log_info("URL opened: " + url)
    return response.read()


def log_info(msg):
    logger.info('HtmlScraper: %s' % msg)

def log_debug(msg):
    logger.debug('HtmlScraper: %s' % msg)
    
    

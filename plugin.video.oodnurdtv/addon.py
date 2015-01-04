#!/usr/bin/python
#Plugin to watch BG TV on XBMC through the www.drundoo.com web site
#Copyright (C) 2014  pesheto
#
#Note: The program requires an account set up through http://www.drundoo.com

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

from xbmcswift2 import Plugin
import xbmc, xbmcgui
import sys

from resources.drundoo import drundoo

plugin = Plugin()
my_drundoo = drundoo(plugin.get_setting('username'),plugin.get_setting('password'))


@plugin.route('/')
def index():
    
    items = [{'label':'Live', 'path':plugin.url_for('live')},
             {'label':'Timeshift', 'path':plugin.url_for('time')},
             {'label':'Playlist', 'path':plugin.url_for('playlist')},
             {'label':'ZAPIS', 'path':plugin.url_for('zapis')}
            ]
        
    return items

######################################
#This section is for the live stations
######################################

@plugin.route('/live/')
def live():
    play_title, play_link = my_drundoo.get_list('http://www.drundoo.com/channels/',4)
    items=[]
    for my_title, my_link in zip(play_title, play_link):
        items.append({'label':my_title,'path': plugin.url_for('live2',live_var=my_link),'is_playable':True})
        
    return items

@plugin.route('/live2/<live_var>')
def live2(live_var):
    url = live_var
    plugin.set_resolved_url(my_drundoo.play_live_url(url))

######################################
#End of live section 
######################################

######################################
#Timeshift section
######################################

@plugin.route('/time/')
def time():
    items=[]
    
    play_title, play_link = my_drundoo.get_list('http://www.drundoo.com/channels/',2)
    
    for my_title, my_link in zip(play_title, play_link):
        items.append({'label': my_title,'path': plugin.url_for('time_stations',url=my_link)})
        
    return items

@plugin.route('/time_stations/,<url>')
def time_stations(url):
    
    play_title, play_link = my_drundoo.get_list(url,3)

    items = []
    for my_title, my_link in zip(play_title, play_link):
        items.append({'label':my_title,'path': plugin.url_for('time_url',url=my_link),'is_playable':True})
    return items

@plugin.route('/time_url/<url>')
def time_url(url):
    url = url
    plugin.set_resolved_url(my_drundoo.play_live_url(url))

#####################################
#End of timeshift section
#####################################

#####################################
#Playlist section
#####################################

@plugin.route('/playlist/')
def playlist():
    play_title = []
    play_link = []	
    for i in range(1,20):
        temp_title, temp_link = my_drundoo.get_list('http://www.drundoo.com/watch/playlists/?page='+str(i))
	play_title.extend(temp_title)
        play_link.extend(temp_link)
    
    items=[]
    for my_title, my_link in zip(play_title, play_link):
        items.append({'label':my_title,'path': plugin.url_for('playlist_stations',playlist=my_link)})
        
    return items

@plugin.route('/playlist/,<playlist>')
def playlist_stations(playlist):
    
    play_link, play_title = my_drundoo.make_shows(playlist,'list')

    items = []
    for my_title,my_link in zip(play_title,play_link):
        items.append({'label': my_title,'path':plugin.url_for('playlist_final',url=my_link), 'is_playable':True})
    return items

@plugin.route('/playlist_final/<url>')
def playlist_final(url):
    plugin.set_resolved_url(my_drundoo.play_live_url(url))

#####################################
#End of playlist section
#####################################

#####################################
#Zapis section
#####################################

@plugin.route('/zapis/')
def zapis():
    play_title, play_link = my_drundoo.get_list('http://www.drundoo.com/channels/',2)
    items=[]
    for my_title, my_link in zip(play_title, play_link):
        items.append({'label':my_title,'path': plugin.url_for('oshte',zapis=my_link)})
        
    return items

@plugin.route('/oshte/<zapis>')
def oshte(zapis):
    #oshte_list = my_drundoo.get_list('http://www.drundoo.com/channels/97/btv_hd/')
    play_title, play_link = my_drundoo.get_list(zapis)
    items=[]
    for my_title, my_link in zip(play_title, play_link):
        items.append({'label':my_title,'path': plugin.url_for('oshte_stations',oshte=my_link)})
        
    return items

@plugin.route('/oshte_stations/,<oshte>')
def oshte_stations(oshte):
    
    play_link, play_title = my_drundoo.make_shows(oshte,'list')

    items = []
    for my_title,my_link in zip(play_title,play_link):
        items.append({'label': my_title,'path': plugin.url_for('oshte_final',url=my_link), 'is_playable':True})
    return items

@plugin.route('/oshte_final/<url>')
def oshte_final(url):
    plugin.set_resolved_url(my_drundoo.play_live_url(url))

#####################################
#End of zapis section
#####################################



if __name__ == '__main__':
    plugin.run()

# -*- coding: utf-8 -*-

'''
    Funimation|Now Add-on
    Copyright (C) 2016 Funimation|Now

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import re;
import sys;
import json;
import time;
import xbmc;
import hashlib;
import os;
import zlib;
import base64;
import codecs;
import xmlrpclib;
import logging;

try: 
    from sqlite3 import dbapi2 as database;

except: 
    from pysqlite2 import dbapi2 as database;

from resources.lib.modules import control;


logger = logging.getLogger('funimationnow');



class player(xbmc.Player):
    def __init__ (self):
        xbmc.Player.__init__(self);


    def run(self, meta):
        
        try:
            
            control.sleep(200);

            self.totalTime = 0; 
            self.currentTime = 0;
            self.offset = '0';

            self.content = meta['content'];
            self.ids = meta['ids'];
            self.show_id = meta['show_id'];
            self.asset_id = meta['asset_id'];


            if(meta['continueplayback'] == 0):
                self.offset = meta['progress'];


            self.item = control.item(path=meta['url']);
            
            self.item.setArt(meta['art']);

            self.item.setInfo(type='Video', infoLabels = meta['infoLabels']);


            if 'plugin' in control.infoLabel('Container.PluginName'):
                control.player.play(meta['url'], self.item);

            control.resolve(int(sys.argv[1]), True, self.item);

            control.window.setProperty('script.trakt.ids', json.dumps(self.ids));

            self.keepPlaybackAlive();

            control.window.clearProperty('script.trakt.ids');


        except Exception as inst:
            logger.error(inst);
            
            return;


    def keepPlaybackAlive(self):

        from resources.lib.modules import utils;

        overlay = '6';
        playcount = 0;
        pname = '%s.player.overlay' % control.addonInfo('id');

        control.window.clearProperty(pname);

        showstatus = utils.getshowstatus(self.show_id);

        if showstatus is not None and self.asset_id in showstatus:

            try:

                status = showstatus[self.asset_id];
                playcount = int(status['watched']);
                
                overlay = '6' if playcount <= 0 else '7';

            except:
                overlay = '6';
                pass;


        for i in range(0, 240):

            if self.isPlayingVideo(): 
                break;

            xbmc.sleep(1000);


        if overlay == '7':

            while self.isPlayingVideo():

                try:
                    self.currentTime = self.getTime();
                    self.totalTime = self.getTotalTime();

                    utils.syncdbprogress(self.show_id, self.asset_id, self.content, self.currentTime, self.totalTime, False, '7');

                except Exception as inst:
                    logger.error(inst);
                    pass;

                xbmc.sleep(2000);

        else:

            while self.isPlayingVideo():

                try:

                    self.currentTime = self.getTime();
                    self.totalTime = self.getTotalTime();

                    watcher = ((self.currentTime / self.totalTime) >= .9);
                    property = control.window.getProperty(pname);

                    if watcher == True and not property == '7':

                        utils.syncdbprogress(self.show_id, self.asset_id, self.content, self.currentTime, self.totalTime, False, '7');

                        try:
                            control.window.setProperty(pname, '7');

                        except Exception as inst:
                            logger.error(inst);
                            pass;


                    elif watcher == False and not property == '6':

                        utils.syncdbprogress(self.show_id, self.asset_id, self.content, self.currentTime, self.totalTime, False, '6');

                        try:
                            control.window.setProperty(pname, '6');

                        except Exception as inst:
                            logger.error(inst);
                            pass;

                    else:

                        utils.syncdbprogress(self.show_id, self.asset_id, self.content, self.currentTime, self.totalTime, False, str(property));
                        

                except Exception as inst:
                    logger.error(inst);

                    pass;

                xbmc.sleep(2000);


    def idleForPlayback(self):

        for i in range(0, 200):

            if control.condVisibility('Window.IsActive(busydialog)') == 1: 
                control.idle();

            else: 
                break;

            control.sleep(100);


    def onPlayBackStarted(self):
        from resources.lib.modules import trakt;

        if not self.offset == '0': 
            self.seekTime(float(self.offset));

        self.idleForPlayback();

        trakt.startProgress(self.content, self.show_id, self.asset_id, int(self.offset), self.getTotalTime());


    def onPlayBackResumed(self):
        from resources.lib.modules import trakt;

        trakt.startProgress(self.content, self.show_id, self.asset_id, int(self.currentTime), self.getTotalTime());


    def onPlayBackPaused(self):
        from resources.lib.modules import trakt;

        trakt.pauseProgress(self.content, self.show_id, self.asset_id, int(self.currentTime), self.getTotalTime());


    def onPlayBackStopped(self):

        from resources.lib.modules import utils;

        try:

            pname = '%s.player.overlay' % control.addonInfo('id');
            rname = '%s.player.resumetime' % control.addonInfo('id');

            rtime = str(int(self.currentTime));

            watcher = ((self.currentTime / self.totalTime) >= .9);
            property = control.window.getProperty(pname);

            '''self.item.setProperty("resumetime", str(1000))
            control.window.setProperty(rname, str(1000));

            self.item.setInfo(type='Video', infoLabels = {'resumetime':str(1000)});
            control.refresh();'''

            if watcher == True and not property == '7':

                try:
                    control.window.setProperty(pname, '7');

                except Exception as inst:
                    logger.error(inst);
                    pass;

                utils.syncdbprogress(self.show_id, self.asset_id, self.content, self.currentTime, self.totalTime, True, '7');

            elif watcher == False and not property == '6':

                try:
                    control.window.setProperty(pname, '6');

                except Exception as inst:
                    logger.error(inst);
                    pass;
                    
                utils.syncdbprogress(self.show_id, self.asset_id, self.content, self.currentTime, self.totalTime, True, '6');

            else:
                utils.syncdbprogress(self.show_id, self.asset_id, self.content, self.currentTime, self.totalTime, True, property);

            '''else:
                #We want to show the inprogress tag but it is not working
                control.window.setProperty(rname, rtime);
                control.refresh();'''


            control.refresh();          

        except Exception as inst:
            logger.error(inst);

            pass;


    def onPlayBackEnded(self):
        self.onPlayBackStopped();

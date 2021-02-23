# -*- coding: utf-8 -*-
"""
The database updater module

Copyright 2017-2019, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""

# -- Imports ------------------------------------------------
import time
import datetime
import _strptime
import hashlib
import resources.lib.updateFileParser as UpdateFileParser
import resources.lib.appContext as appContext

from contextlib import closing
from codecs import open

import json

import resources.lib.mvutils as mvutils

# -- Classes ------------------------------------------------
# pylint: disable=bad-whitespace


class UpdateFileImport(object):
    """ The database updator class """

    def __init__(self, targetFilename, pDatabase):
        self.logger = appContext.MVLOGGER.get_new_logger('UpdateFileImport')
        self.notifier = appContext.MVNOTIFIER
        self.settings = appContext.MVSETTINGS
        self.monitor = appContext.MVMONITOR
        self.targetFilename = targetFilename
        self.database = pDatabase
        self.use_xz = mvutils.find_xz() is not None
        self.count = 0
        self.insertCount = 0
        self.updateCount = 0
        self.film = {}
        self.errorCount = 0

######################################################################

    def updateIncremental(self):
        self._update_start()
        self._importFile(self.targetFilename)
        self._update_end()

    def updateFull(self):
        self._update_start()
        self.database.import_begin()
        self._importFile(self.targetFilename)
        self.deletedCount = self.database.import_end()
        self._update_end()

    def _importFile(self, targetFilename):
        #
        if not mvutils.file_exists(targetFilename):
            self.logger.error('File {} does not exists', targetFilename)
            return False
        # estimate number of records in update file
        fileSizeInByte = mvutils.file_size(targetFilename)
        records = int(fileSizeInByte / 600)
        self.logger.info('Starting import of approximately {} records from {}', records, targetFilename)
        #
        # pylint: disable=broad-except
        try:
            flsm = 0
            flts = 0
            #
            sender = ""
            thema = ""
            self.notifier.show_update_progress()
            #
            ufp = UpdateFileParser.UpdateFileParser(self.logger, 512000, targetFilename)
            ufp.init()
            fileHeader = ufp.next(',"X":');
            # META
            # {"Filmliste":["30.08.2020, 11:13","30.08.2020, 09:13","3","MSearch [Vers.: 3.1.139]","d93c9794acaf3e482d42c24e513f78a8"],"Filmliste":["Sender","Thema","Titel","Datum","Zeit","Dauer","Größe [MB]","Beschreibung","Url","Website","Url Untertitel","Url RTMP","Url Klein","Url RTMP Klein","Url HD","Url RTMP HD","DatumL","Url History","Geo","neu"]
            # this is the timestamp of this database update
            # value = jsonDoc['Filmliste'][0]
            value = fileHeader[15:32]
            # self.logger.debug( 'update date ' + value )
            try:
                fldt = datetime.datetime.strptime(value.strip(), "%d.%m.%Y, %H:%M")
                flts = int(time.mktime(fldt.timetuple()))
                self.logger.debug('Filmliste dated {}', value.strip())
                self.database.set_status('UPDATING', pFilmupdate=flts)
            except TypeError:
                # pylint: disable=line-too-long
                # SEE: https://forum.kodi.tv/showthread.php?tid=112916&pid=1214507#pid1214507
                # Wonderful. His name is also Leopold
                try:
                    flts = int(time.mktime(time.strptime(value.strip(), "%d.%m.%Y, %H:%M")))
                    self.database.set_status('UPDATING', pFilmupdate=flts)
                    self.logger.debug('Filmliste dated {}', value.strip())
                    # pylint: disable=broad-except
                except Exception as err:
                    # If the universe hates us...
                    self.logger.debug('Could not determine date "{}" of filmliste: {}', value.strip(), err)
            except ValueError as err:
                pass

            #
            recordArray = [];
            #
            while (True):
                aPart = ufp.next(',"X":');
                if (len(aPart) == 0):
                    break;
                #
                aPart = '{"X":' + aPart;
                if (not(aPart.endswith("}"))):
                    aPart = aPart + "}";
                #
                jsonDoc = json.loads(aPart)
                jsonDoc = jsonDoc['X']
                self._init_record()
                # behaviour of the update list
                if (len(jsonDoc[0]) > 0):
                    sender = jsonDoc[0][:32]
                else:
                    jsonDoc[0] = sender
                # same for thema
                if (len(jsonDoc[1]) > 0):
                    thema = jsonDoc[1][:128]
                else:
                    jsonDoc[1] = thema
                #
                self.film['channel'] = sender
                self.film['show'] = thema
                self.film["title"] = jsonDoc[2][:128]
                #
                if len(jsonDoc[3]) == 10:
                    self.film["aired"] = jsonDoc[3][6:] + '-' + jsonDoc[3][3:5] + '-' + jsonDoc[3][:2]
                    if (len(jsonDoc[4]) == 8):
                        self.film["aired"] = self.film["aired"] + " " + jsonDoc[4]
                #
                if len(jsonDoc[5]) > 0:
                    self.film["duration"] = jsonDoc[5]
                if len(jsonDoc[7]) > 0:
                    self.film["description"] = jsonDoc[7][:1024]
                self.film["url_video"] = jsonDoc[8]
                self.film["website"] = jsonDoc[9]
                self.film["url_sub"] = jsonDoc[10]
                self.film["url_video_sd"] = self._make_url(jsonDoc[12])
                self.film["url_video_hd"] = self._make_url(jsonDoc[14])
                if len(jsonDoc[16]) > 0:
                    self.film["airedepoch"] = int(jsonDoc[16])
                self.film["geo"] = jsonDoc[18]
                #
                # check if the movie is there
                #
                checkString = sender + thema + self.film["title"] + self.film['url_video']
                idhash = hashlib.md5(checkString.encode('utf-8')).hexdigest()
                #
                showid = hashlib.md5(thema.encode('utf-8')).hexdigest()
                showid = showid[:8]
                #
                recordArray.append((
                        idhash,
                        int(time.time()),
                        self.film['channel'],
                        showid,
                        self.film['show'],
                        self.film["title"],
                        self.film['airedepoch'],
                        mvutils.make_duration(self.film['duration']),
                        self.film['description'],
                        self.film['url_sub'],
                        self.film['url_video'],
                        self.film['url_video_sd'],
                        self.film['url_video_hd']
                    ))
                self.count = self.count + 1
                # check
                if self.count % self.settings.getDatabaseImportBatchSize() == 0:
                    if self.monitor.abort_requested():
                        # kodi is shutting down. Close all
                        self._update_end()
                        self.notifier.close_update_progress()
                        raise Exception('User requested Abort')
                    else:
                        # run insert
                        try:
                            (ai, au) = self.database.import_films(recordArray)
                            self.insertCount += ai
                            self.updateCount += au
                        except Exception as err:
                            self.logger.error('Error in data import: {}', err)
                            self.errorCount = self.errorCount + 1
                        recordArray = []
                        # update status
                        percent = int(self.count * 100 / records)
                        percent = percent if percent <= 100 else 100
                        self.logger.debug('In progress (%d%%): insert:%d, update:%d' % (percent, self.insertCount, self.updateCount))
                        self.notifier.update_update_progress(percent, self.count, self.insertCount, self.updateCount)
            if len(recordArray) > 0:
                try:
                    (ai, au) = self.database.import_films(recordArray)
                    self.insertCount += ai
                    self.updateCount += au
                except Exception as err:
                    self.logger.error('Error in data import: {}', err)
                    self.errorCount = self.errorCount + 1
            #
            ufp.close()
            self.notifier.close_update_progress()
            if self.errorCount > 0:
                self.logger.warn('Update finished with error(s)')
        except Exception as err:
            self.logger.error(
                'Error {} while processing {}', err, targetFilename)
            self._update_end()
            self.database.set_status('ABORTED')
            self.notifier.close_update_progress()
            raise

######################################################################

    def _update_start(self):
        self.logger.debug('Initializing update...')
        self.count = 0
        self.insertCount = 0
        self.updateCount = 0
        self.deletedCount = 0
        self.startTime = time.time()
        self.film = {}
        self._init_record()

    def _update_end(self):
        self.logger.info('{} records processed in {} sec. Updated: {} Inserted: {} deleted: {}', self.count, int(time.time() - self.startTime), self.updateCount, self.insertCount, self.deletedCount)

    def _init_record(self):
        self.film["channel"] = ""
        self.film["show"] = ""
        self.film["title"] = ""
        self.film["aired"] = "1980-01-01 00:00:00"
        self.film["duration"] = "00:00:00"
        self.film["description"] = ""
        self.film["url_sub"] = ""
        self.film["url_video"] = ""
        self.film["url_video_sd"] = ""
        self.film["url_video_hd"] = ""
        self.film["airedepoch"] = 0
        self.film["geo"] = ""

    def _make_url(self, val):
        parts = val.split('|')
        if len(parts) == 2:
            cnt = int(parts[0])
            return self.film["url_video"][:cnt] + parts[1]
        else:
            return val

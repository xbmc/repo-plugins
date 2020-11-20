# -*- coding: utf-8 -*-
"""
The database updater module

Copyright 2017-2019, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""

# -- Imports ------------------------------------------------
import os
import time
import datetime
import subprocess
import resources.lib.updateFileParser as UpdateFileParser


# pylint: disable=import-error
try:
    # Python 3.x
    from urllib.error import URLError
except ImportError:
    # Python 2.x
    from urllib2 import URLError

from contextlib import closing
from codecs import open

import json

import resources.lib.mvutils as mvutils

# from resources.lib.utils import *
from resources.lib.store import Store
from resources.lib.exceptions import DatabaseCorrupted
from resources.lib.exceptions import DatabaseLost
from resources.lib.exceptions import ExitRequested

# -- Unpacker support ---------------------------------------
UPD_CAN_BZ2 = False
UPD_CAN_GZ = False

try:
    import bz2
    UPD_CAN_BZ2 = True
except ImportError:
    pass

try:
    import gzip
    UPD_CAN_GZ = True
except ImportError:
    pass

# -- Constants ----------------------------------------------
FILMLISTE_URL = 'https://liste.mediathekview.de/'
FILMLISTE_AKT = 'Filmliste-akt'
FILMLISTE_DIF = 'Filmliste-diff'

# -- Classes ------------------------------------------------
# pylint: disable=bad-whitespace


class MediathekViewUpdater(object):
    """ The database updator class """

    def __init__(self, logger, notifier, settings, monitor=None):
        self.logger = logger
        self.notifier = notifier
        self.settings = settings
        self.monitor = monitor
        self.database = None
        self.use_xz = mvutils.find_xz() is not None
        self.cycle = 0
        self.add_chn = 0
        self.add_shw = 0
        self.add_mov = 0
        self.del_chn = 0
        self.del_shw = 0
        self.del_mov = 0
        self.tot_chn = 0
        self.tot_shw = 0
        self.tot_mov = 0
        self.index = 0
        self.count = 0
        self.film = {}

    def init(self, convert=False):
        """ Initializes the updater """
        if self.database is not None:
            self.exit()
        self.database = Store(self.logger, self.notifier, self.settings)
        self.database.init(convert=convert)

    def exit(self):
        """ Resets the updater """
        if self.database is not None:
            self.database.exit()
            del self.database
            self.database = None

    def reload(self):
        """ Reloads the updater """
        self.exit()
        self.init()

    def is_enabled(self):
        """ Returns if the updater is enabled """
        return self.settings.updenabled

    def get_current_update_operation(self, force=False, full=False):
        """
        Determines which update operation should be done. Returns
        one of these values:

        0 - no update operation pending
        1 - full update
        2 - differential update

        Args:
            force(bool, optional): if `True` a full update
                is always returned. Default is `False`
            full(book, optional): if `True` a full update
                is always returned. Default is `False`
        """
        if self.database is None:
            # db not available - no update
            self.logger.info('Update disabled since database not available')
            return 0
        elif self.settings.updmode == 0:
            # update disabled - no update
            return 0
        elif self.settings.updmode == 1 or self.settings.updmode == 2:
            # manual update or update on first start
            if self.settings.is_update_triggered() is True:
                return self._get_next_update_operation(True, False)
            else:
                # no update on all subsequent calls
                return 0
        elif self.settings.updmode == 3:
            # automatic update
            if self.settings.is_user_alive():
                return self._get_next_update_operation(force, full)
            else:
                # no update if user is idle for more than 2 hours
                return 0
        elif self.settings.updmode == 4:
            # continous update
            return self._get_next_update_operation(force, full)

    def _get_next_update_operation(self, force=False, full=False):
        status = self.database.get_status()
        tsnow = int(time.time())
        tsold = status['lastupdate']
        dtnow = datetime.datetime.fromtimestamp(tsnow).date()
        dtold = datetime.datetime.fromtimestamp(tsold).date()
        if status['status'] == 'UNINIT':
            # database not initialized - no update
            self.logger.debug('database not initialized')
            return 0
        elif status['status'] == "UPDATING" and tsnow - tsold > 10800:
            # process was probably killed during update - no update
            self.logger.info(
                'Stuck update pretending to run since epoch {} reset', tsold)
            self.database.update_status('ABORTED')
            return 0
        elif status['status'] == "UPDATING":
            # already updating - no update
            self.logger.debug('Already updating')
            return 0
        elif not full and not force and tsnow - tsold < self.settings.updinterval:
            # last update less than the configured update interval - no update
            self.logger.debug(
                'Last update less than the configured update interval. do nothing')
            return 0
        elif dtnow != dtold:
            # last update was not today. do full update once a day
            self.logger.debug(
                'Last update was not today. do full update once a day')
            return 1
        elif status['status'] == "ABORTED" and status['fullupdate'] == 1:
            # last full update was aborted - full update needed
            self.logger.debug(
                'Last full update was aborted - full update needed')
            return 1
        elif full is True:
            # full update requested
            self.logger.info('Full update requested')
            return 1
        else:
            # do differential update
            self.logger.debug('Do differential update')
            return 2

    def update(self, full):
        """
        Downloads the database update file and
        then performs a database update

        Args:
            full(bool): Perform full update if `True`
        """
        if self.database is None:
            return
        elif self.database.supports_native_update(full):
            if self.get_newest_list(full):
                if self.database.native_update(full):
                    self.cycle += 1
            self.delete_list(full)
        elif self.database.supports_update():
            if self.get_newest_list(full):
                if self.import_database(full):
                    self.cycle += 1
            self.delete_list(full)

    def import_database(self, full):
        """
        Performs a database update when a
        downloaded update file is available

        Args:
            full(bool): Perform full update if `True`
        """
        (_, _, destfile, avgrecsize) = self._get_update_info(full)
        if not mvutils.file_exists(destfile):
            self.logger.error('File {} does not exists', destfile)
            return False
        # estimate number of records in update file
        fileSizeInByte = mvutils.file_size(destfile)
        records = int(fileSizeInByte / avgrecsize)
        self.logger.info( 'Starting import of {} records from {}', records, destfile )
        if not self.database.ft_init():
            self.logger.warn(
                'Failed to initialize update. Maybe a concurrency problem?')
            return False
        
        # pylint: disable=broad-except
        try:
            starttime = time.time()
            flsm = 0
            flts = 0
            ####
            flsm = 0
            sender = ""
            thema = ""
            self.notifier.show_update_progress()
            (self.tot_chn, self.tot_shw, self.tot_mov) = self._update_start(full)
            
            
            ufp = UpdateFileParser.UpdateFileParser(self.logger, 512000, destfile)
            ufp.init()
            fileHeader = ufp.next(',"X":');
            ### META
            ## {"Filmliste":["30.08.2020, 11:13","30.08.2020, 09:13","3","MSearch [Vers.: 3.1.139]","d93c9794acaf3e482d42c24e513f78a8"],"Filmliste":["Sender","Thema","Titel","Datum","Zeit","Dauer","Größe [MB]","Beschreibung","Url","Website","Url Untertitel","Url RTMP","Url Klein","Url RTMP Klein","Url HD","Url RTMP HD","DatumL","Url History","Geo","neu"]
            # this is the timestamp of this database update
            #value = jsonDoc['Filmliste'][0]
            value = fileHeader[15:32]
            #self.logger.info( 'update date ' + value )
            try:
                fldt = datetime.datetime.strptime(
                    value.strip(), "%d.%m.%Y, %H:%M")
                flts = int(time.mktime(fldt.timetuple()))
                self.database.update_status(filmupdate=flts)
                self.logger.info(
                    'Filmliste dated {}', value.strip())
            except TypeError:
                # pylint: disable=line-too-long
                # SEE: https://forum.kodi.tv/showthread.php?tid=112916&pid=1214507#pid1214507
                # Wonderful. His name is also Leopold
                try:
                    flts = int(time.mktime(time.strptime(
                        value.strip(), "%d.%m.%Y, %H:%M")))
                    self.database.update_status(
                        filmupdate=flts)
                    self.logger.info(
                        'Filmliste dated {}', value.strip())
                    # pylint: disable=broad-except
                except Exception as err:
                    # If the universe hates us...
                    self.logger.debug(
                        'Could not determine date "{}" of filmliste: {}', value.strip(), err)
            except ValueError as err:
                pass            

            ###
            while (True):
                aPart = ufp.next(',"X":');
                if (len(aPart) == 0):
                    break;
                ##
                aPart = '{"X":' + aPart;
                if (not(aPart.endswith("}"))):
                    aPart = aPart + "}";
                ##
                jsonDoc = json.loads(aPart)
                jsonDoc = jsonDoc['X']
                self._init_record()
                # behaviour of the update list
                if (len(jsonDoc[0]) > 0):
                    sender = jsonDoc[0]
                else:
                    jsonDoc[0] = sender
                # same for thema
                if (len(jsonDoc[1]) > 0):
                    thema = jsonDoc[1]
                else:
                    jsonDoc[1] = thema
                ##
                self._add_value( jsonDoc )
                self._end_record(records)
                if self.count % 100 == 0 and self.monitor.abort_requested():
                    # kodi is shutting down. Close all
                    self._update_end(full, 'ABORTED')
                    self.notifier.close_update_progress()
                    return True                

            ufp.close()        
            self._update_end(full, 'IDLE')
            self.logger.info('{} records processed',self.count)
            self.logger.info(
                'Import of {} in update cycle {} finished. Duration: {} seconds',
                destfile,
                self.cycle,
                int(time.time() - starttime)
            )
            self.notifier.close_update_progress()
            return True
        except KeyboardInterrupt:
            self._update_end(full, 'ABORTED')
            self.logger.info('Update cycle {} interrupted by user', self.cycle)
            self.notifier.close_update_progress()
            return False
        except DatabaseCorrupted as err:
            self.logger.error('{} on update cycle {}', err, self.cycle)
            self.notifier.close_update_progress()
        except DatabaseLost as err:
            self.logger.error('{} on update cycle {}', err, self.cycle)
            self.notifier.close_update_progress()
        except Exception as err:
            self.logger.error(
                'Error {} while processing {} on update cycle {}', err, destfile, self.cycle)
            self._update_end(full, 'ABORTED')
            self.notifier.close_update_progress()
        return False

    def get_newest_list(self, full):
        """
        Downloads the database update file

        Args:
            full(bool): Downloads the full list if `True`
        """
        (url, compfile, destfile, _) = self._get_update_info(full)
        if url is None:
            self.logger.error(
                'No suitable archive extractor available for this system')
            self.notifier.show_missing_extractor_error()
            return False

        # cleanup downloads
        self.logger.info('Cleaning up old downloads...')
        mvutils.file_remove(compfile)
        mvutils.file_remove(destfile)

        # download filmliste
        self.notifier.show_download_progress()

        # pylint: disable=broad-except
        try:
            self.logger.info('Trying to download {} from {}...',
                             os.path.basename(compfile), url)
            self.notifier.update_download_progress(0, url)
            mvutils.url_retrieve(
                url,
                filename=compfile,
                reporthook=self.notifier.hook_download_progress,
                aborthook=self.monitor.abort_requested
            )
        except URLError as err:
            self.logger.error('Failure downloading {} - {}', url, err)
            self.notifier.close_download_progress()
            self.notifier.show_download_error(url, err)
            return False
        except ExitRequested as err:
            self.logger.error(
                'Immediate exit requested. Aborting download of {}', url)
            self.notifier.close_download_progress()
            self.notifier.show_download_error(url, err)
            return False
        except Exception as err:
            self.logger.error('Failure writing {}', url)
            self.notifier.close_download_progress()
            self.notifier.show_download_error(url, err)
            return False

        # decompress filmliste
        if self.use_xz is True:
            self.logger.info('Trying to decompress xz file...')
            retval = subprocess.call([mvutils.find_xz(), '-d', compfile])
            self.logger.info('Return {}', retval)
        elif UPD_CAN_BZ2 is True:
            self.logger.info('Trying to decompress bz2 file...')
            retval = self._decompress_bz2(compfile, destfile)
            self.logger.info('Return {}', retval)
        elif UPD_CAN_GZ is True:
            self.logger.info('Trying to decompress gz file...')
            retval = self._decompress_gz(compfile, destfile)
            self.logger.info('Return {}', retval)
        else:
            # should never reach
            pass

        self.notifier.close_download_progress()
        return retval == 0 and mvutils.file_exists(destfile)

    def delete_list(self, full):
        """
        Deletes locally stored database update files

        Args:
            full(bool): Deletes the full lists if `True`
        """
        (_, compfile, destfile, _) = self._get_update_info(full)
        self.logger.info('Cleaning up downloads...')
        mvutils.file_remove(compfile)
        mvutils.file_remove(destfile)

    def _get_update_info(self, full):
        if self.use_xz is True:
            ext = '.xz'
        elif UPD_CAN_BZ2 is True:
            ext = '.bz2'
        elif UPD_CAN_GZ is True:
            ext = '.gz'
        else:
            return (None, None, None, 0, )

        info = self.database.get_native_info(full)
        if info is not None:
            return (
                self._get_update_url(info[0]),
                os.path.join(self.settings.datapath, info[1] + ext),
                os.path.join(self.settings.datapath, info[1]),
                500
            )

        if full:
            return (
                FILMLISTE_URL + FILMLISTE_AKT + ext,
                os.path.join(self.settings.datapath, FILMLISTE_AKT + ext),
                os.path.join(self.settings.datapath, FILMLISTE_AKT),
                600,
            )
        else:
            return (
                FILMLISTE_URL + FILMLISTE_DIF + ext,
                os.path.join(self.settings.datapath, FILMLISTE_DIF + ext),
                os.path.join(self.settings.datapath, FILMLISTE_DIF),
                700,
            )

    def _get_update_url(self, url):
        if self.use_xz is True:
            return url
        elif UPD_CAN_BZ2 is True:
            return os.path.splitext(url)[0] + '.bz2'
        elif UPD_CAN_GZ is True:
            return os.path.splitext(url)[0] + '.gz'
        else:
            # should never happen since it will not be called
            return None

    def _update_start(self, full):
        self.logger.info('Initializing update...')
        self.add_chn = 0
        self.add_shw = 0
        self.add_mov = 0
        self.del_chn = 0
        self.del_shw = 0
        self.del_mov = 0
        self.index = 0
        self.count = 0
        self.film = {
            "channel": "",
            "show": "",
            "title": "",
            "aired": "1980-01-01 00:00:00",
            "duration": "00:00:00",
            "size": 0,
            "description": "",
            "website": "",
            "url_sub": "",
            "url_video": "",
            "url_video_sd": "",
            "url_video_hd": "",
            "airedepoch": 0,
            "geo": ""
        }
        return self.database.ft_update_start(full)

    def _update_end(self, full, status):
        self.logger.info('Added: channels:%d, shows:%d, movies:%d ...' % (
            self.add_chn, self.add_shw, self.add_mov))
        (self.del_chn, self.del_shw, self.del_mov, self.tot_chn, self.tot_shw,
         self.tot_mov) = self.database.ft_update_end(full and status == 'IDLE')
        self.logger.info('Deleted: channels:%d, shows:%d, movies:%d' %
                         (self.del_chn, self.del_shw, self.del_mov))
        self.logger.info('Total: channels:%d, shows:%d, movies:%d' %
                         (self.tot_chn, self.tot_shw, self.tot_mov))
        self.database.update_status(
            status,
            int(time.time()) if status != 'ABORTED' else None,
            None,
            1 if full else 0,
            self.add_chn, self.add_shw, self.add_mov,
            self.del_chn, self.del_shw, self.del_mov,
            self.tot_chn, self.tot_shw, self.tot_mov
        )

    def _init_record(self):
        self.index = 0
        self.film["title"] = ""
        self.film["aired"] = "1980-01-01 00:00:00"
        self.film["duration"] = "00:00:00"
        self.film["size"] = 0
        self.film["description"] = ""
        self.film["website"] = ""
        self.film["url_sub"] = ""
        self.film["url_video"] = ""
        self.film["url_video_sd"] = ""
        self.film["url_video_hd"] = ""
        self.film["airedepoch"] = 0
        self.film["geo"] = ""

    def _end_record(self, records):
        if self.count % 1000 == 0:
            # pylint: disable=line-too-long
            percent = int(self.count * 100 / records)
            self.logger.info('In progress (%d%%): channels:%d, shows:%d, movies:%d ...' % (
                percent, self.add_chn, self.add_shw, self.add_mov))
            self.notifier.update_update_progress(
                percent if percent <= 100 else 100, self.count, self.add_chn, self.add_shw, self.add_mov)
            self.database.update_status(
                add_chn=self.add_chn,
                add_shw=self.add_shw,
                add_mov=self.add_mov,
                tot_chn=self.tot_chn + self.add_chn,
                tot_shw=self.tot_shw + self.add_shw,
                tot_mov=self.tot_mov + self.add_mov
            )
            self.count = self.count + 1
            (_, cnt_chn, cnt_shw, cnt_mov) = self.database.ft_insert_film(
                self.film,
                True
            )
        else:
            self.count = self.count + 1
            (_, cnt_chn, cnt_shw, cnt_mov) = self.database.ft_insert_film(
                self.film,
                False
            )
        self.add_chn += cnt_chn
        self.add_shw += cnt_shw
        self.add_mov += cnt_mov

    def _add_value(self, valueArray):
        self.film["channel"] = valueArray[0]
        self.film["show"] = valueArray[1][:255]
        self.film["title"] = valueArray[2][:255]
        ##
        if len(valueArray[3]) == 10:
            self.film["aired"] = valueArray[3][6:] + '-' + valueArray[3][3:5] + '-' + valueArray[3][:2]  
            if (len(valueArray[4]) == 8):
                self.film["aired"] = self.film["aired"] + " " + valueArray[4]
        ##
        if len(valueArray[5]) > 0:
            self.film["duration"] = valueArray[5]
        if len(valueArray[6]) > 0:
            self.film["size"] = int(valueArray[6])
        if len(valueArray[7]) > 0:
            self.film["description"] = valueArray[7]
        self.film["url_video"] = valueArray[8]
        self.film["website"] = valueArray[9]
        self.film["url_sub"] = valueArray[10]    
        self.film["url_video_sd"] = self._make_url(valueArray[12])
        self.film["url_video_hd"] = self._make_url(valueArray[14])
        if len(valueArray[16]) > 0:
            self.film["airedepoch"] = int(valueArray[16])
        self.film["geo"] = valueArray[18]
        
    def _make_url(self, val):
        parts = val.split('|')
        if len(parts) == 2:
            cnt = int(parts[0])
            return self.film["url_video"][:cnt] + parts[1]
        else:
            return val

    def _decompress_bz2(self, sourcefile, destfile):
        blocksize = 8192
        try:
            with open(destfile, 'wb') as dstfile, open(sourcefile, 'rb') as srcfile:
                decompressor = bz2.BZ2Decompressor()
                for data in iter(lambda: srcfile.read(blocksize), b''):
                    dstfile.write(decompressor.decompress(data))
                # pylint: disable=broad-except
        except Exception as err:
            self.logger.error('bz2 decompression failed: {}'.format(err))
            return -1
        return 0

    def _decompress_gz(self, sourcefile, destfile):
        blocksize = 8192
        # pylint: disable=broad-except

        try:
            with open(destfile, 'wb') as dstfile, gzip.open(sourcefile) as srcfile:
                for data in iter(lambda: srcfile.read(blocksize), b''):
                    dstfile.write(data)
        except Exception as err:
            self.logger.error(
                'gz decompression of "{}" to "{}" failed: {}', sourcefile, destfile, err)
            if mvutils.find_gzip() is not None:
                gzip_binary = mvutils.find_gzip()
                self.logger.info(
                    'Trying to decompress gzip file "{}" using {}...', sourcefile, gzip_binary)
                try:
                    mvutils.file_remove(destfile)
                    retval = subprocess.call([gzip_binary, '-d', sourcefile])
                    self.logger.info('Calling {} -d {} returned {}',
                                     gzip_binary, sourcefile, retval)
                    return retval
                except Exception as err:
                    self.logger.error(
                        'gz commandline decompression of "{}" to "{}" failed: {}',
                        sourcefile, destfile, err)
            return -1
        return 0

    # pylint: disable=pointless-string-statement
    """
    def _decompress_gz(self, sourcefile, destfile):
        blocksize = 8192
        # pylint: disable=broad-except,line-too-long

        try:
            srcfile = gzip.open(sourcefile)
        except Exception as err:
            self.logger.error('gz decompression of "{}" to "{}" failed on opening gz file: {}'.format(
                sourcefile, destfile, err))
            return -1

        try:
            dstfile = open(destfile, 'wb')
        except Exception as err:
            self.logger.error('gz decompression of "{}" to "{}" failed on opening destination file: {}'.format(
                sourcefile, destfile, err))
            return -1

        try:
            for data in iter(lambda: srcfile.read(blocksize), b''):
                try:
                    dstfile.write(data)
                except Exception as err:
                    self.logger.error('gz decompression of "{}" to "{}" failed on writing destination file: {}'.format(
                        sourcefile, destfile, err))
                    return -1
        except Exception as err:
            self.logger.error('gz decompression of "{}" to "{}" failed on reading gz file: {}'.format(
                sourcefile, destfile, err))
            return -1
        return 0
"""

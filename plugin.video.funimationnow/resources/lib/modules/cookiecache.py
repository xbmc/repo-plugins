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


import time;
import hashlib;
import logging;

from resources.lib.modules import control;

try: 
    from sqlite3 import dbapi2 as database;

except: 
    from pysqlite2 import dbapi2 as database;


logger = logging.getLogger('funimationnow');


def fetch(uid, idx = None):

    try:

        dbcon = database.connect(control.cookiesFile);
        dbcur = dbcon.cursor();

    except:

        return None;

    try:

        dbcur.execute("SELECT * FROM cookies WHERE (uid = '%s')" % (uid));

        match = dbcur.fetchone();

        if match is not None:

            if id is None:
                return match;

            else:
                return match[idx];

        else:
            return None;

    except Exception as inst:
        logger.error(inst);

        return None;


def insert(uid, rctext, fninfo):
    
    try:

        control.makeFile(control.dataPath);

        dbcon = database.connect(control.cookiesFile);
        dbcur = dbcon.cursor();

        logger.debug('Creating cookie table if it does not exist.');

        dbcur.execute("CREATE TABLE IF NOT EXISTS cookies (""uid TEXT, ""rctext TEXT, ""fninfo TEXT, UNIQUE(uid)"");");

        try: 

            logger.debug('Attempting to delete cookie entry.');

            #dbcur.execute("DELETE * FROM cookies WHERE (uid = '%s')" % (uid));  # * Is causing a syntax error
            dbcur.execute("DELETE FROM cookies WHERE (uid = '%s')" % (uid));

        except Exception as inst:

            logger.error(inst);

            pass;

        
        try: 

            logger.debug('Attempting to insert cookie entry.');

            dbcur.execute("INSERT INTO cookies Values (?, ?, ?)", (uid, rctext, fninfo));

        except Exception as inst:

            logger.error(inst);

            pass;


        logger.debug('Commiting DB change.');
        
        dbcon.commit();

        return True;


    except Exception as inst:

        logger.error(inst);

        return False;


def clearcookies():

    try: 

        control.makeFile(control.dataPath);

        dbcon = database.connect(control.cookiesFile);
        dbcur = dbcon.cursor();

        #dbcur.execute("DELETE FROM cookies"); #Not working for some reason.  Unclear to why since there are no errors
        dbcur.execute("DROP TABLE cookies");

        return True;

    except Exception as inst:

        logger.error(inst);

        return False;

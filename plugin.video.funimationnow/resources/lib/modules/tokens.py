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


def fetchtvdbtoken():

    try:

        dbcon = database.connect(control.tokensFile);
        dbcur = dbcon.cursor();

    except:

        return None;

    try:

        dbcur.execute("SELECT * FROM tvdbtoken");

        match = dbcur.fetchone();

        if match is not None:

            return match;

        else:
            return None;

    except Exception as inst:
        #logger.error(inst);
        return None;


def inserttvdbtoken(token, edate, rdate):
    
    logger.debug('Attempting to update tvdbtoken DB.');
    
    try:

        logger.debug('Validating DB file exists.');

        control.makeFile(control.dataPath);

        dbcon = database.connect(control.tokensFile);
        dbcur = dbcon.cursor();

        logger.debug('Creating tvdbtoken table if it does not exist.');

        dbcur.execute("CREATE TABLE IF NOT EXISTS tvdbtoken (""token TEXT, ""expiredate TEXT, ""refreshdate TEXT"");");

        try: 

            logger.debug('Attempting to delete tvdbtoken entry.');

            dbcur.execute("DELETE FROM tvdbtoken");

        except Exception as inst:

            #logger.error(inst);
            pass;

        
        try: 

            logger.debug('Attempting to insert tvdbtoken entry.');

            dbcur.execute("INSERT INTO tvdbtoken Values (?, ?, ?)", (token, edate, rdate));

        except Exception as inst:

            #logger.error(inst);
            pass;


        logger.debug('Commiting DB change.');
        
        dbcon.commit();

        return True;


    except Exception as inst:

        #logger.error(inst);
        return False;


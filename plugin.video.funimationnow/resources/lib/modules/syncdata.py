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


def fetchupdated(showid):

    try:

        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

    except:
        return None;

    try:
        import itertools;

        sql_stmt = """
            SELECT tvdbid
                ,lastUpdated
            FROM tvdb_series_info
            WHERE show_id IN ('%s')
        """;

        dbcur.execute(sql_stmt % showid);

        match = dbcur.fetchall();
        
        if match is not None:
            return match;

        else:
            return None;


    except Exception as inst:
        #logger.error(inst);

        return None;


def fetchepisodecount(showid):

    try:

        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

    except:
        return None;

    try:
        import itertools;

        sql_stmt = """
            SELECT COUNT (*)
            FROM tvdb_episode_info
            WHERE show_id IN ('%s')
        """;

        dbcur.execute(sql_stmt % showid);

        match = dbcur.fetchall();
        
        if match is not None:
            return int(match[0][0]);

        else:
            return 0;


    except Exception as inst:
        #logger.error(inst);

        return 0;


def fetchartwork(showid):

    try:

        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

    except:
        return None;

    try:
        import itertools;

        sql_stmt = """
            SELECT images
            FROM tvdb_series_info
            WHERE show_id IN ('%s')
        """;

        dbcur.execute(sql_stmt % showid);

        match = dbcur.fetchall();
        
        if match is not None:
            return match[0][0];

        else:
            return None;


    except Exception as inst:
        #logger.error(inst);

        return None;


def fetchshowname(showid):

    try:

        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

    except:
        return None;

    try:
        import itertools;

        sql_stmt = """
            SELECT fn_show_name
            FROM fn_episode_info
            WHERE show_id IN ('%s')
        """;

        dbcur.execute(sql_stmt % showid);

        match = dbcur.fetchall();
        
        if match is not None:
            return match[0][0];

        else:
            return None;


    except Exception as inst:
        #logger.error(inst);

        return None;


def fetchqueuestate(showid):

    try:

        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

    except:
        return None;

    try:
        import itertools;

        sql_stmt = """
            SELECT inqueue
            FROM fn_queue_info
            WHERE asset_id IN ('%s')
        """;

        dbcur.execute(sql_stmt % showid);

        match = dbcur.fetchall();
        
        if match is not None:
            return True if int(match[0][0]) > 0 else False;

        else:
            return None;


    except Exception as inst:
        #logger.error(inst);
        pass;

        return None;


def fetchshowstatus(showid):

    try:

        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

    except:
        return None;

    try:

        import itertools;
        from resources.lib.modules import trakt;


        if trakt.getTraktCredentialsInfo():

            sql_stmt = """
                SELECT asset_id
                    ,CASE
                        WHEN trakt_watched IS NOT NULL
                        THEN trakt_watched
                        WHEN fn_watched IS NOT NULL
                        THEN fn_watched
                        ELSE 0
                    END AS 'watched'
                    ,CASE
                        WHEN trakt_progress IS NOT NULL
                        THEN trakt_progress
                        WHEN fn_progress IS NOT NULL
                        THEN fn_progress
                        ELSE 0
                    END AS 'progress'
                FROM fn_episode_info
                WHERE show_id IN ('%s')
            """;

        else:

            sql_stmt = """
                SELECT asset_id
                    ,CASE
                        WHEN fn_watched IS NOT NULL
                        THEN fn_watched
                        ELSE 0
                    END AS 'watched'
                    ,CASE
                        WHEN fn_progress IS NOT NULL
                        THEN fn_progress
                        ELSE 0
                    END AS 'progress'
                FROM fn_episode_info
                WHERE show_id IN ('%s')
            """;

        dbcur.execute(sql_stmt % showid);

        desc = dbcur.description;
        column_names = [col[0] for col in desc];

        #statusmeta = {row[0]:dict(itertools.izip(column_names, row)) for row in dbcur};
        statusmeta = dict((row[0], dict(itertools.izip(column_names, row))) for row in dbcur)

        return statusmeta;

    except Exception as inst:
        #logger.error(inst);

        return None;


def fetchepisodes(shows, assets):

    try:

        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

    except:
        return None;

    try:
        import itertools;


        sql_stmt = """
            SELECT tei.*
                ,tsi.genre
                ,tsi.network
                ,tsi.siteRating
                ,tsi.siteRatingCount
                ,tsi.images
            FROM tvdb_episode_info tei
            LEFT JOIN tvdb_series_info tsi ON tsi.tvdbid = tei.tvdbid
            WHERE tei.show_id IN %s
            AND tei.episode_id IN %s
        """;

        if len(assets) == 1:
            assets = list(assets);
            assets.append('');

        if len(shows) == 1:
            shows = list(shows);
            shows.append('');

        #logger.error(sql_stmt % (repr(tuple(map(str, shows))), repr(tuple(map(str, assets)))))

        dbcur.execute(sql_stmt % (repr(tuple(map(str, shows))), repr(tuple(map(str, assets)))));

        desc = dbcur.description;
        column_names = [col[0] for col in desc];

        #episodemeta = {row[1]:dict(itertools.izip(column_names, row)) for row in dbcur};
        episodemeta = dict((row[1], dict(itertools.izip(column_names, row))) for row in dbcur)
        
        return episodemeta;


    except Exception as inst:
        #logger.error(inst);

        return None;


def inserttvdbtoken(token, edate, rdate):
    
    logger.debug('Attempting to update tvdbtoken DB.');
    
    try:

        logger.debug('Validating DB file exists.');

        control.makeFile(control.dataPath);

        dbcon = database.connect(control.synchFile);
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


def insertfnmetacheck(showid, rdate):

    try:

        control.makeFile(control.dataPath);
        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

        dbcur.execute("CREATE TABLE IF NOT EXISTS fn_meta_check (""show_id TEXT, ""lastupdated TEXT, ""UNIQUE(show_id)"");")

        try:

            try: 
                dbcur.execute("DELETE FROM fn_meta_check WHERE show_id = %s" % showid);

            except Exception as inst:
                #logger.error(inst);

                pass;

            dbcur.execute("INSERT INTO fn_meta_check Values (?, ?)", (showid, rdate));

        except Exception as inst:
            #logger.error(inst);

            pass;

        dbcon.commit();

    except:
        return;


def fetchfnmetacheck(showid):

    try:

        control.makeFile(control.dataPath);
        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

        dbcur.execute("CREATE TABLE IF NOT EXISTS fn_meta_check (""show_id TEXT, ""lastupdated TEXT, ""UNIQUE(show_id)"");");

    except Exception as inst:
        #logger.error(inst);
        return None;

    try:

        sql_stmt = """
            SELECT lastupdated
            FROM fn_meta_check
            WHERE show_id = %s
        """;

        dbcur.execute(sql_stmt % showid);

        match = dbcur.fetchall();
        
        if match is not None:
            logger.error(match);
            return match[0][0];

        else:
            return None;


    except Exception as inst:
        #logger.error(inst);

        return None;


def insertfnhistorycheck(showid, rdate):

    try:

        control.makeFile(control.dataPath);
        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

        dbcur.execute("CREATE TABLE IF NOT EXISTS fn_history_check (""show_id TEXT, ""lastupdated TEXT, ""UNIQUE(show_id)"");")

        try:

            try: 
                dbcur.execute("DELETE FROM fn_history_check WHERE show_id = %s" % showid);

            except Exception as inst:
                #logger.error(inst);

                pass;

            dbcur.execute("INSERT INTO fn_history_check Values (?, ?)", (showid, rdate));

        except Exception as inst:
            #logger.error(inst);

            pass;

        dbcon.commit();

    except:
        return;


def fetchfnhistorycheck(showid):

    try:

        control.makeFile(control.dataPath);
        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

        dbcur.execute("CREATE TABLE IF NOT EXISTS fn_history_check (""show_id TEXT, ""lastupdated TEXT, ""UNIQUE(show_id)"");");

    except Exception as inst:
        #logger.error(inst);
        return None;

    try:

        sql_stmt = """
            SELECT lastupdated
            FROM fn_history_check
            WHERE show_id = %s
        """;

        dbcur.execute(sql_stmt % showid);

        match = dbcur.fetchall();
        
        if match is not None:
            logger.error(match);
            return match[0][0];

        else:
            return None;


    except Exception as inst:
        #logger.error(inst);

        return None;


def inserttraktwatchedcheck(showid, rdate):

    try:

        control.makeFile(control.dataPath);
        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

        dbcur.execute("CREATE TABLE IF NOT EXISTS trakt_watched_check (""show_id TEXT, ""lastupdated TEXT, ""UNIQUE(show_id)"");")

        try:

            try: 
                dbcur.execute("DELETE FROM trakt_watched_check WHERE show_id = %s" % showid);

            except Exception as inst:
                #logger.error(inst);

                pass;

            dbcur.execute("INSERT INTO trakt_watched_check Values (?, ?)", (showid, rdate));

        except Exception as inst:
            #logger.error(inst);

            pass;

        dbcon.commit();

    except:
        return;


def fetchtraktwatchedcheck(showid):

    try:

        control.makeFile(control.dataPath);
        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

        dbcur.execute("CREATE TABLE IF NOT EXISTS trakt_watched_check (""show_id TEXT, ""lastupdated TEXT, ""UNIQUE(show_id)"");");

    except Exception as inst:
        #logger.error(inst);
        return None;

    try:

        sql_stmt = """
            SELECT lastupdated
            FROM trakt_watched_check
            WHERE show_id = %s
        """;

        dbcur.execute(sql_stmt % showid);

        match = dbcur.fetchall();
        
        if match is not None:
            return match[0][0];

        else:
            return None;


    except Exception as inst:
        #logger.error(inst);

        return None;


def inserttvdbseries(meta):

    try:

        control.makeFile(control.dataPath);
        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

        dbcur.execute("CREATE TABLE IF NOT EXISTS tvdb_series_info (""show_id TEXT, ""tvdbid TEXT, ""imdbid TEXT, ""seriesid TEXT, ""traktid TEXT, ""lastUpdated TEXT, ""seriesName TEXT, ""status TEXT, ""firstAired TEXT, ""firstEpisode TEXT, ""genre TEXT, ""network TEXT, ""siteRating TEXT, ""siteRatingCount TEXT, ""images TEXT, ""UNIQUE(show_id, tvdbid)"");")

        try:

            try: 
                dbcur.execute("DELETE FROM tvdb_series_info WHERE (show_id = '%s' and tvdbid = '%s')" % (meta['show_id'], meta['tvdbid']));

            except Exception as inst:
                #logger.error(inst);

                pass;

            dbcur.execute("INSERT INTO tvdb_series_info Values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (meta['show_id'], meta['tvdbid'], meta['imdbid'], meta['seriesid'], meta['traktid'], meta['lastUpdated'], meta['seriesName'], meta['status'], meta['firstAired'], meta['firstEpisode'], meta['genre'], meta['network'], meta['siteRating'], meta['siteRatingCount'], meta['images']));

            #dbcur.execute("INSERT INTO tvdb_series_info Values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", meta.values()); #We like this idea but the values seem to have random placement due to restrictions on the dictionary

        except Exception as inst:
            #logger.error(inst);

            pass;

        dbcon.commit();

    except:
        return;


def inserttvdbepisodes(meta):

    try:

        control.makeFile(control.dataPath);
        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

        dbcur.execute("CREATE TABLE IF NOT EXISTS tvdb_episode_info (""show_id TEXT, ""episode_id TEXT, ""tvdbid TEXT, ""tvdbeid TEXT, ""overview TEXT, ""description TEXT, ""absoluteNumber TEXT, ""airedSeason TEXT, ""airedEpisodeNumber TEXT, ""firstAired TEXT, ""tvdbtitle TEXT, ""sorttitle TEXT, ""url TEXT, ""videotype TEXT, ""warched TEXT, ""progress TEXT, ""UNIQUE(show_id, episode_id, tvdbid, tvdbeid)"");");


        try: 

            dbcur.execute("DELETE FROM tvdb_episode_info WHERE (show_id = '%s' and tvdbid = '%s')" % (meta[0]['show_id'], meta[0]['tvdbid']));

        except Exception as inst:
            #logger.error(inst);

            pass;


        for m in meta:

            try:

                dbcur.execute("INSERT INTO tvdb_episode_info Values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (m['show_id'], m['episode_id'], m['tvdbid'], m['tvdbeid'], m['overview'], m['description'], m['absoluteNumber'], m['airedSeason'], m['airedEpisodeNumber'], m['firstAired'], m['episodeName'], m['sorttitle'], m['url'], m['videotype'], m['watched'], m['progress']));

            except Exception as inst:
                #logger.error(inst);

                pass;

        dbcon.commit();

    except:
        return;


def updatefnqueue(meta, queuestate=0):

    try:

        control.makeFile(control.dataPath);
        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

        dbcur.execute("CREATE TABLE IF NOT EXISTS fn_queue_info (""asset_id TEXT, ""inqueue TEXT, ""UNIQUE(asset_id)"");");

        for m in meta:

            try:

                dbcur.execute("INSERT OR IGNORE INTO fn_queue_info (asset_id, inqueue) VALUES ('%s', %s)" % (m['asset_id'], queuestate));
                dbcur.execute("UPDATE fn_queue_info SET inqueue = %s WHERE asset_id = %s" % (queuestate, m['asset_id']));

            except Exception as inst:
                #logger.error(inst);

                pass;

        dbcon.commit();

    except Exception as inst:
        #logger.error(inst);

        return None;


def addremovefnqueue(meta):

    try:

        control.makeFile(control.dataPath);
        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

        dbcur.execute("CREATE TABLE IF NOT EXISTS fn_queue_info (""asset_id TEXT, ""inqueue TEXT, ""UNIQUE(asset_id)"");");


        try:

            #RunPlugin(%s?action=updatemyqueue&asset_id=%s&series_name=%s&state=0

            dbcur.execute("INSERT OR IGNORE INTO fn_queue_info (asset_id, inqueue) VALUES ('%s', %s)" % (meta['asset_id'], meta['state']));
            dbcur.execute("UPDATE fn_queue_info SET inqueue = %s WHERE asset_id = %s" % (meta['state'], meta['asset_id']));

        except Exception as inst:
            #logger.error(inst);

            pass;

        dbcon.commit();

        if int(meta['state']) > 0:
            return (True, "%s added to your anime queue successfully!" % meta['series_name']);

        else:
            return (True, "%s removed from your anime queue successfully!" % meta['series_name']);

    except Exception as inst:
        #logger.error(inst);

        if int(meta['state']) > 0:
            return (False, "There was an error adding %s to your anime queue." % meta['series_name']);

        else:
            return (False, "There was an error removing %s from your anime queue." % meta['series_name']);


def insertfnepisodes(meta, itype):

    try:

        control.makeFile(control.dataPath);
        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

        dbcur.execute("CREATE TABLE IF NOT EXISTS fn_episode_info (""show_id TEXT, ""asset_id TEXT, ""video_type TEXT, ""fn_progress TEXT, ""fn_watched TEXT, ""fn_show_name TEXT, ""trakt_slug TEXT, ""trakt_series_id TEXT, ""trakt_episode_id TEXT, ""trakt_progress TEXT, ""trakt_watched TEXT, ""UNIQUE(show_id, asset_id)"");");
        dbcur.execute("CREATE TABLE IF NOT EXISTS trakt_progress_info (""trakt_series_id TEXT, ""trakt_episode_id TEXT, ""tvdbid TEXT, ""tvdbeid TEXT, ""season TEXT, ""episode TEXT, ""trakt_progress TEXT, ""lastupdated TEXT, ""UNIQUE(trakt_series_id, trakt_episode_id, tvdbid, tvdbeid)"");");

        for m in meta:

            try:

                if itype == 'series':

                    #dbcur.execute("INSERT OR REPLACE INTO fn_episode_info (show_id, asset_id, video_type) VALUES", (m['show_id'], m['asset_id'], m['video_type']));
                    dbcur.execute("INSERT OR IGNORE INTO fn_episode_info (show_id, asset_id, video_type, fn_progress, fn_watched, fn_show_name) VALUES ('%s', '%s', '%s', 0, 0, '%s')" % (m['show_id'], m['asset_id'], m['video_type'], m['show_name']));

                    #INSERT OR IGNORE INTO book(id) VALUES(1001);
                    #UPDATE book SET name = 'Programming' WHERE id = 1001;

                elif itype == 'history':

                    dbcur.execute("UPDATE fn_episode_info SET fn_progress = %s, fn_watched = %s WHERE show_id = %s AND asset_id = %s" % (m['checkpoint'], m['watched'], m['show_id'], m['asset_id']));


                elif itype == 'trakt':

                    sql_stmt = """
                        WITH TMP_TBL AS (
                            SELECT trakt_episode_id
                                ,trakt_progress
                            FROM trakt_progress_info
                            WHERE trakt_series_id = %s
                                AND tvdbid = %s
                                AND tvdbeid = (
                                SELECT tvdbeid
                                    FROM tvdb_episode_info
                                    WHERE show_id = %s
                                    AND airedSeason = %s
                                    AND airedEpisodeNumber = %s
                                    AND tvdbid = %s
                                )
                        )
                        UPDATE fn_episode_info
                        SET trakt_slug = '%s'
                            ,trakt_series_id = %s
                            ,trakt_watched = %s 
                            ,trakt_episode_id = (
                                SELECT trakt_episode_id
                                FROM TMP_TBL
                            )
                            ,trakt_progress = (
                                SELECT trakt_progress
                                FROM TMP_TBL
                            )
                        WHERE asset_id = (
                            SELECT episode_id
                            FROM tvdb_episode_info
                            WHERE show_id = %s
                            AND airedSeason = %s
                            AND airedEpisodeNumber = %s
                            AND tvdbid = %s
                        ) 
                    """;

                    #logger.error(sql_stmt % (m['trakt_slug'], m['trakt_season_id'], m['completed'], m['show_id'], m['season_number'], m['number']))

                    sql_stmt = (sql_stmt % (m['trakt_series_id'], m['tvdbid'], m['show_id'], m['season_number'], m['number'], m['tvdbid'], m['trakt_slug'], m['trakt_series_id'], m['completed'], m['show_id'], m['season_number'], m['number'], m['tvdbid']));

                    dbcur.execute(sql_stmt);


                elif itype == 'player':

                    dbcur.execute("INSERT OR IGNORE INTO fn_episode_info (show_id, asset_id) VALUES ('%s', '%s')" % (m['show_id'], m['asset_id']));

                    sql_stmt = """
                        UPDATE fn_episode_info
                        SET show_id = '%s'
                            ,asset_id = '%s'
                            ,video_type = '%s'
                            ,fn_progress = '%s'
                            ,fn_watched = %s
                            ,trakt_progress = '%s'
                            ,trakt_watched = '%s'
                        WHERE show_id = %s
                        AND asset_id = %s
                    """;


                    dbcur.execute(sql_stmt % (m['show_id'], m['asset_id'], m['video_type'], m['fn_progress'], m['fn_watched'], m['trakt_progress'], m['trakt_watched'], m['show_id'], m['asset_id']));


                '''elif itype == 'progress':
                    dbcur.execute("INSERT OR REPLACE INTO fn_episode_info (show_id, asset_id, video_type) VALUES", (m['show_id'], m['asset_id'], m['video_type']));'''

            except Exception as inst:
                #logger.error(inst);

                pass;

        dbcon.commit();

        #we probably want to add some user notification for failures

    except Exception as inst:
        #logger.error(inst);

        return None;


def synctraktprogress(meta, rdate):

    try:

        control.makeFile(control.dataPath);
        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

        dbcur.execute("CREATE TABLE IF NOT EXISTS trakt_progress_info (""trakt_series_id TEXT, ""trakt_episode_id TEXT, ""tvdbid TEXT, ""tvdbeid TEXT, ""season TEXT, ""episode TEXT, ""trakt_progress TEXT, ""lastupdated TEXT, ""UNIQUE(trakt_series_id, trakt_episode_id, tvdbid, tvdbeid)"");");

        try: 

            dbcur.execute("DELETE FROM trakt_progress_info");

        except Exception as inst:
            #logger.error(inst);

            pass;

        for m in meta:

            try:

                dbcur.execute("INSERT INTO trakt_progress_info Values (?, ?, ?, ?, ?, ?, ?, ?)", (m['show']['ids']['trakt'], m['episode']['ids']['trakt'], m['show']['ids']['tvdb'], m['episode']['ids']['tvdb'], m['episode']['season'], m['episode']['number'], m['progress'], rdate));

            except Exception as inst:
                #logger.error(inst);

                pass;

        dbcon.commit();

    except Exception as inst:
        #logger.error(inst);

        return None;


def fetchtraktprogresslastupdated():

    try:

        control.makeFile(control.dataPath);
        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

        dbcur.execute("CREATE TABLE IF NOT EXISTS trakt_progress_info (""trakt_series_id TEXT, ""trakt_episode_id TEXT, ""tvdbid TEXT, ""tvdbeid TEXT, ""season TEXT, ""episode TEXT, ""trakt_progress TEXT, ""lastupdated TEXT, ""UNIQUE(trakt_series_id, trakt_episode_id, tvdbid, tvdbeid)"");");

    except:
        return None;

    try:

        sql_stmt = """
            SELECT lastupdated
            FROM trakt_progress_info
        """;

        dbcur.execute(sql_stmt);

        match = dbcur.fetchall();
        
        if match is not None:
            return match[0][0];

        else:
            return None;


    except Exception as inst:
        #logger.error(inst);

        return None;


def fetchtraktupdateinfo(show_id, asset_id):

    try:

        control.makeFile(control.dataPath);
        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

        dbcur.execute("CREATE TABLE IF NOT EXISTS tvdb_episode_info (""show_id TEXT, ""episode_id TEXT, ""tvdbid TEXT, ""tvdbeid TEXT, ""overview TEXT, ""description TEXT, ""absoluteNumber TEXT, ""airedSeason TEXT, ""airedEpisodeNumber TEXT, ""firstAired TEXT, ""tvdbtitle TEXT, ""sorttitle TEXT, ""url TEXT, ""videotype TEXT, ""warched TEXT, ""progress TEXT, ""UNIQUE(show_id, episode_id, tvdbid, tvdbeid)"");");

    except Exception as inst:
        #logger.error(inst);
        return None;

    try:

        sql_stmt = """
            SELECT tvdbid
               ,airedSeason
               ,airedEpisodeNumber
            FROM tvdb_episode_info
            WHERE show_id = %s
            AND episode_id = %s
        """;

        dbcur.execute(sql_stmt % (show_id, asset_id));

        match = dbcur.fetchall();
        
        if match is not None:
            return match[0];

        else:
            return None;


    except Exception as inst:
        #logger.error(inst);

        return None;


def fetchtraktprogressinfo(show_id, asset_id):

    try:

        control.makeFile(control.dataPath);
        dbcon = database.connect(control.synchFile);
        dbcur = dbcon.cursor();

        dbcur.execute("CREATE TABLE IF NOT EXISTS tvdb_episode_info (""show_id TEXT, ""episode_id TEXT, ""tvdbid TEXT, ""tvdbeid TEXT, ""overview TEXT, ""description TEXT, ""absoluteNumber TEXT, ""airedSeason TEXT, ""airedEpisodeNumber TEXT, ""firstAired TEXT, ""tvdbtitle TEXT, ""sorttitle TEXT, ""url TEXT, ""videotype TEXT, ""warched TEXT, ""progress TEXT, ""UNIQUE(show_id, episode_id, tvdbid, tvdbeid)"");");
        dbcur.execute("CREATE TABLE IF NOT EXISTS tvdb_series_info (""show_id TEXT, ""tvdbid TEXT, ""imdbid TEXT, ""seriesid TEXT, ""traktid TEXT, ""lastUpdated TEXT, ""seriesName TEXT, ""status TEXT, ""firstAired TEXT, ""firstEpisode TEXT, ""genre TEXT, ""network TEXT, ""siteRating TEXT, ""siteRatingCount TEXT, ""images TEXT, ""UNIQUE(show_id, tvdbid)"");");

    except Exception as inst:
        #logger.error(inst);
        return None;

    try:

        sql_stmt = """
            SELECT tsi.seriesName
               ,tei.airedSeason
               ,tei.airedEpisodeNumber
            FROM tvdb_episode_info tei
            LEFT JOIN tvdb_series_info tsi ON tsi.tvdbid = tei.tvdbid
            WHERE tei.show_id = %s
            AND tei.episode_id = %s
        """;

        dbcur.execute(sql_stmt % (show_id, asset_id));

        match = dbcur.fetchall();
        
        if match is not None:
            return match[0];

        else:
            return None;


    except Exception as inst:
        #logger.error(inst);

        return None;

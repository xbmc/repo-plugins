#!/usr/bin/python
# -*- coding: utf8 -*-

""" 
Database abstraction layer for Sqlite and MySql
Copyright (C) 2012 Xycl

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

ATTENTION:
Needs the following entries in addon.xml
  <requires>
    .......
    <import addon="script.module.myconnpy" version="0.3.2"/>
  </requires>

Usage:
-----------------------------------------------------------------------------------
Get a database class :

db = DBFactory('mysql', db_name, db_user, db_pass, db_address='127.0.0.1', port=3306)
or
db = DBFactory('sqlite', db_name)

1) The database class automatically connects to the DB within __init__()
2) Supported methods:
a) connect() and disconnect(). That means you can disconnect and later reconnect using connect() method as long as the DB class instance exists.
b) cursor(). Creates a cursor object and returns it.
c) commit()
-----------------------------------------------------------------------------------
Get a Cursor
cursor = db.cursor()

Supported methods:
1) close() which closes the cursor.
2) execute(statement, bind_variables). To use bind variables use the ? as placeholder. Example: "select * from table where column = ?".
3) fetchone(). Fetches one row. Return None in case of end of fetch.
4) fetchall(). Fetches all rows.
5) request(). Does an execute() and fetchall() with the possiblity to use bind variables.



Example

db_type  = 'mysql' if common.getaddon_setting('mysql')=='true' else 'sqlite'
db_name  = 'Pictures.db' if len(common.getaddon_setting('db_name')) == 0 else common.getaddon_setting('db_name')
if db_type == 'sqlite':
    db_user    = ''
    db_pass    = ''
    db_address = ''
    db_port    = ''
else:
    db_user    = common.getaddon_setting('db_user')
    db_pass    = common.getaddon_setting('db_pass')
    db_address = common.getaddon_setting('db_address')
    db_port    = common.getaddon_setting('db_port')

"""


import xbmc
import common

database=''

def DBFactory(backend, db_name, *args):
    global database
    
    backends = {'mysql':MysqlConnection, 'sqlite':SqliteConnection}

    if backend.lower() == 'mysql':

        import mysql.connector as database
            
    # default is to use Sqlite
    else:
        backend = 'sqlite'
        try:
            from sqlite3 import dbapi2 as database
        except:
            from pysqlite2 import dbapi2 as database        
                
    return backends[backend.lower()](db_name, *args)
    


class BaseConnection(object):

    def connect(self):
        raise NotImplementedError( "Database:connect() not implemented" )


    def cursor(self):        
        raise NotImplementedError( "Database:cursor() not implemented" )


    def disconnect(self):
        self.connection.close()


    def commit(self):
        self.connection.commit()



class MysqlConnection(BaseConnection):

    def __init__(self, *args):
        self.connect(*args)

    
    def connect( self, db_name, db_user, db_pass, db_address='127.0.0.1', db_port=3306):
        self.db_name  = db_name
        self.db_user = db_user
        self.db_pass = db_pass
        if db_port != 3306: 
            self.db_address = '%s:%s' %(db_address,db_port)
        else:
            self.db_address = db_address

        self.connection = database.connect(db = db_name, user = db_user, passwd = db_pass, host = db_address) #, port = db_port)
        self.connection.set_charset('utf8')
        self.connection.set_unicode(True)


    def cursor(self):        
        return MysqlCursor(self.connection.cursor(), self.connection)

        
    def get_ddl_primary_key(self):
        return " auto_increment not null primary key "
        
        
    def get_ddl_varchar(self, length):
        return " varchar(%d) "%length
        
        
    def get_backend(self):
        return "mysql"



class SqliteConnection(BaseConnection):

    def __init__(self, *args):
        self.connect(*args)


    def connect(self, db_name, *args):
        self.db_name = db_name
        self.connection = database.connect(db_name)
        self.connection.text_factory = unicode


    def cursor(self):        
        return SqliteCursor(self.connection.cursor(), self.connection)


    def get_ddl_primary_key(self):
        return " primary key not null "


    def get_ddl_varchar(self, length):
        return " text "
        
    def get_backend(self):
        return "sqlite"



class BaseCursor(object):

    def __init__(self, cursor, connection):
        self.cursor = cursor
        self.connection = connection


    def close(self):
        self.cursor.close()


    def execute(self, sql, bindvariables=[]):
        if bindvariables and isinstance(self, MysqlCursor) == True:
            sql = sql.replace('?', '%s')
        if bindvariables :
            self.cursor.execute(sql, bindvariables)
        else:
            self.cursor.execute(sql)


    def fetchone(self):
        row_object = self.cursor.fetchone()
        if row_object is not None:
            return [column for column in row_object]
        else:
            return None


    def fetchall(self):
        rows = []
        
        #return [row for row in self.cursor.fetchall()]
        for row in self.cursor.fetchall():
            cols = []
            for col in row:

                if isinstance(col, basestring):
                    col = common.smart_unicode(col)
                    #print col
                #else:
                #    print type(col)
                #    print col
                    
                cols.append(col)
                
            rows.append(cols)
            
        return rows

    def request_with_binds(self, statement, bindvariables = []):
    
        return self.request(statement, bindvariables)


    def request(self, statement, bindvariables = []):

        binds = []
        return_value= []
        try:
            try:
                if bindvariables > 0:
                    for value in bindvariables:
                        if type(value).__name__ == 'str':
                            binds.append(common.smart_unicode(value))
                        else:
                            binds.append(value)
                    self.execute( statement, binds )
                    try:
                        return_value = self.fetchall()
                    except:
                        pass


                else:
                    self.execute( statement, binds )
                    try:
                        return_value = self.fetchall()
                    except:
                        pass
                self.connection.commit()
            except Exception,msg:
                try:
                    common.log("Database abstraction layer",  "The request failed :", xbmc.LOGERROR )
                    common.log("Database abstraction layer",  "%s - %s"%(Exception,str(msg)), xbmc.LOGERROR )
                except:
                    pass
                try:
                    common.log("Database abstraction layer",  "SQL > %s"%statement, xbmc.LOGERROR)
                except:
                    pass
                try:
                    i = 1
                    for var in binds:
                        common.log ("SQL request numvar = %d  content = %s"%(i,var), xbmc.LOGERROR)
                        i=i+1
                except:
                    pass
        except Exception,msg:
            try:
                common.log("Database abstraction layer",  "The request failed :", xbmc.LOGERROR )
                common.log("Database abstraction layer",  "%s - %s"%(Exception,msg), xbmc.LOGERROR )
            except:
                pass

        return return_value



class MysqlCursor(BaseCursor):
    pass



class SqliteCursor(BaseCursor):
    pass


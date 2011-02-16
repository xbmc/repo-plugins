import os,sys,time
import urllib,urllib2,re
import xbmc,xbmcplugin,xbmcgui,xbmcaddon
from pysqlite2 import dbapi2 as sqlite
import common
__settings__ = xbmcaddon.Addon(id='plugin.audio.hvsc')
set_bcdialogs = __settings__.getSetting( "bcdialogs" )

if not sys.argv[1]=="":
	dbfilename = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.audio.hvsc/db/', 'database.db'  ))
	
	if sys.argv[1]=="add":
		dbcon = sqlite.connect(dbfilename)
		dbcursor = dbcon.cursor()
		query = 'SELECT * FROM siddb where filename="' + sys.argv[2] + '"'
		dbcursor.execute(query)
		row = dbcursor.fetchone()
		id = row[0]
		query = 'UPDATE siddb SET fav=1 WHERE (id=\'' + str(id) + '\')'
		dbcursor.execute(query)
		dbcon.commit()
		
		if set_bcdialogs=="true":
			dialog = xbmcgui.Dialog()
			dia_title = common.get_lstring(50033)
			dia_l1 = common.get_lstring(51000)
			ok = dialog.ok(dia_title, dia_l1)	
			
	
	if sys.argv[1]=="rem":
		dbcon = sqlite.connect(dbfilename)
		dbcursor = dbcon.cursor()
		query = 'SELECT * FROM siddb where filename="' + sys.argv[2] + '"'
		dbcursor.execute(query)
		row = dbcursor.fetchone()
		id = row[0]
		query = 'UPDATE siddb SET fav=0 WHERE (id=\'' + str(id) + '\')'
		dbcursor.execute(query)
		dbcon.commit()
		
		if set_bcdialogs=="true":
			dialog = xbmcgui.Dialog()
			dia_title = common.get_lstring(50033)
			dia_l1 = common.get_lstring(51001)
			ok = dialog.ok(dia_title, dia_l1)	
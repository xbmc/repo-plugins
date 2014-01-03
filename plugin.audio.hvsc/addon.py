#HVSC by Insayne

# Static Libraries
import os,sys,time
import urllib,urllib2,re
import xbmc,xbmcplugin,xbmcgui,xbmcaddon
#from pysqlite2 import dbapi2 as sqlite

#from sqlite import dbapi2 as sqlite

try: import sqlite as sqlite
except: pass
try: import sqlite3 as sqlite
except: pass

import urlparse	# Parameter parsing
import math		# Used for ceil function, page generation
import cgi 		# Used for Parameter Splitting
import string 	# Used for Alphabet Generation

# plugin Constants
__plugin__ = "High Voltage SID Collection"
__author__ = "Insayne (Code) & HannaK (Graphics) & Cptspiff (Contributor)"
__url__ = "https://code.google.com/p/insayne-projects/"
__svn_url__ = "https://insayne-projects.googlecode.com/svn/trunk/XBMC/Audio/plugin.audio.hvsc/"
__version__ = "0.8"
__svn_revision__ = "$Revision$"
__XBMC_Revision__ = xbmc.getInfoLabel('System.BuildVersion')
__settings__ = xbmcaddon.Addon(id='plugin.audio.hvsc')

# Settings 
addonpath = __settings__.getAddonInfo('path')
addonsavepath = __settings__.getAddonInfo('profile')
databasefile =  xbmc.translatePath(addonsavepath + 'db/database.db')


# Here we append the API path
path = xbmc.translatePath(__settings__.getAddonInfo('path'))
api = xbmc.translatePath(os.path.join(path, "hvscAPI"))
sys.path.append(api)

# Custom Libraries
import common		# My common Functions (Makes it more readable for common operations)
import set			# Settings Handler (Makes it more readable)

# Addon Global Variables
dbfilename = databasefile
dbcon = "Unset"
dbcursor = "Unset"
prev_letter = "Unset"

# Settings
set_aplay = __settings__.getSetting( "aplay" )
set_splay = __settings__.getSetting( "splay" )
set_limit = set.get_pagelimit(__settings__.getSetting( "delimit" ))

# Settings : Stream Source
set_stream_source = __settings__.getSetting( "smode" )
if set_stream_source=="0":
	set_source = set.get_source(__settings__.getSetting( "smirror" ))
if set_stream_source=="1":
	set_source = __settings__.getSetting( "sid_path" )

# Settings: Misc
set_pctracking = __settings__.getSetting( "pctracking" )

# Settings: Folder View Toggles	
set_fview_musicians = __settings__.getSetting( "fv_musicians" )
set_fview_demos = __settings__.getSetting( "fv_demos" )
set_fview_games = __settings__.getSetting( "fv_games" )
set_fview_search_file = __settings__.getSetting( "fv_search_file" )
set_fview_search_artist = __settings__.getSetting( "fv_search_artist" )
set_fview_search_title = __settings__.getSetting( "fv_search_title" )

# Settings: Song Length Mode & Custom Interval/Delay
set_slmode = __settings__.getSetting( "sl_mode" )
set_slcustom = set.getsl(__settings__.getSetting( "sl_custom" ))

# Settings: Sort Order, Display Style
set_atsmusicians = set.get_ats(__settings__.getSetting("ats_musicians"))
set_atdmusicians = set.get_atd(__settings__.getSetting("atd_musicians"))
set_atsgames = set.get_ats(__settings__.getSetting("ats_games"))
set_atdgames = set.get_atd(__settings__.getSetting("atd_games"))
set_atsdemos = set.get_ats(__settings__.getSetting("ats_demos"))
set_atddemos = set.get_atd(__settings__.getSetting("atd_demos"))

set_atssearch_file = set.get_ats(__settings__.getSetting("ats_search_file"))
set_atdsearch_file = set.get_atd(__settings__.getSetting("atd_search_file"))
set_atssearch_artist = set.get_ats(__settings__.getSetting("ats_search_artist"))
set_atdsearch_artist = set.get_atd(__settings__.getSetting("atd_search_artist"))
set_atssearch_title = set.get_ats(__settings__.getSetting("ats_search_title"))
set_atdsearch_title = set.get_atd(__settings__.getSetting("atd_search_title"))

# Initializes the Addon
# Checks the Paths and the database :)
def init_addon():
	common.checkpaths()
	global set_source
	global set_stream_source
	common.verify_local()
	common.check_database()
	# Clean Temp Directory
	pathtemp = xbmc.translatePath(addonsavepath + 'temp/')
	files = os.listdir(pathtemp)
	for file in files:
		delfile = xbmc.translatePath(os.path.join(pathtemp, file))
		os.unlink(delfile)

		
		

# Generates the main Index (Root Directory)

def Generate_Index():
	global set_fview_musicians
	global set_fview_games
	global set_fview_demos
	
	root_path = xbmc.translatePath(__settings__.getAddonInfo('path'))
	img_path = xbmc.translatePath(os.path.join( root_path, 'resources', 'images'))
			
	# Strings 
	
	l_bookmarks = common.get_lstring(50000)
	l_musicians = common.get_lstring(50001)
	l_games = common.get_lstring(50002)
	l_demos = common.get_lstring(50003)
	l_top = common.get_lstring(50004)
	l_search = common.get_lstring(50005)
	l_addonutilities = common.get_lstring(50006)
	
	# Define Images
	
	i_bookmarks = xbmc.translatePath(os.path.join(img_path, "bookmarks.png"))
	i_musicians = xbmc.translatePath(os.path.join(img_path, "musicians.png"))
	i_games = xbmc.translatePath(os.path.join(img_path, "games.png"))
	i_demos = xbmc.translatePath(os.path.join(img_path, "demos.png"))
	i_top = xbmc.translatePath(os.path.join(img_path, "top.png"))
	i_search = xbmc.translatePath(os.path.join(img_path, "search.png"))
	i_addonutilities = xbmc.translatePath(os.path.join(img_path, "utilities.png"))
	i_bonus = xbmc.translatePath(os.path.join(img_path, "bonus.png"))

	
	addDir(l_bookmarks,'getindex.php?&category=FAV' , 10, i_bookmarks)
	addDir(l_musicians,'getindex.php?&category=MUSICIANS&fview=' + set_fview_musicians, 2, i_musicians)
	addDir(l_games,'getindex.php?&category=GAMES&fview=' + set_fview_games , 2, i_games)
	addDir(l_demos,'getindex.php?&category=DEMOS&fview=' + set_fview_demos , 2, i_demos)
	addDir(l_top,'getindex.php?&category=TOP' , 9, i_top)
	addDir(l_search,'getindex.php?&category=SEARCH&fview=1' , 8, i_search)

	easteregg = xbmc.translatePath(os.path.join(addonsavepath , 'easteregg.txt'))
	filecheck = os.path.isfile(easteregg)
	if filecheck==True:
		addDir("Bonus", "plugin://plugin.audio.hvsc/mode=13", 13, i_bonus)

	addDir(l_addonutilities, "none", 11, i_addonutilities)
		

# Short but working addir and addlink :)
def addDir(name,url,mode,iconimage):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
	return ok

def addLink(name,mode,url,iconimage):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
	return ok
	
def addELink(name,url,iconimage):
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultAudio.png", thumbnailImage=iconimage)
	liz.setInfo( type="Audio", infoLabels={ "Title": name } )
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
	return ok

# Add Song:
# This will add a song - obvious, eh?

def add_song(db_filename, db_artist, db_title, db_year, db_comment, sort_letter, db_songlength, total, isfav):

	odb_filename = db_filename
	global set_stream_source
	global set_source
	if set_stream_source=="1":
		rootdir = set_source.replace("\\", "/")
	else:
		rootdir = set_source
	rootdir = rootdir + db_filename
	db_filename = xbmc.translatePath(rootdir)

	
	global set_slmode
	if set_slmode=="0":
		db_songlength = common.get_song_length(db_songlength, 1)
	else:
		global set_slcustom
		db_songlength = set_slcustom

	db_year = str(db_year).replace("?", "0")
	db_year = int(db_year[:4])
	url = db_filename
	
	u = odb_filename
	mode = 7
	name = "1"
	db_filename = odb_filename
	url=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	
	ok=True
	liz=xbmcgui.ListItem(db_filename, iconImage="DefaultAudio.png", thumbnailImage="")
	liz.setInfo( type="Music", infoLabels={ "Duration": db_songlength, "Title": db_artist + " - " + db_title, "Artist": db_artist, "Year": db_year, "Genre": "SID", "TrackNumber": 1, "Comment": "None" } )
	liz.setProperty("IsPlayable","true")
	
	# Context Menu
	global path
	script = xbmc.translatePath(os.path.join( path , 'hvscAPI', 'fav.py'))
	param = odb_filename
	if isfav==1:
		l_remsid = common.get_lstring(50015)
		cm = [(l_remsid, 'XBMC.RunScript(' + script + ', rem , ' + param + ')',)]
	else:
		l_addsid = common.get_lstring(50014)
		cm = [(l_addsid, 'XBMC.RunScript(' + script + ', add , ' + param + ')',)]
	liz.addContextMenuItems(cm)
			
	
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,totalItems=total,isFolder=False)
	return ok
	
# Add Song: Title - Artist Edition
def add_song_ta(db_filename, db_artist, db_title, db_year, db_comment, sort_letter, db_songlength, total, isfav):
	odb_filename = db_filename
	global set_stream_source
	global set_source
	if set_stream_source=="1":
		rootdir = set_source.replace("\\", "/")
	else:
		rootdir = set_source
	rootdir = rootdir + db_filename
	db_filename = xbmc.translatePath(rootdir)
	
	global set_slmode
	if set_slmode=="0":
		db_songlength = common.get_song_length(db_songlength, 1)
	else:
		global set_slcustom
		db_songlength = set_slcustom

	
	db_year = str(db_year).replace("?", "0")
	db_year = int(db_year[:4])
	url = db_filename
	
	u = odb_filename
	mode = 7
	name = "1"
	db_filename = odb_filename
	url=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)	
	
	ok=True
	liz=xbmcgui.ListItem(db_filename, iconImage="DefaultAudio.png", thumbnailImage="")
	liz.setInfo( type="Music", infoLabels={ "Duration": db_songlength, "Title": db_title + " - " + db_artist, "Artist": db_artist, "Year": db_year, "Genre": "SID", "TrackNumber": 1, "Comment": "None" } )
	liz.setProperty("IsPlayable","true")

	# Context Menu
	global path
	script = xbmc.translatePath(os.path.join( path , 'hvscAPI', 'fav.py'))
	param = odb_filename
	if isfav==1:
		cm = [('Remove SID Bookmark', 'XBMC.RunScript(' + script + ', rem , ' + param + ')',)]
	else:
		cm = [('Add SID Bookmark', 'XBMC.RunScript(' + script + ', add , ' + param + ')',)]
	liz.addContextMenuItems(cm)


	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,totalItems=total)
	return ok

# Add Song for Multitrack Titles
def add_song_multi(db_filename,db_filename_ut, db_artist, db_title, db_year, db_comment, sort_letter, total, num, db_songlength, isfav):
	odb_filename = db_filename_ut
	if set_stream_source=="1":
		rootdir = set_source.replace("\\", "/")
	else:
		rootdir = set_source
	rootdir = rootdir + db_filename
	db_filename = xbmc.translatePath(rootdir)

	db_year = str(db_year).replace("?", "0")
	db_year = int(db_year[:4])

	global set_slmode
	if set_slmode=="0":
		db_songlength = common.get_song_length(db_songlength, num)
	else:
		global set_slcustom
		db_songlength = set_slcustom
	
	url = db_filename
	
	u = odb_filename
	mode = 7
	name = str(num)
	db_filename = odb_filename
	url=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)	
	
	ok=True
	liz=xbmcgui.ListItem(db_filename, iconImage="DefaultAudio.png", thumbnailImage="")
	liz.setInfo( type="Music", infoLabels={ "Duration": db_songlength, "Title": str(num) + ". " + db_artist + " - " + db_title, "Artist": db_artist, "Year": db_year, "Genre": "SID", "TrackNumber": num, "Comment": "None" } )
	liz.setProperty("IsPlayable","true")
	
	# Context Menu
	global path
	script = xbmc.translatePath(os.path.join( path , 'hvscAPI', 'fav.py'))
	param = odb_filename
	if isfav==1:
		cm = [('Remove SID Bookmark', 'XBMC.RunScript(' + script + ', rem , ' + param + ')',)]
	else:
		cm = [('Add SID Bookmark', 'XBMC.RunScript(' + script + ', add , ' + param + ')',)]
	liz.addContextMenuItems(cm)

	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,totalItems=total)
	return ok

def update_playcount(filename):
	global dbfilename
	global dbcon 
	global dbcursor
	global prev_letter
	dbcon = sqlite.connect(dbfilename)
	dbcursor = dbcon.cursor()
	
	query = 'SELECT * FROM siddb where filename="' + filename + '"'
	dbcursor.execute(query)
	row = dbcursor.fetchone()
	
	id = row[0]
	count = row[27]
	count = int(count) + 1
	
	query = 'UPDATE siddb SET playcount=\'' + str(count) + '\' WHERE (id=\'' + str(id) + '\')'
	dbcursor.execute(query)
	dbcon.commit()
	


# This blob is for parameter parsing (MODE/URL)

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param

params=get_params()
url=None
name=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

if mode==None or url==None or len(url)<1:
	init_addon()
	Generate_Index()
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

	
# Mode 1:
# This Mode runs the Database Creator - it is called by the tool
elif mode==1:
	global dbcon
	global dbcursor
	global path
	if url=="createdb":
	
		dia_title = common.get_lstring(50016)
		dia_l1 = common.get_lstring(50017)
		dia_l2 = common.get_lstring(50018)
		dialog = xbmcgui.Dialog()
		ret = dialog.yesno(dia_title, dia_l1, dia_l2)
		if ret==1:		
			script = xbmc.translatePath(os.path.join(path, "hvscAPI", "dbcreator.py"))
			xbmc.executebuiltin("XBMC.RunScript(" + script + ")")
		else:
			dialog = xbmcgui.Dialog()
			
			dia_title = common.get_lstring(50016)
			dia_l1 = common.get_lstring(50019)
			ok = dialog.ok(dia_title, dia_l1)	
			
	
	elif url=="res_pc":
	
		dia_title = common.get_lstring(50033)
		dia_l1 = common.get_lstring(50034)
		dialog = xbmcgui.Dialog()
		ret = dialog.yesno(dia_title, dia_l1)
		if ret==1:				
			filename = databasefile
			connection = sqlite.connect(filename)
			cursor = connection.cursor()
			query = "UPDATE siddb SET playcount=0"
			cursor.execute(query)
			connection.commit()
			connection.close()
			
			dialog = xbmcgui.Dialog()
			dia_title = common.get_lstring(50033)
			dia_l1 = common.get_lstring(50036)
			ok = dialog.ok(dia_title, dia_l1)	
		else:
			dialog = xbmcgui.Dialog()
			dia_title = common.get_lstring(50033)
			dia_l1 = common.get_lstring(50037)
			ok = dialog.ok(dia_title, dia_l1)	
	
	
	elif url=="del_books":
		dia_title = common.get_lstring(50033)
		dia_l1 = common.get_lstring(50038)
		dialog = xbmcgui.Dialog()
		ret = dialog.yesno(dia_title, dia_l1)
		if ret==1:		
		
			filename = databasefile
			connection = sqlite.connect(filename)
			cursor = connection.cursor()
			query = "UPDATE siddb SET fav=0"
			cursor.execute(query)
			connection.commit()
			connection.close()
			
			dialog = xbmcgui.Dialog()
			dia_title = common.get_lstring(50033)
			dia_l1 = common.get_lstring(50039)
			ok = dialog.ok(dia_title, dia_l1)	
		else:
			dialog = xbmcgui.Dialog()
			dia_title = common.get_lstring(50033)
			dia_l1 = common.get_lstring(50040)
			ok = dialog.ok(dia_title, dia_l1)	

#Mode 2:
# This mode Generates the Alphanumerical sorting dynamically
elif mode==2:
	# Generate URL Parameters
	url = "http://www.google.com/" + url
	dic = cgi.parse_qs(urlparse.urlparse(url)[4])
	for i in dic.keys():
		dic[i] = "".join(dic[i])
		
	cat = dic["category"]
	fv_view = dic["fview"]

	if fv_view=="0":
		mode = 3
	else:
		mode = 5
	
	# Here we deploy the sorting style
	if cat=="DEMOS":
		global set_atsdemos
		global set_atddemos
		order_song_by = set_atddemos
		order_by = set_atsdemos
	elif cat=="MUSICIANS":
		global set_atsmusicians
		global set_atdmusicians
		order_song_by = set_atdmusicians
		order_by = set_atsmusicians
	elif cat=="GAMES":
		global set_atsgames
		global set_atdgames
		order_song_by = set_atdgames
		order_by = set_atsgames
	elif cat=="SEARCH":
		global set_atssearch
		global set_atdsearch
		order_song_by = set_atdsearch
		order_by = set_atssearch
	else:
		order_song_by = "at"
		order_by = "artist"

	# Set up the base path
	path = xbmc.translatePath(__settings__.getAddonInfo('path'))
	imgf = xbmc.translatePath(os.path.join(path, "resources", "images"))

	# 0-9
	img = xbmc.translatePath(os.path.join(path, "resources", "images", "0-9.png"))
	addDir("0-9",'getindex.php?&category=' + cat + '&letter=num&orderby=' + order_by + '&songorderby=' + order_song_by + '&page=1&limit=' + str(set_limit) , mode , img)
	
	# Alphabet
	for c in string.ascii_uppercase:
		img = xbmc.translatePath(os.path.join(path, "resources", "images", c + ".png"))
		addDir(c,'getindex.php?&category=' + cat + '&letter=' + c + '&orderby=' + order_by + '&songorderby=' + order_song_by + '&page=1&limit=' + str(set_limit) , mode , img)

	# Unknown/Others
	img = xbmc.translatePath(os.path.join(path, "resources", "images", "Unknown.png"))
	addDir("Others",'getindex.php?&category=' + cat + '&letter=misc&orderby=' + order_by + '&songorderby=' + order_song_by + '&page=1&limit=' + str(set_limit) , mode , img)

# Mode 3:
# This mode Lists Artists or Titles as folders
elif mode==3:
	url = "http://www.google.com/" + url
	dic = cgi.parse_qs(urlparse.urlparse(url)[4])
	for i in dic.keys():
		dic[i] = "".join(dic[i])
	
	cat = dic["category"]
	p_limit = dic["limit"]
	p_page = dic["page"]
	letter = dic["letter"]
	orderby = dic["orderby"]
	songorderby = dic["songorderby"]
	
	# Lets generate the page number/count
	global set_limit
	
	if set_limit>0:
		p_nextpage = int(p_page) + 1
		p_query_start = (int(p_page) * int(set_limit)) - int(set_limit)
		p_query_end = int(set_limit)
	else:
		p_nextpage = 0
	

	# Database Connection 
	dbcheck = common.check_database()
	if dbcheck==True:
		global dbfilename
		global dbcon 
		global dbcursor
		global prev_letter
		dbcon = sqlite.connect(dbfilename)
		dbcursor = dbcon.cursor()
		totalc = 0
		t_pages = 0

		# Check the Type of Letter for the query
		if letter=="num":
			sql_like = "GLOB '[0-9]*'"
			
		elif letter=="misc":
			sql_like = "GLOB '[^0-9A-Za-z]*'"
		elif letter=="search":
			searchterm = dic["searchterm"]
			searchcategory = dic["searchcategory"]
			sql_like = "LIKE '%" + searchterm + '%\''
		else:
			sql_like = "LIKE \"" + letter + "%\""
		
		if letter!="search":
			# Query Generation
			if p_limit>0:
				query_count = 'SELECT COUNT(DISTINCT ' + orderby + ') FROM siddb where category="' + cat + '" AND ' + orderby + " " + sql_like
				dbcursor.execute(query_count)
				totalc = dbcursor.fetchone()[0]
				total = int(p_limit) + 1
				query = 'SELECT * FROM siddb WHERE category="' + cat + '" AND ' + orderby + " " + sql_like + ' GROUP BY ' + orderby + ' ORDER BY ' + orderby +  ' COLLATE nocase ASC LIMIT ' + str(p_query_start) + ',' + str(p_query_end)
			else:
				query_count = 'SELECT COUNT(DISTINCT ' + orderby + ') FROM siddb where category="' + cat + '" AND ' + orderby + " " + sql_like
				dbcursor.execute(query_count)
				total = dbcursor.fetchone()[0]
				query = 'SELECT * FROM siddb WHERE category="' + cat + '" AND ' + orderby + " " + sql_like + ' GROUP BY ' + orderby + ' ORDER BY ' + orderby + " COLLATE nocase ASC"
		else:
			if p_limit>0:
				query_count = 'SELECT COUNT(DISTINCT ' + searchcategory + ') FROM siddb where ' + searchcategory + ' ' + sql_like
				dbcursor.execute(query_count)
				totalc = dbcursor.fetchone()[0]
				total = int(p_limit) + 1
				query = 'SELECT * FROM siddb WHERE ' + searchcategory + ' ' + sql_like + ' GROUP BY ' + orderby + ' ORDER BY ' + orderby +  ' COLLATE nocase ASC LIMIT ' + str(p_query_start) + ',' + str(p_query_end)
	
		dbcursor.execute(query)
		for row in dbcursor:
			db_id = row[0]
			db_filename = row[2]
			db_artist = row[8]
			db_title = row[7]

			if letter=="search":
				link = 'index.php?id=' + str(db_id) + '&category=' + str(cat) + '&searchterm=' + searchterm + '&searchcategory=' + searchcategory + '&letter=' + letter + '&orderby=' + str(orderby) + '&songorderby=' + str(songorderby) + '&page=1&limit=' + str(p_limit)
			else:
				link = 'index.php?id=' + str(db_id) + '&category=' + str(cat) + '&letter=' + letter + '&orderby=' + str(orderby) + '&songorderby=' + str(songorderby) + '&page=1&limit=' + str(p_limit)
			
			if songorderby=="at":
				addDir(db_artist.encode("UTF-8") , link , 4, "") 
			else:
				addDir(db_title.encode("UTF-8") , link , 4, "") 
			
		# Next Page Generation
		
		if not totalc==0:
			tpages = float(totalc) / float(set_limit)
			tpages = int(math.ceil(tpages))
			if tpages<p_nextpage:
				p_nextpage = 0
		else:
			tpages = 0
			p_nextpage = 0
		
		if letter=="search":
			next_page_li_url = 'getindex.php?&category=' + cat + '&searchterm=' + searchterm + '&searchcategory=' + searchcategory + '&letter=' + letter + '&orderby=' + str(orderby) + '&songorderby=' + str(songorderby) + '&page=' + str(p_nextpage) + '&limit=' + str(p_limit)
		else:
			next_page_li_url = 'getindex.php?&category=' + cat + '&letter=' + letter + '&orderby=' + str(orderby) + '&songorderby=' + str(songorderby) + '&page=' + str(p_nextpage) + '&limit=' + str(p_limit)
		next_page_li_name = "[" + str(p_page) + "/" + str(tpages) + "] Next  >>"

		# Next Page
		if p_nextpage!=0:
			addDir(next_page_li_name, next_page_li_url ,3, "")	
			
	
# Mode 4
# This mode lists folder view contents
elif mode==4:
	url = "http://www.google.com/" + url
	dic = cgi.parse_qs(urlparse.urlparse(url)[4])
	for i in dic.keys():
		dic[i] = "".join(dic[i])
	
	id = dic["id"]
	cat = dic["category"]
	p_limit = dic["limit"]
	p_page = dic["page"]
	letter = dic["letter"]
	orderby = dic["orderby"]
	songorderby = dic["songorderby"]
	
	# Lets generate the page number/count
	global set_limit
	
	if set_limit>0:
		p_nextpage = int(p_page) + 1
		p_query_start = (int(p_page) * int(set_limit)) - int(set_limit)
		p_query_end = int(set_limit)
	else:
		p_nextpage = 0
	
	dbcheck = common.check_database()
	if dbcheck==True:
		global dbfilename
		global dbcon 
		global dbcursor
		global prev_letter
		dbcon = sqlite.connect(dbfilename)
		dbcursor = dbcon.cursor()
		totalc = 0
		t_pages = 0


		query = 'SELECT * FROM siddb where ID="' + id + '"'
		dbcursor.execute(query)
		row = dbcursor.fetchone()

		# What we search for (Artist or title, depending on ordering)
		if orderby=="title":
			searchterm = row[7]
			
			if cat!="SEARCH":
				query = 'SELECT * FROM siddb where category="' + cat + '" AND title="' + searchterm + '" ORDER BY ' + orderby + ' COLLATE nocase ASC'
				query_count = 'SELECT COUNT(*) FROM siddb where category="' + cat + '" AND title="' + searchterm + '"'
			else:
				title = row[7]
				csearchterm = dic["searchterm"]
				searchterm = dic["searchterm"]
				searchterm = "LIKE '%" + searchterm + "%'"
				searchcategory = dic["searchcategory"]
				query = 'SELECT * FROM siddb WHERE title="' + title + '" AND ' + searchcategory + ' ' + searchterm + ' ORDER BY ' + orderby + ' COLLATE nocase ASC' 
				query_count = 'SELECT COUNT(*) FROM siddb WHERE title="' + title + '" AND ' + searchcategory + ' ' + searchterm
				
	
		elif orderby=="artist":
			searchterm = row[8]
			if cat!="SEARCH":
				query = 'SELECT * FROM siddb where category="' + cat + '" AND artist="' + searchterm + '" ORDER BY ' + orderby + ' COLLATE nocase ASC' 
				query_count = 'SELECT COUNT(*) FROM siddb where category="' + cat + '" AND artist="' + searchterm + '"'
			else:
				artist = row[8]
				csearchterm = dic["searchterm"]
				searchterm = dic["searchterm"]
				searchterm = "LIKE '%" + searchterm + "%'"
				searchcategory = dic["searchcategory"]
				query = 'SELECT * FROM siddb WHERE artist="' + artist + '" AND ' + searchcategory + ' ' + searchterm + ' ORDER BY ' + orderby + ' COLLATE nocase ASC' 
				query_count = 'SELECT COUNT(*) FROM siddb WHERE artist="' + artist + '" AND ' + searchcategory + ' ' + searchterm
		else:
			searchterm = row[8]
			if cat!="SEARCH":
				query = 'SELECT * FROM siddb where category="' + cat + '" AND artist="' + searchterm + '" ORDER BY ' + orderby + ' COLLATE nocase ASC' 
				query_count = 'SELECT COUNT(*) FROM siddb where category="' + cat + '" AND artist="' + searchterm + '"'
			else:
				artist = row[8]
				csearchterm = dic["searchterm"]
				searchterm = dic["searchterm"]
				searchterm = "LIKE '%" + searchterm + "%'"
				searchcategory = dic["searchcategory"]
				query = 'SELECT * FROM siddb WHERE artist="' + artist + '" AND ' + searchcategory + ' ' + searchterm + ' ORDER BY ' + orderby + ' COLLATE nocase ASC' 
				query_count = 'SELECT COUNT(*) FROM siddb WHERE artist="' + artist + '" AND ' + searchcategory + ' ' + searchterm

		
		print "SQL QUERY: " + query.encode("UTF-8")
		print "SQL COUNT QUERY: " + query_count.encode("UTF-8")
		dbcursor.execute(query_count)
		totalc = dbcursor.fetchone()[0]
		if p_limit>0:
			query = query + ' LIMIT ' + str(p_query_start) + ',' + str(p_query_end)
			total = int(p_limit) + 1
			
		# And here comes the actual query
			
		count = 0
		scount = 0
		dbcursor.execute(query)
		for row in dbcursor:
			count += 1
			db_filename = row[2]
			db_artist = row[8]
			db_title = row[7]
			db_releasednum = row[9]
			db_songlength = row[13]
			db_stilentry = row[26]
			db_songs = row[11]
			db_isfav = row[28]
			
			if db_songs <= 1:
				scount += 1
				sort_letter = "None"
				if songorderby=="at":
					add_song(db_filename, db_artist, db_title, db_releasednum, db_stilentry, sort_letter, db_songlength, total, db_isfav)
				elif songorderby=="ta":
					add_song_ta(db_filename, db_artist, db_title, db_releasednum, db_stilentry, sort_letter, db_songlength, total, db_isfav)
				else:
					add_song(db_filename, db_artist, db_title, db_releasednum, db_stilentry, sort_letter, db_songlength, total, db_isfav)
					
			else:
				if songorderby=="at":
					name = db_artist + " - " + db_title
				else:
					name = db_title + " - " + db_artist
				addDir(name.encode("UTF-8") , db_filename , 6, "") 
				
		# Next Page Generation
	
		if not totalc==0:
			tpages = float(totalc) / float(set_limit)
			tpages = int(math.ceil(tpages))
			if tpages<p_nextpage:
				p_nextpage = 0
		else:
			tpages = 0
			p_nextpage = 0
		
		if cat!="SEARCH":
			next_page_li_url = 'getindex.php?&id=' + id + '&category=' + cat + '&letter=' + letter + '&orderby=' + str(orderby) + '&songorderby=' + str(songorderby) + '&page=' + str(p_nextpage) + '&limit=' + str(p_limit)
		else:
			next_page_li_url = 'getindex.php?&id=' + id + '&category=' + cat + '&searchterm=' + csearchterm + '&searchcategory=' + searchcategory + '&letter=' + letter + '&orderby=' + str(orderby) + '&songorderby=' + str(songorderby) + '&page=' + str(p_nextpage) + '&limit=' + str(p_limit)

		next_page_li_name = "[" + str(p_page) + "/" + str(tpages) + "] Next  >>"

		# Next Page
		if p_nextpage!=0:
			addDir(next_page_li_name, next_page_li_url ,4, "")	
			
		global set_splay
		if set_splay=="true":
			if scount==1:	
				if set_stream_source=="1":
					global set_source
					rootdir = set_source.replace("\\", "/")
				else:
					rootdir = set_source
				rootdir = rootdir + db_filename
				media = xbmc.translatePath(rootdir)
				xbmc.executebuiltin("XBMC.PlayMedia(" + media + ")")
			
	

# Mode 5:
# List Folder Contents (Folder View)
elif mode==5:
	url = "http://www.google.com/" + url
	dic = cgi.parse_qs(urlparse.urlparse(url)[4])
	for i in dic.keys():
		dic[i] = "".join(dic[i])
	
	cat = dic["category"]
	p_limit = dic["limit"]
	p_page = dic["page"]
	letter = dic["letter"]
	orderby = dic["orderby"]
	songorderby = dic["songorderby"]
	
	
	# Lets generate the page number/count
	global set_limit
	
	if set_limit>0:
		p_nextpage = int(p_page) + 1
		p_query_start = (int(p_page) * int(set_limit)) - int(set_limit)
		p_query_end = int(set_limit)
	else:
		p_nextpage = 0
	

	# Database Connection 
	dbcheck = common.check_database()
	if dbcheck==True:
		global dbfilename
		global dbcon 
		global dbcursor
		global prev_letter
		dbcon = sqlite.connect(dbfilename)
		dbcursor = dbcon.cursor()
		totalc = 0
		t_pages = 0

		# Check the Type of Letter for the query
		if letter=="num":
			sql_like = "GLOB '[0-9]*'"
			
		elif letter=="misc":
			sql_like = "GLOB '[^0-9A-Za-z]*'"
		elif letter=="search":
			searchterm = dic["searchterm"]
			csearchterm = dic["searchterm"]
			searchcategory = dic["searchcategory"]
			sql_like = "LIKE '%" + searchterm + '%\''
			
		else:
			sql_like = "LIKE \"" + letter + "%\""
		
		# Query Generation
		
		if letter!="search":
			if p_limit>0:
				query_count = 'SELECT COUNT(*) FROM siddb WHERE category="' + cat + '" AND ' + orderby + " " + sql_like
				dbcursor.execute(query_count)
				totalc = dbcursor.fetchone()[0]
				total = int(p_limit) + 1
				query = 'SELECT * FROM siddb WHERE category="' + cat + '" AND ' + orderby + " " + sql_like + ' ORDER BY ' + orderby + ' COLLATE nocase ASC LIMIT ' + str(p_query_start) + ',' + str(p_query_end)
			else:
				query_count = 'SELECT COUNT(*) FROM siddb WHERE category="' + cat + '" AND ' + orderby + " " + sql_like
				dbcursor.execute(query_count)
				total = dbcursor.fetchone()[0]
				query = 'SELECT * FROM siddb WHERE category="' + cat + '" AND ' + orderby + " " + sql_like + ' ORDER BY ' + orderby + ' COLLATE nocase ASC'
			
			next_page_li_url = 'getindex.php?category=' + cat + '&page=' + str(p_nextpage) + '&letter=' + letter + '&orderby=' + orderby + '&songorderby=' + songorderby + '&limit=' + str(p_limit)
		
		else:
			query_count = 'SELECT COUNT(*) FROM siddb WHERE ' + searchcategory + " " + sql_like 
				 
			dbcursor.execute(query_count)
			total = dbcursor.fetchone()[0]
			totalc = total
			query = 'SELECT * FROM siddb WHERE ' + searchcategory + " " + sql_like + ' ORDER BY ' + orderby + ' COLLATE nocase ASC LIMIT ' + str(p_query_start) + ',' + str(p_query_end)
			next_page_li_url = 'getindex.php?category=' + cat + '&searchterm=' + csearchterm + '&searchcategory=' + searchcategory + '&page=' + str(p_nextpage) + '&letter=' + letter + '&orderby=' + orderby + '&songorderby=' + songorderby + '&limit=' + str(p_limit)
		
	
		# Next Page Generation
	
		if not totalc==0:
			tpages = float(totalc) / float(set_limit)
			tpages = int(math.ceil(tpages))
			if tpages<p_nextpage:
				p_nextpage = 0
		else:
			tpages = 0
			p_nextpage = 0
		
		next_page_li_name = "[" + str(p_page) + "/" + str(tpages) + "] Next  >>"
		
		count = 0
		dbcursor.execute(query)

		for row in dbcursor:
			count += 1
			db_filename = row[2]
			db_artist = row[8]
			db_title = row[7]
			db_releasednum = row[9]
			db_songlength = row[13]
			db_stilentry = row[26]
			db_songs = row[11]
			db_isfav = row[28]

	
			if db_songs <= 1:
				sort_letter = "None"
				if songorderby=="at":
					add_song(db_filename, db_artist, db_title, db_releasednum, db_stilentry, sort_letter, db_songlength, total, db_isfav)
				elif songorderby=="ta":
					add_song_ta(db_filename, db_artist, db_title, db_releasednum, db_stilentry, sort_letter, db_songlength, total, db_isfav)
				else:
					add_song(db_filename, db_artist, db_title, db_releasednum, db_stilentry, sort_letter, db_songlength, total, db_isfav)
					
			else:
				if songorderby=="at":
					name = db_artist + " - " + db_title
				else:
					name = db_title + " - " + db_artist
				addDir(name.encode("UTF-8") , db_filename , 6, "") 
	
		# Next Page
		if p_nextpage!=0:
			addDir(next_page_li_name, next_page_li_url ,5, "")	
			
# Mode 6
# Multitrack listing 
elif mode==6:
	# Database Connection 
	dbcheck = common.check_database()
	if dbcheck==True:
		global dbfilename
		global dbcon 
		global dbcursor
		global prev_letter
		dbcon = sqlite.connect(dbfilename)
		dbcursor = dbcon.cursor()
		query = 'SELECT * FROM siddb WHERE filename="' + url + '"'
		dbcursor.execute(query)
		for row in dbcursor:
			rowid = row[0]
			db_category = row[1]
			db_filename = row[2]
			db_format = row[3]
			db_version = row[4]
			db_dataoffset = row[5]
			db_md5 = row[6]
			db_title = row[7]
			db_artist = row[8]
			db_releasednum = row[9]
			db_releasedname = row[10]
			db_songs = row[11]
			db_startsong = row[12]
			db_songlength = row[13]
			db_size = row[14]
			db_initaddr = row[15]
			db_playaddr = row[16]
			db_loadrange = row[17]
			db_speed = row[18]
			db_musplayer = row[19]
			db_playsid_basic = row[20]
			db_clock = row[21]
			db_sidmodel = row[22]
			db_startpage = row[23]
			db_pagelen = row[24]
			db_stil = row[25]
			db_stilentry = row[26]
			db_file_exist = row[27]
			db_isfav = row[28]
			total = db_songs
			count = 0
			for num in range(db_songs):
				count += 1
				sort_letter = "None"
				
				db_filename_ut = db_filename
				
				rootdir = db_filename
				
				db_filename_temp = xbmc.translatePath(rootdir)
				
				db_add = db_filename_temp.split("/")[-1]
				db_add = db_add.replace(".sid", "")
				db_add = db_add + "-" + str(count) + ".sidstream"
				db_file = xbmc.translatePath(db_filename_temp + "/" + db_add)
				
				# Playback File
				if count==1:
					if set_stream_source=="1":
						rootdir = set_source.replace("\\", "/")
					else:
						rootdir = set_source
					rootdir = rootdir + db_file
					media = xbmc.translatePath(rootdir)
				add_song_multi(db_file,db_filename_ut, db_artist, db_title, db_releasednum, db_stilentry, sort_letter, total, count, db_songlength, db_isfav)
		
		global set_aplay
		if set_aplay=="true":
			xbmc.executebuiltin("XBMC.PlayMedia(" + media + ")")
# Mode 7
# Playback mode (currently broken)	
elif mode==7:
	print "MODE 7"
	songnum = int(name)
	
	global set_stream_source
	global set_source
	if set_stream_source=="1":
		rootdir = set_source.replace("\\", "/")
	else:
		rootdir = set_source
	
	if songnum==1:
		rootdir = rootdir + url
		db_filename = xbmc.translatePath(rootdir)
	else:
		db_filename_temp = xbmc.translatePath(url)
		db_add = db_filename_temp.split("/")[-1]
		db_add = db_add.replace(".sid", "")
		db_add = db_add + "-" + str(songnum) + ".sidstream"
		db_file = xbmc.translatePath(rootdir + "/" + url + "/" + db_add)
		db_filename = db_file		
	
	# Play Count Tracking
	global set_pctracking
	if set_pctracking=="true":
		update_playcount(url)

	li=xbmcgui.ListItem(path = db_filename)
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
	

# Mode 8:
# Search Engine
elif mode==8:
	l_title = common.get_lstring(50007)
	kb = xbmc.Keyboard("", l_title, False)
	kb.doModal()
	if (kb.isConfirmed() and len(kb.getText()) >= 1):
		# Here we convert the search term into its native format
		searchterm = kb.getText()
		
		if searchterm =="uuddlrlrba":
		
			easteregg = xbmc.translatePath(os.path.join(addonsavepath , 'easteregg.txt'))
			filecheck = os.path.isfile(easteregg)
			if filecheck==False:
				file = open(easteregg, 'w')
				file.write("You are the best!")
				file.close()

			dialog = xbmcgui.Dialog()
			dia_title = common.get_lstring(55002)
			dia_l1 = common.get_lstring(55003)
			dia_l2 = common.get_lstring(55004)
			ok = dialog.ok(dia_title, dia_l1, dia_l2)	
	
			name = common.get_lstring(55000)
			u = "http://www.insayne.net/xbmc-stuff/hvsc/c64tribute.mp4"
			iconimage = ""
			liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
			liz.setInfo( type="Video", infoLabels={ "Title": name } )
			ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
			addDir(common.get_lstring(55001), "http://remix.kwed.org/?chart=&view=arranger&page=1", 12, "")
		else:
			# Dirty Fix (Im bad, I know)
			fsearchterm = ""
			allowedchars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,_"
			for letter in searchterm:
				if letter in allowedchars:
					fsearchterm = fsearchterm + letter
				else:
					fsearchterm = fsearchterm + "%"
			
			searchterm = fsearchterm
			
			# Generate URL Parameters
			url = "http://www.google.com/" + url
			dic = cgi.parse_qs(urlparse.urlparse(url)[4])
			for i in dic.keys():
				dic[i] = "".join(dic[i])
				
			cat = dic["category"]
			fv_view = dic["fview"]

			global set_fview_search_file
			global set_fview_search_artist
			global set_fview_search_title
			
			if set_fview_search_file=="0":
				file_mode = 3
			else:
				file_mode = 5

			if set_fview_search_artist=="0":
				artist_mode = 3
			else:
				artist_mode = 5

			if set_fview_search_title=="0":
				title_mode = 3
			else:
				title_mode = 5
				
			# Get the Search Ordering/Display
			global set_atssearch_file
			global set_atdsearch_file
			global set_atssearch_artist
			global set_atdsearch_artist
			global set_atssearch_title
			global set_atdsearch_title
			
			l_fn = common.get_lstring(50008)
			l_art = common.get_lstring(50009)
			l_title = common.get_lstring(50010)
			
			# Here we should check first if the user enabled it... but we shall not
			img = ""
			addDir(l_fn,'getindex.php?&category=' + cat + '&letter=search&searchterm=' + searchterm + '&searchcategory=filename&orderby=' + set_atssearch_file + '&songorderby=' + set_atdsearch_file + '&page=1&limit=' + str(set_limit) , file_mode , img)
			addDir(l_art,'getindex.php?&category=' + cat + '&letter=search&searchterm=' + searchterm + '&searchcategory=artist&orderby=' + set_atssearch_artist + '&songorderby=' + set_atdsearch_artist + '&page=1&limit=' + str(set_limit) , artist_mode , img)
			addDir(l_title,'getindex.php?&category=' + cat + '&letter=search&searchterm=' + searchterm + '&searchcategory=title&orderby=' + set_atssearch_title + '&songorderby=' + set_atdsearch_title + '&page=1&limit=' + str(set_limit) , title_mode , img)
	
# TOP
elif mode==9:
	songorderby = "at"
	sort_letter = "None"
	# Database Connection 
	dbcheck = common.check_database()
	if dbcheck==True:
		global dbfilename
		global dbcon 
		global dbcursor
		dbcon = sqlite.connect(dbfilename)
		dbcursor = dbcon.cursor()

		query_count = 'SELECT COUNT(*) FROM siddb WHERE playcount!="0"'
		dbcursor.execute(query_count)
		total = dbcursor.fetchone()[0]
		query = 'SELECT * FROM siddb WHERE playcount!="0" ORDER BY playcount COLLATE nocase DESC LIMIT 0,100'
		
		count = 0
		dbcursor.execute(query)

		for row in dbcursor:
			count += 1
			db_filename = row[2]
			db_artist = row[8]
			db_title = row[7]
			db_releasednum = row[9]
			db_songlength = row[13]
			db_stilentry = "Playcount: " + str(row[27])
			db_songs = row[11]
			db_fav = row[28]
	
			if db_songs <= 1:
				if songorderby=="at":
					add_song(db_filename, db_artist, db_title, db_releasednum, db_stilentry, sort_letter, db_songlength, total, db_fav)
				elif songorderby=="ta":
					add_song_ta(db_filename, db_artist, db_title, db_releasednum, db_stilentry, sort_letter, db_songlength, total, db_fav)
				else:
					add_song(db_filename, db_artist, db_title, db_releasednum, db_stilentry, sort_letter, db_songlength, total, db_fav)
					
			else:
				if songorderby=="at":
					name = db_artist + " - " + db_title
				else:
					name = db_title + " - " + db_artist
				addDir(name.encode("UTF-8") , db_filename , 6, "") 
	

elif mode==10:
	songorderby = "at"
	sort_letter = "None"
	# Database Connection 
	dbcheck = common.check_database()
	if dbcheck==True:
		global dbfilename
		global dbcon 
		global dbcursor
		dbcon = sqlite.connect(dbfilename)
		dbcursor = dbcon.cursor()

		query_count = 'SELECT COUNT(*) FROM siddb WHERE fav="1"'
		dbcursor.execute(query_count)
		total = dbcursor.fetchone()[0]
		query = 'SELECT * FROM siddb WHERE fav="1" ORDER BY artist COLLATE nocase ASC'

		count = 0
		dbcursor.execute(query)

		for row in dbcursor:
			count += 1
			db_filename = row[2]
			db_artist = row[8]
			db_title = row[7]
			db_releasednum = row[9]
			db_songlength = row[13]
			db_stilentry = "Playcount: " + str(row[27])
			db_songs = row[11]
			db_fav = 1
	
			if db_songs <= 1:
				if songorderby=="at":
					add_song(db_filename, db_artist, db_title, db_releasednum, db_stilentry, sort_letter, db_songlength, total, db_fav)
				elif songorderby=="ta":
					add_song_ta(db_filename, db_artist, db_title, db_releasednum, db_stilentry, sort_letter, db_songlength, total, db_fav)
				else:
					add_song(db_filename, db_artist, db_title, db_releasednum, db_stilentry, sort_letter, db_songlength, total, db_fav)
					
			else:
				if songorderby=="at":
					name = db_artist + " - " + db_title
				else:
					name = db_title + " - " + db_artist
				addDir(name.encode("UTF-8") , db_filename , 6, "") 

elif mode==11:
	l_cdb = common.get_lstring(50011)
	l_rpc = common.get_lstring(50012)
	l_dbooks = common.get_lstring(50013)
	addLink(l_cdb, 1, "createdb", "")
	addLink(l_rpc, 1, "res_pc", "")
	addLink(l_dbooks, 1, "del_books", "")
	
elif mode==12:
	dic = cgi.parse_qs(urlparse.urlparse(url)[4])
	for i in dic.keys():
		dic[i] = "".join(dic[i])

	page = int(dic["page"])
	maxpage = 57
	next_page = page + 1
	np_label = "[" + str(page) + "] Next >>"
	np_url = 'http://remix.kwed.org/?chart=&view=arranger&page=' + str(next_page)
	
	req_url = 'http://remix.kwed.org/?chart=&view=arranger&page=' + str(page)
	host = 'http://remix.kwed.org/'
	UAS = "None"

	regex_big = '<tr class=".+?">(.+?)</tr>'	
	regex = '<a title=".+?" href="(.+?)">(.+?)</a>.+?</td>.+?<td>.+?<a href=".+?>(.+?)</a>.+?</td>.+?<td>(.+?)</td>.+?<td class="icons">'

	req = urllib2.Request(req_url)
	req.add_header('User-Agent', UAS)
	response = urllib2.urlopen(req)
	html=response.read()
	response.close()
	html = html.replace("\n", "")
	html = html.replace("\r", "")

	count = 0

	video_files = re.compile(regex_big).findall(html)
	for html in video_files:
		htmlre = re.compile(regex).findall(html)
		for link, title, artist, composer in htmlre:
			count += 1
			name = artist + " - " + title + " (" + common.clean_name(composer) + ")"
			addELink(name, host + link, "")

	if maxpage>next_page:
		addDir(np_label, np_url, 12, "")
	
	
elif mode==13:
	name = common.get_lstring(55000)
	u = "http://www.insayne.net/xbmc-stuff/hvsc/c64tribute.mp4"
	iconimage = ""
	liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
	addDir(common.get_lstring(55001), "http://remix.kwed.org/?chart=&view=arranger&page=1", 12, "")

print "Mode: " + str(mode)
print "URL: " + str(url)

xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.setContent(int(sys.argv[1]), content="music" )
xbmcplugin.endOfDirectory(int(sys.argv[1]))


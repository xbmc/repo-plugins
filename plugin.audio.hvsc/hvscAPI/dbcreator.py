# Static Libraries
import os, sys, urllib, urllib2, re, time
import xbmcplugin,xbmcgui,xbmcaddon
import datetime
import common
import zipfile

try: import sqlite as sqlite
except: pass
try: import sqlite3 as sqlite
except: pass

import csv


# plugin Constants
__plugin__ = "High Voltage SID Collection DB Creator"
__author__ = "Insayne (Code) & HannaK (Graphics) & Cptspiff (Contributor)"
__url__ = ""
__svn_url__ = ""
__version__ = "0.8"
__svn_revision__ = "$Revision$"
__XBMC_Revision__ = xbmc.getInfoLabel('System.BuildVersion')
__settings__ = xbmcaddon.Addon(id='plugin.audio.hvsc')
	
# Settings 
addonpath = __settings__.getAddonInfo('path')
addonsavepath = __settings__.getAddonInfo('profile')
databasefile =  xbmc.translatePath(addonsavepath + 'db/database.db')


# And here we have the magic to parse the CSV File
# As well as to put it into the SQL Lite Database

def dbcreate(csv_db):

	start = time.time()
	
	pDialog = xbmcgui.DialogProgress()
	dia_title = common.get_lstring(50016)
	dia_l1 = common.get_lstring(50020)
	ret = pDialog.create(dia_title, dia_l1)
	
	# Remove old Database
	filecheck = os.path.isfile(databasefile)
	if filecheck==True:
		os.unlink(databasefile)
	
				
	# Define the input list CSV File

	csv_filename = xbmc.translatePath(xbmc.translatePath(csv_db))
	
	# Establish an SQL connection
	connection = sqlite.connect(databasefile)
	cursor = connection.cursor()

	# Create the main table
	cursor.execute('CREATE TABLE siddb (id INTEGER PRIMARY KEY, category TEXT, filename TEXT, format TEXT, version NUMERIC, dataoffset TEXT, md5 TEXT, title TEXT, artist TEXT, release_date NUMERIC, release_name TEXT, songs NUMERIC, startsong NUMERIC, songlength TEXT, size NUMERIC, initaddr TEXT, playaddr TEXT, loadrange TEXT, speed TEXT, musplayer TEXT, playsid_basic NUMERIC, clock TEXT, sidmodel TEXT, startpage TEXT, pagelen TEXT, stil TEXT, stilentry TEXT, playcount NUMERIC, fav NUMERIC)')

	# Here we open the file and create the content variable
	# This is just to count it

	csvfile = open(csv_filename, 'rb')
	csvfile_content = csv.reader(csvfile, delimiter=',', quotechar='"')
	count = 0
	total = len(list(csvfile_content))

	#Now that we got the total Count, it is time to reopen the file, else it will not work
	csvfile.close()
	csvfile = open(csv_filename, 'rb')
	csvfile_content = csv.reader(csvfile, delimiter=',', quotechar='"')

	# Now we go through it

	for row in csvfile_content:
		count += 1

		# CSV Variables (Reading Rows)

		csv_filename = row[0].decode('iso-8859-1')
		csv_format = row[1].decode('iso-8859-1')
		csv_version = row[2].decode('iso-8859-1')
		csv_dataoffset = row[3].decode('iso-8859-1')
		csv_md5 = row[4].decode('iso-8859-1')
		csv_title = row[5].decode('iso-8859-1')
		csv_artist = row[6].decode('iso-8859-1')
		csv_released = row[7].decode('iso-8859-1')
		csv_releasednum = csv_released.split(" ")[0]
		csv_releasedname = csv_released.replace(csv_releasednum, "")
		csv_songs = row[8].decode('iso-8859-1')
		csv_startsong = row[9].decode('iso-8859-1')
		csv_songlength = row[10].decode('iso-8859-1')
		csv_size = row[11].decode('iso-8859-1')
		csv_initaddr = row[12].decode('iso-8859-1')
		csv_playaddr = row[13].decode('iso-8859-1')
		csv_loadrange = row[14].decode('iso-8859-1')
		csv_speed = row[15].decode('iso-8859-1')
		csv_musplayer = row[16].decode('iso-8859-1')
		csv_playsid_basic = row[17].decode('iso-8859-1')
		csv_clock = row[18].decode('iso-8859-1')
		csv_sidmodel = row[19].decode('iso-8859-1')
		csv_startpage = row[20].decode('iso-8859-1')
		csv_pagelen = row[21].decode('iso-8859-1')
		csv_stil = row[22].decode('iso-8859-1')
		#csv_stilentry = row[23].decode('iso-8859-1')
		csv_stilentry = ""
		csv_playcount = 0
		csv_fav = 0

		# Error Checking
		if (csv_stilentry == ""): csv_stilentry = "0"

		if (count!=1):
			csv_category = csv_filename.split("/")[1]
			cursor.execute('INSERT INTO siddb VALUES (null, ?, ?, ?, ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ? , ?, ?, ?, ?)', (csv_category, csv_filename, csv_format, csv_version, csv_dataoffset, csv_md5, csv_title, csv_artist, csv_releasednum, csv_releasedname, csv_songs, csv_startsong, csv_songlength, csv_size, csv_initaddr, csv_playaddr, csv_loadrange, csv_speed, csv_musplayer, csv_playsid_basic, csv_clock, csv_sidmodel, csv_startpage, csv_pagelen, csv_stil, csv_stilentry, csv_playcount, csv_fav ))
			ips_time = time.time() - start
			ips = count / ips_time
			dia_l1 = common.get_lstring(50021)
			dia_l2 = common.get_lstring(50022) + " " + str(count) + "/" + str(total)
			dia_l3 = common.get_lstring(50023) + " " + str(int(round(ips)))
			percent = (float(count) / float(total)) * 100
			print percent
			pDialog.update(int(percent), dia_l1, dia_l2, dia_l3)
			

	connection.commit()
	global global_start_time
	end = time.time()
	elapsed = end - global_start_time
	
	
	dialog = xbmcgui.Dialog()
	dia_title = common.get_lstring(50016)
	dia_l1 = common.get_lstring(50024) + " " + str(datetime.timedelta(seconds=int(elapsed)))
	dia_l2 = common.get_lstring(50025)
	ok = dialog.ok(dia_title, dia_l1)
	#print "Finished Downloading, Unzipping, Parsing and SQL Injecting the Database in " + str(datetime.timedelta(seconds=int(elapsed)))

# Hook to update the Dialog
def download_cache_hook(count, blockSize, totalSize):
	global pDialog
	global fn
	global start_time
	global downloaded
	if not (pDialog.iscanceled()):
		downloaded = downloaded + blockSize
		if downloaded > totalSize:
			downloaded = totalSize
		try:
			percent = int(min((count*blockSize*100)/totalSize, 100))
		except:
			 percent = 100
		if count != 0:
			time_elapsed = time.time() - start_time
			kbs = downloaded / time_elapsed
			dl_left = totalSize - downloaded
			time_remaining = int(dl_left) / int(kbs)
			time_total = time_remaining + time_elapsed
			kbs = common.convert_bytes(kbs)
			dia_l1 = common.get_lstring(50026) + ": " + fn
			dia_l2 = common.get_lstring(50027) + ": " + str(common.convert_bytes(downloaded)) + "/" + str(common.convert_bytes(totalSize)) + " @ " + str(kbs) + "/s"
			dia_l3 = common.get_lstring(50028) + ": " + str(datetime.timedelta(seconds=int(time_elapsed))) + "/" + str(datetime.timedelta(seconds=int(time_total))) + " (" + common.get_lstring(50029) + ": " + str(datetime.timedelta(seconds=int(time_remaining))) + ")"
			pDialog.update(percent, dia_l1, dia_l2, dia_l3)
	else:
		if not percent==100:
			raise "Cancelled"

# This is our little Downloader, it will download the file, once complete
# it will run the unzip progress (func: unzip_downloaded_cache)

def download(url, dir):
	global pDialog
	global start_time
	global downloaded
	downloaded = 0
	error = 0
	start_time = time.time()
	pDialog = xbmcgui.DialogProgress()
	dia_title = common.get_lstring(50016)
	dia_l1 = common.get_lstring(50030)
	ret = pDialog.create(dia_title, dia_l1)
	global fn
	fn = url.rsplit("/")[-1]
	filename = xbmc.translatePath(os.path.join(dir, fn))
	remoteaddr = url

	try:
		urllib.urlretrieve(remoteaddr,filename, reporthook=download_cache_hook)
	except:
		error = 1
		dialog = xbmcgui.Dialog()
		dia_title = common.get_lstring(50016)
		dia_l1 = common.get_lstring(50031)
		ok = dialog.ok(dia_title, dia_l1)
	
	if not error==1:
		unzip_downloaded_cache(filename)

# Here we have the Unzipper of the CSV Archive
# It will extract it into the userdir\addonfolder\temp\
# Once it is done, it will remove the downloaded archive
# and then run the Database Creation (func: dbcreate)

def unzip_downloaded_cache(archive):
	outdir = xbmc.translatePath(os.path.join( addonsavepath, 'temp'))
	pDialog = xbmcgui.DialogProgress()
	dia_title = common.get_lstring(50016)
	dia_l1 = common.get_lstring(50032)
	ret = pDialog.create(dia_title, dia_l1)
	count = 0
	zfobj = zipfile.ZipFile(archive)
	ico_total = len(zfobj.namelist())
	for name in zfobj.namelist():
		count = count + 1
		percent = int(((float(count) / ico_total) * 100))
		outfilename = xbmc.translatePath(os.path.join(outdir, name))
		outfile = open(os.path.join(outdir, name), 'wb')
		outfile.write(zfobj.read(name))
		outfile.close()
		dia_l1 = common.get_lstring(50026) + ": " + str(name)
		pDialog.update(int(percent), dia_l1)
	zfobj.close()
	os.remove(archive)
	dbcreate(outfilename)
	return

# This Function gets the latest Link for the CSV Archive
# It then passes it on to the downloader (func: download)
def get_csv_link():
	UAS = ""
	url = 'http://www.transbyte.org/SID/SIDlist.html'
	req = urllib2.Request(url)
	req.add_header('User-Agent', UAS)
	response = urllib2.urlopen(req)
	content=response.read()
	response.close()

	content = content.replace("\r", "")
	content = content.replace("\n", "")

	regex = '<TABLE.+?<A HREF="(.+?)">.+?</A>.+?</TABLE>'
	downloads = re.compile(regex).findall(content)
	if len(downloads) > 0:
		downloadurl = "http://www.transbyte.org/SID/" + downloads[1]
		
	download(downloadurl, os.path.join( addonsavepath, 'temp'))

# Set the global start time, check the paths, then grab the link
global_start_time =  time.time()
common.checkpaths()
get_csv_link()
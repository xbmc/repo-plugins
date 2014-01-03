# Static Libraries
import os,sys,time
import xbmc, xbmcaddon

# plugin Constants
__plugin__ = "High Voltage SID Collection"
__author__ = "Insayne (Code) & HannaK (Graphics) & Cptspiff (Contributor)"
__url__ = ""
__svn_url__ = ""
__version__ = "0.6"
__svn_revision__ = "$Revision$"
__XBMC_Revision__ = xbmc.getInfoLabel('System.BuildVersion')
__settings__ = xbmcaddon.Addon(id='plugin.audio.hvsc')

# Gets the Page item limit based on the integer value from the Settings.
def get_pagelimit(id):
	set_limit = "ERROR"
	
	if id=="0":
		set_limit = 50000
	elif id=="1":
		set_limit = 25
	elif id=="2":
		set_limit = 50
	elif id=="3":
		set_limit = 100
	elif id=="4":
		set_limit = 250
	elif id=="5":
		set_limit = 500
	elif id=="6":
		set_limit = 1000

	# Final Validation
	if set_limit!="ERROR":
		return set_limit
	else:
		return 25

# Gets the Song Length based on the integer value from the Settings.
def getsl(num):
	if num=="0":
		result = 60
	elif num=="1":
		result = 120
	elif num=="2":
		result = 180
	elif num=="3":
		result = 240
	elif num=="4":
		result = 300
	elif num=="5":
		result = 600
	elif num=="6":
		result = 1200
	elif num=="7":
		result = 1800
	elif num=="8":
		result = 2400
	elif num=="9":
		result = 3000
	elif num=="10":
		result = 3600
	elif num=="11":
		result = 7200
	elif num=="12":
		result = 14400
	elif num=="13":
		result = 21600
	elif num=="14":
		result = 28800
	elif num=="15":
		result = 36000
	elif num=="16":
		result = 43200
	elif num=="17":
		result = 86400
	else:
		result = 600
	return result

# Gets the Ordering based on the integer value from the Settings.

def get_ats(ats):
	if ats=="0":
		result = "artist"
	elif ats=="1":
		result = "title"
	else:
		result = "artist"
	return result
	
# Gets the Displaying limit based on the integer value from the Settings.
def get_atd(atd):
	if atd=="0":
		result = "at"
	elif atd=="1":
		result = "ta"
	else:
		result = "at"
	return result

# Gets the Source based on the integer value from the Settings.

def get_source(id):
	set_source = "ERROR"
	
	if id=="0":
		set_source = 'http://www.c64.org/HVSC'
	elif id=="1":
		set_source = 'ftp://dl.xs4all.nl/pub/mirror/HVSC/C64Music'
	elif id=="2":
		set_source = 'http://hafnium.prg.dtu.dk/HVSC/C64Music'
	elif id=="3":
		set_source = 'http://hvsc.pixolut.com/C64Music'
	elif id=="4":
		set_source = 'http://www.tld-crew.de/c64music'
	elif id=="5":
		set_source = 'http://hvsc.perff.dk'
	
	# Final Validation
	if set_source!="ERROR":
		return set_source
	else:
		return 'http://hvsc.perff.dk'
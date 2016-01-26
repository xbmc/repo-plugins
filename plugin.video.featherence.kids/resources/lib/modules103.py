# -*- coding: utf-8 -*-
import urllib,urllib2,sys,re,xbmcplugin,xbmcgui,xbmcaddon,xbmc,os

from variables import *
from shared_modules import *
if "plugin." in addonID: from shared_modules3 import *
'''---------------------------'''


'''105'''
def CATEGORIES102B(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102C(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102D(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102E(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102F(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102G(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102H(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102I(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102J(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102K(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102L(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102M(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102N(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=saftadatia') #דתיה בן דור
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102O(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102P(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102Q(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102R(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102S(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102T(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102U(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102V(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102W(General_LanguageL, background, background2): #
	'''סרטים'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''אירית'''
	if 'Irish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''בולגרית'''
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''טורקית'''
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''יפנית'''
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_id=')
	
	'''קוריאנית'''
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קזחית'''
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קטלאנית'''
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''קריאולית האיטית'''
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רומנית'''
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(105980).encode('utf-8'),list,17,"",addonString(105980).encode('utf-8'),'1',"", getAddonFanart(background, custom = "", default=background2))

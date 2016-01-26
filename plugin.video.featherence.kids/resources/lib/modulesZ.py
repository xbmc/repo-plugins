# -*- coding: utf-8 -*-
import urllib,urllib2,sys,re,xbmcplugin,xbmcgui,xbmcaddon,xbmc,os

from variables import *
from shared_modules import *
if "plugin." in addonID: from shared_modules3 import *
'''---------------------------'''

def CATEGORIES101Z(General_LanguageL, background, background2): #ערוצי טלוויזיה (שירים וסיפורים לילדים)
	'''ערוצי טלוויזיה'''
	
	'''עברית'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_ch=') #
		list.append('&youtube_ch=23music/playlists') #ערוץ החינוכית מוזיקה
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),list,17,"http://flaglane.com/download/israeli-flag/israeli-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://pre15.deviantart.net/2dd4/th/pre/f/2015/166/3/2/israel_aph_by_wolf_kid1000-d8xdbyp.jpg"))
		
	'''אנגלית'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_ch=KidsTV123/playlists') #KidsTV123
		list.append('&youtube_ch=wearebusybeavers/playlists') #Busy Beavers
		list.append('&youtube_ch=SuperSimpleSongs/playlists') #SuperSimpleSongs
		list.append('&youtube_ch=UCGwA4GjY4nGMIYvaJiA0EGA') #English Singsing
		list.append('&youtube_ch=TheChuChuTV/playlists') #ערוץ צ'ו-צ'ו
		list.append('&youtube_ch=yogabbagabba/playlists') # יו גאבה גאבה
		list.append('&youtube_ch=adesriza/playlists') #Kids Song Channel
		list.append('&youtube_ch=kidshut/playlists') #Kids Hut Channel
		list.append('&youtube_ch=cbeebiesgrownups/playlists') #cbeebiesgrownups
		
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),list,17,"http://flaglane.com/download/british-flag/british-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),'1',50, getAddonFanart(background,custom=""))
	
	'''אוזבקית'''
	list = []
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),list,17,"http://flaglane.com/download/uzbekistani-flag/uzbekistani-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''איטלקית'''
	list = []
	if 'Italian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),list,17,"http://flaglane.com/download/italian-flag/italian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אוקראינית'''
	list = []
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_ch=') #
	
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),list,17,"http://www.enchantedlearning.com/europe/ukraine/flag/Flagbig.GIF",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אינדונזית'''
	list = []
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),list,17,"http://www.united-states-flag.com/media/catalog/product/cache/2/thumbnail/9df78eab33525d08d6e5fb8d27136e95/F/L/FLGDECL1000004754_-00_indonesia-flag-decal_3.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אירית'''
	list = []
	if 'Irish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),list,17,"http://flaglane.com/download/irish-flag/irish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''בולגרית'''
	list = []
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),list,17,"http://flaglane.com/download/bulgarian-flag/bulgarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גאורגית'''
	list = []
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),list,17,"http://freestock.ca/georgia_grunge_flag_sjpg1133.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גרמנית'''
	list = []
	if 'German' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),list,17,"http://flaglane.com/download/german-flag/german-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''דנית'''
	list = []
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),list,17,"http://flaglane.com/download/dane-flag/dane-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הודית'''
	list = []
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),list,17,"http://www.iloveindia.com/national-symbols/pics/indian-flag.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הולנדית'''
	list = []
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),list,17,"http://flaglane.com/download/dutch-flag/dutch-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''הונגרית'''
	list = []
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),list,17,"http://flaglane.com/download/hungarian-flag/hungarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''טורקית'''
	list = []
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),list,17,"http://flaglane.com/download/turkish-flag/turkish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''יוונית'''
	list = []
	if 'Greek' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),list,17,"http://flaglane.com/download/greek-flag/greek-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''יפנית'''
	list = []
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_ch=supersimplejapanese') #SuperSimpleSongs
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),list,17,"http://flaglane.com/download/japanese-flag/japanese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סינית'''
	list = []
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),list,17,"http://flaglane.com/download/chinese-flag/chinese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סלובקית'''
	list = []
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),list,17,"http://flaglane.com/download/slovakian-flag/slovakian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
		
	'''ספרדית'''
	list = []
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_ch=UCBbsyG0o_cWlyY46ZRSdYJg/playlists') #ערוץ צ'ו-צ'ו
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),list,17,"http://flaglane.com/download/spanish-flag/spanish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סרבית'''
	list = []
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),list,17,"http://www.flagsinformation.com/serbian-flag.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פולנית'''
	list = []
	if 'Polish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),list,17,"http://flaglane.com/download/polish-flag/polish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פורטוגזית'''
	list = []
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),list,17,"http://flaglane.com/download/portuguese-flag/portuguese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פינית'''
	list = []
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),list,17,"http://flaglane.com/download/finnish-flag/finnish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

	'''ערבית'''
	list = []
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),list,17,"http://flaglane.com/download/emirian-flag/emirian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צ'כית'''
	list = []
	if 'Czech' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),list,17,"http://flaglane.com/download/czech-flag/czech-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צרפתית'''
	list = []
	if 'French' in General_LanguageL:
		list.append('&youtube_ch=ComptinesTVfr/playlists') #Comptines TV
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),list,17,"http://flaglane.com/download/french-flag/french-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קוריאנית'''
	list = []
	if 'Korean' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),list,17,"http://flaglane.com/download/south-korean-flag/south-korean-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קזחית'''
	list = []
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),list,17,"http://flaglane.com/download/kazakh-flag/kazakh-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קטלאנית'''
	list = []
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),list,17,"http://www.barcelonas.com/images/la-senyera.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קריאולית האיטית'''
	list = []
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),list,17,"http://flaglane.com/download/haitian-flag/haitian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רומנית'''
	list = []
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),list,17,"http://flaglane.com/download/romanian-flag/romanian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רוסית'''
	list = []
	if 'Russian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),list,17,"http://flaglane.com/download/russian-flag/russian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''שוודית'''
	list = []
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),list,17,"http://flaglane.com/download/swedish-flag/swedish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''תאילנדית'''
	list = []
	if 'Thai' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),list,17,"http://flaglane.com/download/thai-flag/thai-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

def CATEGORIES102Z(General_LanguageL, background, background2): #ערוצי טלוויזיה (הצגות)
	'''ערוצי טלוויזיה'''
	
	'''עברית'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),list,17,"http://flaglane.com/download/israeli-flag/israeli-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://pre15.deviantart.net/2dd4/th/pre/f/2015/166/3/2/israel_aph_by_wolf_kid1000-d8xdbyp.jpg"))
		
	'''אנגלית'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_ch=UCrNz73k6_mObQJSwJS1t4oQ') #TheDirtyOldFolkers
		list.append('&youtube_ch=UCTB-nHxdhjhH7DTTSWAxYQQ') #The Stillorgan Players
		
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),list,17,"http://flaglane.com/download/british-flag/british-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),'1',50, getAddonFanart(background,custom=""))

	'''אוזבקית'''
	list = []
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),list,17,"http://flaglane.com/download/uzbekistani-flag/uzbekistani-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''איטלקית'''
	list = []
	if 'Italian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),list,17,"http://flaglane.com/download/italian-flag/italian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אוקראינית'''
	list = []
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_ch=') #
	
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),list,17,"http://www.enchantedlearning.com/europe/ukraine/flag/Flagbig.GIF",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אינדונזית'''
	list = []
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),list,17,"http://www.united-states-flag.com/media/catalog/product/cache/2/thumbnail/9df78eab33525d08d6e5fb8d27136e95/F/L/FLGDECL1000004754_-00_indonesia-flag-decal_3.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אירית'''
	list = []
	if 'Irish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),list,17,"http://flaglane.com/download/irish-flag/irish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''בולגרית'''
	list = []
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),list,17,"http://flaglane.com/download/bulgarian-flag/bulgarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גאורגית'''
	list = []
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),list,17,"http://freestock.ca/georgia_grunge_flag_sjpg1133.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גרמנית'''
	list = []
	if 'German' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),list,17,"http://flaglane.com/download/german-flag/german-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''דנית'''
	list = []
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),list,17,"http://flaglane.com/download/dane-flag/dane-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הודית'''
	list = []
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),list,17,"http://www.iloveindia.com/national-symbols/pics/indian-flag.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הולנדית'''
	list = []
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),list,17,"http://flaglane.com/download/dutch-flag/dutch-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''הונגרית'''
	list = []
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),list,17,"http://flaglane.com/download/hungarian-flag/hungarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''טורקית'''
	list = []
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),list,17,"http://flaglane.com/download/turkish-flag/turkish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''יוונית'''
	list = []
	if 'Greek' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),list,17,"http://flaglane.com/download/greek-flag/greek-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''יפנית'''
	list = []
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),list,17,"http://flaglane.com/download/japanese-flag/japanese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סינית'''
	list = []
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),list,17,"http://flaglane.com/download/chinese-flag/chinese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סלובקית'''
	list = []
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),list,17,"http://flaglane.com/download/slovakian-flag/slovakian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
		
	'''ספרדית'''
	list = []
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),list,17,"http://flaglane.com/download/spanish-flag/spanish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סרבית'''
	list = []
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),list,17,"http://www.flagsinformation.com/serbian-flag.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פולנית'''
	list = []
	if 'Polish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),list,17,"http://flaglane.com/download/polish-flag/polish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פורטוגזית'''
	list = []
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),list,17,"http://flaglane.com/download/portuguese-flag/portuguese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פינית'''
	list = []
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),list,17,"http://flaglane.com/download/finnish-flag/finnish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

	'''ערבית'''
	list = []
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),list,17,"http://flaglane.com/download/emirian-flag/emirian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צ'כית'''
	list = []
	if 'Czech' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),list,17,"http://flaglane.com/download/czech-flag/czech-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צרפתית'''
	list = []
	if 'French' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),list,17,"http://flaglane.com/download/french-flag/french-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קוריאנית'''
	list = []
	if 'Korean' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),list,17,"http://flaglane.com/download/south-korean-flag/south-korean-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קזחית'''
	list = []
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),list,17,"http://flaglane.com/download/kazakh-flag/kazakh-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קטלאנית'''
	list = []
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),list,17,"http://www.barcelonas.com/images/la-senyera.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קריאולית האיטית'''
	list = []
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),list,17,"http://flaglane.com/download/haitian-flag/haitian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רומנית'''
	list = []
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),list,17,"http://flaglane.com/download/romanian-flag/romanian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רוסית'''
	list = []
	if 'Russian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),list,17,"http://flaglane.com/download/russian-flag/russian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''שוודית'''
	list = []
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),list,17,"http://flaglane.com/download/swedish-flag/swedish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''תאילנדית'''
	list = []
	if 'Thai' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),list,17,"http://flaglane.com/download/thai-flag/thai-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

def CATEGORIES103Z(General_LanguageL, background, background2): #ערוצי טלוויזיה
	'''ערוצי טלוויזיה'''
	
	'''עברית'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),list,17,"http://flaglane.com/download/israeli-flag/israeli-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://pre15.deviantart.net/2dd4/th/pre/f/2015/166/3/2/israel_aph_by_wolf_kid1000-d8xdbyp.jpg"))
		
	'''אנגלית'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),list,17,"http://flaglane.com/download/british-flag/british-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),'1',50, getAddonFanart(background,custom=""))

	'''אוזבקית'''
	list = []
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),list,17,"http://flaglane.com/download/uzbekistani-flag/uzbekistani-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''איטלקית'''
	list = []
	if 'Italian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),list,17,"http://flaglane.com/download/italian-flag/italian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אוקראינית'''
	list = []
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_ch=') #
	
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),list,17,"http://www.enchantedlearning.com/europe/ukraine/flag/Flagbig.GIF",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אינדונזית'''
	list = []
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),list,17,"http://www.united-states-flag.com/media/catalog/product/cache/2/thumbnail/9df78eab33525d08d6e5fb8d27136e95/F/L/FLGDECL1000004754_-00_indonesia-flag-decal_3.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אירית'''
	list = []
	if 'Irish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),list,17,"http://flaglane.com/download/irish-flag/irish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''בולגרית'''
	list = []
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),list,17,"http://flaglane.com/download/bulgarian-flag/bulgarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גאורגית'''
	list = []
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),list,17,"http://freestock.ca/georgia_grunge_flag_sjpg1133.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גרמנית'''
	list = []
	if 'German' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),list,17,"http://flaglane.com/download/german-flag/german-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''דנית'''
	list = []
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),list,17,"http://flaglane.com/download/dane-flag/dane-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הודית'''
	list = []
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),list,17,"http://www.iloveindia.com/national-symbols/pics/indian-flag.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הולנדית'''
	list = []
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),list,17,"http://flaglane.com/download/dutch-flag/dutch-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''הונגרית'''
	list = []
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),list,17,"http://flaglane.com/download/hungarian-flag/hungarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''טורקית'''
	list = []
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),list,17,"http://flaglane.com/download/turkish-flag/turkish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''יוונית'''
	list = []
	if 'Greek' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),list,17,"http://flaglane.com/download/greek-flag/greek-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))	
	
	'''יפנית'''
	list = []
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),list,17,"http://flaglane.com/download/japanese-flag/japanese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סינית'''
	list = []
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),list,17,"http://flaglane.com/download/chinese-flag/chinese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סלובקית'''
	list = []
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),list,17,"http://flaglane.com/download/slovakian-flag/slovakian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
		
	'''ספרדית'''
	list = []
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),list,17,"http://flaglane.com/download/spanish-flag/spanish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סרבית'''
	list = []
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),list,17,"http://www.flagsinformation.com/serbian-flag.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פולנית'''
	list = []
	if 'Polish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),list,17,"http://flaglane.com/download/polish-flag/polish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פורטוגזית'''
	list = []
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),list,17,"http://flaglane.com/download/portuguese-flag/portuguese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פינית'''
	list = []
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),list,17,"http://flaglane.com/download/finnish-flag/finnish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

	'''ערבית'''
	list = []
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),list,17,"http://flaglane.com/download/emirian-flag/emirian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צ'כית'''
	list = []
	if 'Czech' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),list,17,"http://flaglane.com/download/czech-flag/czech-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צרפתית'''
	list = []
	if 'French' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),list,17,"http://flaglane.com/download/french-flag/french-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קוריאנית'''
	list = []
	if 'Korean' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),list,17,"http://flaglane.com/download/south-korean-flag/south-korean-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קזחית'''
	list = []
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),list,17,"http://flaglane.com/download/kazakh-flag/kazakh-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קטלאנית'''
	list = []
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),list,17,"http://www.barcelonas.com/images/la-senyera.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קריאולית האיטית'''
	list = []
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),list,17,"http://flaglane.com/download/haitian-flag/haitian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רומנית'''
	list = []
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),list,17,"http://flaglane.com/download/romanian-flag/romanian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רוסית'''
	list = []
	if 'Russian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),list,17,"http://flaglane.com/download/russian-flag/russian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''שוודית'''
	list = []
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),list,17,"http://flaglane.com/download/swedish-flag/swedish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''תאילנדית'''
	list = []
	if 'Thai' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),list,17,"http://flaglane.com/download/thai-flag/thai-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

def CATEGORIES104Z(General_LanguageL, background, background2): #ערוצי טלוויזיה (סדרות)
	'''ערוצי טלוויזיה'''
	
	'''עברית'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_ch=malachiblum/playlists') #מלאכי בלום
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),list,17,"http://flaglane.com/download/israeli-flag/israeli-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://pre15.deviantart.net/2dd4/th/pre/f/2015/166/3/2/israel_aph_by_wolf_kid1000-d8xdbyp.jpg"))
		
	'''אנגלית'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),list,17,"http://flaglane.com/download/british-flag/british-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),'1',50, getAddonFanart(background,custom=""))

	'''אוזבקית'''
	list = []
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),list,17,"http://flaglane.com/download/uzbekistani-flag/uzbekistani-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''איטלקית'''
	list = []
	if 'Italian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),list,17,"http://flaglane.com/download/italian-flag/italian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אוקראינית'''
	list = []
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_ch=') #
	
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),list,17,"http://www.enchantedlearning.com/europe/ukraine/flag/Flagbig.GIF",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אינדונזית'''
	list = []
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),list,17,"http://www.united-states-flag.com/media/catalog/product/cache/2/thumbnail/9df78eab33525d08d6e5fb8d27136e95/F/L/FLGDECL1000004754_-00_indonesia-flag-decal_3.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אירית'''
	list = []
	if 'Irish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),list,17,"http://flaglane.com/download/irish-flag/irish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''בולגרית'''
	list = []
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),list,17,"http://flaglane.com/download/bulgarian-flag/bulgarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גאורגית'''
	list = []
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),list,17,"http://freestock.ca/georgia_grunge_flag_sjpg1133.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גרמנית'''
	list = []
	if 'German' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),list,17,"http://flaglane.com/download/german-flag/german-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''דנית'''
	list = []
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),list,17,"http://flaglane.com/download/dane-flag/dane-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הודית'''
	list = []
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),list,17,"http://www.iloveindia.com/national-symbols/pics/indian-flag.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הולנדית'''
	list = []
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),list,17,"http://flaglane.com/download/dutch-flag/dutch-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''הונגרית'''
	list = []
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),list,17,"http://flaglane.com/download/hungarian-flag/hungarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''טורקית'''
	list = []
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_ch=foxkidstr/playlists') #Fox Kids
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),list,17,"http://flaglane.com/download/turkish-flag/turkish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''יוונית'''
	list = []
	if 'Greek' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),list,17,"http://flaglane.com/download/greek-flag/greek-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''יפנית'''
	list = []
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),list,17,"http://flaglane.com/download/japanese-flag/japanese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סינית'''
	list = []
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),list,17,"http://flaglane.com/download/chinese-flag/chinese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סלובקית'''
	list = []
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),list,17,"http://flaglane.com/download/slovakian-flag/slovakian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
		
	'''ספרדית'''
	list = []
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),list,17,"http://flaglane.com/download/spanish-flag/spanish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סרבית'''
	list = []
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),list,17,"http://www.flagsinformation.com/serbian-flag.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פולנית'''
	list = []
	if 'Polish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),list,17,"http://flaglane.com/download/polish-flag/polish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פורטוגזית'''
	list = []
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),list,17,"http://flaglane.com/download/portuguese-flag/portuguese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פינית'''
	list = []
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),list,17,"http://flaglane.com/download/finnish-flag/finnish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

	'''ערבית'''
	list = []
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_ch=UCxUfxvkZb_0f-RsJmCsGGMw/playlists') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),list,17,"http://flaglane.com/download/emirian-flag/emirian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צ'כית'''
	list = []
	if 'Czech' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),list,17,"http://flaglane.com/download/czech-flag/czech-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צרפתית'''
	list = []
	if 'French' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),list,17,"http://flaglane.com/download/french-flag/french-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קוריאנית'''
	list = []
	if 'Korean' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),list,17,"http://flaglane.com/download/south-korean-flag/south-korean-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קזחית'''
	list = []
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),list,17,"http://flaglane.com/download/kazakh-flag/kazakh-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קטלאנית'''
	list = []
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),list,17,"http://www.barcelonas.com/images/la-senyera.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קריאולית האיטית'''
	list = []
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),list,17,"http://flaglane.com/download/haitian-flag/haitian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רומנית'''
	list = []
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),list,17,"http://flaglane.com/download/romanian-flag/romanian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רוסית'''
	list = []
	if 'Russian' in General_LanguageL:
		list.append('&youtube_ch=JetixRussiaChannelTV/playlists') #JetixRussiaChannelTV
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),list,17,"http://flaglane.com/download/russian-flag/russian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''שוודית'''
	list = []
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),list,17,"http://flaglane.com/download/swedish-flag/swedish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''תאילנדית'''
	list = []
	if 'Thai' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),list,17,"http://flaglane.com/download/thai-flag/thai-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

def CATEGORIES105Z(General_LanguageL, background, background2): #ערוצי טלוויזיה (סרטים)
	'''ערוצי טלוויזיה'''
	
	'''עברית'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),list,17,"http://flaglane.com/download/israeli-flag/israeli-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://pre15.deviantart.net/2dd4/th/pre/f/2015/166/3/2/israel_aph_by_wolf_kid1000-d8xdbyp.jpg"))
		
	'''אנגלית'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),list,17,"http://flaglane.com/download/british-flag/british-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),'1',50, getAddonFanart(background,custom=""))

	'''אוזבקית'''
	list = []
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),list,17,"http://flaglane.com/download/uzbekistani-flag/uzbekistani-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''איטלקית'''
	list = []
	if 'Italian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),list,17,"http://flaglane.com/download/italian-flag/italian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אוקראינית'''
	list = []
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_ch=') #
	
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),list,17,"http://www.enchantedlearning.com/europe/ukraine/flag/Flagbig.GIF",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אינדונזית'''
	list = []
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),list,17,"http://www.united-states-flag.com/media/catalog/product/cache/2/thumbnail/9df78eab33525d08d6e5fb8d27136e95/F/L/FLGDECL1000004754_-00_indonesia-flag-decal_3.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אירית'''
	list = []
	if 'Irish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),list,17,"http://flaglane.com/download/irish-flag/irish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''בולגרית'''
	list = []
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),list,17,"http://flaglane.com/download/bulgarian-flag/bulgarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גאורגית'''
	list = []
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),list,17,"http://freestock.ca/georgia_grunge_flag_sjpg1133.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גרמנית'''
	list = []
	if 'German' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),list,17,"http://flaglane.com/download/german-flag/german-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''דנית'''
	list = []
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),list,17,"http://flaglane.com/download/dane-flag/dane-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הודית'''
	list = []
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),list,17,"http://www.iloveindia.com/national-symbols/pics/indian-flag.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הולנדית'''
	list = []
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),list,17,"http://flaglane.com/download/dutch-flag/dutch-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''הונגרית'''
	list = []
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),list,17,"http://flaglane.com/download/hungarian-flag/hungarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''טורקית'''
	list = []
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),list,17,"http://flaglane.com/download/turkish-flag/turkish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''יוונית'''
	list = []
	if 'Greek' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),list,17,"http://flaglane.com/download/greek-flag/greek-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''יפנית'''
	list = []
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),list,17,"http://flaglane.com/download/japanese-flag/japanese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סינית'''
	list = []
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),list,17,"http://flaglane.com/download/chinese-flag/chinese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סלובקית'''
	list = []
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),list,17,"http://flaglane.com/download/slovakian-flag/slovakian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
		
	'''ספרדית'''
	list = []
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),list,17,"http://flaglane.com/download/spanish-flag/spanish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סרבית'''
	list = []
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),list,17,"http://www.flagsinformation.com/serbian-flag.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פולנית'''
	list = []
	if 'Polish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),list,17,"http://flaglane.com/download/polish-flag/polish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פורטוגזית'''
	list = []
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),list,17,"http://flaglane.com/download/portuguese-flag/portuguese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פינית'''
	list = []
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),list,17,"http://flaglane.com/download/finnish-flag/finnish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

	'''ערבית'''
	list = []
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),list,17,"http://flaglane.com/download/emirian-flag/emirian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צ'כית'''
	list = []
	if 'Czech' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),list,17,"http://flaglane.com/download/czech-flag/czech-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צרפתית'''
	list = []
	if 'French' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),list,17,"http://flaglane.com/download/french-flag/french-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קוריאנית'''
	list = []
	if 'Korean' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),list,17,"http://flaglane.com/download/south-korean-flag/south-korean-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קזחית'''
	list = []
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),list,17,"http://flaglane.com/download/kazakh-flag/kazakh-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קטלאנית'''
	list = []
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),list,17,"http://www.barcelonas.com/images/la-senyera.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קריאולית האיטית'''
	list = []
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),list,17,"http://flaglane.com/download/haitian-flag/haitian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רומנית'''
	list = []
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),list,17,"http://flaglane.com/download/romanian-flag/romanian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רוסית'''
	list = []
	if 'Russian' in General_LanguageL:
		list.append('&youtube_ch=getmovies/playlists') #
		list.append('&youtube_pl=PLIf4rYL_srdU4GHrrC2SY6FpPWV05dr-i') #Russian Kids Movies
		list.append('&youtube_id=jEQvhO3QCDg') #Three heroes and Shamahanskaya queen (cartoon)
		list.append('&youtube_id=8vPQKM5UOJU')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),list,17,"http://flaglane.com/download/russian-flag/russian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''שוודית'''
	list = []
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),list,17,"http://flaglane.com/download/swedish-flag/swedish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''תאילנדית'''
	list = []
	if 'Thai' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),list,17,"http://flaglane.com/download/thai-flag/thai-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

def CATEGORIES106Z(General_LanguageL, background, background2): #ערוצי טלוויזיה (פעוטות)
	'''ערוצי טלוויזיה'''
	
	'''עברית'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_ch=UCj10fKNd5h64J_M9YIQu0Zw/playlists')
		list.append('&youtube_ch=UCcYc90JDakyeXGeZgPL1ejA/playlists') #לולי
		list.append('&youtube_ch=UCl0jQT2Cj5brTRt5azL5E6g') #ג'וניור
		list.append('&youtube_ch=HopIsraeliChildhood/playlists') #הופ ילדות ישראלית
		list.append('&youtube_ch=UC8Zlrwmbc3-AjrjTxzqL7Uw/playlists') #צופי
		#ערוץ ניקלודיאון גוניור
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),list,17,"http://flaglane.com/download/israeli-flag/israeli-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://pre15.deviantart.net/2dd4/th/pre/f/2015/166/3/2/israel_aph_by_wolf_kid1000-d8xdbyp.jpg"))
		
	'''אנגלית'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_ch=UCGxnmQJquvQwlV_ICDfAKNA/playlists')
		list.append('&youtube_ch=') #ערוץ ניקלודיאון גוניור
		list.append('&youtube_ch=UCKcQ7Jo2VAGHiPMfDwzeRUw/playlists') #ערוץ צ'ו-צ'ו
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),list,17,"http://flaglane.com/download/british-flag/british-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),'1',50, getAddonFanart(background,custom=""))

	'''אוזבקית'''
	list = []
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),list,17,"http://flaglane.com/download/uzbekistani-flag/uzbekistani-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''איטלקית'''
	list = []
	if 'Italian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),list,17,"http://flaglane.com/download/italian-flag/italian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אוקראינית'''
	list = []
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_ch=') #
	
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),list,17,"http://www.enchantedlearning.com/europe/ukraine/flag/Flagbig.GIF",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אינדונזית'''
	list = []
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_ch=UC4OcQbL1ZRfAhqiOLkyANew/playlists')
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),list,17,"http://www.united-states-flag.com/media/catalog/product/cache/2/thumbnail/9df78eab33525d08d6e5fb8d27136e95/F/L/FLGDECL1000004754_-00_indonesia-flag-decal_3.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אירית'''
	list = []
	if 'Irish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),list,17,"http://flaglane.com/download/irish-flag/irish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''בולגרית'''
	list = []
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),list,17,"http://flaglane.com/download/bulgarian-flag/bulgarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גאורגית'''
	list = []
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),list,17,"http://freestock.ca/georgia_grunge_flag_sjpg1133.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גרמנית'''
	list = []
	if 'German' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),list,17,"http://flaglane.com/download/german-flag/german-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''דנית'''
	list = []
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),list,17,"http://flaglane.com/download/dane-flag/dane-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הודית'''
	list = []
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),list,17,"http://www.iloveindia.com/national-symbols/pics/indian-flag.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הולנדית'''
	list = []
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_ch=BabyTVNederlands/playlists') #Baby TV
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),list,17,"http://flaglane.com/download/dutch-flag/dutch-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''הונגרית'''
	list = []
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=PLWo4IqXs7qRCNWAihXvq54pemNXgiw74R') #Baby TV
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),list,17,"http://flaglane.com/download/hungarian-flag/hungarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''טורקית'''
	list = []
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_ch=BabyTVTurkish/playlists') #Baby TV
		list.append('&youtube_ch=') #
		list.append('&youtube_ch=adisebabatv/playlists') #ערוץ עליבאבא
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),list,17,"http://flaglane.com/download/turkish-flag/turkish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''יוונית'''
	list = []
	if 'Greek' in General_LanguageL:
		list.append('&youtube_ch=BabyTVGreek/playlists') #Baby TV
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),list,17,"http://flaglane.com/download/greek-flag/greek-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''יפנית'''
	list = []
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_ch=babytvjapanese/playlists') #Baby TV
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),list,17,"http://flaglane.com/download/japanese-flag/japanese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סינית'''
	list = []
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),list,17,"http://flaglane.com/download/chinese-flag/chinese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סלובקית'''
	list = []
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),list,17,"http://flaglane.com/download/slovakian-flag/slovakian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
		
	'''ספרדית'''
	list = []
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_ch=') #
		list.append('&youtube_ch=babytvspanish/playlists') #Baby TV
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),list,17,"http://flaglane.com/download/spanish-flag/spanish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סרבית'''
	list = []
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),list,17,"http://www.flagsinformation.com/serbian-flag.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פולנית'''
	list = []
	if 'Polish' in General_LanguageL:
		list.append('&youtube_ch=') #
		list.append('&youtube_ch=BabyTVPolski/playlists') #Baby TV
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),list,17,"http://flaglane.com/download/polish-flag/polish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פורטוגזית'''
	list = []
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_ch=BabyTVBrazil/playlists') #Baby TV
		list.append('&youtube_ch=BabyTVPortugues/playlists') #Baby TV
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),list,17,"http://flaglane.com/download/portuguese-flag/portuguese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פינית'''
	list = []
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),list,17,"http://flaglane.com/download/finnish-flag/finnish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

	'''ערבית'''
	list = []
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_ch=BabyTVArabic/playlists') #Baby TV
		list.append('&youtube_ch=braa3eem/playlists') #Baraem HD
		list.append('&youtube_ch=l3araem') #l3araem
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),list,17,"http://flaglane.com/download/emirian-flag/emirian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צ'כית'''
	list = []
	if 'Czech' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),list,17,"http://flaglane.com/download/czech-flag/czech-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צרפתית'''
	list = []
	if 'French' in General_LanguageL:
		list.append('&youtube_ch=BabyTVFrench/playlists') #Baby TV
		list.append('&youtube_ch=nickelodeonjuniorfr/playlists') #ערוץ ניקלודיאון גוניור
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),list,17,"http://flaglane.com/download/french-flag/french-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קוריאנית'''
	list = []
	if 'Korean' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),list,17,"http://flaglane.com/download/south-korean-flag/south-korean-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קזחית'''
	list = []
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),list,17,"http://flaglane.com/download/kazakh-flag/kazakh-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קטלאנית'''
	list = []
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),list,17,"http://www.barcelonas.com/images/la-senyera.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קריאולית האיטית'''
	list = []
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),list,17,"http://flaglane.com/download/haitian-flag/haitian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רומנית'''
	list = []
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),list,17,"http://flaglane.com/download/romanian-flag/romanian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רוסית'''
	list = []
	if 'Russian' in General_LanguageL:
		list.append('&youtube_ch=BabyTVRussian/playlists')
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),list,17,"http://flaglane.com/download/russian-flag/russian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''שוודית'''
	list = []
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),list,17,"http://flaglane.com/download/swedish-flag/swedish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''תאילנדית'''
	list = []
	if 'Thai' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),list,17,"http://flaglane.com/download/thai-flag/thai-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

def CATEGORIES107Z(General_LanguageL, background, background2): #ערוצי טלוויזיה (קטנטנים)
	'''ערוצי טלוויזיה'''
	
	'''עברית'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_ch=disneyjuniorisrael/playlists') #דיסני ג'וניור
		list.append('&youtube_ch=hopchannel/playlists') #הופ!
		list.append('&youtube_ch=UCQWDQwBdFVOPjvBy6mgqUQQ') #ניק ג'וניור ישראל
		list.append('&wallaNew2=http://nickjr.walla.co.il/&name_=Nick Junior Israel&')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),list,17,"http://flaglane.com/download/israeli-flag/israeli-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://pre15.deviantart.net/2dd4/th/pre/f/2015/166/3/2/israel_aph_by_wolf_kid1000-d8xdbyp.jpg"))
		
	'''אנגלית'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_ch=disneyjunior/playlists') #דיסני ג'וניור
		list.append('&youtube_ch=DisneyJuniorUK/playlists') #דיסני ג'וניור
		list.append('&youtube_ch=MinidiscoUK/playlists') #ערוץ מינידיסקו
		list.append('&youtube_ch=UC3djj8jS0370cu_ghKs_Ong') #hooplakidz
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),list,17,"http://flaglane.com/download/british-flag/british-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),'1',50, getAddonFanart(background,custom=""))

	'''אוזבקית'''
	list = []
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),list,17,"http://flaglane.com/download/uzbekistani-flag/uzbekistani-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''איטלקית'''
	list = []
	if 'Italian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),list,17,"http://flaglane.com/download/italian-flag/italian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אוקראינית'''
	list = []
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_ch=') #
	
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),list,17,"http://www.enchantedlearning.com/europe/ukraine/flag/Flagbig.GIF",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אינדונזית'''
	list = []
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),list,17,"http://www.united-states-flag.com/media/catalog/product/cache/2/thumbnail/9df78eab33525d08d6e5fb8d27136e95/F/L/FLGDECL1000004754_-00_indonesia-flag-decal_3.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אירית'''
	list = []
	if 'Irish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),list,17,"http://flaglane.com/download/irish-flag/irish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''בולגרית'''
	list = []
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_ch=UCFZQqQBX-XqZ9BMtaDOVg3A/playlists') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),list,17,"http://flaglane.com/download/bulgarian-flag/bulgarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גאורגית'''
	list = []
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),list,17,"http://freestock.ca/georgia_grunge_flag_sjpg1133.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גרמנית'''
	list = []
	if 'German' in General_LanguageL:
		list.append('&youtube_ch=UChIwMYwfK1S-P1DTtAKIs3A/playlists') #ערוץ מינידיסקו
		list.append('&youtube_ch=DisneyJuniorGermany/playlists') #דיסני ג'וניור
		
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),list,17,"http://flaglane.com/download/german-flag/german-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''דנית'''
	list = []
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_ch=UC8uswywABlSdllEXHpJagJw/playlists') #דיסני ג'וניור
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),list,17,"http://flaglane.com/download/dane-flag/dane-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הודית'''
	list = []
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_ch=UCV1t1Kb_fbd3jUsYWywkjcQ/playlists') #דיסני ג'וניור
		list.append('&youtube_ch=UCBWV-kJ67Sl9rIsqA7RjzyA/playlists') #דיסני ג'וניור
		
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),list,17,"http://www.iloveindia.com/national-symbols/pics/indian-flag.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הולנדית'''
	list = []
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_ch=UCRWlUS-tveicl_GxQ6vsCRg/playlists') #ערוץ טיטונוס
		list.append('&youtube_ch=UCD69tZl3tqlb3LJXf8U6Hqg/playlists') #דיסני ג'וניור
		list.append('&youtube_ch=ddcompany/playlists') #ערוץ מינידיסקו
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),list,17,"http://flaglane.com/download/dutch-flag/dutch-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''הונגרית'''
	list = []
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),list,17,"http://flaglane.com/download/hungarian-flag/hungarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''טורקית'''
	list = []
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),list,17,"http://flaglane.com/download/turkish-flag/turkish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''יוונית'''
	list = []
	if 'Greek' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),list,17,"http://flaglane.com/download/greek-flag/greek-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''יפנית'''
	list = []
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),list,17,"http://flaglane.com/download/japanese-flag/japanese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סינית'''
	list = []
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),list,17,"http://flaglane.com/download/chinese-flag/chinese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סלובקית'''
	list = []
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),list,17,"http://flaglane.com/download/slovakian-flag/slovakian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
		
	'''ספרדית'''
	list = []
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_ch=UCTpAjwOrvCySeZBfsMXfD9Q/playlists') #ערוץ מינידיסקו
		list.append('&youtube_ch=DisneyJuniorES/playlists') #דיסני ג'וניור
		list.append('&youtube_ch=DisneyJuniorLA/playlists') #דיסני ג'וניור
		
		list.append('&youtube_ch=AnimakidsTV') #AnimakidsTV
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),list,17,"http://flaglane.com/download/spanish-flag/spanish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סרבית'''
	list = []
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),list,17,"http://www.flagsinformation.com/serbian-flag.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פולנית'''
	list = []
	if 'Polish' in General_LanguageL:
		list.append('&youtube_ch=disneyjuniorpl/playlists') #דיסני ג'וניור
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),list,17,"http://flaglane.com/download/polish-flag/polish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פורטוגזית'''
	list = []
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),list,17,"http://flaglane.com/download/portuguese-flag/portuguese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פינית'''
	list = []
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),list,17,"http://flaglane.com/download/finnish-flag/finnish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

	'''ערבית'''
	list = []
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),list,17,"http://flaglane.com/download/emirian-flag/emirian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צ'כית'''
	list = []
	if 'Czech' in General_LanguageL:
		list.append('&youtube_ch=DisneyJuniorCR/playlists') #דיסני ג'וניור
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),list,17,"http://flaglane.com/download/czech-flag/czech-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צרפתית'''
	list = []
	if 'French' in General_LanguageL:
		list.append('&youtube_ch=MinidiscoNL/playlists') #ערוץ מינידיסקו
		list.append('&youtube_ch=ssebastienn/playlists') #ערוץ טיטונוס
		list.append('&youtube_ch=UCCzFnM_wVA6OF_6o4TVPMcQ/playlists') #ערוץ טיטונוס
		list.append('&youtube_ch=UCbExdKOgxC4YQMHjrcGEfCQ/playlists') #ערוץ טיטונוס
		list.append('&youtube_ch=DisneyJuniorFR/playlists') #דיסני ג'וניור
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),list,17,"http://flaglane.com/download/french-flag/french-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קוריאנית'''
	list = []
	if 'Korean' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),list,17,"http://flaglane.com/download/south-korean-flag/south-korean-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קזחית'''
	list = []
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),list,17,"http://flaglane.com/download/kazakh-flag/kazakh-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קטלאנית'''
	list = []
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),list,17,"http://www.barcelonas.com/images/la-senyera.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קריאולית האיטית'''
	list = []
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),list,17,"http://flaglane.com/download/haitian-flag/haitian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רומנית'''
	list = []
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),list,17,"http://flaglane.com/download/romanian-flag/romanian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רוסית'''
	list = []
	if 'Russian' in General_LanguageL:
		list.append('&youtube_ch=MinidiscoRU/playlists') #ערוץ מינידיסקו
		list.append('&youtube_ch=UCIOwKErxRgAWecQrVVax2MA/playlists') #רכבות מChaggingtona
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),list,17,"http://flaglane.com/download/russian-flag/russian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''שוודית'''
	list = []
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_ch=DisneyjuniorSe/playlists') #דיסני ג'וניור
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),list,17,"http://flaglane.com/download/swedish-flag/swedish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''תאילנדית'''
	list = []
	if 'Thai' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),list,17,"http://flaglane.com/download/thai-flag/thai-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

def CATEGORIES108Z(General_LanguageL, background, background2): #ערוצי טלוויזיה (ילדים ונוער)
	'''ערוצי טלוויזיה'''
	
	'''עברית'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_ch=UCYFLZdLRZGnmKQBH6RB8IjA/playlists') #ערוץ החינוכית
		list.append('&youtube_ch=23tv/playlists') #ערוץ החינוכית
		list.append('&youtube_ch=The23Kidz/playlists') #ערוץ החינוכית ילדים
		list.append('&youtube_ch=23bagrut/playlists') #ערוץ החינוכית בגרות
		
		list.append('&youtube_ch=UCOFp2_GttW3ljCuOc7r4l7g/playlists') #ערוץ הילדים
		list.append('&youtube_ch=nickelodeonIsrael/playlists') #ערוץ ניקלודיאון
		list.append('&youtube_ch=YesVOD/playlists') #YesVOD
		list.append('&youtube_ch=LEGO/playlists') #LEGO

	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),list,17,"http://flaglane.com/download/israeli-flag/israeli-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://pre15.deviantart.net/2dd4/th/pre/f/2015/166/3/2/israel_aph_by_wolf_kid1000-d8xdbyp.jpg"))
		
	'''אנגלית'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_ch=Nickelodeon/playlists') #ערוץ ניקלודיאון
		list.append('&youtube_ch=UCHiceVclOIFCgAcveITRLLw/playlists') #ערוץ ניקלודיאון
		list.append('&youtube_ch=KidsAnimalChannel/playlists') #Kids Animal Channel
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),list,17,"http://flaglane.com/download/british-flag/british-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),'1',50, getAddonFanart(background,custom=""))

	'''אוזבקית'''
	list = []
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),list,17,"http://flaglane.com/download/uzbekistani-flag/uzbekistani-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''איטלקית'''
	list = []
	if 'Italian' in General_LanguageL:
		list.append('&youtube_ch=UCsHe74knLccbgec6WdGAkPQ/playlists') #ערוץ ניקלודיאון
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),list,17,"http://flaglane.com/download/italian-flag/italian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אוקראינית'''
	list = []
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_ch=') #
	
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),list,17,"http://www.enchantedlearning.com/europe/ukraine/flag/Flagbig.GIF",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אינדונזית'''
	list = []
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),list,17,"http://www.united-states-flag.com/media/catalog/product/cache/2/thumbnail/9df78eab33525d08d6e5fb8d27136e95/F/L/FLGDECL1000004754_-00_indonesia-flag-decal_3.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אירית'''
	list = []
	if 'Irish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),list,17,"http://flaglane.com/download/irish-flag/irish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''בולגרית'''
	list = []
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),list,17,"http://flaglane.com/download/bulgarian-flag/bulgarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גאורגית'''
	list = []
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),list,17,"http://freestock.ca/georgia_grunge_flag_sjpg1133.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גרמנית'''
	list = []
	if 'German' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),list,17,"http://flaglane.com/download/german-flag/german-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''דנית'''
	list = []
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),list,17,"http://flaglane.com/download/dane-flag/dane-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הודית'''
	list = []
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_ch=OfficialNickIndia/playlists') #ערוץ ניקלודיאון
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),list,17,"http://www.iloveindia.com/national-symbols/pics/indian-flag.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הולנדית'''
	list = []
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_ch=nickelodeonoffiziell/playlists')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),list,17,"http://flaglane.com/download/dutch-flag/dutch-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''הונגרית'''
	list = []
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),list,17,"http://flaglane.com/download/hungarian-flag/hungarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''טורקית'''
	list = []
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_ch=foxkidstr/playlists') #Fox Kids
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),list,17,"http://flaglane.com/download/turkish-flag/turkish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''יוונית'''
	list = []
	if 'Greek' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),list,17,"http://flaglane.com/download/greek-flag/greek-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''יפנית'''
	list = []
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),list,17,"http://flaglane.com/download/japanese-flag/japanese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סינית'''
	list = []
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),list,17,"http://flaglane.com/download/chinese-flag/chinese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סלובקית'''
	list = []
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),list,17,"http://flaglane.com/download/slovakian-flag/slovakian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
		
	'''ספרדית'''
	list = []
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_ch=mundonickelodeon/playlists') #ערוץ ניקלודיאון
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),list,17,"http://flaglane.com/download/spanish-flag/spanish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סרבית'''
	list = []
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),list,17,"http://www.flagsinformation.com/serbian-flag.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פולנית'''
	list = []
	if 'Polish' in General_LanguageL:
		list.append('&youtube_ch=UCBgfqkarug1n6eM5yqsUwDg/playlists') #ערוץ ניקלודיאון
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),list,17,"http://flaglane.com/download/polish-flag/polish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פורטוגזית'''
	list = []
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_ch=canalnickelodeonpt/playlists') #ערוץ ניקלודיאון
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),list,17,"http://flaglane.com/download/portuguese-flag/portuguese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פינית'''
	list = []
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),list,17,"http://flaglane.com/download/finnish-flag/finnish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

	'''ערבית'''
	list = []
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_ch=TheNickelodeonarabia/playlists') #ערוץ ניקלודיאון
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),list,17,"http://flaglane.com/download/emirian-flag/emirian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צ'כית'''
	list = []
	if 'Czech' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),list,17,"http://flaglane.com/download/czech-flag/czech-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צרפתית'''
	list = []
	if 'French' in General_LanguageL:
		list.append('&youtube_ch=nickelodeonfr/playlists') #ערוץ ניקלודיאון
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),list,17,"http://flaglane.com/download/french-flag/french-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קוריאנית'''
	list = []
	if 'Korean' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),list,17,"http://flaglane.com/download/south-korean-flag/south-korean-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קזחית'''
	list = []
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_ch=UCv8R8vF9lR_A_zhu5VOP2iA/playlists') #ערוץ ניקלודיאון
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),list,17,"http://flaglane.com/download/kazakh-flag/kazakh-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קטלאנית'''
	list = []
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),list,17,"http://www.barcelonas.com/images/la-senyera.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קריאולית האיטית'''
	list = []
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),list,17,"http://flaglane.com/download/haitian-flag/haitian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רומנית'''
	list = []
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_ch=UCOudV7aMMSQl2GiD-SVNIew/playlists') #ערוץ ניקלודיאון
		list.append('&youtube_ch=xidechannel/playlists') #JetixWorld
		
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),list,17,"http://flaglane.com/download/romanian-flag/romanian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רוסית'''
	list = []
	if 'Russian' in General_LanguageL:
		list.append('&youtube_ch=promonickrus/playlists') #ערוץ ניקלודיאון
		list.append('&youtube_ch=UCItWLjJyvP4VZVe6lkBDsog/playlists') #האבות של קריקטורות חינוכיות
		list.append('&youtube_ch=JetixRussiaChannelTV/playlists') #JetixRussiaChannelTV
		
		
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),list,17,"http://flaglane.com/download/russian-flag/russian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''שוודית'''
	list = []
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),list,17,"http://flaglane.com/download/swedish-flag/swedish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''תאילנדית'''
	list = []
	if 'Thai' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),list,17,"http://flaglane.com/download/thai-flag/thai-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

def CATEGORIES109Z(General_LanguageL, background, background2): #ערוצי טלוויזיה
	'''ערוצי טלוויזיה'''
	
	'''עברית'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),list,17,"http://flaglane.com/download/israeli-flag/israeli-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://pre15.deviantart.net/2dd4/th/pre/f/2015/166/3/2/israel_aph_by_wolf_kid1000-d8xdbyp.jpg"))
		
	'''אנגלית'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),list,17,"http://flaglane.com/download/british-flag/british-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),'1',50, getAddonFanart(background,custom=""))

	'''אוזבקית'''
	list = []
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),list,17,"http://flaglane.com/download/uzbekistani-flag/uzbekistani-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''איטלקית'''
	list = []
	if 'Italian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),list,17,"http://flaglane.com/download/italian-flag/italian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אוקראינית'''
	list = []
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_ch=') #
		list.append('&youtube_ch=ukranima/playlists') #Ukranima
	
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),list,17,"http://www.enchantedlearning.com/europe/ukraine/flag/Flagbig.GIF",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אינדונזית'''
	list = []
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),list,17,"http://www.united-states-flag.com/media/catalog/product/cache/2/thumbnail/9df78eab33525d08d6e5fb8d27136e95/F/L/FLGDECL1000004754_-00_indonesia-flag-decal_3.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אירית'''
	list = []
	if 'Irish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),list,17,"http://flaglane.com/download/irish-flag/irish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''בולגרית'''
	list = []
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),list,17,"http://flaglane.com/download/bulgarian-flag/bulgarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גאורגית'''
	list = []
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),list,17,"http://freestock.ca/georgia_grunge_flag_sjpg1133.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גרמנית'''
	list = []
	if 'German' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),list,17,"http://flaglane.com/download/german-flag/german-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''דנית'''
	list = []
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),list,17,"http://flaglane.com/download/dane-flag/dane-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הודית'''
	list = []
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),list,17,"http://www.iloveindia.com/national-symbols/pics/indian-flag.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),'1',50, getAddonFanart(background, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הולנדית'''
	list = []
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),list,17,"http://flaglane.com/download/dutch-flag/dutch-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''הונגרית'''
	list = []
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),list,17,"http://flaglane.com/download/hungarian-flag/hungarian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''טורקית'''
	list = []
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),list,17,"http://flaglane.com/download/turkish-flag/turkish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''יוונית'''
	list = []
	if 'Greek' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),list,17,"http://flaglane.com/download/greek-flag/greek-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''יפנית'''
	list = []
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),list,17,"http://flaglane.com/download/japanese-flag/japanese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סינית'''
	list = []
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),list,17,"http://flaglane.com/download/chinese-flag/chinese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סלובקית'''
	list = []
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),list,17,"http://flaglane.com/download/slovakian-flag/slovakian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
		
	'''ספרדית'''
	list = []
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),list,17,"http://flaglane.com/download/spanish-flag/spanish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''סרבית'''
	list = []
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),list,17,"http://www.flagsinformation.com/serbian-flag.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פולנית'''
	list = []
	if 'Polish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),list,17,"http://flaglane.com/download/polish-flag/polish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פורטוגזית'''
	list = []
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),list,17,"http://flaglane.com/download/portuguese-flag/portuguese-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פינית'''
	list = []
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),list,17,"http://flaglane.com/download/finnish-flag/finnish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

	'''ערבית'''
	list = []
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),list,17,"http://flaglane.com/download/emirian-flag/emirian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צ'כית'''
	list = []
	if 'Czech' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),list,17,"http://flaglane.com/download/czech-flag/czech-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צרפתית'''
	list = []
	if 'French' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),list,17,"http://flaglane.com/download/french-flag/french-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קוריאנית'''
	list = []
	if 'Korean' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),list,17,"http://flaglane.com/download/south-korean-flag/south-korean-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קזחית'''
	list = []
	if 'Kazakh' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),list,17,"http://flaglane.com/download/kazakh-flag/kazakh-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קטלאנית'''
	list = []
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),list,17,"http://www.barcelonas.com/images/la-senyera.jpg",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קריאולית האיטית'''
	list = []
	if 'Haitian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),list,17,"http://flaglane.com/download/haitian-flag/haitian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רומנית'''
	list = []
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),list,17,"http://flaglane.com/download/romanian-flag/romanian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''רוסית'''
	list = []
	if 'Russian' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),list,17,"http://flaglane.com/download/russian-flag/russian-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''שוודית'''
	list = []
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_ch=')
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),list,17,"http://flaglane.com/download/swedish-flag/swedish-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''תאילנדית'''
	list = []
	if 'Thai' in General_LanguageL:
		list.append('&youtube_ch=') #
	addDir('-' + addonString_servicefeatherence(32089).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),list,17,"http://flaglane.com/download/thai-flag/thai-flag-medium.png",addonString_servicefeatherence(32082).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),'1',50, getAddonFanart(background, custom="", default=background2))

	
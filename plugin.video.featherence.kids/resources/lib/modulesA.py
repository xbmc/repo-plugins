# -*- coding: utf-8 -*-
import urllib,urllib2,sys,re,xbmcplugin,xbmcgui,xbmcaddon,xbmc,os

from variables import *
from shared_modules import *
if "plugin." in addonID: from shared_modules3 import *
'''---------------------------'''
	
def CATEGORIES101A(General_LanguageL, background, background2): #עמוד הבא שירים וסיפורים
	'''עמוד הבא'''
	list = []

	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''אנגלית'''
	if 'English' in General_LanguageL:
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
		
	addDir('-' + localize(33078),list,6,featherenceserviceicons_path + 'nextpage.png',"",'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES102A(General_LanguageL, background, background2): #עמוד הבא הצגות ילדים
	'''עמוד הבא'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		'''עוד...'''
		list = []
		list.append('&youtube_id=0FaBsetswDA') #אחותי הקטנה
		list.append('&youtube_id=PUL2C9mEAKQ') #גינת הפלאים של רינת
		list.append('&youtube_id=o20-0VygrsE') #גינת השטוזים של דתיה
		list.append('&youtube_id=-ihwgBW3sVs') #לא יאומן כי יסופר
		list.append('&youtube_id=_ixMuVcAGhA') #סוד השוקולד
		list.append('&youtube_id=YOs5zhvXUf8') #הפיג'מות
		list.append('&youtube_id=kbzPyZV3cck') #תום סוייר
		list.append('&youtube_id=i5yQxLraENk') #האסופית
		list.append('&youtube_id=yfEzE5V409k')
		list.append('&youtube_pl=PLuDrdycU7c6gcx20C2zPrM87gMfaaoCov') #עוץ לי גוץ לי
		#list.append('&wallaNew=item_id%3D2833366&name_=זרעים של מסטיק&')
		
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_id=b1bC503njMI')
		list.append('&youtube_id=V1LEbSnUeM0') #Christmas 2013
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
		list.append('&youtube_pl=PLue6znsWBAfeG6yPc9M9FkJ955RTLBXH6')
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

	addDir('-' + localize(33078),list,6,featherenceserviceicons_path + 'nextpage.png',"",'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES104A(General_LanguageL, background, background2): #עמוד הבא סדרות
	'''עמוד הבא'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:

		list.append('&youtube_id=')
		list.append('&youtube_pl=')
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

	addDir('-' + localize(33078),list,6,featherenceserviceicons_path + 'nextpage.png',"",'1',"", getAddonFanart(background, custom = "", default=background2))
		
def CATEGORIES105A(General_LanguageL, background, background2): #עמוד הבא סרטים
	'''עמוד הבא'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		list.append('&youtube_id=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_id=RwY6ZNmV1OU')
		list.append('&youtube_pl=PLZOPiMtEyky3WOXdj-PUdbTsGpsm-zS8m')
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
		list.append('&youtube_pl=PLIf4rYL_srdU4GHrrC2SY6FpPWV05dr-i') #Russian Kids Movies
		list.append('&youtube_id=jEQvhO3QCDg') #Three heroes and Shamahanskaya queen (cartoon)
		list.append('&youtube_id=8vPQKM5UOJU')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir('-' + localize(33078),list,6,featherenceserviceicons_path + 'nextpage.png',"",'1',"", getAddonFanart(background, custom = "", default=background2))
	
def CATEGORIES106A(General_LanguageL, background, background2): #עמוד הבא פעוטות
	'''עמוד הבא'''
	list = []

	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLwimDnICcPKNQy5TSz2s5XKWsE6kKV5C1') #מגלים עם לולי
		list.append('&youtube_id=dby1qndJnGs')
		list.append('&youtube_id=Ood3teygwh8')
		list.append('&youtube_id=KEDLj-c5zZg')
		list.append('&youtube_id=y24MAvLMHdE')
		list.append('youtube_pl=PLnraPnhPHcc4EJiGhB2lh3cq0xo3gD0gp') #צופי
		list.append('youtube_pl=PLnraPnhPHcc7gx1zReO0qmXQ5nGV_6wtJ') #צופי
		list.append('youtube_pl=PLnraPnhPHcc7O4BysIZ9_9nBOuakjrvUJ') #צופי
		list.append('youtube_pl=PLnraPnhPHcc7ZM0lb57BnB2QK9syspUuF') #צופי
		
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLydGVtigmLv3dH5928n81xDim_3YrVHZ7') #Baby TV

	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=PLkEXJmKDVso5cQjSUez3x8oLsI7VloRPE')
	
	'''אינדונזית'''
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_pl=PLgClOKaT2s3qrYvMBQPjgYN3iYLcRbt3R')
	
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
		list.append('&youtube_pl=PLWZsBPdcLf9yQpGIWJxLaUfamE5JbCt_H')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	'''יוונית'''
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=PL7Orgq9K_2UGacpdTRzKVgy_yPirEmItY') #מכל מיני
		
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
		list.append('&youtube_pl=PLwSb6vqkP17DnPHcnjCM66IWLC2Eh8zTu') #Baby TV
		
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=PLZ8depkdPswrWb-fUqGCczOqndCZIX24S') #מכל מיני
	
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
		list.append('&youtube_pl=PLCsBweb0jQ6Ryvv3inUpGXnZXAwCIFEbm') #Shapes for kids children
		list.append('&youtube_pl=PLA8O63dq_Dpf7YuaGE1LZr8HIqtrldyZi') #?
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir('-' + localize(33078),list,6,featherenceserviceicons_path + 'nextpage.png',"",'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES107A(General_LanguageL, background, background2): #עמוד הבא קטנטנים
	'''עמוד הבא'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=') #
		
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_id=xhap8ezkfCE')
		
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		
	'''אוקראינית'''
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=PLElG6fwk_0UkTp_pGUhU_npcyRR2HLV26') #אוסף לקטנטנים
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
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=') #
		
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
		list.append('&youtube_pl=') #
		
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
		list.append('&youtube_pl=PL5BF1A9A947CEC28B') #מכל מיני
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
		list.append('&youtube_pl=PL5p0NjRxSV8Dw8nK2rm-mr9ykr7OA5dQ_') #old russian cartoons random
		list.append('&youtube_pl=PL465ZjxENzxGCYVR3zCKWdNzpT_S6L26Q')
		list.append('&youtube_pl=PLHfTivZrNVwwehlbkuaUeWQmQidWoA-Gi')
		list.append('&youtube_pl=PLOgjrDemRWxKAYykYCyyHjhLg-AnVL_WJ')
		list.append('&youtube_pl=PLSMkCnnjbZ7DjWFUBHXHNt3y0PJ5XorXg') #כלי רכב
		list.append('&youtube_pl=PLlMf1oyFb61vBtkTBcfgcVaDzogYtVmG3') #כלי רכב
		
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir('-' + localize(33078),list,6,featherenceserviceicons_path + 'nextpage.png',"",'1',"", getAddonFanart(background, custom = "", default=background2))
	
def CATEGORIES108A(General_LanguageL, background, background2): #עמוד הבא ילדים ונוער
	'''עמוד הבא'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')

		
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
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
		list.append('&youtube_id=tHdRnmWMrXc') #RUCA AND YOUR FRIENDS
	
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
		list.append('&youtube_pl=PLuSa9BEmb98GaPSgf8KjNgpRH5Cjo2L4o') #Louis Anderson Cyrillic Series 1 Lui Andersoni Qartulad Seria 1
		list.append('&youtube_pl=') #
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir('-' + localize(33078),list,6,featherenceserviceicons_path + 'nextpage.png',"",'1',"", getAddonFanart(background, custom = "", default=background2))
	
def CATEGORIES109A(General_LanguageL, background, background2): #עמוד הבא לימוד שפה
	'''עמוד הבא'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		list.append('&youtube_id=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
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

	addDir('-' + localize(33078),list,6,featherenceserviceicons_path + 'nextpage.png',"",'1',"", getAddonFanart(background, custom = "", default=background2))

def CATEGORIES110A(General_LanguageL, background, background2): #עמוד הבא ?
	'''עמוד הבא'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		list.append('&youtube_id=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
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

	addDir('-' + localize(33078),list,6,featherenceserviceicons_path + 'nextpage.png',"",'1',"", getAddonFanart(background, custom = "", default=background2))
	
	

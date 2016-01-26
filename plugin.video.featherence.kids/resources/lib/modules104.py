#-*- coding: utf-8 -*-
import urllib,urllib2,sys,re,xbmcplugin,xbmcgui,xbmcaddon,xbmc,os

from variables import *
from shared_modules import *
if "plugin." in addonID: from shared_modules3 import *
'''---------------------------'''

#list.append('&youtube_pl=PL618DEA0E28636BC2') #Yu-Gi-Oh!
	
'''104'''
def CATEGORIES104B(General_LanguageL, background, background2): #פריקבוי וצ'אם צ'אם
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%f4%f8%e9%f7%e1%e5%e9%20%e5%f6%27%e0%ed%20%f6%27%e0%ed&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f1778310')
		list.append('&youtube_id=TpuVTMAktUc')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLRa0vFtcoHevRtQPnBJEJsq7WStrZhM5B') #S2
		list.append('&youtube_pl=PLhbx1Utemog4VPnw_UgSLs_gYZMTpXLE7')
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
		list.append('&youtube_pl=PL_nR8tuy6O1NuYIM2otOy7qSXw6Q81AY2')
	
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

	addDir(addonString(10762).encode('utf-8'),list,17,"https://upload.wikimedia.org/wikipedia/en/thumb/4/4d/Fanboy_and_Chum_Chum_logo.png/250px-Fanboy_and_Chum_Chum_logo.png",addonString(107620).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))

def CATEGORIES104C(General_LanguageL, background, background2): #פלאנט שין
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%f4%ec%e0%f0%e8%20%f9%e9%ef&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f1849206')
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLg5g_Q8udSqCaVqHfnIiHuVY_7DwkTTCz')
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

	addDir(addonString(10483).encode('utf-8'),list,17,"http://www.gasmangroup.com/blog/wp-content/uploads/2015/05/Trial-by-jerry-2.jpg",addonString(104830).encode('utf-8'),'1',"", getAddonFanart(background, custom="https://caua1000.files.wordpress.com/2012/10/sc1_1024.jpg", default=background2))

def CATEGORIES104D(General_LanguageL, background, background2): #ג'ימי ניוטרון
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%e2%27%e9%ee%e9%20%f0%e9%e5%e8%f8%e5%ef&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f1688219')
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLjDLgg_nO1v6cN1VUCVKfxPl1nVnTH8I8') #S1
		list.append('&youtube_pl=PLqP78Cshv1ykbs2x0zQm67wpSLauECvA0')
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

	addDir(addonString(10484).encode('utf-8'),list,17,"https://upload.wikimedia.org/wikipedia/en/thumb/7/71/The_Adventures_of_Jimmy_Neutron_Boy_Genius_logo.png/250px-The_Adventures_of_Jimmy_Neutron_Boy_Genius_logo.png",addonString(104840).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))

def CATEGORIES104E(General_LanguageL, background, background2): #משוגעגע
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%ee%f9%e5%e2%f2%e2%f2&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2802800')
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLB-ixs1gngUMEOU8Wx9j3Y5dpvo2igxkv') #S1
		list.append('&youtube_pl=PLa2x65y820ZQv_Zy8Iy5LE1oP4HyjVFkS')
		list.append('&youtube_pl=PLhdYefsmYuxacwKkayAxxtVnPEXF2QJuS')
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
		list.append('&youtube_pl=PLwLVa1RYGXSTOF3NpCLtuOJ3EFCQcMyjJ')
	
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

	addDir(addonString(10485).encode('utf-8'),list,17,"http://www.gifmania.co.uk/Animated-Cartoons-Animated-Gifs/Animated-Nickelodeon/Breadwinners/Breadwinners-91014.gif",addonString(104850).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://www.awn.com/sites/default/files/image/featured/1024064-season-two-breadwinners-lands-nickelodeon-april-5.jpg", default=background2))

def CATEGORIES104F(General_LanguageL, background, background2): #הנוקמים: לוחמי העל
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=module=http%3a%2f%2fwww.sdarot.wf%2fseries&url=all-heb')
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL3pJWvlMAbHh97E0hvpbEbhDcBE4o7prU') #S1
		list.append('&youtube_pl=PL3pJWvlMAbHhhgf91BsqiGochD6yhbXY1') #S2
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

	addDir(addonString(10488).encode('utf-8'),list,17,"https://upload.wikimedia.org/wikipedia/he/thumb/5/5a/Avengers_2010_animated.jpg/300px-Avengers_2010_animated.jpg",addonString(104880).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))

def CATEGORIES104G(General_LanguageL, background, background2): #מלחמת הכוכבים: המורדים
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1362&series_name=%d7%9e%d7%9c%d7%97%d7%9e%d7%aa%20%d7%94%d7%9b%d7%95%d7%9b%d7%91%d7%99%d7%9d%3a%20%d7%94%d7%9e%d7%95%d7%a8%d7%93%d7%99%d7%9d%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1362%2fstar-wars-rebels-%d7%9e%d7%9c%d7%97%d7%9e%d7%aa-%d7%94%d7%9b%d7%95%d7%9b%d7%91%d7%99%d7%9d-%d7%94%d7%9e%d7%95%d7%a8%d7%93%d7%99%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLgP379x--W4ZPG7KJzWD6XL0pNGen74a2') #S1
		list.append('&youtube_pl=PLsNE3pORizv4UHWlqw6gaHnjr-mXkSQXm') #S2
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
		list.append('&youtube_pl=PLuMhJMX4b4LkhwV82zgFZF8cF82zj5lKH')
		list.append('&youtube_pl=PL1s_GIH3XuCTp6tbyH-KQHy1DFjWmx-di')
	
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
		list.append('&youtube_pl=PLo-TJArWm5kl3btVopreshVetwb6i3SJt') #S1
		
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

	addDir(addonString(10489).encode('utf-8'),list,17,"http://www.sdarot.pm/media/series/1362.jpg",addonString(104890).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))

def CATEGORIES104H(General_LanguageL, background, background2): #צ'ימה
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLKMFPiSCwUk3rCsFi4mGgF0easITs__2x')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=ELR0T0TMLbvr0') #S1
		list.append('&youtube_pl=PLhZISbIWzxzV1PrTJ7ZmTF50YW5EtdmJQ') #S1
		list.append('&youtube_pl=PLUkmjfDR7bJDLsrKigF07CWxxxSlwXHuj')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=PLLOeGExLxyzM1KZs9gemhepkgxARklymE') #S1+
		
		list.append('&youtube_id=Jc_ciq8MMZU') #S2E2
		list.append('&youtube_id=OKs-XW3awNo') #S3E14
		
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
		list.append('&youtube_pl=PLiWp6bZu2PDZcvYdWx531a2K3dtBvVS4E') #S1
		list.append('&youtube_pl=')
	
	'''גאורגית'''
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''גרמנית'''
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=PL65bSKHWOkkVg217qDvVNZhnR-460066o') #S1
		list.append('&youtube_pl=')
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=PLt2K1Hf3IgJU27cpWJMxshDhgnN6NsCbH') #S1
		list.append('&youtube_pl=') #
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		pass
		
	
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
		list.append('&youtube_pl=PLQSB0bybEVzazUOx6Uhy5mBWeUMD6hT3u')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=9YaVNsFJ10g') #
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
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PL8MyJbCU5Mi6muRS3QWGFdS9nOQKeKH8S') #S1
		list.append('&youtube_pl=PL8MyJbCU5Mi4RA8hcBp6MjVE4xK6ixVid') #S2
		list.append('&youtube_pl=PLv36p3yPlGlzJc138BRYRwtChMPDkYNVx') #S
		
	
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
		list.append('&youtube_pl=PLAevrj2yKZu9PbEfkYpnpeoSBvilnEHFA')
		list.append('&youtube_pl=PLTdC8moEK00K0AYc1AU_0swh0yuCOHhjo')
		list.append('&youtube_pl=PLTdC8moEK00K0AYc1AU_0swh0yuCOHhjo')
		
		
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(10490).encode('utf-8'),list,17,'http://www.watchcartoononline.com/thumbs/Lego-Legends-of-Chima-Season-3-Episode-14-Wings-of-Fire.jpg',addonString(104900).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://www.wallpapersforkids.com/wallpapers/1920x1080/lego_legends_of_chima_1.jpg"))
	
def CATEGORIES104I(General_LanguageL, background, background2): #דובוני אכפת לי
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a4%d7%a8%d7%a7%d7%99%d7%9d%20%d7%9e%d7%9c%d7%90%d7%99%d7%9d&url=seasonId%3d2546390')
		list.append('&youtube_id=TxDBZPsgy8s')
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLR6qb6y-1e97omsW2P0imc3s3DErNPwtM') #S1
		list.append('&youtube_pl=PLLDPut200IH4bkrhnrMv-1ShRLovh5YK6') #S2
		list.append('&youtube_pl=PLXSlB4yMaoJsE2_cZ_OedM7ejD_FpZbEm') #S3
		list.append('&youtube_pl=PL7tKi5y0-xFz6CDbfLwemLkZ2EA2IGRu-')
		list.append('&youtube_pl=PLzIW2YAtLiqpcpKir638OHXUd5qt6llsG')
		
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=PLDFB56D1BBBA52FA7')
		list.append('&youtube_pl=PLo4DrcUVRBS5EluLbm0el6X0OS4UNY64T')
	
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
		list.append('&youtube_pl=PLB83493E6106A1B3A')
		list.append('&youtube_pl=PL3AB0BEED0A9291CD')
		list.append('&youtube_pl=PL3AB0BEED0A9291CD')
	
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
		list.append('&youtube_pl=PL9BFEB552FFEE2B74')
		list.append('&youtube_pl=PLk9ejlY4-zeLBPv4_mNX9Zu7V-1hDK3w2')
		
	
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

	addDir(addonString(10623).encode('utf-8'),list,17,'http://vignette4.wikia.nocookie.net/carebears/images/e/e5/Take_Care_Bear.jpg/revision/latest?cb=20120405172827',addonString(106230).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://7-themes.com/data_images/out/67/7001447-care-bears.jpg"))

def CATEGORIES104J(General_LanguageL, background, background2): #נילס הולגרסון
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=713&series_name=%d7%a0%d7%99%d7%9c%d7%a1%20%d7%94%d7%95%d7%9c%d7%92%d7%a8%d7%a1%d7%95%d7%9f%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f713%2fthe-wonderful-adventures-of-nils-%d7%a0%d7%99%d7%9c%d7%a1-%d7%94%d7%95%d7%9c%d7%92%d7%a8%d7%a1%d7%95%d7%9f-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PL_8KXLhQVQMKVZInMgWpGe9osYlO5lcBa') #Hebrew
		list.append('&youtube_pl=PLwXEsK85wc0NYyg8whoBrNpRznTV7r1vP') #Hebrew
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
		list.append('&youtube_pl=PL5xXAWMbhAtlp-Vsrgo5lknESnpIMdrvG') #German
		list.append('&youtube_pl=PL-CILcssSDKHF1X4RVHoVINov3ncHiYGx') #German
	
	'''דנית'''
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=PLwSzDIvrlKomOp7zAfJwAbYweV1Tn2w0a') #Dutch
	
	'''הונגרית'''
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=PLE2498963634F01D0') #Hungarian
	
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
		list.append('&youtube_pl=PL8XovLToH9hYd1Yo6gehiq6xiT4fodI3m')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PL23B942DCBE599DBF') #French
		list.append('&youtube_pl=PLBC31B0EF15725285') #French
		list.append('&youtube_pl=PL-_HUSbX6NgQ--_qCJzdFifgsADfDLkST') #French
	
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

	addDir(addonString(10468).encode('utf-8'),list,17,'http://www.sratim.co.il/contents/series/images/IL/2072.jpg',addonString(104680).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))

def CATEGORIES104K(General_LanguageL, background, background2): #סיפורי מוש
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL9mJOYidEPhoUg_j1fwald53hRuM0hOuc') #סיפורי מוש
		
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=PLz_WViLi_Q3e4erK7Ko4w7iZh3vLcQa_t') #סיפורי מוש
	
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
		list.append('&youtube_pl=PL8rtSe8ySfcvUFWHEK7VHNbECKbDxMsou')
		
	'''הודית'''
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''הולנדית'''
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=PL8rtSe8ySfcvUFWHEK7VHNbECKbDxMsou') #סיפורי מוש
	
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
		list.append('&youtube_pl=PLF803EED0CFFE413A') #סיפורי מוש
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=PLnM6FRWnL-PK-tcWDmrKMkSX7dTW6wZDl')
	
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
		list.append('&youtube_pl=PLp5RH-yn0Nvg4Ujl1c---UJrX5reJd8cS')
	
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

	addDir(addonString(10491).encode('utf-8'),list,17,'http://www.m4e.de/media/2014/09/SG_9a_4-530x357.jpg',addonString(104910).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://datas.series-tv-shows.com/pic/tvdb/12063/fanart.jpg"))

def CATEGORIES104L(General_LanguageL, background, background2): #אגדות האחים גרים
	'''סדרות'''
	thumb = 'https://upload.wikimedia.org/wikipedia/en/thumb/6/6c/Gftc.jpg/220px-Gftc.jpg'
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		
		list.append('&youtube_pl=PLYlrzbISBfkuyDzUwktkKJ8ecy-RZ3AHI') #S1
		list.append('&youtube_pl=PLYlrzbISBfktPBUHxCckXbRxD6KkCapzu') #S2
		list.append('&youtube_pl=PLmNjn7uj9TQUxjlYuWFN0RZg1RUUfu9SG') #Hebrew
		list.append('&youtube_pl=PLxd2PvjbApyUmvVaMyQsaiqJnu4tultQw') #Hebrew
		
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLE918DC6AFF74BBD3')
		list.append('&youtube_pl=')
		
	'''אוזבקית'''
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''איטלקית'''
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=PL1A36687F1D0E073E')
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
		list.append('&youtube_pl=PL9A89EE24241DACF2')
	
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
		list.append('&youtube_pl=PLC3D9DAFFB4D8323B')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=PL84F67208407C7AC3')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		thumb = 'https://upload.wikimedia.org/wikipedia/ar/9/97/%D9%81%D9%8A_%D8%AC%D8%B9%D8%A8%D8%AA%D9%8A_%D8%AD%D9%83%D8%A7%D9%8A%D8%A9.gif'
		list.append('&youtube_pl=PLanXyg33qZLG3QByLzH9W3dkgC8DCXdhS')
	
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
	
	addDir(addonString(10499).encode('utf-8'),list,17,thumb,addonString(104990).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))

def CATEGORIES104M(General_LanguageL, background, background2): #סאקורה לוכדת הקלפים
	'''סדרות'''
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
		list.append('&youtube_pl=PLI6L7wB4bdu30OZnsJosHpBK5E2W_NkbA')
	
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

	addDir(addonString(10498).encode('utf-8'),list,17,"https://upload.wikimedia.org/wikipedia/en/thumb/5/50/Cardcaptor_Sakura_vol1_cover.jpg/230px-Cardcaptor_Sakura_vol1_cover.jpg",addonString(104980).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))

def CATEGORIES104N(General_LanguageL, background, background2): #נינג'גו - מאסטר הספינג'יצו
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1820&series_name=%d7%a0%d7%99%d7%a0%d7%92%27%d7%92%d7%95%20-%20%d7%9e%d7%90%d7%a1%d7%98%d7%a8%20%d7%94%d7%a1%d7%a4%d7%99%d7%a0%d7%92%27%d7%99%d7%a6%d7%95%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%20%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1820%2fninjago-masters-of-spinjitzu-%d7%a0%d7%99%d7%a0%d7%92-%d7%92%d7%95-%d7%9e%d7%90%d7%a1%d7%98%d7%a8-%d7%94%d7%a1%d7%a4%d7%99%d7%a0%d7%92-%d7%99%d7%a6%d7%95-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=')
	
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL5833BFE67466AE31') #English
		list.append('&youtube_pl=PLs20ZA0q4gQCBBKghE6rUuVL9VsvVBqvA') #English
		list.append('&dailymotion_pl=x3ul0k') #S1
		list.append('&dailymotion_pl=x43uhy') #S2
		if not 'Hebrew' in General_LanguageL:
			list.append('&youtube_pl=ELmWM3zMzLY3I') #S1
			list.append('&youtube_pl=ELGbD9SrC9H3Y') #S2
			list.append('&youtube_pl=ELWhYHdg_CkvY') #S3
			list.append('&youtube_pl=PLs20ZA0q4gQCBBKghE6rUuVL9VsvVBqvA') #S4
			list.append('&youtube_pl=ELPq2ykMpt2mLsPSg0c1rFOQ') #S4
			list.append('&youtube_pl=EL8Ms60ICex7TzF-_0x9hoqg') #S5
			
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
		list.append('&youtube_pl=PL2axIq3IX4USVUXhZuE9ZqPLqccTqlpTj') #
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=PLx3f1q8-kngmvAuHjYhfAayGn9QgV8Ngp') #
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLNqK12R0zSvTt3eq256TuCxfq7SClHu9p') #
		list.append('&youtube_pl=PLMD5TcWgUOO7FuRhuD_fTDuGMXCg3rb9Y') #
		list.append('&youtube_pl=') #
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=PL5peNfSV4E_DjFWUtD23GR54c40LkOY5z') #
	
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
		list.append('&youtube_pl=PL7qJy8wXdrSjulrGwV3dVrbO5dNl1NG5g') #
	
	'''רוסית'''
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')

	addDir(addonString(10479).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1820.jpg',addonString(104790).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://s1.dmcdn.net/KJt5P/1280x720-F13.jpg"))

def CATEGORIES104O(General_LanguageL, background, background2): #אוטובוס הקסמים
	'''סדרות'''
	thumb = 'https://upload.wikimedia.org/wikipedia/en/thumb/e/e8/The_Magic_School_Bus_title_credit.jpg/220px-The_Magic_School_Bus_title_credit.jpg'
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		thumb = 'http://www.sdarot.pm/media/series/1032.jpg'
		list.append('&sdarot=season_id=1&series_id=1032&series_name=%d7%90%d7%95%d7%98%d7%95%d7%91%d7%95%d7%a1%20%d7%94%d7%a7%d7%a1%d7%9e%d7%99%d7%9d%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1032%2fthe-magic-school-bus-%d7%90%d7%95%d7%98%d7%95%d7%91%d7%95%d7%a1-%d7%94%d7%a7%d7%a1%d7%9e%d7%99%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=PLojgGSYuCHTB2q0TvkcGuhKteg3hNsZle')
		list.append('&youtube_pl=')
		
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLgeJ6bGP6EDkHog7QpPxB8EcsFTjnl8Ut')
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
		list.append('&youtube_pl=PLt6wYMdXCggoOQDo5tn33e40Hbd5taQFy')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_id=SmOwM4DHaTc')
	
	'''פורטוגזית'''
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פינית'''
	if 'Finnish' in General_LanguageL:
		list.append('&youtube_pl=')

	'''ערבית'''
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=PL21Max3krxq_L7bvKLVa0u21t4dGHXImT')
	
	'''צ'כית'''
	if 'Czech' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		
	'''צרפתית'''
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PLE8_AKSaJse9_IzmzI6GWKkmmBwlDANoN')
	
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
		thumb = 'https://upload.wikimedia.org/wikipedia/ru/thumb/7/7a/%D0%92%D0%BE%D0%BB%D1%88%D0%B5%D0%B1%D0%BD%D1%8B%D0%B9_%D1%88%D0%BA%D0%BE%D0%BB%D1%8C%D0%BD%D1%8B%D0%B9_%D0%B0%D0%B2%D1%82%D0%BE%D0%B1%D1%83%D1%81_%28%D0%BF%D0%BE%D1%81%D1%82%D0%B5%D1%80%29.jpg/250px-%D0%92%D0%BE%D0%BB%D1%88%D0%B5%D0%B1%D0%BD%D1%8B%D0%B9_%D1%88%D0%BA%D0%BE%D0%BB%D1%8C%D0%BD%D1%8B%D0%B9_%D0%B0%D0%B2%D1%82%D0%BE%D0%B1%D1%83%D1%81_%28%D0%BF%D0%BE%D1%81%D1%82%D0%B5%D1%80%29.jpg'
		list.append('&youtube_pl=PL4uSs79W8jWvYsux3wxN97wLHdJ-LP-pf')
	
	'''שוודית'''
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=')
		
	'''תאילנדית'''
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=')
	
	addDir(addonString(10403).encode('utf-8'),list,17,thumb,addonString(104030).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://ecx.images-amazon.com/images/I/71HZ-fXNyYL._SL1094_.jpg", default=background2))

def CATEGORIES104P(General_LanguageL, background, background2): #דיגימון [אוסף]
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLKMFPiSCwUk2AWPSN0CngtMfiB8oFWZwX')
		list.append('&youtube_pl=PLk98jt4ayAVJr26ugq6oAD6j0QjfVxSGD')
		list.append('&youtube_pl=PLKMFPiSCwUk3S3KtIMAOv83IiRQNgHp7T') #Fusion S1E1-5
		list.append('&youtube_pl=PLKMFPiSCwUk3nYihy4qmImPx17sQHYF88') #Frontier S1E1-3
		 
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLsUxWIZFayHW37hhKAaOaeD2zyw0-ILsO') #S1
		list.append('&youtube_id=VtQtElW7CqQ') #S1E19-27
		list.append('&youtube_pl=PLXSH0wBFP4_EYuu7mamD67KEffWoh1o3k') #S2
		
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

	addDir(addonString(10416).encode('utf-8') + space + '[Collection]',list,17,'http://forumsgallery.tapuz.co.il/ForumsGallery/galleryimages/medium/453gallery_13767.gif',addonString(104160).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://static.zerochan.net/Digimon.full.1707809.jpg", default=background2))

def CATEGORIES104Q(General_LanguageL, background, background2): #סיילור מון
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=548&series_name=%d7%a1%d7%99%d7%99%d7%9c%d7%95%d7%a8%20%d7%9e%d7%95%d7%9f%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f548%2fsailor-moon-%d7%a1%d7%99%d7%99%d7%9c%d7%95%d7%a8-%d7%9e%d7%95%d7%9f-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLsg4IBMPLqMTJVTYNvRMz5ZP7_q6HH0E4') #Hebrew
		list.append('&youtube_pl=PLFt-xe6eTY8MwVS7xZi9bq9nMZg5b4ClL') #Hebrew
		list.append('&youtube_pl=')
		
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLA2A7425252E73586') #English
		list.append('&youtube_pl=PL37753E7A32DB1E38') #English #http://ib.huluim.com/show_key_art/18617?size=1600x600
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
		list.append('&youtube_id=wf-owQJJwG0')
		list.append('&youtube_id=q0pnbuHIBHI')
	
	'''סינית'''
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''סלובקית'''
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''ספרדית'''
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLHXYIWG5iMqZ5i5rHzR-vCoVpnZCyllbb') #Spanish
		list.append('&youtube_pl=')
	
	'''סרבית'''
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=')
	
	'''פולנית'''
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=PLINgVpX-p-GIefI8KNsLMoOQ7Qp-0ygMZ')
		list.append('&youtube_pl=PL0C04B8D69D8C4394') #S2
	
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
	
	addDir(addonString(10472).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/548.jpg',addonString(104720).encode('utf-8'),'1',"",getAddonFanart(background, custom="http://vignette3.wikia.nocookie.net/sailormoon/images/7/77/Sailor_moon_crystal_04_rei_usagi_and_ami_as_princesses.jpg/revision/latest?cb=20140818191116", default=background2))

def CATEGORIES104R(General_LanguageL, background, background2): #דראגון בול
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1815&series_name=%d7%93%d7%a8%d7%92%d7%95%d7%9f%20%d7%91%d7%95%d7%9c%20-%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1815%2fdragon-ball-%d7%93%d7%a8%d7%92%d7%95%d7%9f-%d7%91%d7%95%d7%9c-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=')
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLIEbITAtGBebWGyBZQlkiMXwt30WqG9Bd')
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
		list.append('&youtube_pl=PLHwX4SWGT6V6fnZVv1W24dTqnb2CtOAs6')
	
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

	addDir(addonString(10528).encode('utf-8'),list,17,"https://upload.wikimedia.org/wikipedia/en/c/c9/DB_Tank%C5%8Dbon.png",addonString(105280).encode('utf-8'),'1',"", getAddonFanart(background, custom="https://images-eds-ssl.xboxlive.com/image?url=8Oaj9Ryq1G1_p3lLnXlsaZgGzAie6Mnu24_PawYuDYIoH77pJ.X5Z.MqQPibUVTcgjkDHLJ4ACWCtBhZH26FgKJLYIRdxB78cQ4q6IF.U6653o1OT0agXq5.ZnKCFmU7bvbHELaozXVCQOViok21vpwKKwwrQbrXZb50ko8.OCSJKpL0ME9m.Tr7mQarxYUJ5ObQh.j88cLczQdiHbaO0hGXBnXon57ycbQ._bgfuFI-&format=jpg", default=background2))

def CATEGORIES104S(General_LanguageL, background, background2): #דראגון בול Z
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=293&series_name=%d7%93%d7%a8%d7%92%d7%95%d7%9f%20%d7%91%d7%95%d7%9c%20%d7%96%d7%99%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f293%2fdragon-ball-z-%d7%93%d7%a8%d7%92%d7%95%d7%9f-%d7%91%d7%95%d7%9c-%d7%96%d7%99-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLzPOIgqAmUxsr8WjTdDiNvgIjzOqwwD1O')
		list.append('&youtube_pl=PL6E0EE345D513F341')
		
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLIEbITAtGBeYy4Gi9gSZT0GKXndtWEVev')
		list.append('&youtube_pl=PLWyJiIUfiUwW_l0E_mD8yumdQ6W9yGJpc')
		list.append('&youtube_pl=PLIEbITAtGBeZ4DNOjaALTh8jDLn8_L4Pa')
		list.append('&youtube_pl=PLIEbITAtGBeZCo9HFoiPSRgrMvyynBy8R')
		
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
		list.append('&youtube_pl=PL7yHJ1OH2RFJvXpnEsBEgLqDprSWuS5rU')
		list.append('&youtube_pl=PL531Q7zcnaMa3lz0rvu5nm4qC5IZb7Zlo')
	
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

	addDir(addonString(10528).encode('utf-8') + space + 'Z',list,17,"http://www.sdarot.pm/media/series/293.jpg",addonString(105280).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://www.technobuffalo.com/wp-content/uploads/2015/10/Dragon-Ball-Z-Extreme-Budoten.jpg", default=background2))

def CATEGORIES104T(General_LanguageL, background, background2): #דראגון בול S
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1813&series_name=%d7%93%d7%a8%d7%92%d7%95%d7%9f%20%d7%91%d7%95%d7%9c%20%d7%a1%d7%95%d7%a4%d7%a8%20-%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1813%2fdragon-ball-super-%d7%93%d7%a8%d7%92%d7%95%d7%9f-%d7%91%d7%95%d7%9c-%d7%a1%d7%95%d7%a4%d7%a8-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
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
		list.append('&youtube_pl=PLyc2dFYhZECbcZP_64xKT5rN4Sgc3S7Er') #SUB
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

	addDir(addonString(10528).encode('utf-8') + space + 'S',list,17,"http://www.sdarot.pm/media/series/1813.jpg",addonString(105280).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://iheartcartoon.com/wp-content/uploads/2015/09/dragon-ball-super-poster-570x805.0.0.jpg", default=background2))

def CATEGORIES104U(General_LanguageL, background, background2): #דראגון בול GT
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=531&series_name=%d7%93%d7%a8%d7%92%d7%95%d7%9f%20%d7%91%d7%95%d7%9c%20%d7%92%27%d7%99%20%d7%98%d7%99%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f531%2fdragon-ball-gt-%d7%93%d7%a8%d7%92%d7%95%d7%9f-%d7%91%d7%95%d7%9c-%d7%92-%d7%99-%d7%98%d7%99-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=')
		
	'''אנגלית'''
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLIEbITAtGBearIZ38rXEGiqv-HYtpqFE3')
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
		list.append('&youtube_pl=PLbwudPzS-K_rGz8-m6CE_4oXBWrCnXgm7')
	
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

	addDir(addonString(10528).encode('utf-8') + space + 'GT',list,17,"http://www.sdarot.pm/media/series/1552.jpg",addonString(105280).encode('utf-8'),'1',"", getAddonFanart(background, custom="https://i.ytimg.com/vi/ojTY3lhlieo/maxresdefault.jpg", default=background2))

def CATEGORIES104V(General_LanguageL, background, background2): #דראגון בול K
	'''סדרות'''
	list = []
	
	'''עברית'''
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1275&series_name=%d7%93%d7%a8%d7%92%d7%95%d7%9f%20%d7%91%d7%95%d7%9c%20%d7%a7%d7%90%d7%99%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1275%2fdragon-ball-kai-%d7%93%d7%a8%d7%92%d7%95%d7%9f-%d7%91%d7%95%d7%9c-%d7%a7%d7%90%d7%99-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
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

	addDir(addonString(10528).encode('utf-8') + space + 'K',list,17,"http://www.sdarot.pm/media/series/1275.jpg",addonString(105280).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))

def CATEGORIES104W(General_LanguageL, background, background2): #
	'''סדרות'''
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

	addDir(addonString(104980).encode('utf-8'),list,17,"",addonString(104980).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))

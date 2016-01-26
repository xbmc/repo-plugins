# -*- coding: utf-8 -*-
import urllib,urllib2,sys,re,xbmcplugin,xbmcgui,xbmcaddon,xbmc,os

from variables import *
from shared_modules import *
if "plugin." in addonID: from shared_modules3 import *
from modules101 import *
from modules102 import *
from modules104 import *
from modules106 import *
from modules107 import *
from modules108 import *
from modules109 import *
from modulesZ import *
from modulesA import *
'''---------------------------'''
	
def CATEGORIES():
	'''------------------------------
	---MAIN--------------------------
	------------------------------'''
	try: General_Language = getsetting('General_Language')
	except: General_Language = systemlanguage
	
	CATEGORIES_SEARCH(mode=30, url="")
	addDir('-' + addonString(100).encode('utf-8'),'',100,featherenceserviceicons_path + 'star.png',addonString_servicefeatherence(32800).encode('utf-8'),'1',50, getAddonFanart(100, urlcheck_=True)) #My Kids
	
	addDir(addonString(101).encode('utf-8'),'',101,featherenceserviceicons_path + 'music.png',addonString(1010).encode('utf-8'),'1',58, getAddonFanart(101, default="http://p1.pichost.me/i/28/1509965.jpg", urlcheck_=True)) #SONGS AND STORIES
	addDir(addonString(102).encode('utf-8'),'',102,featherenceserviceicons_path + 'bank.png',addonString(1020).encode('utf-8'),'1',58, getAddonFanart(102, default="http://2.bp.blogspot.com/-Dz3-VwZZryE/Uh5ZXg7zCMI/AAAAAAAAdCQ/OmLVkdWI47c/s1600/Disney+Junior+Live+Pirate+and+Princess+Adventure+-+Jake%252C+Izzy+%2526+Cubby.jpg", urlcheck_=True)) #SHOWS
	addDir(addonString(104).encode('utf-8'),'',104,featherenceserviceicons_path + 'tvshows.png',addonString(1040).encode('utf-8'),'1',2, getAddonFanart(104, default="http://www.canadiananimationresources.ca/wp-content/uploads/2012/10/9-Story-Arthur-Couch.jpg", urlcheck_=True)) #TV SHOWS
	addDir(addonString(105).encode('utf-8'),'',105,featherenceserviceicons_path + 'movies.png',addonString(1050).encode('utf-8'),'1',1, getAddonFanart(105, default="http://4.bp.blogspot.com/-Af2HcIQzlg8/UhwQ8lKPucI/AAAAAAAACIA/d7aY4RrxUfk/s1600/bambi-friends-disney-animated-movie-photo.jpg", urlcheck_=True)) #MOVIES
	addDir(addonString(106).encode('utf-8'),'',106,featherenceserviceicons_path + 'toddlers.png',addonString(1060).encode('utf-8'),'1',58, getAddonFanart(106, default="http://1.bp.blogspot.com/-MnUXpmW1n1M/UKfOgAXUmXI/AAAAAAAAbBY/BfoQ1FNgNUk/s1600/duvcar1024x768_en_27.jpg", urlcheck_=True)) #Toddlers
	addDir(addonString(107).encode('utf-8'),'',107,featherenceserviceicons_path + 'kids.png',addonString(1070).encode('utf-8'),'1',58, getAddonFanart(107, default="http://7-themes.com/data_images/out/63/6986632-dora-wallpaper-free.jpg", urlcheck_=True)) #Tiny
	addDir(addonString(108).encode('utf-8'),'',108,featherenceserviceicons_path + 'kids2.png',addonString(1080).encode('utf-8'),'1',50, getAddonFanart(108, default="http://30k0u22sosp4xzag03cfogt1.wpengine.netdna-cdn.com/wp-content/uploads/2015/03/strika-3.jpg", urlcheck_=True)) #Kids and Young
	addDir(addonString(109).encode('utf-8'),'',109,featherenceserviceicons_path + 'ud.png',addonString(1090).encode('utf-8'),'1',50, getAddonFanart(109, default="", urlcheck_=True)) #Learn Language
	addDir(addonString(200).encode('utf-8') % (General_Language),'',200,featherenceserviceicons_path + 'ud.png','[COLOR=red]1: %s | 2: %s | 3: %s[/COLOR]' % (General_Language, General_Language2, General_Language3) + '[CR]' + addonString_servicefeatherence(32081).encode('utf-8'),'1',50, getAddonFanart(200, urlcheck_=True)) #Forigen Language

	#addDir('קלסיקלטת','plugin://plugin.video.wallaNew.video/?mode=1&module=338&name=קלסיקלטת&url=http://vod.walla.co.il/channel/338/clasicaletet',8,'https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcTYE2VT8CR2O31MsqAhdaydYrqrCD--HCCdGcs7blBn3Zh92Kwq','','1',"", getAddonFanart(0))
	#addDir('ניק','plugin://plugin.video.wallaNew.video/?mode=1&module=nick&name=ניק&url=http://nick.walla.co.il/',8,'http://www.karmieli.co.il/sites/default/files/images/nico.jpg','','1',"", getAddonFanart(0))
	#addDir('גוניור','plugin://plugin.video.wallaNew.video/?mode=1&module=nickjr&name=גוניור&url=http://nickjr.walla.co.il/',8,'http://upload.wikimedia.org/wikipedia/he/1/19/%D7%A2%D7%A8%D7%95%D7%A5_%D7%92%27%D7%95%D7%A0%D7%99%D7%95%D7%A8.jpg','','1',"", getAddonFanart(0))

def CATEGORIES100(name, iconimage, desc, fanart):
	'''------------------------------
	---My-Kids-----------------------
	------------------------------'''
	fanart = 100
	
	'''כפתור הילדים שלי חדש..'''
	addDir(addonString_servicefeatherence(86).encode('utf-8') % (addonString(100).encode('utf-8')),"New",20,featherenceserviceicons_path + 'clipboard.png',addonString_servicefeatherence(87).encode('utf-8') + addonString_servicefeatherence(88).encode('utf-8') + addonString_servicefeatherence(89).encode('utf-8'),'s',50, getAddonFanart(fanart, urlcheck_=True))
		
	'''רשימת השמעה 1'''
	if Custom_Playlist1_ID != "": addDir(Custom_Playlist1_Name,Custom_Playlist1_ID,18,Custom_Playlist1_Thumb,Custom_Playlist1_Description,'1',50, getAddonFanart("Custom_Playlist1", urlcheck_=True))
	'''רשימת השמעה 2'''
	if Custom_Playlist2_ID != "": addDir(Custom_Playlist2_Name,Custom_Playlist2_ID,18,Custom_Playlist2_Thumb,Custom_Playlist2_Description,'2',50, getAddonFanart("Custom_Playlist2", urlcheck_=True))
	'''רשימת השמעה 3'''
	if Custom_Playlist3_ID != "": addDir(Custom_Playlist3_Name,Custom_Playlist3_ID,18,Custom_Playlist3_Thumb,Custom_Playlist3_Description,'3',50, getAddonFanart("Custom_Playlist3", urlcheck_=True))
	'''רשימת השמעה 4'''
	if Custom_Playlist4_ID != "": addDir(Custom_Playlist4_Name,Custom_Playlist4_ID,18,Custom_Playlist4_Thumb,Custom_Playlist4_Description,'4',50, getAddonFanart("Custom_Playlist4", urlcheck_=True))
	'''רשימת השמעה 5'''
	if Custom_Playlist5_ID != "": addDir(Custom_Playlist5_Name,Custom_Playlist5_ID,18,Custom_Playlist5_Thumb,Custom_Playlist5_Description,'5',50, getAddonFanart("Custom_Playlist5", urlcheck_=True))
	'''רשימת השמעה 6'''
	if Custom_Playlist6_ID != "": addDir(Custom_Playlist6_Name,Custom_Playlist6_ID,18,Custom_Playlist6_Thumb,Custom_Playlist6_Description,'6',50, getAddonFanart("Custom_Playlist6", urlcheck_=True))
	'''רשימת השמעה 7'''
	if Custom_Playlist7_ID != "": addDir(Custom_Playlist7_Name,Custom_Playlist7_ID,18,Custom_Playlist7_Thumb,Custom_Playlist7_Description,'7',50, getAddonFanart("Custom_Playlist7", urlcheck_=True))
	'''רשימת השמעה 8'''
	if Custom_Playlist8_ID != "": addDir(Custom_Playlist8_Name,Custom_Playlist8_ID,18,Custom_Playlist8_Thumb,Custom_Playlist8_Description,'8',50, getAddonFanart("Custom_Playlist8", urlcheck_=True))
	'''רשימת השמעה 9'''
	if Custom_Playlist9_ID != "": addDir(Custom_Playlist9_Name,Custom_Playlist9_ID,18,Custom_Playlist9_Thumb,Custom_Playlist9_Description,'9',50, getAddonFanart("Custom_Playlist9", urlcheck_=True))
	'''רשימת השמעה 10'''
	if Custom_Playlist10_ID != "": addDir(Custom_Playlist10_Name,Custom_Playlist10_ID,18,Custom_Playlist10_Thumb,Custom_Playlist10_Description,'10',50, getAddonFanart("Custom_Playlist10", urlcheck_=True))
	
	'''מעודפים'''
	addDir(localize(1036),"",32,featherenceserviceicons_path + 'star.png','','1',50, getAddonFanart(fanart, urlcheck_=True))
	
'''1=SONGS, 2=SHOWS, 3=LITTLE, 4=TVSHOWS, 5=MOVIES, 6=?, 7=BABY, 8=?, 9=OTHERS'''

def CATEGORIES101(name, iconimage, desc, fanart):
	background = 101
	background2 = "" #http://p1.pichost.me/i/28/1509965.jpg"
	
	CATEGORIES_RANDOM() #אקראי
	CATEGORIES101Z(General_LanguageL, background, background2) #ערוצי טלוויזיה
	CATEGORIES101B(General_LanguageL, background, background2) #השירים הראשונים שלי
	CATEGORIES101C(General_LanguageL, background, background2) #שירי ילדים
	CATEGORIES101D(General_LanguageL, background, background2) #שירי לילה טוב
	CATEGORIES101E(General_LanguageL, background, background2) #שירי דיסני
	CATEGORIES101I(General_LanguageL, background, background2) #אוסף סיפורים
	CATEGORIES101M(General_LanguageL, background, background2) #חגים
	
	
	'''עכבר העיר ועכבר הכפר'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1618&series_name=%d7%a2%d7%9b%d7%91%d7%a8%20%d7%94%d7%a2%d7%99%d7%a8%20%d7%95%d7%a2%d7%9b%d7%91%d7%a8%20%d7%94%d7%9b%d7%a4%d7%a8%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1618%2fthe-country-mouse-and-the-city-mouse-adventures-%d7%a2%d7%9b%d7%91%d7%a8-%d7%94%d7%a2%d7%99%d7%a8-%d7%95%d7%a2%d7%9b%d7%91%d7%a8-%d7%94%d7%9b%d7%a4%d7%a8-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL33796B8BB9BE81AD') #English
		list.append('&youtube_pl=PL33796B8BB9BE81AD') #English
		list.append('&youtube_id=C90qaiNDWFA') #English
	addDir(addonString(10176).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1618.jpg',addonString(101760).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''אוסף דיג דיג דוג'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom4=plugin://plugin.video.wallaNew.video/?url=item_id%3D2565012&mode=10&name=דיג דיג דוג: שלוש ארבע לעבודה&module=wallavod')
		list.append('&youtube_id=cRPDgeKNP3s') #דיג דיג דוג 1
		list.append('&youtube_id=2lKQWaQZ4f8') #דיג דיג דוג 3
		list.append('&youtube_id=Cz_zw8yKurM') #דיג דיג דוג לפעוטות
		list.append('&youtube_id=j-53oVXHwlA') #דיג דיג דוג שלוש ארבע לעבודה
	addDir('אוסף דיג דיג דוג',list,17,'','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''עץ השירים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&wallaNew=item_id%3D2538763')
		list.append('&wallaNew=item_id%3D2538765')
		list.append('&wallaNew=item_id%3D2538766')
		list.append('&wallaNew=item_id%3D2538767')
		list.append('&wallaNew=item_id%3D2538768')
	addDir('עץ השירים',list,17,'','','1',50,getAddonFanart(background, custom="", default=background2))

	'''שירי דתיה בן דור''' 
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL1m90DJcwEbQmbZ8QLo3JCMs38VyioavB')
		list.append('&youtube_pl=PL1m90DJcwEbQmbZ8QLo3JCMs38VyioavB')
		list.append('&youtube_pl=PLAZEBF7w1an9tqCwiQ7rYI8kB2RY1sU7x')
	addDir(addonString(4).encode('utf-8') + space + addonString(10112).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Datia_ben_dor_%D7%93%D7%AA%D7%99%D7%94_%D7%91%D7%9F_%D7%93%D7%95%D7%A8.jpg/250px-Datia_ben_dor_%D7%93%D7%AA%D7%99%D7%94_%D7%91%D7%9F_%D7%93%D7%95%D7%A8.jpg',addonString(101120).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''שירי עוזי חיטמן''' 
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&wallaNew=item_id%3D2538763')
		list.append('&youtube_pl=PLB58E216840771949')
		list.append('&youtube_pl=PL0145D27A0D5E1810')
		list.append('&youtube_pl=PLC740DFBAF8C3F893')
		list.append('&youtube_id=YMLsE_DMPGQ')
		list.append('&youtube_id=21zlKTnPBcU')
	addDir(addonString(10103).encode('utf-8'),list,17,'http://www.lifemusic.co.il/files/singers/big/1248883756s56Ly.jpg',addonString(101030).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''שירי פרפר נחמד'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL51YAgTlfPj45OPEXI-ibfJy8ON0k1ARh')
		list.append('&youtube_pl=PLNWPkdPqwKqtbM6--m50SdENigIXvoAqm') 
	addDir(addonString(10105).encode('utf-8'),list,17,'http://www.sdarot.wf/media/series/1092.jpg',addonString(101050).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''שירי מיכל כלפון'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLPWc8VdaIIsAHPacvuyNfA-y8VSxoh4or')
		list.append('&youtube_pl=PL9boemkB6hYz5WlmI-QH_xmRyZDpHKvt9')
	addDir(addonString(10768).encode('utf-8'),list,17,'http://yt3.ggpht.com/-4Rd1GQEZnaM/AAAAAAAAAAI/AAAAAAAAAAA/pfQtiUaNjng/s88-c-k-no/photo.jpg',addonString(107680).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''סיפורי דתיה בן דרור''' 
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLAZEBF7w1an9Evjuibug2h-g0CDGvrJGX')
		list.append('&youtube_id=x9rGd_SVleE')
		list.append('&youtube_id=Si6x12FUdoA')
		list.append('&youtube_id=PH5lD8FpVqM')
		
	addDir(addonString(3).encode('utf-8') + space + addonString(10112).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Datia_ben_dor_%D7%93%D7%AA%D7%99%D7%94_%D7%91%D7%9F_%D7%93%D7%95%D7%A8.jpg/250px-Datia_ben_dor_%D7%93%D7%AA%D7%99%D7%94_%D7%91%D7%9F_%D7%93%D7%95%D7%A8.jpg',addonString(101120).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''שירי ענבלי בא לי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLPWc8VdaIIsAHPacvuyNfA-y8VSxoh4or')
	addDir(addonString(10106).encode('utf-8'),list,17,'http://www.tel-aviv.gov.il/ToEnjoy/CulterAndArts/DocLib4/inbali.jpg.jpg',addonString(101060).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES101J(General_LanguageL, background, background2) #סיפורי התנ"ך
	
	'''סיפורי סבא טוביה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL6jaO-hu0IvwHsU9bzS8caFo8reAxEseX')
		list.append('&youtube_pl=PLHq0SR_JzssA6InY1XROQZ6TfqV3KbOfE')
	addDir(addonString(3).encode('utf-8') + space + addonString(10108).encode('utf-8'),list,17,'http://images.mouse.co.il/storage/2/e/b-saba.jpg',addonString(101080).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES101A(General_LanguageL, background, background2) #עמוד הבא שירים וסיפורים
	
def CATEGORIES102(name, iconimage, desc, fanart):
	background = 102
	background2 = "" #http://2.bp.blogspot.com/-Dz3-VwZZryE/Uh5ZXg7zCMI/AAAAAAAAdCQ/OmLVkdWI47c/s1600/Disney+Junior+Live+Pirate+and+Princess+Adventure+-+Jake%252C+Izzy+%2526+Cubby.jpg"
	
	CATEGORIES_RANDOM() #אקראי
	CATEGORIES102Z(General_LanguageL, background, background2) #ערוצי טלוויזיה
	
	'''101 כלבים דלמטים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=RxMNt87ghsQ')
	addDir(addonString(10202).encode('utf-8'),list,5,'http://www.pashbar.co.il/pictures/show_big_0712083001297352431.jpg',addonString(102020).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''Pantomime Collections'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_id=6CSJWnljAiA') #Harvey Grammar Pantomime
		list.append('&youtube_id=P3GzNZ2O3ik') #Nuffield College
		list.append('&youtube_id=mnXhoqpehUo') #Dick Whittington
		list.append('&youtube_id=M4d6d9uDCwc') #
		
		
	addDir('Pantomime Collections',list,17,'','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''אי המטמון'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=Cmd0VxJmmBA')
	addDir(addonString(10204).encode('utf-8'),list,5,'http://images.mouse.co.il/storage/0/e/ggg--Matmon.jpg',addonString(102040).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''אלאדין'''
	list = []
	fanart = 'http://www.jfuoco.com/images/trips/08/alladin_cast.gif'
	thumb = 'http://www.atmtxphoto.com/Blog/Creative-commons/i-6HJdmnn/0/L/disney-california-adventure-aladdin-stage-show-3-L.jpg'
	if 'Hebrew' in General_LanguageL:
		fanart = 'https://i.ytimg.com/vi/rCnTx-fUa6Y/maxresdefault.jpg'
		thumb = 'http://images.mouse.co.il/storage/8/1/aladin20134412_1136250_0..jpg'
		list.append('&youtube_id=sVCYRfk3Wcc')
		list.append('&youtube_id=aIY0onCV9u0')
	if 'English' in General_LanguageL:
		list.append('&youtube_id=iagPDqOtaKE')
		list.append('&youtube_id=zJi4hGBf5vs')
		list.append('&youtube_id=0Jgf7_WNP6o') #2011
		
	addDir(addonString(10205).encode('utf-8'),list,17,thumb,addonString(102050).encode('utf-8'),'1',50, getAddonFanart(background, custom=fanart))
	
	'''אמא אווזה'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_id=V1LEbSnUeM0')
	addDir(addonString(10206).encode('utf-8'),list,5,'https://i.ytimg.com/vi/fE3emlfJRLA/hqdefault.jpg',addonString(102060).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://www.countrychild.co.uk/wp-content/uploads/2014/12/Mother-Goose-at-Salisbury-Playhouse-credit-Robert-Workman.jpg"))
	
	'''בילבי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=sHMEnVpDJR8')
	addDir(addonString(10207).encode('utf-8'),list,5,'http://i.ytimg.com/vi/2mxOiPccxOs/maxresdefault.jpg',addonString(102070).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''גאליס המופע'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&dailymotion_id=x2aps1v')
		list.append('&dailymotion_id=x2apt79')
	addDir(addonString(10209).encode('utf-8'), list,17, 'http://up389.siz.co.il/up1/znmi3xqzndjg.jpg',addonString(102090).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''ג'ק ואפון הפלא'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_id=AWg7mK46Hkw') #Jack and the Beanstalk
		list.append('&youtube_id=Vs8SldXFzic') #English
		
	addDir(addonString(10208).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Jack_and_the_Beanstalk_Giant_-_Project_Gutenberg_eText_17034.jpg/220px-Jack_and_the_Beanstalk_Giant_-_Project_Gutenberg_eText_17034.jpg',addonString(102080).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''גיבורי האור'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=nwlo00FHCRc')
	addDir(addonString(10211).encode('utf-8'),list,5,'http://www.booknet.co.il/imgs/site/prod/7294276219850b.jpg',addonString(102110).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''גיגיגיגונת קלטת ילדים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=tKDm79jqRcI')
	addDir(addonString(10213).encode('utf-8'),list,5,'http://erezdvd.co.il/sites/default/files/imagecache/product_full/products/369504.jpg',addonString(102130).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''דוד חיים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%92%d7%99%d7%91%d7%95%d7%a8%d7%99%20%d7%94%d7%90%d7%95%d7%a8%20%d7%94%d7%93%d7%95%d7%a8%20%d7%94%d7%91%d7%90&url=seasonId%3d2884528')
		list.append('&youtube_id=ugmThlqdPJw')
		list.append('&youtube_id=X3j6mQ9VgLI')
		list.append('&youtube_id=T_a52ktWfLc')
		list.append('&youtube_id=FruAxOYP0uw')
		list.append('&custom4=plugin://plugin.video.MakoTV/?url=http%3A%2F%2Fwww.mako.co.il%2Fmako-vod-kids%2FVOD-66e32295e3b1741006.htm%3FsCh%3D131102642cecc310%26pId%3D540607453&mode=4&name=%D7%93%D7%95%D7%93+%D7%97%D7%99%D7%99%D7%9D+-+%D7%94%D7%98%D7%99%D7%95%D7%9C+%D7%90%D7%9C+%D7%94%D7%90%D7%95%D7%A6%D7%A8&iconimage=http://img.mako.co.il/2014/09/30/kids_dod_haim_01_1920X1080_02_f.jpg')
		list.append('&custom4=plugin://plugin.video.MakoTV/?url=http%3A%2F%2Fwww.mako.co.il%2Fmako-vod-kids%2FVOD-12e2b6e81057e31006.htm%3FsCh%3D131102642cecc310%26pId%3D540607453&mode=4&name=%D7%93%D7%95%D7%93+%D7%97%D7%99%D7%99%D7%9D+2&iconimage=http://img.mako.co.il/2013/05/12/kids_dod_haim_02_1920X1080_f.jpg')
		list.append('&custom4=plugin://plugin.video.MakoTV/?url=http%3A%2F%2Fwww.mako.co.il%2Fmako-vod-kids%2FVOD-7f43e7693548e31006.htm%3FsCh%3D131102642cecc310%26pId%3D540607453&mode=4&name=%D7%93%D7%95%D7%93+%D7%97%D7%99%D7%99%D7%9D+-+%D7%94%D7%94%D7%A6%D7%92%D7%94&iconimage=http://img.mako.co.il/2014/07/21/1920X1080_Haim_Theater_f.jpg')
	addDir(addonString(10715).encode('utf-8'),list,5,'http://www.nmcunited.co.il/Images/dynamic/movies/Dod-Haim2.jpg',addonString(107150).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''היפה והחיה'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_id=W3RgLlrjiHE')
	addDir(addonString(10530).encode('utf-8'),list,5,'https://upload.wikimedia.org/wikipedia/en/thumb/7/7c/Beautybeastposter.jpg/220px-Beautybeastposter.jpg',addonString(105300).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''היפיפייה הנרדמת'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_id=-EmYTTjzUbg') #English
	addDir(addonString(10531).encode('utf-8'),list,5,'https://upload.wikimedia.org/wikipedia/en/thumb/4/43/Sleeping_beauty_disney.jpg/220px-Sleeping_beauty_disney.jpg',addonString(105310).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''המכבים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=LFoX4vn6Obg')
	addDir(addonString(10225).encode('utf-8'),list,5,'http://www.ideals.co.il/wp-content/uploads/2015/02/nas3.jpg',addonString(102250).encode('utf-8'),'1',50, getAddonFanart(background, custom="https://i.ytimg.com/vi/NUXjR_WIJfQ/maxresdefault.jpg"))
	
	'''הקוסם מארץ עוץ'''
	thumb = 'http://www.sdarot.pm/media/series/1078.jpg'
	list = []
	if 'Hebrew' in General_LanguageL:
		thumb = 'http://www.habama.co.il/Habama/Upload/Children/%D7%9E%D7%90%D7%A8%D7%A5-%D7%A2%D7%95%D7%A5-%D7%A2%D7%A0%D7%A7-%D7%A7%D7%9E%D7%99%D7%A0%D7%A1%D7%A7%D7%99.jpg'
		list.append('&youtube_id=3rvK4dA5qwY')
	if 'English' in General_LanguageL:
		list.append('&youtube_id=xkYnLdqrORE') #English
		list.append('&youtube_id=TMoIGToMI-4') #English
		list.append('&youtube_id=LRHTlRQhuTo') #Wizard Of Oz
		list.append('&youtube_id=TnyoyDxm-Fs') #Wizard of Oz
		
	addDir(addonString(10431).encode('utf-8'),list,17,thumb,addonString(104310).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''הרקולס - המחזמר המלא'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=UiqG4WAcvCM')
	addDir(addonString(10227).encode('utf-8'),list,5,'http://moridim.me/images/large/191.jpg',addonString(102270).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''יובל המבולבל'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=6UrdISJBBC4')
		list.append('&youtube_id=C2Rm4IuVWNQ')
		list.append('&youtube_id=CZDniCIenbA')
		list.append('&youtube_id=H9rwsZ1roRQ')
		list.append('&youtube_id=oAkA7DnCBdE')
		#list.append('&custom4=plugin://plugin.video.MakoTV/?url=http%3A%2F%2Fwww.mako.co.il%2Fmako-vod-kids%2FVOD-a4c39d434280e31006.htm%3FsCh%3D131102642cecc310%26pId%3D540607453&mode=4&name=%D7%A2%D7%95%D7%9C%D7%9E%D7%95+%D7%A9%D7%9C+%D7%99%D7%95%D7%91%D7%9C+%D7%94%D7%9E%D7%91%D7%95%D7%9C%D7%91%D7%9C&iconimage=http://img.mako.co.il/2013/04/21/1920X1080_yuval_world_f.jpg')
	addDir(addonString(10731).encode('utf-8'),list,17,'http://yt3.ggpht.com/-FHcf2Rxu08A/AAAAAAAAAAI/AAAAAAAAAAA/dxzE2ng3uXI/s88-c-k-no/photo.jpg',addonString(107310).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://www.ashdodnet.com/dyncontent/t_post/2012/7/24/26370203843604787436.jpg"))
	
	'''ילד פלא'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=e5c134277697c')
	addDir(addonString(10231).encode('utf-8'),list,5,'http://shows.myfirsthomepage.co.il/admin/gamePics/yeled_pele7282014125120PM.jpg',addonString(102310).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://www.tamuseum.org.il/Data/Uploads/%D7%AA%D7%9E%D7%95%D7%A0%D7%94%20%D7%99%D7%9C%D7%93%20%D7%A4%D7%9C%D7%901.JPG"))
	
	'''לירן הקוסם מהאגדות'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=kNS4xMdPIos')
	addDir(addonString(10239).encode('utf-8'),list,5,'http://i.ytimg.com/vi/5gN4SMO8EfE/maxresdefault.jpg',addonString(102390).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''מותק הילדות התחברו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=1wLhD4yqQxU')
		list.append('&youtube_id=_Lv0UHXaY4I')
		list.append('&youtube_id=j_BClvgFwMw')
		list.append('&youtube_id=_WBgn4iw8gw')
	addDir(addonString(10243).encode('utf-8'),list,17,'http://media.org.il/images/Baby.girls.tap.the.musical.IL.1999_Front.Cover.jpg',addonString(102430).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))

	'''מותק של פסטיבל'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLE915B350E437A7D8')
		list.append('&youtube_pl=PL8C370A361DD07BDB')
		list.append('&youtube_id=t2ksCC_RyLw')
		list.append('&youtube_id=2KQBeOM')
	addDir(addonString(10244).encode('utf-8'),list,5,'http://www.yap.co.il/prdPics/4991_desc3_5_1_1409123377.jpg',addonString(102440).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''מיכל הקטנה''' 
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%9e%d7%99%d7%9b%d7%9c%20%d7%94%d7%a7%d7%98%d7%a0%d7%94%20%d7%a8%d7%95%d7%a6%d7%94%20%d7%9c%d7%94%d7%99%d7%95%d7%aa%20%d7%92%d7%93%d7%95%d7%9c%d7%94&url=seasonId%3d2888149')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%9e%d7%99%d7%9b%d7%9c%20%d7%94%d7%a7%d7%98%d7%a0%d7%94%20%d7%95%d7%94%d7%98%d7%95%d7%a0%d7%98%d7%95%d7%a0%d7%99%d7%9d&url=seasonId%3d2890384')
		list.append('&wallaNew=item_id%3D2567432')
		list.append('&wallaNew=item_id%3D2698903')
		list.append('&wallaNew=item_id%3D258362')
		list.append('&custom4=plugin://plugin.video.MakoTV/?url=http%3A%2F%2Fwww.mako.co.il%2Fmako-vod-kids%2FVOD-d04048a07975f31006.htm%3FsCh%3D131102642cecc310%26pId%3D540607453&mode=4&name=%D7%9E%D7%99%D7%9B%D7%9C+%D7%94%D7%A7%D7%98%D7%A0%D7%94+%22%D7%94%D7%A9%D7%99%D7%A8+%D7%A9%D7%91%D7%9C%D7%91%22&iconimage=http://img.mako.co.il/2013/06/24/michal_shir_f.jpg')
		list.append('&youtube_id=IEeuv8mtRLI')
	addDir(addonString(10245).encode('utf-8'),list,5,'http://www.pashbar.co.il/pictures/show_big_0523173001376412565.jpg',addonString(102450).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''מרקו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=XgnCNCt71d8')
	addDir(addonString(10248).encode('utf-8'),list,5,'http://www.ykp.co.il/cd_halev.jpg',addonString(102480).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''משחקי הפסטיגל'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=d2953353ab9e8')
	addDir(addonString(10250).encode('utf-8'),list,5,'http://www.ligdol.co.il/Upload/pestigal2014_poster.jpg',addonString(102500).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''נסיך מצרים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=LFoX4vn6Obg')
	addDir(addonString(10252).encode('utf-8'),list,5,'http://www.ideals.co.il/wp-content/uploads/2015/02/nas3.jpg',addonString(102520).encode('utf-8'),'1',50, getAddonFanart(background, custom="https://i.ytimg.com/vi/NUXjR_WIJfQ/maxresdefault.jpg"))
	
	'''סינדרלה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=snr9wxyEzpA')
	if 'English' in General_LanguageL:
		list.append('&youtube_id=Hp_ekaM6wLk')
		list.append('&youtube_id=_ywvSa0JSEE')
	addDir(addonString(10255).encode('utf-8'),list,5,'http://afisha.israelinfo.ru/pictures/19949.jpg',addonString(102550).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''ספר הגונגל'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=TlWVoNz_B3o')
	addDir(addonString(10258).encode('utf-8'),list,5,'http://images.mouse.co.il/storage/3/7/ggg--book20090908_2343750_0..jpg',addonString(102580).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''עמי ותמי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=8d6a2e7a3cd54')
	addDir(addonString(10261).encode('utf-8'),list,5,'http://www.tivon.co.il/vault/Zoar/amitami-B.jpg',addonString(102610).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''עליבאבא וארבעים השודדים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=gxgvTe3kPGY')
	if 'English' in General_LanguageL:
		list.append('&youtube_id=SmG8F9-ZH-0')	
		
	addDir(addonString(10262).encode('utf-8'),list,5,'http://i.ytimg.com/vi/EMtHOrNBXKU/hqdefault.jpg',addonString(102620).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''עליסה בארץ הפלאות'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=4Zp-6Ts07Qw')
	addDir(addonString(10263).encode('utf-8'),list,5,'http://images.mouse.co.il/storage/3/0/b--alice.jpg',addonString(102630).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''פיטר פן'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=gTuMB5sz8pY')
	if 'English' in General_LanguageL:
		list.append('&youtube_id=6l70mf7d2Jw')	
	
	addDir(addonString(10267).encode('utf-8'),list,17,'http://i48.tinypic.com/f5ceuq.jpg',addonString(102670).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''פסטיבל כיף לי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_ch=UCTxlaUXzxohVekL_Zym-hsw')
		list.append('&youtube_id=lZgpGH9wTHY')
	addDir(addonString(10269).encode('utf-8'),list,5,'http://3.bp.blogspot.com/-LIy_QkefJ-M/UuaoyVJu82I/AAAAAAAAAus/Dpd7rKKbUfM/s1600/KEF2014+POS+copy.jpg',addonString(102690).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''פסטיגל'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_ch=UCKs_S8Uo5rLCNhlSanFpfFQ')
		list.append('&youtube_ch=UC8z6QWcSpDfeHY0sni4IDwA')
		list.append('&youtube_pl=PLwimDnICcPKPL4MdOLIQrGDMTOAshuQ2l')
	addDir(addonString(10270).encode('utf-8'),list,17,'http://yt3.ggpht.com/-2Nux9ubjSCA/AAAAAAAAAAI/AAAAAAAAAAA/P8I968rchgE/s88-c-k-no/photo.jpg',addonString(102700).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''צ'פצ'ולה' - מיכל כלפון'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=EKlFN3awN_w')
		list.append('&youtube_id=UC64wDQFgTq9RpI1P8_p-SxA')
		list.append('&custom4=plugin://plugin.video.MakoTV/?url=http%3A%2F%2Fwww.mako.co.il%2Fmako-vod-kids%2FVOD-be230098ac9a051006.htm%3FsCh%3D131102642cecc310%26pId%3D540607453&mode=4&name=%D7%A6%27%D7%A4%D7%A6%27%D7%95%D7%9C%D7%94+%D7%95%D7%94%D7%A8%D7%A4%D7%AA%D7%A7%D7%90%D7%95%D7%AA+%D7%94%D7%97%D7%99%D7%95%D7%AA&iconimage=http://img.mako.co.il/2015/10/27/kids_C_animal_adventure_f.jpg')
		list.append('&wallaNew=item_id%3D2728550')
	addDir(addonString(10768).encode('utf-8'),list,17,'http://yt3.ggpht.com/-4Rd1GQEZnaM/AAAAAAAAAAI/AAAAAAAAAAA/pfQtiUaNjng/s88-c-k-no/photo.jpg',addonString(107680).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''רובין הוד'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=6nZk0H89jDQ')
	if 'English' in General_LanguageL:
		list.append('&youtube_id=iyke1Yx0y78')
		list.append('&youtube_id=2uMZwF9hlVo')
		list.append('&youtube_id=zOp0eZ08hYE')
		list.append('&youtube_id=Vb72XqW9vOU') #2014
		
	addDir(addonString(10272).encode('utf-8'),list,17,'http://erezdvd.co.il/sites/default/files/imagecache/product_full/products/14810.jpg',addonString(102720).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''רובין זו קרוזו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=')
	if 'English' in General_LanguageL:
		list.append('&youtube_id=EVEc0RyDhvM')
		list.append('&youtube_id=kZ4zzYBD4Cs')
		list.append('&youtube_id=KqnsUtNPhFE')
		
	addDir(addonString(10273).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Robinson_Crusoe_and_Man_Friday_Offterdinger.jpg/170px-Robinson_Crusoe_and_Man_Friday_Offterdinger.jpg',addonString(102730).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''רינת גבאי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=ykKWS-Udw2s')
	addDir(addonString(10274).encode('utf-8'),list,5,'http://img.mako.co.il/2013/09/16/fantasy50X70-poster_SHOWS_g.jpg',addonString(102740).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''שורום זורום'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=9rGV96uhqPw')
	addDir(addonString(10284).encode('utf-8'),list,5,'http://images1.ynet.co.il/PicServer4/2015/07/30/6201572/01_SM.jpg',addonString(102840).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''שלגיה והצייד'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=0rPEJ-kD1dc')
	if 'English' in General_LanguageL:
		list.append('&youtube_id=6SIbUd6inRU')
		list.append('&youtube_id=PEK_gfl60R8')
		list.append('&youtube_id=Mif76xXF8zo')
	addDir(addonString(10287).encode('utf-8'),list,17,'http://www.dossinet.me/coverage_pics/1b5d66af0d230ff716d50f07fd6defc0.jpg',addonString(102870).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''סבא טוביה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLE494A88ED3823578')
	addDir(addonString(10108).encode('utf-8'),list,5,'http://yt3.ggpht.com/--gG5kz68N_k/AAAAAAAAAAI/AAAAAAAAAAA/37Cr6jMJSCg/s88-c-k-no/photo.jpg',addonString(1010800).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES102A(General_LanguageL, background, background2) #עמוד הבא שירים וסיפורים
	
def CATEGORIES104(name, iconimage, desc, fanart):
	background = 104
	background2 = "" #http://www.canadiananimationresources.ca/wp-content/uploads/2012/10/9-Story-Arthur-Couch.jpg"
	
	'''חיפוש'''
	if 'Hebrew' in General_LanguageL: addDir(localize(137) + space + 'Sdarot TV','&activatewindow=plugin://plugin.video.sdarot.tv/?mode=6&name=%5bCOLOR%20red%5d%20%d7%97%d7%a4%d7%a9%20%20%5b%2fCOLOR%5d&summary&url=http%3a%2f%2fwww.sdarot.wf%2fsearch',8,featherenceserviceicons_path + 'se.png','חיפוש תוכן בהרחבת סדרות','1',"", getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES_RANDOM() #אקראי
	CATEGORIES104Z(General_LanguageL, background, background2) #ערוצי טלוויזיה
	
	'''אאוץ'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1864&series_name=%d7%90%d7%90%d7%95%d7%a5%27%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&summary&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1864%2foperation-ouch-%d7%90%d7%90%d7%95%d7%a5-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	addDir(addonString(10401).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/1864.jpg',addonString(104010).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://www.sdarot.pm/media/series/1864.jpg"))
	
	CATEGORIES104L(General_LanguageL, background, background2) #אגדות האחים גרים
	
	'''אגדות המלך שלמה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=815&series_name=%d7%90%d7%92%d7%93%d7%95%d7%aa%20%d7%94%d7%9e%d7%9c%d7%9a%20%d7%a9%d7%9c%d7%9e%d7%94%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&summary&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f815%2ftales-of-a-wise-king-hebdub-%d7%90%d7%92%d7%93%d7%95%d7%aa-%d7%94%d7%9e%d7%9c%d7%9a-%d7%a9%d7%9c%d7%9e%d7%94-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLOx5NGhretuY8wp75WCY5PQQx8agiZ2IC')
	addDir(addonString(10402).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/815.jpg',addonString(104020).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''אוגי והמקקים*'''
	list = []
	list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a4%d7%a8%d7%a7%d7%99%d7%9d%20%d7%9e%d7%9c%d7%90%d7%99%d7%9d&url=seasonId%3d2830054')
	list.append('&youtube_pl=PLsN1aN-kzJnOgSDAwE5PPF3IH9fGH57Xx')
	list.append('&youtube_pl=PLDks7iHzd1bV7S9aLZfEtFmoToSrJPPdE')
	addDir(addonString(10429).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/585.jpg',addonString(104290).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES104O(General_LanguageL, background, background2) #אוטובוס הקסמים
	
	'''אלאדין'''
	list = []
	if 'Hebrew' in General_LanguageL: pass
	if 'Italian' in General_LanguageL:
		list.append('&dailymotion_pl=x3qyi3') #Italian #S1
		list.append('&dailymotion_pl=x46bvx') #Italian #S1
		list.append('&dailymotion_pl=x4129o') #Italian #S2
		list.append('&dailymotion_pl=x412a4') #Italian #S3
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PL-fIrVtK0oZpQ7WmzXI04nbenZ-W4nj4Z')
	addDir(addonString(10529).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/he/thumb/d/d9/Aladdin_TV_series.jpg/250px-Aladdin_TV_series.jpg',addonString(105290).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''אנימניאקס'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1104&summary&series_name=%d7%90%d7%a0%d7%99%d7%9e%d7%a0%d7%99%d7%90%d7%a7%d7%a1%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1104%2fanimaniacs-%d7%90%d7%a0%d7%99%d7%9e%d7%a0%d7%99%d7%90%d7%a7%d7%a1-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
	addDir(addonString(10404).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/1104.jpg',addonString(104040).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
								 
	'''אקס מן'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1434&series_name=%d7%90%d7%a7%d7%a1-%d7%9e%d7%9f%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&summary&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1434%2fx-men-%d7%90%d7%a7%d7%a1-%d7%9e%d7%9f-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=PLN0EJVTzRDL9ObPf7m4GCN2BL6Ayreybh')
		list.append('&youtube_pl=PL240D6E0D52552316') #Broken
		list.append('&youtube_pl=PL8D5045D1EA3AA091') #Broken
		list.append('&youtube_pl=PLE69A961D0351E331') #Broken
	addDir(addonString(10405).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1434.jpg',addonString(104050).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
							  
	'''אקס-מן: הדור הבא'''
	fanart = 'http://images-cdn.moviepilot.com/images/c_fill,h_720,w_1280/t_mp_quality/enumedpsjv5z9hypcjna/rumor-fox-closing-in-on-deal-for-x-men-live-action-series-will-it-really-happen-x-men-559825.jpg'
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1435&series_name=%d7%90%d7%a7%d7%a1-%d7%9e%d7%9f%3a%20%d7%94%d7%93%d7%95%d7%a8%20%d7%94%d7%91%d7%90%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1435%2fx-men-evolution-%d7%90%d7%a7%d7%a1-%d7%9e%d7%9f-%d7%94%d7%93%d7%95%d7%a8-%d7%94%d7%91%d7%90-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
	addDir(addonString(10406).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/1435.jpg',addonString(104060).encode('utf-8'),'1',50, getAddonFanart(background, custom=fanart))
	
	'''ארתור'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=461&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f461%2farthur-%d7%90%d7%a8%d7%aa%d7%95%d7%a8-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a4%d7%a8%d7%a7%d7%99%d7%9d%20%d7%9e%d7%9c%d7%90%d7%99%d7%9d&url=seasonId%3d2558030')
		list.append('&youtube_pl=PL17sRM9raf1Q-i_fTe45N0UBqNgdnZTD6')
		list.append('&youtube_pl=PLN0EJVTzRDL96B86muPPFwgdymQjlwmLZ')
	addDir(addonString(10407).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/461.jpg',addonString(104070).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''באג בראש'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=461&series_name=%d7%90%d7%a8%d7%aa%d7%95%d7%a8%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f461%2farthur-%d7%90%d7%a8%d7%aa%d7%95%d7%a8-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
	addDir(addonString(10408).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/1497.jpg',addonString(104080).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))	
	
	'''בארץ הקטקטים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1323&series_name=%d7%91%d7%90%d7%a8%d7%a5%20%d7%94%d7%a7%d7%98%d7%a7%d7%98%d7%99%d7%9d%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1323%2fthe-littl-bits-%d7%91%d7%90%d7%a8%d7%a5-%d7%94%d7%a7%d7%98%d7%a7%d7%98%d7%99%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLR7DTcU2p0Qg5sF-jE09YnRymKba8N8l_')
		list.append('&youtube_pl=PLAlLEuz2HJebactpYs8hhJgPS1N2HDmar')
		list.append('&youtube_pl=PLN0EJVTzRDL-WaGew7sZQHQc1l48LSZmp')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLnMOar3QFQYI4IlS9nNLZ_3wFMa-mf2pP') #English
		list.append('&youtube_pl=PLZs0gQed9tMQsC9dAjvjlHeEzibEliBjW') #English
	addDir(addonString(10409).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1323.jpg',addonString(104090).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))	
	
	'''בוב ספוג מכנס מרובע'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%e1%e9%fa%20%e0%f0%e5%e1%e9%f1&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f1810190')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%d7%a2%d7%95%d7%93%20%d7%a4%d7%a8%d7%a7%d7%99%d7%9d&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f1688134%26page%3d2')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%e1%e5%e1%f1%f4%e5%e2%20%ee%eb%f0%f1%20%ee%f8%e5%e1%f2&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f1688133')
		list.append('&sdarot=series_id=490&series_name=%d7%91%d7%95%d7%91%d7%a1%d7%a4%d7%95%d7%92%20%d7%9e%d7%9b%d7%a0%d7%a1%20%d7%9e%d7%a8%d7%95%d7%91%d7%a2%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f490%2fspongebob-squarepants-%d7%91%d7%95%d7%91%d7%a1%d7%a4%d7%95%d7%92-%d7%9e%d7%9b%d7%a0%d7%a1-%d7%9e%d7%a8%d7%95%d7%91%d7%a2-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLjDLgg_nO1v6sKrBN5fm-XZf2f52ko7E7') #English
	addDir(addonString(10410).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/490.jpg',addonString(104100).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''בולי איש השלג'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1642&series_name=%d7%91%d7%95%d7%9c%d7%99%20%d7%90%d7%99%d7%a9%20%d7%94%d7%a9%d7%9c%d7%92%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1642%2fbouli-%d7%91%d7%95%d7%9c%d7%99-%d7%90%d7%99%d7%a9-%d7%94%d7%a9%d7%9c%d7%92-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PL0o6qImfDA9rt-5UwjlPs-9pVON7-LPA_')
		list.append('&youtube_id=2j2ISqZ40GU')
		list.append('&youtube_id=oV_sUQa4BLE')
		list.append('&youtube_id=qi5D5LnmrYk')
	addDir(addonString(10411).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1642.jpg',addonString(104110).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''בילבי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1159&series_name=%d7%91%d7%99%d7%9c%d7%91%d7%99%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&summary=%d7%91%d7%99%d7%9c%d7%91%d7%99%20%d7%94%d7%99%d7%90%20%d7%99%d7%9c%d7%93%d7%94%20%d7%9e%d7%99%d7%95%d7%97%d7%93%d7%aa%20%d7%91%d7%9e%d7%99%d7%a0%d7%94%20%d7%a9%d7%a2%d7%95%d7%a9%d7%94%20%d7%9b%d7%9c%20%d7%9e%d7%94%20%d7%a9%d7%91%d7%90%20%d7%9c%d7%94.%20%d7%94%d7%99%d7%90%20%d7%97%d7%96%d7%a7%d7%94%20%d7%95%d7%90%d7%9e%d7%99%d7%a6%d7%94%2c%20%d7%97%d7%9b%d7%9e%d7%94%20%d7%9e%d7%9b%d7%95%d7%9c%d7%9d%2c%20%d7%a9%d7%95%d7%91%d7%91%d7%94%20%d7%95%d7%91%d7%9c%d7%92%d7%a0%d7%99%d7%a1%d7%98%d7%99%d7%aa%20%d7%9c%d7%90%20%d7%a7%d7%98%d7%a0%d7%94.%20%d7%94%d7%99%d7%90%20%d7%97%d7%99%d7%94%20%d7%91%d7%95%d7%99%d7%9c%d7%94%20%d7%a2%d7%9d%20%d7%97%d7%91%d7%a8%d7%99%d7%94%3a%20%d7%94%d7%90%d7%97%d7%99%d7%9d%20%d7%98%d7%95%d7%9e%d7%99%20%d7%95%d7%90%d7%a0%d7%99%d7%a7%d7%94%2c%20%d7%94%d7%a7%d7%95%d7%a3%20%22%d7%9e%d7%a8%20%d7%a0%d7%9c%d7%a1%d7%95%d7%9f%22%20%d7%95%d7%94%d7%a1%d7%95%d7%a1%20%d7%a9%d7%9c%d7%94.%20%d7%94%d7%97%d7%91%d7%95%d7%a8%d7%94%20%d7%97%d7%95%d7%95%d7%94%20%d7%94%d7%a8%d7%a4%d7%aa%d7%a7%d7%90%d7%95%d7%aa%20%d7%a8%d7%91%d7%95%d7%aa%20%d7%95%d7%9c%d7%a4%d7%a2%d7%9e%d7%99%d7%9d%20%d7%92%d7%9d%20%d7%9e%d7%a1%d7%aa%d7%91%d7%9b%d7%aa%20%d7%91%d7%a6%d7%a8%d7%95%d7%aa%3b%20%d7%90%d7%91%d7%9c%2c%20%d7%9c%d7%90%20%d7%9c%d7%93%d7%90%d7%95%d7%92%20%d7%91%d7%99%d7%9c%d7%91%d7%99%20%d7%aa%d7%9e%d7%99%d7%93%20%d7%9e%d7%a6%d7%9c%d7%99%d7%97%d7%94%20%d7%9c%d7%94%d7%aa%d7%92%d7%91%d7%a8%20%d7%a2%d7%9c%20%d7%9b%d7%9c%20%d7%94%d7%a7%d7%a9%d7%99%d7%99%d7%9d%20%d7%94%d7%a2%d7%95%d7%9e%d7%93%d7%99%d7%9d%20%d7%91%d7%93%d7%a8%d7%9a%20%d7%91%d7%96%d7%9b%d7%95%d7%aa%20%d7%9b%d7%95%d7%97%d7%95%d7%aa%d7%99%d7%94%20%d7%94%d7%9e%d7%99%d7%95%d7%97%d7%93%d7%99%d7%9d%2c%20%d7%94%d7%90%d7%a0%d7%a8%d7%92%d7%99%d7%94%20%d7%95%d7%94%d7%93%d7%9e%d7%99%d7%95%d7%9f%20%d7%94%d7%9e%d7%a4%d7%95%d7%aa%d7%97%20%d7%a9%d7%9c%d7%94.&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1159%2fpippi-longstocking-%d7%91%d7%99%d7%9c%d7%91%d7%99-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_id=CBWXP_5gxSw')
		list.append('&youtube_id=kgLCdl2q8XQ')
		list.append('&youtube_id=5tc2MzqqHH8')
		list.append('&youtube_id=L878q4J48L8')
	addDir(addonString(10207).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1159.jpg',addonString(102070),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''בנות הים פיצ'י פיצ'י פיץ'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=550&series_name=%d7%91%d7%a0%d7%95%d7%aa%20%d7%94%d7%99%d7%9d%20%d7%a4%d7%99%d7%a6%27%d7%99%20%d7%a4%d7%99%d7%a6%27%d7%99%20%d7%a4%d7%99%d7%a5%27%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f550%2fmermaid-melody-pichi-pichi-pitch-%d7%91%d7%a0%d7%95%d7%aa-%d7%94%d7%99%d7%9d-%d7%a4%d7%99%d7%a6-%d7%99-%d7%a4%d7%99%d7%a6-%d7%99-%d7%a4%d7%99%d7%a5-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=PLXLQCKKIyvStclVXSB76tdtDptKZLscJ_')
	addDir(addonString(10412).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/550.jpg',addonString(104120).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''בנימין הפיל'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL1SAyTUFBb767lthA5ZrIux5ierTsdY8X') #בנימין הפיל
		list.append('&youtube_pl=PL1SAyTUFBb74t4LAyNvAwQrPhqpz8aPl9')
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=PL1SAyTUFBb74M_o7qtwLX507S1U11DFdq') #בנימין הפיל
		list.append('&youtube_pl=')
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=PL1SAyTUFBb76vI6mmDVJW-idZzy5w3O95') #בנימין הפיל
		list.append('&youtube_pl=')
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PL1SAyTUFBb76lUw0NZmBs5wivH7C2rDjH') #בנימין הפיל
		list.append('&youtube_pl=')
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=PL8xBm2jGFeURg8zePCAvOmz0HKF0Buxx9') #בנימין הפיל
		list.append('&youtube_pl=PL1SAyTUFBb74hUX32r6aqasGENGL4YShb')
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=PL1SAyTUFBb76FQRP8IUUdRWdyvejE7KHg') #בנימין הפיל
		list.append('&youtube_pl=')	
	if 'French' in General_LanguageL:
		list.append('&youtube_id=6M2Ll1ckj-o')
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PL1SAyTUFBb77CVJW1egme_gOlYTcPsy1X') #בנימין הפיל
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
	addDir(addonString(10434).encode('utf-8'),list,17,'https://s-media-cache-ak0.pinimg.com/736x/3a/bf/04/3abf042ce92ac9656ca71f7de3c6f969.jpg',addonString(104340).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''ברבי'''
	list = []
	
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLL-dZ_buCnGLL_5O0KJQE68_2Vqb55tls') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLUyVAz5vm69lBuq2509ziZzWomSBhd4x-') #English
	if 'Thai' in General_LanguageL:
		list.append('&youtube_pl=PL3_OyqmNQ5jogMj02awwJgqv138pqmIue') #Thai
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PL6jk7-ujY14TgQzza2Tz9DL7CfaPMDvC2') #Spanish
		list.append('&youtube_id=zrsIpOZHuBo')
		
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=PLHRg_DI8OiY6GsdaIO6qTnlO7BBJlajDP') #Dutch
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=PL7tHlGdGn8tgNocLA1u0rfj_vSn3PUqSS') #Portuguese
	addDir(addonString(10230).encode('utf-8'),list,17,'http://ia.media-imdb.com/images/M/MV5BMTg0MDc4MzU4NF5BMl5BanBnXkFtZTgwNjM5MTgyMjE@._V1_SY317_CR16,0,214,317_AL_.jpg',addonString(102300).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://images5.fanpop.com/image/photos/31900000/Barbie-Life-In-The-Dream-House-barbie-life-in-the-dreamhouse-31984906-1600-1200.jpg"))
	
	'''ג'רג מלך הג'ונגל'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1909&series_name=%d7%92%27%d7%95%d7%a8%d7%92%27%20%d7%9e%d7%9c%d7%9a%20%d7%94%d7%92%27%d7%95%d7%a0%d7%92%d7%9c%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1909%2fgeorge-of-the-jungle-%d7%92-%d7%95%d7%a8%d7%92-%d7%9e%d7%9c%d7%9a-%d7%94%d7%92-%d7%95%d7%a0%d7%92%d7%9c-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_ch=georgeofthejungle')
	addDir(addonString(10413).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1909.jpg',addonString(104130).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''גברת פלפלת'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1314&series_name=%d7%92%d7%91%d7%a8%d7%aa%20%d7%a4%d7%9c%d7%a4%d7%9c%d7%aa%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1314%2flittle-mrs-pepperpot-%d7%92%d7%91%d7%a8%d7%aa-%d7%a4%d7%9c%d7%a4%d7%9c%d7%aa-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLkLrihhmnxYGoIg5xDLAR-hzpsvRgeabM')
	addDir(addonString(10414).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1314.jpg',addonString(104140).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES104D(General_LanguageL, background, background2) #ג'ימי ניוטרון
	CATEGORIES104I(General_LanguageL, background, background2) #דובוני אכפת לי
	
	'''דורימון'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL95CWWe9DuaJ6xtv1V8ZxDvoG_cB3z4bc')
	addDir(addonString(10415).encode('utf-8'),list,17,'http://www.animation-animagic.com/img/conteudo/2632008151425.jpg',addonString(104150).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES104P(General_LanguageL, background, background2) #דיגימון
	
	'''דנבר הדינוזאור האחרון'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLWIkOi4pSkd8b3DGMHT5UkKZPZ_KzheUu')
		list.append('&youtube_pl=PLb1xghMkI5XmVJubEwR1WH6qq6QPOMXSz')
	
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PL74D068B7A8C01DBB')
	
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PLcFEa8vQIcKtU1VknkYflFnH7DjtBwaHt')
	
	if 'Italiano' in General_LanguageL:
		list.append('&youtube_pl=PL282B62C90158252C')
	
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=PLZsA2bTSVjpRV57QDRH25-HFKRG5HCWaZ')
	
	if 'Chinese' in General_LanguageL:
		list.append('&youtube_pl=PL3EB7946A98ACC0CD')
		
		
	addDir(addonString(10426).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/en/thumb/f/f3/Denver_the_Last_Dinosaur_title_card.jpg/250px-Denver_the_Last_Dinosaur_title_card.jpg',addonString(104260).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''דני שובבני'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdaort=season_id=1&series_id=448&series_name=%d7%93%d7%a0%d7%99%20%d7%a9%d7%95%d7%91%d7%91%d7%a0%d7%99%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&summary=%d7%93%d7%a0%d7%99%20%d7%a9%d7%95%d7%91%d7%91%d7%a0%d7%99%20%d7%94%d7%95%d7%90%20%d7%99%d7%9c%d7%93%20%d7%a9%d7%9c%d7%90%20%d7%9e%d7%a4%d7%a1%d7%99%d7%a7%20%d7%9c%d7%a2%d7%a9%d7%95%d7%aa%20%d7%a9%d7%98%d7%95%d7%99%d7%95%d7%aa%2c%20%d7%9c%d7%94%d7%a6%d7%99%d7%a7%20%d7%9c%d7%a9%d7%9b%d7%a0%d7%99%d7%9d%2c%20%d7%9c%d7%a2%d7%a9%d7%95%d7%aa%20%d7%a0%d7%96%d7%a7%d7%99%d7%9d%20%d7%95%d7%91%d7%a7%d7%99%d7%a6%d7%95%d7%a8%20%d7%9c%d7%94%d7%99%d7%95%d7%aa%20%d7%9b%d7%9e%d7%95%20%d7%9b%d7%9c%20%d7%99%d7%9c%d7%93%20%d7%91%d7%9f%20%d7%92%d7%99%d7%9c%d7%95.%20%d7%99%d7%97%d7%93%20%d7%a2%d7%9d%20%d7%9b%d7%9c%d7%91%d7%95%20%d7%94%d7%9e%d7%95%d7%a4%d7%a8%d7%a2%20%d7%91%d7%a9%d7%9d%20%d7%a8%d7%90%d7%a3%2c%20%d7%93%d7%a0%d7%99%20%d7%9e%d7%97%d7%95%d7%9c%d7%9c%20%d7%9e%d7%94%d7%95%d7%9e%d7%95%d7%aa%20%d7%91%d7%a9%d7%9b%d7%95%d7%a0%d7%94%2c%20%d7%9b%d7%90%d7%a9%d7%a8%20%d7%9b%d7%95%d7%95%d7%a0%d7%95%d7%aa%d7%99%d7%95%20%d7%94%d7%98%d7%95%d7%91%d7%95%d7%aa%2c%20%d7%94%d7%a8%d7%a6%d7%95%d7%9f%20%d7%94%d7%9e%d7%95%d7%98%d7%a2%d7%94%20%d7%9c%d7%a2%d7%96%d7%95%d7%a8%20%d7%95%d7%94%d7%a1%d7%a7%d7%a8%d7%a0%d7%95%d7%aa%20%d7%a9%d7%9c%d7%95%20%d7%a9%d7%90%d7%99%d7%a0%d7%94%20%d7%99%d7%95%d7%93%d7%a2%d7%aa%20%d7%a9%d7%95%d7%91%d7%a2%20%d7%9e%d7%95%d7%91%d7%99%d7%9c%d7%99%d7%9d%20%d7%90%d7%95%d7%aa%d7%95%20%d7%9c%d7%94%d7%a8%d7%a4%d7%aa%d7%a7%d7%90%d7%95%d7%aa%20%d7%95%d7%9b%d7%99%d7%95%d7%a4%d7%99%d7%9d.&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f448%2fdennis-the-menace-%d7%93%d7%a0%d7%99-%d7%a9%d7%95%d7%91%d7%91%d7%a0%d7%99-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a4%d7%a8%d7%a7%d7%99%d7%9d%20%d7%9e%d7%9c%d7%90%d7%99%d7%9d&url=seasonId%3d2548246')
		list.append('&youtube_pl=EvU1EzELJI8&list=PL68ECBFC6278EB7BE') #Hebrew
		list.append('&youtube_id=zWwqxZPg8as') #Hebrew
		list.append('&youtube_id=yLMFuFM5b7U') #Hebrew
		list.append('&youtube_id=VYxab_Lh0gg') #Hebrew
		list.append('&youtube_id=EjpsfP86Neo') #Hebrew
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=PL810CC2AF30CEFF13') #Serbian
	addDir(addonString(10417).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/448.jpg',addonString(104170).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''דן דין השופט'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1009&series_name=%d7%93%d7%9f%20%d7%93%d7%99%d7%9f%20%d7%94%d7%a9%d7%95%d7%a4%d7%98%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&summary=%d7%93%d7%9f%20%d7%93%d7%99%d7%9f%20%d7%94%d7%95%d7%90%20%d7%a9%d7%95%d7%a4%d7%98%20%d7%97%d7%9b%d7%9d%20%d7%90%d7%a9%d7%a8%20%d7%a0%d7%a7%d7%a8%d7%90%20%d7%a2%22%d7%99%20%d7%94%d7%92%d7%9e%d7%93%d7%99%d7%9d%20%d7%91%d7%9b%d7%9c%20%d7%94%d7%a2%d7%95%d7%9c%d7%9d%20%d7%9c%d7%a4%d7%aa%d7%95%d7%a8%20%d7%90%d7%aa%20%d7%91%d7%a2%d7%99%d7%95%d7%aa%d7%99%d7%94%d7%9d.%20%d7%a0%d7%a2%d7%96%d7%a8%20%d7%91%d7%a2%d7%95%d7%96%d7%a8%d7%95%2c%20%d7%91%d7%99%d7%a0%d7%95%2c%20%d7%93%d7%9f%20%d7%93%d7%99%d7%9f%20%d7%a2%d7%a3%20%d7%9c%d7%9b%d7%9c%20%d7%9e%d7%a7%d7%95%d7%9d%20%d7%a2%d7%9c%20%d7%92%d7%91%d7%95%20%d7%a9%d7%9c%20%d7%98%d7%99%d7%9c%d7%99%20%d7%94%d7%91%d7%a8%d7%91%d7%95%d7%a8.%20%d7%94%d7%92%d7%9e%d7%93%d7%99%d7%9d%20%d7%a6%d7%a8%d7%99%d7%9b%d7%99%d7%9d%20%d7%9c%d7%94%d7%99%d7%96%d7%94%d7%a8%20%d7%9e%d7%94%d7%98%d7%a8%d7%95%d7%9c%d7%99%d7%9d%20%d7%94%d7%a8%d7%a2%d7%99%d7%9d%20%d7%a9%d7%9e%d7%aa%d7%a0%d7%9b%d7%9c%d7%99%d7%9d%20%d7%9c%d7%94%d7%9d%20%d7%91%d7%9b%d7%9c%20%d7%94%d7%96%d7%93%d7%9e%d7%a0%d7%95%d7%aa.&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1009%2fthe-wisdom-of-the-gnomes-%d7%93%d7%9f-%d7%93%d7%99%d7%9f-%d7%94%d7%a9%d7%95%d7%a4%d7%98-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	addDir(addonString(10418).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/1009.jpg',addonString(104180).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))	
	
	CATEGORIES104R(General_LanguageL, background, background2) #דראגון בול
	CATEGORIES104S(General_LanguageL, background, background2) #דראגון בול Z
	CATEGORIES104T(General_LanguageL, background, background2) #דראגון בול S
	CATEGORIES104U(General_LanguageL, background, background2) #דראגון בול GT
	CATEGORIES104V(General_LanguageL, background, background2) #דראגון בול K
	
	'''הדבורה מאיה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=668&series_name=%d7%94%d7%93%d7%91%d7%95%d7%a8%d7%94%20%d7%9e%d7%90%d7%99%d7%94%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&summary=%d7%9e%d7%90%d7%99%d7%94%20%d7%94%d7%99%d7%90%20%d7%93%d7%91%d7%95%d7%a8%d7%94%20%d7%9e%d7%a8%d7%93%d7%a0%d7%99%d7%aa%2c%20%d7%a1%d7%a7%d7%a8%d7%a0%d7%99%d7%aa%20%d7%95%d7%a9%d7%95%d7%91%d7%91%d7%94.%20%d7%94%d7%99%d7%90%20%d7%a2%d7%95%d7%96%d7%91%d7%aa%20%d7%90%d7%aa%20%d7%94%d7%9b%d7%95%d7%95%d7%a8%d7%aa%20%d7%9b%d7%93%d7%99%20%d7%9c%d7%a6%d7%90%d7%aa%20%d7%9c%d7%98%d7%99%d7%95%d7%9c%20%d7%91%d7%a2%d7%95%d7%9c%d7%9d%20%d7%99%d7%97%d7%93%20%d7%a2%d7%9d%20%d7%94%d7%93%d7%91%d7%95%d7%a8%d7%95%d7%9f%20%d7%95%d7%95%d7%99%d7%9c%d7%99.%20%d7%94%d7%a9%d7%a0%d7%99%d7%99%d7%9d%20%d7%a2%d7%95%d7%91%d7%a8%d7%99%d7%9d%20%d7%94%d7%a8%d7%a4%d7%aa%d7%a7%d7%90%d7%95%d7%aa%20%d7%a7%d7%a1%d7%95%d7%9e%d7%95%d7%aa%20%d7%95%d7%a4%d7%95%d7%92%d7%a9%d7%99%d7%9d%20%d7%97%d7%91%d7%a8%d7%99%d7%9d%20%d7%91%d7%93%d7%a8%d7%9a%20%d7%97%d7%93%d7%a9%d7%99%d7%9d.%20%d7%9e%d7%90%d7%99%d7%94%20%d7%97%d7%95%d7%96%d7%a8%d7%aa%20%d7%9c%d7%9b%d7%95%d7%95%d7%a8%d7%aa%20%d7%97%d7%96%d7%a7%d7%94%20%d7%95%d7%97%d7%9b%d7%9e%d7%94%20%d7%94%d7%a8%d7%91%d7%94%20%d7%99%d7%95%d7%aa%d7%a8.&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f668%2fmaya-the-bee-%d7%94%d7%93%d7%91%d7%95%d7%a8%d7%94-%d7%9e%d7%90%d7%99%d7%94-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLfcYs4SRZfuKJs0CL98BF0_OOGRWlmpdQ')
	addDir(addonString(10419).encode('utf-8'),list,17,'http://tochka.bg/uploads/ckfinder/images/maya_the_bee.png',addonString(104190).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''הובוס ספר הקסמים הגדול'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1532&series_name=%d7%94%d7%95%d7%91%d7%95%d7%a1%20%d7%a1%d7%a4%d7%a8%20%d7%94%d7%a7%d7%a1%d7%9e%d7%99%d7%9d%20%d7%94%d7%92%d7%93%d7%95%d7%9c%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1532%2fthe-ultimate-book-of-spells-%d7%94%d7%95%d7%91%d7%95%d7%a1-%d7%a1%d7%a4%d7%a8-%d7%94%d7%a7%d7%a1%d7%9e%d7%99%d7%9d-%d7%94%d7%92%d7%93%d7%95%d7%9c-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=5VMJY095Bdw&list=PL4CFD7A57188E27EF') #English
	addDir(addonString(10420).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1532.jpg',addonString(104200).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''היה היה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=418&series_name=%d7%94%d7%99%d7%94%20%d7%94%d7%99%d7%94%20%3a%20%d7%94%d7%90%d7%93%d7%9d%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f418%2fonce-upon-a-time-man-%d7%94%d7%99%d7%94-%d7%94%d7%99%d7%94-%d7%94%d7%90%d7%93%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&sdarot=series_id=440&series_name=%d7%94%d7%99%d7%94%20%d7%94%d7%99%d7%94%20%3a%20%d7%94%d7%97%d7%99%d7%99%d7%9d%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f440%2fonce-upon-a-time-life-%d7%94%d7%99%d7%94-%d7%94%d7%99%d7%94-%d7%94%d7%97%d7%99%d7%99%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&sdarot=series_id=803&series_name=%d7%94%d7%99%d7%94%20%d7%94%d7%99%d7%94%20%3a%20%d7%94%d7%97%d7%9c%d7%9c%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f803%2fonce-upon-a-time-space-%d7%94%d7%99%d7%94-%d7%94%d7%99%d7%94-%d7%94%d7%97%d7%9c%d7%9c-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&sdarot=series_id=575&series_name=%d7%94%d7%99%d7%94%20%d7%94%d7%99%d7%94%20%3a%20%d7%9b%d7%93%d7%95%d7%a8%20%d7%94%d7%90%d7%a8%d7%a5%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f575%2fonce-upon-a-time-planet-earth-%d7%94%d7%99%d7%94-%d7%94%d7%99%d7%94-%d7%9b%d7%93%d7%95%d7%a8-%d7%94%d7%90%d7%a8%d7%a5-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&sdarot=series_id=785&series_name=%d7%94%d7%99%d7%94%20%d7%94%d7%99%d7%94%20%3a%20%d7%9e%d7%9e%d7%a6%d7%99%d7%90%d7%99%d7%9d%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f785%2fonce-upon-a-time-the-discoverers-%d7%94%d7%99%d7%94-%d7%94%d7%99%d7%94-%d7%9e%d7%9e%d7%a6%d7%99%d7%90%d7%99%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a4%d7%a8%d7%a7%d7%99%d7%9d%20%d7%9e%d7%9c%d7%90%d7%99%d7%9d&url=seasonId%3d2914073')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=5&module=wallavod&name=%d7%94%d7%99%d7%94%20%d7%94%d7%99%d7%94&url=seriesId%3d2520965')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=5&module=wallavod&name=%d7%94%d7%99%d7%94%20%d7%94%d7%99%d7%94%20%d7%94%d7%97%d7%99%d7%99%d7%9d&url=seriesId%3d2520985')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=5&module=wallavod&name=%d7%94%d7%99%d7%94%20%d7%94%d7%99%d7%94%20%d7%9b%d7%93%d7%95%d7%a8%20%d7%94%d7%90%d7%a8%d7%a5&url=seriesId%3d2521001')
		list.append('&youtube_pl=PLPO4_vX2WeIV8QjNMKILbbGXwxY0H3jgZ')
		list.append('&youtube_pl=PLXMxuZI8uq9KidUj9TVY3PHQlYbesoHoL')
		list.append('&youtube_pl=PLaKQk3jt0eydFOgVJq5z9VjANdEokSzwK')
		list.append('&youtube_pl=PL7sOvsxkL3kvJJKw4pKWvI1z3yxjmy2or')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLtVMs6v6Q1Ga-UNtigCi04dQHk-ETRVgG') #English
	addDir(addonString(10421).encode('utf-8'),list,17,'http://msc.wcdn.co.il/archive/1239471-54.jpg',addonString(104210).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://cnemacentre.com/wp-content/uploads/images/show-images/once-upon-a-time-man-1.jpg"))
	
	'''הדרדסים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=236&series_name=%d7%94%d7%93%d7%a8%d7%93%d7%a1%d7%99%d7%9d%20-%20%d7%9e%d7%93%d7%95%d7%91%d7%91&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f236%2fthe-smurfs-%d7%94%d7%93%d7%a8%d7%93%d7%a1%d7%99%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&hotVOD=http%3a%2f%2fhot.ynet.co.il%2fExt%2fComp%2fHot%2fTopSeriesPlayer_Hot%2fCdaTopSeriesPlayer_VidItems_Hot%2f0%2c13031%2cL-10842-525-0-0%2c00.html',)
		list.append('&hotVOD=http%3A%2F%2Fhot.ynet.co.il%2FCmn%2FApp%2FVideo%2FCmmAppVideoApi_AjaxItems%2F0%2C13776%2C48507-0%2C00.html')
		list.append('&youtube_pl=PL66F75CE8DFB7A2A2')
		list.append('&youtube_pl=PLo3vmw8N0knb9tZuIy7AR9fMPTUzr1oiI')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLaE8D0PEpUTtHl3NzB3VfscnmW68cZC58')
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=PLITCTw1CghePN4J1nA4hwRzKaxGhxlV4e')
	
	addDir(addonString(10422).encode('utf-8'),list,17,'http://f.nanafiles.co.il/upload/Xternal/IsraBlog/73/34/75/753473/misc/23130510.jpg',addonString(104220).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://www.pop-cultured.net/wp-content/uploads/2015/04/The-Smurfs.jpg"))

	'''הזרבובים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1313&series_name=%d7%94%d7%96%d7%a8%d7%91%d7%95%d7%91%d7%99%d7%9d&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1313%2fthe-snorks-%d7%94%d7%96%d7%a8%d7%91%d7%95%d7%91%d7%99%d7%9d')
		list.append('&youtube_id=1BgMQNYKatk') #Hebrew
		list.append('&youtube_pl=PLR7DTcU2p0QiY-wI8KC6f01uzKLDZcuAc') #Broken
	addDir(addonString(10423).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/1313.jpg',addonString(104230).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''החתולים הסמוראים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLR7DTcU2p0QhPmznEmitRHkv5RcUG3E-s') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLS4APdRj5MZdhdNEmwWUcZL_Tx_skioQX') #English
	addDir(addonString(10424).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1147.jpg',addonString(104240).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''היתקליף'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a4%d7%a8%d7%a7%d7%99%d7%9d%20%d7%9e%d7%9c%d7%90%d7%99%d7%9d&url=seasonId%3d2549973')
	
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL3qYiMswhauCyACTWt3otYgpPxWitR8hf')
		list.append('&youtube_pl=PLAEyhCIv-X253BV8VQJ3agJSLCnTTVpLG')
	
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=PLWBDfHynTzdwgWWw1olAWXTlUeJKvRYpU')
		list.append('&youtube_pl=')	

	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=PLovF9Z5TJjw-oEbBB3iGcKEXpk5JDnsiO')
		list.append('&youtube_pl=')	
		
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=PLdLOL3PeA3mrqjMcLeAhjMYws7945WkXB')
		list.append('&youtube_pl=')
		
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PLc6qwHwxvejYiJh5xbMlwu1It61HWgJSb')
		list.append('&youtube_pl=')
	
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=PLt_luoZum2FHcglJhP9YzZumJeMhvUVer')
		list.append('&youtube_pl=')

	addDir(addonString(10626).encode('utf-8'),list,17,'http://vignette4.wikia.nocookie.net/heathcliff/images/2/25/Heathcliff8.jpg/revision/latest?cb=20130709224249',addonString(106260).encode('utf-8'),'1',50, getAddonFanart(background, custom="https://i.ytimg.com/vi/Pa6TTBsMduE/maxresdefault.jpg"))
	
	'''הלב'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=745&series_name=%d7%94%d7%9c%d7%91%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f745%2fmarco-%d7%94%d7%9c%d7%91-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PL_8KXLhQVQMLx3W2W6YXTmaNHoPmlLl28')
	addDir(addonString(10425).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/745.jpg',addonString(104250).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''הלו קיטי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1684&series_name=%d7%94%d7%a8%d7%a4%d7%aa%d7%a7%d7%90%d7%95%d7%aa%20%d7%94%d7%9c%d7%95%20%d7%a7%d7%99%d7%98%d7%99%20%d7%95%d7%97%d7%91%d7%a8%d7%99%d7%9d%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1684%2fhello-kitty-and-friends-%d7%94%d7%a8%d7%a4%d7%aa%d7%a7%d7%90%d7%95%d7%aa-%d7%94%d7%9c%d7%95-%d7%a7%d7%99%d7%98%d7%99-%d7%95%d7%97%d7%91%d7%a8%d7%99%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL_li6wrWZhCA-MeGb1AR8BCsQLpzXkdqq') #English
	addDir(addonString(10721).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1684.jpg',addonString(107210).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES104F(General_LanguageL, background, background2) #סדרות - הנוקמים: לוחמי העל
	
	'''המומינים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=366&series_name=%d7%94%d7%9e%d7%95%d7%9e%d7%99%d7%a0%d7%99%d7%9d%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f366%2fthe-moomins-%d7%94%d7%9e%d7%95%d7%9e%d7%99%d7%a0%d7%99%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLofb-8yEl5BTeMeGHneOhJaETOrMWewPV')
		list.append('&youtube_pl=PL_8KXLhQVQMLvEJlwakyjEeFfOgGQKaCo')
		list.append('&youtube_pl=PL_8KXLhQVQMLB8AzFqkq5Tg7c_8ZX8RRb')
		list.append('&youtube_pl=PLN0EJVTzRDL-IJiTK4_B1ni8tlRNQvaBg')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLZs0gQed9tMS75zW8XwafIT_nRjYOg7Tn') #English
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=PL3Fa6uLkHmwYTX2ZNzgIk4nqCwgHjssH8') #	
		
	addDir(addonString(10427).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/366.jpg',addonString(104270).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://www.licensing.biz/files/0%200moo1.jpg"))
	
	'''המופע של לולו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=460&series_name=%d7%94%d7%9e%d7%95%d7%a4%d7%a2%20%d7%a9%d7%9c%20%d7%9c%d7%95%d7%9c%d7%95%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f460%2fthe-little-lulu-show-%d7%94%d7%9e%d7%95%d7%a4%d7%a2-%d7%a9%d7%9c-%d7%9c%d7%95%d7%9c%d7%95-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLVH181b17p3ZfXPIemTyuQInMBUaf6bXH')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL9Tf3rDOT4eW8jTFyBzZd4f9y4lix95Td') #English
	addDir(addonString(10428).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/460.jpg',addonString(104280).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://orig01.deviantart.net/efcd/f/2013/070/c/b/lulu_loves_tubby_by_re_ed-d5xrhne.jpg"))
	
	'''המעופפים הנועזים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1387&series_name=%d7%94%d7%9e%d7%a2%d7%95%d7%a4%d7%a4%d7%99%d7%9d%20%d7%94%d7%a0%d7%95%d7%a2%d7%96%d7%99%d7%9d%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1387%2fthe-little-flying-bears-%d7%94%d7%9e%d7%a2%d7%95%d7%a4%d7%a4%d7%99%d7%9d-%d7%94%d7%a0%d7%95%d7%a2%d7%96%d7%99%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLR7DTcU2p0QhYwFJuI0zFXFmAN-q6n4A0')
		list.append('&youtube_pl=PL_8KXLhQVQMLhguXwe-d2HjvficZsfbEj')
	if 'Slovak' in General_LanguageL:
		list.append('&youtube_pl=PLHbwPevLSfBRPuKWOrtxYDPlbIntcfviv') #Slovak
	if 'Croatian' in General_LanguageL:
		list.append('&youtube_pl=PL741A6F9BEA016A4E') #Croatian
	addDir(addonString(10430).encode('utf-8'),list,17,'http://upload.wikimedia.org/wikipedia/he/archive/e/e8/20060406072630!Flying_bears.jpg',addonString(104300).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''הנסיכה סיסי'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLOcNLH674qyGMBieogtC7uVwJr07JNIwL')
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=PLB7F61D166BE8DCFB')
	if 'Italiano' in General_LanguageL:
		list.append('&youtube_pl=PLA283C960B1F4F3C0')
		list.append('&youtube_pl=PLIsDVmWmkg9F3HM8EgHEXR8KWCjZXpFH1')
		list.append('&youtube_pl=PLA283C960B1F4F3C0')
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=PLU29Q4rBWGxGc7EMZ6-3Fawe4_n_QCp50')
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=PLB7F61D166BE8DCFB')
	if 'Dansk' in General_LanguageL:
		list.append('&youtube_pl=PLB7F61D166BE8DCFB')
		
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PLPZ1XC7N-0RUAtKzH6N987SwNqcp5W2XG')
	addDir(addonString(10492).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/he/thumb/d/d4/Princes_sissi.jpg/250px-Princes_sissi.jpg',addonString(104920).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://www.zastavki.com/pictures/originals/2013/Cartoons_Princess_Sissi_052166_.jpg", default=background2))
	
	'''הקוסם מארץ עוץ'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1078&series_name=%d7%94%d7%a7%d7%95%d7%a1%d7%9d%20%d7%9e%d7%90%d7%a8%d7%a5%20%d7%a2%d7%95%d7%a5%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1078%2fthe-wonderful-wizard-of-oz-%d7%94%d7%a7%d7%95%d7%a1%d7%9d-%d7%9e%d7%90%d7%a8%d7%a5-%d7%a2%d7%95%d7%a5-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLrm9dDLqwrHnZF86MMTIb-Q3LSKLGLTDQ')
		list.append('&youtube_pl=PL6cgUTK_W5ypfpul22dpMBSSOrya57p-X')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLS3SOlSTtJcDe-vQ-T46r_cB1U_ENAuKF') #English
		list.append('&youtube_pl=PLEUj0OPG9zo6opg5r3HH-78KWAw6FRw87') #English
	addDir(addonString(10431).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1078.jpg',addonString(104310).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''הענק הירוק'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1738&series_name=%d7%94%d7%a2%d7%a0%d7%a7%20%d7%94%d7%99%d7%a8%d7%95%d7%a7%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1738%2fthe-incredible-hulk-%d7%94%d7%a2%d7%a0%d7%a7-%d7%94%d7%99%d7%a8%d7%95%d7%a7-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PL5884348CE48B25A6')
	addDir(addonString(10432).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1738.jpg',addonString(104320).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''הפנתר הורוד'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1347&series_name=%d7%94%d7%a4%d7%a0%d7%aa%d7%a8%20%d7%94%d7%95%d7%95%d7%a8%d7%95%d7%93%20%2a%d7%90%d7%99%d7%9c%d7%9d%2a&summary&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1347%2fthe-pink-panther-cartoons-%d7%94%d7%a4%d7%a0%d7%aa%d7%a8-%d7%94%d7%95%d7%95%d7%a8%d7%95%d7%93-%d7%90%d7%99%d7%9c%d7%9d')
		list.append('&youtube_ch=PinkPanthersShow')
		list.append('&youtube_pl=PL6cOKIs-_ungXuX1X2Phr1EZegne4nk-h')
		list.append('&youtube_pl=PL459EEABC17B35E51')
	addDir(addonString(10433).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1347.jpg',addonString(104330).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''הפינגווינים ממדגסקר'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=416&series_name=%d7%94%d7%a4%d7%99%d7%a0%d7%92%d7%95%d7%95%d7%99%d7%a0%d7%99%d7%9d%20%d7%9e%d7%9e%d7%93%d7%92%d7%a1%d7%a7%d7%a8%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f416%2fthe-penguins-of-madagascar-%d7%94%d7%a4%d7%99%d7%a0%d7%92%d7%95%d7%95%d7%99%d7%a0%d7%99%d7%9d-%d7%9e%d7%9e%d7%93%d7%92%d7%a1%d7%a7%d7%a8-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLoAFYXAZNpvo-8i3MUajyo4vFDKGHmuWq') #English
	addDir(addonString(10435).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/416.jpg',addonString(108990).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''השוטר גרזן'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=589&series_name=%d7%94%d7%a9%d7%95%d7%98%d7%a8%20%d7%92%d7%a8%d7%96%d7%9f%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f589%2faxe-cop-%d7%94%d7%a9%d7%95%d7%98%d7%a8-%d7%92%d7%a8%d7%96%d7%9f-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLouuoG3C0vOBFIK7bFajnhA06ToGxa4VE') #English
	addDir(addonString(10436).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/589.jpg',addonString(108990).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''וולברין והאקס מן'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=823&series_name=%d7%95%d7%95%d7%9c%d7%91%d7%a8%d7%99%d7%9f%20%d7%95%d7%94%d7%90%d7%a7%d7%a1-%d7%9e%d7%9f%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f823%2fwolverine-and-the-x-men-%d7%95%d7%95%d7%9c%d7%91%d7%a8%d7%99%d7%9f-%d7%95%d7%94%d7%90%d7%a7%d7%a1-%d7%9e%d7%9f-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=PLR7DTcU2p0QhGsv3LuA3GnCJWjoPBCafl') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL5BE97D3FB689E48E') #English
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=PLB90059899E3B7CD0') #Portuguese
		list.append('&youtube_pl=PLzbICfFWEQ6frJukA5mzLSlpJbIARy37f') #Portuguese
	addDir(addonString(10437).encode('utf-8'),list,17,'http://i.ytimg.com/vi/_C9qXB0iPUY/hqdefault.jpg',addonString(104370).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''חבורת הצב המעופף'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=589&series_name=%d7%94%d7%a9%d7%95%d7%98%d7%a8%20%d7%92%d7%a8%d7%96%d7%9f%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f589%2faxe-cop-%d7%94%d7%a9%d7%95%d7%98%d7%a8-%d7%92%d7%a8%d7%96%d7%9f-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_id=IkzdDqeR7kQ')
	if 'Ukrainian' in General_LanguageL:
		list.append('&youtube_pl=PLHPshmrm2yZYGLnm5_DjUEDhovX0dJ85Z') #Ukrainian
	addDir(addonString(10438).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/1050.jpg',addonString(1084380).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''חברים בחווה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%f1%e5%f4%f8%20%f9%e8%e5%fa%f0%e9%f7&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2662395')
		list.append('&sdarot=season_id=1&series_id=646&series_name=%d7%97%d7%91%d7%a8%d7%99%d7%9d%20%d7%91%d7%97%d7%95%d7%95%d7%94%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f646%2fback-at-the-barnyard-%d7%97%d7%91%d7%a8%d7%99%d7%9d-%d7%91%d7%97%d7%95%d7%95%d7%94-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=PLYQo3vRiiRc4YxLzsXZV2dT7IGP3MF-N7')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLCnZ4jf66RYIuf5W_ZLYsgNYLaCr4nAs4') #English
	addDir(addonString(10439).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/646.jpg',addonString(108990).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))	
	
	'''חוש חש הבלש'''
	thumb = 'http://www.classickidstv.co.uk/wiki/images/5/51/Inspector_Gadget_The_Original_Series_R1.jpg'
	list = []
	if 'Hebrew' in General_LanguageL:
		thumb = 'http://www.sdarot.pm/media/series/1397.jpg'
		list.append('&sdarot=season_id=1&series_id=1397&series_name=%d7%97%d7%95%d7%a9%20%d7%97%d7%a9%20%d7%94%d7%91%d7%9c%d7%a9%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&summary=%d7%a1%d7%93%d7%a8%d7%aa%20%d7%90%d7%a0%d7%99%d7%9e%d7%a6%d7%99%d7%94%20%d7%a7%d7%95%d7%9e%d7%99%d7%aa%2c%20%22%d7%97%d7%95%d7%a9%20%d7%97%d7%a9%22%20%d7%94%d7%95%d7%90%20%d7%91%d7%9c%d7%a9%20%d7%9e%d7%a4%d7%95%d7%96%d7%a8%2c%20%d7%9e%d7%92%d7%95%d7%a9%d7%9d%20%d7%95%d7%9c%d7%90%20%d7%99%d7%95%d7%a6%d7%9c%d7%97%20%d7%a9%d7%91%d7%92%d7%95%d7%a4%d7%95%20%d7%94%d7%95%d7%a9%d7%aa%d7%9c%d7%95%20%d7%90%d7%99%d7%91%d7%a8%d7%99%d7%9d%20%d7%91%d7%99%d7%95%d7%a0%d7%99%d7%99%d7%9d%20%d7%a9%d7%95%d7%a0%d7%99%d7%9d%20%d7%90%d7%a9%d7%a8%20%d7%9e%d7%a7%d7%a0%d7%99%d7%9d%20%d7%9c%d7%95%20%d7%9b%d7%95%d7%97%d7%95%d7%aa%20%d7%a2%d7%9c%20%d7%98%d7%91%d7%a2%d7%99%d7%99%d7%9d.%20%d7%90%d7%95%d7%99%d7%91%d7%95%20%d7%94%d7%a2%d7%99%d7%a7%d7%a8%d7%99%20%d7%94%d7%95%d7%90%20%d7%93%d7%95%d7%a7%d7%98%d7%95%d7%a8%20%d7%a8%d7%a9%d7%a2%20%d7%95%d7%9e%d7%a1%d7%aa%d7%95%d7%a8%d7%99%2c%20%d7%9e%d7%a0%d7%94%d7%99%d7%92%20%d7%90%d7%a8%d7%92%d7%95%d7%9f%20%d7%a4%d7%a9%d7%a2.%20%d7%9c%d7%97%d7%95%d7%a9%20%d7%97%d7%a9%20%d7%a2%d7%95%d7%96%d7%a8%d7%99%d7%9d%20%d7%90%d7%97%d7%99%d7%99%d7%a0%d7%99%d7%aa%d7%95%20%d7%a7%d7%a8%d7%9f%20%d7%95%d7%9b%d7%9c%d7%91%d7%94%20%d7%94%d7%97%d7%9b%d7%9d%20%22%d7%9e%d7%95%d7%97%22%2c%20%d7%9b%d7%9e%d7%95%20%d7%92%d7%9d%20%d7%a9%d7%a0%d7%99%20%d7%94%d7%a8%d7%95%d7%91%d7%95%d7%98%d7%99%d7%9d%20%d7%a4%d7%99%d7%93%d7%92%27%d7%98%20%d7%95%d7%93%d7%99%d7%92%27%d7%98%20%d7%94%d7%9e%d7%9b%d7%95%d7%a0%d7%99%d7%9d%20%22%d7%94%d7%97%d7%95%d7%a9%d7%97%d7%a9%d7%99%d7%9d%22.%20%d7%94%d7%9d%20%d7%9e%d7%a6%d7%99%d7%9c%d7%99%d7%9d%20%d7%90%d7%95%d7%aa%d7%95%20%d7%9e%d7%a1%d7%9b%d7%a0%d7%95%d7%aa%20%d7%95%d7%9e%d7%9b%d7%95%d7%95%d7%a0%d7%99%d7%9d%20%d7%90%d7%95%d7%aa%d7%95%20%d7%9c%d7%a1%d7%99%d7%9b%d7%95%d7%9c%20%d7%94%d7%a4%d7%a9%d7%a2%20%d7%9e%d7%91%d7%9c%d7%99%20%d7%a9%d7%94%d7%95%d7%90%20%d7%9e%d7%95%d7%93%d7%a2%20%d7%9c%d7%9b%d7%9a%20%d7%91%d7%9b%d7%9c%d7%9c.&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1397%2finspector-gadget-%d7%97%d7%95%d7%a9-%d7%97%d7%a9-%d7%94%d7%91%d7%9c%d7%a9-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a4%d7%a8%d7%a7%d7%99%d7%9d%20%d7%9e%d7%9c%d7%90%d7%99%d7%9d&url=seasonId%3d2555838')
		list.append('&youtube_pl=PLcnOogeoQ4TrfP9mO57AQY543KTLaTl8N')
		list.append('&youtube_id=MbgrFDbE3b0')
		list.append('&youtube_id=kWmBP09MM9w')
		list.append('&youtube_id=P3gW3zPEhjY')
		list.append('&youtube_id=uj9miIc0Ow4')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLzsJ0eqQdfa6tDzsMSoC3cNFyhTLUW8Y-') #English
		list.append('&youtube_pl=PLWXd7CnPnkybfU-_26JRUtOR1-ItqJ6-l') #English
	addDir(addonString(10440).encode('utf-8'),list,17,thumb,addonString(104400).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://images7.alphacoders.com/478/478307.jpg"))
	
	'''חיות בקצר'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1565&series_name=%d7%97%d7%99%d7%95%d7%aa%20%d7%91%d7%a7%d7%a6%d7%a8%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1565%2falmost-naked-animals-%d7%97%d7%99%d7%95%d7%aa-%d7%91%d7%a7%d7%a6%d7%a8-%d7%9e%d7%93%d7%95%d7%91%d7%91')	
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLLSc-PLxC0fDK_KKFnOqYjpWZfeOlqBdz6uc5mk')
		list.append('&youtube_pl=PLa6NpPOElbKAbujKC5-PI_kqLP8Wv6qsL')
	addDir(addonString(10493).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1565.jpg',addonString(104930).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://tbivision.com/wp-content/uploads/2012/11/ANA_301_001.jpg"))
	
	'''חיים בביוב*'''
	list = []
	list.append('&sdarot=series_id=1605&series_name=%d7%97%d7%99%d7%99%d7%9d%20%d7%91%d7%91%d7%99%d7%95%d7%91%20-%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1605%2flarva-%d7%97%d7%99%d7%99%d7%9d-%d7%91%d7%91%d7%99%d7%95%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
	list.append('&youtube_pl=PLxA7z7YQAqR7OCDM5-Cc4O-Nuswd8ChZ7')
	list.append('&youtube_pl=PLCAz374llh8UZxgCmKrBgdxPbjv6DdV3W')
	list.append('&youtube_pl=PLVkmXbocRodPcTHEC9P2JtcO3xn1NbRz9')
	if 'Korean' in General_LanguageL:
		list.append('&youtube_pl=PLjDLgg_nO1v4dctdGzRJOy-yd0sHJk8oa')
	addDir(addonString(10441).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/1605.jpg',addonString(104410).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''חנונים ומפלצות'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1664&series_name=%d7%97%d7%a0%d7%95%d7%a0%d7%99%d7%9d%20%d7%95%d7%9e%d7%a4%d7%9c%d7%a6%d7%95%d7%aa%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1664%2fnerds-and-monsters-%d7%97%d7%a0%d7%95%d7%a0%d7%99%d7%9d-%d7%95%d7%9e%d7%a4%d7%9c%d7%a6%d7%95%d7%aa-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=PLXZL-qLQhCnYMJh0r02R7-9YUqDxyg3z0')
	addDir(addonString(10442).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1664.jpg',addonString(104420).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''חתולי הרעם 1'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1786&series_name=%d7%97%d7%aa%d7%95%d7%9c%d7%99%20%d7%94%d7%a8%d7%a2%d7%9d%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1786%2fthundercats-%d7%97%d7%aa%d7%95%d7%9c%d7%99-%d7%94%d7%a8%d7%a2%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_id=tVRhbs4wjhM')
		list.append('&youtube_id=ktSs9OT7Dqk')
		list.append('&youtube_id=xgu7gcM689A')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL4CFA334404DEC69F') #English
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLjiShxUr9GYBkN3-bYt5Y5P-vMPpaeHZQ')
	addDir(addonString(10443).encode('utf-8') + space + '1',list,17,'http://www.sdarot.pm/media/series/1786.jpg',addonString(104430).encode('utf-8'),'1',"",getAddonFanart(background, custom="http://cdn.buzzlie.com/wp-content/uploads/2015/05/thundercats3.jpg", default=background2))
	
	'''חתולי הרעם 2'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLcbFHwFk2aTDCIXkYyTavn8DO8kA5t7FE')
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=') #Spanish
	addDir(addonString(10443).encode('utf-8') + space + '2',list,17,'http://download.gamezone.com/uploads/image/data/1123265/article_post_width_news-thundercats.jpg','On the planet known as Third Earth, the Cats have lived and thrived for generations in the kingdom of Thundera. The Cats are led by Claudus, with his son and heir Lion-O. However, one night the kingdom is attacked by the Lizard army led by the evil sorcerer Mumm-Ra. With them, the Lizards bring technology (a concept unfamiliar to the Cats). Because of this, Thundera is destroyed, Claudus is killed by Mumm-Ra, and the rest of the Cats are enslaved.','1',"",getAddonFanart(background, custom="http://news.thundercats.ws/wp-content/uploads/sites/6/2011/11/Thundercats-Group-Shot_1321985048.jpg", default=background2))
	
	'''טאק וכוח הג'וג'ו'''
	thumb = 'https://upload.wikimedia.org/wikipedia/en/thumb/7/7e/Tak_and_Power_Of_Juju_-_Logo.PNG/250px-Tak_and_Power_Of_Juju_-_Logo.PNG'
	list = []
	if 'Hebrew' in General_LanguageL:
		thumb = 'http://www.sdarot.pm/media/series/1790.jpg'
		list.append('&sdarot=series_id=1790&series_name=%d7%98%d7%90%d7%a7%20%d7%95%d7%9b%d7%95%d7%97%20%d7%94%d7%92%27%d7%95%d7%92%27%d7%95%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1790%2ftak-and-the-power-of-juju-%d7%98%d7%90%d7%a7-%d7%95%d7%9b%d7%95%d7%97-%d7%94%d7%92-%d7%95%d7%92-%d7%95-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLPQjX_uthHq6OJLhZRr6G2jQtBMC8VIKr')
	addDir(addonString(10494).encode('utf-8'),list,17,thumb,addonString(104940).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://cdn.photonesta.com/images/www.search-best-cartoon.com/wallpapers/tak-and-the-power-of-juju/tak-and-the-power-of-juju-01.jpg"))
	
	'''טוב טוב הגמד'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1581&series_name=%d7%98%d7%95%d7%91%20%d7%98%d7%95%d7%91%20%d7%94%d7%92%d7%9e%d7%93%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1581%2fthe-world-of-david-the-gnome-%d7%98%d7%95%d7%91-%d7%98%d7%95%d7%91-%d7%94%d7%92%d7%9e%d7%93-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&dailymotion_pl=x4932d') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLrEuz9dJQmAkIYkhcB4iZpoOlUDnMNDif') #English
		list.append('&youtube_pl=PL0630E307D00F8411') #English
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PL72AD87F35AE91F6E') #French
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=PL9-GLKMfFv9WHO9fJcaCx9GeOF9q8-Lo1') #Italian

	addDir(addonString(10444).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1581.jpg',addonString(104440).encode('utf-8'),'1',50, getAddonFanart(background, custom="https://saturdaymourningcartoons.files.wordpress.com/2014/12/david-the-gnome.jpg"))
	
	'''טוטלי ספייס'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=462&series_name=%d7%98%d7%95%d7%98%d7%9c%d7%99%20%d7%a1%d7%a4%d7%99%d7%99%d7%a1%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f462%2ftotally-spies-%d7%98%d7%95%d7%98%d7%9c%d7%99-%d7%a1%d7%a4%d7%99%d7%99%d7%a1-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLFP5pUyg4YtCFkEzFyhKbFs2KL_8SxVFM') #English
		list.append('&youtube_pl=PLDIydMBGHDvKUHM_a0qca8Nrj1SxWwgO-') #English
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PLby7JALZWGy53rZr4yXo4BkjpwXLhmNFI') #Russian
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=PL37423D9401198B55') #Serbian
	addDir(addonString(10445).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/462.jpg',addonString(104450).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''טום וג'רי*'''
	list = []
	list.append('&youtube_pl=PLN0EJVTzRDL-jbMDnITZcYO48kE1Hv3mc')
	list.append('&youtube_pl=PLs3DueTtwGGppFDT2xv9zVBf4mz6RuOLj')
	list.append('&youtube_pl=PL6hnqKp_bygo_2MFE6j3WWLitYXwhHGx3')
	addDir(addonString(10446).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/he/thumb/2/23/Tomjerrylogo40s.jpg/280px-Tomjerrylogo40s.jpg',addonString(104460).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''טום סויר'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1438&series_name=%d7%98%d7%95%d7%9d%20%d7%a1%d7%95%d7%99%d7%99%d7%a8%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1438%2ftom-sawyer-%d7%98%d7%95%d7%9d-%d7%a1%d7%95%d7%99%d7%99%d7%a8-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLStjg118dmDO9ReHlRp5abjNBR5yJ1kpK') #English
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLGU_lKDKx9IZHY1DfhcKaceLT_WJEc0wL') #Spanish
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PLiItfFtbus3Dq0IueYp8XJOkWXwDW7K1V') #French
	addDir(addonString(10447).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1438.jpg',addonString(104470).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''טורבו צוות פגז'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1615&series_name=%d7%98%d7%95%d7%a8%d7%91%d7%95%20%d7%a6%d7%95%d7%95%d7%aa%20%d7%a4%d7%92%d7%96%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1615%2fturbo-fast-%d7%98%d7%95%d7%a8%d7%91%d7%95-%d7%a6%d7%95%d7%95%d7%aa-%d7%a4%d7%92%d7%96-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	if 'English' in General_LanguageL:
		list.append('&youtube_ch=UCsW-cNhlQipm64Nw6YfRzDg') #English
	addDir(addonString(10448).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1615.jpg',addonString(104480).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''טיטוף'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1615&series_name=%d7%98%d7%95%d7%a8%d7%91%d7%95%20%d7%a6%d7%95%d7%95%d7%aa%20%d7%a4%d7%92%d7%96%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1615%2fturbo-fast-%d7%98%d7%95%d7%a8%d7%91%d7%95-%d7%a6%d7%95%d7%95%d7%aa-%d7%a4%d7%92%d7%96-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLVaxnIxB-SSnTOY3UdnW1ydxMLkv2m3vr')	
	addDir(addonString(10449).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/661.jpg',addonString(104490).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''כלב חשאי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=778&series_name=%d7%9b%d7%9c%d7%91%20%d7%97%d7%a9%d7%90%d7%99%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f778%2ftuff-puppy-%d7%9b%d7%9c%d7%91-%d7%97%d7%a9%d7%90%d7%99-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%eb%ec%e1%20%e7%f9%e0%e9&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2503183')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%ec%fa%f4%e5%f1%20%e0%fa%20%e1%ec%e9%e9%f7&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2853374')
		list.append('&wallaNew2=http://nickjr.walla.co.il/')
		list.append('&youtube_id=70mN9C1VigM')
		list.append('&youtube_id=EZg4C1koHJE')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL0FiPoE71AM1UH15ojxY5C5vj5uSv6eaz')
	addDir(addonString(10450).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/778.jpg',addonString(104500).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://images5.fanpop.com/image/photos/31100000/Puppy-Punch-tuff-puppy-31170740-1024-768.jpg"))
	
	'''לאקי לוק'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1446&series_name=%d7%9c%d7%90%d7%a7%d7%99%20%d7%9c%d7%95%d7%a7%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1446%2flucky-luke-%d7%9c%d7%90%d7%a7%d7%99-%d7%9c%d7%95%d7%a7-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLVe-nXljLcEw1z0KRytUl_Lssg8qujUCH')
	if 'English' in General_LanguageL:	
		list.append('&youtube_pl=PLCD5B9AD1151F3E0B') #English
		list.append('&youtube_pl=PLBuQjTjLLLgzAxxC6lysDD-WO6x0CPFBQ') #English
	addDir(addonString(10451).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1446.jpg',addonString(104510).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES104H(General_LanguageL, background, background2) #צ'ימה
	
	'''מאיה ומיגל'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1264&series_name=%d7%9e%d7%90%d7%99%d7%94%20%d7%95%d7%9e%d7%99%d7%92%d7%9c%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1264%2fmaya-miguel-%d7%9e%d7%90%d7%99%d7%94-%d7%95%d7%9e%d7%99%d7%92%d7%9c-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=PLvx5W_59a3514Kf8NIdDRBoFhe3TQUKds')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL_ZweOlCch9Y3VgJQMq44umQJJdWBtimm') #English
	addDir(addonString(10452).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1264.jpg',addonString(104520).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''מאשה והדוב*'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&dailymotion_pl=x47br7')
	if 'Russian' in General_LanguageL or 1 + 1 == 2:
		list.append('&youtube_pl=PLXnIohISHNIuH97pzQYV5O96-Q7-VwhRV')
		list.append('&youtube_pl=PL4-zn_348odBKcfUeZznqhkc_-UYtWnep')
		list.append('&youtube_pl=PLdAdTJgxziWAXNLIR5oeHbUT8HDnXOjAt')
		list.append('&youtube_pl=PLXnIohISHNIvsnUNe8RwvhksUSFzdQsiT')
		list.append('&youtube_pl=PLPYC---L3hwl7yImm5Rk3Iol0Efln7CDe')
	addDir(addonString(10241).encode('utf-8'),list,17,'http://assets3.mi-web.org/foto_miniaturas/0012/5812/Masha_Oso028_mediano.jpg?1368008744',addonString(102410).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://www.clementoni.com/media/prod/26046/es/masha-and-the-bear-60-piezas-supercolor-puzzle_lpV639i.jpg"))
	
	'''מולי וצומי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=2077&series_name=%d7%9e%d7%95%d7%9c%d7%99%20%d7%95%d7%a6%d7%95%d7%9e%d7%99&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f2077%2fmuli-and-tzumi-%d7%9e%d7%95%d7%9c%d7%99-%d7%95%d7%a6%d7%95%d7%9e%d7%99')
		list.append('&youtube_pl=PLfcYs4SRZfuJHmb8y_BpUpzAsm1guoAlK')
	addDir(addonString(10453).encode('utf-8'),list,17,'http://www.yap.co.il/prdPics/4309_desc3_2_1_1390393153.jpg',addonString(104530).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
		
	'''מונסטר היי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1594&series_name=%d7%9e%d7%95%d7%a0%d7%a1%d7%98%d7%a8%20%d7%94%d7%99%d7%99%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1594%2fmonster-high-%d7%9e%d7%95%d7%a0%d7%a1%d7%98%d7%a8-%d7%94%d7%99%d7%99-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLq7XN-iC2Vqxe8H7-GCZoKzYTKmpDwFpz') #English
		list.append('&youtube_pl=PLq7XN-iC2Vqz1MIctpY7goTjf1mZv2F9Q') #English
		list.append('&youtube_pl=PLq7XN-iC2VqyFHnAVKvvATh7DJximiNrq') #English
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLq7XN-iC2VqyruMLBI8MdvJjLub5URhtY') #Spanish
	
	addDir(addonString(10454).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1594.jpg',addonString(104540).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''מועדון ווינX'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=456&series_name=%d7%9e%d7%95%d7%a2%d7%93%d7%95%d7%9f%20%d7%95%d7%95%d7%99%d7%a0%d7%a7%d7%a1%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f456%2fwinx-club-%d7%9e%d7%95%d7%a2%d7%93%d7%95%d7%9f-%d7%95%d7%95%d7%99%d7%a0%d7%a7%d7%a1-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=PLby7JALZWGy6xV7aec0CC9LFdeaEgsM_g') #Hebrew
		list.append('&youtube_pl=PLsvJJHNjHidCEbC_IM4LC7Mp56wQ-3A4H') #Hebrew
		
		list.append('&dailymotion_pl=x3j85r') #S4
		list.append('&dailymotion_pl=x3v205') #S5
		list.append('&dailymotion_pl=x3w6u5') #S6
		list.append('&dailymotion_pl=x3tlpa') #S6
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLJg404csJ854N08KuIMR9prlfveYScLIz') #English
		list.append('&dailymotion_pl=x3ibmc') #S6
		list.append('&dailymotion_pl=x3rvbd') #S7
		
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLQvqWmQTCX-jR_xRqX-ouF8dbWC0yNz9t') #Spanish
		list.append('&youtube_pl=PLQvqWmQTCX-jBHlk7d79ZSeHLc5nV8Rzk') #Spanish
		
		list.append('&dailymotion_pl=x40gnb') #S3
		list.append('&dailymotion_pl=x449l3') #S7
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PL80E8353D11F3BBE4') #French
	addDir(addonString(10455).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/456.jpg',addonString(104550).encode('utf-8'),'1',"",getAddonFanart(background, custom="https://i.ytimg.com/vi/zMSgF3xdHZ4/maxresdefault.jpg", default=background2))
	
	'''מחנה הפחד'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1616&series_name=%d7%9e%d7%97%d7%a0%d7%94%20%d7%94%d7%a4%d7%97%d7%93%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1616%2fcamp-lakebottom-%d7%9e%d7%97%d7%a0%d7%94-%d7%94%d7%a4%d7%97%d7%93-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLGPMEy1jNEDZtmvAZQoddwLgK0GoAJGeV') #English
	addDir(addonString(10456).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1616.jpg',addonString(104560).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''מטורללים'''
	list = [] #Nick #Hot
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1667&series_name=%d7%9e%d7%98%d7%95%d7%a8%d7%9c%d7%9c%d7%99%d7%9d%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1667%2ftrolls-of-troy-%d7%9e%d7%98%d7%95%d7%a8%d7%9c%d7%9c%d7%99%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=PLf5Wskorw9t6lSLxSpE9acGNYSGkirYp0')
	addDir(addonString(10457).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/1667.jpg',addonString(104570).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
		
	'''מייטי מקס'''
	thumb = 'http://ia.media-imdb.com/images/M/MV5BMTkyMzE3MDIzMl5BMl5BanBnXkFtZTcwODEzNjMyMQ@@._V1_SX214_AL_.jpg'
	fanart = 'http://orig10.deviantart.net/0afb/f/2015/103/7/e/mightymax_by_fooray-d8pjomo.jpg'
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&dailymotion_id=x17xn3s')
		list.append('&youtube_id=4t-8ebOB_I8') #S2E1
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLBA98D24AE96BD6CB') #S1-2
		list.append('&youtube_pl=PLWwnLtb5fzbaRqn_PpAQSXNOVyue_S8Bq') #S1
	if 'French' in General_LanguageL:
		list.append('&dailymotion_pl=xt1pg')
	if 'Italian' in General_LanguageL:
		list.append('&dailymotion_pl=x18qqjs')
	if 'Catalan' in General_LanguageL:
		list.append('&dailymotion_pl=x41v8u')
	
	addDir(addonString(10495).encode('utf-8'),list,17,thumb,addonString(104950).encode('utf-8'),'1',"", getAddonFanart(background, custom=fanart, default=background2))
	
	'''מיקי מאוס'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1490&series_name=%d7%9e%d7%99%d7%a7%d7%99%20%d7%9e%d7%90%d7%95%d7%a1&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1490%2fmickey-mouse-%d7%9e%d7%99%d7%a7%d7%99-%d7%9e%d7%90%d7%95%d7%a1')
		list.append('&youtube_pl=PLRnOaTF6ebYr6lGEgf6g338-tVEdbDrpQ') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLzmYALoiB7Iu06wVm_j9wNLp3kMIMGprt') #English
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLuVSRZz8Gp_SRZiUdbGQiDyVeWtGBignf') #Spanish
	if 'Catalan' in General_LanguageL:
		list.append('&youtube_pl=PLuVSRZz8Gp_S3LydxhuuBrgOGFWxwta5i') #Catalan
	addDir(addonString(10458).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1490.jpg',addonString(104580).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://2.bp.blogspot.com/-D9F8GNiT1yg/Uh-cUtD8p-I/AAAAAAAABY0/2ja3WYAkTcY/s1600/Disney-Mickey-Mouse-Characters-Wallpaper.jpg"))
	
	'''מיקמק'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=861&series_name=%d7%9e%d7%99%d7%a7%d7%9e%d7%a7%20%3a%20%d7%94%d7%a1%d7%93%d7%a8%d7%94%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f861%2fmikmak-hasidra-%d7%9e%d7%99%d7%a7%d7%9e%d7%a7-%d7%94%d7%a1%d7%93%d7%a8%d7%94-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PL663sDNTault52-VzCCu4w0CfnoAtrmRg')
		list.append('&youtube_pl=PL663sDNTaulu5KpP6eyz9Xr3caOQUDEl_')
		list.append('&youtube_pl=PL663sDNTault52-VzCCu4w0CfnoAtrmRg')
		list.append('&youtube_id=1CshWmAFinY')
		list.append('&youtube_id=a5WNY-FMMyQ')
	addDir(addonString(10459).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/861.jpg',addonString(104590).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''מלחמת הכוכבים: המורדים'''
	CATEGORIES104G(General_LanguageL, background, background2)
	
	'''פליקס הארנב'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1689&series_name=%d7%9e%d7%9b%d7%aa%d7%91%d7%99%d7%9d%20%d7%9e%d7%a4%d7%9c%d7%99%d7%a7%d7%a1%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1689%2fletters-from-felix-%d7%9e%d7%9b%d7%aa%d7%91%d7%99%d7%9d-%d7%9e%d7%a4%d7%9c%d7%99%d7%a7%d7%a1-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLtcsu9_D0HqT0GQQOAZa0IojDpHPo6bOf') #Hebrew
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=PLNaowF97PdRVElGqD9b2O63gZ3E3rkdTn') #German
	addDir(addonString(10460).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1689.jpg',addonString(104600).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''מסביב לעולם ב80 יום'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=2098&series_name=%d7%9e%d7%a1%d7%91%d7%99%d7%91%20%d7%9c%d7%a2%d7%95%d7%9c%d7%9d%20%d7%91-80%20%d7%99%d7%95%d7%9d%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f2098%2faround-the-world-in-eighty-days-%d7%9e%d7%a1%d7%91%d7%99%d7%91-%d7%9c%d7%a2%d7%95%d7%9c%d7%9d-%d7%91-80-%d7%99%d7%95%d7%9d-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLZs0gQed9tMR0EebER8Ef3Kofil7DSTCc') #English
		list.append('&youtube_pl=PL743C68A0E8EC9204') #English
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=PL1BAF9E4D733BF48B') #Dutch
		list.append('&youtube_pl=PL250AA5EDA0ED364A1') #Dutch
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=PL9-GLKMfFv9UxrkzbGzPjtZSlk25xmS6T') #Italian
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PL39408FA9CAE12F76') #French
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PL859115B075C9FC75') #Russian
		list.append('&youtube_pl=PL7BCE3AB0D5BBD87C') #Russian
	
	addDir(addonString(10461).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/2098.jpg',addonString(104610).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''מסיפורי המלך בבר'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1657&series_name=%d7%9e%d7%a1%d7%99%d7%a4%d7%95%d7%a8%d7%99%20%d7%94%d7%9e%d7%9c%d7%9a%20%d7%91%d7%91%d7%a8%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1657%2fbabar-%d7%9e%d7%a1%d7%99%d7%a4%d7%95%d7%a8%d7%99-%d7%94%d7%9e%d7%9c%d7%9a-%d7%91%d7%91%d7%a8-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLqcqK3dfusFJIWQ5DU_EUFPoRiPIdKj7H') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_ch=UCFe57hUldf3jWklSRCuztgg') #English
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=PLIB_OgW7nli5rQJ3MfAEg5xLpo3FuMHUS')
		
	addDir(addonString(10462).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/1657.jpg',addonString(104620).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''מפלצת בטעות'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=819&series_name=%d7%9e%d7%a4%d7%9c%d7%a6%d7%aa%20%d7%91%d7%98%d7%a2%d7%95%d7%aa%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f819%2fmonster-by-mistake-%d7%9e%d7%a4%d7%9c%d7%a6%d7%aa-%d7%91%d7%98%d7%a2%d7%95%d7%aa-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLCWuG3cXW_gboBSGpMvkHlNxqY0pG1HII') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_id=H2WSULnUyTA') #English
	addDir(addonString(10463).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/819.jpg',addonString(104630).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''מפעל הגיבורים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%ee%f4%f2%ec%20%e4%e2%e9%e1%e5%f8%e9%ed&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f1883282')
		list.append('&youtube_pl=PLuQCYUv97StTYPWiHQ70kxF6MLp_h8jEW') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLpXGrlS-zgkq5uuIfhl0hvocjnvOeXAcm') #English
	addDir(addonString(10487).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/HeroFactoryLogo.svg/200px-HeroFactoryLogo.svg.png',addonString(104870).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''מקס ושרד'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%ee%f7%f1%20%e5%f9%f8%e3&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2851543')
		list.append('&youtube_pl=') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLugK-QLYyzSwRCsGOlt_fIN97UTEp5ulz') #English
	addDir(addonString(10828).encode('utf-8'),list,6,'https://upload.wikimedia.org/wikipedia/en/1/1f/Max_%26_Shred_show_title_logo.png',addonString(108280).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))

	'''מקס סטיל''' #HOT VOD YOUNG / SERET IL
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1637&series_name=%d7%9e%d7%a7%d7%a1%20%d7%a1%d7%98%d7%99%d7%9c%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1637%2fmax-steel-%d7%9e%d7%a7%d7%a1-%d7%a1%d7%98%d7%99%d7%9c-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLqXC-FsML6on-N7kHFe4OLhTXZEPmj8A4') #English
		list.append('&youtube_pl=PLNVb4XeGx1kIO7u39mIT88QDxBgsF-dUA') #English
		list.append('&youtube_pl=PLqXC-PLEqwPYouHqaJwNaYQ_4vv7reSQXjO9gXO') #English
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=PLc6DM_HUHuJXuawQJtspo2-LMNEzp5z1a') #German
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=PLc6DM_HUHuJVKREFwsZx9EcVL7YmEk4Ar') #Greek
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLc6DM_HUHuJXa9FOdAzxUAPtGsqtbI0nP') #Spanish
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=PLc6DM_HUHuJXPFouQplvWEPcJZWJfZ2KS') #Turkish
	if 'Brazilian' in General_LanguageL:
		list.append('&youtube_pl=PLc6DM_HUHuJXXqRy06F3n3ixMvG1mztA8') #Brazilian

	addDir(addonString(10464).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/1637.jpg',addonString(104640).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES104E(General_LanguageL, background, background2) #משוגעגע
	
	'''משטרת האגדות'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLR7DTcU2p0QiaEmc56lGHMpxW4ladE93X') #Hebrew
		list.append('&youtube_pl=PLWS_jfm9LLlk2ONsN9KrpUaublCKZuCY8') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL-b1n-EI-zIIRAwSuMTHbhrYUX4aeHNHL') #English
	addDir(addonString(10465).encode('utf-8'),list,17,'http://www.tvland.co.il/Pics/mishterethaagadotbig.jpg',addonString(104650).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''משפחת סימפסון'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=57&series_name=%d7%9e%d7%a9%d7%a4%d7%97%d7%aa%20%d7%a1%d7%99%d7%9e%d7%a4%d7%a1%d7%95%d7%9f%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f57%2fthe-simpsons-%d7%9e%d7%a9%d7%a4%d7%97%d7%aa-%d7%a1%d7%99%d7%9e%d7%a4%d7%a1%d7%95%d7%9f-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=PLeY7w-PAPTxgVYpTYrGWr01Bbqf-FcXNn')
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_id=fZeepoLKRes') #Spanish
	addDir(addonString(10466).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/57.jpg',addonString(104660).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://media.comicbook.com/uploads1/2014/10/the-simpsons-tv-series-cast-wallpaper-109911.jpeg"))

	'''נארוטו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=612&series_name=%d7%a0%d7%90%d7%a8%d7%95%d7%98%d7%95%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f612%2fnaruto-%d7%a0%d7%90%d7%a8%d7%95%d7%98%d7%95-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL6PhB-zwNh9ZLpW3fvZ3O_8AoU5qw2OkD') #English
	addDir(addonString(10467).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/612.jpg',addonString(104670).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES104J(General_LanguageL, background, background2) #נילס הולגרסון
	
	CATEGORIES104N(General_LanguageL, background, background2) #נינג'גו - מאסטר הספינג'יצו
	
	CATEGORIES104M(General_LanguageL, background, background2) #סאקורה לוכדת הקלפים
	
	'''סברינה המכשפה הצעירה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1154&series_name=%d7%a1%d7%91%d7%a8%d7%99%d7%a0%d7%94%20%d7%94%d7%9e%d7%9b%d7%a9%d7%a4%d7%94%20%d7%94%d7%a6%d7%a2%d7%99%d7%a8%d7%94%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1154%2fsabrina-the-animated-series-%d7%a1%d7%91%d7%a8%d7%99%d7%a0%d7%94-%d7%94%d7%9e%d7%9b%d7%a9%d7%a4%d7%94-%d7%94%d7%a6%d7%a2%d7%99%d7%a8%d7%94-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLkGxGUmfDKPkOOYKrd8gpnwDa40NsBmUv') #Hebrew
		list.append('&youtube_pl=PLIR_swtdpOGk6ckBBUEvuorr5Dzh7gtze') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLqcNVz8UuCsJRznsI9nDbIgVL-aJ6daZy') #English
		list.append('&youtube_pl=PLk0ITqthka1BOtOa4uq3CGk3rVyMlZSry') #English
	addDir(addonString(10469).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1154.jpg',addonString(104690).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''סוניק X'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=459&series_name=sonic-x-%d7%a1%d7%95%d7%a0%d7%99%d7%a7-x-%d7%9e%d7%93%d7%95%d7%91%d7%91&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f459%2fsonic-x-%d7%a1%d7%95%d7%a0%d7%99%d7%a7-x-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_id=AGuOahTZjjo') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLjkvw-XFL7UO4W3PcxdjXVWl-CNhm3DC7') #English
		list.append('&youtube_pl=PLEHMqhHsi5QWX6Sd2yK5irNNPFD5QSWWz') #English
		list.append('&youtube_pl=PLYEPskF2zHF6ztSidztkpjbi_7IqBDcMx') #English
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=PLk_S0ES7k_qA9lmnEtiTDzV6UxrkuKApr') #Polish
		list.append('&youtube_pl=PL-OG25DoK_1WRj1JafwlyxzbzqzqQgzy6') #Polish
	addDir(addonString(10470).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/459.jpg',addonString(104700).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''סוניק הקיפוד'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=5&module=wallavod&name=%d7%a1%d7%95%d7%a0%d7%99%d7%a7&url=seriesId%3d2847535')
		list.append('&sdarot=series_id=1710&series_name=%d7%a1%d7%95%d7%a0%d7%99%d7%a7%20-%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1710%2fsonic-the-hedgehog-%d7%a1%d7%95%d7%a0%d7%99%d7%a7-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&sdarot=season_id=1&series_id=657&series_name=%d7%a1%d7%95%d7%9c%20%d7%90%d7%99%d7%98%d7%a8%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f657%2fsoul-eater-%d7%a1%d7%95%d7%9c-%d7%90%d7%99%d7%98%d7%a8-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&sdarot=season_id=1&series_id=459&series_name=%d7%a1%d7%95%d7%a0%d7%99%d7%a7%20X%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f459%2fsonic-x-%d7%a1%d7%95%d7%a0%d7%99%d7%a7-x-%d7%9e%d7%93%d7%95%d7%91%d7%91')	
		list.append('&sdarot=season_id=1&series_id=1886&series_name=%d7%a1%d7%95%d7%a0%d7%99%d7%a7%20%d7%91%d7%95%d7%9d%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1886%2fsonic-boom-%d7%a1%d7%95%d7%a0%d7%99%d7%a7-%d7%91%d7%95%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL8w7FER3tTVB9hNreSe1l_qVOV-bLtxY1') #English
		list.append('&youtube_pl=PL_LA4m8CuQky60SVswr5tFqQxqKB997iI') #English
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=PL9ieY-C9TKmJ5CrvBzjHaFT_M0M1pbP8o') #Portuguese
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLj8nCHarKPBNR5WeXivy6OXOMwiq13I4J') #Spanish
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PLEA183AF7E0AB5E03') #French
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=PL046656EF6D2E6674') #Dutch
	addDir(addonString(10471).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1518.jpg',addonString(104710).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES104K(General_LanguageL, background, background2) #סיפורי מוש
	CATEGORIES104Q(General_LanguageL, background, background2) #סיילור מון
	
	'''סמוראי ג'ק'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=781&series_name=%d7%a1%d7%9e%d7%95%d7%a8%d7%90%d7%99%20%d7%92%27%d7%a7%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f781%2fsamurai-jack-%d7%a1%d7%9e%d7%95%d7%a8%d7%90%d7%99-%d7%92-%d7%a7-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=ELPVbaRdOOKNE') #English
		list.append('&youtube_pl=EL4Pg00crNGI8') #English
		list.append('&youtube_pl=ELuFHychuxQ-8') #English
		list.append('&youtube_pl=PLegU20VWl5AVo8uIzYAkfxcrVbQOUV1ox') #English
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=PLF347DDA292C0B8D2') #Japanish
	addDir(addonString(10473).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/781.jpg',addonString(104730).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''סנדוקאן'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLR7DTcU2p0QgWYVQap5zPK0MkwJizYku_') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLL7dcgwYKsm1SSm_ats6bW7UQ61ADzw-X') #English
		list.append('&youtube_pl=PLA9E141AA1CEBEF5A') #English
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLfH8EZSX2voZXwKsPe5Yoi6ifBD7DrfDs') #Spanish
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=PL9873BAE8277C0C38') #Dutch
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PLF93CFD76BC5D322A') #French
	
	addDir(addonString(10474).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1308.jpg',addonString(104740).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''ספיידרמן (אוסף)'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=695&series_name=%d7%a1%d7%a4%d7%99%d7%99%d7%93%d7%a8%d7%9e%d7%9f%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f695%2fspider-man-%d7%a1%d7%a4%d7%99%d7%99%d7%93%d7%a8%d7%9e%d7%9f-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&sdarot=series_id=723&series_name=%d7%a1%d7%a4%d7%99%d7%99%d7%93%d7%a8%d7%9e%d7%9f%20%d7%90%d7%99%d7%a9%20%d7%94%d7%a2%d7%9b%d7%91%d7%99%d7%a9%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f723%2fultimate-spider-man-%d7%a1%d7%a4%d7%99%d7%99%d7%93%d7%a8%d7%9e%d7%9f-%d7%90%d7%99%d7%a9-%d7%94%d7%a2%d7%9b%d7%91%d7%99%d7%a9-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&sdarot=series_id=723&series_name=%d7%a1%d7%a4%d7%99%d7%99%d7%93%d7%a8%d7%9e%d7%9f%20%d7%90%d7%99%d7%a9%20%d7%94%d7%a2%d7%9b%d7%91%d7%99%d7%a9%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f723%2fultimate-spider-man-%d7%a1%d7%a4%d7%99%d7%99%d7%93%d7%a8%d7%9e%d7%9f-%d7%90%d7%99%d7%a9-%d7%94%d7%a2%d7%9b%d7%91%d7%99%d7%a9-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLZs0gQed9tMSElYC30JlPa40L7oFWmQ_C') #English
		list.append('&youtube_pl=PL1EA385D86ED1BF85') #English
		list.append('&youtube_pl=PL-8S9YDhDiwNcY_329gxvMje8ZtmXHNaZ') #English
		list.append('&youtube_pl=PLIEbITAtGBeZUo2UUyjW6iQayfMXv8SCy') #English
	addDir(addonString(10475).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/695.jpg',addonString(104750).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://cdn.collider.com/wp-content/uploads/ultimate-spider-man-image.jpg"))
	
	'''ספר הגונגל'''
	list = []
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=PL4eNR_m-ysh-3hy-ADCehyREw7EGpv0z-')
	addDir(addonString(10258).encode('utf-8'),list,5,'http://images.mouse.co.il/storage/3/7/ggg--book20090908_2343750_0..jpg',addonString(102580).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	
	'''סקובי דו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1429&series_name=%d7%a1%d7%a7%d7%95%d7%91%d7%99%20%d7%93%d7%95%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1429%2fscooby-doo-%d7%a1%d7%a7%d7%95%d7%91%d7%99-%d7%93%d7%95-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&sdarot=series_id=1214&series_name=%d7%a1%d7%a7%d7%95%d7%91%d7%99%20%d7%93%d7%95%20%d7%9e%d7%a1%d7%aa%d7%95%d7%a8%d7%99%d7%9f%20%d7%91%d7%a2%22%d7%9e&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1214%2fscooby-doo-mystery-incorporated-%d7%a1%d7%a7%d7%95%d7%91%d7%99-%d7%93%d7%95-%d7%9e%d7%a1%d7%aa%d7%95%d7%a8%d7%99%d7%9f-%d7%91%d7%a2-%d7%9e')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=ELXAmZ_OYm38M') #English
		list.append('&youtube_pl=ELPruZJpaRnmo') #English
		list.append('&youtube_pl=ELtUasJElSQn8') #English
		list.append('&youtube_pl=ELRhaVYhLImsM') #English
		list.append('&youtube_pl=ELh5rokX6BnT0') #English
	addDir(addonString(10476).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1429.jpg',addonString(104760).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''פאוור ריינג'רס'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=2099&series_name=%d7%a4%d7%90%d7%95%d7%95%d7%a8%20%d7%a8%d7%99%d7%99%d7%a0%d7%92%27%d7%a8%d7%a1%20%d7%91%d7%97%d7%9c%d7%9c%20-%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f2099%2fpower-rangers-in-space-%d7%a4%d7%90%d7%95%d7%95%d7%a8-%d7%a8%d7%99%d7%99%d7%a0%d7%92-%d7%a8%d7%a1-%d7%91%d7%97%d7%9c%d7%9c-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&sdarot=season_id=1&series_id=2129&series_name=%d7%a4%d7%90%d7%95%d7%95%d7%a8%20%d7%a8%d7%99%d7%99%d7%a0%d7%92%27%d7%a8%d7%a1%20%d7%93%d7%99%d7%a0%d7%95%20%d7%a6%27%d7%90%d7%a8%d7%92%27&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f2129%2fpower-rangers-dino-charge-%d7%a4%d7%90%d7%95%d7%95%d7%a8-%d7%a8%d7%99%d7%99%d7%a0%d7%92-%d7%a8%d7%a1-%d7%93%d7%99%d7%a0%d7%95-%d7%a6-%d7%90%d7%a8%d7%92')
		list.append('&sdarot=season_id=1&series_id=1709&series_name=%d7%a4%d7%90%d7%95%d7%95%d7%a8%20%d7%a8%d7%99%d7%99%d7%a0%d7%92%27%d7%a8%d7%a1%20%d7%a1%d7%99%d7%91%d7%95%d7%91%d7%99%d7%9d%20%d7%9c%d7%93%d7%a7%d7%94&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1709%2fpower-rangers-rpm-%d7%a4%d7%90%d7%95%d7%95%d7%a8-%d7%a8%d7%99%d7%99%d7%a0%d7%92-%d7%a8%d7%a1-%d7%a1%d7%99%d7%91%d7%95%d7%91%d7%99%d7%9d-%d7%9c%d7%93%d7%a7%d7%94')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a4%d7%a8%d7%a7%d7%99%d7%9d%20%d7%9e%d7%9c%d7%90%d7%99%d7%9d&url=seasonId%3d2617840')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a4%d7%a8%d7%a7%d7%99%d7%9d%20%d7%9e%d7%9c%d7%90%d7%99%d7%9d&url=seasonId%3d2595189')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a4%d7%a8%d7%a7%d7%99%d7%9d%20%d7%9e%d7%9c%d7%90%d7%99%d7%9d&url=seasonId%3d2520794')
		list.append('&youtube_pl=PLerLBKQYk11GAK1aviMgeEF2L6F3mWAEn') #Hebrew
		list.append('&youtube_pl=PLLIUYaEsBH6ZsDjq2ZJOnN4I4oMKNxqbZ') #Hebrew
		list.append('&youtube_pl=PLKMFPiSCwUk0w5bwxxxzob5tCGjnY4LfY') #Hebrew
		list.append('&youtube_pl=PLKMFPiSCwUk01oKz850en3WtD80zdmGus') #S14
	
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL5JnXzSWCdmd2i9k0mYlncHE3N11wa5sZ') #English
		list.append('&youtube_pl=PLN9GsozMMP5qugRIjDC4eAf3dF9ucONlr') #English
		list.append('&youtube_pl=PL32C56A2FCDA5B66D') #English
		list.append('&youtube_pl=PLC6071322045E33D9') #English
		list.append('&youtube_pl=PLC6071322045E33D9') #English
		list.append('&youtube_pl=PLhNIJQtTs5KLuj9S7gwqbH7G3rB1MXblb') #English
		list.append('&dailymotion_pl=x3n97x') #English
		list.append('&dailymotion_pl=x3m0wa') #English
	addDir(addonString(10477).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/711.jpg',addonString(104770).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''פוקימון'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1495&series_name=%d7%a4%d7%95%d7%a7%d7%99%d7%9e%d7%95%d7%9f%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1495%2fpokemon-hebsub-%d7%a4%d7%95%d7%a7%d7%99%d7%9e%d7%95%d7%9f-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&sdarot=series_id=433&series_name=%d7%a4%d7%95%d7%a7%d7%99%d7%9e%d7%95%d7%9f%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f433%2fpokemon-%d7%a4%d7%95%d7%a7%d7%99%d7%9e%d7%95%d7%9f-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&sdarot=season_id=1&series_id=1192&series_name=%d7%a4%d7%95%d7%a7%d7%99%d7%9e%d7%95%d7%9f%20%d7%93%d7%91%d7%a8%d7%99%20%d7%94%d7%99%d7%9e%d7%99%d7%9d%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1192%2fpokemon-chronicles-%d7%a4%d7%95%d7%a7%d7%99%d7%9e%d7%95%d7%9f-%d7%93%d7%91%d7%a8%d7%99-%d7%94%d7%99%d7%9e%d7%99%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&sdarot=season_id=1&series_id=2119&series_name=%d7%a4%d7%95%d7%a7%d7%99%d7%9e%d7%95%d7%9f%3a%20%d7%94%d7%9e%d7%a7%d7%95%d7%a8%d7%95%d7%aa%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f2119%2fpokemon-origins-%d7%a4%d7%95%d7%a7%d7%99%d7%9e%d7%95%d7%9f-%d7%94%d7%9e%d7%a7%d7%95%d7%a8%d7%95%d7%aa-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&sdarot=season_id=1&series_id=2120&series_name=%d7%a4%d7%95%d7%a7%d7%99%d7%9e%d7%95%d7%9f%3a%20%d7%94%d7%aa%d7%a4%d7%aa%d7%97%d7%95%d7%aa%20%d7%94%d7%9e%d7%92%d7%94%20%d7%94%d7%97%d7%96%d7%a7%d7%94%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f2120%2fpokemon-strongest-mega-evolution-%d7%a4%d7%95%d7%a7%d7%99%d7%9e%d7%95%d7%9f-%d7%94%d7%aa%d7%a4%d7%aa%d7%97%d7%95%d7%aa-%d7%94%d7%9e%d7%92%d7%94-%d7%94%d7%97%d7%96%d7%a7%d7%94-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&dailymotion_pl=x34tag') #Hebrew
		list.append('&youtube_pl=PLCvjpWBfw_7iaUfacUr7NRzsYOtyHJf0M') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLYi30KTSgtG8xQtFGsYIiN4xX7NGq6sOK') #English
		list.append('&dailymotion_pl=x30xbc') #English
	if 'Hindi' in General_LanguageL:
		list.append('&youtube_id=x2kmbwv') #Hindi
	
	addDir(addonString(10478).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/433.jpg',addonString(104780).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''פיטר פן'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1000&series_name=%d7%a4%d7%99%d7%98%d7%a8%20%d7%a4%d7%9f%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1000%2fpeter-pan-%d7%a4%d7%99%d7%98%d7%a8-%d7%a4%d7%9f-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PL_8KXLhQVQMIMJ_lQkl0Z393wwTtRgg_i') #Hebrew
		list.append('&youtube_pl=PLiDCIQSNnvwc-FqtPLIy3i3i5p0UoB5Fr') #Hebrew
	if 'Haitian' in General_LanguageL:
		list.append('&dailymotion_pl=x3kky6') #קרואלית איטית
	if 'French' in General_LanguageL:
		list.append('&dailymotion_pl=xe92x') #French
		list.append('&dailymotion_pl=x1hqyr') #French
	if 'Italian' in General_LanguageL:
		list.append('&dailymotion_pl=x41cih') #Italian
	addDir(addonString(10267).encode('utf-8'),list,17,'https://encrypted-tbn1.gstatic.com/images?q=tbn:ANd9GcSpAqoUxOIErj3Kgl4053S4oixnvZCcvoJwhf83xupmupsHWKh8',addonString(102670).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''פינוקיו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=904&series_name=%d7%a4%d7%99%d7%a0%d7%95%d7%a7%d7%99%d7%95%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f904%2fthe-adventures-of-pinocchio-%d7%a4%d7%99%d7%a0%d7%95%d7%a7%d7%99%d7%95-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PL17BB1526E0625514') #Hebrew
		list.append('&youtube_pl=PLwXEsK85wc0OQV1DgaY4zC0_CiB8ZD5j9') #Hebrew
	addDir(addonString(10480).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/904.jpg',addonString(104800).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES104C(General_LanguageL, background, background2) #פלאנט שין
	CATEGORIES104B(General_LanguageL, background, background2) #פריקבוי וצ'אם צ'אם
	
	'''צבי הנינג'ה 1 (1987)''' #NICK (WALLA)
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=636&series_name=%d7%a6%d7%91%d7%99%20%d7%94%d7%a0%d7%99%d7%a0%d7%92%27%d7%94%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f636%2fteenage-mutant-ninja-turtles-%d7%a6%d7%91%d7%99-%d7%94%d7%a0%d7%99%d7%a0%d7%92-%d7%94-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94') #Hebrew subs
		list.append('&youtube_id=W7B3NXG0aDY')
		list.append('&youtube_id=E7naeIx3rqo')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL6fJmjt84zZjpEMYCLgX689DlYHAOY5eO') #English
		list.append('&youtube_pl=PLJOXtFyZkYoeQSXGSDHqhuX4Q2P777dl1') #English
		list.append('&youtube_pl=PLwGuYe9NVBWmp2zRCeqAFBCy8IYEPOEd_') #English #S3
	addDir(addonString(10580).encode('utf-8') + space + '1',list,17,'http://www.sdarot.pm/media/series/636.jpg',addonString(105800).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://vignette1.wikia.nocookie.net/dc-marvel-tmnt/images/8/84/Teenage_Mutant_Ninja_Turtles_(1987).jpg/revision/latest?cb=20140408173125"))
	
	'''צבי הנינג'ה 2 (2012)'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%d7%a2%d7%95%d7%93%20%d7%a4%d7%a8%d7%a7%d7%99%d7%9d&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2594836%26page%3d2')
		list.append('&sdarot=series_id=1530&series_name=%d7%a6%d7%91%d7%99%20%d7%94%d7%a0%d7%99%d7%a0%d7%92%27%d7%94%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1530%2fteenage-mutant-ninja-turtles-%d7%a6%d7%91%d7%99-%d7%94%d7%a0%d7%99%d7%a0%d7%92-%d7%94-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94') #Hebrew
		list.append('&sdarot=series_id=1670&series_name=%d7%a6%d7%91%d7%99%20%d7%94%d7%a0%d7%99%d7%a0%d7%92%27%d7%94%3a%20%d7%94%d7%93%d7%95%d7%a8%20%d7%94%d7%91%d7%90%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1670%2fninja-turtles-the-next-mutation-%d7%a6%d7%91%d7%99-%d7%94%d7%a0%d7%99%d7%a0%d7%92-%d7%94-%d7%94%d7%93%d7%95%d7%a8-%d7%94%d7%91%d7%90-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a4%d7%a8%d7%a7%d7%99%d7%9d%20%d7%9e%d7%9c%d7%90%d7%99%d7%9d&url=seasonId%3d2623650')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?%23039%3b%d7%94%20%d7%94%d7%93%d7%95%d7%a8%20%d7%94%d7%91%d7%90&mode=2&module=338&name=%d7%a6%d7%91%d7%99%20%d7%94%d7%a0%d7%99%d7%a0%d7%92&url=http%3a%2f%2fvod.walla.co.il%2ftvshow%2f2623645%2fninja-turtles-the-next-mutation')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL2DB18B47B9E7A3DA') #English
		list.append('&youtube_pl=PL38jdb5xOHbE5ROUr9v1qDFU28Q8XO3RO') #English #S1
		list.append('&youtube_pl=PLjX9hKnb2rTVo7_1slvotGkIExpVEL-nL') #English
		list.append('&youtube_pl=PLjX9hKnb2rTVo7_1slvotGkIExpVEL-nL') #English #S1
		list.append('&youtube_pl=PLjX9hKnb2rTWJsXtTTKIDvHa0swXHEtVT') #English #S4
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLpPLzEufnyNMudPzz__ekbSEdC0_h95c9') #Spanish
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PL60657681808C7A03') #French
	addDir(addonString(10580).encode('utf-8') + space + '2',list,17,'http://www.sdarot.pm/media/series/1530.jpg',addonString(105800).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''צ'ארלי בראון'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL0JlJB5gdQUHOAfdfCNwzCJt5kvMwDGAP')
		list.append('&youtube_pl=PLeagipoZmyfmLmP1HKhyY-h7-Iwjkk52M')
		
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=PLMxgaYQNtoym-Ty6CUwpMNdUUPte7cmpU')	
	if 'German' in General_LanguageL:
		list.append('&youtube_id=u-j64okEHCs')		
		
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_id=4SvYGfe-Mqc')
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	addDir(addonString(10482).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/en/thumb/2/22/Charlie_Brown.png/150px-Charlie_Brown.png',addonString(104820).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''קספר'''
	list = []
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PL-fIrVtK0oZoMiDgF8qocU5yN1Rsr5qKa')
	addDir(addonString(10481).encode('utf-8'),list,17,'https://rufiojones.files.wordpress.com/2011/08/casper2.jpg',addonString(104810).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''רובוטריקים 1 (1992)'''
	thumb = 'http://www.sdarot.pm/media/series/1395.jpg'
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1395&series_name=Transformers%20-%20HebDub&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1395%2ftransformers-hebdub-%d7%a8%d7%95%d7%91%d7%95%d7%98%d7%a8%d7%99%d7%a7%d7%99%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&sdarot=series_id=1431&series_name=Transformers&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1431%2ftransformers-%d7%a8%d7%95%d7%91%d7%95%d7%98%d7%a8%d7%99%d7%a7%d7%99%d7%9d-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94') #English
		list.append('&youtube_pl=PLE509500608BCEB9A') #English
		list.append('&youtube_pl=PLEF9DC7B987249D43') #English
		list.append('&youtube_pl=ELh2QPH8jbzz4') #English
		list.append('&youtube_pl=PLfp_r1A709h-H--XWKvJcD6_ALO5Qt22h') #English
		list.append('&youtube_pl=PL72F5C7FFA297740E') #English #S3 S4
	
	addDir(addonString(10582).encode('utf-8') + space + '1' + space + '(1992)',list,17,thumb,addonString(105820).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))

	'''רובוטריקים 2 (2007) (Animated)'''
	thumb = 'http://ia.media-imdb.com/images/M/MV5BMTA4NDQzNDUxNDdeQTJeQWpwZ15BbWU3MDAxMzE4NTI@._V1_UY268_CR103,0,182,268_AL_.jpg'
	plot = 'Transformers crash land on present day Earth and inadvertently cause a technological revolution. They wake up 50 years later in a world where robots are used in everyday life. StarScream arrives looking for their AllSpark.'
	list = []
	if 'Hebrew' in General_LanguageL:
		pass
	if 'English' in General_LanguageL:
		pass
	addDir(addonString(10582).encode('utf-8') + space + '2' + space + '(2007)' + space + '(Animated)',list,17,thumb,plot,'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''רובוטריקים 3 (2010) (Prime)'''
	thumb = 'http://ia.media-imdb.com/images/M/MV5BMTczNDM3MzY1Nl5BMl5BanBnXkFtZTcwOTg5NjU1OQ@@._V1_UY268_CR4,0,182,268_AL_.jpg'
	plot = 'In this new set of adventures the Autobots live on Earth and maintain their secret identity. They are joined by 3 teens as they battle the Decepticons.'
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1451&series_name=Transformers%20Prime%20Hebdub&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1451%2ftransformers-prime-hebdub-%d7%a8%d7%95%d7%91%d7%95%d7%98%d7%a8%d7%99%d7%a7%d7%99%d7%9d-%d7%a4%d7%a8%d7%99%d7%99%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLpDv_jA6rpIQrDFRGpLv8Er-taOeq7sPR') #English
		list.append('&youtube_pl=PL-j7p6cmFFmwbRdp3lQVX5uEdmtT94zXA') #English
	
	addDir(addonString(10582).encode('utf-8') + space + '3' + space + '(2010)' + space + '(Prime)',list,17,thumb,plot,'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''רובוטריקים 4 (2011) (Rescue Bots)'''
	thumb = 'http://ia.media-imdb.com/images/M/MV5BMjE1Njc1NTQxM15BMl5BanBnXkFtZTcwNjIxMDgyNw@@._V1_UY268_CR5,0,182,268_AL_.jpg'
	plot = 'The Rescue Bots are Transformers that work with a family of heroes to rescue humans from disasters. These non-violent Transformer stories are aimed at preschool viewers.'
	list = []
	if 'Hebrew' in General_LanguageL:
		pass
	addDir(addonString(2011).encode('utf-8') + space + '4' + space + '(2011)' + space + '(Rescue Bots)',list,17,thumb,plot,'1',50,getAddonFanart(background, custom="", default=background2))
	
	
	'''רובוטריקים 5 (2015) (Robots in Disguise)'''
	thumb = 'http://ia.media-imdb.com/images/M/MV5BMjMwNTIxNzEwMV5BMl5BanBnXkFtZTgwNDMwMDI1NTE@._V1_UY268_CR87,0,182,268_AL_.jpg'
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1665&series_name=Transformers%20Robots%20in%20Disguise&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1665%2ftransformers-robots-in-disguise-%d7%a8%d7%95%d7%91%d7%95%d7%98%d7%a8%d7%99%d7%a7%d7%99%d7%9d-%d7%91%d7%94%d7%a1%d7%95%d7%95%d7%90%d7%94-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL7857F7FC0CE2EC05') #English
	addDir(addonString(10582).encode('utf-8') + space + '5' + space + '(2015)' + space + '(Robots in Disguise)',list,17,thumb,addonString(105820).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''רובוטריקים (Gameplay)'''
	thumb = ''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_ch=transformersrevengeofthefallen') #English
	#addDir(addonString(10582).encode('utf-8') + space + '(Gameplay)',list,17,thumb,'','',50,getAddonFanart(background, custom="", default=background2))

	'''שאלתיאל קוואק'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1137&series_name=%d7%a9%d7%90%d7%9c%d7%aa%d7%99%d7%90%d7%9c%20%d7%a7%d7%95%d7%95%d7%90%d7%a7%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1137%2falfred-j-kwak-%d7%a9%d7%90%d7%9c%d7%aa%d7%99%d7%90%d7%9c-%d7%a7%d7%95%d7%95%d7%90%d7%a7-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PL_8KXLhQVQMKOtRoV1SuOu95dvVo-ea2J') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL5p6VZkX3u2XOrTAP_nmXjms-LWvVBcBts') #English
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLMUK7XxmIwPAAlqAgdewVL-ZhBb8nYop3') #Spanish
		list.append('&youtube_pl=PLr3j2qexlLJknHyg4PhqDolInwT2w_sOe') #Spanish
	if 'Finish' in General_LanguageL:
		list.append('&youtube_pl=PLAI8n3kFtznCVkl-wvK20s5CNZ7X3y2Hr') #Finish
	if 'German' in General_LanguageL:
		list.append('&youtube_pl=PL83EB11DD1D5EF206') #German
		list.append('&youtube_pl=PLxrn5FVkko2aSQ1VtJqsCdPeThBy82t26') #German
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=PL3EF10E10A9956F05') #Dutch
		list.append('&youtube_pl=PLqmrnUMcT7FlnkkfRj9_FsMbxe2cet0lU') #Dutch
	addDir(addonString(10583).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1137.jpg',addonString(105830).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://fallytv.com/showinfo/80686/80686-4.jpg"))
	
	'''שלגיה ושבעת הגמדים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL_8KXLhQVQMKKrMMm0glr1TMQoxCjFuTk') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLtgj60MypUp_mvrhlG1TGZteM-HBh_vzv') #English
	addDir(addonString(10589).encode('utf-8'),list,17,'http://www.coloring4fun.com/wp-content/uploads/2013/03/snow-white-600x300.jpg',addonString(105890).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''שלושת המוסקטרים'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLyTuZsx2zEs8yu8SWz0FfYxCxKmc6cmVU') #English
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PLo1kzli4cgLeBUsyInDov6DqME6y1CvXz') #French
	addDir(addonString(10486).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/821.jpg',addonString(104860).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''Walt Disney Cartoons*'''
	thumb = 'http://img15.deviantart.net/9b16/i/2011/212/e/e/walt_disney_pictures_logo_icon_by_mahesh69a-d42bchp.png'
	list = []
	list.append('&custom8=plugin://plugin.video.supercartoons/?image=C%3a%5cUsers%5cgal%5cAppData%5cRoaming%5cKodi%5caddons%5cplugin.video.supercartoons%5cresources%5cartwork%5ccharacters.png&mode=400&page=1&title=Characters')
	list.append('&custom4=plugin://plugin.video.supercartoons/?mode=100&title=Kids+Time+%2810+Random+Cartoons%29&image=C%3A%5CUsers%5Cgal%5CAppData%5CRoaming%5CKodi%5Caddons%5Cplugin.video.supercartoons%5Cresources%5Cartwork%5Ckidstime.png&page=1')
	list.append('&youtube_pl=PLhGipfv0juZWh-OMeXOvJ-Ibt9wZtdJK1') #English
	list.append('&youtube_pl=PL7spvnQF9O-j1qnZLPTyLYfmQAifdSfN9') #English
	list.append('&youtube_pl=PL7spvnQF9O-hVKRHmNu8uTJeNF5mr6oGj') #English
	list.append('&youtube_id=OM6xvpzqCUA') #English
	list.append('&youtube_id=Q8AZ16uBhr8') #English
	list.append('&youtube_id=2n7UgwWGUeQ') #English
	list.append('&youtube_id=1-x1kz3OHvw') #English
	list.append('&youtube_id=-VbQoS7O4Ls') #English
	list.append('&youtube_id=8Qa_OCHDsOc') #English
	list.append('&youtube_id=xLZhlP-PQ5A') #English
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PL7spvnQF9O-gzBQghS5lQ9T6kmU3CExZw') #Spanish
	addDir('Walt Disney Cartoons',list,17,thumb,'','plugin.video.supercartoons',58, getAddonFanart(background, custom="https://i.ytimg.com/vi/Us4ZsVZiZjQ/maxresdefault.jpg"))
	
	'''The Mozart Band'''
	thumb = 'https://i1.ytimg.com/sh/Qt0yd__tuiM/showposter.jpg?v=503372e5'
	plot = 'The Mozart Band (original Spanish title, La banda de Mozart) is a 1995 animated television series produced by the BRB Internacional and Marathon Animation studios.'
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=ELkJDYNzDnzgo') #English
		list.append('&youtube_pl=PLL7dcgwYKsm0diDe04UG4TyPRm5p8IS8_') #English
	addDir('The Mozart Band',list,17,thumb,plot,'',58, getAddonFanart(background, custom="https://i.ytimg.com/vi/Us4ZsVZiZjQ/maxresdefault.jpg"))
	
	CATEGORIES104A(General_LanguageL, background, background2) #עמוד הבא הצגות ילדים
	
def CATEGORIES105(name, iconimage, desc, fanart):
	background = 105
	background2 = "" #http://4.bp.blogspot.com/-Af2HcIQzlg8/UhwQ8lKPucI/AAAAAAAACIA/d7aY4RrxUfk/s1600/bambi-friends-disney-animated-movie-photo.jpg"
	
	CATEGORIES_RANDOM() #אקראי
	CATEGORIES105Z(General_LanguageL, background, background2) #ערוצי טלוויזיה
	
	if 'Hebrew' in General_LanguageL:
		check_seretil_me = urlcheck('http://seretil.me', ping=False)
		check_10q_tv = urlcheck('http://10q.tv', ping=False)
		check_gozlan_me = urlcheck('http://anonymouse.org/cgi-bin/anon-www.cgi/http://gozlan.eu/', ping=False)
		check_movix_me = "" #check_movix_me = urlcheck('http://www.movix.me/series', ping=True) #GAL CHECK THIS (PING)
		
		'''סרטים מדובבים'''
		count = 1
		if check_movix_me == 'ok':
			addDir(addonString(10520).encode('utf-8') + space + str(count),'plugin://plugin.video.movixws/?iconimage=http%3a%2f%2fwww.in-hebrew.co.il%2fimages%2flogo-s.jpg&mode=2&name=Kids%20-%20%d7%99%d7%9c%d7%93%d7%99%d7%9d&url=http%3a%2f%2fwww.movix.me%2fgenres%2fKids',8,'http://www.in-hebrew.co.il/images/logo-s.jpg','','1',50,getAddonFanart(background, custom="", default=background2)) ; count += 1
			addDir(addonString(10520).encode('utf-8') + space + str(count),'plugin://plugin.video.movixws/?iconimage=http%3a%2f%2ficons.iconarchive.com%2ficons%2fdesignbolts%2ffree-movie-folder%2f256%2fAnimated-icon.png&mode=2&name=Animation%20-%20%d7%90%d7%a0%d7%99%d7%9e%d7%a6%d7%99%d7%94&url=http%3a%2f%2fwww.movix.me%2fgenres%2fAnimation',8,'http://icons.iconarchive.com/icons/designbolts/free-movie-folder/256/Animated-icon.png','','1',50,getAddonFanart(background, custom="", default=background2)) ; count += 1
		if check_seretil_me == 'ok':
			#addDir(addonString(10520).encode('utf-8'),list1,6,'http://www.iphoneil.net/icone/111185-icon.png',addonString(105200).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
			addDir(addonString(10520).encode('utf-8') + space + str(count),'plugin://plugin.video.seretil/?mode=4&name=%d7%9e%d7%93%d7%95%d7%91%d7%91%d7%99%d7%9d%20%d7%a8%d7%90%d7%a9%d7%99&url=http%3a%2f%2fseretil.me%2fcategory%2f%25D7%25A1%25D7%25A8%25D7%2598%25D7%2599%25D7%259D-%25D7%259E%25D7%2593%25D7%2595%25D7%2591%25D7%2591%25D7%2599%25D7%259D%2fpage1%2f',8,'http://blog.tapuz.co.il/seretilNET/images/3745375_1.jpg',addonString(105200).encode('utf-8'),'1',58,getAddonFanart(background, custom="", default=background2)) ; count += 1
			#addDir('[COLOR=red]' + addonString(10520).encode('utf-8') + space + str(count) + '[/COLOR]','plugin://plugin.video.seretil/?mode=211&name=%20%d7%90%d7%95%d7%a1%d7%a3%20%d7%a1%d7%a8%d7%98%d7%99%d7%9d%20%d7%9e%d7%93%d7%95%d7%91%d7%91%d7%99%d7%9d&url=http%3a%2f%2fseretil.me%2f%25D7%2590%25D7%2595%25D7%25A1%25D7%25A3-%25D7%25A1%25D7%25A8%25D7%2598%25D7%2599%25D7%259D-%25D7%259E%25D7%2593%25D7%2595%25D7%2591%25D7%2591%25D7%2599%25D7%259D%2f',8,'http://blog.tapuz.co.il/seretilNET/images/3745375_1.jpg',addonString(196).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2)) ; count += 1
			#addDir('[COLOR=red]' + addonString(10520).encode('utf-8') + space + str(count) + '[/COLOR]','plugin://plugin.video.seretil/?mode=211&name=%d7%90%d7%95%d7%a1%d7%a3%20%d7%9e%d7%a1%d7%a4%d7%a8%202%20%d7%a1%d7%a8%d7%98%d7%99%d7%9d%20%d7%9e%d7%93%d7%95%d7%91%d7%91%d7%99%d7%9d&url=http%3a%2f%2fseretil.me%2f%25D7%2590%25D7%2595%25D7%25A1%25D7%25A3-%25D7%2592%25D7%2593%25D7%2595%25D7%259C-%25D7%25A9%25D7%259C-%25D7%25A1%25D7%25A8%25D7%2598%25D7%2599%25D7%259D-%25D7%259E%25D7%25A6%25D7%2595%25D7%2599%25D7%25A8%25D7%2599%25D7%259D%25D7%259E%25D7%2593%25D7%2595%25D7%2591%25D7%2591%25D7%2599%25D7%259D%2f',8,'http://blog.tapuz.co.il/seretilNET/images/3745375_1.jpg',addonString(196).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2)) ; count += 1

		'''סרטים מתורגמים'''
		count = 1
		if check_10q_tv == 'ok': 
			addDir(addonString(10535).encode('utf-8') + space + str(count),'plugin://plugin.video.10qtv/?mode=6&name=%d7%9e%d7%a9%d7%a4%d7%97%d7%94&url=http%3a%2f%2fwww.10q.tv%2fboard%2ffilmy%2fmshfhha%2f17',8,'http://mirror.cinosure.com/superrepo/v5/addons/plugin.video.10qtv/icon.png',addonString(110).encode('utf-8'),'1',57) ; count += 1
			addDir(addonString(10535).encode('utf-8') + space + str(count),'plugin://plugin.video.10qtv/?mode=6&name=אנימציה&url=http://www.10q.tv/board/filmy/animciha/5',8,'http://mirror.cinosure.com/superrepo/v5/addons/plugin.video.10qtv/icon.png',addonString(110).encode('utf-8'),'1',57) ; count += 1
			'''---------------------------'''
		if check_gozlan_me == 'ok':
			addDir(addonString(10535).encode('utf-8') + space + str(count),'plugin://plugin.video.gozlan.me/?mode=1&name=%d7%a1%d7%a8%d7%98%d7%99%20%d7%90%d7%a0%d7%99%d7%9e%d7%a6%d7%99%d7%94&url=http%3a%2f%2fanonymouse.org%2fcgi-bin%2fanon-www.cgi%2fhttp%3a%2f%2fgozlan.co%2f%2fsearch.html%3fg%3d%25D7%2590%25D7%25A0%25D7%2599%25D7%259E%25D7%25A6%25D7%2599%25D7%2594',8,'http://ftp.acc.umu.se/mirror/addons.superrepo.org/v5/addons/plugin.video.gozlan.me/icon.png','','1',58,getAddonFanart(background, custom="", default=background2)) ; count += 1
			addDir(addonString(10535).encode('utf-8') + space + str(count),'plugin://plugin.video.gozlan.me/?mode=1&name=%d7%a1%d7%a8%d7%98%d7%99%20%d7%9e%d7%a9%d7%a4%d7%97%d7%94&url=http%3a%2f%2fanonymouse.org%2fcgi-bin%2fanon-www.cgi%2fhttp%3a%2f%2fgozlan.co%2f%2fsearch.html%3fg%3d%25D7%259E%25D7%25A9%25D7%25A4%25D7%2597%25D7%2594',8,'http://ftp.acc.umu.se/mirror/addons.superrepo.org/v5/addons/plugin.video.gozlan.me/icon.png','','1',58,getAddonFanart(background, custom="", default=background2)) ; count += 1
			'''---------------------------'''
		
	
	'''אוגי והמקקים (2014)*'''
	list = []
	list.append('&dailymotion_id=x2rirvo')
	addDir(addonString(10429).encode('utf-8') + space + '(2014)',list,5,'http://www.sdarot.pm/media/series/585.jpg',addonString(104290).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''אוגי והמקקים (2015)*'''
	list = []
	list.append('&dailymotion_id=x31fwqj')
	addDir(addonString(10429).encode('utf-8') + space + '(2015)',list,5,'http://www.sdarot.pm/media/series/585.jpg',addonString(104290).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))

	'''אלאדין 1 (1991)'''
	list = []
	if 'Hindi' in General_LanguageL:
		list.append('&dailymotion_id=x2shy23') #Hindi
	addDir(addonString(10529).encode('utf-8') + space + '1' + space + '(1992)',list,6,'https://upload.wikimedia.org/wikipedia/he/thumb/5/58/Aladdinposter.jpg/250px-Aladdinposter.jpg',addonString(105290).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''אלאדין 2 (1994)'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&dailymotion_id=x2imi9m') #English
	if 'Hindi' in General_LanguageL:
		list.append('&dailymotion_id=x2shy25') #Hindi
	addDir(addonString(10529).encode('utf-8') + space + '2' + space + '(1994)',list,6,'https://upload.wikimedia.org/wikipedia/he/thumb/5/58/Aladdinposter.jpg/250px-Aladdinposter.jpg',addonString(105290).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''אלאדין 3 (1996)'''
	list = []
	
	list.append('&dailymotion_id=x3g57qg') #English
	if 'Hindi' in General_LanguageL:
		list.append('&dailymotion_id=x2shy24') #Hindi
	addDir(addonString(10529).encode('utf-8') + space + '3' + space + '(1996)',list,6,'https://upload.wikimedia.org/wikipedia/he/thumb/5/58/Aladdinposter.jpg/250px-Aladdinposter.jpg',addonString(105290).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''אמיל והבלשים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=iipZpLSwTn4') #Hebrew
	
	addDir('אמיל והבלשים',list,17,'','','1',"",getAddonFanart(background, custom="", default=background2))
	
	'''ארתור - בסה"כ רוקנלרול'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=PYTnccj8QW8')
	addDir('ארתור - בסה"כ רוקנלרול',list,17,'','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''ארתור - חבר הולך לאיבוד'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=cXUbOYJ6TEU')
	addDir('ארתור - חבר הולך לאיבוד',list,17,'','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''בבי הקוסמת הצעירה (2012)'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=b_mVeOE8i0o') #Hebrew
	
	addDir('בבי הקוסמת הצעירה (2012)',list,17,'','','1',"",getAddonFanart(background, custom="", default=background2))
	
	'''בילבי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=yE5W16Czh4g')
	addDir(addonString(10207).encode('utf-8'),list,5,'http://i.ytimg.com/vi/2mxOiPccxOs/maxresdefault.jpg',addonString(102070).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''ברבי ***אוסף***'''
	thumb = 'http://ia.media-imdb.com/images/M/MV5BMjA5NTE3OTcwOV5BMl5BanBnXkFtZTcwMjA4NzgxMQ@@._V1_UY268_CR2,0,182,268_AL_.jpg'
	plot = ''
	list = []
	if 'English' in General_LanguageL:
		list.append('&dailymotion_id=x2ixc2d') #English
		list.append('&dailymotion_id=x2ixc0z') #English
		list.append('&dailymotion_id=x2ir248') #English
		list.append('&dailymotion_id=x2lal4z') #English
		list.append('&dailymotion_id=x399i07') #English
		list.append('&dailymotion_id=x2i7hd0') #English
		list.append('&dailymotion_id=x2g6o39') #English
		list.append('&dailymotion_id=x2tibbo') #English
		list.append('&dailymotion_id=x2lfbb6') #English
		list.append('&dailymotion_id=x2ivr3w') #English
		list.append('&youtube_id=-xJuZyEtT3I') #English
	if 'Hindi' in General_LanguageL:
		list.append('&dailymotion_id=x2ht25v') #Hindi
		list.append('&dailymotion_id=x2ixbar') #Hindi
		list.append('&dailymotion_id=x2ixc2d') #Hindi
		list.append('&dailymotion_id=x2h66f2') #Hindi
		list.append('&dailymotion_id=x3bxv3y') #Hindi
		list.append('&dailymotion_id=x32n436') #Hindi
		list.append('&dailymotion_id=x3255i6') #Hindi
		list.append('&dailymotion_id=x3c28ns') #Hindi
	
	if 'Thai' in General_LanguageL:
		list.append('&dailymotion_id=x2elh43') #Thai
		list.append('&dailymotion_id=x2ecgag') #Thai
		list.append('&dailymotion_id=x2en51z') #Thai
		list.append('&dailymotion_id=x2esd6p') #Thai
		list.append('&dailymotion_id=x2eol06') #Thai
		list.append('&dailymotion_id=x2ejc0p') #Thai
		list.append('&dailymotion_id=x2eyr1k') #Thai
		list.append('&dailymotion_id=x2ewf52') #Thai
		list.append('&dailymotion_id=x2ewj2o') #Thai
		list.append('&dailymotion_id=x2elgnb') #Thai
		list.append('&dailymotion_id=x2esck4') #Thai
		list.append('&dailymotion_id=x2elpyx') #Thai
		list.append('&dailymotion_id=x2ed3l4') #Thai
	addDir(addonString(10230).encode('utf-8') + space + '[Collection]',list,6,thumb,plot,'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''גשם של פלאפל'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=jeN7D0jHjKQ') #Hebrew
	addDir('גשם של פלאפל',list,17,'','','1',"",getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES102B(General_LanguageL, background, background2) #דראגון בול [Collection]
	
	'''הדרדסים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=R4Zl42XfJtA')
	addDir(addonString(10422).encode('utf-8'),list,17,'http://f.nanafiles.co.il/upload/Xternal/IsraBlog/73/34/75/753473/misc/23130510.jpg',addonString(104220).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''היתקליף '''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a4%d7%a8%d7%a7%d7%99%d7%9d%20%d7%9e%d7%9c%d7%90%d7%99%d7%9d&url=seasonId%3d2549973')
	if 'English' in General_LanguageL:
		list.append('&youtube_id=r-3ckLnkPyc')
	addDir(addonString(10626).encode('utf-8'),list,17,'http://vignette4.wikia.nocookie.net/heathcliff/images/2/25/Heathcliff8.jpg/revision/latest?cb=20130709224249',addonString(106260).encode('utf-8'),'1',50, getAddonFanart(background, custom="https://i.ytimg.com/vi/Pa6TTBsMduE/maxresdefault.jpg"))
	
	'''הילד שרצה להיות דב'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=R1O5law49HI') #Hebrew
	
	addDir('הילד שרצה להיות דב',list,17,'','','1',"",getAddonFanart(background, custom="", default=background2))
	
	'''היפה והחיה (1992)'''
	list = []
	list.append('&dailymotion_id=x2jk5nl')
	if 'Thai' in General_LanguageL:
		list.append('&dailymotion_id=x2elw3f') #Thai
	addDir(addonString(10530).encode('utf-8') + space + '(1991)',list,6,'https://upload.wikimedia.org/wikipedia/en/thumb/7/7c/Beautybeastposter.jpg/220px-Beautybeastposter.jpg',addonString(105300).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''היפיפייה הנרדמת (1959)'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&dailymotion_id=x3gbixs') #English
	addDir(addonString(10531).encode('utf-8') + space + '(1959)',list,6,'https://upload.wikimedia.org/wikipedia/en/thumb/4/43/Sleeping_beauty_disney.jpg/220px-Sleeping_beauty_disney.jpg',addonString(105310).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''הנסיכה סופייה (2012)'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=') #Hebrew
	
	if 'English' in General_LanguageL:
		list.append('&dailymotion_id=x2lhahj') #English
		
	if 'Thai' in General_LanguageL:
		list.append('&dailymotion_id=x2jjovt') #Thai
	addDir(addonString(10722).encode('utf-8') + space + '(2012)',list,17,'http://global.fncstatic.com/static/managed/img/fn-latino/lifestyle/Sofia_Logo.jpg',addonString(107220).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://vignette4.wikia.nocookie.net/disney/images/c/ce/Cinderella-Sofia-the-first.jpg/revision/latest?cb=20131006155938"))
	
	'''הצילו אני דג'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=TlWVoNz_B3o')
	addDir('הצילו אני דג',list,17,'','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''הרמב"ם הגדול'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=2NpLGjQvtn8') #Hebrew
	
	addDir('הרמב"ם הגדול',list,17,'','','1',"",getAddonFanart(background, custom="", default=background2))
	
	'''חלב ודבש'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=3MXTabnJGl0') #Hebrew
	
	addDir('חלב ודבש',list,17,'','','1',"",getAddonFanart(background, custom="", default=background2))
	
	'''טינקרבל 1 (2008)'''
	thumb = 'http://ia.media-imdb.com/images/M/MV5BMjA4NTQzMDQ2MV5BMl5BanBnXkFtZTcwNzQwODQ2MQ@@._V1_UY268_CR1,0,182,268_AL_.jpg' 
	list = []
	addDir(addonString(10537).encode('utf-8') + space + '1' + space + '(2008)',list,6,thumb,addonString(105370).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''טינקרבל 2 (2009)'''
	thumb = 'http://ia.media-imdb.com/images/M/MV5BMTc3OTc4ODc4OV5BMl5BanBnXkFtZTcwOTEzOTIxMw@@._V1_UY268_CR5,0,182,268_AL_.jpg' 
	list = []
	if 'English' in General_LanguageL:
		list.append('&dailymotion_id=x2l4is1') #English
	addDir(addonString(10537).encode('utf-8') + space + '2' + space + '(2009)',list,6,thumb,addonString(105370).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''טינקרבל 3 (2010)'''
	thumb = 'http://ia.media-imdb.com/images/M/MV5BMTYwMjI1MDIzMl5BMl5BanBnXkFtZTcwMTM4Nzc5Nw@@._V1_UY268_CR10,0,182,268_AL_.jpg' 
	list = []
	
	addDir(addonString(10537).encode('utf-8') + space + '3' + space + '(2010)',list,6,thumb,addonString(105370).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))

	'''טינקרבל 4 (2012)'''
	thumb = 'http://ia.media-imdb.com/images/M/MV5BMTYwMjI1MDIzMl5BMl5BanBnXkFtZTcwMTM4Nzc5Nw@@._V1_UY268_CR10,0,182,268_AL_.jpg' 
	list = []
	
	addDir(addonString(10537).encode('utf-8') + space + '4' + space + '(2012)',list,6,thumb,addonString(105370).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
		
	'''טינקרבל 5 (2014)'''
	thumb = 'http://ia.media-imdb.com/images/M/MV5BMTk5NjUzMDg3OV5BMl5BanBnXkFtZTgwMDE1MzYwMTE@._V1_UY268_CR9,0,182,268_AL_.jpg'
	list = []
	if 'Thai' in General_LanguageL:
		list.append('&dailymotion_id=x2eu58u') #Thai
	addDir(addonString(10537).encode('utf-8') + space + '5' + space + '(2014)',list,6,thumb,addonString(105370).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''טרזן (1999)'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&dailymotion_id=x3gbh1o') #English
	addDir(addonString(10539).encode('utf-8') + space + '(1999)',list,6,'http://ia.media-imdb.com/images/M/MV5BMTIxNzY1MDg2Ml5BMl5BanBnXkFtZTcwMDgxMDEzMQ@@._V1_UY268_CR2,0,182,268_AL_.jpg',addonString(105390).encode('utf-8'),'1',50, getAddonFanart(background, custom="https://i.ytimg.com/vi/73yinrBti8k/maxresdefault.jpg"))
	
	'''מועדון ווינX [Collection]'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=8xZDb6OK4e4')
		list.append('&youtube_id=SVXBErt1fHE')
		list.append('&youtube_id=zMSgF3xdHZ4')
	if 'English' in General_LanguageL:	
		list.append('&youtube_id=k_huLZPULZg')
		list.append('&youtube_id=dLVm8IrUamM')
		list.append('&youtube_id=oMCRUUvwz58')
		list.append('&youtube_id=ZYw7hBoEiwo')
	
	addDir(addonString(10455).encode('utf-8') + space + '[Collection]',list,17,'http://www.sdarot.pm/media/series/456.jpg',addonString(104550).encode('utf-8'),'1',"",getAddonFanart(background, custom="https://i.ytimg.com/vi/zMSgF3xdHZ4/maxresdefault.jpg", default=background2))
	
	'''מלך האריות 1 (1994)'''
	thumb = 'http://ia.media-imdb.com/images/M/MV5BMjEyMzgwNTUzMl5BMl5BanBnXkFtZTcwNTMxMzM3Ng@@._V1__SX2064_SY1000_.jpg'
	list = []
	if 'English' in General_LanguageL:
		list.append('&dailymotion_id=x2f088y') #English
		list.append('&dailymotion_id=x2balxi&name_=default&') #English
	if 'Hindi' in General_LanguageL:
		list.append('&dailymotion_id=x2snuxz') #Hindi
	addDir(addonString(10540).encode('utf-8') + space + '1' + space + '(1994)',list,6,thumb,addonString(105400).encode('utf-8'),'1',50, getAddonFanart(background, custom="https://i.ytimg.com/vi/n_Cl4Lwia3o/maxresdefault.jpg"))
	
	'''מלך האריות 2 (1998)'''
	thumb = 'http://ia.media-imdb.com/images/M/MV5BMTI5ODU4Mzc5OF5BMl5BanBnXkFtZTcwNzU3NTYyMQ@@._V1_UY268_CR3,0,182,268_AL_.jpg'
	list = []
	if 'English' in General_LanguageL:
		list.append('&dailymotion_id=x3gihrq') #English
	if 'Hindi' in General_LanguageL:
		pass
		
	addDir(addonString(10540).encode('utf-8') + space + '2' + space + '(1998)',list,6,thumb,addonString(105400).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://s1.dmcdn.net/JAHm2/1280x720-dM3.jpg"))
	
	'''מלך האריות 3 (2004)'''
	thumb = 'http://ia.media-imdb.com/images/M/MV5BMjAyNjE3MTkzMF5BMl5BanBnXkFtZTYwNzc3NDg2._V1_UY268_CR5,0,182,268_AL_.jpg'
	list = []
	if 'English' in General_LanguageL:
		pass
		#list.append('&dailymotion_id=x2iopcp') #Removed!
	if 'Hindi' in General_LanguageL:
		list.append('&dailymotion_id=x2sqt1o') 
	addDir(addonString(10540).encode('utf-8') + space + '3' + space + '(2004)',list,17,thumb,addonString(105400).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://wallpaperbeta.com/wallpaper_800x600/the_lion_king_3_hakuna_matata_1_%C3%90_%C3%90_film_800x600_hd-wallpaper-10933.jpg"))
	
	'''נילס הולגרסון'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=87A_2Q2CSFc') #Hebrew
	addDir(addonString(10468).encode('utf-8'),list,17,'http://www.sratim.co.il/contents/series/images/IL/2072.jpg',addonString(104680).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''מסביב לעולם עם טוויטי )'''
	thumb = ''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=mZfCJK6fv1U')
	if 'English' in General_LanguageL:
		list.append('&dailymotion_id=') #English
	if 'Hindi' in General_LanguageL:
		list.append('&dailymotion_id=') #Hindi
	addDir('מסביב לעולם עם טוויטי הסרט',list,6,thumb,'','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''סוד השוקולד'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=_ixMuVcAGhA')
	addDir('סוד השוקולד',list,17,'','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''סינדרלה (1950)'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&dailymotion_id=x3bvjsu') #English
	if 'Hindi' in General_LanguageL:
		list.append('&dailymotion_id=x2snuxz') #Hindi
	addDir(addonString(10550).encode('utf-8') + space + '1' + space + '(1950)',list,6,'http://ia.media-imdb.com/images/M/MV5BOTQxMDk1OTEyNl5BMl5BanBnXkFtZTYwNjQ0MTA5._V1__SX2064_SY1000_.jpg',addonString(105500).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''סינדרלה 2 (2002)'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&dailymotion_id=x39g9oc') #English
	addDir(addonString(10550).encode('utf-8') + space + '2' + space + '(2002)',list,6,'http://vignette2.wikia.nocookie.net/disney/images/2/21/Cinderella_II_Dreams_Come_True.jpg/revision/latest?cb=20121128002048',addonString(105500).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''סמי הכבאי (הסרט)'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=e3ChxP5afl4')
	addDir(addonString(10551).encode('utf-8'),list,17,'https://market.marmelada.co.il/photos/791458.jpg',addonString(105510).encode('utf-8'),'1',"",getAddonFanart(background, custom="http://www.tiptopline.nl/internet/beeldscherm/graphics/fireman_sam-04.jpg", default=background2))
	
	'''עלי באבא'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=nrspEf7H3Zk')
	addDir('עלי באבא',list,17,'','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''עליסה בארץ הפלאות (1951)'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&dailymotion_id=x2hq634') #English
	addDir(addonString(10509).encode('utf-8') + space + '(1951)',list,6,'https://upload.wikimedia.org/wikipedia/en/thumb/c/c1/Alice_in_Wonderland_%281951_film%29_poster.jpg/220px-Alice_in_Wonderland_%281951_film%29_poster.jpg',addonString(105090).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''עליסה בארץ הפלאות (2010)'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&dailymotion_id=x2id755') #English
	addDir(addonString(10509).encode('utf-8') + space + '(2010)',list,6,'https://upload.wikimedia.org/wikipedia/he/thumb/7/77/%D7%90%D7%9C%D7%99%D7%A1%D7%91%D7%90%D7%A8%D7%A5%D7%94%D7%A4%D7%9C%D7%90%D7%95%D7%AA.JPG/220px-%D7%90%D7%9C%D7%99%D7%A1%D7%91%D7%90%D7%A8%D7%A5%D7%94%D7%A4%D7%9C%D7%90%D7%95%D7%AA.JPG',addonString(105090).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''פיטר פן (1953)'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&dailymotion_id=x2ja5gz') #English
	addDir(addonString(10479).encode('utf-8') + space + '(1953)',list,6,'https://upload.wikimedia.org/wikipedia/he/thumb/b/ba/Pinocchio-1940-poster.jpg/250px-Pinocchio-1940-poster.jpg',addonString(104790).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''פינוקיו (1940)'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_id=dOA4-RuW_AU') #English
		list.append('&dailymotion_id=x2m89uu') #English
		list.append('&dailymotion_id=x2jpq4x') #English
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PL2kVc_zmRW2XjL3aph_IwKnSuJr9Uqs8S') #Spanish
	addDir(addonString(10480).encode('utf-8') + space + '(1940)',list,6,'https://upload.wikimedia.org/wikipedia/he/thumb/b/ba/Pinocchio-1940-poster.jpg/250px-Pinocchio-1940-poster.jpg',addonString(104800).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''פינוקיו (1992)'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_id=T7DFGAukEU0') #English
	addDir(addonString(10480).encode('utf-8') + space + '(1992)',list,6,'https://upload.wikimedia.org/wikipedia/he/thumb/b/ba/Pinocchio-1940-poster.jpg/250px-Pinocchio-1940-poster.jpg',addonString(104800).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES107M(General_LanguageL, background, background2) #קוסמות קטנות
	
	'''קסם של הורים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=otAsfw6yr1w') #
	addDir('קסם של הורים',list,17,'','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''קסם של הורים חג המולד (2013)'''
	thumb = ''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=yQyvTHIg8fE')
	if 'English' in General_LanguageL:
		list.append('&dailymotion_id=') #English
	if 'Hindi' in General_LanguageL:
		list.append('&dailymotion_id=') #Hindi
	addDir('קסם של הורים חג המולד (2013)',list,6,thumb,'','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''שלגיה ושבעת הגמדים (1937)'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&dailymotion_id=x2idsek') #English
	addDir(addonString(10589).encode('utf-8') + space + '(1937)',list,6,'http://ia.media-imdb.com/images/M/MV5BMTg3MTU1MjU2N15BMl5BanBnXkFtZTcwNzUyOTIxMw@@._V1__SX2064_SY1000_.jpg',addonString(105890).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''שפיצים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=ohhRMlTBTz4')
	addDir('שפיצים',list,17,'','','1',50,getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES105A(General_LanguageL, background, background2) #עמוד הבא סרטים
	
def CATEGORIES106(name, iconimage, desc, fanart):
	'''לפעוטות'''
	background = 106
	background2 = "" #http://1.bp.blogspot.com/-MnUXpmW1n1M/UKfOgAXUmXI/AAAAAAAAbBY/BfoQ1FNgNUk/s1600/duvcar1024x768_en_27.jpg"
	
	'''אקראי'''
	CATEGORIES_RANDOM() #אקראי
	CATEGORIES106Z(General_LanguageL, background, background2) #ערוצי טלוויזיה
	
	'''ערוצי טלוויזיה'''
	
	CATEGORIES106F(General_LanguageL, background, background2) #אוליבר
	
	'''אוצר מילים עם נוני'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLErYJg2XgxyXmgk6cyROtlJh2g-Fk_T6n')
		list.append('&youtube_pl=PLD6olaR57ZFlhTg5XRloT_rbJ8VgjlDsp')
		list.append('&youtube_id=hu7Wa2URXi4')
		list.append('&youtube_id=zSHKufiJvL4')
	if 'English' in General_LanguageL:
		pass
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=PLI3Ou6qeL8cutZ2J0QOw8c1t7Ee0coj8b')
		list.append('&youtube_pl=PLqYzUBrrH-OtK-g_DUdPV0_suL-cbcbZE')
		list.append('&youtube_pl=PLJW3gU5Gp3s1YKMixqWNl_CaILIRCI1wi')
		
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PLnc7YfgjG-D-R4By7CzjnL-XvakeClrFW')
	
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PL85EfYJjPp_DCOSmJGpuK89OCRrMPYS6n')
	if 'Georgian' in General_LanguageL:
		list.append('&youtube_pl=PLxfqqYFhVYmGv1sYp5DXj1kyXrmT8B4pI')

	addDir(addonString(10602).encode('utf-8'),list,17,'http://i.ytimg.com/vi/m67adbe1SOg/0.jpg',addonString(106020).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''בואלה וקואלה*'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL63295318280A7354')
		list.append('&youtube_pl=PL4F7EE458D510EE96')
		
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PL8F17B3FB69BA627F')
		list.append('&youtube_pl=PL0E88F6019272E685')
		
	
	addDir(addonString(10611).encode('utf-8'),list,17,'http://ww1.prweb.com/prfiles/2006/08/14/424791/uptotenBoowaKwala.jpg',addonString(106110).encode('utf-8'),'1',50, getAddonFanart(background, custom="https://lh5.ggpht.com/Yq719nfYOCeafMVVZwlL7TONN1gxd4jKhkE9L4YcKwViWdBhAEi-WEeLBboTtQFOGGc=h900"))
	
	'''בייבי איינשטיין*'''
	list = []
	
	list.append('&youtube_pl=PLwxbE7ppBW4l1nxhAxPS7ZNkQQN3Z4_jr') #בייבי איינשטיין
	list.append('&youtube_pl=PLvadvyUkv4iFxFnsG0i1mLhuvR5nQBUcf')
	list.append('&dailymotion_pl=x377f1')
	
	addDir(addonString(10603).encode('utf-8'),list,17,'http://d202m5krfqbpi5.cloudfront.net/books/1170326163l/46377.jpg',addonString(106030).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://allwallpapersnew.com/wp-content/gallery/baby-einstein-images/05008612327.jpg"))
	
	'''בילי בם בם'''
	CATEGORIES106D(General_LanguageL, background, background2)
	
	'''בינג'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLTleo-h9TFqJ4NDGmEMQXirjzWpATU1-3')
	addDir('בינג',list,17,'https://i.ytimg.com/vi/HWq9EuKkimI/hqdefault.jpg','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''ברנרד*'''
	thumb = 'https://upload.wikimedia.org/wikipedia/en/thumb/f/fa/Bernard_Bear_Poster.jpg/250px-Bernard_Bear_Poster.jpg'
	list = []
	list.append('&youtube_pl=PLegWv2p63OBOSDqXOiBigHgsq_Ep2kaKY')
	list.append('&youtube_pl=PLKLzBLbyOE9vMP4ZQaylo9gst_fgVTS01')
	list.append('&youtube_pl=PLKLzBLbyOE9u1GYfAp6BL_e5zLmlTGoYP')
	addDir(addonString(10615).encode('utf-8'),list,17,thumb,addonString(106150).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''גילגולון'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLTleo-h9TFqJpX20e1Twkc18L3a5neRMl')
	addDir('גילגולון',list,17,'https://i.ytimg.com/vi/JH8wKDynqNY/hqdefault.jpg','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''דביבוני בונבוני'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLTleo-h9TFqJ8NnaZsoLeuWiQLYaEarDu')
	addDir('דביבוני בונבוני',list,17,'https://i.ytimg.com/vi/ZUXYkF9uQNY/hqdefault.jpg','','1',50,getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES106G(General_LanguageL, background, background2) #דובוני אכפת לי (חדש)
	
	'''דובים ונהנים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLTleo-h9TFqIaAW5pDJO8ThJ_rrohsRLE')
	addDir(addonString(10617).encode('utf-8'),list,17,'http://luli.tv/Img/Albums/556/medium/%D7%93%D7%95%D7%91%D7%99%D7%9D-%D7%95%D7%A0%D7%94%D7%A0%D7%99%D7%9D3.jpg',addonString(106170).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES106E(General_LanguageL, background, background2) #דרקו	
	
	'''הגלופסים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a4%d7%a8%d7%a7%d7%99%d7%9d%20%d7%9e%d7%9c%d7%90%d7%99%d7%9d&url=seasonId%3d2593551')
		
	addDir(addonString(10624).encode('utf-8'),list,17,'http://msc.walla.co.il/w/w-160/1448200-29.jpg',addonString(106240).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''הארי הארנב'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLnraPnhPHcc7NZwbC41nphBAe-1jxXVSN')
		list.append('&youtube_id=DvYvtAoKye0')
	addDir(addonString(10618).encode('utf-8'),list,17,'https://i.ytimg.com/vi/_GASnq3zBuE/hqdefault.jpg',addonString(106180).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''הגן הקסום'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLTleo-h9TFqITKBrRwiH7gr_BEzC8d7qU')
	addDir('הגן הקסום',list,17,'http://simania.co.il/bookimages/covers64/644273.jpg','','1',50,getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES107L(General_LanguageL, background, background2) #דוק רופאת הצעצועים
	
	'''הכבשה שושנה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&wallaNew=item_id%3D2819037')
		list.append('&wallaNew=item_id%3D2819043')
		list.append('&wallaNew=item_id%3D2819050')
		list.append('&wallaNew=item_id%3D2817560')
		list.append('&wallaNew=item_id%3D2817583')
		list.append('&wallaNew=item_id%3D2817533')
		list.append('&wallaNew=item_id%3D2820067')
		list.append('&youtube_pl=PLC47880737B43FF96')
	addDir(addonString(10619).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1487.jpg',addonString(106190).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''הנימנונמים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&wallaNew=seasonId%3d2556132')
		list.append('&sdarot=season_id=1&series_id=873&series_name=%d7%94%d7%a0%d7%99%d7%9e%d7%a0%d7%95%d7%9e%d7%99%d7%9d%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f873%2fhanimnumim-%d7%94%d7%a0%d7%99%d7%9e%d7%a0%d7%95%d7%9e%d7%99%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	addDir(addonString(10620).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/873.jpg',addonString(106200).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	
	'''ויפו הכלב המעופף'''
	CATEGORIES106C(General_LanguageL, background, background2)

	'''זומזומים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLTleo-h9TFqLCFVU5Jtu1c76X0fT3KNG4')
	addDir('זומזומים',list,17,'https://i.ytimg.com/vi/nhqjS1EKsW8/hqdefault.jpg','','1',50,getAddonFanart(background, custom="", default=background2))
	
	''''''
	
	'''טונקי'''
	
	'''טוקטוק'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLTleo-h9TFqKkr82pGJe-bk1pMMxFg_b-')
	addDir('טוקטוק',list,17,'https://i.ytimg.com/vi/Cv7uEqCzgDk/hqdefault.jpg','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''טיגה וטוגה'''

	
	'''טין טן'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLTleo-h9TFqIJm4WwQGG8pIJ5OeUAsFN9')
	addDir('טין טן',list,17,'https://i.ytimg.com/vi/Qa9JAroeS4I/hqdefault.jpg','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''טיפה טופה'''

	'''יש לנחש עם חן'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=iNxcJ2GNJgA')
		list.append('&sdarot=season_id=1&series_id=883&series_name=%d7%99%d7%a9%20%d7%9c%d7%a0%d7%97%d7%a9%20%d7%a2%d7%9d%20%d7%97%d7%9f%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f883%2fyesh-lenahesh-%d7%99%d7%a9-%d7%9c%d7%a0%d7%97%d7%a9-%d7%a2%d7%9d-%d7%97%d7%9f-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	addDir('יש לנחש עם חן',list,17,'http://www.sdarot.pm/media/series/883.jpg','','1',"",getAddonFanart(background, custom="", default=background2))
	
	'''מוסטי'''
	
	'''מיילו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLTleo-h9TFqJI6GrNCJO9yjyXbZHS9X-F')
	if 'French' in General_LanguageL:
		list.append('&youtube_id=0oFDMV7OlUE')
		list.append('&dailymotion_id=x6ibte')
		list.append('&dailymotion_id=x6jo89')

	addDir(addonString(10616).encode('utf-8'),list,17,'https://i.ytimg.com/vi/Us7tmcvl01w/hqdefault.jpg',addonString(106160).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES106H(General_LanguageL, background, background2) #מיפי
	
	'''מספרי משימה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLn0MlLMGvwMVJrWgO028RM6UJrax1ItDr')
	
	addDir('מספרי משימה',list,17,'http://i.ytimg.com/vi/DjUCZgrL8cY/hqdefault.jpg',addonString(106000).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES106I(General_LanguageL, background, background2) #פוקיו
	
	'''פים ופימבה*'''
	list = []
	list.append('&youtube_pl=PLvIdvaV3orE-FmApmbSoDRXPVnlNW5TAS')
	list.append('&youtube_pl=PLTNonj9ImqaI2F7DHlMxZ3VDn8gwpaTKe')
	list.append('&youtube_pl=PLaorT66MlVdw0Ebw7cVh44jKZUQZjMbfJ')
	list.append('&youtube_pl=PLxXOTs-eZ3U4MB90gIXs7OzGyvY6l260K')
	
	list.append('&youtube_pl=PLXpVk0zgung3azsj24E2V1pkcsP8xAjDA') #English
	
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=PLCya5IM-g-FHu4jlq53yXU0FcnxWfX3U1')
	addDir(addonString(10638).encode('utf-8'),list,17,'http://msc.wcdn.co.il/archive/941107-54.jpg',addonString(106380).encode('utf-8'),'1',58,getAddonFanart(background, custom="", default=background2))
	
	'''פיצי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL5kivPlEfMCTa3yiShQstAKsvzsdZIbkx')
		list.append('&youtube_id=FKRVfhMczq8')
	addDir(addonString(10647).encode('utf-8'),list,17,'http://i.ytimg.com/vi/Y02LzkHJ_Uk/hqdefault.jpg',addonString(106470).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''צ'רלי ודודו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLTleo-h9TFqK3NlYz7T3fz6XGRfTVk2FH')
		list.append('&youtube_id=k-bXuLHXDU4')
	addDir(addonString(10657).encode('utf-8'),list,17,'https://i.ytimg.com/vi/QLtv1_pibW8/hqdefault.jpg',addonString(106570).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	''''''
	
	'''קוקו הארנב'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLTleo-h9TFqLxJd-fvXvoQFuxMXBt8k1g')
		list.append('&youtube_id=WIug1uuY3OM')
	addDir(addonString(10661).encode('utf-8'),list,17,'http://www.luli.tv/Img/Albums/377/medium/koko.jpg',addonString(106610).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''קטני'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLbHXbhgZi5cL97NlobjLHNtBwIA9VHcmw') #קטני
		list.append('&youtube_pl=PL004FC6C7ABCC0EB6')
		
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL004FC6C7ABCC0EB6') #קטני
		list.append('&youtube_pl=PLgrW7n7d9dGhal0a58isK-zn6dutfDtYO') #קטני
		list.append('&youtube_pl=PL569CDAE96B5E3F55') #קטני
		list.append('&youtube_pl=PLXpYKJNcYOf23gX6NX4oEAakBjoKtcTVN') #קטני
		
		
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=PLporszkvR1VfMzI9-XGFpgB0Nk_d5FcUj') #קטני
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLD03iNFvg_Iu6zly-qEhAu6UVEGkDxC6X') #קטני
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=PLaeO-USZ2EjxD1hW8atjt4dG6YWfEd9ov') #קטני
	
		
	addDir(addonString(10662).encode('utf-8'),list,17,'http://ecx.images-amazon.com/images/I/51cnuhgYF7L.jpg',addonString(106620).encode('utf-8'),'1',58, getAddonFanart(background, custom="http://ecx.images-amazon.com/images/I/91h3597ypWL._SL1500_.jpg"))
	
	'''קמי'''
	
	'''קרוסלת הקסמים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLTleo-h9TFqLUEkMOnwJQhkETZikw27J5')
	addDir('קרוסלת הקסמים',list,17,'https://i.ytimg.com/vi/zxcbz-Ix8aU/hqdefault.jpg','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''שבט גולו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLTleo-h9TFqIuUXjhWsQI1LpD2jFs7Doj')
	addDir('שבט גולו',list,17,'https://i.ytimg.com/vi/J58qhUyUtzg/hqdefault.jpg','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''תולי האהוב'''
	
	'''תפודים קטנים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLTleo-h9TFqILDjwXEF1zHTBwzbmnA-HT')
	addDir('תפודים קטנים',list,17,'https://i.ytimg.com/vi/8HVk4ODOl8g/hqdefault.jpg','','1',50,getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES106A(General_LanguageL, background, background2) #עמוד הבא פעוטות
	
def CATEGORIES107(name, iconimage, desc, fanart):
	background = 107
	background2 = "" #http://7-themes.com/data_images/out/63/6986632-dora-wallpaper-free.jpg"
	
	CATEGORIES_RANDOM() #אקראי
	CATEGORIES107Z(General_LanguageL, background, background2) #ערוצי טלוויזיה
	
	CATEGORIES107D(General_LanguageL, background, background2) #אדיבו
	
	CATEGORIES107I(General_LanguageL, background, background2) #צוות אומי זומי
	
	CATEGORIES107J(General_LanguageL, background, background2) #ארמון החיות
	
	'''בגינה של לין'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nickjr&name=%e1%e2%e9%f0%e4%20%f9%ec%20%ec%e9%ef&url=http%3a%2f%2fnickjr.walla.co.il%2f%3fw%3d%2f%2f2717314')
		list.append('&youtube_pl=PLPWc8VdaIIsDcjHMTBavJG-Rm8p0wvvW_')
	addDir(addonString(10705).encode('utf-8'),list,17,'http://img.youtube.com/vi/lQt9W6DU5dQ/0.jpg',addonString(107110).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES107C(General_LanguageL, background, background2) #קטנטנים - בוב הבנאי
	
	'''בומבה'''
	list = []
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_ch=BumbaKanaal/playlists')
		list.append('&youtube_pl=PLITCTw1CghePbU3EjP9D3qcRCOHFkJmJ1')
	if 'French' in General_LanguageL:
		list.append('&youtube_ch=ChaineDeBumba/playlists')
		
	addDir(addonString(10703).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Bumba-plopsaindoor.jpg/266px-Bumba-plopsaindoor.jpg',addonString(107030).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''בחצר של פופיק'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.MakoTV/?iconimage=http%3a%2f%2fimg.mako.co.il%2f2015%2f08%2f30%2fpupik_yard_f.jpg&mode=2&name=%d7%a2%d7%95%d7%a0%d7%94%201&url=http%3a%2f%2fwww.mako.co.il%2fmako-vod-23tv%2fpupik-yard-s1')
		list.append('&sdarot=series_id=1674&series_name=%d7%91%d7%97%d7%a6%d7%a8%20%d7%a9%d7%9c%20%d7%a4%d7%95%d7%a4%d7%99%d7%a7&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1674%2fbahazer-shel-popik-%d7%91%d7%97%d7%a6%d7%a8-%d7%a9%d7%9c-%d7%a4%d7%95%d7%a4%d7%99%d7%a7')
		list.append('&youtube_pl=PLth1a195qHsiYX3v_ICFAlJtnG5Yr4J0-')
	addDir('בחצר של פופיק',list,17,'http://www.sdarot.pm/media/series/1674.jpg',addonString(108990).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''בלייז ומכוניות הענק'''
	list = []
	if 'Hebrew' in General_LanguageL:
		#list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nickjr&name=%e1%ec%e9%e9%e6%20%e5%ee%eb%e5%f0%e9%e5%fa%20%e4%f2%f0%f7&url=http%3a%2f%2fnickjr.walla.co.il%2f%3fw%3d%2f%2f2868092') #Empty!
		pass
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLcj83Ngp_IlMC0eE45W0FBily_QmTtgMQ')
		list.append('&youtube_pl=')
	
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PL3qHjxSSl7AHN2XTwmBo-zD4rM4m0re19')	
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PLhsTwJBjtycgz2VmCTX-hkemfrB-vpiau')
		list.append('&youtube_pl=PLy4w2NOU7fm5HcLNdv0yFrBoE7YG9JJrm')
		if not 'Hebrew' in General_LanguageL:
			list.append('&youtube_pl=PLAyhcT8ZqFWNIWMFjt7l3LqJq0StcHocj')
	addDir(addonString(10708).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/en/thumb/3/30/Blaze_and_the_Monster_Machines_logo.png/250px-Blaze_and_the_Monster_Machines_logo.png',addonString(107080).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://4.bp.blogspot.com/-lzXysVf6vg0/UyINE-X3B3I/AAAAAAAAXXs/XCoe51pywtw/s1600/Blaze_and_the_Monster_Machines_Nickelodeon_Preschool_Nick_Jr.jpg"))
	
	CATEGORIES107E(General_LanguageL, background, background2) #דובי קטן
	
	'''ברבונסקי'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLqjVAzhugdWLoyjj0vJz405G-hS74QL1P')
		list.append('&youtube_pl=PLqjVAzhugdWK-f5YBHgywxM-6t-DvDjWN')
		
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PLogBXxHVJONDRWSpXcDV6qK9nM_WP-q_n')
		list.append('&youtube_pl=PLogBXxHVJONDRWSpXcDV6qK9nM_WP-q_n')
		list.append('&youtube_id=j4tavakwmcg')
	addDir(addonString(10710).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/ru/4/4d/%D0%91%D0%B0%D1%80%D0%B1%D0%BE%D1%81%D0%BA%D0%B8%D0%BD%D1%8B.png',addonString(107100).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''דוח דלעת'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLR7DTcU2p0QhuQU-SWBGtywN6Zt1bapZt') #Hebrew
	addDir(addonString(10714).encode('utf-8'),list,17,'http://juniortv.co.il/wp-content/uploads/2015/08/EP008_Still_004-825x510.jpg',addonString(107140).encode('utf-8'),'1',50, getAddonFanart(background, custom="https://i.ytimg.com/vi/q-1z1VdRXp0/maxresdefault.jpg"))
	
	'''דורה וחברים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom4=http://62.90.90.56/walla_vod/_definst_/mp4:media/015/242/1524273-40.mp4/playlist.m3u8')
		list.append('&youtube_id=-aeSQFWB1pA')
		list.append('&youtube_id=zbSxLv4HH3I')
		list.append('&youtube_id=_CbY8wBblCw')
		
	if 'English' in General_LanguageL:
		list.append('&youtube_id=3TQAy66Mpug')
		list.append('&youtube_pl=PLYUPX95OFYmglVK0H8V6pQYWv7xCgCLwA')
		list.append('&youtube_pl=PLwC1cnFbggP0lFxJboaw8moC5qj_P2V0f')
		list.append('&youtube_pl=EL1q_Il1879aRo4teP2it5Cg')
		
	addDir(addonString(10711).encode('utf-8'),list,17,'http://www.2bdaddy.co.il/wp-content/uploads/unnamed-25.jpg',addonString(107110).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://www.trbimg.com/img-53ee62bb/turbine/la-et-st-dora-and-friends-into-the-city-review-20140815"))
	
	'''דן הדוור'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1577&series_name=%d7%93%d7%9f%20%d7%94%d7%93%d7%95%d7%95%d7%a8&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1577%2fdan-hadavar-%d7%93%d7%9f-%d7%94%d7%93%d7%95%d7%95%d7%a8')
		list.append('&youtube_pl=PL_8KXLhQVQMK05YV3wTQ4SZyEo2kWDvNH')
	addDir(addonString(10712).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1577.jpg','','1',50,getAddonFanart(background, custom="", default=background2))

	'''דן ומוזלי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.MakoTV/?iconimage=http%3a%2f%2fimg.mako.co.il%2f2015%2f07%2f23%2fdan_muzli_f.jpg&mode=2&name=%d7%a2%d7%95%d7%a0%d7%94%201&url=http%3a%2f%2fwww.mako.co.il%2fmako-vod-23tv%2fdan-and-muzli-s1')
	addDir(addonString(10713).encode('utf-8'),list,6,'http://img.mako.co.il/2015/07/23/dan_muzli_f.jpg','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''דן מדען'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=_RaEmzVsXuc')
		list.append('&youtube_id=pWAW2WIveb4')
		list.append('&youtube_id=W4BgnDYJoI8')
		list.append('&youtube_id=tb0PCFSwWjA')
	addDir('דן מדען',list,17,'http://www.ishim.co.il/i/9/929.jpg','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''הדוד חיים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1943&series_name=%d7%9e%d7%94%20%d7%9e%d7%99%20%d7%9e%d7%95%20%d7%a2%d7%9d%20%d7%93%d7%95%d7%93%20%d7%97%d7%99%d7%99%d7%9d&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1943%2fma-me-moo-with-uncle-haim-%d7%9e%d7%94-%d7%9e%d7%99-%d7%9e%d7%95-%d7%a2%d7%9d-%d7%93%d7%95%d7%93-%d7%97%d7%99%d7%99%d7%9d')
		list.append('&youtube_pl=PLTNonj9ImqaIuFt2AyqdYFx6bCnKoFsIc')
		list.append('&youtube_id=VQLASGxELwc')
		list.append('&youtube_id=5yOKydYwMmk')
	addDir(addonString(10715).encode('utf-8'),list,17,'http://www.yap.co.il/prdPics/4298_desc3_2_2_1390119036.jpg',addonString(107150).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''הופלה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLfcYs4SRZfuI2EVify6lL8SwUc11oJ_UL')
	addDir('הופלה',list,17,'https://i.ytimg.com/vi/JJ7ZxtIBzCI/default.jpg','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''הורים וגורים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL51YAgTlfPj5sp5nUKFuwuUddCXYjiH8F')
	addDir(addonString(10717).encode('utf-8'),list,17,'https://i.ytimg.com/vi/2QOPSd1hKhQ/default.jpg',addonString(107200).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES107H(General_LanguageL, background, background2) #החברים של ברני
	CATEGORIES107O(General_LanguageL, background, background2) #החיוך של רוזי
	
	'''היי בינבה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1142&series_name=%d7%94%d7%99%d7%99%20%d7%91%d7%99%d7%a0%d7%91%d7%94%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1142%2fbumpety-boo-%d7%94%d7%99%d7%99-%d7%91%d7%99%d7%a0%d7%91%d7%94-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLsCZljh6GgKUyE7rFV66powMC1H7XrXx3')
		list.append('&youtube_id=YUNtUxIc708')
	addDir(addonString(10719).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/1142.jpg',addonString(107190).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''הרפתקאות הלו קיטי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLsu9uBjRGa__a0Mj54uZl25lod_e1_9A9')
		list.append('&youtube_pl=PL-_BcMXVkaspyjwz7S5Hs_Rgih0F1d8_d')
		list.append('&youtube_pl=PLfcYs4SRZfuI1H_eTSxA61k7_-zUOQIqC')
	
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=PLy_oDopn4AKRnE4OMtOX_yn3kDjg1yRvv')
	
	addDir(addonString(10721).encode('utf-8'),list,17,'http://www.ligdol.co.il/Upload/hello%20kitty285.jpg',addonString(107210).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES107K(General_LanguageL, background, background2) #הנסיכה סופייה
	
	'''הסוד של מיה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nickjr&name=%e4%f1%e5%e3%20%f9%ec%20%ee%e9%e4&url=http%3a%2f%2fnickjr.walla.co.il%2f%3fw%3d%2f%2f1688505')
		list.append('&youtube_pl=PLPWc8VdaIIsCGEVOC2iJxnWNEjI13xbnA')
	addDir(addonString(10723).encode('utf-8'),list,17,'http://msc.wcdn.co.il/w-2-1/w-300/768225-54.jpg',addonString(107230).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	
	'''הרפתקאות פיטר הארנב'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLfcYs4SRZfuLix_YttCD6wumoY6IihOKQ')
		list.append('&youtube_pl=PLwSKZ4wsGYZGAAvTj9qWRz9S-7GfusSZ7')
		
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLkgGhNvMiBBq8bSAqYKZ0zeI5auB0qJnu')
		list.append('&youtube_pl=PLkgGhNvMiBBqXusYRqb43sOgrsT4te7bi')
		list.append('&youtube_id=YUfrUExon0s')
		list.append('&youtube_id=N8JsjlMSLUo')
		list.append('&youtube_id=LMN6UckXUGE')
		list.append('&youtube_id=RmpR4Qs5CdU')
		list.append('&youtube_id=5s_rP-diU3M')
		
		
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PL0UFi8iC0JNjS4_7sCE3VrhjYVLt_se2p')
		list.append('&youtube_id=nKa2S_RtWMY')
		list.append('&youtube_id=VIPr6R4AWIM')
		list.append('&youtube_id=PE1v84f_hXk')
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	addDir(addonString(10724).encode('utf-8'),list,17,'https://d1hekt5vpuuw9b.cloudfront.net/assets/article/dee955838f940459c8bdc9edabaebfe1_peter-rabbit_580x326_featuredImage.jpg',addonString(107240).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://2.bp.blogspot.com/-aIioBe9h7EI/URQurbcSU5I/AAAAAAAAROI/QCtW1fwAtpw/s1600/Nickelodeon-CGI-Animated-Preschool-Series-Peter-Rabbit-Show-Cast-Press-Image-Jr-Junior-Silvergate-Media-Brown-Bag-Films-Cartoon-Animation.jpg"))
	
	'''זמן לזוז'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom4=http://62.90.90.56/walla_vod/_definst_/mp4:media/015/871/1587113-40.mp4/playlist.m3u8')
		list.append('&custom4=http://62.90.90.56/walla_vod/_definst_/mp4:media/015/871/1587119-40.mp4/playlist.m3u8')
	addDir(addonString(10725).encode('utf-8'),list,17,'https://i.ytimg.com/vi/a-W-ieHFz8c/hqdefault.jpg',addonString(107250).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''ויקי וג'וני'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLegWv2p63OBNcqEDI7eVkARiWIbtbUZUS')
		list.append('&youtube_pl=PLE27B67D526863479')
	
	addDir(addonString(10726).encode('utf-8'),list,17,'https://i.ytimg.com/vi/fPnWeHeSxjw/mqdefault.jpg',addonString(107260).encode('utf-8'),'1',50, getAddonFanart(background, custom="https://i.ytimg.com/vi/498POdZHRDA/maxresdefault.jpg"))
	
	'''זאק וקוואק'''
	
	'''חבורת 7ג'''
	list = []
	if 'Hebrew' in General_LanguageL:
		pass
	
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLe-Na2ky4G0AeFESccRuVngVs5dF7HtDe')
				
	addDir(addonString(10738).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/en/1/1c/The_7D_logo.png',addonString(107380).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://img3.wikia.nocookie.net/__cb20140709082318/disney/images/a/a4/The_7D.png"))
	
	'''טימותי הולך לבית הספר'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1736&series_name=%d7%98%d7%99%d7%9e%d7%95%d7%aa%d7%99%20%d7%94%d7%95%d7%9c%d7%9a%20%d7%9c%d7%91%d7%99%d7%aa%20%d7%94%d7%a1%d7%a4%d7%a8%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1736%2ftimothy-goes-to-school-%d7%98%d7%99%d7%9e%d7%95%d7%aa%d7%99-%d7%94%d7%95%d7%9c%d7%9a-%d7%9c%d7%91%d7%99%d7%aa-%d7%94%d7%a1%d7%a4%d7%a8-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLtE3COCsPAWm5JRiKxtfQjUEVy7YiVUMO')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLyJA77GdW64bIjAcK-N9oIEdqStHqjXLL') #English
		list.append('&youtube_pl=PLyJA77GdW64YTdJSP4jIy1GclZ82KcSqq') #English
	addDir(addonString(10728).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1736.jpg',addonString(107280).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))	
	
	'''טימי טיים*'''
	list = []
	list.append('&youtube_pl=PLnw_wYZBfzuMvORLwC7HYsR2qpxXeZucu') #TIMMY TIME
	list.append('&youtube_pl=PLLkqDC9xIu8Z7Aflrjr9SVbULT-42942l')
	list.append('&youtube_pl=PLnw_wYZBfzuNfTcbuUfPrDov2jC8APZk0')
	list.append('&youtube_id=_vb2lCx36bA')
	
	addDir(addonString(10732).encode('utf-8'),list,17,'http://www.littleprince.co.il/pub/5897/timmy/timmy~big%20and%20cuddly~hr~21017.jpg',addonString(107320).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''טלטאביז'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLTleo-h9TFqLYGm9ibuEYE-4kUMvb7vHw')
		list.append('&youtube_pl=PLBDE473A2E30EE847')
		list.append('&youtube_id=TGmpQKg2NtQ')
		list.append('&youtube_id=mAlgerULqyU')
		list.append('&youtube_id=3cJYHKsa52E')
		list.append('&youtube_id=BOzl3RHn4Io')
		list.append('&youtube_id=VZzivZvWidI')
		list.append('&youtube_id=NN_gqjA8jJQ')
		list.append('&youtube_id=AL0RVZMr-VY') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_id=C_Km9NYD-Pw') #English
		list.append('&youtube_id=d_zk--Iconw') #English
		list.append('&youtube_id=d3yfZlIUwF4')
		list.append('&youtube_id=GUWpiwVZ-gI')
		list.append('&youtube_id=wTm5rDg8tqI')
		list.append('&youtube_id=1E9Z0-ppTl0')
		list.append('&youtube_id=JdKoA4lIENc')
		list.append('&youtube_id=GI4j0xDtU5Y')
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=PLiYnki7YcURvX8um3QXUYBflo7nPajnG3') #טלטאביז
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PL58leaokT4HSFmnwtRrjvXQg9SZqnjsaG') #טלטאביז
		list.append('&youtube_pl=PLGmqLSExAs-IEWUaGV7T4usQeWG0KpsMx')
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=PLS6A4SYN00LYYloR80D1aubcjcEO0o376') #טלטאביז
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PL718qI31wRq9nDjjDvBvLzFo3SxpKve-p') #טלטאביז
	addDir(addonString(10729).encode('utf-8'),list,17,'http://ia.media-imdb.com/images/M/MV5BMjE3MDcyMjcxN15BMl5BanBnXkFtZTYwNDQzNTQ5._V1_UX182_CR0,0,182,268_AL_.jpg',addonString(107290).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''טום הטרקטור*'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_id=')

		list.append('&youtube_id=AL0RVZMr-VY') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_id=') #English
		list.append('&youtube_id=') #English
		list.append('&youtube_id=')

	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=PL7888E4250CBA46CA') #טום הטרקטור
		list.append('&youtube_id=lPXDH3JRyuw')
		
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=') #טום הטרקטור
		list.append('&youtube_pl=')
	if 'Polish' in General_LanguageL:
		list.append('&youtube_id=HrozQ_qBqWk')
		list.append('&youtube_id=IToAJBRgUJ0')
		
		
		list.append('&youtube_pl=') #טום הטרקטור
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=') #טום הטרקטור
	
	addDir(addonString(10733).encode('utf-8'),list,17,'http://img3.wikia.nocookie.net/__cb20140514190239/traktor-tom/da/images/f/fa/Tractor_Tom.jpg',addonString(107330).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://www.pohadkar.cz/public/media/Traktor_Tom/obrazky/tractor-tom-1.jpg"))
	
	'''יובל המבולבל'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_ch=7yuval')
		list.append('&youtube_pl=PLzAqQoYm2t2xi_8LMKWYVfW0DjchcSzv0')
		list.append('&youtube_pl=PLfcYs4SRZfuIrU-AvQvAoJ01gW-EnlfHw')
	addDir('יובל המבולבל',list,17,'http://images1.ynet.co.il/PicServer3/2013/05/29/4652192/3977474099288408529no.jpg',addonString(107310).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://www.ashdodnet.com/dyncontent/t_post/2012/7/24/26370203843604787436.jpg"))
	
	'''יצירה בקצרה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLPWc8VdaIIsC0SPM0_dgOVIDn5vcCH8Ti')
		list.append('&youtube_pl=PLPWc8VdaIIsD85fRihIJFTzwt9v_JX2t6')
		list.append('&custom4=http://62.90.90.56/walla_vod/_definst_/mp4:media/015/233/1523392-40.mp4/playlist.m3u8')
		list.append('&custom4=http://62.90.90.56/walla_vod/_definst_/mp4:media/015/242/1524273-40.mp4/playlist.m3u8')
	addDir('יצירה בקצרה',list,17,'http://msc.wcdn.co.il/archive/1475513-5.jpg',addonString(107340).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''מגלים עם דורה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=855&series_name=%d7%9e%d7%92%d7%9c%d7%99%d7%9d%20%d7%a2%d7%9d%20%d7%93%d7%95%d7%a8%d7%94%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f855%2fdora-the-explorer-%d7%9e%d7%92%d7%9c%d7%99%d7%9d-%d7%a2%d7%9d-%d7%93%d7%95%d7%a8%d7%94-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nickjr&name=%ee%e2%ec%e9%ed%20%f2%ed%20%e3%e5%f8%e4&url=http%3a%2f%2fnickjr.walla.co.il%2f%3fw%3d%2f%2f1688309')
		list.append('&youtube_pl=PLXgvSDrkXo6axLzoxsdy1t9bTWKOfF_uN')
	
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLfy2Sf8Vtub1rlUM8x6knGI_U43pFFR2L')
		list.append('&youtube_pl=PLrMeN4frlTDzhevY66QZVrjCOGHs84OjC')
		
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=PLLk0B1a2FT0apXz3ZVHdZ-QprLGuwrU_S')
	
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PL3qHjxSSl7AG4pvTCQWLA97yw10nNspZB')
		list.append('&youtube_id=6q3_SCXFX0U')
		list.append('&youtube_id=rhduMp-AB7Y')
		
		
	addDir(addonString(10740).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/855.jpg',addonString(107400).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://images5.fanpop.com/image/photos/28200000/dora-the-explorer-movies-and-tv-shows-28233860-1280-1024.jpg"))
	
	'''מולי וצומי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=2077&series_name=%d7%9e%d7%95%d7%9c%d7%99%20%d7%95%d7%a6%d7%95%d7%9e%d7%99&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f2077%2fmuli-and-tzumi-%d7%9e%d7%95%d7%9c%d7%99-%d7%95%d7%a6%d7%95%d7%9e%d7%99')
	addDir(addonString(10742).encode('utf-8'),list,17,'http://www.yap.co.il/prdPics/4309_desc3_2_1_1390393153.jpg',addonString(107420).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''מיילס מהמחר'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1667&series_name=%d7%9e%d7%98%d7%95%d7%a8%d7%9c%d7%9c%d7%99%d7%9d%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1667%2ftrolls-of-troy-%d7%9e%d7%98%d7%95%d7%a8%d7%9c%d7%9c%d7%99%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=PLVwL64lSxWWxwkyH-xdNi5bfgyJ_UcudA')
	
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL1fY_FCMpjVJd2U25MFEfgjR9lx-VUntI')
		list.append('&youtube_pl=PL1fY_FCMpjVKjqfzzwqrRgJH_9M7C-Vnj')
		
		
	addDir(addonString(10759).encode('utf-8'),list,17,'http://milesfromtomorrowlandtoys.com/wp-content/uploads/2015/09/Miles_from_tomorrowlan_render1.png',addonString(107590).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://cdnvideo.dolimg.com/cdn_assets/30d9ad46a7c968160f425855f200136ab610fb3e.jpg"))
	
	'''לונטיק'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLqjVAzhugdWJ8Jb_LhDP96B7lMPPDF3Jy')
	if 'Russian' in General_LanguageL:
		list.append('&youtube_id=cW8hxIEE-8g')
		list.append('&youtube_pl=PL96FE73DBEC97346F')
		list.append('&youtube_pl=PLB5181F5EC192226F')

	
	addDir(addonString(10751).encode('utf-8'),list,17,'https://yt3.ggpht.com/-PQGvx_HtSm0/AAAAAAAAAAI/AAAAAAAAAAA/zhHb-7-fKnk/s100-c-k-no/photo.jpg',addonString(107510).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''מועדון החברים של מיקי מאוס'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1656&series_name=%d7%9e%d7%95%d7%a2%d7%93%d7%95%d7%9f%20%d7%94%d7%97%d7%91%d7%a8%d7%99%d7%9d%20%d7%a9%d7%9c%20%d7%9e%d7%99%d7%a7%d7%99%20%d7%9e%d7%90%d7%95%d7%a1%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1656%2fthe-mickey-mouse-club-%d7%9e%d7%95%d7%a2%d7%93%d7%95%d7%9f-%d7%94%d7%97%d7%91%d7%a8%d7%99%d7%9d-%d7%a9%d7%9c-%d7%9e%d7%99%d7%a7%d7%99-%d7%9e%d7%90%d7%95%d7%a1-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLI-nQtOHVKRu0erW8Khquk1pRvEHDpR7i') #English
		list.append('&youtube_pl=PLmC05rj_6ViYvReMLbUEmNgyrKWrmpA4c') #English
	addDir(addonString(10744).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1656.jpg',addonString(107440).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://s2.dmcdn.net/IRKa_/1280x720-nzB.jpg"))
	
	'''מועדון המאפים הטובים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nickjr&name=%ee%f8%20%ec%ee%e4%20%e5%e2%e1%f8%fa%20%eb%eb%e4&url=http%3a%2f%2fnickjr.walla.co.il%2f%3fw%3d%2f%2f2743907')
		list.append('&youtube_pl=PLPWc8VdaIIsDUd9awquJznDcL_aSyi00T')
		list.append('&youtube_pl=PLPWc8VdaIIsCfrHCUj7XKDG_rvLwE9V-p')
	addDir('מועדון המאפים הטובים',list,17,'http://www.erezdvd.co.il/sites/default/files/imagecache/product_full/products/gilisip.jpg',addonString(107450).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''מיכל הקטנה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLTNonj9ImqaKElCJ-4e8X_3BzXvzEYU_0')
	addDir(addonString(10245).encode('utf-8'),list,17,'http://www.pashbar.co.il/pictures/show_big_0523173001376412565.jpg',addonString(102450).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''מיקי כוכבת הילדים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_ch=mikikids')
		list.append('&youtube_id=5Zf0uSGOzlA')
		list.append('&youtube_id=BKCAXKFXwEg')
		list.append('&youtube_id=zGyEGXx3qkU')
	addDir('מיקי כוכבת הילדים',list,17,'http://yt3.ggpht.com/-LQQaGMJh2g0/AAAAAAAAAAI/AAAAAAAAAAA/KebzcCn-y_Y/s88-c-k-no/photo.jpg',addonString(107460).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''מפרץ ההרפתקאות'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nickjr&name=%ee%f4%f8%f5%20%e4%e4%f8%f4%fa%f7%e0%e5%fa&url=http%3a%2f%2fnickjr.walla.co.il%2f%3fw%3d%2f%2f2836047')
		list.append('&sdarot=season_id=1&series_id=1990&series_name=%d7%9e%d7%a4%d7%a8%d7%a5%20%d7%94%d7%94%d7%a8%d7%a4%d7%aa%d7%a7%d7%90%d7%95%d7%aa%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1990%2fpaw-patrol-%d7%9e%d7%a4%d7%a8%d7%a5-%d7%94%d7%94%d7%a8%d7%a4%d7%aa%d7%a7%d7%90%d7%95%d7%aa-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	
	if 'English' in General_LanguageL:
		list.append('&youtube_id=fJQR-Irhwi0') #English
		list.append('&youtube_pl=PL3Mze8NB9uQVLmcBoehWyrkOvuH02R41G')
		list.append('&youtube_pl=PLrMeN4frlTDweVXcqoi65z5CmTRyROUFt')
		list.append('&youtube_pl=PLrMeN4frlTDwCITZsX0PS6EWw9OWTo_G6')
		list.append('&youtube_pl=PLdpGrR3siRzmLzfP_DHcqUD7G0a7KkDxW')
	
	if 'Russian' in General_LanguageL:
		list.append('&youtube_id=') #
		list.append('&youtube_pl=PLrMeN4frlTDz_gBWYQVUYAOUCVpDPQxLf')

	if 'French' in General_LanguageL:
		list.append('&youtube_id=') #
		list.append('&youtube_pl=PL3qHjxSSl7AEHp-CofQtv_DiIBe-MJrRQ')		
		
	addDir(addonString(10752).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/1990.jpg',addonString(107520).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://magazine.hot.net.il/blog/wp-content/uploads/2015/08/-%D7%94%D7%94%D7%A8%D7%A4%D7%AA%D7%A7%D7%90%D7%95%D7%AA-2-%D7%AA%D7%9E%D7%95%D7%A0%D7%94-%D7%9C%D7%A4%D7%95%D7%9C%D7%93%D7%A8-e1438690321188.jpg"))
	
	'''מר עגבניה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLwimDnICcPKMSeyub1DLM_2jG4aPjqI7n')
		list.append('&sdarot=series_id=859&series_name=%d7%99%d7%95%d7%91%d7%9c%20%d7%94%d7%9e%d7%91%d7%95%d7%9c%d7%91%d7%9c%3a%20%d7%9e%d7%a8%20%d7%a2%d7%92%d7%91%d7%a0%d7%99%d7%94&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f859%2fyuval-hamebulbal-mar-hagvaniya-%d7%99%d7%95%d7%91%d7%9c-%d7%94%d7%9e%d7%91%d7%95%d7%9c%d7%91%d7%9c-%d7%9e%d7%a8-%d7%a2%d7%92%d7%91%d7%a0%d7%99%d7%94')
	addDir(addonString(10798).encode('utf-8'),list,17,'http://media.israel-music.com/images/7290014394605.jpg',addonString(107980).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''מר למה וגברת ככה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=5&module=wallavod&name=%d7%9e%d7%a8%20%d7%9c%d7%9e%d7%94%20%d7%95%d7%92%d7%91%d7%a8%d7%aa%20%d7%9b%d7%9b%d7%94&url=seriesId%3d2891414')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nickjr&name=%ee%f8%20%ec%ee%e4%20%e5%e2%e1%f8%fa%20%eb%eb%e4&url=http%3a%2f%2fnickjr.walla.co.il%2f%3fw%3d%2f%2f2743907')
		list.append('&sdarot=series_id=1744&series_name=%d7%9e%d7%a8%20%d7%9c%d7%9e%d7%94%20%d7%95%d7%92%d7%91%d7%a8%d7%aa%20%d7%9b%d7%9b%d7%94&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1744%2fmr-lama-vegveret-kaha-%d7%9e%d7%a8-%d7%9c%d7%9e%d7%94-%d7%95%d7%92%d7%91%d7%a8%d7%aa-%d7%9b%d7%9b%d7%94')
		list.append('&youtube_pl=PLPWc8VdaIIsC8iEN7EhY46jmy93imkpHI')
	addDir(addonString(10748).encode('utf-8'),list,17,'http://msc.wcdn.co.il/archive/1673912-35.gif',addonString(107480).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''משחקי החשיבה של רוני'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom4=http://62.90.90.56/walla_vod/_definst_/mp4:media/020/504/2050413-40.mp4/playlist.m3u8')
		list.append('&custom4=http://62.90.90.56/walla_vod/_definst_/mp4:media/020/504/2050418-40.mp4/playlist.m3u8')
	addDir(addonString(10750).encode('utf-8'),list,17,'http://isc.wcdn.co.il/w9/v/tps/nick/lobbies/general_02.png',addonString(107500).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''משפחת יומולדת'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLPWc8VdaIIsBOUPxtM2CD7yGs1D8NCM_Z')
	addDir(addonString(10749).encode('utf-8'),list,17,'http://msc.wcdn.co.il/archive/1620289-35.gif',addonString(107490).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''סיפורי פיות'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom4=plugin://plugin.video.wallaNew.video/?mode=2&module=nickjr&name=%f1%e9%f4%e5%f8%e9%20%f4%e9%e5%fa&url=http%3a%2f%2fnickjr.walla.co.il%2f%3fw%3d%2f%2f2678298')
		list.append('&youtube_pl=PLPWc8VdaIIsD8YvtRkkqjYC5SF7TKvAcM')
	addDir(addonString(10755).encode('utf-8'),list,17,'http://isc.wcdn.co.il/w9/skins/nick_jr/17/header_pic_2745.png',addonString(107550).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES107P(General_LanguageL, background, background2) #סימסאלה גרים
	CATEGORIES107G(General_LanguageL, background, background2) #סמי הכבאי

	'''סקרדי הסנאי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1679&series_name=%d7%a1%d7%a7%d7%a8%d7%93%d7%99%20%d7%94%d7%a1%d7%a0%d7%90%d7%99%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1679%2fscaredy-squirrel-%d7%a1%d7%a7%d7%a8%d7%93%d7%99-%d7%94%d7%a1%d7%a0%d7%90%d7%99-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLdTNDKNBE8qfyXihNTPzt0rpBYkL07iXw') #English
		list.append('&youtube_pl=ELVEOAQSX3iU83mCsvSXiaUQ') #English
		list.append('&youtube_pl=ELlz0nRWbqZOISrBkk-GrPXg') #English
		list.append('&youtube_pl=ELsRinC_2rDZJq4rrylfjurw') #English
		list.append('&youtube_pl=ELAVmZC-xyw-toK-qc1PCOrw') #English
	addDir(addonString(10764).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1679.jpg',addonString(107640).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''עולמו הקסום של מקס''' #NICK
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=2108&series_name=%d7%a2%d7%95%d7%9c%d7%9e%d7%95%20%d7%94%d7%a7%d7%a1%d7%95%d7%9d%20%d7%a9%d7%9c%20%d7%9e%d7%a7%d7%a1&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f2108%2fthe-magic-world-of-max-%d7%a2%d7%95%d7%9c%d7%9e%d7%95-%d7%94%d7%a7%d7%a1%d7%95%d7%9d-%d7%a9%d7%9c-%d7%9e%d7%a7%d7%a1')
		list.append('&youtube_pl=PLPWc8VdaIIsCeVQhASYBNmykK4gKh0DCe') #Hebrew
	addDir(addonString(10760).encode('utf-8'),list,17,'http://images1.ynet.co.il/PicServer3/2013/07/21/4745895/max_01.jpg',addonString(107600).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''פיקסי'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLqjVAzhugdWJh5cXk3Y39ti4jm-2PohHY')
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PLC72B44008078E9FE')
		list.append('&youtube_pl=PLK7zXb6tNkibmTrztTTHZjd6QignUW4Cq')
		list.append('&youtube_pl=PLbDVT2u1fI0CNahEm2F8SSlZrDN5GrbJn')
	addDir(addonString(10761).encode('utf-8'),list,17,'http://www.youloveit.ru/uploads/gallery/main/791/youloveit_ru_fixiki_kartinki18.jpg',addonString(107610).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://i.vimeocdn.com/video/456717428_1280x720.jpg"))

	'''פנו דרך לנאדי''' #HOP
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a0%d7%90%d7%93%d7%99%20%d7%a2%d7%95%d7%a0%d7%94%203&url=seasonId%3d2660748')
		list.append('&sdarot=series_id=2092&series_name=%d7%a4%d7%a0%d7%95%20%d7%93%d7%a8%d7%9a%20%d7%9c%d7%a0%d7%90%d7%93%d7%99%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f2092%2fmake-way-for-noddy-%d7%a4%d7%a0%d7%95-%d7%93%d7%a8%d7%9a-%d7%9c%d7%a0%d7%90%d7%93%d7%99-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLMgRbqukGSM7jcZwAspOG2i_qX0bZh0I2') #English
		list.append('&youtube_pl=PLNkpbQ4RaGfGnnaYTPCiWoNX2dR55knsX') #English
		list.append('&youtube_pl=PLqTEO1gxHq0yU-J9nTyDvFwiBxuZ_ZGQe') #English
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PLZOr1wY3tRc_3SOdbUEdx_4wfGbFaEZx5') #Russian
		list.append('&youtube_pl=PL_kLJ0xxgnewKOhcrWAOzb9_aC0nGigUS') #Russian
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=PLsmSkb0Izi0ukIPOXrYXs5pjFaBIvtW99') #Portuguese
		list.append('&youtube_pl=PL1BE733471D322384') #Portuguese
	
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=PLE1dWDmNOYmqFeosjy_1GfVv8b-w8FIz5') #Hungarian
	addDir(addonString(10763).encode('utf-8'),list,6,'http://www.sdarot.pm/media/series/2092.jpg',addonString(107630).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''פליפר ולופקה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1153&series_name=%d7%a4%d7%9c%d7%99%d7%a4%d7%a8%20%d7%95%d7%9c%d7%95%d7%a4%d7%a7%d7%94%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1153%2fflipper-and-lopaka-%d7%a4%d7%9c%d7%99%d7%a4%d7%a8-%d7%95%d7%9c%d7%95%d7%a4%d7%a7%d7%94-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=PLerEkB0tFW3aCqMAK0gzZkkF0QjxQx-4h')
		list.append('&youtube_pl=PLerEkB0tFW3brFpEnqz3N4vU6L4NUBQi3')
	addDir(addonString(10765).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1153.jpg','וכבי סדרת האנימציה המדובבת לעברית, המתרחשת באי טרופי קסום ואידילי הם הדולפין פליפר והילד לופקה שהפכו לחברים טובים לאחר שפליפר הציל את לופקה מטביעה באוקיינוס.[CR]פליפר ולופקה, יחד עם החבורה האמיצה שלהם, יוצאים להרפתקאות מרתקות ונלחמים בכוחות הרוע שבראשם התמנון הענק והמרושע דקסטר ושומרי ראשו הכרישים חסרי המוח.','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''פפה החזיר''' #NICK JR
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_ch=UCcp5Afr_1qXMhn3UfDhtc6g/playlists')
		list.append('&youtube_pl=PLFEgnf4tmQe8P9-hSy8io-PyK2LLIVuAz')
		list.append('&youtube_pl=PLFEgnf4tmQe_YHkXH2p7X-dqnBzR0FIJn')
		
		list.append('&youtube_id=aNNB7LPwHkQ')
		list.append('&youtube_id=Ws2NXmtp61Y')
		list.append('&youtube_id=xhap8ezkfCE')
		list.append('&youtube_id=u9zAJz2wyG8') #פפה החזיר
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_id=N-MLaRXIivY')
		list.append('&youtube_id=DvAZRg_VeSg')
		
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PLAEVaVVl7Uh6jf0Lk_2gK-5AoZor_SZ_Z')
		list.append('&youtube_pl=PLrpvkUYQuRUFKClj669y7JFEgr2AkwEPI')
		list.append('&youtube_id=VWbYAAVsKHs')	
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_ch=OficialPeppa/playlists')
	if 'Italian' in General_LanguageL:
		list.append('&youtube_ch=CanaleUfficialePeppa/playlists')
		
	if 'Russian' in General_LanguageL:
		list.append('&youtube_ch=OfficialPeppaRussia/playlists')
		
		list.append('&youtube_pl=PLOgjrDemRWxKAYykYCyyHjhLg-AnVL_WJ')
		
	addDir(addonString(10766).encode('utf-8'),list,17,'http://i2.kym-cdn.com/entries/icons/original/000/017/233/Peppa.png',addonString(107660).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://weknowyourdreams.com/image.php?pic=/images/peppa-pig/peppa-pig-09.jpg"))
	
	'''צ'פצ'ולה' - מיכל כלפון'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_ch=UC64wDQFgTq9RpI1P8_p-SxA')
		list.append('&youtube_id=_Jsa4Ml77-I')
		list.append('&youtube_id=BduVyZALCYs')
		list.append('&wallaNew=item_id%3D2728301')
		list.append('&wallaNew=item_id%3D2728353')
	addDir(addonString(10768).encode('utf-8'),list,17,'https://lh5.googleusercontent.com/-4Rd1GQEZnaM/AAAAAAAAAAI/AAAAAAAAChQ/YOHq90H_OZk/photo.jpg',addonString(107680).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''קאט דה רופ*'''
	list = []
	list.append('&sdarot=series_id=1544&series_name=%d7%a7%d7%90%d7%98%20%d7%93%d7%94%20%d7%a8%d7%95%d7%a4%20-%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1544%2fom-nom-stories-%d7%a7%d7%90%d7%98-%d7%93%d7%94-%d7%a8%d7%95%d7%a4-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
	list.append('&youtube_pl=PLVxGcyI6KPth2dKNkp-0dH2VYCJCppzDE')
	list.append('&youtube_pl=PLqYXYWudQqfYNO42AoFDjr0WUbLtebnCA')
	list.append('&youtube_pl=PLOPSPZSEWlCWpW6kId3LRDlKYrvsfZQsK') #Gameplay
	addDir(addonString(10767).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1544.jpg',addonString(107670).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES107F(General_LanguageL, background, background2) #קירוקי
	CATEGORIES107Q(General_LanguageL, background, background2) #רובו אוטו פולי

	'''רוי בוי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLR7DTcU2p0Qg8pxiEld0Fg3K2Bd8gTKw5')
	addDir(addonString(10772).encode('utf-8'),list,17,'http://amarganim.co.il/images_bo/%D7%A8%D7%95%D7%99%20%D7%91%D7%95%D7%99.jpg',addonString(107720).encode('utf-8'),'1',50, getAddonFanart(background, custom="https://i.ytimg.com/vi/Uci_grLDJVo/maxresdefault.jpg"))
	
	'''רוני וקשיו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nickjr&name=%f8%e5%f0%e9%20%e5%f7%f9%e9%e5&url=http%3a%2f%2fnickjr.walla.co.il%2f%3fw%3d%2f%2f2691928')
		list.append('&youtube_pl=PLPWc8VdaIIsDPb04SHd5fzzqYt3FtmWs-')
		list.append('&youtube_pl=PLPWc8VdaIIsDCX6hU5b-ve2I_MRESc8FZ')
	addDir(addonString(10773).encode('utf-8'),list,17,'http://amarganim.co.il/images_bo/%D7%A8%D7%95%D7%A0%D7%99%20%D7%95%D7%A7%D7%A9%D7%99%D7%95.jpg',addonString(107730).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''רוץ דייגו רוץ!'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nickjr&name=%f8%e5%f5%20%e3%e9%e9%e2%e5%20%f8%e5%f5!&url=http%3a%2f%2fnickjr.walla.co.il%2f%3fw%3d%2f%2f1688298')
		list.append('&youtube_se=commonsearch101&videoDuration=long&&videoDefinition=high&')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLGlfDbXygO0aM7lIzlvQczZUIG7uWVAE_')
		list.append('&youtube_pl=PLGlfDbXygO0bFeMr9q7HHcjnegFvr52yQ')
		
	addDir(addonString(10770).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1359.jpg','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''רורי - מכונית המירוץ'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLBD5CA381B360E697') #רורי - מכונית המירוץ
		list.append('&youtube_pl=PL2_l_4eIE1ayuv8Pu5RJq4__9cWJSz_q3') #S1
		list.append('&youtube_pl=PL2_l_4eIE1awTALqUwY74eAu9jJhrHxIx') #S2
		list.append('&youtube_pl=PL2_l_4eIE1axGrnR3bOyebdHbq4FxEa4X')
		list.append('&youtube_pl=PLCD5DC0818873F01B')
		list.append('&youtube_pl=PL6D2CFE1974DC147A')
		
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLYyLwF_4uU8C5uvETiiiFdeGiDrJZgHWQ') #רורי - מכונית המירוץ
			
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=PL4AB6764BB1A5D9BC') #רורי - מכונית המירוץ
	
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=PL_8KHX6sbn_LmIgyCGpuYsG-kaL3qE6AJ') #רורי - מכונית המירוץ
		list.append('&youtube_pl=PLH1Aa9oodhpvE3_TjiudN9MmgrAc65HP4')
		
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PLNKCGwoKGNlk_mO53RtB8lY2xw_x4KCnW')
	
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=PL51C4EC12702A03E2') #רורי - מכונית המירוץ
	
	if 'Swedish' in General_LanguageL:
		list.append('&youtube_pl=PLimGLL8W7RsnaTo2rktkrhgzKYlgKWXG3') #רורי - מכונית המירוץ
	
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=')
	
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PL3qHjxSSl7AFJdTot0Gntox_a9x9CCzEv') #רורי - מכונית המירוץ
		
		
	addDir(addonString(10771).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/en/thumb/4/46/RoaryTheRacingCarFullCharacters.png/280px-RoaryTheRacingCarFullCharacters.png',addonString(107710).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://www.factorycreate.com/wp-content/uploads/2014/10/Factory_Roary_LargeImage_1350x760_02.jpg"))
	
	'''רינת ויויו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLVisQUXwii8qa6lRDe1OmCIup6ylcprfc')
	addDir(addonString(10774).encode('utf-8'),list,17,'http://media.israel-music.com/images/7290012163999.jpg',addonString(107740).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''שטויות בחדשות'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nickjr&name=%f9%e8%e5%e9%e5%fa%20%e1%e7%e3%f9%e5%fa&url=http%3a%2f%2fnickjr.walla.co.il%2f%3fw%3d%2f%2f2691886')
		list.append('&youtube_pl=PLPWc8VdaIIsBzxaUfj3smv1tJ8sKQXwrW')
	addDir(addonString(10777).encode('utf-8'),list,17,'http://images1.ynet.co.il/PicServer3/2013/02/04/4440787/shtuyot_01.jpg',addonString(107770).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''שלדון'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL_8KXLhQVQMLzs0EHUhG_9PwxVsFgDAo4')
	addDir(addonString(10778).encode('utf-8'),list,17,'https://i.ytimg.com/vi/6kSynpNXMBs/default.jpg',addonString(107780).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''שון כבשון*'''
	list = []
	list.append('&youtube_ch=UCgeyhZ9dcdOuNAy9MVa7W6w/playlists')
	list.append('&youtube_pl=PLYaaF6e9cMtG4fx0bxhS7lVNYYJ0toqqr')
	if 'Indonesian' in General_LanguageL:
		list.append('&youtube_id=KtIa3HsLxng') #S1
		list.append('&youtube_pl=PL75WpgEj_KA2a6-aSWRtjzwqLpth8afUj') #S2
		list.append('&youtube_pl=PL75WpgEj_KA0B8fal43tCjQfJwvQR8vKf') #S
	
	addDir(addonString(10730).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/he/thumb/3/36/%D7%A9%D7%95%D7%9F_%D7%9B%D7%91%D7%A9%D7%95%D7%9F_-_%D7%9C%D7%95%D7%92%D7%95.png/250px-%D7%A9%D7%95%D7%9F_%D7%9B%D7%91%D7%A9%D7%95%D7%9F_-_%D7%9C%D7%95%D7%92%D7%95.png',addonString(107300).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''שמרסקי'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PLeVA7eICJ6d0zofGFGpd3t_RXBjbuQGdW')
		list.append('&youtube_pl=PLeVA7eICJ6d30xzPCWQm7198EUJgVdOjN')
		list.append('&youtube_pl=PLeVA7eICJ6d0Lywa2hyj513nrCmrgnHdj')
		list.append('&youtube_pl=PLK7zXb6tNkiYi1TZ8HoLUS7ppv3C_AxMb')
	
	addDir(addonString(10787).encode('utf-8'),list,17,'https://yt3.ggpht.com/-NaEYR_gMd_s/AAAAAAAAAAI/AAAAAAAAAAA/ev0E714j9mM/s100-c-k-no/photo.jpg',addonString(107870).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	'''שלוש ארבע לעבודה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nickjr&name=%f9%ec%e5%f9%20%e0%f8%e1%f2%20%ec%f2%e1%e5%e3%e4&url=http%3a%2f%2fnickjr.walla.co.il%2f%3fw%3d%2f%2f2693368')
		list.append('&youtube_pl=PLPWc8VdaIIsASIzs8TcS3FFYEL68jBPWO')
	addDir(addonString(10779).encode('utf-8'),list,17,'http://www.hll.co.il/web/8888/nsf/web/8017/%D7%A9%D7%9C%D7%95%D7%A9-%D7%90%D7%A8%D7%91%D7%A2-%D7%9C%D7%A2%D7%91%D7%95%D7%93%D7%94.jpg',addonString(107790).encode('utf-8'),'1',"",getAddonFanart(background, custom="", default=background2))
	
	'''תגליות''' #לוגי
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_id=')
	addDir('תגליות',list,17,'','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''תומס הקטר'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLsDVVvjmKAxEeSD3K7wybKJ42BbZc5JlJ') #תומס הקטר
		
		list.append('&youtube_id=FrUVIyhhhkQ')
		list.append('&youtube_id=5wko2ncDqmo')
		list.append('&youtube_id=bBH0ele7qdw')
	if 'English' in General_LanguageL:
		list.append('&youtube_id=Twm_igTeias') #תומס הקטר #S1
		list.append('&youtube_id=Q2FlQuQfDso') #תומס הקטר #S2
		list.append('&youtube_id=ncXVNRl3JNo') #תומס הקטר #S3
		list.append('&youtube_id=74S8SubJnig') #תומס הקטר #S4
		list.append('&youtube_id=95QevK_1A4A') #תומס הקטר #S5
		list.append('&youtube_pl=PLMcW4qao7rUVLfxzX7zYhSd7C1fl-R-di') #תומס הקטר #S17
		list.append('&youtube_pl=PLI2i4PrLia3gAAYjMaVbAwdt1xrOsUaXS') #תומס הקטר
	
	if 'Japanese' in General_LanguageL:
		list.append('&youtube_pl=PLwGUVOoN_pI3QbBFmTHQ76uYtVS7c4yF9')
		list.append('&youtube_id=mhwasuXjMKg') #תומס הקטר
		list.append('&youtube_id=-r8U7pwvU8E') #תומס הקטר
		
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=') #תומס הקטר
	addDir(addonString(10786).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/en/d/dc/Thomas_Tank_Engine_1.JPG',addonString(107840).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://s2.dmcdn.net/IDb4H/1280x720-ebU.jpg"))
	
	'''תותית'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a4%d7%a8%d7%a7%d7%99%d7%9d%20%d7%9e%d7%9c%d7%90%d7%99%d7%9d&url=seasonId%3d2550328')
		list.append('&wallaNew=seasonId%3d2710592') #Hebrew
		list.append('&youtube_pl=PLfcYs4SRZfuJgh8F-yrhcqKuQke6YbHLj') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLGNVqRT1VxkJBlBVQFiF-FZuzPVRLhUXm') #English
		list.append('&youtube_pl=PLX4pO2h-uwKBRpV8SKQre69BJxdDY4J_i') #English
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PL31D1F4E7E212F382') #French
		list.append('&youtube_pl=PLF7169918C82398BF') #French
	addDir(addonString(10784).encode('utf-8'),list,17,'https://i1.ytimg.com/sh/YO96TrSN7Do/showposter.jpg?v=508e4f85',addonString(107840).encode('utf-8'),'1',50,getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES107A(General_LanguageL, background, background2) #עמוד הבא קטנטנים
	
def CATEGORIES108(name, iconimage, desc, fanart):
	background = 108
	background2 = "" #http://30k0u22sosp4xzag03cfogt1.wpengine.netdna-cdn.com/wp-content/uploads/2015/03/strika-3.jpg
	
	CATEGORIES_RANDOM() #אקראי
	CATEGORIES108Z(General_LanguageL, background, background2) #ערוצי טלוויזיה
	
	'''אגדת הנסיך וליאנט'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=PLITCTw1CgheMxcO_E0VMrd9LQSuWE49MW')
		
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=')
		
	addDir(addonString(10858).encode('utf-8'),list,17,'http://ecx.images-amazon.com/images/I/51leujDMgQL.jpg',addonString(108580).encode('utf-8'),'1',50, getAddonFanart(background, custom="https://static.justwatch.com/backdrop/496670/s1440/the-legend-of-prince-valiant", default=background2))
	
	'''אוסטין ואלי'''
	thumb = 'https://upload.wikimedia.org/wikipedia/en/thumb/c/c9/Austin_%26_ally_tv_series_logo.png/200px-Austin_%26_ally_tv_series_logo.png'
	fanart = 'http://img.lum.dolimg.com/v1/images/au_disneychannel_aaa_ross_aanda_superroom_albumcover_d16e7f65.jpeg'
	list = []
	if 'Hebrew' in General_LanguageL:
		thumb = 'https://upload.wikimedia.org/wikipedia/he/1/1b/A%26a.hebrew.png'
		list.append('&youtube_pl=')
	if 'English' in General_LanguageL:
		list.append('&dailymotion_pl=x46tyj') #S1-3
		list.append('&dailymotion_pl=x2fj350') #S1-3
		list.append('&dailymotion_pl=x2fiw3b') #S2
		list.append('&dailymotion_pl=x3irdaq') #S4
		
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=PLXXlWZEt9lW6W03mrW407QLmBZdRs7U4I')
		
	addDir(addonString(10859).encode('utf-8'),list,17,thumb,addonString(108590).encode('utf-8'),'1',50, getAddonFanart(background, custom=fanart, default=background2))
	
	CATEGORIES108C(General_LanguageL, background, background2) #אחים וחיות אחרות
	
	'''איוון הצארביץ והזאב האפור'''
	list = []
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PLOgjrDemRWxKAYykYCyyHjhLg-AnVL_WJ') #איוון הצארביץ והזאב האפור
		list.append('&youtube_pl=PLjnasSEuz-qROskHRihuIMhACIQQhrDZw')
		
	addDir(addonString(10803).encode('utf-8'),list,17,'http://www.fest.md/files/events/45/image_4571_1_large.jpg',addonString(108030).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''איוון מקסימוב'''
	list = []
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PL1HIp83QRJHQOmroSI5hWLo0ma89aFtND')
		list.append('&youtube_pl=PLp1Znx4yjhEvp8XODti0-0Mgnuojr3rTV')
	addDir(addonString(10802).encode('utf-8'),list,17,'https://i.ytimg.com/vi/gJEBr4MJ0uI/mqdefault.jpg',addonString(108020).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אייס'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.MakoTV/?iconimage=http%3a%2f%2fimg.mako.co.il%2f2015%2f07%2f23%2fhafranim_f.jpg&mode=2&name=%d7%a2%d7%95%d7%a0%d7%94%201&url=http%3a%2f%2fwww.mako.co.il%2fmako-vod-23tv%2fthe-diggers-S1')
		list.append('&youtube_pl=PLKMFPiSCwUk3QnO33fixyo8gCPIBN6pf0')
		
	if 'English' in General_LanguageL:
		if not 'Hebrew' in General_LanguageL:
			list.append('&youtube_pl=PLwAAJ8zskC84ZvLI23zWD85SkfaytngH-')
	addDir(addonString(10851).encode('utf-8'),list,17,'http://vignette2.wikia.nocookie.net/voiceacting/images/4/48/Get_Ace_Web_Logo.jpg/revision/latest?cb=20140315004313',addonString(108510).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://images.tvnz.co.nz/tvnz_images/get_ace/2015/01/get_ace_e345_Master.jpg", default=background2))
	
	'''איטי ועצבני'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLKMFPiSCwUk08zM6SlJ3RrCu2_zdReijH')
	addDir('איטי ועצבני',list,17,'http://f.frogi.co.il/pic/VOD_zoom/itivazbani/itivazbni_gadol_vod.png?r=1436869042','','1',"", getAddonFanart(background, custom="", default=background2))
	
	'''איק החתול'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLOcNLH674qyEvz6V-X7BPsRnJA7otQ3ds')
	if 'Russian' in General_LanguageL:	
		list.append('&youtube_pl=')
	addDir(addonString(10801).encode('utf-8'),list,17,'https://images.rapgenius.com/de1193471b5b2ab9ce7eaec9c896ec18.800x521x1.png',addonString(108010).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''אלוף הסופר סטרייקה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLKMFPiSCwUk27kVfF2uHBMqVZ9XaykEYN') #?
	addDir('אלוף הסופר סטרייקה',list,17,'http://images1.ynet.co.il/PicServer4/2015/10/07/6545370/aluf_super_strika_01.jpg','','1',50, getAddonFanart(background, custom="http://zoomtv.co.il/wp-content/uploads/2015/10/%D7%90%D7%9C%D7%95%D7%A3-%D7%94%D7%A1%D7%95%D7%A4%D7%A8-%D7%A1%D7%98%D7%A8%D7%99%D7%99%D7%A7%D7%94-%D7%9C%D7%95%D7%92%D7%95.png", default=background2))
	
	'''אלישע'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=2021&series_name=%d7%90%d7%9c%d7%99%d7%a9%d7%a2-elisha%2fseason%2f1&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f2021%2f%d7%90%d7%9c%d7%99%d7%a9%d7%a2-elisha%2fseason%2f1')
		
	addDir('אלישע',list,17,'https://upload.wikimedia.org/wikipedia/he/thumb/0/02/%D7%90%D7%9C%D7%99%D7%A9%D7%A2_%D7%A1%D7%93%D7%A8%D7%94.jpg/250px-%D7%90%D7%9C%D7%99%D7%A9%D7%A2_%D7%A1%D7%93%D7%A8%D7%94.jpg','אלישע היא קומדיית מצבים ישראלית, בכיכובו של יובל סמו המתרחשת בבית הספר "הרצל" בפתח תקווה','1',50, getAddonFanart(background, custom="", default=background2))
	
	'''בבית של פיסטוק'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL9FD9492D8C95F00F') #בבית של פיסטוק
	addDir('בבית של פיסטוק',list,17,'https://upload.wikimedia.org/wikipedia/he/thumb/6/6c/FistukLogo.jpg/250px-FistukLogo.jpg',addonString(108040).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''בורו גלאי החייזרים'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLOcNLH674qyG-Xfgy-9pxWeE6fWHIL7dh') #English
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=')
	addDir(addonString(10818).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/en/a/ab/Bureau_of_Alien_Detectors.png',addonString(108180).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''Bobobobs'''
	list = [] 
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLB461927E7B8CF3F1') #English
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PL063973E8C7388E65') #French
	addDir(addonString(10811).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/he/thumb/6/6c/FistukLogo.jpg/250px-FistukLogo.jpg',addonString(108110).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES108D(General_LanguageL, background, background2) #ביוויס ובאטהד
	
	'''בית אנוביס'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%e1%e9%fa%20%e0%f0%e5%e1%e9%f1&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f1810190')
	addDir(addonString(10816).encode('utf-8'),list,6,'https://upload.wikimedia.org/wikipedia/he/thumb/3/3c/House_of_Anubis.jpg/250px-House_of_Anubis.jpg',addonString(108160).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''בלה והבולדוגס'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%e1%ec%e4%20%e5%e4%e1%e5%ec%e3%e5%e2%f1&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2888985')
	if 'English' in General_LanguageL:
		if not 'Hebrew' in General_LanguageL:
			list.append('&youtube_pl=ELjuobdmKDkF2ilbSpE1D8fg')
	addDir(addonString(10815).encode('utf-8'),list,6,'https://upload.wikimedia.org/wikipedia/en/thumb/1/12/Bellaandthebulldogslogo.png/200px-Bellaandthebulldogslogo.png',addonString(108150).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''בלי סודות''' #addonString(10804).encode('utf-8')
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL9FD9492D8C95F00F') #בלי סודות
		list.append('&youtube_pl=PL29CF6709AA760AB5')
		list.append('&sdarot=season_id=1&series_id=1143&series_name=%d7%91%d7%9c%d7%99%20%d7%a1%d7%95%d7%93%d7%95%d7%aa&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1143%2fwithout-secrets-%d7%91%d7%9c%d7%99-%d7%a1%d7%95%d7%93%d7%95%d7%aa')
	addDir('בלי סודות',list,17,'http://www.sdarot.pm/media/series/1143.jpg','בבית של פיסטוק היא ספין-אוף של סדרת הטלוויזיה הישראלית לילדים "רגע עם דודלי".[CR]הסדרה הופקה על ידי הטלוויזיה החינוכית במשך שתי עונות בין השנים 1981 - 1983 וכללה 29 פרקים שצולמו בעונה הראשונה בשחור-לבן (18 פרקים) ובעונה השנייה בצבע (11 פרקים). הסדרה שודרה בשידורים חוזרים לאורך כל שנות השמונים והתשעים וזכתה לפופולריות רבה בקרב ילדי ישראל.[CR]עלילת הסדרה מתמקדת בהרפתקאותיהם של פיסטוק (ספי ריבלין) וידידו רגע (ציפי מור). פיסטוק הוא אדם תמהוני חביב ומגושם המתגורר בבית קטן ומוזר על ראש גבעה ורגע הוא בובה שהפכה לילד. בנוסף, התוכנית הכילה גם פינה של בובה בשם "פלטיאל ממגדיאל" וסדרה נוספת עם בובות מהולנד ב סיפורימפו אשר דובבו לעברית.[CR]הסדרה הופקה בתקציב נמוך משמעותית מסדרת האם "רגע עם דודלי". למעט פרקים מיוחדים היא צולמה רובה ככולה באולפני הטלוויזיה החינוכית ברמת אביב. החל מעונתה השנייה, זו הייתה ההפקה הראשונה של הטלוויזיה החינוכית שצולמה בצבע.[CR]רבים מפרקי הסדרה שצולמו בשחור-לבן נחשבים כיום לאבודים, מאחר שהטלוויזיה החינוכית מעולם לא שימרה אותם ולא העבירה אותם מהסרטים המקוריים לפורמט דיגיטלי מודרני.[CR]שיר הפתיחה של התוכנית נכתב על ידי לאה נאור, הולחן על ידי נורית הירש, ובוצע על ידי אילנית.','1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גאליס'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_ch=UC1ZvZmYKkigob8Vg7MSgqjg') #?
		list.append('&dailymotion_pl=x3mu52') #S1
		list.append('&dailymotion_pl=x3my1z') #S2
		list.append('&dailymotion_pl=x3mzpe') #S3
		list.append('&dailymotion_pl=x3n07f') #S4
		#list.append('&dailymotion_pl=x3nt5q') #S5
		list.append('&dailymotion_pl=x48aar') #S6
		
		list.append('&youtube_se=commonsearch101&videoDuration=long&')
		list.append('&sdarot=series_id=421&series_name=%d7%92%d7%90%d7%9c%d7%99%d7%a1&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f421%2fgalis-%d7%92%d7%90%d7%9c%d7%99%d7%a1')
	addDir(addonString(10849).encode('utf-8'),list,17,'http://www.sdarot.wf/media/series/421.jpg',addonString(108490).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://niranbd.com/newcity/vcitypics/950593/976250_597922800238215_757208968_o.jpg", default=background2))
	
	'''גיבורי האור הדור הבא'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%92%d7%99%d7%91%d7%95%d7%a8%d7%99%20%d7%94%d7%90%d7%95%d7%a8%20%d7%94%d7%93%d7%95%d7%a8%20%d7%94%d7%91%d7%90&url=seasonId%3d2884528')
	addDir('גיבורי האור הדור הבא',list,6,'','','1',50,getAddonFanart(background, custom="", default=background2))
	'''גלקטיק פוטבול'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLHGRa3D4Qeg3Vmg4oAkO-rfLoWA9Ybj0k') #גלקטיק פוטבול
		list.append('&youtube_pl=PLDOEpwVmWYUsqtvYg12JP_y51qoXpObEA') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL4FAE601401A6B3F3') #English #S1
		list.append('&youtube_pl=PLDAAEF5D78E11754B') #English #S2
		list.append('&youtube_pl=PL005SsHOGXPPjJDAemQjWvK7lvBL5iQnW') #English #S3
		list.append('&youtube_pl=PLOcNLH674qyFkgYT1powjI-XcBhAqUtA6') #English
	if 'Bulgarian' in General_LanguageL:	
		list.append('&youtube_pl=PLWMCwroYhJSo2sFT6InbR6kiQGovNvcsK') #Bulgarian
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=PLDexQIApun8-FuZkNLaoBe0JagWq9I-I-') #Italian #S2
	if 'Hungarian' in General_LanguageL:
		list.append('&youtube_pl=PLi6qC0rHH6ZgZano90K1AC9umjDocRWVV') #Hungarian #S2
	
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=PL4A983F74692C098F') #Turkish #S1
		list.append('&youtube_pl=PL4A37742103A8546E') #Turkish #S2
	addDir(addonString(10821).encode('utf-8'),list,17,'https://pbs.twimg.com/profile_images/541776376/Galactik_Reduced_Carr__400x400.jpg',addonString(108210).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''ג'ינג'י'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=') #
		list.append('&youtube_pl=') #
		list.append('&youtube_pl=') #
	addDir("ג'ינג'י",list,17,'http://msc.wcdn.co.il/w/w-635/1999686-18.jpg','','1',50, getAddonFanart(background, custom="https://www.yes.co.il/SiteCollectionImages/Pages/GINGI_landingP3.jpg", default=background2))
	
	'''גיבורי התנ"ך'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1083&series_name=%d7%92%d7%99%d7%91%d7%95%d7%a8%d7%99%20%d7%94%d7%aa%d7%a0%22%d7%9a&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1083%2fgreatest-heroes-and-legends-of-the-bible-%d7%92%d7%99%d7%91%d7%95%d7%a8%d7%99-%d7%94%d7%aa%d7%a0-%d7%9a')
		list.append('&youtube_pl=PLx1dI0IFg6RqlKwV-RPhXx_YZfDbadc7h') #גיבורי התנ"ך
	
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL67F1DD7B9B45213A')
		list.append('&youtube_pl=PLE8E08292878C59A1')
		list.append('&youtube_pl=PLx1dI0IFg6RqlKwV-RPhXx_YZfDbadc7h')
		list.append('&youtube_pl=PL488DDE53D6E20EEE')
		list.append('&youtube_id=Q1nUIA2uGMI')
		
		
	addDir(addonString(10820).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1083.jpg',addonString(108200).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גים באטן'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLOcNLH674qyEigxNLxRyVKL-c1fL9Aw_o')
	if 'Russian' in General_LanguageL:	
		list.append('&youtube_pl=')
	addDir(addonString(10819).encode('utf-8'),list,17,'http://www.animenewsnetwork.com/thumbnails/fit200x200/encyc/A116-12.jpg',addonString(108190).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גלילאו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLth1a195qHsjFGXCmLtU0WZDuLq4CiWz4') #גלילאו
		list.append('&youtube_pl=PL51YAgTlfPj6Ypxb-_Dh0eoCztCXiBYsN')
		list.append('&youtube_pl=PLth1a195qHsigShKnT9DsIyKxcTBQ70Tf')
		list.append('&youtube_pl=PL51YAgTlfPj5ERxljvk0cLQAjnLMj3son') #S4
		list.append('&youtube_pl=PLFw7KwIWHNB14v2w1rx_drmWtZPldqgtp') #S4-5
	addDir(addonString(10810).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Hila_Korach.jpg/250px-Hila_Korach.jpg',addonString(108100).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''גן חיות'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%e2%ef%20%e7%e9%e5%fa&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2656314')
	addDir('גן חיות',list,6,'https://upload.wikimedia.org/wikipedia/he/thumb/2/28/%D7%9C%D7%95%D7%92%D7%95_%D7%92%D7%9F_%D7%97%D7%99%D7%95%D7%AA.jpeg/240px-%D7%9C%D7%95%D7%92%D7%95_%D7%92%D7%9F_%D7%97%D7%99%D7%95%D7%AA.jpeg','בפתיח של כל פרק מופיע מאפיין מצחיק של גן החיות גנחה שבצומת מנחה.[CR]כל פרק מתחיל כאשר מנהל גן החיות מר פיקולו מעלה רעיון חדש לשיפור גן החיות גנחה שבצומת מנחה. הוא נוהג לקרוא למזכירתו דורותי ולציין מה יש לעשות כדי לבצע רעיון זה, אך היא חשה שעלולות להיווצר תקלות בביצוע הרעיון. בכל פרק מתרחשות עלילות משנה של דמויות נוספות בקרב עובדי גן החיות ומבקריו.','1',50, getAddonFanart(background, custom="", default=background2))
	
	'''האגדה של קורה''' #The Legend of Korra
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%e4%e0%e2%e3%e4%20%f9%ec%20%f7%e5%f8%e4&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2579878')
	addDir('האגדה של קורה',list,6,'','','1',50, getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES108B(General_LanguageL, background, background2) #הארווי ביקס
	
	'''הדב פדינגטון'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLWJa48pm3noa-CVm1nZMEZUHcQTH795Pm')
		list.append('&youtube_pl=PL5D179E8870E9F8F9')
		list.append('&youtube_pl=PLWJa48pm3noa-CVm1nZMEZUHcQTH795Pm')
		
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PLE6B301EF25A1B959') #הדב פדינגטון
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=')
	addDir(addonString(10823).encode('utf-8'),list,17,'http://www.product-reviews.net/wp-content/userimages/2007/09/paddington.jpg',addonString(10823).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''הופה היי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL1236E31BAFB62B85') #הופה היי
	addDir('הופה היי',list,17,'https://upload.wikimedia.org/wikipedia/he/thumb/e/ef/Hopa_Hey.jpg/250px-Hopa_Hey.jpg','הופה היי הייתה להקה ותוכנית טלוויזיה ישראלית מצליחה לילדים ולכל המשפחה אשר הופיעה וצולמה ברחבי ישראל במהלך שנות השמונים ושנות התשעים.[CR]סדרת הטלוויזיה של הופה היי הופקה לטלוויזיה מיוני 1986 עד מאי 1995 והכילה 63 פרקים. הסדרה שודרה בערוץ הראשון במסגרת מחלקת התוכניות לילדים ונוער.[CR]בעקבות הצלחת סדרת הטלוויזיה בקרב ילדי ישראל, במהלך שנות פעילותה הופיעה הלהקה ברחבי ישראל בשמונה מופעים מצליחים והוציאה שבעה אלבומים. מוצרים נלווים נוספים של הופה היי אשר נמכרו לאורך השנים כוללים ספרים, קלטות וידאו וחטיף שוקולד.','1',50, getAddonFanart(background, custom="", default=background2))
	
	'''הזבלונים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL1236E31BAFB62B85')
	if 'English' in General_LanguageL:	
		list.append('&youtube_pl=PLBndX23tvlo8tNeHSxeWrBdjBDMTv6XlF') #S1
		list.append('&youtube_pl=PLM1bVm0b8Gm0VUSB9Qz7Z5JqVVmFWhj9a')
		list.append('&youtube_id=tihWbgMa-NQ')
		list.append('&youtube_id=1JoHFjtiLHE')
	if 'Greek' in General_LanguageL:	
		list.append('&youtube_id=Cszu-vXyg-A')
		
	addDir(addonString(10852).encode('utf-8'),list,17,'http://www.myfirsthomepage.co.il/mfhp/trend/image/ziblonim/banner.jpg',addonString(108520).encode('utf-8'),'1',50, getAddonFanart(background, custom="https://i.ytimg.com/vi/3Vuj2hIfDtc/maxresdefault.jpg", default=background2))
	
	'''החיים עם לואי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		list.append('&youtube_pl=')
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=PLOcNLH674qyFE_bpQAmTft7NuZA7qBNBW')
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PLovF9Z5TJjw8d9PF_SmDtsdF6mTgtrL15')
		
	addDir(addonString(10817).encode('utf-8'),list,17,'http://ia.media-imdb.com/images/M/MV5BMTU1MzY1NjM3NF5BMl5BanBnXkFtZTcwNzY4NzEyMQ@@._V1_SX214_AL_.jpg',addonString(108170).encode('utf-8'),'1',50, getAddonFanart(background, custom="https://thumbs01.myvideo.ge/screens/227/2265298.jpg", default=background2))
	
	'''החממה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=5&module=wallavod&name=%d7%94%d7%97%d7%9e%d7%9e%d7%94&url=seriesId%3d2855906')
		list.append('&sdarot=series_id=349&series_name=%d7%94%d7%97%d7%9e%d7%9e%d7%94&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f349%2fhahamama-%d7%94%d7%97%d7%9e%d7%9e%d7%94')
		list.append('&youtube_se=UCdAREOT3Agv88XHKfGs9TPw') #?
		
	addDir('החממה',list,6,'https://upload.wikimedia.org/wikipedia/he/thumb/5/5b/Hahamama.jpg/250px-Hahamama.jpg','החממה היא סדרת נוער ישראלית.[CR]הסדרה מתארת את עלילותיהם של בני נוער הלומדים בבית-ספר למנהיגים הנקרא "החממה" שעל שפת הכנרת.','1',50, getAddonFanart(background, custom="https://i.ytimg.com/vi/qhil5N9kWi8/maxresdefault.jpg"))
	
	
	
	'''החפרנים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.MakoTV/?iconimage=http%3a%2f%2fimg.mako.co.il%2f2015%2f07%2f23%2fhafranim_f.jpg&mode=2&name=%d7%a2%d7%95%d7%a0%d7%94%201&url=http%3a%2f%2fwww.mako.co.il%2fmako-vod-23tv%2fthe-diggers-S1')
	addDir(addonString(10812).encode('utf-8'),list,6,'http://img.mako.co.il/2015/07/23/hafranim_f.jpg',addonString(108120).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''הטופוס'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL0975E268A42E4399')
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PL8229305931BB2E0B')
		
	if 'Dutch' in General_LanguageL:
		list.append('&youtube_pl=PLDyfEDDq7obVDwqQTJlwpNefhfb54eajN')
	if 'Polish' in General_LanguageL:
		list.append('&youtube_pl=PLgrNRgZxdFPCodbntsO9Nep8hirCwF2wS')
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLOcNLH674qyFuBlRvQYwlUdFEZgE4yUF4')
	addDir(addonString(10825).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/en/2/2d/Tofus.jpg',addonString(108250).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''The Tick'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLxqFxAMV_HrHDWuG0WdL4efHjEHXJ-ig0')
	if 'Russian' in General_LanguageL:	
		list.append('&youtube_pl=PLovF9Z5TJjw86v5oWnRwMjEIrwyuMc7Wu')
	addDir(addonString(10846).encode('utf-8'),list,6,'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/The_Tick_%28S%C3%A9rie_de_desenho_animado%29.jpg/250px-The_Tick_%28S%C3%A9rie_de_desenho_animado%29.jpg',addonString(108460).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES108F(General_LanguageL, background, background2) #הילדים מחדר 402

	'''הסוכן אנרי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%e4%f1%e5%eb%ef%20%e4%f0%f8%e9&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2851924')
	addDir('הסוכן אנרי',list,6,'','','1',50, getAddonFanart(background, custom="", default=background2))
	
	'''הצחוקייה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%e5%e9%f7%e8%e5%f8%e9%e5%f1&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f1744947')
	addDir('הצחוקייה',list,6,'','','1',50, getAddonFanart(background, custom="", default=background2))
	
	
	'''הקבצים הסודיים של כלבי מרגלים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLyuJqPammrxl2ShakPFQH-4yMAdtCEXE9')
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_id=')
		list.append('&youtube_pl=')
		
		
	if 'Romanian' in General_LanguageL:
		list.append('&youtube_pl=PLIUOFDAQm0tdAJdzaD_GMX82UXR5DBR5w')
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PLWMCwroYhJSoepoqlLT3za1PpmYpnjCR3')
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=PLuQquogfWXdssgPhLIBlHFftuUTB-kfUn')	
		
	addDir(addonString(10824).encode('utf-8'),list,17,'https://s-media-cache-ak0.pinimg.com/736x/bc/17/11/bc17115194d6d15c98673f790141849c.jpg',addonString(108240).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''הקומדי סטור'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLKMFPiSCwUk35KmF0lRIeW641IbkseuER')
		list.append('&youtube_id=OnTGfthIrSE')
		list.append('&youtube_id=xyo6FLeZ3Aw')
		list.append('&youtube_id=aSke8kN719Q')
		list.append('&youtube_id=Ui6doOZZdgg')
		list.append('&youtube_id=kQ-w5sdqOZ8')
		list.append('&youtube_id=eyUuh89Ivi0')
		list.append('&youtube_id=Tciexh7ZTio')
		list.append('&youtube_id=bCGekFm2_w4')
		list.append('&youtube_id=xlbcC9iQA0M')
	addDir(addonString(10807).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/he/5/58/Komedi.jpg',addonString(108070).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''הרפתקאות קראט'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLa8HWWMcQEGShWcQbipVlr3uEEnr0bLeh')
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PL75Ev9SzNPCbBph8ohUx7PztLgGIqqxkS')
	addDir(addonString(10813).encode('utf-8'),list,17,'http://pbskids.org/apps/media/apps/WK_World_PBS_Apps-1024X1024.png',addonString(108130).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''ויקטוריוס'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%e5%e9%f7%e8%e5%f8%e9%e5%f1&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f1744947')
	addDir('ויקטוריוס',list,6,'','','1',"", getAddonFanart(background, custom="", default=background2))
	
	'''חבורת הספסל האחורי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%e7%e1%e5%f8%fa%20%e4%f1%f4%f1%ec%20%e4%e0%e7%e5%f8%e9&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2825941')
	addDir('חבורת הספסל האחורי',list,6,'','','1',"", getAddonFanart(background, custom="", default=background2))
	
	'''חידון התנך'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL51YAgTlfPj51ODBIMhtOF_lYxjS1cuQh')
	addDir(addonString(10809).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Peresohad1985hidon.jpg/350px-Peresohad1985hidon.jpg',addonString(108090).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''טופו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL0Z8ES1NjCOLmnEaxOl5fWHvKP62ky3Bt')
	addDir('טופו',list,17,'https://i.ytimg.com/vi/D0e3ltYvggw/hqdefault.jpg','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''לואי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=')
		list.append('&youtube_pl=')
		list.append('&youtube_id=In78b28tpeQ')
		list.append('&youtube_pl=')
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=')
	addDir(addonString(10826).encode('utf-8'),list,17,'https://i.ytimg.com/vi/MvItl_ca-J8/hqdefault.jpg',addonString(108260).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://s2.dmcdn.net/OGBIH/1280x720-gt2.jpg", default=background2))
	
	'''חי ב-LA LA לנד'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%9e%d7%99%d7%9b%d7%9c%20%d7%94%d7%a7%d7%98%d7%a0%d7%94%20%d7%95%d7%94%d7%98%d7%95%d7%a0%d7%98%d7%95%d7%a0%d7%99%d7%9d&url=seasonId%3d2890384')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%97%d7%99%20%d7%91-%20LA%20LA%20%d7%9c%d7%a0%d7%93%202&url=seasonId%3d2855896')
	addDir('חי ב-LA LA לנד',list,6,'','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''יומני החופש הגדול'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=5&module=wallavod&name=%d7%99%d7%95%d7%9e%d7%a0%d7%99%20%d7%94%d7%97%d7%95%d7%a4%d7%a9%20%d7%94%d7%92%d7%93%d7%95%d7%9c&url=seriesId%3d2855910')
	addDir('יומני החופש הגדול',list,6,'','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''יפניק'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%e9%f4%f0%e9%f7&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f1878402')
		list.append('&youtube_pl=PLuQCYUv97StS-YtE8BYNUpLIxKrGOBAe6')
	addDir(addonString(10814).encode('utf-8'),list,17,'',addonString(108140).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''לא מדהימה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%ec%e0%20%ee%e3%e4%e9%ee%e4&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f1688289')
	addDir('לא מדהימה',list,6,'','','1',"", getAddonFanart(background, custom="", default=background2))
	
	'''לתפוס את בלייק'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%ec%fa%f4%e5%f1%20%e0%fa%20%e1%ec%e9%e9%f7&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2853374')
	addDir('לתפוס את בלייק',list,6,'','','1',"", getAddonFanart(background, custom="", default=background2))
	
	'''מבצע קיפוד'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=428&series_name=%d7%9e%d7%91%d7%a6%d7%a2%20%d7%a7%d7%99%d7%a4%d7%95%d7%93&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f428%2fmivtza-kipod-%d7%9e%d7%91%d7%a6%d7%a2-%d7%a7%d7%99%d7%a4%d7%95%d7%93')
		list.append('&youtube_pl=PL-SBsAk8heRkmohaurMbQdGHXoF-W4sHJ') #S1
		list.append('&youtube_pl=PL-SBsAk8heRlmbAFxsqL20CD3KTM9_a6i') #S2
		list.append('&youtube_pl=PL-PL_gKiiTUgBvZVgma7WShCSNpAfUrYhyEb') #S3
		list.append('&youtube_pl=PL-PLuzkzb0C0aRLZTbIC4vNtQKbHUkq1nTWI') #S3
		
	addDir('מבצע קיפוד',list,6,'http://www.sdarot.pm/media/series/428.jpg','מבצע קיפוד היא סדרת הרפתקאות חינוכית לילדים, ששודרה בערוץ לוגי. הסדרה היא סדרת בת של הסדרה "נשרים".','1',"", getAddonFanart(background, custom="", default=background2))
	
	'''מה פתאום'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.MakoTV/?iconimage=http%3a%2f%2fimg.mako.co.il%2f2013%2f08%2f15%2fma_pitom_f.jpg&mode=2&name=%d7%a2%d7%95%d7%a0%d7%94%201&url=http%3a%2f%2fwww.mako.co.il%2fmako-vod-23tv%2fma-pitom-s1')
	addDir(addonString(10834).encode('utf-8'),list,6,'http://img.mako.co.il/2008/08/06/replacement-b.jpg',addonString(108340).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''מועדון החנונים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLBaGngHK8wj2Ejhha53BVxYYCyCm-Y2y0') #S1
		list.append('&youtube_pl=PLKMFPiSCwUk0myYc1Z8oPLGO6hXJdf5uv') #S2
		list.append('&youtube_pl=PLKMFPiSCwUk22xxgMwcNShgeBYNSfotbB')
		list.append('&youtube_id=8xwzlXqOzwM') #S2E1
		
	
	addDir(addonString(10827).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/he/thumb/5/5e/%D7%9E%D7%95%D7%A2%D7%93%D7%95%D7%9F_%D7%94%D7%97%D7%A0%D7%95%D7%A0%D7%99%D7%9D.jpg/250px-%D7%9E%D7%95%D7%A2%D7%93%D7%95%D7%9F_%D7%94%D7%97%D7%A0%D7%95%D7%A0%D7%99%D7%9D.jpg',addonString(108270).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''מרטין על הבוקר'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1056&series_name=%d7%9e%d7%a8%d7%98%d7%99%d7%9f%20%d7%a2%d7%9c%20%d7%94%d7%91%d7%95%d7%a7%d7%a8%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1056%2fmartin-morning-%d7%9e%d7%a8%d7%98%d7%99%d7%9f-%d7%a2%d7%9c-%d7%94%d7%91%d7%95%d7%a7%d7%a8-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=PL46680F40368D0F46')
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PLRHlpEIdAaUJPRYLuwcZWv2yqJmZdOE3S') #French
	addDir(addonString(10829).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1056.jpg',addonString(108290).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''מריו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=2018&series_name=%d7%9e%d7%a8%d7%99%d7%95&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f2018%2fmario-%d7%9e%d7%a8%d7%99%d7%95')
		list.append('&dailymotion_pl=x45ton')
		list.append('&dailymotion_pl=x45p6g')
	addDir(addonString(10832).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/2018.jpg',addonString(108320).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''מר קו*'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=928&series_name=%d7%9e%d7%a8%20%d7%a7%d7%95&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f928%2fla-linea-%d7%9e%d7%a8-%d7%a7%d7%95')
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=PL69CA847A1767B3D5') #Italian
		list.append('&youtube_pl=PL2346AC7ACF71633B') #Italian
	addDir(addonString(10830).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/928.jpg',addonString(108300).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''מר שיהוק'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=2101&series_name=%d7%9e%d7%a8%20%d7%a9%d7%99%d7%94%d7%95%d7%a7%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f2101%2fmr-hiccup-%d7%9e%d7%a8-%d7%a9%d7%99%d7%94%d7%95%d7%a7-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=PLxixvuzGJWPNpD1OdK5x4LoqYKjfNUTNy')
	addDir(addonString(10831).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/2101.jpg',addonString(108310).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''מרוין מרוין'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%ee%f8%e5%e5%e9%ef%20%ee%f8%e5%e5%e9%ef&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2753755')
		list.append('&youtube_pl=') #?
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=') #
	
	addDir('מרוין מרוין',list,6,'','','1',"", getAddonFanart(background, custom="", default=background2))
	
	'''מרתה מדברת'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1640&series_name=%d7%9e%d7%a8%d7%aa%d7%94%20%d7%9e%d7%93%d7%91%d7%a8%d7%aa%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1640%2fmartha-speaks-%d7%9e%d7%a8%d7%aa%d7%94-%d7%9e%d7%93%d7%91%d7%a8%d7%aa-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=PL_8KXLhQVQMLtfN5bkh11lSA6Awg5rt9y')
	addDir(addonString(10833).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1640.jpg',addonString(108330).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''משלים שועליים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=986&series_name=%d7%9e%d7%a9%d7%9c%d7%99%d7%9d%20%d7%a9%d7%95%d7%a2%d7%9c%d7%99%d7%99%d7%9d%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f986%2fmeshalim-shualyim-%d7%9e%d7%a9%d7%9c%d7%99%d7%9d-%d7%a9%d7%95%d7%a2%d7%9c%d7%99%d7%99%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PL1F479A5492E26B5C') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLROxl1XYA9feI1PPaaOtNmxMssCdacnNX') #English
		list.append('&youtube_pl=PL2tnhrkjPvkutDzPrOwhdiJWBNluZSVaM') #English
	addDir(addonString(10835).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/986.jpg',addonString(108990).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''משפחת כספי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%ee%f9%f4%e7%fa%20%eb%f1%f4%e9&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2565349')
		list.append('&youtube_pl=') #?
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=') #
	
	addDir('משפחת כספי',list,6,'','','1',"", getAddonFanart(background, custom="", default=background2))
	
	'''נביא החושך''' #Sdarot
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLwqmbDQfp96ieQhPFLZD2oaOTYMDLhwJ4') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLQH9_jN7uLguhvbpxnjMoruzg9xTY3rNi') #English
		list.append('&youtube_pl=PLuQ1zyXvUqEiZaTQQVwyj0JRjTqKktBXz') #English
	addDir(addonString(10839).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1634.jpg',addonString(108390).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES107N(General_LanguageL, background, background2) #נווה עצלנות
	
	'''נוי והדר''' #WALLA VOD
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1454&series_name=%d7%a0%d7%95%d7%99%20%d7%95%d7%94%d7%93%d7%a8&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1454%2fnoy-ve-hadar-%d7%a0%d7%95%d7%99-%d7%95%d7%94%d7%93%d7%a8')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a0%d7%95%d7%99%20%d7%95%d7%94%d7%93%d7%a8&url=seasonId%3d2855980')
		list.append('&youtube_id=Z51T2XotMoM')
		list.append('&youtube_id=tEkfczvaoZQ')
		list.append('&youtube_id=tEkfczvaoZQ')
	addDir(addonString(10842).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1454.jpg',addonString(108420).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))

	''''נאנוק'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL_8KXLhQVQMJJ4nHubadbykzbHhzzmUPu')
		list.append('&sdarot=season_id=1&series_id=1315&series_name=%d7%a0%d7%90%d7%a0%d7%95%d7%a7%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1315%2fnanook-%d7%a0%d7%90%d7%a0%d7%95%d7%a7-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	addDir(addonString(10836).encode('utf-8'),list,17,'http://www.popy.co.il/media/Objects/Contents/E39C72A33AED45878CAB555CC24CE6BB.png.img?w=209&h=161&t=f',addonString(107540).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''נאס"א : העולם שלנו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1910&series_name=%d7%a0%d7%90%d7%a1%22%d7%90%20%3a%20%d7%94%d7%a2%d7%95%d7%9c%d7%9d%20%d7%a9%d7%9c%d7%a0%d7%95%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1910%2fnasa-our-world-%d7%a0%d7%90%d7%a1-%d7%90-%d7%94%d7%a2%d7%95%d7%9c%d7%9d-%d7%a9%d7%9c%d7%a0%d7%95-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLTnbwiCw-mMTMyud7eaLkzfQBN5gMwTIE')
	addDir(addonString(10837).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1910.jpg',addonString(108370).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''נסקר רייסר'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLZs0gQed9tMSLhHXasmy0gSjgs_vv9sU5') #English
	if 'Serbian' in General_LanguageL:
		list.append('&youtube_pl=PLWMCwroYhJSqSut59L-Sxr0A5IR-0XWeE') #Serbian
	addDir(addonString(10843).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/en/7/7f/Nascar_racers_title.png',addonString(108430).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''סאם וקאט'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%f1%e0%ed%20%e5%f7%e0%e8&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2741687')
		list.append('&youtube_pl=') #?
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=') #
	
	addDir('סאם וקאט',list,6,'','','1',"", getAddonFanart(background, custom="", default=background2))
	
	'''סבבה בנט''' #MAKO
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=891&series_name=%d7%a1%d7%91%d7%91%d7%94%20%d7%91%d7%a0%d7%98&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f891%2fsababa-benet-%d7%a1%d7%91%d7%91%d7%94-%d7%91%d7%a0%d7%98')
		list.append('&youtube_id=IJ5pD7Jyzxw')
		list.append('&youtube_id=ZBnOdu3L3SI')
		list.append('&youtube_id=MM3ZkbrHJlo')
		list.append('&youtube_id=uIXc-jhmMTk')
	addDir(addonString(10844).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/891.jpg',addonString(108440).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	
	'''סדריק'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=563&series_name=%d7%a1%d7%93%d7%a8%d7%99%d7%a7%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f563%2fcedric-%d7%a1%d7%93%d7%a8%d7%99%d7%a7-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLIR_swtdpOGlM5pCPxgrVF0PZEHo2ajHn') #Hebrew
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PLiItfFtbus3DFOhVyy075yXjvAy9XJrG5') #French
		list.append('&youtube_pl=PLia0fh24w3OtjX-rI3OFpHNGGH65Zbdtz') #French
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=PLKGaRn_uvwDfCDN0VaGqpVi62m6ufUny6') #Turkish
		list.append('&youtube_pl=PLHDypsdYQJJDgKLp0DquYdZbbnc1YSNue') #Turkish
	addDir(addonString(10838).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/563.jpg',addonString(108380).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''סול איטר'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=657&series_name=%d7%a1%d7%95%d7%9c%20%d7%90%d7%99%d7%98%d7%a8%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f657%2fsoul-eater-%d7%a1%d7%95%d7%9c-%d7%90%d7%99%d7%98%d7%a8-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=PL438F23E3CAF45E30') #?
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLRncpcX6yCQIjAlkwY0jt4Ojb4hfVFio5') #English
		list.append('&youtube_pl=ELl52PjjPiC8I') #?
	if 'Uzbek' in General_LanguageL:
		list.append('&youtube_pl=PLFYo6tyrrt1IiiOZrzmFTJYtIXwXRhUNi') #אוזבקית
	
	addDir(addonString(10854).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/657.jpg',addonString(108540).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''סופר סטרייקה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1566&series_name=%d7%a1%d7%95%d7%a4%d7%a8%20%d7%a1%d7%98%d7%a8%d7%99%d7%99%d7%a7%d7%94%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1566%2fsupa-strikas-%d7%a1%d7%95%d7%a4%d7%a8-%d7%a1%d7%98%d7%a8%d7%99%d7%99%d7%a7%d7%94-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&sdarot=series_id=1566&series_name=%d7%a1%d7%95%d7%a4%d7%a8%20%d7%a1%d7%98%d7%a8%d7%99%d7%99%d7%a7%d7%94%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&summary&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1566%2fsupa-strikas-%d7%a1%d7%95%d7%a4%d7%a8-%d7%a1%d7%98%d7%a8%d7%99%d7%99%d7%a7%d7%94-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLU6_PRY_7y1TQMr67fJ6WC2mzkqtVyU3B')
		list.append('&youtube_pl=PLKMFPiSCwUk3bjgDUSlTPskV9rA74nBiB')
		
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLJbBhDouIDY2moXY4n3F-px9zd-66RDP9') #English
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLJbBhDouIDY1KBvLTtnqihGTP2uxoVTJB') #Spanish
	if 'Portuguese' in General_LanguageL:
		list.append('&youtube_pl=PLJbBhDouIDY2b7rgjhkpgAJIWY5Vos-3j') #Portuguese
	if 'Polski' in General_LanguageL:
		list.append('&youtube_pl=PLJbBhDouIDY33fDF10-RtrFj9jivfiwH7') #Polski
	addDir(addonString(10840).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1566.jpg',addonString(108400).encode('utf-8'),'1',"http://30k0u22sosp4xzag03cfogt1.wpengine.netdna-cdn.com/wp-content/uploads/2015/03/strika-3.jpg", getAddonFanart(background, custom="", default=background2))
	
	'''סנג'אי וקרייג''' #NICK
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%f1%f0%e2%27%e0%e9%20%e5%f7%f8%e9%e9%e2&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2741715')
		list.append('&sdarot=season_id=1&series_id=1788&series_name=%d7%a1%d7%a0%d7%92%27%d7%90%d7%99%20%d7%95%d7%a7%d7%a8%d7%99%d7%99%d7%92%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1788%2fsanjay-and-craig-%d7%a1%d7%a0%d7%92-%d7%90%d7%99-%d7%95%d7%a7%d7%a8%d7%99%d7%99%d7%92-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLTjHc6tMisa8E1PS6NzXCldlpAAVAzpMW') #English
	
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PLwLVa1RYGXSQp_AgMlXLLs_RmcTKtXMTS') #French
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=PLge1O0RQ5hhbQ8F6e5Xux8poqfLb7LnwN')	
		
		
	#addDir(addonString(10841).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1788.jpg',addonString(108410).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''ספיד רייסר''' #SDAROT
	list = []
	list.append('&youtube_pl=PLR7DTcU2p0QjzH9muKiw1eTbp0aU3hB63') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLZcWUVgQtnviQjBdcwStkS6y6PA3j2mUA') #English
		list.append('&youtube_pl=PLe0iK_w3CRsqlVFQechdeNh8Nlm0f0Gfn') #English
	addDir(addonString(10863).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1804.jpg',addonString(108630).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''עמרי והפייה יעל'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL419YR22ubLBPUYYOTxv3y4J4jadrvBDM') #?
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=') #
	
	addDir('עמרי והפייה יעל',list,17,'','','1',"", getAddonFanart(background, custom="", default=background2))
	
	'''עיר החזירים'''
	list = []
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLOcNLH674qyHjdSXYpB6CPrkGOI-h7YSZ')
	if 'Russian' in General_LanguageL:	
		list.append('&youtube_pl=PLovF9Z5TJjw_T_-WPi7cr7dSptxqSXKHz')
	addDir(addonString(10864).encode('utf-8'),list,6,'http://s12.radikal.ru/i185/1103/28/6f6b8ba901b3.png',addonString(108640).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''עיר המלאכים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=554&series_name=%d7%a2%d7%99%d7%a8%20%d7%94%d7%9e%d7%9c%d7%90%d7%9b%d7%99%d7%9d%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f554%2fangel-s-friends-%d7%a2%d7%99%d7%a8-%d7%94%d7%9e%d7%9c%d7%90%d7%9b%d7%99%d7%9d-%d7%9e%d7%93%d7%95%d7%91%d7%91')
		list.append('&youtube_pl=PLBc-duIJ68eRIqdBV_R0jTHsIAd5aet-x') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL-IcKdcVyt_X68_zjNMqeI3IDyNr4LaE4') #English
		list.append('&youtube_pl=PL-PLYKWkz8U9vamZh7_xnY-kYKp5ZhP4y2oH') #English
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PLA2784F98198B430D') #French
		list.append('&youtube_pl=PLGYC_8BSiiFudjhrlcRHQm9uw1sYR8Xwv') #French
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLeLNnWBsUgnLS4_wFT4cEf8sKsAyFqCxc') #Spanish
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=PLC7B66C12749CB929') #Italian
		list.append('&youtube_pl=PLDE08622C1114A775') #Italian
	if 'Greek' in General_LanguageL:
		list.append('&youtube_pl=PL7a8BZvixhYvPr9jcgl1WBxQRjBZBjoV4') #Greek
		list.append('&youtube_pl=PL7F9941728DC2A2F4') #Greek
	if 'Turkish' in General_LanguageL:
		list.append('&youtube_pl=PL8zbfEfQBH4fcLTQNNkOeTDbO_Kg7OcVj') #Turkish
	addDir(addonString(10861).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/554.jpg',addonString(108610).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''על טבעי: סדרת האנימציה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1255&series_name=%d7%a2%d7%9c%20%d7%98%d7%91%d7%a2%d7%99%3a%20%d7%a1%d7%93%d7%a8%d7%aa%20%d7%94%d7%90%d7%a0%d7%99%d7%9e%d7%a6%d7%99%d7%94%20%2a%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1255%2fsupernatural-the-animation-%d7%a2%d7%9c-%d7%98%d7%91%d7%a2%d7%99-%d7%a1%d7%93%d7%a8%d7%aa-%d7%94%d7%90%d7%a0%d7%99%d7%9e%d7%a6%d7%99%d7%94-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL_AYqxzHii9ijePQIl8CEzizRkr5JYEjd') #English
		list.append('&youtube_pl=PLxbJ3NXwaPMXrXqmSM-zCy-AbO-f2BQME') #English
	addDir(addonString(10866).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1255.jpg',addonString(108660).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))

	'''ערי הזהב הנסתרות'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1626&series_name=%d7%a2%d7%a8%d7%99%20%d7%94%d7%96%d7%94%d7%91%20%d7%94%d7%a0%d7%a1%d7%aa%d7%a8%d7%95%d7%aa%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1626%2fthe-mysterious-cities-of-gold-%d7%a2%d7%a8%d7%99-%d7%94%d7%96%d7%94%d7%91-%d7%94%d7%a0%d7%a1%d7%aa%d7%a8%d7%95%d7%aa-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		list.append('&youtube_pl=PLwqmbDQfp96ichTyPjD-MMC5bZxYn01Mf') #Hebrew
		list.append('&youtube_pl=PLKMFPiSCwUk0g2xv447QfJlQHuMtNKegW') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=x2hPBpbfK2E&list=ELvLRRJftv4ZQ') #English
		list.append('&youtube_pl=PLKMFPiSCwUk0g2xv447QfJlQHuMtNKegW') #English
	addDir(addonString(10867).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1460.jpg',addonString(108670).encode('utf-8'),'1',"", getAddonFanart(background, custom="http://plus4chan.org/b/coc/src/137179873453.png", default=background2))
	
	'''פופאי המלח*'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1469&series_name=%d7%a4%d7%95%d7%a4%d7%90%d7%99%20%d7%94%d7%9e%d7%9c%d7%97&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1469%2fpopeye-the-sailor-%d7%a4%d7%95%d7%a4%d7%90%d7%99-%d7%94%d7%9e%d7%9c%d7%97')
	list.append('&youtube_pl=PLAD2B3930314C3FA5')
	list.append('&youtube_pl=PL9MZvRGPZkoEzhmpgT-wjPmljDeiRDOld')
	list.append('&youtube_pl=PL9MZvRGPZkoHV-2Cm2-DVpW3OdOaTnsGC')
	list.append('&youtube_pl=PLgHHcDslTatSQ-4O8jzEXsvHdfmcVA1lt')
	addDir(addonString(10868).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1469.jpg',addonString(108680).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''פוקה''' #SDAROT
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PLwqmbDQfp96g7F4hn-6yT2XRXi3w1oHPl') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLpKIU9Us2Mvpo6jpW64RXaMShLHosRNnY-wjPmljDeiRDOld') #English
		list.append('&youtube_pl=PL5DA5DBE69686729D') #English
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLpKIU9Us2Mvrl86maUz6a8NAoQcKgoMd-') #Spanish
		list.append('&youtube_pl=PLo4Z3qdePPNjc-eyvKXULuN1GuSBLlEzo') #Spanish
	if 'French' in General_LanguageL:
		list.append('&youtube_pl=PLkt5Bvp27tD1kfd5-qh62gr9reMf8oRmJ') #French
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=PLkt5Bvp27tD3CMAIJqLeNJe3vTbhEzbvx') #Italian
	addDir(addonString(10870).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/1635.jpg',addonString(108700).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES108P(General_LanguageL, background, background2) #פינגו
	
	'''1 2 3 פינגווינים!''' #Sdarot
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL_8KXLhQVQMIkR9iafygY0ztBUPSAyUki') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL0D8BG0UKzYax5sl56VUWgFuZEWHXdu5J') #English
		list.append('&youtube_pl=PLuQ1zyXvUqEiZaTQQVwyj0JRjTqKktBXz') #English
	addDir(addonString(10869).encode('utf-8'),list,17,'https://i.ytimg.com/vi/vzVdiqGJZ7E/default.jpg',addonString(108690).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''פיניאס ופרב'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=532&series_name=%d7%a4%d7%99%d7%a0%d7%99%d7%90%d7%a1%20%d7%95%d7%a4%d7%a8%d7%91%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2b%d7%aa%d7%a8%d7%92%d7%95%d7%9d%20%d7%9e%d7%95%d7%91%d7%a0%d7%94%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f532%2fphinnias-ferb-%d7%a4%d7%99%d7%a0%d7%99%d7%90%d7%a1-%d7%95%d7%a4%d7%a8%d7%91-%d7%9e%d7%93%d7%95%d7%91%d7%91-%d7%aa%d7%a8%d7%92%d7%95%d7%9d-%d7%9e%d7%95%d7%91%d7%a0%d7%94')
		#list.append('&youtube_pl=PLpm7RYAjgzoKDbffmhuNrxc_-lpTorM7G') #Hebrew
	if 'English' in General_LanguageL:
		list.append('&dailymotion_pl=x48bpr') #English #S1
		list.append('&dailymotion_pl=x48bps') #English #S2
		list.append('&dailymotion_pl=x48bpu') #English #S3
	addDir(addonString(10871).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/532.jpg',addonString(108710).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''פליקס החתול''' #WALLA VOD
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=574&series_name=%d7%a4%d7%9c%d7%99%d7%a7%d7%a1%20%d7%94%d7%97%d7%aa%d7%95%d7%9c%20-%20%2a%d7%9e%d7%93%d7%95%d7%91%d7%91%2a&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f574%2ffelix-the-cat-%d7%a4%d7%9c%d7%99%d7%a7%d7%a1-%d7%94%d7%97%d7%aa%d7%95%d7%9c-%d7%9e%d7%93%d7%95%d7%91%d7%91')
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLDqISjt-2YGUqZpTEM-38BNZSshzcViNj') #English
		list.append('&youtube_pl=PL896C42A946504FB2') #English
		list.append('&youtube_pl=PLyUjzUUY7MEld66JKzwqpbBJiMrR3LyMi') #English
	addDir(addonString(10872).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/574.jpg',addonString(108720).encode('utf-8'),'1',"", getAddonFanart(background, custom="", default=background2))
	
	'''פלישת הרבידים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		#list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%f4%ec%e9%f9%fa%20%e4%f8%e1%e9%e3%e9%ed&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2741602') #ריק
		list.append('&youtube_pl=') #S1
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PLF_QeNkDVBPLvhU8p0olMp7hwEIjifFIj') #S1
	if 'French' in General_LanguageL:
		list.append('&youtube_ch=lapincretinsinvasion/playlists')
		list.append('&youtube_id=kt_X0enZRLc') #S1
		list.append('&youtube_id=In78b28tpeQ')
		list.append('&youtube_pl=H_jIyw7cap4') #S2
	if 'Arabic' in General_LanguageL:
		list.append('&youtube_id=mU5spS35oG4')
		list.append('&youtube_id=bbGRFrZV-XQ')
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_id=dGMC6-MJ03U')
		
		
	addDir(addonString(10845).encode('utf-8'),list,17,'http://www.nick.com/nick/app/iOS/shows/rabbids-invasion/show-cover-rabbids.jpg',addonString(108450).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://vignette2.wikia.nocookie.net/ravingrabbids/images/7/73/Rabbids-invasion-101-a-omelet-party-16x9.jpg/revision/latest?cb=20130802190758", default=background2))
	
	'''פרפר נחמד'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.MakoTV/?iconimage=http%3a%2f%2fimg.mako.co.il%2f2013%2f06%2f06%2fparpar_nice_f.jpg&mode=2&name=%d7%a2%d7%95%d7%a0%d7%94%201&url=http%3a%2f%2fwww.mako.co.il%2fmako-vod-23tv%2fparpar-s1')
		list.append('&sdarot=series_id=1092&series_name=%d7%a4%d7%a8%d7%a4%d7%a8%20%d7%a0%d7%97%d7%9e%d7%93&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1092%2fparpar-nehmad-%d7%a4%d7%a8%d7%a4%d7%a8-%d7%a0%d7%97%d7%9e%d7%93')
		list.append('&youtube_pl=PL51YAgTlfPj7XTzORdSrWpgCfF1x7ZUeK')
		list.append('&youtube_pl=PL5B247BE19DDE24D5') #Hebrew
		list.append('&youtube_pl=PLE117810DAD8DB2AD') #Hebrew
		list.append('&youtube_pl=PL_mw-BY43H9zxMB_75CMCbEcidGU9-UQQ') #Hebrew
	addDir(addonString(10105).encode('utf-8'),list,17,'http://www.sdarot.wf/media/series/1092.jpg',addonString(101050).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''צור משלנו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=1320&series_name=%d7%a6%d7%95%d7%a8%20%d7%9e%d7%a9%d7%9c%d7%a0%d7%95&url=http%3a%2f%2fwww.sdarot.pm%2fwatch%2f1320%2ftzur-meshelanu-%d7%a6%d7%95%d7%a8-%d7%9e%d7%a9%d7%9c%d7%a0%d7%95')
		list.append('&youtube_pl=PLtz5gfkQ59bJw2o_B23A_Pb1ooaHq3-tj')
	addDir('צור משלנו',list,17,'http://www.sdarot.pm/media/series/1320.jpg',"צור משלנו זו תוכנית חינוכית וערכית לילדים. מדובר בבובה ועוד מס' שחקנים שכל פרק עוסק בנושא אחר חינוכי וערכי. כגון לכבד את האחר, לשפוט לכף זכות, לעזור לשני וכו' צור הוא ילד סקרן בעל הרבה חוש הומור, נוטה לשאול שאלות ואף ליישם את מה שהוא לומד.",'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קופיקו'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=UCCktKuBGZ1kHifzp9Mxu6Eg')
		list.append('&youtube_pl=PLN0EJVTzRDL_9qHYdDXgf6tslifiY_4zI')
		list.append('&youtube_pl=PLR7DTcU2p0QhDzYbbniDNwSbXUM_p6N3f')
		list.append('&youtube_pl=PLR7DTcU2p0QgEdLPHhrhKtxElvYVrseAQ') #Hebrew #S2
		list.append('&youtube_pl=PLR7DTcU2p0QhNGUffSgu8_5dP3lnOGZTx') #Hebrew #S3
	addDir(addonString(10855).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/422.jpg',addonString(108550).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''קשת וענן'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=season_id=1&series_id=1751&series_name=%d7%a7%d7%a9%d7%aa%20%d7%95%d7%a2%d7%a0%d7%9f&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f1751%2fkeshet-veanan-%d7%a7%d7%a9%d7%aa-%d7%95%d7%a2%d7%a0%d7%9f')
		list.append('&youtube_pl=PL51YAgTlfPj6qcpdP7e44dNj7xHuwd3oo') #Hebrew
	addDir(addonString(10805).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/he/thumb/5/56/Keshet_and_Anan_logo.jpg/250px-Keshet_and_Anan_logo.jpg',addonString(108050).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''ראש גדול'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&sdarot=series_id=572&series_name=%d7%a8%d7%90%d7%a9%20%d7%92%d7%93%d7%95%d7%9c&url=http%3a%2f%2fwww.sdarot.wf%2fwatch%2f572%2frosh-gadol-%d7%a8%d7%90%d7%a9-%d7%92%d7%93%d7%95%d7%9c')
		list.append('&youtube_pl=PLNMdxRa6e5t-8xyd3eFtXKIHbd6gcZPXG')
		list.append('&youtube_id=2cuxr5DLnwg')
		list.append('&youtube_id=TEuf9SojWug')
		list.append('&youtube_id=dspu_9neTsA')
		list.append('&youtube_id=syv0DjQqJQ0')
	addDir(addonString(10865).encode('utf-8'),list,17,'http://www.sdarot.pm/media/series/572.jpg',addonString(108650).encode('utf-8'),'1',50, getAddonFanart(background, custom="http://30k0u22sosp4xzag03cfogt1.wpengine.netdna-cdn.com/wp-content/uploads/2015/04/rosh-gadol7.jpg", default=background2))
	
	'''רגע עם דודלי'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&youtube_pl=PL51YAgTlfPj5gUK-SIhbYyAMUQASzrZAw')
	addDir(addonString(10806).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/he/thumb/f/fe/Dodlee.jpg/250px-Dodlee.jpg',addonString(108060).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES108Q(General_LanguageL, background, background2) #רחוב סומסום
	
	'''קסם של הורים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%f7%f1%ed%20%f9%ec%20%e4%e5%f8%e9%ed&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2516297')
		list.append('&youtube_pl=PLaGWxxBsbL1D_bSy9Vuy_UCAONqidrlWB') #
	addDir('קסם של הורים',list,17,'','','1',50, getAddonFanart(background, custom="", default=background2))
	
	'''שאמן קינג'''
	list = []
	if 'Hebrew' in General_LanguageL:
		pass
	if 'English' in General_LanguageL:
		list.append('&youtube_pl=PL494DB3F3F5F5F6CB') #English
	if 'Russian' in General_LanguageL:
		list.append('&youtube_pl=PLWMCwroYhJSqqXaG7kh8u6yk9O5gKvI29') #שאמן קינג
	if 'Italian' in General_LanguageL:
		list.append('&youtube_pl=PL327HVtSHDnsYYKAsrudqZjaOX8brHVNO') #Italian
	if 'Bulgarian' in General_LanguageL:
		list.append('&youtube_pl=PLNTB1s2moCBc2G1WKhMPI_e0RPocTVpfK') #Bulgarian
	if 'Spanish' in General_LanguageL:
		list.append('&youtube_pl=PLBCBF4FA8CB8C4FE9') #Spanish
	addDir(addonString(10885).encode('utf-8'),list,17,'https://upload.wikimedia.org/wikipedia/en/9/92/Shaman_King_25.png',addonString(108850).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''שבט צוללת'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a9%d7%91%d7%98%20%d7%a6%d7%95%d7%a6%d7%9c%d7%aa&url=seasonId%3d2855982')
		list.append('&youtube_pl=PLKMFPiSCwUk3QeQW6cq_GyoDKxZ5n0Uai') #
	addDir('שבט צוללת',list,17,'','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''שוברי גלים'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=3&module=wallavod&name=%d7%a4%d7%a8%d7%a7%d7%99%d7%9d%20%d7%9e%d7%9c%d7%90%d7%99%d7%9d&url=seasonId%3d2884205')
	addDir('שוברי גלים',list,6,'','','1',50,getAddonFanart(background, custom="", default=background2))
	
	'''שטותניק'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%f9%e8%e5%fa%f0%e9%f7&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f1837648')
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%f1%e5%f4%f8%20%f9%e8%e5%fa%f0%e9%f7&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2662395')
		list.append('&youtube_pl=PLuQCYUv97StRk-DsmuAL0ptZPJ9ATkguV') #סופר שטותניק
		
	addDir('שטותניק',list,17,'','','1',50, getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES108E(General_LanguageL, background, background2) #שי-רה נסיכת הכוח
	
	'''שכונה'''
	list = []
	if 'Hebrew' in General_LanguageL:
		#list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%f9%eb%e5%f0%e4&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2796370') #Empty!
		list.append('&dailymotion_pl=x45tcn')
		list.append('&youtube_pl=PLuQCYUv97StR0o1N7zfbpobVVwev0sx91')
		
	addDir('שכונה',list,6,'https://upload.wikimedia.org/wikipedia/he/8/80/10628436_316742958505148_2646201463663204371_n.jpg','','1',"", getAddonFanart(background, custom="", default=background2))
	
	'''שרגא בישגדא'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.MakoTV/?iconimage=http%3a%2f%2fimg.mako.co.il%2f2014%2f08%2f06%2fShraga_1920x1080_f.jpg&mode=1&name=%d7%a9%d7%a8%d7%92%d7%90%20%d7%91%d7%99%d7%a9%d7%92%d7%93%d7%90&url=http%3a%2f%2fwww.mako.co.il%2fmako-vod-23tv%2fshraga-bishgada')
		list.append('&youtube_pl=PL51YAgTlfPj5KPYOntZkqg2Nwyqj2M1Lf')
	addDir(addonString(10808).encode('utf-8'),list,17,'https://i.ytimg.com/vi/E5JQ2o84iSw/hqdefault.jpg',addonString(108080).encode('utf-8'),'1',50, getAddonFanart(background, custom="", default=background2))
	
	'''תראו את אבא'''
	list = []
	if 'Hebrew' in General_LanguageL:
		list.append('&custom8=plugin://plugin.video.wallaNew.video/?mode=2&module=nick&name=%fa%f8%e0%e5%20%e0%fa%20%e0%e1%e0&url=http%3a%2f%2fnick.walla.co.il%2f%3fw%3d%2f%2f2850878')
	addDir('תראו את אבא',list,17,'','','1',50, getAddonFanart(background, custom="", default=background2))
	
	CATEGORIES108A(General_LanguageL, background, background2) #עמוד הבא ילדים ונוער
	
def CATEGORIES109(name, iconimage, desc, fanart):
	'''לימוד שפה'''
	background = 109
	background2 = ""
	
	CATEGORIES_RANDOM() #אקראי
	CATEGORIES109B(General_LanguageL, background, background2) #לימוד שפה
	
	CATEGORIES109A(General_LanguageL, background, background2) #עמוד הבא לימוד שפה
	
def CATEGORIES200():
	background = 200
	background2 = ""
	
	'''עברית'''
	addDir(addonString_servicefeatherence(32900).encode('utf-8'),'Hebrew',90,"http://flaglane.com/download/israeli-flag/israeli-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32900).encode('utf-8')),'1',50, getAddonFanart(200, custom="http://pre15.deviantart.net/2dd4/th/pre/f/2015/166/3/2/israel_aph_by_wolf_kid1000-d8xdbyp.jpg"))
	
	'''אנגלית'''
	addDir(addonString_servicefeatherence(32901).encode('utf-8'),'English',90,"http://flaglane.com/download/british-flag/british-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32901).encode('utf-8')),'1',50, getAddonFanart(200,custom=""))
	
	'''אוזבקית'''
	addDir(addonString_servicefeatherence(32929).encode('utf-8'),'Uzbek',90,"http://flaglane.com/download/uzbekistani-flag/uzbekistani-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32929).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''אוקראינית'''
	addDir(addonString_servicefeatherence(32903).encode('utf-8'),'Ukrainian',90,"http://www.enchantedlearning.com/europe/ukraine/flag/Flagbig.GIF",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32903).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''איטלקית'''
	addDir(addonString_servicefeatherence(32909).encode('utf-8'),'Italian',90,"http://flaglane.com/download/italian-flag/italian-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32909).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))	
	
	'''אינדונזית'''
	addDir(addonString_servicefeatherence(32927).encode('utf-8'),'Indonesian',90,"http://www.united-states-flag.com/media/catalog/product/cache/2/thumbnail/9df78eab33525d08d6e5fb8d27136e95/F/L/FLGDECL1000004754_-00_indonesia-flag-decal_3.jpg",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32927).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''אירית'''
	addDir(addonString_servicefeatherence(32912).encode('utf-8'),'Irish',90,"http://flaglane.com/download/irish-flag/irish-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32912).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''בולגרית'''
	addDir(addonString_servicefeatherence(32928).encode('utf-8'),'Bulgarian',90,"http://flaglane.com/download/bulgarian-flag/bulgarian-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32928).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''גאורגית'''
	addDir(addonString_servicefeatherence(32906).encode('utf-8'),'Georgian',90,"http://freestock.ca/georgia_grunge_flag_sjpg1133.jpg",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32906).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''גרמנית'''
	addDir(addonString_servicefeatherence(32920).encode('utf-8'),'German',90,"http://flaglane.com/download/german-flag/german-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32920).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''דנית'''
	addDir(addonString_servicefeatherence(32933).encode('utf-8'),'Dansk',90,"http://flaglane.com/download/dane-flag/dane-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32933).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''הודית'''
	addDir(addonString_servicefeatherence(32923).encode('utf-8'),'Hindi',90,"http://www.iloveindia.com/national-symbols/pics/indian-flag.jpg",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32923).encode('utf-8')),'1',50, getAddonFanart(200, custom="http://allpicts.in/download/5073/india_flag_fluttering_by_kids_for_Indian_Independence_day_Celebration.jpg/"))
	
	'''הולנדית'''
	addDir(addonString_servicefeatherence(32902).encode('utf-8'),'Dutch',90,"http://flaglane.com/download/dutch-flag/dutch-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32902).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''הונגרית'''
	addDir(addonString_servicefeatherence(32921).encode('utf-8'),'Hungarian',90,"http://flaglane.com/download/hungarian-flag/hungarian-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32921).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''טורקית'''
	addDir(addonString_servicefeatherence(32916).encode('utf-8'),'Turkish',90,"http://flaglane.com/download/turkish-flag/turkish-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32916).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''יוונית'''
	addDir(addonString_servicefeatherence(32931).encode('utf-8'),'Greek',90,"http://flaglane.com/download/greek-flag/greek-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32931).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''יפנית'''
	addDir(addonString_servicefeatherence(32911).encode('utf-8'),'Japanese',90,"http://flaglane.com/download/japanese-flag/japanese-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32911).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''סינית'''
	addDir(addonString_servicefeatherence(32907).encode('utf-8'),'Chinese',90,"http://flaglane.com/download/chinese-flag/chinese-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32907).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''סלובקית'''
	addDir(addonString_servicefeatherence(32917).encode('utf-8'),'Slovak',90,"http://flaglane.com/download/slovakian-flag/slovakian-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32917).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''ספרדית'''
	addDir(addonString_servicefeatherence(32908).encode('utf-8'),'Spanish',90,"http://flaglane.com/download/spanish-flag/spanish-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32908).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
		
	'''סרבית'''
	addDir(addonString_servicefeatherence(32915).encode('utf-8'),'Serbian',90,"http://www.flagsinformation.com/serbian-flag.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32915).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''פולנית'''
	addDir(addonString_servicefeatherence(32922).encode('utf-8'),'Polish',90,"http://flaglane.com/download/polish-flag/polish-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32922).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''פורטוגזית'''
	addDir(addonString_servicefeatherence(32918).encode('utf-8'),'Portuguese',90,"http://flaglane.com/download/portuguese-flag/portuguese-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32918).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''פינית'''
	addDir(addonString_servicefeatherence(32925).encode('utf-8'),'Finnish',90,"http://flaglane.com/download/finnish-flag/finnish-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32925).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))

	'''ערבית'''
	addDir(addonString_servicefeatherence(32926).encode('utf-8'),'Arabic',90,"http://flaglane.com/download/emirian-flag/emirian-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32926).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''צ'כית'''
	addDir(addonString_servicefeatherence(32934).encode('utf-8'),'Czech',90,"http://flaglane.com/download/czech-flag/czech-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32934).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''צרפתית'''
	addDir(addonString_servicefeatherence(32904).encode('utf-8'),'French',90,"http://flaglane.com/download/french-flag/french-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32904).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''קוריאנית'''
	addDir(addonString_servicefeatherence(32913).encode('utf-8'),'Korean',90,"http://flaglane.com/download/south-korean-flag/south-korean-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32913).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''קזחית'''
	addDir(addonString_servicefeatherence(32930).encode('utf-8'),'Kazakh',90,"http://flaglane.com/download/kazakh-flag/kazakh-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32930).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''קטלאנית'''
	addDir(addonString_servicefeatherence(32919).encode('utf-8'),'Catalan',90,"http://www.barcelonas.com/images/la-senyera.jpg",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32919).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''קריאולית האיטית'''
	addDir(addonString_servicefeatherence(32924).encode('utf-8'),'Haitian',90,"http://flaglane.com/download/haitian-flag/haitian-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32924).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''רומנית'''
	addDir(addonString_servicefeatherence(32914).encode('utf-8'),'Romanian',90,"http://flaglane.com/download/romanian-flag/romanian-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32914).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''רוסית'''
	addDir(addonString_servicefeatherence(32905).encode('utf-8'),'Russian',90,"http://flaglane.com/download/russian-flag/russian-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32905).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))

	'''שוודית'''
	addDir(addonString_servicefeatherence(32932).encode('utf-8'),'Swedish',90,"http://flaglane.com/download/swedish-flag/swedish-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32932).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))
	
	'''תאילנדית'''
	addDir(addonString_servicefeatherence(32910).encode('utf-8'),'Thai',90,"http://flaglane.com/download/thai-flag/thai-flag-medium.png",addonString(1).encode('utf-8') % (addonString_servicefeatherence(32910).encode('utf-8')),'1',50, getAddonFanart(200, custom=""))


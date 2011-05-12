import urllib,urllib2,re,os
import xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.diy')
__language__ = __settings__.getLocalizedString
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )


def getShows():
		addDir(__language__(30000), '/diy-10-grand-in-your-hand/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/05/28/tenGrand_lg_100.jpg')
		addDir(__language__(30001), '/diy-10-killer-kitchen-projects/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/08/22/spShow_10-Killer-Kitchen-Projects_s994x100.jpg')
		addDir(__language__(30002), '/diy-10-killer-weekend-projects/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/09/08/spShow_10-Killer-Weekend-Projects_s994x100.jpg')
		addDir(__language__(30003), '/diy-10-things-you-must-know2/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/06/04/spShow_10-things-you-must-know_s994x200.jpg')
		addDir(__language__(30004), '/diy-americas-most-desperate-landscape2/videos/index.html',1,'http://img.diynetwork.com/DIY/2011/02/16/spShow_AMDL_s994x200.jpg')
		addDir(__language__(30005), '/diy-b-original-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/27/B-Original-sm-100.jpg')
		addDir(__language__(30006), '/diy-bathtastic-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2011/01/06/spShow_BATHtastic_s994x200.jpg')
		addDir(__language__(30007), '/diy-backyard-blitz/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/02/23/spShow_Backyard-Blitz_s994x100.jpg')
		addDir(__language__(30008), '/diy-backyard-stadiums/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/09/16/spShow_Backyard-Stadiums_s994x100.jpg')
		addDir(__language__(30009), '/diy-barkitecture/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/27/Barkitecture-sm-100.jpg')
		addDir(__language__(30010), '/diy-bath-crashers/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/06/04/spShow_Bath-Crashers_s994x200.jpg')
		addDir(__language__(30011), '/diy-bathroom-renovations-episodes/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/24/BathroomRenovations-lg-110.jpg')
		addDir(__language__(30012), '/diy-carol-duvall-show-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/05/01/CarolDuvallShow-sm-100.jpg')
		addDir(__language__(30013), '/diy-carter-can-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/27/CarterCan-sm-100.jpg')
		addDir(__language__(30014), '/diy-cool-tools-episodes/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/11/02/spShow_Cool-Tools_s994x200.jpg')
		addDir(__language__(30015), '/diy-cool-tools-inventors-challenge/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/10/23/spShow_cool-tools-inventors_s994x200.jpg')
		addDir(__language__(30016), '/diy-cool-tools-hardware-show/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/10/23/spShow_cool-tools-hardware-show_s994x200.jpg')
		addDir(__language__(30017), '/diy-creative-juice-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/05/28/CreativeJuice-sm-100.jpg')
		addDir(__language__(30018), '/diy-diy-dominator/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/05/18/spShow_DIY-Dominator_s994x200.jpg')
		addDir(__language__(30019), '/diy-diy-to-the-rescue-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/24/DIYToTheRescue-lg-100.jpg')
		addDir(__language__(30020), '/diy-deconstruction-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/24/Deconstruction-lg-100.jpg')
		addDir(__language__(30021), '/diy-desperate-landscapes-episodes/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/24/DesperateLandscapes-lg-111.jpg')
		addDir(__language__(30022), '/diy-desperate-landscapes-top-10/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/02/08/spShow_Desperate-Landscapes-Top-10_s994x200.jpg')
		addDir(__language__(30023), '/diy-disaster-house/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/09/02/spShow_Disaster-House_s994x200.jpg')
		addDir(__language__(30024), '/diy-dream-house/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/29/DreamHouse-sm-100.jpg')
		addDir(__language__(30025), '/diy-dream-house-log-cabin/videos/index.html',1,'http://img.diynetwork.com/DIY/2011/01/05/spShow_dream-house-log-cabin_s994x100.jpg')
		addDir(__language__(30026), '/diy-family-renovation/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/05/26/spShow_Family-Renovation_s994x100.jpg')
		addDir(__language__(30027), '/diy-freeform-furniture/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/09/16/spShow_Freeform-Furniture_s994x100.jpg')
		addDir(__language__(30028), '/diy-fresh-from-the-orchard/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/10/21/sp100_fresh-from-the-orchard_s994x100.jpg')
		addDir(__language__(30029), '/diy-fresh-from-the-garden/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/05/05/FreshFromTheGarden-sm-110.jpg')
		addDir(__language__(30030), '/diy-garage-mahal-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/03/03/spShow_Garage-Mahal-Bill_s994x200.jpg')
		addDir(__language__(30031), '/diy-hammered/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/12/11/spShow_Hammered_s994x100.jpg')
		addDir(__language__(30032), '/diy-haulin-house/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/27/haulinHouse-sm-100.jpg')
		addDir(__language__(30033), '/diy-house-crashers/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/06/14/spShow_House-Crashers_s994x200.jpg')
		addDir(__language__(30034), '/diy-i-hate-my-kitchen/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/08/22/spShow_I-Hate-My-Kitchen_s994x200.jpg')
		addDir(__language__(30035), '/diy-indoors-out-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2011/02/02/spShow_Indoors-Out_s994x200.jpg')
		addDir(__language__(30036), '/diy2/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/24/KitchenImpossible-lg-100.jpg')
		addDir(__language__(30037), '/diy12/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/20/KitchenRenovations-lg_100.jpg')
		addDir(__language__(30038), '/diy-make-a-move-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/24/MakeAMove-sm-101.jpg')
		addDir(__language__(30039), '/diy-man-caves-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/16/ManCaves_lg-105.jpg')
		addDir(__language__(30040), '/diy-mega-dens/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/11/09/spShow_Mega-Dens_s994x200.jpg')
		addDir(__language__(30041), '/diy-money-hunters/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/04/13/spShow_Money-Hunters_s994x200.jpg')
		addDir(__language__(30042), '/diy-project-xtreme-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/27/ProjectXtreme-lg-100.jpg')
		addDir(__language__(30043), '/diy-rehab-addict/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/10/29/spShow_Rehab-Addict_s994x200.jpg')
		addDir(__language__(30044), '/diy-renovation-realities-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/24/RenovationRealities-lg-100.jpg')
		addDir(__language__(30045), '/diy-rescue-renovation2/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/05/10/spShow_Rescue-Renovation_s994x200.jpg')
		addDir(__language__(30046), '/diy-rock-solid-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/20/RockSolid_lg-100.jpg')
		addDir(__language__(30047), '/diy-run-my-renovation2/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/07/23/spFeature_Run-My-Renovation_s994x200.jpg')
		addDir(__language__(30048), '/diy-studfinder/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/10/20/sp100_studfinder_s994x100.jpg')
		addDir(__language__(30049), '/diy-sweat-equity-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/09/19/spShow_Sweat-Equity_s994x200.jpg')
		addDir(__language__(30050), '/diy14/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/24/KingOfDirt-lg-110.jpg')
		addDir(__language__(30051), '/diy-the-vanilla-ice-project/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/09/20/spShow_The-Vanilla-Ice-Project_SPack_s994x200.jpg')
		addDir(__language__(30052), '/diy-this-new-house/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/05/10/spShow_This-New-House_s994x200.jpg')
		addDir(__language__(30053), '/diy-turf-war/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/02/08/spShow_Turf-War_s994x200.jpg')
		addDir(__language__(30054), '/diy-under-construction-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/27/UnderConstruction-sm-102.jpg')
		addDir(__language__(30055), '/diy-wasted-spaces/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/27/WastedSpaces-sm-100.jpg')
		addDir(__language__(30056), '/diy-yard-crashers-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/17/YardCrashers_lg-101.jpg')
		addDir(__language__(30057), '/diy-yard-crashers-top-10/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/02/08/spShow_Yard-Crashers-Top-10_s994x200.jpg')
	

def index(url):
		url='http://www.diynetwork.com'+url
		req = urllib2.Request(url)
		req.addheaders = [('Referer', 'http://www.diynetwork.com'),
				('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link)
		if soup.find('div', attrs={'id' : "more-videos-from-show"}):
				shows = soup.find('div', attrs={'id' : "more-videos-from-show"})('h4')
				for show in shows:
						name = show.string
						url = show.next.next.next('a')[0]['href']
						addDir(name,url,1,'')
		showID=re.compile("var snap = new SNI.DIY.Player.FullSize\(\\'.+?\\',\\'(.+?)\\', \\'\\'\);").findall(link)
		if len(showID)<1:
				showID=re.compile("var snap = new SNI.DIY.Player.FullSize\(\'.+?','(.+?)', '.+?'\);").findall(link)
		print'--------> '+showID[0]
		url='http://www.hgtv.com/hgtv/channel/xml/0,,'+showID[0]+',00.xml'
		req = urllib2.Request(url)
		req.addheaders = [('Referer', 'http://www.diynetwork.com'),
				('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link)
		videos = soup('video')
		for video in videos:
				name = video('clipname')[0].string
				length = video('length')[0].string
				thumb = video('thumbnailurl')[0].string
				description = video('abstract')[0].string
				link = video('videourl')[0].string
				playpath = link.replace('http://wms.scrippsnetworks.com','').replace('.wmv','')
				url = 'rtmp://flash.scrippsnetworks.com:1935/ondemand?ovpfv=1.1 swfUrl="http://common.scrippsnetworks.com/common/snap/snap-3.0.3.swf" playpath='+playpath
				addLink(name,url,description,length,thumb)


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


def addLink(name,url,description,length,iconimage):
		ok=True
		liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
		liz.setInfo( type="Video", infoLabels={ "Title": name , "Plot":description, "Duration":length } )
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
		return ok


def addDir(name,url,mode,iconimage):
		u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
		ok=True
		liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
		liz.setInfo( type="Video", infoLabels={ "Title": name } )
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
		return ok
		
			
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

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None:
		print ""
		getShows()
	
elif mode==1:
		print ""+url
		index(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))

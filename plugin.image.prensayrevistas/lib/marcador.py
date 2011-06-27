# -*- coding: utf-8 -*-
import os, sys, urllib
import xbmc, xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.image.prensayrevistas')
__profile__  = __settings__.getAddonInfo('profile')

FAVORITE_PATH = xbmc.translatePath(os.path.join(__profile__,'favorites'))

if not os.path.exists(FAVORITE_PATH): os.makedirs(FAVORITE_PATH)


def read(file):

	file_path = os.path.join(FAVORITE_PATH,file)
	favorite = open(file_path)
	line = favorite.readlines()
	
	try:
		name = urllib.unquote_plus(line[0].strip())
	except:
		name = line[0].strip()

	try:
		url = urllib.unquote_plus(line[1].strip())
	except:
		url = line[1].strip()

	mode = int(line[2])

	try:
		thumb = urllib.unquote_plus(line[3].strip())
	except:
		thumb = line[3].strip()

	favorite.close()
	return name,url,mode,thumb

class save:
	def __init__(self):
		name = sys.argv[2]
		url = sys.argv[3]
		mode = sys.argv[4]
		thumb = sys.argv[5]
		try:
			os.mkdir(FAVORITE_PATH)
		except:
			pass

		files = os.listdir(FAVORITE_PATH)
		if len(files)>0:
			for file in files:
				count = 1
				try:
					file_num = int( file[0:-4] )+1
					if file_num > count:
						count = file_num
				except:
					pass

		else:
			count = 1

		content = ""
		content = content + urllib.quote_plus(name)+'\n'
		content = content + urllib.quote_plus(url)+'\n'
		content = content + str(mode)+'\n'
		content = content + urllib.quote_plus(thumb)+'\n'    
		savename = '%08d.txt' % count

		file_path = os.path.join(FAVORITE_PATH,savename)
		favorite = open(file_path,"w")
		favorite.write(content)
		favorite.flush();
		favorite.close()

class erase:
	def __init__(self):
		name = sys.argv[2]
		file_path = os.path.join(FAVORITE_PATH,name)
		os.remove(urllib.unquote_plus(file_path))
		xbmc.executebuiltin("Container.Refresh")
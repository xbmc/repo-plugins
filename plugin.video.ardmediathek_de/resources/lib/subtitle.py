#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import xbmc
import re
import resources.lib.utils as utils
import xbmcaddon
import HTMLParser
import xbmcvfs
addonID = 'plugin.video.ardmediathek_de'
addon = xbmcaddon.Addon(id=addonID)
subFile = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')+'/sub.srt').decode('utf-8')

baseUrl = "http://www.ardmediathek.de"
coloredSubtitles = addon.getSetting("coloredSubtitles") == "true"
	
def setSubtitle(uri,offset=0):
	if offset != 0:
		print offset
	print baseUrl+uri
	if uri.startswith('/subtitle'):
		_newSubtitle(baseUrl+uri)
	else:
		_oldSubtitle(baseUrl+uri)

def _newSubtitle(url):
	#if os.path.exists(subFile):
	#	os.remove(subFile)
	if xbmcvfs.exists(subFile):
		xbmcvfs.delete(subFile)
	try:
		content = utils.getUrl(url)
	except:
		content = ""
	if content:
		dict = _stylesSetup(re.compile('<tt:styling>(.+?)</tt:styling>', re.DOTALL).findall(content)[0])
		div = re.compile('<tt:div.+?>(.+?)</tt:div>', re.DOTALL).findall(content)[0]
		p = re.compile('<tt:p(.+?)</tt:p>', re.DOTALL).findall(div)
		i = 1
		buffer = ''
		for part in p:
			if '<tt:span' in part:
				part = part.replace('begin="1','begin="0').replace('end="1','end="0').replace('\n','').replace('<tt:br/>','\n')
				begin = re.compile('begin="(.+?)"').findall(part)[0]
				begin = begin.replace(".",",")[:-1]
				end = re.compile('end="(.+?)"').findall(part)[0]
				end = end.replace(".",",")[:-1]
				s = part.split('>')[0]
				part = part.replace(s+'>','')
				if 'style=' in s:
					style = re.compile('style="(.+?)"').findall(s)[0]
					if dict[style]:
						part = '<font color="'+dict[style]+'">'+part+'</font>'
				match = re.compile('<(.+?)>').findall(part)
				for entry in match:
					if entry.startswith('tt:span'):
						if 'style' in entry:
							style = re.compile('style="(.+?)"').findall(entry)[0]
							part = part.replace('<'+entry+'>','<font color="'+dict[style]+'">')
						else:
							part = part.replace('<'+entry+'>','')
					elif entry.startswith('tt:/span'):
						part = part.replace('</tt:span>','</font>')
					else:
						part = part.replace('<'+entry+'>','')
				

				buffer += str(i) + '\n'
				buffer += begin+" --> "+end+"\n"
				buffer += part + '\n\n'
				i+=1
		
		f = xbmcvfs.File(subFile, 'w')
		f.write(buffer)
		f.close()
		xbmc.sleep(1000)
		xbmc.Player().setSubtitles(subFile)

def _oldSubtitle(url):
	if os.path.exists(subFile):
		os.remove(subFile)
	try:
		content = utils.getUrl(url)
	except:
		content = ""
	if content:
		dict = _stylesSetup(re.compile('<styling>(.+?)</styling>', re.DOTALL).findall(content)[0])
		matchLine = re.compile('<p id=".+?" begin="1(.+?)" end="1(.+?)".+?style="(.+?)">(.+?)</p>', re.DOTALL).findall(content)
		#fh = open(subFile, 'a')
		f = xbmcvfs.File(subFile, 'w')
		count = 1
		for begin, end, style, line in matchLine:
			begin = "0"+begin.replace(".",",")[:-1]
			end = "0"+end.replace(".",",")[:-1]
			text = ''
			line = line.replace('\n','').strip()
			line = line.replace("<br />","\n")
			
			if dict[style]:
				line = '<font color="'+dict[style]+'">'+line+'</font>'

			s = line.split('<')
			for entry in s:
				if entry.startswith('span'):
					if 'tts:color' in entry.split('>')[0]:
						color = re.compile('tts:color="(.+?)"', re.DOTALL).findall(entry.split('>')[0])[0]
						line = line.replace('<'+entry.split('>')[0]+'>','<font color="'+color+'">')
			line = line.replace('</span>','</font>')

			while '  ' in line:
				line = line.replace('  ',' ')
			line = line.replace(' \n','\n').replace(' </font>\n','</font>\n')
			#fh.write(str(count)+"\n"+begin+" --> "+end+"\n"+_cleanTitle(line)+"\n\n")
			f.write(str(count)+"\n"+begin+" --> "+end+"\n"+_cleanTitle(line)+"\n\n")
			
			count+=1
		f.close()
		xbmc.sleep(1000)
		xbmc.Player().setSubtitles(subFile)
"""	
def _oldSubtitle(url):
	if os.path.exists(subFile):
		os.remove(subFile)
	try:
		content = utils.getUrl(url)
	except:
		content = ""
	if content:
		dict = _stylesSetup(re.compile('<styling>(.+?)</styling>', re.DOTALL).findall(content)[0])
		matchLine = re.compile('<p id=".+?" begin="1(.+?)" end="1(.+?)".+?style="(.+?)">(.+?)</p>', re.DOTALL).findall(content)
		fh = open(subFile, 'a')
		count = 1
		for begin, end, style, line in matchLine:
			begin = "0"+begin.replace(".",",")[:-1]
			end = "0"+end.replace(".",",")[:-1]
			match = re.compile('<span(.+?)>', re.DOTALL).findall(line)
			for span in match:
				line = line.replace("<span"+span+">","")
			line = line.replace("<br />","\n").replace("</span>","").strip()
			if dict[style]:
				line = '<font color="'+dict[style]+'">'+line+'</font>'
			fh.write(str(count)+"\n"+begin+" --> "+end+"\n"+_cleanTitle(line)+"\n\n")
			count+=1
		fh.close()
		xbmc.sleep(1000)
		xbmc.Player().setSubtitles(subFile)
"""	
def _stylesSetup(styles):
	dict = {}
	styles = styles.replace('tt:','').replace('xml:','')
	match_styles = re.compile('<style(.+?)>', re.DOTALL).findall(styles)
	for style in match_styles:
		id = re.compile('id="(.+?)"', re.DOTALL).findall(style)[0]
		if 'color=' in style and coloredSubtitles:
			color = re.compile('color="(.+?)"', re.DOTALL).findall(style)[0]
		else:
			color = False
		dict[id] = color
	return dict


def _cleanTitle(title,html=True):
	if html:
		title = HTMLParser.HTMLParser().unescape(title)
		return title.encode("utf-8")
	else:
		title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#034;", "\"").replace("&#039;", "'").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
		title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö").replace("&eacute;", "é").replace("&egrave;", "è")
		title = title.replace("&#x00c4;","Ä").replace("&#x00e4;","ä").replace("&#x00d6;","Ö").replace("&#x00f6;","ö").replace("&#x00dc;","Ü").replace("&#x00fc;","ü").replace("&#x00df;","ß")
		title = title.replace("&apos;","'").strip()
		return title
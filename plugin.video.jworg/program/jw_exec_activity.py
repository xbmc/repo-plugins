"""
ACTIVITIES RELATED FUNCTION
"""
import jw_config
import jw_common

import xbmcplugin
import xbmcgui
import xbmc

import re
import urllib

# List of available news
def showActivityIndex():

	language    = jw_config.language

	url 		= jw_common.getUrl(language)
	url 		= url + jw_config.const[language]["activity_index"]

	html 		= jw_common.loadUrl(url)

	# see_all[n][0] = section index relative url
	# see_all[n][1] = section title
	# see_all[n][2] = "See all" localized
	regexp_see_all = '<p class="seeAll"><a href="([^"]+)" title="([^"]+)">(.*)</a></p>'
	see_all = re.findall(regexp_see_all, html)

	# highlight[n][0] = lastest news relative link
	# highlight[n][2] = option title attribute
	# highlight[n][1] = lastest news title
	regexp_highlight = '<h3><a href="([^"]+)"( title="[^"]+")*>(.*)</a></h3>'
	highlight = re.findall (regexp_highlight, html)


	# iages[n][0] = full url of thumb
	regexp_images = "data-img-size-md='([^']+)'"
	images = re.findall (regexp_images, html)

	# separated highlight

	count = 0
	# Show  lastest news from this section, like on website
	title = jw_common.cleanUpText( highlight[count][2] ) 
	title = jw_common.removeHtml(title)
	listItem = xbmcgui.ListItem( 
		label  			= "[COLOR=FF00B7EB]" + title + "[/COLOR]",
		thumbnailImage	= images[count],
	)	
	params = {
		"content_type"  : "executable", 
		"mode" 			: "open_activity_article", 
		"url"			: highlight[count][0]
	} 
	url = jw_config.plugin_name + '?' + urllib.urlencode(params)
	xbmcplugin.addDirectoryItem(
		handle		= jw_config.plugin_pid, 
		url			= url, 
		listitem	= listItem, 
		isFolder	= True 
	) 

	count = 1
	for section in see_all :

		title = jw_common.cleanUpText( section[1] + " (" + section[2] + ") ") 
		listItem = xbmcgui.ListItem( 
			label  			= "[B]" + title + "[/B]",
			# no thumbnail available from website, will be used standard folder icon
		)	
		params = {
			"content_type"  : "executable", 
			"mode" 			: "open_activity_section", 
			"url"			: section[0]
		} 
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)
		xbmcplugin.addDirectoryItem(
			handle		= jw_config.plugin_pid, 
			url			= url, 
			listitem	= listItem, 
			isFolder	= True 
		) 

		# Show lastest news from this section, like on website
		title = jw_common.cleanUpText( "--> " + highlight[count][2] ) 
		title = jw_common.removeHtml(title)
		listItem = xbmcgui.ListItem( 
			label  			= "[COLOR=FF00B7EB]" + title + "[/COLOR]",
			thumbnailImage	= images[count],
		)	
		params = {
			"content_type"  : "executable", 
			"mode" 			: "open_activity_article", 
			"url"			: highlight[count][0]
		} 
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)
		xbmcplugin.addDirectoryItem(
			handle		= jw_config.plugin_pid, 
			url			= url, 
			listitem	= listItem, 
			isFolder	= True 
		) 

		count = count +1


	xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)


def showActivitySection(url):

	url 	= "http://www.jw.org" + url
	html 	= jw_common.loadUrl(url)

	# titles[n][0] = lastest news relative link
	# titles[n][2] = optional title attribute
	# titles[n][2] = lastest news title
	regexp_titles = '<h3><a href="([^"]+)"( title="[^"]+")*>(.*)</a></h3>'
	titles = re.findall (regexp_titles, html)

	# iages[n][0] = full url of thumb
	regexp_images = "data-img-size-sm='([^']+)'"
	images = re.findall (regexp_images, html)

	count = 0
	# Number of images is relative to number of articles, so we
	# automatically exclude texts and links from sidebar videos
	for i in images :

		# Show lastest news from this section, like on website
		title = jw_common.cleanUpText( titles[count][2] ) 
		title = jw_common.removeHtml( title )
		listItem = xbmcgui.ListItem( 
			label  			= title,
			thumbnailImage	= images[count],
		)	
		params = {
			"content_type"  : "executable", 
			"mode" 			: "open_activity_article", 
			"url"			: titles[count][0]
		} 
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)
		xbmcplugin.addDirectoryItem(
			handle		= jw_config.plugin_pid, 
			url			= url, 
			listitem	= listItem, 
			isFolder	= True 
		) 

		count = count +1


	xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)


def showArticle(url):

	url 	= "http://www.jw.org" + url
	html 	= jw_common.loadUrl(url)

	activity = Activity()
	activity.customInit(html);
	activity.doModal();
	del activity
	xbmc.executebuiltin('Action("back")')




# Window showing activity related news text

#get actioncodes from https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/Key.h
ACTION_MOVE_UP 		= 3
ACTION_MOVE_DOWN 	= 4
ACTION_PAGE_UP 		= 5
ACTION_PAGE_DOWN 	= 6

class Activity(xbmcgui.WindowDialog):

	def __init__(self):
		if jw_config.emulating: xbmcgui.Window.__init__(self)

	def customInit(self, text):

		border = 50; # px relative to 1280/720 fixed grid resolution

		# width is always 1280, height is always 720.
		bg_image = jw_config.dir_media + "blank.png"
		self.ctrlBackgound = xbmcgui.ControlImage(
			0,0, 
			1280, 720, 
			bg_image
		)
		
		self.ctrlBackgound2 = xbmcgui.ControlImage(
			0,0, 
			1280, 90, 
			bg_image
		)
		self.ctrlTitle= xbmcgui.ControlTextBox(
			border, 0, 
			1280 - border *2, 90, 
			'font35_title', "0xFF0000FF"
		)
		self.ctrlText= xbmcgui.ControlTextBox(
            border, 20, 
            1280 - border *2, 10000, # Really long articles already found !
            'font30', "0xFF000000"
        )
		
		self.addControl (self.ctrlBackgound)
		self.addControl (self.ctrlText)
		self.addControl (self.ctrlBackgound2)
		self.addControl (self.ctrlTitle)
		
		self.ctrlTitle.setText( self.getTitle(text) )
		self.ctrlText.setText( self.getText(text) )
		

	def onAction(self, action):
		(x,y) =  self.ctrlText.getPosition()

		if action == ACTION_MOVE_UP:
			if y > 0:
				return
			y = y + 50;
			self.ctrlText.setPosition(x,y)
			return

		if action == ACTION_MOVE_DOWN:
			(x,y) =  self.ctrlText.getPosition()
			y = y - 50;
			self.ctrlText.setPosition(x,y)
			return

		if action == ACTION_PAGE_UP:
			if y > 0:
				return
			y = y + 500;
			self.ctrlText.setPosition(x,y)
			return

		if action == ACTION_PAGE_DOWN:
			(x,y) =  self.ctrlText.getPosition()
			y = y - 500;
			self.ctrlText.setPosition(x,y)
			return

		self.close()

	# Grep news title
	def getTitle(self, text):
		regexp_header = "<h1([^>]*)>(.*)</h1>"
		headers = re.findall(regexp_header, text)
		return jw_common.removeHtml(headers[0][1])
		

	def getText(self, text):

		text =  re.sub("<strong>", "[B]", text)
		text =  re.sub("</strong>", "[/B]", text)
		text =  re.sub("<a[^>]+>", "", text)

		regexp_pars = '<p id="p[0-9]+" class="p[0-9]+">(.+)</p>|<h3 class="inline">(.+)</h3>'
		pars = re.findall(regexp_pars, text)


		out = ""
		for par in pars:
			text = par[0] + "[B]"+par[1]+"[/B]"
			out = out + "\n\n" + jw_common.removeHtml(text)
		out = out + "\n\n[COLOR=FF0000FF][I]" + jw_common.t(30038).encode("utf8") + "[/I][/COLOR]"

		return out
		
# -*- coding: UTF-8 -*-
"""
SIGN LANGUAGE VIDEO RELATED FUNCTIONS
"""

import xbmcplugin
import xbmcgui
import xbmc

from BeautifulSoup import BeautifulSoup 
import urllib
import re

import jw_common
import jw_config

# show available video categories
def showVideoFilter():

	language 	= jw_config.language
	url 		= jw_config.main_url  + jw_config.const[language]["sign_index"] 

	html 	= jw_common.loadUrl(url)
	soup 	= BeautifulSoup(html)

	boxes 	= soup.findAll('div',{"class":"box"})

	for box in boxes :
		box_content = box.findAll('div',{'class':'boxcontent'})
		for content in box_content :

			content_divs = content.findAll('div')
			img_src 		= content_divs[0].findAll('img')[0].get("src")
			category_link 	= content_divs[1].find('a').get('href')
			category_name	= content_divs[1].find('a').contents[0].encode("utf-8")
			category_name	= jw_common.cleanUpText(category_name)

			listItem = xbmcgui.ListItem(
				label 			= category_name, 
				thumbnailImage 	= img_src
			)

			params = { 
				"content_type" 	: "video", 
				"mode" 			: "open_sign_video_category", 
				"url"			: category_link,
				"thumb" 		: img_src
			} 

			url = jw_config.plugin_name + '?' + urllib.urlencode(params)
			xbmcplugin.addDirectoryItem(
				handle	 = jw_config.plugin_pid, 
				url 	 = url, 
				listitem = listItem, 
				isFolder = True 
			)  

	xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)


# Used to show list of publication issue
# if were found zero or more issue per pages, it's launched showVideoCategorySpecificIssue
# if zero it's a simplet publication without publication title inside the table
def showVideoCategory(category_url, thumb) :

	html 	= jw_common.loadUrl(category_url)
	soup 	= BeautifulSoup(html)

	# search "select year" box [italian watchtower sing language, for example]
	sel_year_label = soup.findAll('label', {'for' : 'selYear' })

	if len(sel_year_label) > 0 :

		year_selector = soup.findAll('select', {'id' : 'selYear'})
		selected_year = year_selector[0].findAll('option', {'selected':'selected'})

		listItem = xbmcgui.ListItem(
			label 			= "[COLOR blue][B]" +
								sel_year_label[0].contents[0].encode("utf-8") + " (" +
							  	selected_year[0].contents[0].encode("utf-8") + ") " +
								"[/B][/COLOR]",

			thumbnailImage  = thumb,
		)	
		params = { 
			"content_type" 		: "video", 
			"mode" 				: "open_sign_video_sel_year", 
			"url"				: category_url,
			'thumb'				: thumb,
		}
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)
		xbmcplugin.addDirectoryItem(
			handle	 = jw_config.plugin_pid, 
			url 	 = url, 
			listitem = listItem, 
			isFolder = True 
		)  

	# search "select book" box [italian bible sing language, for example]
	sel_book_labels = soup.findAll('label', {'for' : 'selBook' })
	if len(sel_book_labels) > 0 :

		book_selector = soup.findAll('select', {'id' : 'selBook'})
		selected_book = book_selector[0].findAll('option', {'selected':'selected'})

		listItem = xbmcgui.ListItem(
			label 			= "[COLOR blue][B]" +
								sel_book_labels[0].contents[0].encode("utf-8") + " (" +
							  	selected_book[0].contents[0].encode("utf-8") + ") " +
								"[/B][/COLOR]",

			thumbnailImage  = thumb,
		)	
		params = { 
			"content_type" 		: "video", 
			"mode" 				: "open_sign_video_sel_book", 
			"url"				: category_url,
			'thumb'				: thumb,
		}
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)
		xbmcplugin.addDirectoryItem(
			handle	 = jw_config.plugin_pid, 
			url 	 = url, 
			listitem = listItem, 
			isFolder = True 
		)  

	# Start looking for publication details
	pub_titles = soup.findAll('tr', {'class' : re.compile(r'\bpubTitle\b')})

	pub_titles_found = len(pub_titles)
	
	if  pub_titles_found > 1 :

		pub_title_index = -1
		for title in pub_titles :

			issue_title_cell = title.findAll('th')[0]
			
			issue_title = issue_title_cell.find('em').contents[0].encode("utf-8")
			issue_title = issue_title + issue_title_cell.contents[1].encode("utf-8")
			issue_title = jw_common.cleanUpText(issue_title)

			pub_title_index = pub_title_index + 1

			listItem = xbmcgui.ListItem(
				label 			= issue_title, 
				thumbnailImage 	= thumb
			)

			params = { 
				"content_type" 		: "video", 
				"mode" 				: "open_sign_video_category_with_specific_issue", 
				"url"				: category_url,
				"thumb" 			: thumb,
				"pub_title_index"	: pub_title_index
			} 

			url = jw_config.plugin_name + '?' + urllib.urlencode(params)
			xbmcplugin.addDirectoryItem(
				handle	 = jw_config.plugin_pid, 
				url 	 = url, 
				listitem = listItem, 
				isFolder = True 
			)  

		xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)
		return

	elif  pub_titles_found == 1 :
		showVideoCategorySpecificIssue(category_url, thumb, 0) 
	else :
		showVideoCategorySpecificIssue(category_url, thumb, -1) 
		

# This specific version is for watchtower page, which has more than one pub per page
# The previous folder has already showed the list of issue of this category of publication
# Here I got the index ( zero based). So I'll browser entire table, and discard
# all of chapters not related to the specified issue
def showVideoCategorySpecificIssue(category_url, thumb, pub_title_index) :

	pub_title_index = int(pub_title_index) #because it's a string actually !
	html 			= jw_common.loadUrl(category_url)
	soup 			= BeautifulSoup(html)

	rows = soup.findAll('tr')

	pub_index_found = -1
	first_chapter_row = None
	last_chapter_row = None
	row_index = -1

	for row in rows :
		row_index = row_index + 1
		row_class = None
		try:
			row_class = row["class"]
		except:
			pass

		if row_class is not None and 'pubTitle' in row_class :
			pub_index_found = pub_index_found + 1	
			continue

		if row_class is None and pub_index_found == pub_title_index:
			first_cell = row.findAll("td")[0]
			first_cell_class = first_cell["class"]

			# This is needed because watchtower, for example, has one image for a whole issue
			# so after first row of the issue, the other rows have no images
			if first_cell_class == "calign" :
				cell = row.findAll("td")[2]
				thumb = first_cell.findAll('img')[0].get('src')
			else :
				cell = row.findAll("td")[1]

			# Needed for publications without videos !
			# Example: http://www.jw.org/apps/I_QrYQFVTrCsVrGlBBX?selLang=ISL&selPub=938
			try :
				chapter_title = cell.contents[0].encode("utf-8")
				chapter_title = jw_common.cleanUpText(chapter_title)
			except :
				continue

			res_found = searchResolution(category_url, row_index)

			if res_found == False :
				chapter_title 	= "[COLOR=blue][B]" + chapter_title + "[/B][/COLOR]"
				is_folder 		= True
			else :
				chapter_title 	= chapter_title + " [" + res_found + "]"
				is_folder 		= False

			listItem = xbmcgui.ListItem(
				label 			= chapter_title, 
				thumbnailImage 	= thumb
			)

			params = { 
				"content_type" 		: "video", 
				"mode" 				: "open_sign_video_category_specific_row", 
				"url"				: category_url,
				"thumb" 			: thumb,
				"row_index"			: row_index
			} 

			url = jw_config.plugin_name + '?' + urllib.urlencode(params)
			
			xbmcplugin.addDirectoryItem(
				handle		= jw_config.plugin_pid, 
				url			= url, 
				listitem	= listItem, 
				isFolder	= is_folder
			) 
		
	xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)	


# very similar to showVideoCategorySpecificRow
# return a boolean false or found resolution
def searchResolution(category_url, row_index) :

	# looking for choosen resolution or first available resolution unde it
	max_resolution	= xbmcplugin.getSetting(jw_config.plugin_pid, "max_resolution")
	if max_resolution == 0 :
		return False

	row_index 	= int(row_index) #because it's a string actually !
	html 		= jw_common.loadUrl(category_url)
	soup 		= BeautifulSoup(html)

	row = soup.findAll('tr')[row_index]

	row_cells = row.findAll("td")

	start_cell = 2 # zero-base indexing
	first_cell_class = row.findAll("td")[0]["class"]
	if first_cell_class == "calign":
		start_cell = 3

	video_dict = {}

	cell_index = -1
	for cell in row_cells :
		cell_index = cell_index + 1
		if cell_index == (start_cell -1): 
			article_title = jw_common.cleanUpText(cell.contents[0].encode("utf-8"))

		if cell_index >= start_cell :

			# This is needed for resolution cell empty
			if cell.find("a") is None :
				continue

			video_src 		= cell.find("a").get("href")
			video_quality 	= cell.find("a").contents[0].encode("utf-8")

			video_dict [ video_quality ] = video_src

	# Look for choosen resolution
	max_resolution_string = max_resolution + "p"

  	keys = sorted(list(video_dict.keys()), reverse=True)
  	for key in keys :
  		if (key <= max_resolution_string )  :
			return key

	# If am here, I surely have NOT the default resolution found
	return False


# Get the list of playable item (a list of video resolution and title)
# from a specific row of the page
def showVideoCategorySpecificRow(category_url, thumb, row_index) :

	row_index 	= int(row_index) #because it's a string actually !
	html 		= jw_common.loadUrl(category_url)
	soup 		= BeautifulSoup(html)

	row = soup.findAll('tr')[row_index]

	row_cells = row.findAll("td")

	start_cell = 2 # zero-base indexing
	first_cell_class = row.findAll("td")[0]["class"]
	if first_cell_class == "calign":
		start_cell = 3

	video_dict = {}

	cell_index = -1
	for cell in row_cells :
		cell_index = cell_index + 1
		if cell_index == (start_cell -1): 
			article_title = jw_common.cleanUpText(cell.contents[0].encode("utf-8"))

		if cell_index >= start_cell :

			# This is needed for resolution cell empty
			if cell.find("a") is None :
				continue

			video_src 		= cell.find("a").get("href")
			video_quality 	= cell.find("a").contents[0].encode("utf-8")

			video_dict [ video_quality ] = video_src

			listItem = xbmcgui.ListItem(
				label 			= "[" + video_quality + "] - " + article_title,
				thumbnailImage	= thumb
			)

			listItem.setInfo(
				type 		= 'Video', 
				infoLabels 	= {'Title': article_title}
			)
			listItem.setProperty("IsPlayable","true")

			xbmcplugin.addDirectoryItem(
				handle		= jw_config.plugin_pid, 
				url			= video_src, 
				listitem	= listItem, 
				isFolder	= False 
			) 

	# looking for choosen resolution or first available resolution unde it
	max_resolution	= xbmcplugin.getSetting(jw_config.plugin_pid, "max_resolution")

	if max_resolution > 0 :

		max_resolution_string = max_resolution + "p"

	  	keys = sorted(list(video_dict.keys()), reverse=True)
	  	for key in keys :
	  		if (key <= max_resolution_string )  :
	  			listItem = xbmcgui.ListItem(
					label 			=  article_title
				)
				listItem.setInfo(
					type 		= 'Video', 
					infoLabels 	= {'Title': article_title}
				)

				url_to_play = video_dict[key]

				xbmc.Player().play(item=url_to_play, listitem=listItem)

				return


	# this will be executed only if no available res found
	# this could happen if not preference setted, or if 
	# for example, selected 240p and only 360p availabe.
	xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)		


# Year selector
# This happens only for watchtower study edition.
def selYear(category_url, thumb) :

	html 	= jw_common.loadUrl(category_url)
	soup 	= BeautifulSoup(html)

	year_selector = soup.findAll('select', {'id' : 'selYear'})

	if len(year_selector)==1 :

		options = year_selector[0].findAll('option')

		for option in options :

			year = option.contents[0].encode("utf-8")

			listItem = xbmcgui.ListItem(
				label 			= year, 
				thumbnailImage	= thumb,
			)

			category_url = category_url + "&selYear=" + year
			params = { 
				"content_type" 		: "video", 
				"mode" 				: "open_sign_video_category", 
				"url"				: category_url,
				"thumb" 			: thumb,
			} 

			url = jw_config.plugin_name + '?' + urllib.urlencode(params)
			xbmcplugin.addDirectoryItem(
				handle	 = jw_config.plugin_pid, 
				url 	 = url, 
				listitem = listItem, 
				isFolder = True 
			)  

	xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)	


# Book selector
# This happens only for the bible 
def selBook(category_url, thumb) :

	html 	= jw_common.loadUrl(category_url)
	soup 	= BeautifulSoup(html)

	book_selector = soup.findAll('select', {'id' : 'selBook'})

	if len(book_selector)==1 :

		options = book_selector[0].findAll('option')

		for option in options :

			book = option.contents[0].encode("utf-8")
			book_num = option.get("value").encode("utf-8") 

			listItem = xbmcgui.ListItem(
				label 			= book, 
				thumbnailImage	= thumb,
			)

			category_url_with_book = category_url + "&selBook=" + book_num

			params = { 
				"content_type" 		: "video", 
				"mode" 				: "open_sign_video_category", 
				"url"				: category_url_with_book,
				"thumb" 			: thumb,
			} 

			url = jw_config.plugin_name + '?' + urllib.urlencode(params)
			xbmcplugin.addDirectoryItem(
				handle	 = jw_config.plugin_pid, 
				url 	 = url, 
				listitem = listItem, 
				isFolder = True 
			)  

	xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)	
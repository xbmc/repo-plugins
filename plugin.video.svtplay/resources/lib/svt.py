# -*- coding: utf-8 -*-
import CommonFunctions
import re
import helper

common = CommonFunctions
common.plugin = "SVT Play 3::svt"

def getChannels(url):
  html = helper.getPage(url)

  container = common.parseDOM(html, "ul", attrs = { "data-player":"player" })[0]

  lis = common.parseDOM(container, "li")

  channels = []

  for li in lis:
    chname = common.parseDOM(li, "a", ret = "title")[0]
    thumbnail = common.parseDOM(li, "a", ret = "data-thumbnail")[0]
    url = common.parseDOM(li, "a", ret = "href")[0]
    prname = common.parseDOM(li, "span", attrs = { "class":"[^\"']*playChannelMenuTitle[^\"']*"})[0]
    chname = re.sub("\S*\|.*","| ",chname)
    title = chname + prname
    title = common.replaceHTMLCodes(title)
    if not thumbnail.startswith("http://"):
      thumbnail = "http://www.svtplay.se" + thumbnail
    common.log("thumbnail:"+thumbnail)
    channels.append({"title":title,"url":url,"thumbnail":thumbnail})

  return channels

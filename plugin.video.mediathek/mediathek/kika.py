# -*- coding: utf-8 -*-
#-------------LicenseHeader--------------
# plugin.video.Mediathek - Gives access to most video-platforms from German public service broadcasters
# Copyright (C) 2010  Raptor 2101 [raptor2101@gmx.de]
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>. 
import re, time;
from mediathek import *

class KIKA(Mediathek):
  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;
    self.rootLink = "http://www.kika.de";
    self.menuTree = (
        TreeNode("0","Videos",self.rootLink+"/videos/index.html",True),
        TreeNode("1","Sendungen von A-Z","",False,
          (
            TreeNode("1.0","A",self.rootLink+"/sendungen/sendungenabisz100_page-A_zc-05fb1331.html",True),
            TreeNode("1.1","B",self.rootLink+"/sendungen/sendungenabisz100_page-B_zc-1775e6d8.html",True),
            TreeNode("1.2","C",self.rootLink+"/sendungen/sendungenabisz100_page-C_zc-6248eba0.html",True),
            TreeNode("1.3","D",self.rootLink+"/sendungen/sendungenabisz100_page-D_zc-e090a8fb.html",True),
            TreeNode("1.4","E",self.rootLink+"/sendungen/sendungenabisz100_page-E_zc-ec2376ed.html",True),
            TreeNode("1.5","F",self.rootLink+"/sendungen/sendungenabisz100_page-F_zc-f76734a0.html",True),
            TreeNode("1.6","G",self.rootLink+"/sendungen/sendungenabisz100_page-G_zc-34bda7c3.html",True),
            TreeNode("1.7","H",self.rootLink+"/sendungen/sendungenabisz100_page-H_zc-7e25e70a.html",True),
            TreeNode("1.8","I",self.rootLink+"/sendungen/sendungenabisz100_page-I_zc-b7f774f5.html",True),
            TreeNode("1.9","J",self.rootLink+"/sendungen/sendungenabisz100_page-J_zc-3130680a.html",True),
            TreeNode("1.10","K",self.rootLink+"/sendungen/sendungenabisz100_page-K_zc-c8f76ba1.html",True),
            TreeNode("1.11","L",self.rootLink+"/sendungen/sendungenabisz100_page-L_zc-bbebc1a7.html",True),
            TreeNode("1.12","M",self.rootLink+"/sendungen/sendungenabisz100_page-M_zc-00574a43.html",True),
            TreeNode("1.13","N",self.rootLink+"/sendungen/sendungenabisz100_page-N_zc-b079366f.html",True),
            TreeNode("1.14","O",self.rootLink+"/sendungen/sendungenabisz100_page-O_zc-febc55f5.html",True),
            TreeNode("1.15","P",self.rootLink+"/sendungen/sendungenabisz100_page-P_zc-2c1a492f.html",True),
            TreeNode("1.16","Q",self.rootLink+"/sendungen/sendungenabisz100_page-Q_zc-2cb019d6.html",True),
            TreeNode("1.17","R",self.rootLink+"/sendungen/sendungenabisz100_page-R_zc-cab3e22b.html",True),
            TreeNode("1.18","S",self.rootLink+"/sendungen/sendungenabisz100_page-S_zc-e7f420d0.html",True),
            TreeNode("1.19","T",self.rootLink+"/sendungen/sendungenabisz100_page-T_zc-84a2709f.html",True),
            TreeNode("1.20","U",self.rootLink+"/sendungen/sendungenabisz100_page-U_zc-a26c1157.html",True),
            TreeNode("1.21","V",self.rootLink+"/sendungen/sendungenabisz100_page-V_zc-1fc26dc3.html",True),
            TreeNode("1.22","W",self.rootLink+"/sendungen/sendungenabisz100_page-W_zc-25c5c777.html",True),
            TreeNode("1.23","Y",self.rootLink+"/sendungen/sendungenabisz100_page-Y_zc-388beba7.html",True),
            TreeNode("1.24","Z",self.rootLink+"/sendungen/sendungenabisz100_page-Z_zc-e744950d.html",True),
            TreeNode("1.25","...",self.rootLink+"/sendungen/sendungenabisz100_page-1_zc-43c28d56.html",True)
          )
        )
      )
          
    self.regex_videoPages=re.compile("<a href=\"(.*?sendereihe\\d+.html)\" class=\"linkAll\" title=\"(.*?)\">");
    self.regex_videoLinks=re.compile("<a href=\"(.*?/sendungen/videos/video\\d+?)\\.html\"");
    

    self.regex_xml_title=re.compile("<title>(.*?)</title>");
    self.regex_xml_image=re.compile("<teaserimage>\\s*?<url>(.*?)</url>");
    self.regex_xml_videoLink=re.compile("<asset>\\s*?<profileName>(.*?)</profileName>.*?<progressiveDownloadUrl>(.*?)</progressiveDownloadUrl>\\s*?</asset>",re.DOTALL)
    
    self.regex_videoLink=re.compile("rtmp://.*?\.mp4");
  @classmethod
  def name(self):
    return "KI.KA";
  
  def isSearchable(self):
    return False;
    
  def searchVideo(self, searchText):
    return;
  
  def buildVideoLink(self,pageLink):
    xmlPage = self.loadPage(self.rootLink+pageLink);
    
    title = unicode(self.regex_xml_title.search(xmlPage).group(1),"UTF-8");
    image = self.regex_xml_image.search(xmlPage).group(1).replace("**aspectRatio**","tlarge169").replace("**width**","1472");
    
    self.gui.log("%s %s"%(title,image));
    links = {};
    for match in self.regex_xml_videoLink.finditer(xmlPage):
      profile = match.group(1);
      directLink = match.group(2);
      self.gui.log("%s %s"%(profile,directLink));
      if("MP4 Web S" in profile):
        links[0] = SimpleLink(directLink, 0);
      if("MP4 Web L" in profile):
        links[1] = SimpleLink(directLink, 0);
      if("MP4 Web L+" in profile):
        links[2] = SimpleLink(directLink, 0);
      if("MP4 Web XL" in profile):
        links[3] = SimpleLink(directLink, 0);
    
    return DisplayObject(title,"",image,"",links,True, None);
  
  def buildPageMenu(self, link, initCount):
    mainPage = self.loadPage(link);
    
    
    videoLinks = list(self.regex_videoLinks.finditer(mainPage));
    count = initCount + len(videoLinks)
    if(len(videoLinks) > 0):
      for match in videoLinks:
        link=match.group(1)+"-avCustom.xml";
        
        displayObject = self.buildVideoLink(link);
        self.gui.buildVideoLink(displayObject,self, count);
    else:  
      videoPages = list(self.regex_videoPages.finditer(mainPage));
      count = initCount + len(videoPages)
      for match in videoPages:
        link=match.group(1);
        
        if(not link.startswith(self.rootLink)):
          link = self.rootLink+link;
          
        subPage = self.loadPage(link);
        linkFound = self.regex_videoLinks.search(subPage)
        if(linkFound):
          title = unicode(match.group(2),"UTF-8");
          displayObject = DisplayObject(title,"",None,"",link,False, None);
          self.gui.buildVideoLink(displayObject,self, count);
    
# -*- coding: utf-8 -*-
#-------------LicenseHeader--------------
# plugin.video.Mediathek - Gives acces to the most video-platforms from german public service broadcaster
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

class KIKAPlus(Mediathek):
  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;
    self.rootLink = "http://kikaplus.net/clients/kika/";
    self.idLink=self.rootLink+"kikaplus/";
    self.menuTree = (
        TreeNode("0","TV nach Alter","",False,
          (
            TreeNode("0.0","ab  6 Jahre",self.idLink+"index.php?ag=2",True),
            TreeNode("0.1","ab 10 Jahre",self.idLink+"index.php?ag=3",True)
          )
        ),
        TreeNode("1","Sendungen von A-Z","",False,
          (
            TreeNode("1.0","B-C","",False,
              (
                TreeNode("1.0.0","Bernd & Friends",                       "http://kikaplus.net/clients/kika/kikaplus/?programm=120&ag=4",True),
                TreeNode("1.0.1","BERND DAS BROT",                        "http://kikaplus.net/clients/kika/kikaplus/?programm=36&ag=3",True),
                TreeNode("1.0.2","Boris - Ein Junge vom Baikalsee",       "http://kikaplus.net/clients/kika/kikaplus/?programm=179&ag=3",True),
                TreeNode("1.0.3","Checker Can",                           "http://kikaplus.net/clients/kika/kikaplus/?programm=167&ag=3",True),
                TreeNode("1.0.4","Checker Can - Quick Check",             "http://kikaplus.net/clients/kika/kikaplus/?programm=180&ag=3",True),
              )
            ),
            TreeNode("1.1","D","",False,
              (
                TreeNode("1.1.0","dasbloghaus.tv",                        "http://kikaplus.net/clients/kika/kikaplus/?programm=142&ag=4",True),
                TreeNode("1.1.1","Die Tigerentenbande",                   "http://kikaplus.net/clients/kika/kikaplus/?programm=132&ag=3",True),
                TreeNode("1.1.2","Fluch des Falken",                      "http://kikaplus.net/clients/kika/kikaplus/?programm=166&ag=4",True),
                TreeNode("1.1.3","Fortsetzung folgt - Die Dokumentation", "http://kikaplus.net/clients/kika/kikaplus/?programm=41&ag=3",True),
              )
            ),
            TreeNode("1.2","K-L","",False,
              (
                TreeNode("1.2.0","KAILEREI",                              "http://kikaplus.net/clients/kika/kikaplus/?programm=155&ag=3",True),
                TreeNode("1.2.1","KI.KA LIVE",                            "http://kikaplus.net/clients/kika/kikaplus/?programm=110&ag=4",True),
                TreeNode("1.2.2","KRIMI.DE",                              "http://kikaplus.net/clients/kika/kikaplus/?programm=152&ag=4",True),
                TreeNode("1.2.3","KUMMERKASTEN",                          "http://kikaplus.net/clients/kika/kikaplus/?programm=147&ag=4",True),
                TreeNode("1.2.4","kurz+klick",                            "http://kikaplus.net/clients/kika/kikaplus/?programm=140&ag=4",True),
                TreeNode("1.2.5","logo!",                                 "http://kikaplus.net/clients/kika/kikaplus/?programm=113&ag=4",True),
              )
            ),
            TreeNode("1.3","M-Q","",False,
              (
                TreeNode("1.3.0","Marsupilami",                           "http://kikaplus.net/clients/kika/kikaplus/?programm=117&ag=3",True),
                TreeNode("1.3.1","Mein Style - Die Modemacher",           "http://kikaplus.net/clients/kika/kikaplus/?programm=162&ag=4",True),
                TreeNode("1.3.2","Meine neue Familie",                    "http://kikaplus.net/clients/kika/kikaplus/?programm=136&ag=4",True),
                TreeNode("1.3.3","Piets irre Pleiten",                    "http://kikaplus.net/clients/kika/kikaplus/?programm=103&ag=3",True),
                TreeNode("1.3.4","quergelesen",                           "http://kikaplus.net/clients/kika/kikaplus/?programm=135&ag=3",True),
              )
            ),
            TreeNode("1.4","S-W","",False,
              (
                TreeNode("1.4.0","Schloss Einstein - Erfurt",             "http://kikaplus.net/clients/kika/kikaplus/?programm=90&ag=4",True),
                TreeNode("1.4.1","Schnitzeljagd im Heiligen Land",        "http://kikaplus.net/clients/kika/kikaplus/?programm=122&ag=3",True),
                TreeNode("1.4.2",u"Eine Möhre für Zwei",                  "http://kikaplus.net/clients/kika/kikaplus/?programm=168&ag=4",True),
                TreeNode("1.4.3","SHERLOCK YACK - Der Zoodetektiv",       "http://kikaplus.net/clients/kika/kikaplus/?programm=184&ag=3",True),
                TreeNode("1.4.4","STURMFREI",                             "http://kikaplus.net/clients/kika/kikaplus/?programm=165&ag=4",True),
                TreeNode("1.4.5","TANZALARM!",                            "http://kikaplus.net/clients/kika/kikaplus/?programm=92&ag=3",True),
                TreeNode("1.4.6","Wissen macht Ah!",                      "http://kikaplus.net/clients/kika/kikaplus/?programm=86&ag=4",True),
              )
            ),
            
          )
        )
      )
    
    self.regex_videoPages=re.compile("<a style=\".*?\" href=\"(\?id=.*?)\"( alt=\"Video abspielen\")*>\s*?<span.*?>\s*?<img.*? src=\"../(mediathek/previewpic/.*?\.jpg)\".*?title=\"<label>(.+?)</label><br />(.*?)<br /><br />Sendedatum: (\d{2}.\d{2}.\d{4})<br />");
    

    self.regex_videoLink=re.compile("rtmp://.*?\.mp4");
  @classmethod
  def name(self):
    return "KI.KA-Plus";
  
  def isSearchable(self):
    return False;
    
  def searchVideo(self, searchText):
    return;
  
  def buildPageMenu(self, link, initCount, subLink = False):
    mainPage = self.loadPage(link);
    videoPages = list(self.regex_videoPages.finditer(mainPage));
    print len(videoPages);
    for match in videoPages:
      videoLink=match.group(1);
      imageLink=match.group(3).replace(" ","%20");
      
      title = unicode(match.group(4),"UTF-8");
      subTitle = unicode(match.group(5),"UTF-8");
      dateString = unicode(match.group(6),"UTF-8");
      
      date = time.strptime(dateString,"%d.%m.%Y");
      
      videoPage = self.loadPage(self.idLink+videoLink, None, 4);
      if videoPage == "":
        continue;
      videoLink=self.regex_videoLink.search(videoPage).group();
      videoLinks={0:SimpleLink(videoLink,0)};
      
      displayObject = DisplayObject(title,subTitle,self.rootLink+imageLink,"",videoLinks,True, date);
      self.gui.buildVideoLink(displayObject,self, initCount + len(videoPages));

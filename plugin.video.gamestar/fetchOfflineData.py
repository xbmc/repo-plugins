# -*- coding: utf-8 -*-
import os,subprocess,urllib,re, sys, time;
from gamestar import GamestarWeb
from xml.dom import minidom;

regex_getTargetPath = re.compile("[^/]*\\..{3}$");
regex_getRootPath = re.compile(".*/");

class RateLimiter(object):
  def __init__(self, maxRate):
    self.maxRate = maxRate
    self.last_update = 0
    self.last_downloaded_kb = 0

  def __call__(self, block_count, block_size, total_size):
    if(self.maxRate > 0):    
      total_kb = (block_count*block_size) / 1024.
      delta_kb = total_kb - self.last_downloaded_kb;
      self.last_downloaded_kb = total_kb;

      now = time.time()
      time_needed = now - self.last_update
      
      time_predicted = delta_kb/self.maxRate;
      if(time_predicted > time_needed):
        time.sleep(time_predicted - time_needed);
          
      self.last_update = now

class OfflineGui(object):
  def __init__(self, configXmlPath, rateLimiter):
    
    self.configXml = minidom.parse(configXmlPath);
    self.archivePath = self.getSettingValue("path");

    if(self.archivePath == None):
      print "No archive path is set"
      sys.exit(1)

    self.rateLimiter = rateLimiter;
    self.targetFiles = [];
  def getSettingValue(self, settingId):
    settingId = unicode(settingId);
    for settingNode in self.configXml.getElementsByTagName("setting"):
      if(settingNode.getAttribute("id") == settingId):        
        return settingNode.getAttribute("value");
    return None;
  def log(self, msg):
    if type(msg) not in (str, unicode):
      print type(msg);
    else:
      print msg.encode('utf8');
    
  def buildVideoLink(self,videoItem, forcePrecaching):
    targetFile = regex_getTargetPath.search(videoItem.url).group()
    targetFile = os.path.join(self.archivePath, targetFile);
    
    try:
      print ("Downloading: "+targetFile);
      if not os.path.exists(targetFile):
        if os.path.exists(targetFile+".tmp"):
          os.remove(fileName+".tmp");
        urllib.urlretrieve(videoItem.url, filename=targetFile+".tmp", reporthook = self.rateLimiter)
        os.rename(targetFile+".tmp",targetFile);
      self.targetFiles.append(targetFile);
    except Exception, e:
      print "error downloading %s: %s" % (videoItem.url, e)
    
  def buildCategoryLink(self,galleryItem):
    #wird nicht gebraucht
    pass;
  
  def openMenuContext(self):
    pass;
  
  def closeMenuContext(self):
    pass;
    
  def errorOK(self,title="", msg=""):
    pass;
    
  def cleanUp(self):
    for fileName in os.listdir(self.archivePath):
      fileName = os.path.join(self.archivePath,fileName);
      if(fileName not in self.targetFiles):
        os.remove(fileName);
        
cats = [];
try:
  rateLimiter = RateLimiter(float(sys.argv[2]));
except:
  rateLimiter = RateLimiter(0);
rateLimiter.__call__(0,0,0);

gui = OfflineGui(sys.argv[1],rateLimiter);
webSite=GamestarWeb(gui);

for category in webSite.categories:
  print "%d %s\n"%(category.index,gui.getSettingValue(category.index))
  if(gui.getSettingValue(category.index)>1): 
    print "Fetching: %d"%category.title
    webSite.builCategoryMenu(category, False);
  
gui.cleanUp();

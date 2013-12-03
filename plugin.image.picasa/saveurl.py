import xbmc, xbmcvfs, xbmcgui, xbmcaddon, urllib2, os, sys, urlparse

def ERROR(message,hide_tb=False):
	LOG('ERROR: ' + message)
	short = str(sys.exc_info()[1])
	if hide_tb:
		LOG('ERROR Message: ' + short)
	else:
		import traceback #@Reimport
		traceback.print_exc()
	return short
	
def LOG(message):
	print 'FORUMBROWSER: %s' % message
	
class SaveURL:
	def __init__(self,addonID,url,temp):
		self.addonID = addonID
		self.url = url
		self.temp = temp
		try:
			self.start()
		except:
			err = ERROR('Failed')
			xbmcgui.Dialog().ok('ERROR','Download Error','',err)
		
	def start(self):
		self.makeTemp()
		if not self.url: return
		target = self.askTarget()
		if not target: return
		self.download(target)
		
	def makeTemp(self):
		if not os.path.exists(self.temp):
			profile = xbmc.translatePath(xbmcaddon.Addon(self.addonID).getAddonInfo('profile'))
			self.temp = os.path.join(profile,self.temp)
			if not os.path.exists(self.temp): os.makedirs(self.temp)
			
	def askTarget(self):
		downloadPath = xbmcaddon.Addon(self.addonID).getSetting('download_path') or ''
		downloadPath = xbmcgui.Dialog().browse(3,'Choose Download Path','files','',False,False,downloadPath)
		if not downloadPath: return
		xbmcaddon.Addon(self.addonID).setSetting('download_path',downloadPath)
		return downloadPath
	
	def download(self,target):
		d = Downloader('Downloading File')
		path,ext = d.downloadURL(self.temp,self.url) #@UnusedVariable
		if not os.path.exists(path):
			xbmcgui.Dialog().ok('Failed',os.path.basename(path),'','Failed To Download')
			return
		target = target + os.path.basename(path)
		xbmcvfs.copy(path,target)
		if not xbmcvfs.exists(target):
			xbmcgui.Dialog().ok('Failed',os.path.basename(path),'','Failed Copy File')
			return
		xbmcvfs.delete(path)
		xbmcgui.Dialog().ok('Done',os.path.basename(path),'','Copied Successfully')

class Downloader:
	def __init__(self,header='',message=''):
		self.message = message
		self.prog = xbmcgui.DialogProgress()
		self.prog.create(header,message)
		self.current = 0
		self.display = ''
		self.file_pct = 0
		
	def progCallback(self,read,total):
		if self.prog.iscanceled(): return False
		pct = int(((float(read)/total) * (self.file_pct)) + (self.file_pct * self.current))
		self.prog.update(pct)
		return True
		
	def downloadURLs(self,targetdir,urllist,ext=''):
		file_list = []
		self.total = len(urllist)
		self.file_pct = (100.0/self.total)
		try:
			for url,i in zip(urllist,range(0,self.total)):
				self.current = i
				if self.prog.iscanceled(): break
				self.display = 'File %s of %s' % (i+1,self.total)
				self.prog.update(int((i/float(self.total))*100),self.message,self.display)
				fname = os.path.join(targetdir,str(i) + ext)
				fname, ftype = self.getUrlFile(url,fname,callback=self.progCallback) #@UnusedVariable
				file_list.append(os.path.basename(fname))
		except:
			ERROR('DOWNLOAD URLS ERROR')
			self.prog.close()
			return None
		self.prog.close()
		return file_list
	
	def downloadURL(self,targetdir,url,fname=None):
		if not fname:
			fname = os.path.basename(urlparse.urlsplit(url)[2])
			if not fname: fname = 'file'
		f,e = os.path.splitext(fname)
		fn = f
		ct=0
		while ct < 1000:
			ct += 1
			path = os.path.join(targetdir,fn + e)
			if not os.path.exists(path): break
			fn = f + str(ct)
		else:
			raise Exception
		
		try:
			self.current = 0
			self.display = 'Downloading %s' % os.path.basename(path)
			self.prog.update(0,self.message,self.display)
			target,ftype = self.getUrlFile(url,path,callback=self.progCallback) #@UnusedVariable
		except:
			ERROR('DOWNLOAD URL ERROR')
			self.prog.close()
			return (None,'')
		self.prog.close()
		return (target,ftype)
		
		
			
	def fakeCallback(self,read,total): return True

	def getUrlFile(self,url,target=None,callback=None):
		if not target: return #do something else eventually if we need to
		if not callback: callback = self.fakeCallback
		urlObj = urllib2.urlopen(url)
		size = int(urlObj.info().get("content-length",-1))
		ftype = urlObj.info().get("content-type",'')
		fname = urlObj.info().get('Content-Disposition').split('=',1)[-1].strip().strip('"')
		ext = None
		if '/' in ftype: ext = '.' + ftype.split('/')[-1].replace('jpeg','jpg')
		if fname:
			target = os.path.join(os.path.dirname(target),fname)
		elif ext:
			fname, x = os.path.splitext(target) #@UnusedVariable
			target = fname + ext
		#Content-Disposition: attachment; filename=FILENAME
		outfile = open(target, 'wb')
		read = 0
		bs = 1024 * 8
		while 1:
			block = urlObj.read(bs)
			if block == "": break
			read += len(block)
			outfile.write(block)
			if not callback(read, size): raise Exception('Download Canceled')
		outfile.close()
		urlObj.close()
		return (target,ftype)

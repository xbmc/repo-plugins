import default
reload(default)
from default import FlickrSession,LOG,photoURL
import ShareSocial #@UnresolvedImport

def doShareSocial():
	return FlickrTargetFunctions()

class FlickrTargetFunctions(ShareSocial.TargetFunctions):
	def provide(self,getObj,ID=None):
		fsession = FlickrSession()
		if not fsession.username: return getObj.error('NOUSERS')
		if not fsession.authenticate(): return
		flickr = fsession.flickr
		if getObj.type == 'feed':
			LOG('Providing feed to ShareSocial')
			photos = flickr.activity_userPhotos(timeframe='365d')
			
			try:
				g = photos.find('items').find('item').attrib.get
			except:
				LOG('sharing: provide(): No items in photostream')
				return getObj.error('EMPTYFEED')
			
			clientid = g('owner','')
			clientname = g('ownername','')
			clienticon = photoURL(g('iconfarm',''),g('iconserver',''),g('owner',''),buddy=True)
			client = {'id':clientid,'name':clientname,'photo':clienticon}
			#print client
			for i in photos.find('items').findall('item'):
				
				g = i.attrib.get
				pic = photoURL(g('farm',''),g('server',''),g('id',''),g('secret',''))
				
				event = i.find('activity').find('event','')
				
				g = event.attrib.get
				userimage =  photoURL(g('iconfarm',''),g('iconserver',''),g('user',''),buddy=True)
				
				msg = event.text
				if not msg: msg = g('type','').title()
				
				getObj.addItem(g('username','?'),userimage,msg,g('dateadded',''),pic,client_user=client)
		return getObj
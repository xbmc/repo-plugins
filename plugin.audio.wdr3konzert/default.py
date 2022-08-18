# -*- coding: utf-8 -*-

import libwdr


class wdrkonzert(libwdr.libwdr):
	def libWdrListMain(self):
		l = []
		l.append({'metadata':{'name':self.translation(30000)}, 'params':{'mode':'libWdrListId', 'id':'konzertplayer-uebersicht-100'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(30001)}, 'params':{'mode':'libWdrListId', 'id':'konzertplayer-uebersicht-klassik-100'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(30002)}, 'params':{'mode':'libWdrListId', 'id':'konzertplayer-uebersicht-jazz-100'}, 'type':'dir'})
		#l.append({'metadata':{'name':self.translation(30000)}, 'params':{'mode':'listItems','uri':'/kalender/'}, 'type':'dir'})#'New'
		#l.append({'metadata':{'name':self.translation(30001)}, 'params':{'mode':'listItems','uri':'/klassische-musik/'}, 'type':'dir'})#'Klassische Musik'
		#l.append({'metadata':{'name':self.translation(30002)}, 'params':{'mode':'listItems','uri':'/jazz-and-more/'}, 'type':'dir'})#'Jazz and More'
		return {'items':l,'name':'root'}
	


wdr = wdrkonzert()
wdr.action()
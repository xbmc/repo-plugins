# -*- coding: utf-8 -*-
import libwdr

class wdraudio(libwdr.libwdr):

	def libWdrListMain(self):
		l = []
		l.append({'metadata':{'name':self.translation(32030)}, 'params':{'mode':'libWdrListId', 'id':'audio-uebersicht-100'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(32132)}, 'params':{'mode':'libMediathekListLetters','ignore':'#,x', 'subParams':'{"mode":"libWdrListLetter"}'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(32133)}, 'params':{'mode':'libMediathekListDate', 'subParams':'{"mode":"libWdrListDateVideos"}'}, 'type':'dir'})
		return {'items':l,'name':'root'}

	def libWdrListLetter(self):
		import libwdrrssandroidparser
		if self.params["letter"] == 'c':
			return libwdrrssandroidparser.parseShows(f'sendungen-{self.params["letter"]}-102')
		else:
			return libwdrrssandroidparser.parseShows(f'sendungenabisz-{self.params["letter"]}-100')

	def libWdrListDateVideos(self):
		self.params['id'] = f'sendung-verpasst-audios-100~_tag-{self.params["ddmmyyyy"]}'
		return self.libWdrListId()


wdr = wdraudio()
wdr.action()
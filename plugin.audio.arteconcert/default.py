# -*- coding: utf-8 -*-
import libarte


class arteMusic(libarte.libarte):
	def __init__(self):
		libarte.libarte.__init__(self)
		self.modes['libArteListCategories'] = self.libArteListCategories

	def libArteListMain(self):
		l = []
		l.append({'metadata':{'name':self.translation(32032)}, 'params':{'mode':'libArteListData', 'data':'VIDEO_LISTING', 'uriParams':'{"category":"ARS","videoType":"MOST_RECENT"}'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(32031)}, 'params':{'mode':'libArteListData', 'data':'VIDEO_LISTING', 'uriParams':'{"category":"ARS","videoType":"MOST_VIEWED"}'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(32033)}, 'params':{'mode':'libArteListData', 'data':'VIDEO_LISTING', 'uriParams':'{"category":"ARS","videoType":"LAST_CHANCE"}'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(30503)}, 'params':{'mode':'libArteListCategories'}, 'type':'dir'})
		return {'items':l,'name':'root'}

	def libArteListCategories(self):
		l = []
		l.append({'metadata':{'name':self.translation(30510)}, 'params':{'mode':'libArteListData', 'data':'VIDEO_LISTING', 'uriParams':'{"category":"ARS","subcategories":"MUA","videoType":"MOST_RECENT"}'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(30511)}, 'params':{'mode':'libArteListData', 'data':'VIDEO_LISTING', 'uriParams':'{"category":"ARS","subcategories":"MUE","videoType":"MOST_RECENT"}'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(30512)}, 'params':{'mode':'libArteListData', 'data':'VIDEO_LISTING', 'uriParams':'{"category":"ARS","subcategories":"HIP","videoType":"MOST_RECENT"}'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(30513)}, 'params':{'mode':'libArteListData', 'data':'VIDEO_LISTING', 'uriParams':'{"category":"ARS","subcategories":"MET","videoType":"MOST_RECENT"}'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(30514)}, 'params':{'mode':'libArteListData', 'data':'VIDEO_LISTING', 'uriParams':'{"category":"ARS","subcategories":"CLA","videoType":"MOST_RECENT"}'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(30515)}, 'params':{'mode':'libArteListData', 'data':'VIDEO_LISTING', 'uriParams':'{"category":"ARS","subcategories":"OPE","videoType":"MOST_RECENT"}'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(30516)}, 'params':{'mode':'libArteListData', 'data':'VIDEO_LISTING', 'uriParams':'{"category":"ARS","subcategories":"JAZ","videoType":"MOST_RECENT"}'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(30517)}, 'params':{'mode':'libArteListData', 'data':'VIDEO_LISTING', 'uriParams':'{"category":"ARS","subcategories":"MUD","videoType":"MOST_RECENT"}'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(30518)}, 'params':{'mode':'libArteListData', 'data':'VIDEO_LISTING', 'uriParams':'{"category":"ARS","subcategories":"ADS","videoType":"MOST_RECENT"}'}, 'type':'dir'})
		return {'items':l,'name':self.translation(30503)}
		

o = arteMusic()
o.action()
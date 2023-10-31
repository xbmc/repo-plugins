# -*- coding: utf-8 -*-
from libmediathek4 import lm4
import resources.lib.jsonparser as jsonParser



class filmfriend(lm4):
	def __init__(self):
		lm4.__init__(self)
		self.defaultMode = 'listMain'

		self.modes.update({
			'listSearch': self.listSearch,
			'listMain': self.listMain,
			'listVideos': self.listVideos,
			'listWatchList': self.listWatchList,
		})

		self.searchModes = {
			'listVideoSearch': self.listVideoSearch,
		}

		self.playbackModes = {
			'playVideo':self.playVideo,
		}

	def listMain(self):
		l = []
		l.append({'metadata':{'name':self.translation(32030)}, 'type':'dir', 'params':{'mode':'listSearch', 'content':'videos',  'params':'?facets=Kind&facets=VideoKind&facets=Categories&facets=Genres&facets=GameSituations&facets=AgeRecommendation&facets=AudioLanguages&facets=AudioDescriptionLanguages&facets=SubtitleLanguages&facets=ClosedCaptionLanguages&kinds=Video&kinds=Series&videoKinds=Movie&&&&orderBy=ActiveSinceDateTime&sortDirection=Descending&skip=0&take=20'}})
		l.append({'metadata':{'name':self.translation(32031)}, 'type':'dir', 'params':{'mode':'listSearch', 'content':'videos',  'params':'?facets=Kind&facets=VideoKind&facets=Categories&facets=Genres&facets=GameSituations&facets=AgeRecommendation&facets=AudioLanguages&facets=AudioDescriptionLanguages&facets=SubtitleLanguages&facets=ClosedCaptionLanguages&kinds=Video&videoKinds=Movie&&&&orderBy=MonthlyImpressionScore&sortDirection=Descending&skip=0&take=20'}})
		l.append({'metadata':{'name':self.translation(30600)}, 'type':'dir', 'params':{'mode':'listSearch', 'content':'tvshows', 'params':'?facets=Kind&facets=VideoKind&facets=Categories&facets=Genres&facets=GameSituations&facets=AgeRecommendation&facets=AudioLanguages&facets=AudioDescriptionLanguages&facets=SubtitleLanguages&facets=ClosedCaptionLanguages&kinds=Series&&languageIsoCode=EN&orderBy=EnglishOrder&sortDirection=Ascending&skip=0&take=500'}})
		l.append({'metadata':{'name':self.translation(30601)}, 'type':'dir', 'params':{'mode':'listSearch', 'content':'movies',  'params':'?facets=Kind&facets=VideoKind&facets=Categories&facets=Genres&facets=GameSituations&facets=AgeRecommendation&facets=AudioLanguages&facets=AudioDescriptionLanguages&facets=SubtitleLanguages&facets=ClosedCaptionLanguages&kinds=Video&videoKinds=Movie&categories=d36cbed2-7569-4b94-9080-03ce79c2ecee&orderBy=EnglishOrder&sortDirection=Ascending&skip=0&take=500'}})
		l.append({'metadata':{'name':self.translation(30602)}, 'type':'dir', 'params':{'mode':'listWatchList', 'content':'videos',  'params':'?totalCount=true&take=500&sortOrder=RecentlyAdded'}})
		l.append({'metadata':{'name':self.translation(32139)}, 'params':{'mode':'libMediathekSearch', 'searchMode':'listVideoSearch'}, 'type':'dir'})
		return {'items':l,'name':'root'}

	def listSearch(self):
		return jsonParser.parseSearch(self.params['params'],self.params['content'])

	def listWatchList(self):
		return jsonParser.parseWatchList(self.params['params'],self.params['content'])

	def listVideoSearch(self,searchString):
		return jsonParser.parseSearch(f'?search={searchString}&facets=Kind&facets=VideoKind&facets=Categories&facets=Genres&facets=GameSituations&facets=AgeRecommendation&facets=AudioLanguages&facets=AudioDescriptionLanguages&facets=SubtitleLanguages&facets=ClosedCaptionLanguages&kinds=Video&kinds=Series&kinds=Person&videoKinds=Movie&languageIsoCode=EN&orderBy=Score&sortDirection=Descending&skip=0&take=30')

	def listVideos(self):
		return jsonParser.parseVideos(self.params['id'],self.params['content'])

	def playVideo(self):
		return jsonParser.getVideoUrl(self.params['video'])

if sys.argv[1] == 'libraryPicker':
	import resources.lib.login as login
	login.pick()
elif sys.argv[1] == 'libraryLogin':
	import resources.lib.login as login
	login.login()
else:
	p = filmfriend()
	p.action()

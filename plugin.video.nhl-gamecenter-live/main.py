import base64, os, pickle, sys, urllib, urlparse
import xbmc, xbmcaddon, xbmcgui, xbmcplugin
try:
	import simplejson as json
except ImportError:
	import json
# http://mail.python.org/pipermail/python-list/2009-June/540579.html
import _strptime
from datetime import datetime
from dateutil import tz
from resources.lib.nhlgc import nhlgc

__addon__       = xbmcaddon.Addon()
__addonurl__    = sys.argv[0]
__addonhandle__ = int(sys.argv[1])
__addonargs__   = urlparse.parse_qs(sys.argv[2][1:])
__addonicon__   = __addon__.getAddonInfo('icon')
__addonfanart__ = __addon__.getAddonInfo('fanart')
__addonname__   = __addon__.getAddonInfo('name')
__cwd__         = __addon__.getAddonInfo('path').decode('utf-8')
__profile__     = __addon__.getAddonInfo('profile').decode('utf-8')
__language__    = __addon__.getLocalizedString
__teams_json__  = os.path.join(__cwd__, 'teams.json')
__cookiesfile__ = xbmc.translatePath(os.path.join(__profile__, 'cookies.lwp'))

game_time_format = xbmc.getRegion('dateshort') + ' ' + xbmc.getRegion('time').replace(':%S', '')

class XBMC_NHL_GameCenter(object):
	# This is the list of bitrates defined in settings.xml. These two sources
	# should be kept in sync!
	SETTINGS_BITRATES = [
# The following are for reference only, and should remain commented out:
#		'Always ask',   # 0
#		'Best quality', # 1
		'5000',         # 2
		'4500',         # 3
		'3000',         # 4
		'1600',         # 5
		'1200',         # 6
		'800',          # 7
		'400',          # 8
		'240',          # 9
		'150',          # 10
	]

	MATCHUP_IMAGES_URL = 'http://nhl.cdn.neulion.net/u/nhlgc_roku/images/HD/%s_at_%s.jpg'

	def __init__(self, skip_networking=False):
		username    = __addon__.getSetting('gc_username')
		password    = __addon__.getSetting('gc_password')
		rogerslogin = __addon__.getSetting('gc_rogerslogin') == 'true'

		proxy_config = None
		if __addon__.getSetting('proxy_enabled') == 'true':
			proxy_config = {
				'scheme': __addon__.getSetting('proxy_scheme'),
				'host': __addon__.getSetting('proxy_host'),
				'port': __addon__.getSetting('proxy_port'),
				'auth': {
					'username': __addon__.getSetting('proxy_username'),
					'password': __addon__.getSetting('proxy_password'),
				},
			}
			if proxy_config['auth']['username'] == '' and proxy_config['auth']['password'] == '':
				proxy_config['auth'] = None

		hls_server = None
		try:
			self.has_hls_proxy = False
			hls_proxy = xbmcaddon.Addon('service.nhl-hls-proxy')
			hls_server = {
				'host': hls_proxy.getSetting('hls_listen_host'),
				'port': int(hls_proxy.getSetting('hls_listen_port')),
			}
			urllib.urlopen('http://%s:%d' % (hls_server['host'], hls_server['port']))
			self.has_hls_proxy = True
		except RuntimeError:
			# Failed to get the handle for the add-on, so it probably hasn't
			# been enabled.
			pass
		except IOError:
			# Failed to connect to the proxy server, so it either hasn't been
			# enabled, or it failed to start up.
			pass

		try:
			self.game_center = nhlgc(username, password, rogerslogin, proxy_config, hls_server, __cookiesfile__, skip_networking)
		except nhlgc.LogicError as error:
			self.display_notification(error)
			raise RuntimeError(error)
		except nhlgc.NetworkError as error:
			self.display_notification(error)
			raise RuntimeError(error)

		self.preferred_bitrate  = int(__addon__.getSetting('preferred_bitrate'))
		self.always_ask_bitrate = self.preferred_bitrate == 0

		self.team_info = self.parse_teams_json(__teams_json__)
		team_names_setting = int(__addon__.getSetting('team_names'))
		if team_names_setting == 1:
			self.team_info_key = 'team'
		elif team_names_setting == 2:
			self.team_info_key = 'full-name'
		elif team_names_setting == 3:
			self.team_info_key = None
		else:
			self.team_info_key = 'city'
		self.show_scores = __addon__.getSetting('show_scores') == 'true'
		self.at_instead_of_vs = __addon__.getSetting('at_instead_of_vs') == 'true'
		self.show_stream_duration = __addon__.getSetting('show_stream_duration') == 'true'

	def parse_teams_json(self, teams_file):
		with open(teams_file) as file_obj:
			teams_json = file_obj.read()
		return json.loads(teams_json)

	def display_notification(self, msg):
		xbmcgui.Dialog().ok(__language__(30035), str(msg))

	def build_game_info(self, game, title_suffix=''):
		info = {
			'genre': 'Hockey',
#			'year': int(game['season']),
			'episode': int(game['id']),
			'season': int(game['season']),
#			'cast': [
#				self.team_info[game['home_team']]['full-name'],
#				self.team_info[game['away_team']]['full-name'],
#			],
			'title': self.game_title(game, None)[0],
			'duration': 0,
		}
		if len(title_suffix) > 0:
			info['title'] += ' ' + title_suffix
		if self.show_stream_duration and game['start_time'] is not None:
			info['aired'] = game['start_time'].astimezone(tz.tzlocal()).strftime('%Y-%m-%d')
			if game['end_time'] is not None:
				# FIXME: This is both correct and incorrect at the same time.
				# It's correct because the start and end times are correct.
				# It's incorrect because non-live streams don't have commercials.
				#
				# Times seem to be high by about 50 minutes, so lets just chop
				# that time off and hope for the best.
				time_delta = game['end_time'] - game['start_time']
				info['duration'] = str((time_delta.seconds / 60) - 50)
		return info

	def add_folder(self, label=None, params={}, game=None):
		item = xbmcgui.ListItem(label)
		item.setProperty('fanart_image', __addonfanart__)

		icon = None
		if game is not None:
			params['game'] = self.serialize_data(game)
			icon = self.matchup_image(game)
			item.setInfo('video', self.build_game_info(game))
		if icon is None:
			icon = __addonicon__
		item.setIconImage(icon)
		item.setArt({'thumb': icon})

		url = __addonurl__
		if len(params) > 0:
			url += '?' + urllib.urlencode(params)
		xbmcplugin.addDirectoryItem(
			isFolder=True,
			handle=__addonhandle__,
			url=url,
			listitem=item,
		)

	def add_item(self, label=None, url=__addonurl__, params={}, game=None):
		item = xbmcgui.ListItem(label)
		item.setProperty('fanart_image', __addonfanart__)

		icon = None
		if game is not None:
			icon = self.matchup_image(game)
			item.setInfo('video', self.build_game_info(game, '(' + label + ')'))
		if icon is None:
			icon = __addonicon__
		item.setIconImage(icon)
		item.setArt({'thumb': icon})

		if len(params) > 0:
			url += '?' + urllib.urlencode(params)
		xbmcplugin.addDirectoryItem(
			isFolder=False,
			handle=__addonhandle__,
			url=url,
			listitem=item,
		)

	def select_bitrate(self, streams):
		sorted_streams = sorted(streams, key=int, reverse=True)

		# Pick the best quality stream.
		if self.preferred_bitrate == 1:
			return sorted_streams[0]
		# Pick a specific stream quality.
		if self.preferred_bitrate > 1:
			for bitrate in sorted_streams:
				if bitrate == self.SETTINGS_BITRATES[self.preferred_bitrate]:
					return bitrate
		# Ask what bitrate the user wants.
		dialog = xbmcgui.Dialog()
		xbmc.executebuiltin('Dialog.Close(busydialog)')
		ret = dialog.select(__language__(30005), sorted_streams)
		return sorted_streams[ret]

	def game_title(self, game, scoreboard):
		# Get the team names.
		home_team = game['home_team']
		away_team = game['away_team']
		if self.team_info_key is not None:
			if home_team in self.team_info:
				home_team = self.team_info[home_team][self.team_info_key]
			if away_team in self.team_info:
				away_team = self.team_info[away_team][self.team_info_key]

		# Get the score for the game.
		home_team_score, away_team_score = game['home_goals'], game['away_goals']
		if scoreboard is not None and game['id'] in scoreboard:
			if home_team_score is None and str(scoreboard[game['id']]['hts']) != '':
				home_team_score = str(scoreboard[game['id']]['hts'])
			if away_team_score is None and str(scoreboard[game['id']]['ats']) != '':
				away_team_score = str(scoreboard[game['id']]['ats'])

		# Get the required dates and times.
		current_time_utc = datetime.utcnow().replace(tzinfo=tz.tzutc())
		if game['start_time'] is not None:
			start_time_local = game['start_time'].astimezone(tz.tzlocal()).strftime(game_time_format)
		else:
			start_time_local = game['date'].strftime(xbmc.getRegion('dateshort'))

		# Start with the basic title of "Team vs Team".
		lang_id = 30027
		if self.at_instead_of_vs == True:
			home_team, away_team = away_team, home_team
			home_team_score, away_team_score = away_team_score, home_team_score
			lang_id = 30028
		title = home_team + __language__(lang_id) + away_team

		# Handle game status flags.
		status_flags = ''
		if game['blocked']:
			status_flags = __language__(30022)
		else:
			game_ended = False
			if game['end_time'] is not None:
				if current_time_utc >= game['end_time']:
					# Game has ended.
					game_ended = True
					time_delta = current_time_utc - game['end_time']
					if time_delta.days < 1:
						status_flags = __language__(30024)
			if not game_ended and game['live'] and current_time_utc >= game['start_time']:
				# Game is in progress.
				status_flags = __language__(30023)

		# Handle showing the game score.
		game_score = ''
		if self.show_scores and home_team_score is not None and away_team_score is not None:
			game_score = '(%s-%s)' % (home_team_score, away_team_score)

		# Prepend the game start time.
		return (
			title,
			start_time_local,
			status_flags,
			game_score,
		)

	def formatted_game_title(self, game, scoreboard):
		title = self.game_title(game, scoreboard)
		game_title = title[1] + ': '
		if len(title[2]) > 0:
			game_title += title[2] + ' '
		game_title += title[0]
		if len(title[3]) > 0:
			game_title += ' ' + title[3]
		return game_title

	def matchup_image(self, game):
		image = None
		try:
			home_team, away_team = game['home_team'], game['away_team']
			if 'alt-abbr' in self.team_info[home_team]:
				home_team = self.team_info[home_team]['alt-abbr']
			if 'alt-abbr' in self.team_info[away_team]:
				away_team = self.team_info[away_team]['alt-abbr']
			image = self.MATCHUP_IMAGES_URL % (away_team, home_team)
		except KeyError:
			pass
		return image

	def serialize_data(self, data):
		return base64.b64encode(pickle.dumps(data, pickle.HIGHEST_PROTOCOL))

	def unserialize_data(self, data):
		return pickle.loads(base64.b64decode(data))

	def MODE_list(self, today_only):
		retry_args = {'mode': 'list'}
		if today_only == True:
			retry_args['type'] = 'today'
		else:
			retry_args['type'] = 'recent'

		scoreboard = None
		try:
			scoreboard = self.game_center.get_current_scoreboard()
		except nhlgc.NetworkError:
			pass

		try:
			games = self.game_center.get_games_list(today_only)
			for game in games:
				if game['end_time'] is not None:
					params = {'mode': 'view_options'}
				else:
					params = {
						'mode': 'watch',
						'stream_type': self.game_center.STREAM_TYPE_LIVE,
					}
				self.add_folder(
					label=self.formatted_game_title(game, scoreboard),
					params=params,
					game=game,
				)
			return
		except nhlgc.NetworkError as error:
			self.display_notification(error)
		except nhlgc.LoginError as error:
			self.display_notification(error)
		except nhlgc.LogicError as error:
			self.display_notification(error)
		self.add_item(label=__language__(30030), params=retry_args)

	def MODE_view_options(self, game):
		view_options = [
			(__language__(30059), self.game_center.STREAM_TYPE_LIVE),
		]
		if game['end_time'] is not None:
			view_options += [
				(__language__(30060), self.game_center.STREAM_TYPE_CONDENSED),
				(__language__(30061), self.game_center.STREAM_TYPE_HIGHLIGHTS),
			]
		for label, stream_type in view_options:
			self.add_folder(
				label=label,
				params={
					'mode': 'watch',
					'stream_type': stream_type,
				},
				game=game,
			)

	def MODE_watch(self, game, stream_type):
		retry_args = {
			'mode': 'watch',
			'game': game,
			'stream_type': stream_type,
		}

		if stream_type == self.game_center.STREAM_TYPE_HIGHLIGHTS:
			highlights = self.game_center.get_game_highlights(game['season'], game['id'], game['season_type'])
			if 'home' in highlights and 'publishPoint' in highlights['home']:
				self.add_item(label=__language__(30025), url=highlights['home']['publishPoint'], game=game)
			if 'away' in highlights and 'publishPoint' in highlights['away']:
				self.add_item(label=__language__(30026), url=highlights['away']['publishPoint'], game=game)
			if 'french' in highlights and 'publishPoint' in highlights['away']:
				self.add_item(label=__language__(30062), url=highlights['french']['publishPoint'], game=game)
			return

		perspectives = [
			(__language__(30025), 'home', self.game_center.PERSPECTIVE_HOME),
			(__language__(30026), 'away', self.game_center.PERSPECTIVE_AWAY),
		]
		if game['french_game'] == True:
			perspectives += [(__language__(30062), 'french', self.game_center.PERSPECTIVE_FRENCH)]

		seen_urls = {}
		use_bitrate = None
		for label, stream_key, perspective in perspectives:
			try:
				from_start = False
				if stream_type == self.game_center.STREAM_TYPE_LIVE and game['streams'][stream_key] is not None:
					playlists = self.game_center.get_playlists_from_m3u8_url(game['streams'][stream_key])
				else:
					if stream_type == self.game_center.STREAM_TYPE_LIVE:
						from_start = True
					playlists = self.game_center.get_video_playlists(game['season'], game['id'], game['season_type'], stream_type, perspective)

				if len(playlists) == 1:
					stream_url = playlists.values()[0]
				else:
					if use_bitrate is None or use_bitrate not in playlists:
						use_bitrate = self.select_bitrate(playlists)
					stream_url = playlists[use_bitrate]
				if stream_url not in seen_urls:
					self.add_item(
						label=label,
						url=self.game_center.get_authorized_stream_url(game, stream_url, False),
						game=game,
					)
					if self.has_hls_proxy and from_start == True:
						self.add_item(
							label=label + __language__(30063),
							url=self.game_center.get_authorized_stream_url(game, stream_url, True),
							game=game,
						)
					seen_urls[stream_url] = True
			except nhlgc.NetworkError as error:
				if error.status_code != 404:
					self.display_notification(error)
					self.add_item(label=__language__(30030), params=retry_args)
			except nhlgc.LoginError as error:
				self.display_notification(error)
				self.add_item(label=__language__(30030), params=retry_args)

	def MODE_archives(self, season):
		retry_args = {
			'mode': 'archives',
			'season': season,
		}

		try:
			archives = self.game_center.get_archived_seasons()
			if season is None:
				for archive in archives:
					title = '%d - %d' % (int(archive['season']), int(archive['season']) + 1)
					self.add_folder(title, {
						'mode': 'archives',
						'season': archive['season'],
					})
			else:
				title = '%d - %d: ' % (int(season), int(season) + 1)
				for archive in archives:
					if archive['season'] != season:
						continue
					for month in archive['months']:
						self.add_folder(title + __language__(30037 + int(month) - 1), {
							'mode': 'archives_month',
							'season': season,
							'month': month,
						})
			return
		except nhlgc.NetworkError as error:
			self.display_notification(error)
		except nhlgc.LoginError as error:
			self.display_notification(error)
		except nhlgc.LogicError as error:
			self.display_notification(error)
		self.add_item(label=__language__(30030), params=retry_args)

	def MODE_archives_month(self, season, month):
		retry_args = {
			'mode': 'archives_month',
			'season': season,
			'month': month,
		}

		try:
			games = self.game_center.get_archived_month(season, month)
			for game in games:
				self.add_folder(
					label=self.formatted_game_title(game, None),
					params={'mode': 'view_options'},
					game=game,
				)
			return
		except nhlgc.NetworkError as error:
			self.display_notification(error)
		except nhlgc.LoginError as error:
			self.display_notification(error)
		except nhlgc.LogicError as error:
			self.display_notification(error)
		self.add_item(label=__language__(30030), params=retry_args)

##
# Addon menu system.
##

cache_folder = True
try:
	mode = __addonargs__.get('mode', None)
	if type(mode) == type(list()):
		mode = mode[0]
	skip_networking = False
	if mode is None or mode == 'view_options':
		skip_networking = True
	game_center = XBMC_NHL_GameCenter(skip_networking)

	if mode is None:
		cache_folder = False
		game_center.add_folder(__language__(30029), {'mode': 'list', 'type': 'today'})
		game_center.add_folder(__language__(30032), {'mode': 'list', 'type': 'recent'})
		game_center.add_folder(__language__(30036), {'mode': 'archives', 'season': None})
	elif mode == 'list':
		xbmcplugin.setContent(__addonhandle__, 'episodes')
		cache_folder = False
		today_only = __addonargs__.get('type')[0] == 'today'
		game_center.MODE_list(today_only)
	elif mode == 'view_options':
		game = game_center.unserialize_data(__addonargs__.get('game')[0])
		game_center.MODE_view_options(game)
	elif mode == 'watch':
		xbmcplugin.setContent(__addonhandle__, 'episodes')
		game = game_center.unserialize_data(__addonargs__.get('game')[0])
		stream_type = __addonargs__.get('stream_type')[0]
		game_center.MODE_watch(game, stream_type)
	elif mode == 'archives':
		season = __addonargs__.get('season')[0]
		if season == 'None':
			season = None
		game_center.MODE_archives(season)
	elif mode == 'archives_month':
		xbmcplugin.setContent(__addonhandle__, 'episodes')
		season = __addonargs__.get('season')[0]
		month  = __addonargs__.get('month')[0]
		game_center.MODE_archives_month(season, month)
except RuntimeError:
	pass

xbmcplugin.endOfDirectory(__addonhandle__, cacheToDisc=cache_folder)

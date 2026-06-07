import json
from xbmcaddon import Addon
from xbmcvfs import translatePath
from xbmcgui import Dialog

addon = Addon()
blacklist_path: str = f"{translatePath(addon.getAddonInfo('profile'))}/blacklist.json"

def blacklist_load() -> dict:
	try:
		with open(blacklist_path, 'r') as f: return json.load(f)
	except:
		return dict()

def blacklist_save(blacklist: dict) -> None:
	with open(blacklist_path, 'w+') as f:
		json.dump(blacklist, f)

def blacklist_add(channel_id: str, channel_name: str) -> None:
	blacklist: dict = blacklist_load()

	if channel_id not in blacklist:
		blacklist[channel_id] = dict(name = channel_name)

	blacklist_save(blacklist)

def blacklist_remove(channel_id: str, prompt: bool=False) -> None:
	blacklist: dict = blacklist_load()

	if prompt:
		if not Dialog().yesno(blacklist[channel_id]['name'], addon.getLocalizedString(30024)):
			return

	if channel_id in blacklist:
		del blacklist[channel_id]
		blacklist_save(blacklist)

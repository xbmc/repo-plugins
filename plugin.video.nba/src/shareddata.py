import xbmc,xbmcaddon
import json

class SharedData:

	def __init__(self):
		self.folder = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'));
		self.file_path = self.folder + "shared_data.json"

	def __getFileContent(self):
		try:
			with open(self.file_path) as file:
				file_content = file.read()
				file.close()
		except IOError:
			file_content = "{}"

		json_content = json.loads(file_content)

		return json_content

	def set(self, key, value):
		json_content = self.__getFileContent()

		#Simple "json-path"-like set algorithm
		keys = key.split('.')
		keys_length = len(keys)
		item = json_content
		for index, key in enumerate(keys):
			if key not in item:
				item[key] = {}
			
			if index+1 < keys_length:
				if not isinstance(item[key], dict):
					item[key] = {}
				item = item[key]
			else:
				item[key] = value

		file_content = json.dumps(json_content)

		file = open(self.file_path, "w")
		file.write(file_content)
		file.close()

	def get(self, key):
		json_content = self.__getFileContent()

		#Simple "json-path"-like get algorithm
		keys = key.split(".")
		item = json_content
		try:
			for key in keys:
				item = item.get(key, {})
		except:
			return None

		return item

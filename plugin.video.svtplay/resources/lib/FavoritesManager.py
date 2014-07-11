import hashlib
import json
import os

import xbmc
import xbmcaddon

import CommonFunctions as common

ADDON_ID = "plugin.video.svtplay"
FILE_PATH = xbmc.translatePath("special://profile/addon_data/%s/favorites.json" % ADDON_ID)

FAVORITES = {}

log = common.log

def add(title, url):
  global FAVORITES
  __load_from_disk()
  fav_id = hashlib.md5(title).hexdigest()
  FAVORITES[fav_id] = {
    "title": title,
    "url": url
  }
  __save_to_disk()
  return fav_id

def remove(fav_id):
  global FAVORITES
  __load_from_disk()
  if fav_id in FAVORITES.keys():
    del(FAVORITES[fav_id])
    __save_to_disk()
    return True
  else:
    return False

def remove_by_title(title):
  fav_id = hashlib.md5(title).hexdigest()
  return remove(fav_id)

def clear():
  global FAVORITES
  FAVORITES = {}
  __save_to_disk()

def get(fav_id):
  __load_from_disk()
  if fav_id in FAVORITES.keys():
    return {
      "id": fav_id,
      "title": FAVORITES[fav_id]["title"],
      "url": FAVORITES[fav_id]["url"]
    }
  else:
    return None

def get_by_title(title):
  fav_id = hashlib.md5(title).hexdigest()
  return get(fav_id)

def get_all():
  __load_from_disk()
  favorites = []
  for key in FAVORITES.keys():
    favorites.append({
      "id": key,
      "title": FAVORITES[key]["title"],
      "url": FAVORITES[key]["url"]
    })
  return favorites

def __load_from_disk():
  global FAVORITES
  FAVORITES = {}
  if os.path.exists(FILE_PATH) and os.stat(FILE_PATH).st_size != 0:
    with open(FILE_PATH, "r") as file_handle:
        FAVORITES = json.load(file_handle)
  log("Load from disk: "+str(FAVORITES))

def __save_to_disk():
  log("Save to disk: "+str(FAVORITES))
  with open(FILE_PATH, "w") as file_handle:
    file_handle.write(json.dumps(FAVORITES))

# To support XBMC.RunScript
if __name__ == "__main__":
  log("FM called as script!")
  if len(sys.argv) < 2:
    log("No argument given!")
  else:
    if sys.argv[1] == "add" and len(sys.argv) > 3:
      add(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "remove" and len(sys.argv) > 2:
      remove(sys.argv[2])
      xbmc.executebuiltin("XBMC.Container.Refresh")

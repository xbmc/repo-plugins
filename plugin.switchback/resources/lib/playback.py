import os
import json
from dataclasses import dataclass
from typing import List, Optional

import xbmcvfs

# noinspection PyPackages
from bossanova808.playback import Playback
# noinspection PyPackages
from bossanova808.utilities import get_playcount_and_resume_point, get_advancedsetting
# noinspection PyPackages
from bossanova808.logger import Logger


@dataclass
class PlaybackList:
    """
    A list of Playback objects, with some helper methods.  Stored both in memory (accessible via .list) and on disk (filename at .file)
    Is a standard Python list, so can be iterated over, indexed, etc., and of course, all standard list methods are available.

    To create a PlaybackList::
        switchback = PlaybackList([], xbmcvfs.translatePath(os.path.join(PROFILE, "switchback_list.json")))
    """
    list: List[Playback]
    file: str
    remove_watched_playbacks: bool = False

    def toJson(self) -> str:
        """
        Return the list of Playback objects as JSON

        :return: the list of Playback objects as JSON
        """
        return json.dumps([p.__dict__ for p in self.list], ensure_ascii=False, indent=2)

    def init(self) -> None:
        """
        Initialise/reset in memory PlaybackList, and delete/re-create the empty PlaybackList file
        """
        self.list = []
        xbmcvfs.mkdirs(os.path.dirname(self.file))
        with open(self.file, 'w', encoding='utf-8') as switchback_list_file:
            switchback_list_file.write('[]')

    def load_or_init(self) -> None:
        """
        Load a JSON-formatted PlaybackList from the PlaybackList file
        """
        Logger.info("Try to load PlaybackList from file:", self.file)
        # Ensure we start from a clean slate before loading from disk
        self.list = []
        try:
            with open(self.file, 'r', encoding='utf-8') as switchback_list_file:
                switchback_list_json = json.load(switchback_list_file)
                if not isinstance(switchback_list_json, list):
                    Logger.error(f"PlaybackList file [{self.file}] did not contain a JSON array — reinitialising")
                    self.init()
                    return
                for playback in switchback_list_json:
                    self.list.append(Playback.from_dict(playback))

        except FileNotFoundError:
            Logger.warning(f"Could not find: [{self.file}] - creating empty PlaybackList & file")
            self.init()
        except json.JSONDecodeError:
            Logger.error(f"JSONDecodeError - Unable to parse PlaybackList file [{self.file}] -  creating empty PlaybackList & file")
            self.init()

        list_needs_save = False

        # Defensively collapse any duplicate entries for the same piece of media - there should only
        # ever be one entry (the most recent) per movie/episode/etc. Duplicates can end up here from
        # an older version of the addon that deduplicated on .path alone, which isn't always stable
        # for the same media across plays (see Playback.identity_key). The list is newest-first, so
        # keeping the first occurrence of each identity keeps the most recent one.
        seen_identities = set()
        deduplicated_list = []
        for item in self.list:
            identity = item.identity_key
            if identity in seen_identities:
                Logger.warning(f"Removing duplicate PlaybackList entry for [{item.pluginlabel}] (identity: {identity})")
                list_needs_save = True
                continue
            seen_identities.add(identity)
            deduplicated_list.append(item)
        self.list = deduplicated_list

        # Refresh resume points from the Kodi library (consider e.g. shared library scenarios), and -
        # if the user wants it - filter out watched items, for every library item in one pass. Both
        # pieces of data come from the same JSON-RPC call per dbid, rather than two separate
        # round trips, since a list with several library items otherwise means twice as many
        # JSON-RPC calls on every single load (e.g. just viewing the Switchback list).
        paths_to_remove = []
        for item in list(self.list):
            # DB item? Refresh its resume point, and its playcount if we care about that here
            if item.dbid:
                playcount, library_resume_point = get_playcount_and_resume_point(item.type, item.dbid)

                if self.remove_watched_playbacks:
                    if playcount is None:
                        Logger.warning(f"dbid {item.dbid} no longer valid in Kodi library for [{item.pluginlabel}] - removing from Switchback list")
                        paths_to_remove.append(item.path)
                        list_needs_save = True
                        continue
                    elif playcount > 0:
                        list_needs_save = True
                        Logger.warning(f"Filtering watched playback from the list (as playcount > 0 in Kodi DB): [{item.pluginlabel}]")
                        paths_to_remove.append(item.path)
                        continue

                if library_resume_point != item.resumetime:
                    Logger.debug(f"Retrieved library resume point: {library_resume_point} != existing list resume point {item.resumetime} - updating playback list")
                    list_needs_save = True
                    item.resumetime = library_resume_point

            # Not a DB item - if the user wants watched items filtered, use a calculation instead
            # and compare to the playcount_minium_percent (there's no library playcount to check)
            elif self.remove_watched_playbacks and item.resumetime and item.totaltime:
                percent_played = (item.resumetime / item.totaltime) * 100
                # Use the user set playcount_minium_percent if there is one, or fallback to Kodi default 90 percent
                setting = get_advancedsetting('video/playcountminimumpercent')
                playcount_minium_percent = float(setting) if setting and setting != 0 else 90.0
                if percent_played >= playcount_minium_percent:
                    list_needs_save = True
                    Logger.debug(f"Filtering watched playback from the list (as {percent_played:.1f}% played over playcount_minium_percent {playcount_minium_percent}%): [{item.pluginlabel}]")
                    paths_to_remove.append(item.path)

        if paths_to_remove:
            list_needs_save = True
            for path in paths_to_remove:
                self.remove_playbacks_of_path(path)

        if list_needs_save:
            self.save_to_file()

    def save_to_file(self) -> None:
        """
        Save the PlaybackList to the PlaybackList file (as JSON)
        """
        Logger.info(f"Saving PlaybackList to file: {self.file}")
        import tempfile
        import time
        directory_name = os.path.dirname(self.file)
        temp_dir = None
        if directory_name:
            xbmcvfs.mkdirs(directory_name)
            temp_dir = directory_name
        with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8', dir=temp_dir) as temp_file:
            temp_file.write(self.toJson())
            temporary_name = temp_file.name

        # On Windows, os.replace() can transiently fail with PermissionError if another
        # Switchback process (the service, or an overlapping plugin invocation) has the
        # destination file briefly open - retry a few times rather than letting a routine
        # save crash the caller.
        last_error = None
        for attempt in range(5):
            try:
                os.replace(temporary_name, self.file)
                return
            except PermissionError as e:
                last_error = e
                time.sleep(0.1)
        Logger.error(f"Could not save PlaybackList to file [{self.file}] after retries: {last_error}")
        try:
            os.remove(temporary_name)
        except OSError:
            pass

    def delete_file(self) -> None:
        """
        Deletes the PlaybackList file
        """
        if os.path.exists(self.file):
            Logger.info(f"Deleting PlaybackList file [{self.file}]")
            os.remove(self.file)

    def remove_playbacks_of_path(self, path: str) -> None:
        """
        Remove any playbacks of a given path from the PlaybackList
        """
        self.list = [x for x in self.list if x.path != path]

    def find_playback_by_path(self, path: str) -> Optional[Playback]:
        """
        Return a playback with the matching path if found, otherwise None

        :param path: str The path to search for
        :return: Playback or None: The Playback object if found, otherwise None
        """
        Logger.debug(f"find_playback_by_path: {path}")
        for playback in self.list:
            if playback.path == path:
                Logger.debug(f"Matched playback to [{playback.path}]")
                return playback
        Logger.debug(f"No matching playback for [{path}]")
        return None

    def find_playback_by_identity(self, playback: Playback) -> Optional[Playback]:
        """
        Return an existing list entry representing the same piece of media as the given playback
        (see Playback.identity_key), if found, otherwise None. Unlike find_playback_by_path(), this
        still recognises the same library movie/episode/etc even if the specific path/file Kodi
        reports for it differs between plays (e.g. a direct library click vs an addon-triggered
        Switchback replay of the same item) - which is what actually determines whether a repeat
        play updates the existing entry or wrongly creates a duplicate.

        :param playback: the Playback to find an existing match for
        :return: Playback or None: The matching Playback object if found, otherwise None
        """
        identity = playback.identity_key
        Logger.debug(f"find_playback_by_identity: {identity}")
        for existing in self.list:
            if existing.identity_key == identity:
                Logger.debug(f"Matched playback to [{existing.pluginlabel}]")
                return existing
        Logger.debug(f"No matching playback for identity [{identity}]")
        return None

#!/usr/bin/env python
# encoding: UTF-8

from __future__ import absolute_import

from urllib.parse import quote_plus as quote

import sarpur
import xbmc
import xbmcgui
import xbmcplugin
from sarpur import logger  # noqa
from util import strptime


class GUI(object):
    """
    A very simple class that wraps the interface functions in Kodi
    """

    def __init__(self, addon_handle, base_url):
        """
        :param addon_handle: An identifier that Kodi uses to identify the addon
                             (created in default.py)
        :param base_url: The root internal url used in all calls in the addon
        """
        self.addon_handle = addon_handle
        self.base_url = base_url

    def _get_url(self, action_key, action_value, name):

        format_params = {
            "base_url": self.base_url,
            "key": quote(action_key),
            "value": quote(action_value.encode("utf-8")),
            "name": quote(name.encode("utf-8")),
        }
        return "{base_url}?action_key={key}&" "action_value={value}&name={name}".format(
            **format_params
        )

    def _add_dir(
        self,
        name,
        action_key="",
        action_value="",
        image=None,
        is_folder=False,
        extra_info=None,
        selectable=True,
        context_menu=[],
        subtitles=None,
    ):
        """
        Creates a link in Kodi

        :param name: Name of the link
        :param action_key: Name of the action to take when link selected
        :param action_value: Parameter to use with the action
        :param image: Icon to use for the link
        :param is_folder: Does the link lead to a folder or playable item
        :param extra_info: Extra information for info label
        :param selectable: Default True.

        """
        list_item = xbmcgui.ListItem(name)
        list_item.setArt({"icon": image, "thumbnail": ""})
        if selectable:
            url = self._get_url(action_key, action_value, name)
            list_item.setProperty("IsPlayable", "true")
        else:
            url = ""

        info_labels = {"Title": name}
        if extra_info:
            info_labels.update(extra_info)

        list_item.setInfo(type="Video", infoLabels=info_labels)

        if context_menu:
            list_item.addContextMenuItems(context_menu)

        if subtitles and any(subtitles):
            # Make sure we don't pass in [None]
            list_item.setSubtitles([sub for sub in subtitles if sub])

        xbmcplugin.addDirectoryItem(
            handle=self.addon_handle, url=url, listitem=list_item, isFolder=is_folder
        )

    def add_dir(self, name, action_key, action_value, image="DefaultFolder.png"):
        """
        Create link that leads to another folder (or "folder")

        :param name: The name of the folder
        :param action_key: Action to take
        :param action_value: Parameter to action
        :param image: Image to use with the folder
        """
        self._add_dir(
            name=name,
            action_key=action_key,
            action_value=action_value,
            image=image,
            is_folder=True,
        )

    def add_item(
        self,
        name,
        action_key,
        action_value,
        image="DefaultMovies.png",
        extra_info=None,
        context_menu=[],
        subtitles=None,
    ):
        """
        Create link to playable item (wrapper function for _addDir).

        :param name: The name of the folder
        :param action_key: Action to take
        :param action_value: Parameter to action
        :param image: Image to use for the item
        """
        self._add_dir(
            name=name,
            action_key=action_key,
            action_value=action_value,
            image=image,
            is_folder=False,
            extra_info=extra_info,
            context_menu=context_menu,
            subtitles=subtitles,
        )

    def add_unselectable_item(self, name, image, extra_info=None):
        unselectable_name = "[COLOR red]{0}[/COLOR]".format(name)
        self._add_dir(
            name=unselectable_name,
            image=image,
            selectable=False,
            extra_info=extra_info,
        )

    def add_program_dir(self, program):
        title = program["title"] or program["foreign_title"]
        if title:
            self.add_dir(
                title,
                "list_program_episodes",
                str(program["id"]),
                image=program["image"],
            )

    def add_program_episode(self, program, episode):
        if episode["title"] and program["title"]:
            title = "{0} - {1}".format(program["title"], episode["title"])
        elif episode["title"]:
            title = episode["title"]
        else:
            title = program["title"]
        context_menu = []
        if program["web_available_episodes"] > 1:
            context_menu.append(
                (
                    sarpur.getLocalizedString(30910),
                    "XBMC.Container.Update({0})".format(
                        self._get_url(
                            "list_program_episodes",
                            str(program["id"]),
                            title,
                        )
                    ),
                )
            )
        self.add_item(
            title,
            "play_video",
            episode["file"],
            image=program.get("image"),
            subtitles=[episode.get("subtitles_url")],
            extra_info={
                "Episode": program["episodes"][0]["number"],
                "Premiered": strptime(
                    program["episodes"][0]["firstrun"],
                    "%Y-%m-%dT%H:%M:%S",
                ).strftime("%d.%m.%Y"),
                "TotalEpisodes": program["web_available_episodes"],
                "Plot": "\n".join(program.get("description", [])),
            },
            context_menu=context_menu,
        )

    @staticmethod
    def info_box(title, message):
        """
        Display a pop up message.

        :param title: The title of the pop up window
        :param message: Message you want to display to the user
        """
        xbmcgui.Dialog().ok(title, message)

    @staticmethod
    def keyboard(title):
        """
        Display a keyboard

        :param title: Name of the modal window
        :return: User's input or None
        """
        keyboard = xbmc.Keyboard("", title)
        keyboard.doModal()
        if keyboard.isConfirmed():
            return keyboard.getText().strip()

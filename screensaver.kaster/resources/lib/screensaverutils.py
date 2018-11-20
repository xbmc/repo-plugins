# -*- coding: utf-8 -*-
"""
    screensaver.kaster
    Copyright (C) 2017 enen92

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from . import kodiutils
import xbmcvfs
import xbmc
import os
import json

class ScreenSaverUtils:

    def __init__(self):
        self.images = []

    @staticmethod
    def remove_unknown_author(author):
        if "unknown" in author.lower():
            return kodiutils.get_string(32007)
        else:
            return author

    def __reset_images(self):
        self.images = []

    def __append_image(self, image):
        self.images.append(image)

    def __get_images_recursively(self, path):
        folders, files = xbmcvfs.listdir(xbmc.translatePath(path))
        for _file in files:
            self.__append_image(os.path.join(xbmc.translatePath(path), _file))
        if folders:
            for folder in folders:
                path = os.path.join(path,folder)
                self.__get_images_recursively(path)

    def get_all_images(self):
        return self.images

    def get_own_pictures(self, path):
        self.__reset_images()
        images_dict = {}

        image_file = os.path.join(xbmc.translatePath(path), "images.json")
        if xbmcvfs.exists(image_file):
            f = xbmcvfs.File(image_file)
            try:
               images_dict = json.loads(f.read())
            except ValueError:
               kodiutils.log(kodiutils.get_string(32010), xbmc.LOGERROR)
            f.close()

        self.__get_images_recursively(xbmc.translatePath(path))

        for _file in self.get_all_images():
            if _file.endswith(('.png', '.jpg', '.jpeg')):
                returned_dict = {
                    "url": _file,
                    "private": True
                }
                if images_dict:
                    for image in images_dict:
                        if "image" in image.keys() and os.path.join(xbmc.translatePath(path),image["image"]) == _file:
                            if "line1" in image.keys():
                                returned_dict["line1"] = image["line1"]
                            if "line2" in image.keys():
                                returned_dict["line2"] = image["line2"]
                yield returned_dict



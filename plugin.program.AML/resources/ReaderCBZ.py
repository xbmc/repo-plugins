# -*- coding: UTF-8 -*-

# Based on the PDF Reader Kodi addon by i96751414, licensed under the GPL 2.
# https://github.com/i96751414/plugin.image.pdfreader

import os
import re
import sys
import json
import time
import xbmc
import zlib
import base64
import shutil
import urllib

class CBXReader(PDFReader):
    def __init__(self):
        PDFReader.__init__(self)

    def read(self, path):
        if path.lower().endswith(".cbr"):
            ext = ".cbr"
        elif path.lower().endswith(".cbz"):
            ext = ".cbz"
        else:
            return False

        if os.path.isfile(path) and path.endswith(ext):
            self.file_path = path
        elif path.startswith("http"):
            self.file_path = self.download(path, ext=ext)
        else:
            self.file_path = ""

        if self.file_path:
            xbmc.executebuiltin("Extract(%s, %s)" % (self.file_path, self.temp_images()))
            return True
        else:
            return False

    def convert_to_images(self, save_path=None):
        images_path = []

        if save_path is not None and not os.path.isdir(save_path):
            save_path = None

        for f in os.listdir(self.temp_images()):
            file_path = os.path.join(self.temp_images(), f)

            if os.path.getsize(file_path) > self.min_size or not utils.check_picture_size():
                if save_path is not None:
                    shutil.copyfile(file_path, os.path.join(save_path, f))
                images_path.append(file_path)
        return images_path

    def info(self):
        return {"type": "cbx"}

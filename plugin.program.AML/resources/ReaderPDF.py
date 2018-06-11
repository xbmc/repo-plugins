# -*- coding: UTF-8 -*-

# Based on the PDF Reader Kodi addon by i96751414, licensed under the GPL 2.
# https://github.com/i96751414/plugin.image.pdfreader

# --- Python standard library ---
# from __future__ import unicode_literals
import os
import re
import sys
import json
import time
import xbmc
import zlib
import base64
import shutil

# --- AML packages ---
from utils import *
from utils_kodi import *

# File signatures
FILE_SIGNATURES = [
    {
        'type'       : 'jpg',
        'start_mark' : '\xff\xd8',
        'end_mark'   : '\xff\xd9',
        'end_fix'    : 2,
    },
    {
        'type'       : 'png',
        'start_mark' : '\x89\x50\x4E\x47',
        'end_mark'   : '\xAE\x42\x60\x82',
        'end_fix'    : 4,
    },
]

class PDFReader:
    def __init__(self, PDF_file_str, PDF_images_dir_str):
        # Path of local pdf
        self.file_path = PDF_file_str

        # Temp path
        self.images_dir = PDF_images_dir_str

        # Minimum size for each extracted picture
        self.min_size = 10000

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clean_temp()

    def info(self):
        pdf_content = self.read_contents()

        for t in FILE_SIGNATURES:
            if re.search(t['start_mark'], pdf_content) and \
               re.search(t['end_mark'], pdf_content):
                return t

        return {}

    #
    # Returns basename_noext
    #
    def name(self):
        if self.file_path == '':
            return ''

        return os.path.splitext(self.file_path)[0].replace("\\", "/").split("/")[-1]

    def read_contents(self):
        if self.file_path == '' or not os.path.isfile(self.file_path):
            return ''

        with open(self.file_path, 'rb') as fh:
            # https://docs.python.org/2/library/stdtypes.html#file.read
            # The bytes are returned as a string object.
            return fh.read()

    def get_images_dir(self):
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)

        return self.images_dir

    def convert_to_images(self):
        __debug_function = False

        # >> Creates the images path if doesn't exists
        save_path = self.get_images_dir()

        # >> If the PDF has no images return
        pdf_info = self.info()
        if pdf_info == {}:
            return []

        pdf_type   = pdf_info['type']
        start_mark = pdf_info['start_mark']
        end_mark   = pdf_info['end_mark']
        end_fix    = pdf_info['end_fix']

        name = self.name()
        if not name:
            return []

        pdf_bytes_str = self.read_contents()
        if not pdf_bytes_str:
            return []
        # log_debug('Type of pdf_bytes_str is "{0}"'.format(unicode(type(pdf_bytes_str))))

        start_fix = 0
        i = 0
        dim = 0
        i_offset = 20
        images_path = []
        while True:
            i_stream = pdf_bytes_str.find('stream', i)
            if __debug_function:
                log_debug('\n')
                log_debug('i = {0:6d} / dim = {1}'.format(i, dim))
                log_debug('i_stream = {0}'.format(i_stream))
            if i_stream < 0:
                break

            # sub_str = pdf_bytes_str[i_stream : i_stream + i_offset]
            # hex_chars = map(hex, map(ord, sub_str))
            # log_debug('sub_str {0}'.format(type(sub_str)))
            # log_debug('Hex {0}'.format(hex_chars))
            # log_debug('Raw "{0}"'.format(sub_str.decode('utf8', errors = 'ignore')))

            i_start = pdf_bytes_str.find(start_mark, i_stream, i_stream + i_offset)
            if __debug_function:
                log_debug('i_start  = {0}'.format(i_start))
            if i_start < 0:
                i = i_stream + i_offset
                continue

            i_end_stream = pdf_bytes_str.find('endstream', i_start)
            if i_end_stream < 0:
                raise Exception('Unable to find end of stream')
            i_end = pdf_bytes_str.find(end_mark, i_end_stream - i_offset)
            if i_end < 0:
                raise Exception('Unable to find end of picture')

            i_start += start_fix
            i_end += end_fix

            image = pdf_bytes_str[i_start:i_end]
            if __debug_function:
                log_debug('sys.getsizeof(image) = {0}'.format(sys.getsizeof(image)))

            # >> Using numbered thumbnails - name does not matter
            img_name = '{0}_{1:03d}.{2}'.format(name, dim, pdf_type)

            if sys.getsizeof(image) > self.min_size:
                image_path = os.path.join(save_path, img_name)
                log_debug('Writing img "{0}"'.format(image_path))
                with open(image_path, "wb") as fh:
                    fh.write(image)
                images_path.append(image_path)
                dim += 1
            i = i_end

        # with open(os.path.join(self.temp(), "names.txt"), "w") as fh:
        #     for image_path in images_path:
        #         fh.write("%s\n".format(image_path))

        return images_path

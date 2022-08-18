# -*- coding: utf-8 -*-

# Copyright (c) 2016-2020 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# Advanced MAME Launcher PDF/CBZ/CBR manual image extraction.

# --- Modules/packages in this plugin ---
from .constants import *
from .utils import *
from .db import *

# --- Kodi stuff ---
import xbmcaddon

# --- Load pdfrw module ---
import sys
addon_id = xbmcaddon.Addon().getAddonInfo('id')
sys.path.insert(0, FileName('special://home/addons').pjoin(addon_id).pjoin('pdfrw').getPath())
from pdfrw import PdfReader
from pdfrw.objects.pdfarray import PdfArray
from pdfrw.objects.pdfname import BasePdfName

# --- Python standard library ---
# NOTE String literals are needed in this file so unicode_literals cannot be defined.
#      Is this because of the PDF library???
import io
import pprint
import struct
import time
import types
import zlib
if ADDON_RUNNING_PYTHON_2:
    import StringIO
try:
    from PIL import Image
    PYTHON_PIL_AVAILABLE = True
except:
    PYTHON_PIL_AVAILABLE = False

# -------------------------------------------------------------------------------------------------
# pdfrw module code
# -------------------------------------------------------------------------------------------------
"""
See https://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python/34116472#34116472

Links:
  PDF format: http://www.adobe.com/content/dam/Adobe/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf
  CCITT Group 4: https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-T.6-198811-I!!PDF-E&type=items
  Extract images from pdf: http://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python
  Extract images coded with CCITTFaxDecode in .net: http://stackoverflow.com/questions/2641770/extracting-image-from-pdf-with-ccittfaxdecode-filter
  TIFF format and tags: http://www.awaresystems.be/imaging/tiff/faq.html
"""
def _tiff_header_for_CCITT(width, height, img_size, CCITT_group = 4):
    tiff_header_struct = '<' + '2s' + 'H' + 'L' + 'H' + 'HHLL' * 8 + 'H'

    return struct.pack(
       tiff_header_struct,
       'II',  # Byte order indication: Little endian
       42,  # Version number (always 42)
       8,  # Offset to first IFD
       8,  # Number of tags in IFD
       256, 4, 1, width,  # ImageWidth, LONG, 1, width
       257, 4, 1, height,  # ImageLength, LONG, 1, lenght
       258, 3, 1, 1,  # BitsPerSample, SHORT, 1, 1
       259, 3, 1, CCITT_group,  # Compression, SHORT, 1, 4 = CCITT Group 4 fax encoding
       262, 3, 1, 0,  # Threshholding, SHORT, 1, 0 = WhiteIsZero
       273, 4, 1, struct.calcsize(tiff_header_struct),  # StripOffsets, LONG, 1, len of header
       278, 4, 1, height,  # RowsPerStrip, LONG, 1, lenght
       279, 4, 1, img_size,  # StripByteCounts, LONG, 1, size of image
       0  # last IFD
   )

# Extracs an image from an xobj_dic object.
# Returns a PIL image object or None
def _extract_image_from_XObject(xobj_dic):
    log_debug('extract_image_from_XObject() Initialising ...')

    # --- Get image type and parameters ---
    num_filters = 0
    filter_list = []
    if type(xobj_dic['/Filter']) is PdfArray:
        # log_info('Filter list = "{}"'.format(text_type(xobj_dic['/Filter'])))
        for filter_name in xobj_dic['/Filter']:
            filter_list.append(filter_name)
        num_filters = len(xobj_dic['/Filter'])
    elif type(xobj_dic['/Filter']) is BasePdfName:
        num_filters = 1
        filter_list.append(xobj_dic['/Filter'])
    elif type(xobj_dic['/Filter']) is type(None):
        log_info('type(xobj_dic[\'/Filter\']) is type(None). Skipping.')
        log_info('--- xobj_dic ---')
        log_info(pprint.pformat(xobj_dic))
        log_info('----------------')
        return None
    else:
        log_info('Unknown type(xobj_dic[\'/Filter\']) = "{}"'.format(type(xobj_dic['/Filter'])))
        raise TypeError
    color_space = xobj_dic['/ColorSpace']
    bits_per_component = xobj_dic['/BitsPerComponent']
    height = int(xobj_dic['/Height'])
    width = int(xobj_dic['/Width'])

    # --- Print info ---
    log_debug('num_filters        {}'.format(num_filters))
    for i, filter_name in enumerate(filter_list):
        log_debug('/Filter[{}]         {}'.format(i, filter_name))
    log_debug('/ColorSpace        {}'.format(color_space))
    log_debug('/BitsPerComponent  {}'.format(bits_per_component))
    log_debug('/Height            {}'.format(height))
    log_debug('/Width             {}'.format(width))

    # NOTE /Filter = /FlateDecode may be PNG images. Check for magic number.
    jpg_magic_number     = '\xff\xd8'
    jp2_magic_number     = '\x00\x00\x00\x0C\x6A\x50\x20\x20\x0D\x0A\x87\x0A'
    png_magic_number     = '\x89\x50\x4E\x47'
    gif87_magic_number   = '\x47\x49\x46\x38\x37\x61'
    gif89_magic_number   = '\x47\x49\x46\x38\x39\x61'
    tiff_LE_magic_number = '\x49\x49\x2A\x00'
    tiff_BE_magic_number = '\x4D\x4D\x00\x2A'

    # --- Check for magic numbers ---
    # See https://en.wikipedia.org/wiki/Magic_number_(programming)
    #
    if xobj_dic.stream[0:2] == jpg_magic_number:
        log_debug('JPEG magic number detected!')
    elif xobj_dic.stream[0:12] == jp2_magic_number:
        log_debug('JPEG 2000 magic number detected!')
    elif xobj_dic.stream[0:4] == png_magic_number:
        log_debug('PNG magic number detected!')
    elif xobj_dic.stream[0:6] == gif87_magic_number:
        log_debug('GIF87a magic number detected!')
    elif xobj_dic.stream[0:6] == gif89_magic_number:
        log_debug('GIF89a magic number detected!')
    elif xobj_dic.stream[0:4] == tiff_LE_magic_number:
        log_debug('TIFF little endian magic number detected!')
    elif xobj_dic.stream[0:4] == tiff_BE_magic_number:
        log_debug('TIFF big endian magic number detected!')
    else:
        log_debug('Not known image magic number')

    # --- JPEG and JPEG 2000 embedded images ---
    img = None
    if num_filters == 1 and filter_list[0] == '/DCTDecode':
        log_debug('extract_image_from_XObject() Converting JPG into PIL IMG (/DCTDecode)')
        memory_f = StringIO.StringIO(xobj_dic.stream)
        img = Image.open(memory_f)

    elif num_filters == 2 and filter_list[0] == '/FlateDecode' and filter_list[1] == '/DCTDecode':
        log_debug('extract_image_from_XObject() Converting JPG into PIL IMG (/DCTDecode)')
        # First decompress /FlateDecode
        contents_plain = zlib.decompress(xobj_dic.stream)
        memory_f = StringIO.StringIO(contents_plain)
        img = Image.open(memory_f)

    elif num_filters == 1 and filter_list[0] == '/JPXDecode':
        log_debug('extract_image_from_XObject() Converting JPEG 2000 into PIL IMG (/JPXDecode)')
        memory_f = StringIO.StringIO(xobj_dic.stream)
        img = Image.open(memory_f)

    # --- RGB images with FlateDecode ---
    elif num_filters == 1 and color_space == '/DeviceRGB' and filter_list[0] == '/FlateDecode':
        log_debug('extract_image_from_XObject() Saving /DeviceRGB /FlateDecode image')
        contents_plain = zlib.decompress(xobj_dic.stream)
        img = Image.frombytes('RGB', (width, height), contents_plain)

    # --- Monochrome images, 1 bit per pixel, /Filter /FlateDecode ---
    elif num_filters == 1 and color_space == '/DeviceGray' and filter_list[0] == '/FlateDecode':
        log_debug('extract_image_from_XObject() Saving monochrome /FlateDecode')
        contents_plain = zlib.decompress(xobj_dic.stream)
        img = Image.frombytes('1', (width, height), contents_plain)

    # --- Monochrome images, 1 bit per pixel, /Filter /CCITTFaxDecode (TIFF) ---
    # WARNING FOR SOME REASON THIS CODEC DOES NOT WORK OK YET.
    #         For example, avsp.pdf from ArcadeDB images do not decompress correctly
    elif num_filters == 1 and color_space == '/DeviceGray' and filter_list[0] == '/CCITTFaxDecode':
        """
        The  CCITTFaxDecode filter decodes image data that has been encoded using
        either Group 3 or Group 4 CCITT facsimile (fax) encoding. CCITT encoding is
        designed to achieve efficient compression of monochrome (1 bit per pixel) image
        data at relatively low resolutions, and so is useful only for bitmap image data, not
        for color images, grayscale images, or general data.

        K < 0 --- Pure two-dimensional encoding (Group 4)
        K = 0 --- Pure one-dimensional encoding (Group 3, 1-D)
        K > 0 --- Mixed one- and two-dimensional encoding (Group 3, 2-D)
        """
        log_debug('extract_image_from_XObject() Saving monochrome /CCITTFaxDecode')
        log_debug('/DecodeParms =')
        log_debug('{}'.format(pprint.pformat(xobj_dic['/DecodeParms'])))
        K = int(xobj_dic['/DecodeParms']['/K'])
        if K == -1: CCITT_group = 4
        else:       CCITT_group = 3
        img_size = len(xobj_dic.stream)
        tiff_header = _tiff_header_for_CCITT(width, height, img_size, CCITT_group)
        log_debug('img_size = {0:d}'.format(img_size))
        log_debug('CCITT_group = {0:d}'.format(CCITT_group))
        log_debug('type(tiff_header) = {}'.format(type(tiff_header)))
        log_debug('type(xobj_dic.stream) = {}'.format(type(xobj_dic.stream)))

        # DEBUG file write
        # with io.open('test.tiff', 'wb') as img_file:
        #     img_file.write(tiff_header + xobj_dic.stream)

        # Open memory file with PIL
        # img = Image.open(StringIO.StringIO(tiff_header + xobj_dic.stream))

    else:
        log_debug('Unrecognised image type/filter. It cannot be extracted. Skipping.')

    return img

# OLD CODE (extracts all pages).
# Keep this function for future reference.
def manuals_extract_pages_pdfrw(status_dic, PDF_file_FN, img_dir_FN):
    # --- Load and parse PDF ---
    reader = PdfReader(PDF_file_FN.getPath())
    log_info('PDF file "{}"'.format(PDF_file_FN.getPath()))
    log_info('PDF has {} pages'.format(reader.numPages))

    # --- Iterate page by page ---
    image_counter = 0
    for page_index, page in enumerate(reader.pages):
        # --- Iterate /Resources in page ---
        # log_debug('###### Processing page {} ######'.format(page_index))
        resource_dic = page['/Resources']
        for r_name in resource_dic:
            resource = resource_dic[r_name]
            # Skip non /XObject keys in /Resources
            if r_name != '/XObject': continue

            # DEBUG dump /XObjects dictionary
            # print('--- resource ---')
            # pprint(resource)
            # print('----------------')

            # Traverse /XObject dictionary data. Each page may have 0, 1 or more /XObjects
            # If there is more than 1 image in the page there could be more than 1 /XObject.
            # Some /XObjects are not images, for example, /Subtype = /Form.
            # NOTE Also, images may be inside the /Resources of a /From /XObject.
            img_index = 0
            for xobj_name in resource:
                xobj_dic = resource[xobj_name]
                xobj_type = xobj_dic['/Type']
                xobj_subtype = xobj_dic['/Subtype']
                # >> Skip XObject forms
                if xobj_subtype == '/Form':
                    # >> NOTE There could be an image /XObject in the /From : /Resources dictionary.
                    log_info('Skipping /Form /XObject')
                    log_info('--- xobj_dic ---')
                    log_info(pprint.pformat(xobj_dic))
                    log_info('----------------')
                    continue

                # --- Print info ---
                log_debug('------ Page {0:02d} Image {1:02d} ------'.format(page_index, img_index))
                log_debug('xobj_name     {}'.format(xobj_name))
                log_debug('xobj_type     {}'.format(xobj_type))
                log_debug('xobj_subtype  {}'.format(xobj_subtype))
                # log_debug('--- xobj_dic ---')
                # log_debug(pprint.pformat(xobj_dic))
                # log_debug('----------------')

                # --- Extract image ---
                # Returns a PIL image object or None
                img = _extract_image_from_XObject(xobj_dic)

                # --- Save image ---
                if img:
                    img_basename_str = 'Image_page{0:02d}_img{1:02d}.png'.format(i, img_index)
                    img_path_str = img_dir_FN.pjoin(img_basename_str).getPath()
                    log_debug('Saving IMG "{}"'.format(img_path_str))
                    img.save(img_path_str, 'PNG')
                    image_counter += 1
                    img_index += 1
                else:
                    log_warning('Error extracting image from /XObject')
    log_info('Extracted {} images from PDF'.format(image_counter))

    # --- Initialise status_dic ---
    status_dic['manFormat'] = 'PDF'
    status_dic['numImages'] = image_counter

# -------------------------------------------------------------------------------------------------
# Main function to extract images
# -------------------------------------------------------------------------------------------------
#
# Creates status_dic.
# If JSON INFO files does not exists then rendering is needed.
# If JSON INFO file exists, then compare manual mtime with image extraction time.
# Returns True if extraction is needed, False otherwise.
def manuals_check_img_extraction_needed(PDF_file_FN, img_dir_FN):
    log_debug('manuals_check_img_extraction_needed() Starting ...')
    status_dic = {
        'extraction_needed' : True,
        'manFormat' : 'PDF',
        'numPages' : 0,
        'numImages' : 0,
        # This is a list of lists because each image can have more than 1 filter.
        'imgFilterList' : [],
    }

    # Does the JSON INFO file exists?
    rom_name = PDF_file_FN.getBaseNoExt()
    info_FN = img_dir_FN.pjoin(rom_name + '.json')
    log_info('manuals_check_img_extraction_needed() Info file "{}"'.format(info_FN.getPath()))
    if not info_FN.exists():
        status_dic['extraction_needed'] = True
        return status_dic

    # JSON INFO file exists. Open JSON file and check timestamps.
    info_dic = utils_load_JSON_file(info_FN.getPath())
    man_file_mtime = PDF_file_FN.getmtime()
    if man_file_mtime > info_dic['IMG_timestamp']:
        status_dic['extraction_needed'] = True
        status_dic['manFormat'] = info_dic['manFormat']
        status_dic['numPages'] = info_dic['numPages']
        status_dic['numImages'] = info_dic['numImages']
        status_dic['imgFilterList'] = info_dic['imgFilterList']
    else:
        status_dic['extraction_needed'] = False

    return status_dic

# Global variables for the PDF manual reader.
PDF_reader = None

# This function receives a PDF file in man_file_FN.
# Directory img_dir_FN must exist when calling this function.
#
# Mutates status_dic:
#   status_dic['abort_extraction'] = bool  True is extraction should be aborted
#   status_dic['manFormat'] = string  ['PDF', 'CBZ', 'CBR']
#   status_dic['numPages'] = int
#   status_dic['numImages'] = int
#
# Creates a JSON file with the timestamp of the extraction and timestamp of the manual file.
def manuals_open_PDF_file(status_dic, PDF_file_FN, img_dir_FN):
    global PDF_reader
    log_debug('manuals_open_PDF_file() Starting ...')

    # --- Load and parse PDF ---
    log_info('PDF file "{}"'.format(PDF_file_FN.getPath()))
    PDF_reader = PdfReader(PDF_file_FN.getPath())
    log_info('PDF has {} pages'.format(PDF_reader.numPages))

    # --- Update status_dic ---
    status_dic['abort_extraction'] = False
    status_dic['manFormat'] = 'PDF'
    status_dic['numPages'] = PDF_reader.numPages
    status_dic['numImages'] = 0

def manuals_close_PDF_file():
    global PDF_reader

    PDF_reader = None

# Create JSON INFO file. Call this function after the PDF images have been extracted.
def manuals_create_INFO_file(status_dic, PDF_file_FN, img_dir_FN):
    rom_name = PDF_file_FN.getBaseNoExt()
    info_FN = img_dir_FN.pjoin(rom_name + '.json')
    log_info('manuals_create_INFO_file() Info file "{}"'.format(info_FN.getPath()))
    PDF_timestamp = PDF_file_FN.getmtime()
    IMG_timestamp = time.time()

    info_dic = {
        # Fields copied from status_dic
        'manFormat' : status_dic['manFormat'],
        'numPages' : status_dic['numPages'],
        'numImages' : status_dic['numImages'],
        'imgFilterList' : status_dic['imgFilterList'],
        # Fields only in JSON INFO file
        'PDF_path' : PDF_file_FN.getPath(),
        'IMG_path' : img_dir_FN.getPath(),
        'PDF_timestamp' : PDF_timestamp,
        'PDF_time' : time.strftime('%a %d %b %Y %H:%M:%S', time.localtime(PDF_timestamp)),
        'IMG_timestamp' : IMG_timestamp,
        'IMG_time' : time.strftime('%a %d %b %Y %H:%M:%S', time.localtime(IMG_timestamp)),
    }
    utils_write_JSON_file_pprint(info_FN.getPath(), info_dic)

# Gets a list of filters (codecs) used in the PDF file.
# manuals_extract_PDF_page() is based on this function. In other words, this function has
# debug code and manuals_extract_PDF_page() is a cleaner version.
def manuals_get_PDF_filter_list(status_dic, man_file_FN, img_dir_FN):
    # List of lists because each image may have more than 1 filter.
    img_filter_list_list = []

    # --- Iterate PDF pages ---
    for page_index, page in enumerate(PDF_reader.pages):
        # log_debug('###### Processing page {} ######'.format(page_index))
        resource_dic = page['/Resources']
        # --- Iterate /Resources in page ---
        for resource_name in resource_dic:
            resource = resource_dic[resource_name]
            # Skip non /XObject keys in /Resources
            if resource_name != '/XObject': continue

            # DEBUG dump /XObjects dictionary
            # print('--- resource ---')
            # pprint(resource)
            # print('----------------')

            # Traverse /XObject dictionary data. Each page may have 0, 1 or more /XObjects
            # If there is more than 1 image in the page there could be more than 1 /XObject.
            # Some /XObjects are not images, for example, /Subtype = /Form.
            # Also, images may be inside the /Resources of a /From /XObject.
            img_index = 0
            for xobj_name in resource:
                xobj_dic = resource[xobj_name]
                xobj_type = xobj_dic['/Type']
                xobj_subtype = xobj_dic['/Subtype']
                # Skip XObject forms
                if xobj_subtype == '/Form':
                    # NOTE There could be an image /XObject in the /From : /Resources dictionary.
                    log_info('Skipping /Form /XObject')
                    log_info('--- xobj_dic ---')
                    log_info(pprint.pformat(xobj_dic))
                    log_info('----------------')
                    continue

                # --- Print info ---
                log_debug('------ Page {0:02d} Image {1:02d} ------'.format(page_index, img_index))
                log_debug('xobj_name     {}'.format(xobj_name))
                log_debug('xobj_type     {}'.format(xobj_type))
                log_debug('xobj_subtype  {}'.format(xobj_subtype))
                # log_debug('--- xobj_dic ---')
                # log_debug(pprint.pformat(xobj_dic))
                # log_debug('----------------')

                # --- Extract image filters ---
                num_filters = 0
                filter_list = []
                if type(xobj_dic['/Filter']) is PdfArray:
                    # log_info('Filter list = "{}"'.format(text_type(xobj_dic['/Filter'])))
                    for filter_name in xobj_dic['/Filter']:
                        filter_list.append(filter_name)
                    num_filters = len(xobj_dic['/Filter'])
                elif type(xobj_dic['/Filter']) is BasePdfName:
                    num_filters = 1
                    filter_list.append(xobj_dic['/Filter'])
                elif type(xobj_dic['/Filter']) is type(None):
                    log_info('type(xobj_dic[\'/Filter\']) is type(None). Skipping.')
                    log_info('--- xobj_dic ---')
                    log_info(pprint.pformat(xobj_dic))
                    log_info('----------------')
                else:
                    log_info('Unknown type(xobj_dic[\'/Filter\']) = "{}"'.format(type(xobj_dic['/Filter'])))
                    raise TypeError
                img_filter_list_list.append(' and '.join(filter_list))
                img_index += 1
    status_dic['imgFilterList'] = img_filter_list_list

# Extracts images in a PDF page.
def manuals_extract_PDF_page(status_dic, man_file_FN, img_dir_FN, page_index):
    # --- Get page object ---
    page = PDF_reader.pages[page_index]

    # --- Iterate /Resources in page ---
    image_counter = 0
    log_debug('###### Processing page {} ######'.format(page_index))
    resource_dic = page['/Resources']
    for resource_name in resource_dic:
        resource = resource_dic[resource_name]
        # Skip non /XObject keys in /Resources
        if resource_name != '/XObject': continue

        # Traverse /XObject dictionary data.
        img_index = 0
        for xobj_name in resource:
            xobj_dic = resource[xobj_name]
            xobj_type = xobj_dic['/Type']
            xobj_subtype = xobj_dic['/Subtype']
            # Skip XObject forms
            if xobj_subtype == '/Form':
                # NOTE There could be an image /XObject in the /From : /Resources dictionary.
                log_info('Skipping /Form /XObject')
                log_info('--- xobj_dic ---')
                log_info(pprint.pformat(xobj_dic))
                log_info('----------------')
                continue

            # --- Print info ---
            log_debug('------ Page {0:02d} Image {1:02d} ------'.format(page_index, img_index))
            log_debug('xobj_name     {}'.format(xobj_name))
            log_debug('xobj_type     {}'.format(xobj_type))
            log_debug('xobj_subtype  {}'.format(xobj_subtype))

            # --- Extract image ---
            # Returns a PIL image object or None
            img = _extract_image_from_XObject(xobj_dic)

            # --- Save image ---
            if img:
                img_basename_str = 'Image_page{0:02d}_img{1:02d}.png'.format(page_index, img_index)
                img_path_str = img_dir_FN.pjoin(img_basename_str).getPath()
                log_debug('Saving IMG "{}"'.format(img_path_str))
                img.save(img_path_str, 'PNG')
                image_counter += 1
                img_index += 1
            else:
                log_warning('Error extracting image from /XObject')
    # --- Update info ---
    status_dic['numImages'] += image_counter
    log_info('PDF page {} extracted {} images'.format(page_index, image_counter))

#!/usr/bin/env python

'''
usage:   extract_images.py <some.pdf>

Locates Image XObjects within the PDF and extracts the images in PNG format.
Extracted images will be named Image_pageXX_imgYY.png

'''

import sys
import os
import zlib
from PIL import Image
import pprint
import types
import StringIO
import struct

# --- Add pdfrw module to Python path ---
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir  = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

# --- Import pdrfw stuff ---
from pdfrw import PdfReader
from pdfrw.objects.pdfarray import PdfArray
from pdfrw.objects.pdfname import BasePdfName

# --- Compatibilty with AEL/AML logging functions ---
def log_debug(str):
    print(str)

def log_info(str):
    print(str)

def log_warning(str):
    print(str)

"""
See https://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python/34116472#34116472

Links:
  PDF format: http://www.adobe.com/content/dam/Adobe/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf
  CCITT Group 4: https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-T.6-198811-I!!PDF-E&type=items
  Extract images from pdf: http://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python
  Extract images coded with CCITTFaxDecode in .net: http://stackoverflow.com/questions/2641770/extracting-image-from-pdf-with-ccittfaxdecode-filter
  TIFF format and tags: http://www.awaresystems.be/imaging/tiff/faq.html
                        https://www.fileformat.info/format/tiff/egff.htm
                        
  If the PDF option EncodedByteAlign is true I think the TIFF Tag T4Options must be set.
  See https://www.awaresystems.be/imaging/tiff/tifftags/t4options.html
  The PDF EncodedByteAlign seems to be called GROUP3OPT_FILLBITS in libtiff. However, for some reason
  GROUP3OPT_FILLBITS is only supported for the Group3 decoder and not for the Group4 decoder.
  SumatraPDF uses MuPDF and is able to decode avsp.pdf images. MuPDF has a internal Group4 decoder.
  I believe Pyton PIL relies on libtiff.
"""
def _tiff_header_for_CCITT(width, height, img_size, CCITT_group = 4):
    num_tags = 8
    tiff_header_struct = '<' + '2s' + 'H' + 'L' + 'H' + 'HHLL' * num_tags + 'H'

    # >> Does not work as expected ...
    # 292, 4, 1, 4,  # TIFFTAG_GROUP3OPTIONS, LONG, 1, TIFF Tag T4Options
    return struct.pack(
       tiff_header_struct,
       'II',  # Byte order indication: Little endian
       42,  # Version number (always 42)
       8,  # Offset to first IFD
       num_tags,  # Number of tags in IFD
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

#
# Extracs an image from an xobj_dic object.
# Returns a PIL image object or None
#
def _extract_image_from_XObject(xobj_dic):
    log_debug('extract_image_from_XObject() Initialising ...')

    # --- Get image type and parameters ---
    num_filters = 0
    filter_list = []
    if type(xobj_dic['/Filter']) is PdfArray:
        # log_info('Filter list = "{0}"'.format(unicode(xobj_dic['/Filter'])))
        for filter_name in xobj_dic['/Filter']:
            filter_list.append(filter_name)
        num_filters = len(xobj_dic['/Filter'])
    elif type(xobj_dic['/Filter']) is BasePdfName:
        num_filters = 1
        filter_list.append(xobj_dic['/Filter'])
    elif type(xobj_dic['/Filter']) is types.NoneType:
        log_info('type(xobj_dic[\'/Filter\']) is types.NoneType. Skipping.')
        log_info('--- xobj_dic ---')
        log_info(pprint.pformat(xobj_dic))
        log_info('----------------')
        return None
    else:
        log_info('Unknown type(xobj_dic[\'/Filter\']) = "{0}"'.format(type(xobj_dic['/Filter'])))
        sys.exit(1)
    color_space = xobj_dic['/ColorSpace']
    bits_per_component = xobj_dic['/BitsPerComponent']
    height = int(xobj_dic['/Height'])
    width = int(xobj_dic['/Width'])

    # --- Print info ---
    log_debug('num_filters        {0}'.format(num_filters))
    for i, filter_name in enumerate(filter_list):
        log_debug('/Filter[{0}]         {1}'.format(i, filter_name))
    log_debug('/ColorSpace        {0}'.format(color_space))
    log_debug('/BitsPerComponent  {0}'.format(bits_per_component))
    log_debug('/Height            {0}'.format(height))
    log_debug('/Width             {0}'.format(width))

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
        log_debug('{0}'.format(pprint.pformat(xobj_dic['/DecodeParms'])))
        K = int(xobj_dic['/DecodeParms']['/K'])
        if K == -1: CCITT_group = 4
        else:       CCITT_group = 3
        img_size = len(xobj_dic.stream)
        tiff_header = _tiff_header_for_CCITT(width, height, img_size, CCITT_group)
        log_debug('img_size = {0:d}'.format(img_size))
        log_debug('CCITT_group = {0:d}'.format(CCITT_group))
        log_debug('type(tiff_header) = {0}'.format(type(tiff_header)))
        log_debug('type(xobj_dic.stream) = {0}'.format(type(xobj_dic.stream)))

        # >> DEBUG file write
        # with open('test.tiff', 'wb') as img_file:
        #     img_file.write(tiff_header + xobj_dic.stream)

        # >> Open memory file with PIL
        # img = Image.open(StringIO.StringIO(tiff_header + xobj_dic.stream))

    else:
        log_debug('Unrecognised image type/filter. It cannot be extracted. Skipping.')

    return img

# --- Main ---
inpfn, = sys.argv[1:]
reader = PdfReader(inpfn)
log_info('PDF file "{0}"'.format(inpfn))
log_info('PDF has {0} pages'.format(reader.numPages))

# --- Iterate page by page ---
image_counter = 0
for i, page in enumerate(reader.pages):
    # --- Iterate /Resources in page ---
    # log_debug('###### Processing page {0} ######'.format(i))
    resource_dic = page['/Resources']
    for r_name, resource in resource_dic.iteritems():
        # >> Skip non /XObject keys in /Resources
        if r_name != '/XObject': continue

        # >> DEBUG dump /XObjects dictionary
        # print('--- resource ---')
        # pprint(resource)
        # print('----------------')

        # >> Traverse /XObject dictionary data. Each page may have 0, 1 or more /XObjects
        # >> If there is more than 1 image in the page there could be more than 1 /XObject.
        # >> Some /XObjects are not images, for example, /Subtype = /Form.
        # >> NOTE Also, images may be inside the /Resources of a /From /XObject.
        img_index = 0
        for xobj_name, xobj_dic in resource.iteritems():
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
            img_fname = 'Image_page{0:02d}_img{1:02d}.png'.format(i, img_index)

            # --- Print info ---
            log_debug('------ Page {0:02d} Image {1:02d} ------'.format(i, img_index))
            log_debug('xobj_name     {0}'.format(xobj_name))
            log_debug('xobj_type     {0}'.format(xobj_type))
            log_debug('xobj_subtype  {0}'.format(xobj_subtype))
            # log_debug('--- xobj_dic ---')
            # log_debug(pprint.pformat(xobj_dic))
            # log_debug('----------------')

            # --- Extract image ---
            # Returns a PIL image object or None
            img = _extract_image_from_XObject(xobj_dic)

            # --- Save image ---
            if img:
                img.save(img_fname, 'PNG')
                image_counter += 1
                img_index += 1
            else:
                log_warning('Error extracting image from /XObject')
log_info('Extracted {0} images from PDF'.format(image_counter))

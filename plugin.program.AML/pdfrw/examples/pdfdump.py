#!/usr/bin/env python

'''
usage:   pdfdump.py <some.pdf>

Test script to dump information about PDF files.

reader = PdfReader()

reader.numPages  integer
reader.pages     list of dictionaries
'''

import sys
import os
import zlib
from pprint import pprint

# --- Add pdfrw module to Python path ---
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir  = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

# --- Import pdrfw stuff ---
from pdfrw import PdfReader, PdfWriter
from pdfrw.objects.pdfarray import PdfArray
from pdfrw.objects.pdfname import BasePdfName

# --- Main ---
inpfn, = sys.argv[1:]
reader = PdfReader(inpfn)

print('Raw object printing')
print(unicode(reader))

# print('\n__dict__ print')
# print(unicode(reader.__dict__))

# print('\npprint object printing')
# pprint(reader)

print('\npprint __dict__.keys()')
pprint(reader.__dict__.keys())

print('Number of pages: {0}'.format(reader.numPages))

print('\n--- Dumping page 0 keys ---')
pprint(reader.pages[0].keys())

print('\n--- Dumping page 0 /Type ---')
pprint(reader.pages[0]['/Type'])

print('\n--- Dumping page 0 /Resources ---')
pprint(reader.pages[0]['/Resources'])

print('\n--- Dumping page 0 /MediaBox ---')
pprint(reader.pages[0]['/MediaBox'])

# Page '/Contents' is an instance of PdfDict.
# PdfDict dictionary key '/Length'
# PdfDict dictionary key '/Filter'
# PdfDict attribute 'stream' contains the possibly compressed page contents.
# PdfDict attribute 'indirect' contains a tuple with the object numbers.
print('\n--- Dumping page 0 /Contents ---')
pprint(reader.pages[0]['/Contents'])
# print(type(reader.pages[0]['/Contents']))
# print(reader.pages[0]['/Contents'].__dict__)

if not '/Filter' in reader.pages[0]['/Contents']:
    print('stream is NOT compressed')
    contents_plain = reader.pages[0]['/Contents'].stream
else:
    print('stream IS compressed')
    # For some reason '/Filter' may be a list of strings. Take first element.
    if type(reader.pages[0]['/Contents']['/Filter']) is PdfArray:
        filter = reader.pages[0]['/Contents']['/Filter'][0]
    elif type(reader.pages[0]['/Contents']['/Filter']) is BasePdfName:
        filter = reader.pages[0]['/Contents']['/Filter']
    else:
        print('Unknwon error')
        sys.exit(0)
    print('filter = "{0}"'.format(filter))

    if filter == "/FlateDecode":
        print('stream is compressed with /FlateDecode filter')
        contents_comp = reader.pages[0]['/Contents'].stream
        contents_plain = zlib.decompress(contents_comp)
        print('len(contents_comp) = {0}'.format(len(contents_comp)))
    else:
        print('Unknown /Filter "{0}"'.format(filter))
        sys.exit(0)
print('len(contents_plain) = {0}'.format(len(contents_plain)))
print('--- contents_plain ---')
sys.stdout.write('{0}'.format(contents_plain))
print('----------------------')

# pages = list(page_per_xobj(reader.pages, margin=0.5*72))
# if not pages:
#     raise IndexError("No XObjects found")

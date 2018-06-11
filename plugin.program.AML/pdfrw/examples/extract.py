#!/usr/bin/env python

'''
usage:   extract.py <some.pdf>

Locates Form XObjects and Image XObjects within the PDF,
and creates a new PDF containing these -- one per page.

Resulting file will be named extract.<some.pdf>

'''

import sys
import os

# --- Add pdfrw module to Python path ---
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir  = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

# --- Import pdrfw stuff ---
from pdfrw import PdfReader, PdfWriter
from pdfrw.findobjs import page_per_xobj

# --- Main ---
inpfn, = sys.argv[1:]
outfn = 'extract.' + os.path.basename(inpfn)
# pages = list(page_per_xobj(PdfReader(inpfn).pages, margin=0.5*72))
pages = list(page_per_xobj(PdfReader(inpfn).pages))
if not pages:
    raise IndexError("No XObjects found")
writer = PdfWriter(outfn)
writer.addpages(pages)
writer.write()

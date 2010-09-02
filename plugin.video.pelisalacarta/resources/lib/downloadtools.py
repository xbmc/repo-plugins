# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Download Tools
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
# Based on the code from VideoMonkey XBMC Plugin
#------------------------------------------------------------
from string import *
import xbmcplugin
import sys, os.path
import urllib,urllib2, filecmp
import re, random, string, shutil
import xbmc, xbmcgui
import re, os, time, datetime, traceback
import cookielib, htmlentitydefs
import socket, base64
import binascii
import md5
import xbmctools
import httplib
import gzip,StringIO
import config
import logger

entitydefs = {
    'AElig':    u'\u00C6', # latin capital letter AE = latin capital ligature AE, U+00C6 ISOlat1'
    'Aacute':   u'\u00C1', # latin capital letter A with acute, U+00C1 ISOlat1'
    'Acirc':    u'\u00C2', # latin capital letter A with circumflex, U+00C2 ISOlat1'
    'Agrave':   u'\u00C0', # latin capital letter A with grave = latin capital letter A grave, U+00C0 ISOlat1'
    'Alpha':    u'\u0391', # greek capital letter alpha, U+0391'
    'Aring':    u'\u00C5', # latin capital letter A with ring above = latin capital letter A ring, U+00C5 ISOlat1'
    'Atilde':   u'\u00C3', # latin capital letter A with tilde, U+00C3 ISOlat1'
    'Auml':     u'\u00C4', # latin capital letter A with diaeresis, U+00C4 ISOlat1'
    'Beta':     u'\u0392', # greek capital letter beta, U+0392'
    'Ccedil':   u'\u00C7', # latin capital letter C with cedilla, U+00C7 ISOlat1'
    'Chi':      u'\u03A7', # greek capital letter chi, U+03A7'
    'Dagger':   u'\u2021', # double dagger, U+2021 ISOpub'
    'Delta':    u'\u0394', # greek capital letter delta, U+0394 ISOgrk3'
    'ETH':      u'\u00D0', # latin capital letter ETH, U+00D0 ISOlat1'
    'Eacute':   u'\u00C9', # latin capital letter E with acute, U+00C9 ISOlat1'
    'Ecirc':    u'\u00CA', # latin capital letter E with circumflex, U+00CA ISOlat1'
    'Egrave':   u'\u00C8', # latin capital letter E with grave, U+00C8 ISOlat1'
    'Epsilon':  u'\u0395', # grek capital letter epsilon, U+0395'
    'Eta':      u'\u0397', # greek capital letter eta, U+0397'
    'Euml':     u'\u00CB', # latin capital letter E with diaeresis, U+00CB ISOlat1'
    'Gamma':    u'\u0393', # greek capital letter gamma, U+0393 ISOgrk3'
    'Iacute':   u'\u00CD', # latin capital letter I with acute, U+00CD ISOlat1'
    'Icirc':    u'\u00CE', # latin capital letter I with circumflex, U+00CE ISOlat1'
    'Igrave':   u'\u00CC', # latin capital letter I with grave, U+00CC ISOlat1'
    'Iota':     u'\u0399', # greek capital letter iota, U+0399'
    'Iuml':     u'\u00CF', # latin capital letter I with diaeresis, U+00CF ISOlat1'
    'Kappa':    u'\u039A', # greek capital letter kappa, U+039A'
    'Lambda':   u'\u039B', # greek capital letter lambda, U+039B ISOgrk3'
    'Mu':       u'\u039C', # greek capital letter mu, U+039C'
    'Ntilde':   u'\u00D1', # latin capital letter N with tilde, U+00D1 ISOlat1'
    'Nu':       u'\u039D', # greek capital letter nu, U+039D'
    'OElig':    u'\u0152', # latin capital ligature OE, U+0152 ISOlat2'
    'Oacute':   u'\u00D3', # latin capital letter O with acute, U+00D3 ISOlat1'
    'Ocirc':    u'\u00D4', # latin capital letter O with circumflex, U+00D4 ISOlat1'
    'Ograve':   u'\u00D2', # latin capital letter O with grave, U+00D2 ISOlat1'
    'Omega':    u'\u03A9', # greek capital letter omega, U+03A9 ISOgrk3'
    'Omicron':  u'\u039F', # greek capital letter omicron, U+039F'
    'Oslash':   u'\u00D8', # latin capital letter O with stroke = latin capital letter O slash, U+00D8 ISOlat1'
    'Otilde':   u'\u00D5', # latin capital letter O with tilde, U+00D5 ISOlat1'
    'Ouml':     u'\u00D6', # latin capital letter O with diaeresis, U+00D6 ISOlat1'
    'Phi':      u'\u03A6', # greek capital letter phi, U+03A6 ISOgrk3'
    'Pi':       u'\u03A0', # greek capital letter pi, U+03A0 ISOgrk3'
    'Prime':    u'\u2033', # double prime = seconds = inches, U+2033 ISOtech'
    'Psi':      u'\u03A8', # greek capital letter psi, U+03A8 ISOgrk3'
    'Rho':      u'\u03A1', # greek capital letter rho, U+03A1'
    'Scaron':   u'\u0160', # latin capital letter S with caron, U+0160 ISOlat2'
    'Sigma':    u'\u03A3', # greek capital letter sigma, U+03A3 ISOgrk3'
    'THORN':    u'\u00DE', # latin capital letter THORN, U+00DE ISOlat1'
    'Tau':      u'\u03A4', # greek capital letter tau, U+03A4'
    'Theta':    u'\u0398', # greek capital letter theta, U+0398 ISOgrk3'
    'Uacute':   u'\u00DA', # latin capital letter U with acute, U+00DA ISOlat1'
    'Ucirc':    u'\u00DB', # latin capital letter U with circumflex, U+00DB ISOlat1'
    'Ugrave':   u'\u00D9', # latin capital letter U with grave, U+00D9 ISOlat1'
    'Upsilon':  u'\u03A5', # greek capital letter upsilon, U+03A5 ISOgrk3'
    'Uuml':     u'\u00DC', # latin capital letter U with diaeresis, U+00DC ISOlat1'
    'Xi':       u'\u039E', # greek capital letter xi, U+039E ISOgrk3'
    'Yacute':   u'\u00DD', # latin capital letter Y with acute, U+00DD ISOlat1'
    'Yuml':     u'\u0178', # latin capital letter Y with diaeresis, U+0178 ISOlat2'
    'Zeta':     u'\u0396', # greek capital letter zeta, U+0396'
    'aacute':   u'\u00E1', # latin small letter a with acute, U+00E1 ISOlat1'
    'acirc':    u'\u00E2', # latin small letter a with circumflex, U+00E2 ISOlat1'
    'acute':    u'\u00B4', # acute accent = spacing acute, U+00B4 ISOdia'
    'aelig':    u'\u00E6', # latin small letter ae = latin small ligature ae, U+00E6 ISOlat1'
    'agrave':   u'\u00E0', # latin small letter a with grave = latin small letter a grave, U+00E0 ISOlat1'
    'alefsym':  u'\u2135', # alef symbol = first transfinite cardinal, U+2135 NEW'
    'alpha':    u'\u03B1', # greek small letter alpha, U+03B1 ISOgrk3'
    'amp':      u'\u0026', # ampersand, U+0026 ISOnum'
    'and':      u'\u2227', # logical and = wedge, U+2227 ISOtech'
    'ang':      u'\u2220', # angle, U+2220 ISOamso'
    'aring':    u'\u00E5', # latin small letter a with ring above = latin small letter a ring, U+00E5 ISOlat1'
    'asymp':    u'\u2248', # almost equal to = asymptotic to, U+2248 ISOamsr'
    'atilde':   u'\u00E3', # latin small letter a with tilde, U+00E3 ISOlat1'
    'auml':     u'\u00E4', # latin small letter a with diaeresis, U+00E4 ISOlat1'
    'bdquo':    u'\u201E', # double low-9 quotation mark, U+201E NEW'
    'beta':     u'\u03B2', # greek small letter beta, U+03B2 ISOgrk3'
    'brvbar':   u'\u00A6', # broken bar = broken vertical bar, U+00A6 ISOnum'
    'bull':     u'\u2022', # bullet = black small circle, U+2022 ISOpub'
    'cap':      u'\u2229', # intersection = cap, U+2229 ISOtech'
    'ccedil':   u'\u00E7', # latin small letter c with cedilla, U+00E7 ISOlat1'
    'cedil':    u'\u00B8', # cedilla = spacing cedilla, U+00B8 ISOdia'
    'cent':     u'\u00A2', # cent sign, U+00A2 ISOnum'
    'chi':      u'\u03C7', # greek small letter chi, U+03C7 ISOgrk3'
    'circ':     u'\u02C6', # modifier letter circumflex accent, U+02C6 ISOpub'
    'clubs':    u'\u2663', # black club suit = shamrock, U+2663 ISOpub'
    'cong':     u'\u2245', # approximately equal to, U+2245 ISOtech'
    'copy':     u'\u00A9', # copyright sign, U+00A9 ISOnum'
    'crarr':    u'\u21B5', # downwards arrow with corner leftwards = carriage return, U+21B5 NEW'
    'cup':      u'\u222A', # union = cup, U+222A ISOtech'
    'curren':   u'\u00A4', # currency sign, U+00A4 ISOnum'
    'dArr':     u'\u21D3', # downwards double arrow, U+21D3 ISOamsa'
    'dagger':   u'\u2020', # dagger, U+2020 ISOpub'
    'darr':     u'\u2193', # downwards arrow, U+2193 ISOnum'
    'deg':      u'\u00B0', # degree sign, U+00B0 ISOnum'
    'delta':    u'\u03B4', # greek small letter delta, U+03B4 ISOgrk3'
    'diams':    u'\u2666', # black diamond suit, U+2666 ISOpub'
    'divide':   u'\u00F7', # division sign, U+00F7 ISOnum'
    'eacute':   u'\u00E9', # latin small letter e with acute, U+00E9 ISOlat1'
    'ecirc':    u'\u00EA', # latin small letter e with circumflex, U+00EA ISOlat1'
    'egrave':   u'\u00E8', # latin small letter e with grave, U+00E8 ISOlat1'
    'empty':    u'\u2205', # empty set = null set = diameter, U+2205 ISOamso'
    'emsp':     u'\u2003', # em space, U+2003 ISOpub'
    'ensp':     u'\u2002', # en space, U+2002 ISOpub'
    'epsilon':  u'\u03B5', # greek small letter epsilon, U+03B5 ISOgrk3'
    'equiv':    u'\u2261', # identical to, U+2261 ISOtech'
    'eta':      u'\u03B7', # greek small letter eta, U+03B7 ISOgrk3'
    'eth':      u'\u00F0', # latin small letter eth, U+00F0 ISOlat1'
    'euml':     u'\u00EB', # latin small letter e with diaeresis, U+00EB ISOlat1'
    'euro':     u'\u20AC', # euro sign, U+20AC NEW'
    'exist':    u'\u2203', # there exists, U+2203 ISOtech'
    'fnof':     u'\u0192', # latin small f with hook = function = florin, U+0192 ISOtech'
    'forall':   u'\u2200', # for all, U+2200 ISOtech'
    'frac12':   u'\u00BD', # vulgar fraction one half = fraction one half, U+00BD ISOnum'
    'frac14':   u'\u00BC', # vulgar fraction one quarter = fraction one quarter, U+00BC ISOnum'
    'frac34':   u'\u00BE', # vulgar fraction three quarters = fraction three quarters, U+00BE ISOnum'
    'frasl':    u'\u2044', # fraction slash, U+2044 NEW'
    'gamma':    u'\u03B3', # greek small letter gamma, U+03B3 ISOgrk3'
    'ge':       u'\u2265', # greater-than or equal to, U+2265 ISOtech'
    'gt':       u'\u003E', # greater-than sign, U+003E ISOnum'
    'hArr':     u'\u21D4', # left right double arrow, U+21D4 ISOamsa'
    'harr':     u'\u2194', # left right arrow, U+2194 ISOamsa'
    'hearts':   u'\u2665', # black heart suit = valentine, U+2665 ISOpub'
    'hellip':   u'\u2026', # horizontal ellipsis = three dot leader, U+2026 ISOpub'
    'iacute':   u'\u00ED', # latin small letter i with acute, U+00ED ISOlat1'
    'icirc':    u'\u00EE', # latin small letter i with circumflex, U+00EE ISOlat1'
    'iexcl':    u'\u00A1', # inverted exclamation mark, U+00A1 ISOnum'
    'igrave':   u'\u00EC', # latin small letter i with grave, U+00EC ISOlat1'
    'image':    u'\u2111', # blackletter capital I = imaginary part, U+2111 ISOamso'
    'infin':    u'\u221E', # infinity, U+221E ISOtech'
    'int':      u'\u222B', # integral, U+222B ISOtech'
    'iota':     u'\u03B9', # greek small letter iota, U+03B9 ISOgrk3'
    'iquest':   u'\u00BF', # inverted question mark = turned question mark, U+00BF ISOnum'
    'isin':     u'\u2208', # element of, U+2208 ISOtech'
    'iuml':     u'\u00EF', # latin small letter i with diaeresis, U+00EF ISOlat1'
    'kappa':    u'\u03BA', # greek small letter kappa, U+03BA ISOgrk3'
    'lArr':     u'\u21D0', # leftwards double arrow, U+21D0 ISOtech'
    'lambda':   u'\u03BB', # greek small letter lambda, U+03BB ISOgrk3'
    'lang':     u'\u2329', # left-pointing angle bracket = bra, U+2329 ISOtech'
    'laquo':    u'\u00AB', # left-pointing double angle quotation mark = left pointing guillemet, U+00AB ISOnum'
    'larr':     u'\u2190', # leftwards arrow, U+2190 ISOnum'
    'lceil':    u'\u2308', # left ceiling = apl upstile, U+2308 ISOamsc'
    'ldquo':    u'\u201C', # left double quotation mark, U+201C ISOnum'
    'le':       u'\u2264', # less-than or equal to, U+2264 ISOtech'
    'lfloor':   u'\u230A', # left floor = apl downstile, U+230A ISOamsc'
    'lowast':   u'\u2217', # asterisk operator, U+2217 ISOtech'
    'loz':      u'\u25CA', # lozenge, U+25CA ISOpub'
    'lrm':      u'\u200E', # left-to-right mark, U+200E NEW RFC 2070'
    'lsaquo':   u'\u2039', # single left-pointing angle quotation mark, U+2039 ISO proposed'
    'lsquo':    u'\u2018', # left single quotation mark, U+2018 ISOnum'
    'lt':       u'\u003C', # less-than sign, U+003C ISOnum'
    'macr':     u'\u00AF', # macron = spacing macron = overline = APL overbar, U+00AF ISOdia'
    'mdash':    u'\u2014', # em dash, U+2014 ISOpub'
    'micro':    u'\u00B5', # micro sign, U+00B5 ISOnum'
    'middot':   u'\u00B7', # middle dot = Georgian comma = Greek middle dot, U+00B7 ISOnum'
    'minus':    u'\u2212', # minus sign, U+2212 ISOtech'
    'mu':       u'\u03BC', # greek small letter mu, U+03BC ISOgrk3'
    'nabla':    u'\u2207', # nabla = backward difference, U+2207 ISOtech'
    'nbsp':     u'\u00A0', # no-break space = non-breaking space, U+00A0 ISOnum'
    'ndash':    u'\u2013', # en dash, U+2013 ISOpub'
    'ne':       u'\u2260', # not equal to, U+2260 ISOtech'
    'ni':       u'\u220B', # contains as member, U+220B ISOtech'
    'not':      u'\u00AC', # not sign, U+00AC ISOnum'
    'notin':    u'\u2209', # not an element of, U+2209 ISOtech'
    'nsub':     u'\u2284', # not a subset of, U+2284 ISOamsn'
    'ntilde':   u'\u00F1', # latin small letter n with tilde, U+00F1 ISOlat1'
    'nu':       u'\u03BD', # greek small letter nu, U+03BD ISOgrk3'
    'oacute':   u'\u00F3', # latin small letter o with acute, U+00F3 ISOlat1'
    'ocirc':    u'\u00F4', # latin small letter o with circumflex, U+00F4 ISOlat1'
    'oelig':    u'\u0153', # latin small ligature oe, U+0153 ISOlat2'
    'ograve':   u'\u00F2', # latin small letter o with grave, U+00F2 ISOlat1'
    'oline':    u'\u203E', # overline = spacing overscore, U+203E NEW'
    'omega':    u'\u03C9', # greek small letter omega, U+03C9 ISOgrk3'
    'omicron':  u'\u03BF', # greek small letter omicron, U+03BF NEW'
    'oplus':    u'\u2295', # circled plus = direct sum, U+2295 ISOamsb'
    'or':       u'\u2228', # logical or = vee, U+2228 ISOtech'
    'ordf':     u'\u00AA', # feminine ordinal indicator, U+00AA ISOnum'
    'ordm':     u'\u00BA', # masculine ordinal indicator, U+00BA ISOnum'
    'oslash':   u'\u00F8', # latin small letter o with stroke, = latin small letter o slash, U+00F8 ISOlat1'
    'otilde':   u'\u00F5', # latin small letter o with tilde, U+00F5 ISOlat1'
    'otimes':   u'\u2297', # circled times = vector product, U+2297 ISOamsb'
    'ouml':     u'\u00F6', # latin small letter o with diaeresis, U+00F6 ISOlat1'
    'para':     u'\u00B6', # pilcrow sign = paragraph sign, U+00B6 ISOnum'
    'part':     u'\u2202', # partial differential, U+2202 ISOtech'
    'permil':   u'\u2030', # per mille sign, U+2030 ISOtech'
    'perp':     u'\u22A5', # up tack = orthogonal to = perpendicular, U+22A5 ISOtech'
    'phi':      u'\u03C6', # greek small letter phi, U+03C6 ISOgrk3'
    'pi':       u'\u03C0', # greek small letter pi, U+03C0 ISOgrk3'
    'piv':      u'\u03D6', # greek pi symbol, U+03D6 ISOgrk3'
    'plusmn':   u'\u00B1', # plus-minus sign = plus-or-minus sign, U+00B1 ISOnum'
    'pound':    u'\u00A3', # pound sign, U+00A3 ISOnum'
    'prime':    u'\u2032', # prime = minutes = feet, U+2032 ISOtech'
    'prod':     u'\u220F', # n-ary product = product sign, U+220F ISOamsb'
    'prop':     u'\u221D', # proportional to, U+221D ISOtech'
    'psi':      u'\u03C8', # greek small letter psi, U+03C8 ISOgrk3'
    'quot':     u'\u0022', # quotation mark = APL quote, U+0022 ISOnum'
    'rArr':     u'\u21D2', # rightwards double arrow, U+21D2 ISOtech'
    'radic':    u'\u221A', # square root = radical sign, U+221A ISOtech'
    'rang':     u'\u232A', # right-pointing angle bracket = ket, U+232A ISOtech'
    'raquo':    u'\u00BB', # right-pointing double angle quotation mark = right pointing guillemet, U+00BB ISOnum'
    'rarr':     u'\u2192', # rightwards arrow, U+2192 ISOnum'
    'rceil':    u'\u2309', # right ceiling, U+2309 ISOamsc'
    'rdquo':    u'\u201D', # right double quotation mark, U+201D ISOnum'
    'real':     u'\u211C', # blackletter capital R = real part symbol, U+211C ISOamso'
    'reg':      u'\u00AE', # registered sign = registered trade mark sign, U+00AE ISOnum'
    'rfloor':   u'\u230B', # right floor, U+230B ISOamsc'
    'rho':      u'\u03C1', # greek small letter rho, U+03C1 ISOgrk3'
    'rlm':      u'\u200F', # right-to-left mark, U+200F NEW RFC 2070'
    'rsaquo':   u'\u203A', # single right-pointing angle quotation mark, U+203A ISO proposed'
    'rsquo':    u'\u2019', # right single quotation mark, U+2019 ISOnum'
    'sbquo':    u'\u201A', # single low-9 quotation mark, U+201A NEW'
    'scaron':   u'\u0161', # latin small letter s with caron, U+0161 ISOlat2'
    'sdot':     u'\u22C5', # dot operator, U+22C5 ISOamsb'
    'sect':     u'\u00A7', # section sign, U+00A7 ISOnum'
    'shy':      u'\u00AD', # soft hyphen = discretionary hyphen, U+00AD ISOnum'
    'sigma':    u'\u03C3', # greek small letter sigma, U+03C3 ISOgrk3'
    'sigmaf':   u'\u03C2', # greek small letter final sigma, U+03C2 ISOgrk3'
    'sim':      u'\u223C', # tilde operator = varies with = similar to, U+223C ISOtech'
    'spades':   u'\u2660', # black spade suit, U+2660 ISOpub'
    'sub':      u'\u2282', # subset of, U+2282 ISOtech'
    'sube':     u'\u2286', # subset of or equal to, U+2286 ISOtech'
    'sum':      u'\u2211', # n-ary sumation, U+2211 ISOamsb'
    'sup':      u'\u2283', # superset of, U+2283 ISOtech'
    'sup1':     u'\u00B9', # superscript one = superscript digit one, U+00B9 ISOnum'
    'sup2':     u'\u00B2', # superscript two = superscript digit two = squared, U+00B2 ISOnum'
    'sup3':     u'\u00B3', # superscript three = superscript digit three = cubed, U+00B3 ISOnum'
    'supe':     u'\u2287', # superset of or equal to, U+2287 ISOtech'
    'szlig':    u'\u00DF', # latin small letter sharp s = ess-zed, U+00DF ISOlat1'
    'tau':      u'\u03C4', # greek small letter tau, U+03C4 ISOgrk3'
    'there4':   u'\u2234', # therefore, U+2234 ISOtech'
    'theta':    u'\u03B8', # greek small letter theta, U+03B8 ISOgrk3'
    'thetasym': u'\u03D1', # greek small letter theta symbol, U+03D1 NEW'
    'thinsp':   u'\u2009', # thin space, U+2009 ISOpub'
    'thorn':    u'\u00FE', # latin small letter thorn with, U+00FE ISOlat1'
    'tilde':    u'\u02DC', # small tilde, U+02DC ISOdia'
    'times':    u'\u00D7', # multiplication sign, U+00D7 ISOnum'
    'trade':    u'\u2122', # trade mark sign, U+2122 ISOnum'
    'uArr':     u'\u21D1', # upwards double arrow, U+21D1 ISOamsa'
    'uacute':   u'\u00FA', # latin small letter u with acute, U+00FA ISOlat1'
    'uarr':     u'\u2191', # upwards arrow, U+2191 ISOnum'
    'ucirc':    u'\u00FB', # latin small letter u with circumflex, U+00FB ISOlat1'
    'ugrave':   u'\u00F9', # latin small letter u with grave, U+00F9 ISOlat1'
    'uml':      u'\u00A8', # diaeresis = spacing diaeresis, U+00A8 ISOdia'
    'upsih':    u'\u03D2', # greek upsilon with hook symbol, U+03D2 NEW'
    'upsilon':  u'\u03C5', # greek small letter upsilon, U+03C5 ISOgrk3'
    'uuml':     u'\u00FC', # latin small letter u with diaeresis, U+00FC ISOlat1'
    'weierp':   u'\u2118', # script capital P = power set = Weierstrass p, U+2118 ISOamso'
    'xi':       u'\u03BE', # greek small letter xi, U+03BE ISOgrk3'
    'yacute':   u'\u00FD', # latin small letter y with acute, U+00FD ISOlat1'
    'yen':      u'\u00A5', # yen sign = yuan sign, U+00A5 ISOnum'
    'yuml':     u'\u00FF', # latin small letter y with diaeresis, U+00FF ISOlat1'
    'zeta':     u'\u03B6', # greek small letter zeta, U+03B6 ISOgrk3'
    'zwj':      u'\u200D', # zero width joiner, U+200D NEW RFC 2070'
    'zwnj':     u'\u200C'  # zero width non-joiner, U+200C NEW RFC 2070'
}

entitydefs2 = {
    '$':    '%24',
    '&':    '%26',
    '+':    '%2B',
    ',':    '%2C',
    '/':    '%2F',
    ':':    '%3A',
    ';':    '%3B',
    '=':    '%3D',
    '?':    '%3F',
    '@':    '%40',
    ' ':    '%20',
    '"':    '%22',
    '<':    '%3C',
    '>':    '%3E',
    '#':    '%23',
    '%':    '%25',
    '{':    '%7B',
    '}':    '%7D',
    '|':    '%7C',
    '\\':   '%5C',
    '^':    '%5E',
    '~':    '%7E',
    '[':    '%5B',
    ']':    '%5D',
    '`':    '%60'
}

entitydefs3 = {
    u'ÂÁÀÄÃÅ':  u'A',
    u'âáàäãå':  u'a',
    u'ÔÓÒÖÕ':   u'O',
    u'ôóòöõðø': u'o',
    u'ÛÚÙÜ':    u'U',
    u'ûúùüµ':   u'u',
    u'ÊÉÈË':    u'E',
    u'êéèë':    u'e',
    u'ÎÍÌÏ':    u'I',
    u'îìíï':    u'i',
    u'ñ':       u'n',
    u'ß':       u'B',
    u'÷':       u'%',
    u'ç':       u'c',
    u'æ':       u'ae'
}

def getDownloadPath():
	
	# La ruta de descarga es un parámetro
	downloadpath = config.getSetting("downloadpath")
	
	# No está fijada, intenta forzarla
	try:
		if downloadpath == "":
			logger.info("[downloadtools.py] downloadpath está vacio")
			
			# Busca un setting del skin (Telebision)
			downloadpath = xbmc.getInfoLabel('Skin.String(downloadpath)')
			logger.info("[downloadtools.py] downloadpath en el skin es "+downloadpath)
			
			# No es Telebision, fuerza el directorio home de XBMC
			if downloadpath == "":
				downloadpath = os.path.join (config.DATA_PATH,"downloads")
				xbmc.log("[downloadtools.py] getDownloadPath: downloadpath=%s" % downloadpath)
				if not os.path.exists(downloadpath):
					logger.info("[downliadtools.py] download path doesn't exist:"+downloadpath)
					os.mkdir(downloadpath)
				config.setSetting("downloadpath",downloadpath)
			
			# Es Telebision, lo pone en el skin
			else:
				# guardar setting del skin en setting del plugin
				downloadpath = xbmc.translatePath( downloadpath )
				logger.info("[downloadtools.py] downloadpath nativo es "+downloadpath)
				config.setSetting("downloadpath", downloadpath)
	except:
		pass
	
	logger.info("[downloadtools.py] downloadpath="+downloadpath)
	
	try:
		os.mkdir(downloadpath)
	except:
		pass

	return downloadpath

def getDownloadListPath():
	
	# La ruta de la lista de descargas es un parámetro
	downloadpath = config.getSetting("downloadlistpath")
	
	# No está fijada, intenta forzarla
	try:
		if downloadpath == "":
			logger.info("[downloadtools.py] downloadpath está vacio")
			
			# Busca un setting del skin (Telebision)
			downloadpath = xbmc.getInfoLabel('Skin.String(downloadpath)')
			logger.info("[downloadtools.py] downloadpath en el skin es "+downloadpath)
			
			# No es Telebision, fuerza el directorio home de XBMC
			if downloadpath == "":
				downloadpath = os.path.join (config.DATA_PATH,"downloads","list")
				xbmc.log("[downloadtools.py] getDownloadPath: downloadpath=%s" % downloadpath)
				if not os.path.exists(downloadpath):
					logger.info("[downliadtools.py] download path doesn't exist:"+downloadpath)
					os.mkdir(downloadpath)
				config.setSetting("downloadlistpath",downloadpath)
			
			# Es Telebision, lo pone en el skin
			else:
				# guardar setting del skin en setting del plugin
				downloadpath = os.path.join( downloadpath , "list" )
				downloadpath = xbmc.translatePath( downloadpath )
				logger.info("[downloadtools.py] downloadpath nativo es "+downloadpath)
				config.setSetting("downloadlistpath", downloadpath)
	except:
		pass
	
	logger.info("[downloadtools.py] downloadlistpath="+downloadpath)
	
	try:
		os.mkdir(downloadpath)
	except:
		pass

	return downloadpath

def limpia_nombre_caracteres_especiales(s):
    if not s:
        return ''
    badchars = '\\/:*?\"<>|'
    for c in badchars:
        s = s.replace(c, '')
    return s;

def limpia_nombre_sin_acentos(s):
    if not s:
        return ''
    for key, value in entitydefs3.iteritems():
        for c in key:
            s = s.replace(c, value)
    return s;

def limpia_nombre_excepto_1(s):
	if not s:
		return ''

	# Titulo de entrada
	try:
		logger.info("s1="+urllib.quote_plus(s))
	except:
		logger.info("s1=no printable")

	# Convierte a unicode
	try:
		s = unicode( s, "utf-8" )
	except:
		logger.info("no es utf-8")
		try:
			s = unicode( s, "iso-8859-1" )
		except:
			logger.info("no es iso-8859-1")
			pass
	try:
		logger.info("s2="+urllib.quote_plus(s))
	except:
		logger.info("s2=no printable")

	# Elimina acentos
	s = limpia_nombre_sin_acentos(s)
	try:
		logger.info("s3="+urllib.quote_plus(s))
	except:
		logger.info("s3=no printable")	

	# Elimina caracteres prohibidos
	validchars = " ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890!#$%&'()-@[]^_`{}~."
	stripped = ''.join(c for c in s if c in validchars)
	try:
		logger.info("s4="+urllib.quote_plus(stripped))
	except:
		logger.info("s4=no printable")
	
	# Convierte a iso
	s = stripped.encode("iso-8859-1")
	try:
		logger.info("s5="+urllib.quote_plus(s))
	except:
		logger.info("s5=no printable")

	return s;

def limpia_nombre_excepto_2(s):
    if not s:
        return ''
    validchars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890."
    stripped = ''.join(c for c in s if c in validchars)
    return stripped;

def getfilefromtitle(url,title):
	# Imprime en el log lo que va a descartar
	logger.info("[downloadtools.py] getfilefromtitle: url="+url )
	#logger.info("[downloadtools.py] downloadtitle: title="+urllib.quote_plus( title ))
	plataforma = xbmctools.get_system_platform();
	logger.info("[downloadtools.py] getfilefromtitle: plataforma="+plataforma)
	
	#nombrefichero = xbmc.makeLegalFilename(title + url[-4:])
	if plataforma=="xbox":
		nombrefichero = title[:38] + url[-4:]
		nombrefichero = limpia_nombre_excepto_1(nombrefichero)
	else:
		nombrefichero = title + url[-4:]

	xbmc.log("[downloadtools.py] getfilefromtitle: nombrefichero=%s" % nombrefichero)
	fullpath = os.path.join( getDownloadPath() , nombrefichero )
	xbmc.log("[downloadtools.py] getfilefromtitle: fullpath=%s" % fullpath)
	
	return fullpath

def downloadtitle(url,title):
	fullpath = getfilefromtitle(url,title)
	return downloadfile(url,fullpath)

def downloadfile(url,nombrefichero):
	logger.info("[downloadtools.py] downloadfile: url="+url)
	logger.info("[downloadtools.py] downloadfile: nombrefichero="+nombrefichero)
	# antes
	#f=open(nombrefichero,"wb")
	nombrefichero = xbmc.makeLegalFilename(nombrefichero)
	logger.info("[downloadtools.py] downloadfile: nombrefichero="+nombrefichero)

	# despues
	if os.path.exists(nombrefichero):
		f = open(nombrefichero, 'r+b')
		existSize = os.path.getsize(nombrefichero)
		logger.info("[downloadtools.py] downloadfile: el fichero existe, size=%d" % existSize)
		grabado = existSize
		f.seek(existSize)
	else:
		existSize = 0
		logger.info("[downloadtools.py] downloadfile: el fichero no existe")
		f = open(nombrefichero, 'wb')
		grabado = 0

	# Crea el diálogo de progreso
	progreso = xbmcgui.DialogProgress()
	progreso.create( 'Pelisalacarta' , "Descargando vídeo..." , url , nombrefichero )

	# Timeout del socket a 60 segundos
	socket.setdefaulttimeout(10)

	h=urllib2.HTTPHandler(debuglevel=0)
	request = urllib2.Request(url)
	if existSize > 0:
		request.add_header('Range', 'bytes=%d-' % (existSize, ))

	opener = urllib2.build_opener(h)
	urllib2.install_opener(opener)
	try:
		connexion = opener.open(request)
	except urllib2.HTTPError,e:
		logger.info("[downloadtools.py] downloadfile: error %d (%s) al abrir la url %s" % (e.code,e.msg,url))
		#print e.code
		#print e.msg
		#print e.hdrs
		#print e.fp
		f.close()
		progreso.close()
		# El error 416 es que el rango pedido es mayor que el fichero => es que ya está completo
		if e.code==416:
			return 0
		else:
			return -2

	totalfichero = int(connexion.headers["Content-Length"])
	if existSize > 0:
		totalfichero = totalfichero + existSize

	xbmc.log("Content-Length=%s" % totalfichero)

	blocksize = 100*1024

	bloqueleido = connexion.read(blocksize)
	xbmc.log("Iniciando descarga del fichero, bloqueleido=%s" % len(bloqueleido))

	maxreintentos = 10
	
	while len(bloqueleido)>0:
		try:
			# Escribe el bloque leido
			f.write(bloqueleido)
			grabado = grabado + len(bloqueleido)
			percent = int(float(grabado)*100/float(totalfichero))
			totalmb = float(float(totalfichero)/(1024*1024))
			descargadosmb = float(float(grabado)/(1024*1024))

			# Lee el siguiente bloque, reintentando para no parar todo al primer timeout
			reintentos = 0
			while reintentos <= maxreintentos:
				try:
					before = time.time()
					bloqueleido = connexion.read(blocksize)
					after = time.time()
					if (after - before) > 0:
						velocidad=len(bloqueleido)/((after - before))
						falta=totalfichero-grabado
						if velocidad>0:
							tiempofalta=falta/velocidad
						else:
							tiempofalta=0
						#xbmc.log(sec_to_hms(tiempofalta))
						progreso.update( percent , "%.2fMB/%.2fMB (%d%%) %.2f Kb/s %s falta " % ( descargadosmb , totalmb , percent , velocidad/1024 , sec_to_hms(tiempofalta)))
					break
				except:
					reintentos = reintentos + 1
					xbmc.log("ERROR en la descarga del bloque, reintento %d" % reintentos)
					for line in sys.exc_info():
						logger.info( "%s" % line , xbmc.LOGERROR )
			
			# El usuario cancelo la descarga
			if progreso.iscanceled():
				xbmc.log("Descarga del fichero cancelada")
				f.close()
				progreso.close()
				return -1

			# Ha habido un error en la descarga
			if reintentos > maxreintentos:
				xbmc.log("ERROR en la descarga del fichero")
				f.close()
				progreso.close()

				return -2

		except:
			xbmc.log("ERROR en la descarga del fichero")
			for line in sys.exc_info():
				logger.info( "%s" % line , xbmc.LOGERROR )
			f.close()
			progreso.close()
			
			#advertencia = xbmcgui.Dialog()
			#resultado = advertencia.ok('Error al descargar' , 'Se ha producido un error' , 'al descargar el archivo')
			
			return -2

	f.close()
	progreso.close()
	xbmc.log("Fin descarga del fichero")

def downloadfileGzipped(url,pathfichero):
	logger.info("[downloadtools.py] downloadfileGzipped: url="+url)
	nombrefichero = pathfichero
	logger.info("[downloadtools.py] downloadfileGzipped: nombrefichero="+nombrefichero)

	nombrefichero = xbmc.makeLegalFilename(nombrefichero)
	logger.info("[downloadtools.py] downloadfileGzipped: nombrefichero="+nombrefichero)
	patron = "(http://[^/]+)/.+"
	matches = re.compile(patron,re.DOTALL).findall(url)
	
	if len(matches):
		logger.info("[downloadtools.py] URL principal :"+matches[0])
		url1= matches[0]
	else:
		url1 = url
	
	txheaders =  {'User-Agent':'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)',
	              'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	              'Accept-Language':'es-es,es;q=0.8,en-us;q=0.5,en;q=0.3',
	              'Accept-Encoding':'gzip,deflate',
	              'Accept-Charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	              'Keep-Alive':'115',
	              'Connection':'keep-alive',
	              'Referer':url1,
	              }
	              
		
	txdata = ""
	


	# Crea el diálogo de progreso
	progreso = xbmcgui.DialogProgress()
	progreso.create( 'Pelisalacarta' , "Descargando file..." , url , nombrefichero )

	# Timeout del socket a 60 segundos
	socket.setdefaulttimeout(10)

	h=urllib2.HTTPHandler(debuglevel=0)
	request = urllib2.Request(url, txdata, txheaders)
	#if existSize > 0:
	#	request.add_header('Range', 'bytes=%d-' % (existSize, ))

	opener = urllib2.build_opener(h)
	urllib2.install_opener(opener)
	try:
		connexion = opener.open(request)
	except urllib2.HTTPError,e:
		logger.info("[downloadtools.py] downloadfile: error %d (%s) al abrir la url %s" % (e.code,e.msg,url))
		#print e.code
		#print e.msg
		#print e.hdrs
		#print e.fp
		f.close()
		progreso.close()
		# El error 416 es que el rango pedido es mayor que el fichero => es que ya está completo
		if e.code==416:
			return 0
		else:
			return -2
	nombreficheroBase = os.path.basename(nombrefichero)
	if len(nombreficheroBase) == 0:
		print "Buscando nombre en el Headers de respuesta"
		nombreBase = connexion.headers["Content-Disposition"]
		print nombreBase
		patron = 'filename="([^"]+)"'
		matches = re.compile(patron,re.DOTALL).findall(nombreBase)
		if len(matches)>0:
			titulo = matches[0]
			titulo = GetTitleFromFile(titulo)
			nombrefichero = os.path.join(pathfichero,titulo)
		else:
			print "Nombre del fichero no encontrado"
			print "Colocando nombre temporal :sin_nombre.txt"
			titulo = "sin_nombre.txt"
			nombrefichero = os.path.join(pathfichero,titulo)			
	totalfichero = int(connexion.headers["Content-Length"])
	 
	# despues
	if os.path.exists(nombrefichero):
		f = open(nombrefichero, 'w')
		
		existSize = 0
		logger.info("[downloadtools.py] downloadfileGzipped: el fichero existe, se sobreescribirá, size=%d" % existSize)
		
		
	else:
		existSize = 0
		logger.info("[downloadtools.py] downloadfileGzipped: el fichero no existe")
		f = open(nombrefichero, 'wb')
		

	#if existSize > 0:
	#	totalfichero = totalfichero + existSize
	grabado = 0
	xbmc.log("Content-Length=%s" % totalfichero)

	blocksize = 100*1024

	bloqueleido = connexion.read(blocksize)
	
	compressedstream = StringIO.StringIO(bloqueleido)
	gzipper = gzip.GzipFile(fileobj=compressedstream)
	bloquedata = gzipper.read()
	gzipper.close()
	xbmc.log("Iniciando descarga del fichero, bloqueleido=%s" % len(bloqueleido))

	maxreintentos = 10
	
	while len(bloqueleido)>0:
		try:
			# Escribe el bloque leido
			f.write(bloquedata)
			grabado = grabado + len(bloqueleido)
			percent = int(float(grabado)*100/float(totalfichero))
			totalmb = float(float(totalfichero)/(1024*1024))
			descargadosmb = float(float(grabado)/(1024*1024))


			# Lee el siguiente bloque, reintentando para no parar todo al primer timeout
			reintentos = 0
			while reintentos <= maxreintentos:
				try:
					before = time.time()
					bloqueleido = connexion.read(blocksize)
					
					compressedstream = StringIO.StringIO(bloqueleido)
					gzipper = gzip.GzipFile(fileobj=compressedstream)
					bloquedata = gzipper.read()
					gzipper.close()	
					after = time.time()
					if (after - before) > 0:
						velocidad=len(bloqueleido)/((after - before))
						falta=totalfichero-grabado
						if velocidad>0:
							tiempofalta=falta/velocidad
						else:
							tiempofalta=0
						xbmc.log(sec_to_hms(tiempofalta))
						progreso.update( percent , "%.2fMB/%.2fMB (%d%%) %.2f Kb/s %s falta " % ( descargadosmb , totalmb , percent , velocidad/1024 , sec_to_hms(tiempofalta)))
					break
				except:
					reintentos = reintentos + 1
					xbmc.log("ERROR en la descarga del bloque, reintento %d" % reintentos)
					for line in sys.exc_info():
						logger.info( "%s" % line , xbmc.LOGERROR )
			
			# El usuario cancelo la descarga
			if progreso.iscanceled():
				xbmc.log("Descarga del fichero cancelada")
				f.close()
				progreso.close()
				return -1

			# Ha habido un error en la descarga
			if reintentos > maxreintentos:
				xbmc.log("ERROR en la descarga del fichero")
				f.close()
				progreso.close()

				return -2

		except:
			xbmc.log("ERROR en la descarga del fichero")
			for line in sys.exc_info():
				logger.info( "%s" % line , xbmc.LOGERROR )
			f.close()
			progreso.close()
			
			return -2
	f.close()
	

	
	#print data
	progreso.close()
	xbmc.log("Fin descarga del fichero")
	return nombrefichero
	
def GetTitleFromFile(title):
	# Imprime en el log lo que va a descartar
	logger.info("[downloadtools.py] GetTitleFromFile: titulo="+title )
	#logger.info("[downloadtools.py] downloadtitle: title="+urllib.quote_plus( title ))
	plataforma = xbmctools.get_system_platform();
	logger.info("[downloadtools.py] GetTitleFromFile: plataforma="+plataforma)
	
	#nombrefichero = xbmc.makeLegalFilename(title + url[-4:])
	if plataforma=="xbox":
		nombrefichero = title[:38] + title[-4:]
		nombrefichero = limpia_nombre_excepto_1(nombrefichero)
	else:
		nombrefichero = title
	return nombrefichero
	
def sec_to_hms(seconds):
	m,s = divmod(int(seconds), 60)
	h,m = divmod(m, 60)
	return ("%02d:%02d:%02d" % ( h , m ,s ))


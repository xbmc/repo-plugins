# -*- coding: utf-8 -*-

from __future__ import print_function

import pytest

from .stream import Streams
from .testdata import getfile


DATA = list((quality, format, quality == 'hd')
    for quality in ('hd', 'sd')
    for format in ('mp4', 'webm'))


def test_conferences():
    s = Streams(SampleJson)
    assert len(s.conferences) == 2
    assert s.conferences[0].slug == "eh17"
    assert s.conferences[0].name == "Easterhegg 2017"


def test_rooms():
    s = Streams(SampleJson)
    c = s.conferences[0]
    assert len(c.rooms) == 3
    assert c.rooms[0].slug == "vortragssaal"
    assert c.rooms[0].display == u"Für die Glupscher: Vortragssaal"


@pytest.mark.parametrize('quality,format,hd', DATA)
def test_streams(quality, format, hd):
    s = Streams(SampleJson)
    c = s.conferences[0]
    r = c.rooms[0]
    assert len(r.streams) == 6
    streams = r.streams_sorted(quality, format)
    assert len(streams) == 4
    preferred = streams[0]
    assert preferred.hd is hd
    assert preferred.format == format
    assert preferred.translated is False


@pytest.mark.parametrize('quality,format,hd', DATA)
def test_streams_multiple_translations(quality, format, hd):
    s = Streams(SampleJson)
    c = s.conferences[1]
    r = c.rooms[0]
    assert len(r.streams) == 25
    streams = r.streams_sorted(quality, format)
    assert len(streams) == 12

    preferred = streams[0]
    assert preferred.hd is hd
    assert preferred.format == format
    assert preferred.translated is False

    trans1 = streams[1]
    assert trans1.hd is hd
    assert trans1.format == format
    assert trans1.translated is True

    trans2 = streams[2]
    assert trans2.hd is hd
    assert trans2.format == format
    assert trans2.translated is True


SampleJson = getfile('stream_v2.json')

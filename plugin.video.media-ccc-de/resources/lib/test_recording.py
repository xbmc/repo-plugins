# -*- coding: utf-8 -*-

from __future__ import print_function

from .recording import Recordings
from .testdata import getfile


def test_recordings():
    r = Recordings(SampleJson)
    assert len(r.recordings) == 10
    recordings = r.recordings_sorted("hd", "mp4")
    assert len(recordings) == 6
    preferred = recordings[0]
    assert preferred.hd is True
    assert preferred.format == 'mp4'
    assert len(preferred.languages) == 2


def test_minimal_broken_json():
    r = Recordings(MinimalBrokenJson)
    assert len(r.recordings) == 2
    recordings = r.recordings_sorted("hd", "mp4")
    assert len(recordings) == 2
    preferred = recordings[0]
    assert preferred.hd is True
    assert preferred.format == 'mp4'
    assert len(preferred.languages) == 1


# From https://api.media.ccc.de/public/events/2893
SampleJson = getfile('recording_full.json')
MinimalBrokenJson = getfile('recording_minimal.json')

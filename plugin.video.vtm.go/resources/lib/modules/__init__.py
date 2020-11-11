# -*- coding: utf-8 -*-
""" Shared data """

from __future__ import absolute_import, division, unicode_literals

from collections import OrderedDict

# key         = ID used in the VTM GO API, name of the logo file
# label       = Label to show in the UI
# epg         = ID used in the EPG API
# studio_icon = filename used in resource.images.studios.white
# iptv_preset = Channel Number to use when exporting to IPTV Manager
# iptv_id     = Channel ID to use when exporting to IPTV Manager

CHANNELS = OrderedDict([
    ('vtm', dict(
        label='VTM',
        epg='vtm',
        iptv_preset=3,
        iptv_id='vtm.be',
        studio_icon='VTM',
        youtube=[
            dict(
                # VTM: https://www.youtube.com/user/VTMvideo
                label='VTM',
                logo='vtm',
                path='plugin://plugin.video.youtube/user/VTMvideo/',
            ),
            dict(
                # VTM Nieuws: https://www.youtube.com/channel/UCm1v16r82bhI5jwur14dK9w
                label='VTM Nieuws',
                logo='vtm',
                path='plugin://plugin.video.youtube/channel/UCm1v16r82bhI5jwur14dK9w/',
            ),
            dict(
                # VTM Koken: https://www.youtube.com/user/VTMKOKENvideokanaal
                label='VTM Koken',
                logo='vtm',
                path='plugin://plugin.video.youtube/user/VTMKOKENvideokanaal/',
            ),
        ]
    )),
    ('vtm2', dict(
        label='VTM 2',
        epg='vtm2',
        iptv_preset=7,
        iptv_id='vtm2.be',
        studio_icon='VTM 2',
        youtube=[
            dict(
                # VTM 2: https://www.youtube.com/user/2BEvideokanaal
                label='VTM 2',
                logo='vtm2',
                path='plugin://plugin.video.youtube/user/2BEvideokanaal/',
            ),
        ]
    )),
    ('vtm3', dict(
        label='VTM 3',
        epg='vtm3',
        iptv_preset=8,
        iptv_id='vtm3.be',
        studio_icon='VTM 3',
        youtube=[
            dict(
                # VTM 3: https://www.youtube.com/user/VITAYAvideokanaal
                label='VTM 3',
                logo='vtm3',
                path='plugin://plugin.video.youtube/user/VITAYAvideokanaal/',
            ),
        ]
    )),
    ('vtm4', dict(
        label='VTM 4',
        epg='vtm4',
        iptv_preset=9,
        iptv_id='vtm4.be',
        stream='vtm4',
        studio_icon='VTM 4',
    )),
    ('caz2', dict(
        label='CAZ 2',
        epg='caz-2',
        iptv_preset=10,
        iptv_id='caz2.be',
        stream='caz2',
        studio_icon='CAZ 2',
    )),
    ('vtmkids', dict(
        label='VTM KIDS',
        epg='vtm-kids',
        iptv_preset=13,
        iptv_id='vtmkids.be',
        studio_icon='VTM Kids',
        youtube=[
            dict(
                # VTM KIDS: https://www.youtube.com/channel/UCJgZKD2qpa7mY2BtIgpNR2Q
                label='VTM KIDS',
                logo='vtmkids',
                path='plugin://plugin.video.youtube/channel/UCJgZKD2qpa7mY2BtIgpNR2Q/',
            ),
        ]
    )),
    ('qmusic', dict(
        label='QMusic',
        epg='qmusic',
        iptv_preset=20,
        iptv_id='qmusic.be',
        studio_icon='Q Music',
        youtube=[
            dict(
                # Q-Music: https://www.youtube.com/channel/UCCDccz7bJ9XdwTBkEX1qKlg
                label='QMusic',
                logo='qmusic',
                path='plugin://plugin.video.youtube/channel/UCCDccz7bJ9XdwTBkEX1qKlg/',
            ),
        ]
    )),
    ('vtmnieuws', dict(
        label='VTM Nieuws',
        epg=None,
        iptv_preset=803,
        iptv_id='vtmnieuws.be',
        studio_icon='VTM Nieuws',
        youtube=[
            dict(
                # VTM Nieuws: https://www.youtube.com/channel/UCm1v16r82bhI5jwur14dK9w
                label='VTM Nieuws',
                logo='vtm',
                path='plugin://plugin.video.youtube/channel/UCm1v16r82bhI5jwur14dK9w/',
            ),
        ]
    )),
])

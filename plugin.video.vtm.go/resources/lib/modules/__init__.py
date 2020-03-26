# -*- coding: utf-8 -*-
""" Shared data """

from __future__ import absolute_import, division, unicode_literals

from collections import OrderedDict

# key         = id used in the VTM GO API
# label       = Label to show in the UI
# logo        = File in resources/logos/
# epg         = id used in the EPG API
# studio_icon = filename used in resource.images.studios.white
CHANNELS = OrderedDict([
    ('vtm', dict(
        label='VTM',
        logo='vtm',
        epg='vtm',
        studio_icon='VTM',
        kids=False,
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
    ('q2', dict(
        label='Q2',
        logo='q2',
        epg='q2',
        studio_icon='Q2',
        kids=False,
        youtube=[
            dict(
                # Q2: https://www.youtube.com/user/2BEvideokanaal
                label='Q2',
                logo='q2',
                path='plugin://plugin.video.youtube/user/2BEvideokanaal/',
            ),
        ]
    )),
    ('vitaya', dict(
        label='Vitaya',
        logo='vitaya',
        epg='vitaya',
        studio_icon='Vitaya',
        kids=False,
        youtube=[
            dict(
                # Vitaya: https://www.youtube.com/user/VITAYAvideokanaal
                label='Vitaya',
                logo='vitaya',
                path='plugin://plugin.video.youtube/user/VITAYAvideokanaal/',
            ),
        ]
    )),
    ('caz', dict(
        label='CAZ',
        logo='caz',
        epg='caz',
        stream='caz',
        studio_icon='CAZ',
        kids=False,
    )),
    ('caz2', dict(
        label='CAZ 2',
        logo='caz2',
        epg='caz-2',
        stream='caz2',
        studio_icon='CAZ 2',
        kids=False,
    )),
    ('vtmkids', dict(
        label='VTM KIDS',
        logo='vtmkids',
        epg='vtm-kids',
        studio_icon='VTM Kids',
        kids=True,
        youtube=[
            dict(
                # VTM KIDS: https://www.youtube.com/channel/UCJgZKD2qpa7mY2BtIgpNR2Q
                label='VTM KIDS',
                logo='vtmkids',
                path='plugin://plugin.video.youtube/channel/UCJgZKD2qpa7mY2BtIgpNR2Q/',
            ),
        ]
    )),
    ('vtmkidsjr', dict(
        label='VTM KIDS Jr',
        logo='vtmkidsjr',
        epg='vtm-kids-jr',
        studio_icon='VTM Kids Jr',
        kids=True,
    )),
    ('qmusic', dict(
        label='QMusic',
        logo='qmusic',
        epg='qmusic',
        studio_icon='Q Music',
        kids=False,
        youtube=[
            dict(
                # Q-Music: https://www.youtube.com/user/qmusic
                label='QMusic',
                logo='qmusic',
                path='plugin://plugin.video.youtube/user/qmusic/',
            ),
        ]
    )),
])

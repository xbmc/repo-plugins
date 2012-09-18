from xbmcswift2 import Plugin
import resources.lib.scraper as scraper

__addon_id__ = 'plugin.video.myzen_tv'
__addon_name__ = 'Myzen.tv'

plugin = Plugin(__addon_name__, __addon_id__, __file__)


@plugin.route('/')
def show_free_videos():
    log('show_free_videos started')
    videos = scraper.get_free_videos()
    for video in videos:
        video['path'] = plugin.url_for('play_video', path=video['path'])
        video['is_playable'] = True
    return plugin.finish(videos)


@plugin.route('/play/<path>')
def play_video(path):
    rtmp_params = scraper.get_rtmp_params(path)

    def rtmpdump_output(rtmp_params):
        return (
            'rtmpdump '
            '--rtmp "%(rtmp_url)s" '
            '--app "%(app)s" '
            '--swfUrl "%(swf_url)s" '
            '--playpath "%(playpath)s" '
            '-o test.flv'
        ) % rtmp_params

    def xbmc_output(rtmp_params):
        return (
            '%(rtmp_url)s '
            'app=%(app)s '
            'swfUrl=%(swf_url)s '
            'playpath=%(playpath)s '
        ) % rtmp_params

    playback_url = xbmc_output(rtmp_params)
    log('RTMP cmd: %s' % rtmpdump_output(rtmp_params))
    log('XBMC url: %s' % playback_url)
    return plugin.set_resolved_url(playback_url)


def log(msg):
    print('%s addon: %s' % (__name__, msg))


if __name__ == '__main__':
    try:
        plugin.run()
    except scraper.NetworkError:
        log('NetworkError')

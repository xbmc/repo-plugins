import xbmc

from resources.lib.putio import Client
from resources.lib.helper import SETTINGS

POLL_INTERVAL = 2
PUTIO_API_ENDPOINT = 'https://api.put.io/v2'


if __name__ == '__main__':
    monitor = xbmc.Monitor()
    player = xbmc.Player()

    # This is the documented way to monitor Kodi.
    while not monitor.abortRequested():
        # Block for POLL_INTERVAL seconds, waiting for Kodi to exit.
        if monitor.waitForAbort(POLL_INTERVAL):
            break

        if not player.isPlayingVideo():
            continue

        filename = player.getPlayingFile()
        if not filename:
            continue

        # Kodi returns all video playbacks, including local files etc.
        # make sure the user is playing put.io files from the API.
        if not filename.startswith(PUTIO_API_ENDPOINT):
            continue

        video_is_at = player.getTime()
        if not video_is_at:
            continue

        # don't even bother to send a request if the player is at the start of the video.
        if video_is_at < 10:
            continue

        video_duration = player.getTotalTime()
        if video_duration <= 20:
            continue

        # if the player is very close to finish, set the 'start_from' parameter to the send of the video. because our
        # poll interval is not very precise. just assume user has finished watching the video.
        if (video_duration - video_is_at) < POLL_INTERVAL:
            video_is_at = video_duration

        oauth2_token = SETTINGS.getSetting('oauth2_token')
        if not oauth2_token:
            xbmc.log(msg='[putio.service] Missing OAuth2 Token', level=xbmc.LOGERROR)
            continue

        # FIXME: urlparse combined with os.path.split gives a stupid error. this is python 2.6 in 2016. screw this.
        paths = filename.strip(PUTIO_API_ENDPOINT)
        item_id = paths.split('/')[1]

        # time to send a request
        handler = Client(access_token=oauth2_token, use_retry=True)
        try:
            handler.request('/files/%s/start-from/set' % item_id,
                            method='POST',
                            data={'time': video_is_at})
        except Exception as e:
            xbmc.log(msg='[putio.service] Exception while syncing video position with the API. %s' % e)

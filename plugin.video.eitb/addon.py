from urllib.parse import parse_qsl
from video import VideoHandler
from audio import AudioHandler

import sys
import xbmcaddon
import xbmc

addon = xbmcaddon.Addon()

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

vh = VideoHandler(_handle, _url)
ah = AudioHandler(_handle, _url)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring:
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if "content_type" in params:
            if params["content_type"] == "video":
                vh.list_menu()
                # vh.list_programs()
            elif params["content_type"] == "audio":
                ah.list_radios()
                # ah.list_radio_programs()
        else:
            if "action" in params:
                if params["action"] == "videomenu":
                    # Display the list of videos in a provided category.
                    if params["option"] == "all_tvshows":
                        vh.list_programs()
                    # elif params['option'] == 'last_tvshows':
                    #     vh.list_last_broadcast()
                    elif params["option"] == "program-type-list":
                        vh.list_programs_types()
                elif params["action"] == "videotypelisting":
                    # Display the list of videos in a provided category.
                    vh.list_programs_types_playlist(params["program"])
                elif params["action"] == "videolisting":
                    # Display the list of videos in a provided category.
                    vh.list_playlists(params["program"])
                    # vh.list_episodes(params['program'])
                elif params["action"] == "videoprogram":
                    # Display the list of videos in a provided program.
                    vh.list_episodes(params["program"])
                elif params["action"] == "videoepisode":
                    # Display the list of videos in a provided category.
                    vh.list_videos(params["program"])
                elif params["action"] == "videoplay":
                    # Play a video from a provided URL.
                    vh.play_video(params["video"])
                elif params["action"] == "audioplay":
                    ah.play_audio(params["program"])
                elif params["action"] == "radio":
                    ah.list_radio_programs(params["program"])
                elif params["action"] == "audioprogram":
                    ah.list_seasons(params["program"])
                elif params["action"] == "audioseason":
                    ah.list_program_season_chapters(params["program"])
                elif params["action"] == "audiochapter":
                    ah.list_program_audios(params["program"])
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        vh.list_programs()


if __name__ == "__main__":
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])

import sys
from urllib.parse import parse_qsl
from xbmcaddon import Addon
from xbmcgui import Dialog
from resources.lib.api import Eventvods

PLAYER_NONE = -1
PLAYER_YOUTUBE = 0
PLAYER_TWITCH = 1

__localize__ = Eventvods.localize


if __name__ == "__main__":
    paramstring = sys.argv[2][1:]
    params = dict(parse_qsl(paramstring))
    if params:
        eventvods = Eventvods.load_state()

        if params["action"] == "listgamesubmenu":
            eventvods.main_game_sublist(params["game_id"])

        elif params["action"] == "listeventsubmenu":
            eventvods.main_event_sublist()

        elif params["action"] == "listteamalphas":
            eventvods.team_list_alphabetical()

        elif params["action"] == "listteams":
            eventvods.team_list(params["teamlabel"])

        elif params["action"] == "listteammatches":
            eventvods.team_match_list(params["teamslug"])

        elif params["action"] == "listyears":
            eventvods.year_list(params["mode"])

        elif params["action"] == "listevents":
            try:
                eventvods.event_list(params["mode"], year=params["year"])
            except KeyError:
                eventvods.event_list(params["mode"])

        elif params["action"] == "contextlistteams":
            eventvods.context_team_list(params["slug"])

        elif params["action"] == "contextlisthosts":
            eventvods.context_hosts_list(params["slug"])

        elif params["action"] == "contexteventinfo":
            eventvods.context_event_info(params["slug"])

        elif params["action"] == "contextmatchinfo":
            eventvods.context_match_info(params["match_id"])

        elif params["action"] == "listweeks":
            eventvods.week_list(params["slug"],
                      params["spoilmatches"] == "True")

        elif params["action"] == "listdays":
            eventvods.day_list(int(params["week"]))

        elif params["action"] == "listmatches":
            eventvods.match_list(int(params["day"]))

        elif params["action"] == "listmaps":
            eventvods.map_list(params["match_id"])

        elif params["action"] == "play":
            preferred_player = Addon().getSettingInt("preferredStream")

            if preferred_player == PLAYER_NONE:
                if (params["yt_video_id"] != "none" and
                        params["tw_video_id"] != "none"):

                    choice = Dialog().select(__localize__(30000),
                                            [__localize__(30001),
                                             __localize__(30002)])

                elif params["yt_video_id"] != "none":
                    choice = PLAYER_YOUTUBE
                elif params["tw_video_id"] != "none":
                    choice = PLAYER_TWITCH
                else:
                    choice = PLAYER_NONE

            elif preferred_player == PLAYER_YOUTUBE:
                if params["yt_video_id"] != "none":
                    choice = PLAYER_YOUTUBE
                elif params["tw_video_id"] != "none":
                    choice = PLAYER_TWITCH
                else:
                    choice = PLAYER_NONE

            elif preferred_player == PLAYER_TWITCH:
                if params["tw_video_id"] != "none":
                    choice = PLAYER_TWITCH
                elif params["yt_video_id"] != "none":
                    choice = PLAYER_YOUTUBE
                else:
                    choice = PLAYER_NONE
            else:
                choice = PLAYER_NONE

            if choice == PLAYER_YOUTUBE:
                eventvods.play_youtube_video(params["yt_video_id"],
                          offset=params["yt_offset"])
            elif choice == PLAYER_TWITCH:
                eventvods.play_twitch_video(params["tw_video_id"],
                          offset=params["tw_offset"])

    else:
        eventvods = Eventvods()
        eventvods.main_list()

    eventvods.save_state()

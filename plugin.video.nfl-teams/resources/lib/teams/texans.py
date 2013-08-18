# coding=utf-8
import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "texans"
    _cdaweb_url = "http://www.houstontexans.com/cda-web/"
    _categories = [
        "Cheerleaders",
        "Community",
        #"Español", # TODO: Does currently not return any videos. Most likely an encoding issue
        "Football",
        "Friday Facebook Mailbag",
        "Gameday",
        "HCC",
        "Inside the Game",
        "NFL Network/NFL Films",
        "Press Conferences",
        "Season Highlights",
        "Special Segments",
        "Texans Huddle",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()

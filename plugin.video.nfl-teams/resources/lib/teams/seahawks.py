from resources.lib.nfl2018 import NFL2018


class Team(NFL2018):
    short = "seahawks"
    hostname = "www.seahawks.com"

    def __init__(self, parameters):
        self.parameters = parameters
        NFL2018.__init__(self)

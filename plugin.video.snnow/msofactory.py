import sportsnet, rogers, shawgo, telus, cogeco

class MSOFactory:

    @staticmethod
    def getMSO(name):
        """
        Get an instance of the MSO class based on the MSO name.
        @name the MSO name (eg: Rogers)
        """

        if name == "Sportsnet":
            return sportsnet.Sportsnet()
        elif name == "Rogers":
            return rogers.Rogers()
        elif name == "ShawGo":
            return shawgo.ShawGo()
        elif name == "Telus":
            return telus.Telus()
        elif name == "Cogeco":
            return cogeco.Cogeco()

        return None
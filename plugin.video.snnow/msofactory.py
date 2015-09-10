import rogers, shawgo

class MSOFactory:

    @staticmethod
    def getMSO(name):
        """
        Get an instance of the MSO class based on the MSO name.
        @name the MSO name (eg: Rogers)
        """

        if name == "Rogers":
            return rogers.Rogers()
        elif name == "ShawGo":
            return shawgo.ShawGo()

        return None
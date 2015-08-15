import rogers

class MSOFactory:

    @staticmethod
    def getMSO(name):
        """
        Get an instance of the MSO class based on the MSO name.
        @name the MSO name (eg: Rogers)
        """

        if name == "Rogers":
            return rogers.Rogers()

        return None
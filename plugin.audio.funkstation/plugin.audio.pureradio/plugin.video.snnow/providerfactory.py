from snnow import SportsnetNow

class ProviderFactory:

    @staticmethod
    def getProviderNames():
        """
        Get an instance of the MSO class based on the MSO name.
        @name the MSO name (eg: Rogers)
        """

        snet = SportsnetNow.instance()
        providers = { snet.getRequestorID() : snet.name() }

        return providers

    @staticmethod
    def getProviders():
        snet = SportsnetNow.instance()
        providers = { snet.getRequestorID() : snet }
        return providers
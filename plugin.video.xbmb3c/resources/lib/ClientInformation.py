from uuid import getnode as get_mac

class ClientInformation():

    def getMachineId(self):
        return "%012X"%get_mac()
        
    def getVersion(self):
        return "0.8.6"
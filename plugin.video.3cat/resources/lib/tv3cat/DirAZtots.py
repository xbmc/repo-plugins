from resources.lib.video.FolderVideo import FolderVideo




def getList():
    progsAC = FolderVideo("#A-C", "tots", "progAZ", "", "")
    progsDE = FolderVideo("D-E", "tots", "progAZ", "", "")
    progsFI = FolderVideo("F-I", "tots", "progAZ", "", "")
    progsJL = FolderVideo("J-L", "tots", "progAZ", "", "")
    progsMP = FolderVideo("M-P", "tots", "progAZ", "", "")
    progsQS = FolderVideo("Q-S", "tots", "progAZ", "", "")
    progsTV = FolderVideo("T-V", "tots", "progAZ", "", "")
    progsXZ = FolderVideo("X-Z", "tots", "progAZ", "", "")

    list = [progsAC, progsDE, progsFI, progsJL, progsMP, progsQS, progsTV,
                 progsXZ]
    return list
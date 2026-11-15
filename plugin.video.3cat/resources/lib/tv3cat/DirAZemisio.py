from resources.lib.video.FolderVideo import FolderVideo




def getList():
    progsAC = FolderVideo("#A-C", "emisio", "progAZ", "", "")
    progsDE = FolderVideo("D-E", "emisio", "progAZ", "", "")
    progsFI = FolderVideo("F-I", "emisio", "progAZ", "", "")
    progsJL = FolderVideo("J-L", "emisio", "progAZ", "", "")
    progsMP = FolderVideo("M-P", "emisio", "progAZ", "", "")
    progsQS = FolderVideo("Q-S", "emisio", "progAZ", "", "")
    progsTV = FolderVideo("T-V", "emisio", "progAZ", "", "")
    progsXZ = FolderVideo("X-Z", "emisio", "progAZ", "", "")

    list = [progsAC, progsDE, progsFI, progsJL, progsMP, progsQS, progsTV,
                 progsXZ]
    return list

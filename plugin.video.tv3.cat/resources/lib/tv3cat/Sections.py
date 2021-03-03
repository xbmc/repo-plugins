from resources.lib.video.FolderVideo import FolderVideo



def getList(strings):

    series = FolderVideo(strings.get('series'), "/series/", "sections", "", "")
    information = FolderVideo(strings.get('informatius'), "/informatius/", "sections", "", "")
    entreteniment = FolderVideo(strings.get('entreteniment'), "/entreteniment/", "sections", "",
                                     "")
    sports = FolderVideo(strings.get('esports'), "/esports/", "sections", "", "")
    documentals = FolderVideo(strings.get('documentals'), "/documentals/", "sections", "", "")
    divulgacio = FolderVideo(strings.get('divulgacio'), "/divulgacio/", "sections", "", "")
    cultura = FolderVideo(strings.get('cultura'), "/cultura/", "sections", "", "")
    musica = FolderVideo(strings.get('musica'), "/musica/", "sections", "", "")
    emissio = FolderVideo(strings.get('emissio'), "/programes/", "dirAZemisio", "", "")
    tots = FolderVideo(strings.get('tots'), "/programes-tots/", "dirAZtots", "", "")

    list = [series, information, entreteniment, sports, documentals, divulgacio,
                 cultura, musica, emissio, tots]

    return list

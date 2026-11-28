from resources.lib.video.FolderVideo import FolderVideo


def getList(strings):
    coleccions = FolderVideo(strings.get('coleccions'), "", "coleccions", "", "")
    directe = FolderVideo(strings.get('directe'), "", "directe", "", "")
    pellicules = FolderVideo(strings.get("pellicules"), "", "pellicules", "", "")
    cercar = FolderVideo(strings.get("cercar"), "", "cercar", "", "")
    return [coleccions, directe, pellicules, cercar]

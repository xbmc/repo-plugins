from . import pcloudapi

p = pcloudapi.PCloudApi()
#auth = p.PerformLogon("username", "password")
p.SetAuth("xxxxxxxxxxxxxxx")
folder = p.ListFolderContents("/")
allFileIDs = [ oneItem["fileid"] for oneItem in folder["metadata"]["contents"] if not oneItem["isfolder"] ]
thumbs = p.GetThumbnails(allFileIDs)
print(thumbs)
# print thumbs[381321361]
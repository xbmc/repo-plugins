# Imports
import os
import sys
import globals as g

# Get parameters script from Voinage's tutorial
def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                    params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                    splitparams={}
                    splitparams=pairsofparams[i].split('=')
                    if (len(splitparams))==2:
                            param[splitparams[0]]=splitparams[1]
    return param

# Get torrent or file status icon
def getIcon(isdir,active,complete,p):
	if isdir>1:
		icon = "dir"
		p=p+3
	elif isdir==0:
		icon = "file"
	else:
		icon = "file"
		p=p+3
	if active==1:
		if complete==1:
			iconcol = "9"
		else:
			if p==0: #Don't Download
				iconcol = "0"
			elif p==1: #Normal
				iconcol = "3"
			elif p==2: #High
				iconcol = "4"
			#Now for downloads, not files
			elif p==3: #Idle
				iconcol = "1"
			elif p==4: #Low
				iconcol = "2"
			elif p==5: #Normal
				iconcol = "3"
			elif p==6: #High
				iconcol = "4"
	else:
		iconcol = "0"	
	return os.path.join(g.__icondir__,icon+'_'+iconcol+'.jpg')

# Colour scheme - NO LONGER USED
# Dld & File Completed: Green
# Dld & File P: High  : Yellow
# Dld & File P: Normal: Blue 
# Dld P: Low   : Purple
# Dld Priority: Idle  : Orange
# Dld Stopped & File Don't Download: Red
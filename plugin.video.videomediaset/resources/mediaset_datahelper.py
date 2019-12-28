from phate89lib import kodiutils

def __get_date_string(dt):
    format = kodiutils.getRegion('datelong')
    format = format.replace("%A",kodiutils.KODILANGUAGE(dt.weekday() + 11))
    format = format.replace("%B",kodiutils.KODILANGUAGE(dt.month + 20))
    return dt.strftime(kodiutils.py2_encode(format))

def __gather_info(prog, infos=None):
    if infos is None:
        infos={}
    if not 'title' in infos and 'title' in prog:
        infos['title']=prog["title"]
    if (not 'title' in infos  or infos['title'] == '') and 'mediasetprogram$brandTitle' in prog:
        infos['title']=prog["mediasetprogram$brandTitle"]
    
    if 'credits' not in infos and 'credits' in prog:
        infos['cast']=[]
        infos['director']=[]
        for person in prog['credits']:
            if person['creditType']=='actor':
                infos['cast'].append(person['personName'])
            elif person['creditType']=='director':
                infos['director'].append(person['personName'])

    if not ('plot' in infos or 'plotoutline' in infos):
        plot=""
        plotoutline=""
        #try to find plotoutline
        if 'shortDescription' in prog:
            plotoutline=prog["shortDescription"]
        elif 'mediasettvseason$shortDescription' in prog:
            plotoutline=prog["mediasettvseason$shortDescription"]
        elif 'description' in prog:
            plotoutline=prog["description"]
        elif 'mediasetprogram$brandDescription' in prog:
            plotoutline=prog["mediasetprogram$brandDescription"]
        elif 'mediasetprogram$subBrandDescription' in prog:
            plotoutline=prog["mediasetprogram$subBrandDescription"]
            
        #try to find plot
        if 'longDescription' in prog:
            plot=prog["longDescription"]
        elif 'description' in prog:
            plotoutline=prog["description"]
        elif 'mediasetprogram$brandDescription' in prog:
            plot=prog["mediasetprogram$brandDescription"]
        elif 'mediasetprogram$subBrandDescription' in prog:
            plot=prog["mediasetprogram$subBrandDescription"]
            
        #fill the other if one is empty
        if plot=="":
            plot=plotoutline
        if plotoutline=="":
            plotoutline=plot
        infos['plot'] = plot
        infos['plotoutline'] = plotoutline
        
    if not 'duration' in infos and 'mediasetprogram$duration' in prog:
        infos['duration'] = prog['mediasetprogram$duration']
    if not 'genre' in infos and 'mediasetprogram$genres' in prog:
        infos['genre']=prog['mediasetprogram$genres']
    elif not 'genre' in infos and 'mediasettvseason$genres' in prog:
        infos['genre']=prog['mediasettvseason$genres']
    if not 'year' in infos and 'year' in prog:
        infos['year']=prog['year']
    if not 'season' in infos and 'tvSeasonNumber' in prog:
        infos['season']=prog['tvSeasonNumber']
    if not 'episode' in infos and 'tvSeasonEpisodeNumber' in prog:
        infos['episode']=prog['tvSeasonEpisodeNumber']
    if 'program' in prog:
        return __gather_info(prog['program'],infos)
    return infos

def __gather_art(prog):
    arts = {}
    if 'thumbnails' in prog:
        if 'image_vertical-264x396' in prog['thumbnails']:
            arts['poster'] = prog['thumbnails']['image_vertical-264x396']['url']
            arts['thumb'] = arts['poster']
        elif 'channel_logo-100x100' in prog['thumbnails']:
            arts['poster'] = prog['thumbnails']['channel_logo-100x100']['url']
            arts['thumb'] = arts['poster']
            
        if 'brand_cover-1440x513' in prog['thumbnails']:
            arts['banner'] = prog['thumbnails']['brand_cover-1440x513']['url']
        elif 'image_header_poster-1440x630' in prog['thumbnails']:
            arts['banner'] = prog['thumbnails']['image_header_poster-1440x630']['url']
        elif 'image_header_poster-1440x433' in prog['thumbnails']:
            arts['banner'] = prog['thumbnails']['image_header_poster-1440x433']['url']
        if 'image_header_poster-1440x630' in prog['thumbnails']:
            arts['landscape'] = prog['thumbnails']['image_header_poster-1440x630']['url']
        elif 'image_header_poster-1440x433' in prog['thumbnails']:
            arts['landscape'] = prog['thumbnails']['image_header_poster-1440x433']['url']
        if 'brand_logo-210x210' in prog['thumbnails']:
            arts['icon'] = prog['thumbnails']['brand_logo-210x210']['url']
    elif 'program' in prog:
        return __gather_art(prog['program'])
    return arts

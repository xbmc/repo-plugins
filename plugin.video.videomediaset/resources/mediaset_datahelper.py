
def _gather_media_type(prog):
    if 'programType' in prog:
        if prog['programType'] == 'movie':
            return 'movie'
        if prog['programType'] == 'episode':
            return 'episode'
    if ('mediasetprogram$brandVerticalSiteCMS' in prog and
            prog['mediasetprogram$brandVerticalSiteCMS'] == 'fiction'):
        return 'tvshow'
    if 'tvSeasonNumber' in prog or 'tvSeasonEpisodeNumber' in prog:
        return 'episode'
    if 'seriesId' in prog and 'mediasetprogram$subBrandId' not in prog:
        return 'tvshow'
    if ('mediasetprogram$subBrandDescription' in prog and
            (prog['mediasetprogram$subBrandDescription'].lower() == 'film' or
             prog['mediasetprogram$subBrandDescription'].lower() == 'documentario')):
        return 'movie'
    return 'video'


def _gather_info(prog, titlewd=False, mediatype=None, infos=None):
    if infos is None:
        infos = {}

    if 'mediatype' not in infos:
        if mediatype:
            infos['mediatype'] = mediatype
        else:
            infos['mediatype'] = _gather_media_type(prog)

    if 'title' not in infos:
        if 'title' in prog:
            infos['title'] = prog["title"]
        elif 'mediasetprogram$brandTitle' in prog:
            infos['title'] = prog["mediasetprogram$brandTitle"]
        if (titlewd and 'mediasetprogram$brandTitle' in prog and
                prog['mediasetprogram$brandTitle'] != ''):
            infos['title'] = '{} - {}'.format(prog['mediasetprogram$brandTitle'], infos['title'])

    if 'credits' in prog:
        if 'cast' not in infos:
            infos['cast'] = []
        if 'director' not in infos:
            infos['director'] = []
        for person in prog['credits']:
            if person['creditType'] == 'actor':
                infos['cast'].append(person['personName'])
            elif person['creditType'] == 'director':
                infos['director'].append(person['personName'])

    if not ('plot' in infos or 'plotoutline' in infos):
        plot = ""
        plotoutline = ""
        # try to find plotoutline
        if 'shortDescription' in prog:
            plotoutline = prog["shortDescription"]
        elif 'mediasettvseason$shortDescription' in prog:
            plotoutline = prog["mediasettvseason$shortDescription"]
        elif 'description' in prog:
            plotoutline = prog["description"]
        elif 'mediasetprogram$brandDescription' in prog:
            plotoutline = prog["mediasetprogram$brandDescription"]
        elif 'mediasetprogram$subBrandDescription' in prog:
            plotoutline = prog["mediasetprogram$subBrandDescription"]

        # try to find plot
        # if 'longDescription' in prog: # longDescription sometimes has -
        #    plot = prog["longDescription"]
        if 'description' in prog:
            plotoutline = prog["description"]
        elif 'mediasetprogram$brandDescription' in prog:
            plot = prog["mediasetprogram$brandDescription"]
        elif 'mediasetprogram$subBrandDescription' in prog:
            plot = prog["mediasetprogram$subBrandDescription"]

        # fill the other if one is empty
        if plot == "":
            plot = plotoutline
        if plotoutline == "":
            plotoutline = plot
        infos['plot'] = plot
        infos['plotoutline'] = plotoutline

    if 'genre' not in infos:
        infos['genre'] = []
    if 'mediasetprogram$genres' in prog:
        infos['genre'].extend(prog['mediasetprogram$genres'])
    if 'mediasettvseason$genres' in prog:
        infos['genre'].extend(prog['mediasettvseason$genres'])
    if 'tags' in prog and prog['tags']:
        for t in prog['tags']:
            if t['scheme'] == 'genre':
                infos['genre'].append(t['title'])

    if 'duration' not in infos and 'mediasetprogram$duration' in prog:
        infos['duration'] = prog['mediasetprogram$duration']
    if 'year' not in infos and 'year' in prog:
        infos['year'] = prog['year']
    if 'season' not in infos and 'tvSeasonNumber' in prog:
        infos['season'] = prog['tvSeasonNumber']
    if 'episode' not in infos and 'tvSeasonEpisodeNumber' in prog:
        infos['episode'] = prog['tvSeasonEpisodeNumber']

    if ('season' in infos and 'episode' in infos):
        infos['tvshowtitle'] = prog['mediasetprogram$brandTitle']

    if 'program' in prog:
        return _gather_info(prog['program'], titlewd=titlewd, infos=infos)
    return infos


def _gather_art(prog):
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
        return _gather_art(prog['program'])
    return arts

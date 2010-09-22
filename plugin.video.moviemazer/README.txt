Program plan:

-- User starts MovieMazer --
showCategories -> addDir -> XBMC_DIR

-- User selects Dir -- 
showCurrent -> getCurrent -> showMovies -> getMovieInfo -> addMovie -> XBMC_MOVIE
showTopTen  -> getTopTen  -> showMovies -> getMovieInfo -> addMovie -> XBMC_MOVIE
showRecent  -> getRecent  -> showMovies -> getMovieInfo -> addMovie -> XBMC_MOVIE

-- User selects Movie --
getTrailers -> askTrailers -> XBMC_PLAYLIST

-- User selects Trailer --
playTrailer -> XBMC_PLAY

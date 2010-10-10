Program plan:

-- User starts MovieMazer --
showCategories -> addDir -> XBMC_DIR

-- User selects Dir -- 
showCurrent -> getCurrent -> showMovies -> getMovieInfo -> addMovie -> XBMC_MOVIE
showTopTen  -> getTopTen  -> showMovies -> getMovieInfo -> addMovie -> XBMC_MOVIE
showRecent  -> getRecent  -> showMovies -> getMovieInfo -> addMovie -> XBMC_MOVIE

-- User selects Movie --
getTrailers -> guessPrefTrailer -> playTrailer -> XBMC_PLAY
getTrailers -> askTrailers -> XBMC_DIALOG

-- User selects Trailer --
playTrailer -> playTrailer -> XBMC_PLAY

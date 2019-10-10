# TheMovieDB Helper [![License](https://img.shields.io/badge/License-GPLv3-blue)](https://github.com/jurialmunkey/plugin.video.themoviedb.helper/blob/master/LICENSE.txt)


## Lists based upon another item
TMDbHelper provides several ways to get TMDb lists related to another item.  
All lists require a `&amp;type=` parameter to be specified. Type can be `movie` `tv` or `person`

An additional parameter is required to specify the item that the list will be based upon:  
`&amp;query=$INFO[ListItem.Title]`  
`&amp;imdb_id=$INFO[ListItem.IMDBNumber]`  
`&amp;tmdb_id=$INFO[ListItem.Property(tmdb_id)]`  

Skinners can also specify the optional `&amp;year=` parameter to get better results when using `&amp;query=`


#### Recommendations  
`plugin://plugin.video.themoviedb.helper?info=recommendations&amp;type=movie&amp;imdb_id=$INFO[ListItem.IMDBNumber]`

Types: `movie` `tv`  

#### Similar  
`plugin://plugin.video.themoviedb.helper?info=similar&amp;type=movie&amp;imdb_id=$INFO[ListItem.IMDBNumber]`

Types: `movie` `tv`  

#### Cast  
`plugin://plugin.video.themoviedb.helper?info=cast&amp;type=movie&amp;imdb_id=$INFO[ListItem.IMDBNumber]`

Types: `movie` `tv`  

#### Crew  
`plugin://plugin.video.themoviedb.helper?info=crew&amp;type=movie&amp;imdb_id=$INFO[ListItem.IMDBNumber]`

Types: `movie` `tv`  

#### Keywords  
`plugin://plugin.video.themoviedb.helper?info=movie_keywords&amp;type=movie&amp;imdb_id=$INFO[ListItem.IMDBNumber]`

Types: `movie`  

#### Reviews  
`plugin://plugin.video.themoviedb.helper?info=reviews&amp;type=movie&amp;imdb_id=$INFO[ListItem.IMDBNumber]`

Types: `movie` `tv`  

#### Posters  
`plugin://plugin.video.themoviedb.helper?info=posters&amp;type=movie&amp;imdb_id=$INFO[ListItem.IMDBNumber]`

Types: `movie` `tv`  

#### Fanart  
`plugin://plugin.video.themoviedb.helper?info=fanart&amp;type=movie&amp;imdb_id=$INFO[ListItem.IMDBNumber]`

Types: `movie` `tv`  

#### Seasons  
`plugin://plugin.video.themoviedb.helper?info=seasons&amp;type=tv&amp;query=$INFO[ListItem.TvShowTitle]`

Types: `tv`  

#### Episodes in Season  
`plugin://plugin.video.themoviedb.helper?info=episodes&amp;type=tv&amp;query=$INFO[ListItem.TvShowTitle]&amp;season=2`

Types: `tv`  
Requires: `&amp;season=`  

#### Episode Cast  
`plugin://plugin.video.themoviedb.helper?info=episode_cast&amp;type=tv&amp;query=$INFO[ListItem.TvShowTitle]&amp;season=2&amp;episode=1`

Types: `tv`  
Requires: `&amp;season=` `&amp;episode=`  

#### Episode Thumbs  
`plugin://plugin.video.themoviedb.helper?info=episode_thumbs&amp;type=tv&amp;query=$INFO[ListItem.TvShowTitle]&amp;season=2&amp;episode=1`

Types: `tv`  
Requires: `&amp;season=` `&amp;episode=`  

#### Movies an Actor is Cast in  
`plugin://plugin.video.themoviedb.helper?info=stars_in_movies&amp;type=person&amp;query=$INFO[ListItem.Label]`

Types: `person`  

#### TvShows an Actor is Cast in  
`plugin://plugin.video.themoviedb.helper?info=stars_in_tvshows&amp;type=person&amp;query=$INFO[ListItem.Label]`

Types: `person`  

#### Movies a Person is a Crew Member on
`plugin://plugin.video.themoviedb.helper?info=crew_in_movies&amp;type=person&amp;query=$INFO[ListItem.Label]`

Types: `person`  

#### TvShows a Person is a Crew Member on
`plugin://plugin.video.themoviedb.helper?info=crew_in_tvshows&amp;type=person&amp;query=$INFO[ListItem.Label]`

Types: `person`  

#### Images of a Person
`plugin://plugin.video.themoviedb.helper?info=images&amp;type=person&amp;query=$INFO[ListItem.Label]`

Types: `person`  

#### All Movies in a Collection (aka Set)  
`plugin://plugin.video.themoviedb.helper?info=collection&amp;type=movie&amp;query=$INFO[ListItem.Set]`

Types: `movie`  




## Default Lists  
These lists are bsed upon trends such as recent releases or popularity. Only a type paramater is required.

#### Popular  
`plugin://plugin.video.themoviedb.helper?info=popular&amp;type=movie`

Types: `movie` `tv` `person`  

#### Top Rated  
`plugin://plugin.video.themoviedb.helper?info=top_rated&amp;type=movie`

Types: `movie` `tv`   

#### Upcoming  
`plugin://plugin.video.themoviedb.helper?info=upcoming&amp;type=movie`

Types: `movie`  

#### Airing Today  
`plugin://plugin.video.themoviedb.helper?info=airing_today&amp;type=tv`

Types: `tv`  

#### Now Playing In Theatres  
`plugin://plugin.video.themoviedb.helper?info=now_playing&amp;type=movie`

Types: `movie`  

#### Currently Airing (in the last week)  
`plugin://plugin.video.themoviedb.helper?info=on_the_air&amp;type=tv`

Types: `tv`   




## Search  
Provides a list of items with titles matching the search query.  
`plugin://plugin.video.themoviedb.helper?info=search&amp;type=movie&amp;query=$INFO[ListItem.Label]`  

Types: `movie` `tv` `person`



## Discover  
More complex searching for items of a specific type that much several parameters:  
`plugin://plugin.video.themoviedb.helper?info=discover&amp;type=movie&amp;with_cast=$INFO[ListItem.Label]`  

Types: `movie` `tv` 

Optional Parameters:  
`&amp;with_cast=`  Includes items that have one of the specified people as a cast member  
`&amp;with_crew=`  Includes items that have one of the specified people as a crew member  
`&amp;with_people=`  Includes items that have one of the specified people as a cast or crew member  
`&amp;with_companies=`  Includes items from a matching movie studio   
`&amp;with_genres=`  Includes items with a matching genre  
`&amp;without_genres=`  Excludes items with a matching genre  


Discover will lookup the TMDb IDs for the values in with_genres/with_companies etc. If the TMDb ID is already available, it can be used instead by specifying the with_id parameter:  
`&amp;with_id=True`  

The default discover behaviour is to provide items matching ANY of the values in with_genres/with_companies etc.To retrieve items that match ALL values, change the with_separator to AND:  
`&amp;with_separator=AND`  

If multiple values are separated by a "/" but only the first matching value is desired, then change the with_separator to NONE:  
`&amp;with_separator=NONE`  


## Optional Parameters for ALL Lists  
Only include items that have the specified key that matches the specified value.  
`&amp;filter_key=KEY&amp;filter_value=VALUE`  

Exclude all items that have the specified key that matches the specified value.  
`&amp;exclude_key=KEY&amp;exclude_value=VALUE`  

Example:
`plugin://plugin.video.themoviedb.helper/?info=crew_in_movies&amp;type=person&amp;filter_key=job&amp;filter_value=Director&amp;query=$INFO[ListItem.Director]&amp;exclude_key=title&amp;exclude_value=$INFO[ListItem.Title]`  
This plugin path will get all movies were the Director was a crew member and their job was director. The currently selected movie will be excluded from the list.




## Detailed Item  
`plugin://plugin.video.themoviedb.helper/?info=details&amp;type=movie&amp;query=$INFO[ListItem.Title]`  

Provides additional details about the current item. 

**InfoLabels**  
`ListItem.Title`  
`ListItem.Plot`   
`ListItem.Genre`   
`ListItem.Studio`   
`ListItem.MPAA`   
`ListItem.Country`   
`ListItem.Year`   
`ListItem.Premiered`  
`ListItem.Rating`  
`ListItem.Duration`  

**ListItem.Property(property)**  
`ListItem.Property(tmdb_id)`  
`ListItem.Property(Genre.X.Name)`  
`ListItem.Property(Genre.X.ID)`  
`ListItem.Property(Studio.X.Name)`  
`ListItem.Property(Studio.X.ID)`  
`ListItem.Property(Country.X.Name)`  
`ListItem.Property(Country.X.ID)`  
`ListItem.Property(birthday)`  
`ListItem.Property(deathday)`  
`ListItem.Property(aliases)`  
`ListItem.Property(role)`  
`ListItem.Property(born)`  
`ListItem.Property(budget)`  
`ListItem.Property(revenue)`  

**Additional Properties if OMDb api key specified**  
`ListItem.Property(awards)`  
`ListItem.Property(metacritic_rating)`  
`ListItem.Property(imdb_rating)`  
`ListItem.Property(imdb_votes)`  
`ListItem.Property(rottentomatoes_rating)`  
`ListItem.Property(rottentomatoes_image)`  
`ListItem.Property(rottentomatoes_consensus)`  
`ListItem.Property(rottentomatoes_reviewtotal)`  
`ListItem.Property(rottentomatoes_reviewsfresh)`  
`ListItem.Property(rottentomatoes_reviewsrotten)`  
`ListItem.Property(rottentomatoes_usermeter)`  
`ListItem.Property(rottentomatoes_userreviews)`  


## Script Functions  
TMDb Helper also provides several script functions to assist with making an extended info type experience. See Arctic Zephyr 2 for an example of implementation


Arguments:  
`add_path=`  
e.g. `RunScript(plugin.video.themoviedb.helper,add_path=$INFO[ListItem.FolderPath])`  
Adds the path to `Window(Home).Property(TMDBHelper.Current)`  
Remebers a history of all previously added paths  

`del_path`  
e.g. `RunScript(plugin.video.themoviedb.helper,del_path)`  
Deletes the path in TMDBHelper.Current and replaces it with the previously stored path in the history  

`reset_path`  
e.g. `RunScript(plugin.video.themoviedb.helper,reset_path)`  
Deletes the current path and wipes all history.

`call_id=`  
e.g. `RunScript(plugin.video.themoviedb.helper,add_path=$INFO[ListItem.FolderPath],call_id=1137)`  
After completing the other actions, the script will close all dialogs and do `ActivateWindow(call_id)`  

`call_path=`  
e.g. `RunScript(plugin.video.themoviedb.helper,add_path=$INFO[ListItem.FolderPath],call_path=$INFO[ListItem.FolderPath])`  
After completing the other actions, the script will close all dialogs and do `ActivateWindow(videos, call_path, return)`  

`prevent_del`  
e.g. `RunScript(plugin.video.themoviedb.helper,add_path=$INFO[ListItem.FolderPath],call_id=1137,prevent_del)`  
Will set a lock that prevents `del_path` from deleting `Window(Home).Property(TMDbHelper.Current)` the first time it is called.  

`add_query=` `type=`  
e.g. `RunScript(plugin.video.themoviedb.helper,add_query=$INFO[ListItem.Writer],type=person,call_id=1137,prevent_del)`  
Finds the TMDb ID for the specified item and adds the detailed item path for it to `Window(Home).Property(TMDbHelper.Current)`  
If multiple "/" separated items exist in the infolabel, the user is prompted to select which item to use as the search query for the detailed item. If multiple items subsequently match the search query, the user is prompted to select the desired item from a list of possible matches.

`add_prop=` `prop_id=`  
e.g. `RunScript(plugin.video.themoviedb.helper,add_prop=$INFO[ListItem.Genre],prop_id=SelectedGenre)`  
Prompts user to select an item from a list of items separated by "/". The selected item is then added to a window property as specified by prop_id. For instance, the above path will ask the user to select a genre from all listed genres for a movie and then will add that genre to `Window(Home).Property(TMDbHelper.SelectedGenre)`

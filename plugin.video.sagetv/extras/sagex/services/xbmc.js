/*
* Name: GetMediaFilesWithSubsetOfInfo
* Author: lehighbri
*
* Return: array of mediafile objects with minimum set of information
* Purpose: will grab all mediafiles from sage and only return the information that the XBMC cares about thereby
* reducing the amount of traffic
* 
**********************/
function GetTVMediaFilesWithSubsetOfProperties() {
   var shows = new java.util.ArrayList();
   var files =  MediaFileAPI.GetMediaFiles("T");
   var s = files.length;
   for (var i=0;i<s;i++) {
      var mf = files[i];
      var show = java.util.HashMap();
      show.put('MediaFileID', ""+MediaFileAPI.GetMediaFileID(mf));
      show.put('ShowTitle', MediaFileAPI.GetMediaTitle(mf));
      show.put('ShowExternalID', ShowAPI.GetShowExternalID(mf));
      show.put('AiringStartTime', AiringAPI.GetAiringStartTime(mf));
      shows.add(show);
   }
   return shows;
}

function GetMediaFilesForShowWithSubsetOfProperties(showtitle) {
   var shows = new java.util.ArrayList();
   var files;
   if(showtitle == "") {
      files = MediaFileAPI.GetMediaFiles("T");
   }
   else {
      files = Database.FilterByMethod(MediaFileAPI.GetMediaFiles("T"), "GetMediaTitle", showtitle, true);
   }
   var s = files.length;
   for (var i=0;i<s;i++) {
      var mf = files[i];
      var show = java.util.HashMap();
      show.put('MediaFileID', ""+MediaFileAPI.GetMediaFileID(mf));
      if(showtitle == "") {
         show.put('ShowTitle', ShowAPI.GetShowTitle(mf));
      }
      else {
         show.put('ShowTitle', showtitle);
      }
      show.put('ShowExternalID', ShowAPI.GetShowExternalID(mf));
      show.put('EpisodeTitle', ShowAPI.GetShowEpisode(mf));
      show.put('EpisodeDescription', ShowAPI.GetShowDescription(mf));
      show.put('ShowGenre', ShowAPI.GetShowCategoriesString(mf));
      show.put('AiringID', ""+AiringAPI.GetAiringID(mf));
      show.put('SeasonNumber', ShowAPI.GetShowSeasonNumber(mf));
      show.put('EpisodeNumber', ShowAPI.GetShowEpisodeNumber(mf));
      show.put('AiringChannelName', AiringAPI.GetAiringChannelName(mf));
      show.put('IsFavorite', AiringAPI.IsFavorite(mf));
      show.put('AiringStartTime', AiringAPI.GetAiringStartTime(mf));
      show.put('OriginalAiringDate', ShowAPI.GetOriginalAiringDate(mf));
      show.put('SegmentFiles', MediaFileAPI.GetSegmentFiles(mf));
      show.put('WatchedDuration', AiringAPI.GetWatchedDuration(mf));
      show.put('IsWatched', AiringAPI.IsWatched(mf));
      shows.add(show);
   }
   return shows;
}

function SearchForMediaFiles(searchterm) {
   var shows = new java.util.ArrayList();
   //searchresults will be a vector, not an arraylist like in the functions above
   var searchresults = Database.FilterByMethod(Database.SearchSelectedFields(searchterm,false,true,true,false,false,false,false,false,false,false,"T"), "GetMediaFileForAiring", null, false);
   var s = searchresults.size();
   for (var i=0;i<s;i++) {
      var airing = searchresults.get(i);
      var show = java.util.HashMap();
      var airingID = AiringAPI.GetAiringID(airing);
      if (airingID != 0){
          mf = AiringAPI.GetMediaFileForAiring(AiringAPI.GetAiringForID(airingID));
          show.put('MediaFileID', ""+MediaFileAPI.GetMediaFileID(mf));
          show.put('AiringID', ""+airingID);
          show.put('ShowTitle', ShowAPI.GetShowTitle(mf));
          show.put('ShowExternalID', ShowAPI.GetShowExternalID(mf));
          show.put('EpisodeTitle', ShowAPI.GetShowEpisode(mf));
          show.put('EpisodeDescription', ShowAPI.GetShowDescription(mf));
          show.put('ShowGenre', ShowAPI.GetShowCategoriesString(mf));
          show.put('SeasonNumber', ShowAPI.GetShowSeasonNumber(mf));
          show.put('EpisodeNumber', ShowAPI.GetShowEpisodeNumber(mf));
          show.put('AiringChannelName', AiringAPI.GetAiringChannelName(mf));
          show.put('IsFavorite', AiringAPI.IsFavorite(mf));
          show.put('AiringStartTime', AiringAPI.GetAiringStartTime(mf));
          show.put('OriginalAiringDate', ShowAPI.GetOriginalAiringDate(mf));
          show.put('SegmentFiles', MediaFileAPI.GetSegmentFiles(mf));
          show.put('WatchedDuration', AiringAPI.GetWatchedDuration(mf));
          show.put('IsWatched', AiringAPI.IsWatched(mf));
          shows.add(show);
      }
   }
   return shows;
}

function GetTVMediaFilesGroupedByTitle() {
   var grouped = new java.util.HashMap();
   var files = GetTVMediaFilesWithSubsetOfProperties();
   var s = files.size();
   for (var i=0;i<s;i++) {
      var file = files.get(i);
      var shows = grouped.get(file.get('ShowTitle'));
      if (shows==null) {
         shows = new java.util.ArrayList();
         grouped.put(file.get('ShowTitle'), shows);
         // add full mediafile
      }
      shows.add(file);
   }
   return grouped;
}
from xbmcswift2 import Plugin
from xbmcswift2 import xbmc
import mlb_player
import mlbtv_stream_api
import mlb_exceptions
from globals import *
from mlb_games_queue import MlbGamesQueue

plugin = Plugin()

@plugin.route('/')
def index():
    item = {
        'label': 'Play BasesLoaded',
        'path': plugin.url_for(play_basesloaded.__name__)
    }
    return plugin.finish([item])

@plugin.route('/basesloaded')
def play_basesloaded():
    delay_sec = 20
    refresh_sec = 10
    games_queue = MlbGamesQueue(delay_sec, refresh_sec, plugin)

    # Need a way of checking if there are any current games, not just
    # games that are currently *on*
    # Maybe display to user: "There are N games on right now"
    games = games_queue.get()
    if games is None:
        plugin.notify("No games on")
        return

    monitor = xbmc.Monitor()
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    player = mlb_player.MlbPlayer(mlb_playlist=playlist)

    curr_game = None
    streams_not_found = set([])
    while not monitor.abortRequested():
        # TODO encapsulate all this logic in an object
        if not games:
            # TODO better UX for this situation
            xbmc.log("No game found")
            xbmc.sleep(5000)
            continue

        # Update state of curr_game
        if curr_game is not None:
            new_curr_game = [game for game in games if game['state'].away_team == curr_game['state'].away_team
                                                   and game['state'].home_team == curr_game['state'].home_team]
            if not new_curr_game:
                curr_game = None
            else:
                curr_game = new_curr_game[0]

        # Iterate through best games in order, choosing first one a stream exists for
        for game in games:
            if curr_game == game:
                xbmc.log("Not switching because current game is still best game")
                break

            try:
                # Only switch games if:
                #  curr_game is None (either no curr_game or it's in commercial break)
                #  The change in leverage is > 1.5 and there's a new batter in curr_game
                #  game has a better leverage than curr_game and curr_game is below average leverage (1.0) and there's a new batter in curr_game
                curr_game_none = curr_game is None
                new_batter = curr_game and curr_game['state'].new_batter
                large_leverage_diff = curr_game and (game['leverage_index'] - curr_game['leverage_index'] > 1.5)
                game_better = curr_game and game['leverage_index'] > curr_game['leverage_index']
                curr_game_below_avg = curr_game and curr_game['leverage_index'] < 1.0
                if curr_game_none or (new_batter and (large_leverage_diff or (curr_game_below_avg and game_better))):
                    if (game['state'].home_team, game['state'].away_team) in streams_not_found:
                        xbmc.log("Already know stream doesn't exist for game {0}".format(game))
                        continue

                    stream = mlbtv_stream_api.get_stream(game['state'].home_team, game['state'].away_team)

                    xbmc.log("Switching from {0} to {1}".format(curr_game, game))
                    curr_game = game
                    xbmc.log("stream: " + stream)
                    player.play_video(stream)

                if curr_game == game:
                    xbmc.log("Current game is in commercial break or is over")
                if curr_game != game and (game['leverage_index'] - curr_game['leverage_index']) <= 1.5:
                    xbmc.log("{0} is better game, but not enough better to switch from {1}".format(game, curr_game))
                elif curr_game != game and (game['leverage_index'] - curr_game['leverage_index']) > 1.5:
                    xbmc.log("{0} is a better game, but {1} still has a batter at the plate".format(game, curr_game))

                break
            except mlb_exceptions.StreamNotFoundException:
                streams_not_found.add((game['state'].home_team, game['state'].away_team),)
                xbmc.log("Stream not found for {0}. Setting cache to {1}".format(game, streams_not_found))
                continue

        if monitor.waitForAbort(refresh_sec) or not player.isPlayingVideo():
            break

        # Update games
        games = games_queue.get()

if __name__ == '__main__':
    plugin.run()

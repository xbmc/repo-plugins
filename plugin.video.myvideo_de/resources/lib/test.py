import scraper

def test():
    path_list = (
        'Top_100',
        '/Top_100/Top_100_Charts',
        '/Top_100/Top_100_Single_Charts',
        '/Top_100/Top_100_Serien',
        '/Top_100/Top_100_Entertainment',
        '/Top_100/Top_100_Musik_Clips',
        '/Top_100/Top_100_Filme',
        'Videos_A-Z',
        'Videos_A-Z/Videos_in_Kategorien',
        '/Videos_A-Z?lpage=2&searchWord=&searchOrder=1',
        'Serien',
        'Top_100/Top_100_Serien',
        '/Serien/Alle_Serien_A-Z',
        '/channel/17-Meter',
        '/iframe.php?lpage=2&function=mv_charts&action=highlight_clips&page=9669699&tab=1',
        '/channel/ahnungslos-prosieben',
        '/iframe.php?lpage=2&function=mv_charts&action=full_episodes&page=9150775&tab=1',
        '/channel/videovalis_albert-sagt-natur',
        '/channel/zwei-bei-kallwass',
        '/Serien/ProSieben',
        '/Serien/Sony_Retro',
        '/Serien/Welt_der_Wunder',
        '/Serien/Weitere_Serien',
        '/channel/30-minuten-deutschland',
        '/channel/we-love-mma',
        '/iframe.php?lpage=2&function=mv_charts&action=full_episodes&page=9244249&tab=1',
        'Filme',
        'Top_100/Top_100_Filme',
        '/Videos_A-Z?searchChannelID=369&searchChannel=Film',
        '/Videos_A-Z?lpage=2&searchWord=&searchChannelID=369&searchChannel=Film&searchOrder=1',
        '/Filme/Comedy',
        '/Filme/Horror',
        '/Filme/Thriller',
        '/iframe.php?lpage=2&function=mv_success_box&action=filme_video_list&searchGroup=74590&searchOrder=1',
        '/Filme/Konzerte',
        'Musik',
        '/Musik/Neue_Musik_Videos',
        '/Musik/Pop',
        '/iframe.php?lpage=2&function=mv_charts&action=music_videos&page=music_pop&tab=0',
        '/Musik/Musik_K%C3%Bcnstler',
        '/Musik/Musik_K%C3%BCnstler?lpage=4',
        '/channel/daughtry-official',
    )
    for path in path_list:
        try:
            items, next_page, prev_page = scraper.get_path(path)
        except NotImplementedError:
            raise Exception('No scraper found for path: %s' % path)
        if not items:
            raise Exception('No items found for path: %s' % path)

if __name__ == '__main__':
    test()
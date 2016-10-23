import foxsportsnl


def test_tree_walk():
    items = foxsportsnl.index()
    assert len(items) > 1
    for item in items:
        assert 'label' in item
        assert 'path' in item
        assert 'endpoint' in item['path']
        assert 'category_id' in item['path']
        videos = foxsportsnl.show_category(item['path']['category_id'])
        assert len(videos) == 50
        for video in videos:
            assert 'label' in video
            assert 'thumbnail' in video
            assert 'path' in video
            assert 'endpoint' in video['path']
            assert 'video_id' in video['path']
            assert 'is_playable' in video
            assert video['is_playable'] is True
            playlist_url = foxsportsnl.video_id_to_playlist_url(
                video['path']['video_id']
            )
            assert playlist_url.endswith('playlist.m3u8')

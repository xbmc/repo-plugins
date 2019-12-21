import nos


def test_tree_walk():
    items = nos.index()
    assert len(items) > 1
    for item in items:
        assert 'label' in item
        assert 'path' in item
        assert 'endpoint' in item['path']
        assert 'category_url' in item['path']
        videos = nos.show_category(item['path']['category_url'])
        assert len(videos) >= 1
        for video in videos:
            assert 'label' in video
            assert 'path' in video
            assert 'endpoint' in video['path']
            assert 'video_url' in video['path']
            assert 'is_playable' in video
            assert video['is_playable'] is True
            file_url = nos.video_url_to_file_url(
                video['path']['video_url']
            )
            assert file_url.endswith('.mp4')

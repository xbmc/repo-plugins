import requests


facebook_pages = [
    'https://www.facebook.com/hk.nextmedia/videos/',
    'https://www.facebook.com/standnewshk/videos/',
]

for page in facebook_pages:
    response = requests.get(
        page,
    )

    pos_start = response.text.find('hd_src')
    if pos_start > -1:
        print(pos_start)
        pos_end = response.text.find('",', pos_start)
        print(pos_end)
        if pos_end > -1:
            url = response.text[pos_start + 9: pos_end].replace('\\', '')
            print(url)
            # print(url.encode('utf-8').decode('unicode_escape'))
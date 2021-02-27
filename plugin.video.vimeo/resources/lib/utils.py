import re


def webvtt_to_srt(webvtt):
    srt = ""
    counter = 1

    for line in webvtt.split("\n"):
        if line.startswith("WEBVTT"):
            continue
        if counter == 1 and line == "":
            continue

        matches = re.match(r"^(\d{2}):(\d{2}).(\d{3})\s-->\s(\d{2}):(\d{2}).(\d{3})", line)
        if matches:
            srt += str(counter) + "\n"
            srt += "00:{}:{},{} --> 00:{}:{},{}\n".format(
                matches.group(1),
                matches.group(2),
                matches.group(3),
                matches.group(4),
                matches.group(5),
                matches.group(6),
            )
            counter += 1
        else:
            srt += line + "\n"

    return srt[:-1]

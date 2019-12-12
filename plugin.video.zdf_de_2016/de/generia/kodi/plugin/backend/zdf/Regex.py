import re

def getTagPattern(tag, class_):
    return re.compile('<' + tag + '[^>]*class="([^"]*' + class_ + '[^"]*)"[^>]*>', re.DOTALL)

def getAttrPattern(attr):
    return re.compile(attr + '="([^"]*)"', re.DOTALL)

def getTag(tag, string, match):
    if match is None:
        return None

    i = match.start(0)
    endTag = '</' + tag + '>'
    j = string.find(endTag, i) + len(endTag)
    result = string[i:j]
    return result

def compile(regex):
    return re.compile(regex, re.DOTALL)

def stripTag(tag, string):
    return re.sub(r'<' + tag + '[^>]*>[^<]*</' + tag + '>', '', string)


def cleanTags(string):
    cleaned = re.sub(r'</?[^>]*>', '', string)
    cleaned = cleaned.replace("&#39;", "'")
    return cleaned
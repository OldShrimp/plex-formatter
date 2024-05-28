import os, shutil
import argparse

def findVideos(filePath):
    videos = []
    if os.path.exists(filePath):
        _findVideos(filePath, videos)
    else:
        print("error: " + filePath + " not a valid path.")
    return videos

def _findVideos(filePath, videos):
    if os.path.isfile(filePath):
        if isVideo(os.path.split(filePath)[-1]):
            videos.append(filePath)
    elif os.path.isdir(filePath):
        for file in os.listdir(filePath):
            _findVideos(filePath + "/" + file, videos)

def findDivider(filename):
    divider = ' '
    if len(filename.split()) < len(filename.split('.')):
        divider = '.'
    return divider

def splitExtension(filename):
    extension = filename.split('.')[-1]
    return [filename[:-(len(extension) + 1)], extension]

def isVideo(filename):
    ext = filename.split('.')[-1]
    video_extensions = ["mp4", "mkv", "wmv", "avi", "mov", "avchd", "flv", "f4v", "swf"]
    if ext.lower() in video_extensions:
        return True
    return False

def isTag(word):
    tags = ["4k", "2160", "2160p", "1080", "1080p", "720", "720p", "brrip", "webrip", "hdtv", 
            "amzn", "x264", "h264", "hevc", "h", "264", "265", "h265", "av1"]
    if word.lower() in tags:
        return True
    return False

def isMovie(split_filename):
    for word in split_filename:
        if len(word) == 4 and word.isdigit() and word > "1900" and word < "2100":
            return True
    return False

def isShow(split_filename):
    season_found = False
    episode_found = False
    for word in split_filename:
        if len(word) == 3:
            word_lowercase = word.lower()
            if word_lowercase[0] == 's' and word_lowercase[1].isdigit() and word_lowercase[2].isdigit():
                season_found = True
            if word_lowercase[0] == 'e' and word_lowercase[1].isdigit() and word_lowercase[2].isdigit():
                episode_found = True
            if season_found and episode_found:
                return True
    return False

def formatMovieTitle(vid):
    year = ""
    for word in vid:
        if len(word) == 4 and word.isdigit() and word > "1900" and word < "2100":
            year = word
    title = " ".join(vid[:vid.index(year)]).title()

    return title + " (" + year + ")"

def formatShowTitle(vid):
    season = ""
    episode = ""
    first_tag = ""
    for word in vid:
        word_lowercase = word.lower()
        if word_lowercase[0] == 's' and word_lowercase[1].isdigit() and word_lowercase[2].isdigit():
            season = word
        elif word_lowercase[0] == 'e' and word_lowercase[1].isdigit() and word_lowercase[2].isdigit():
            episode = word
        elif first_tag != "" and isTag(word):
            first_tag = word
   
    show = " ".join(vid[:vid.index(season)]).title()
    episode_name = ""
    if (first_tag == ""):
        episode_name = " ".join(vid[vid.index(episode)+1:]).title()
    else:
        episode_name = " ".join(vid[vid.index(episode)+1:vid.index(first_tag)]).title()
    return show + " - " + season.lower() + episode.lower() + " - " + episode_name

def createMoviePath(dest, file):
    return os.path.join(dest, "Movies", splitExtension(file)[0], file)

def createShowPath(dest, file):
    show_name = file[:file.index(" -")]
    season = "Season " + file[file.index("- s")+3:file.index("- s")+5]
    
    return os.path.join(dest, "Shows", show_name, season, file)

def copyFile(vidSrc, dest):
    ensurePath(os.path.split(dest)[0])
    if os.path.exists(dest):
        print(dest + " already exists")
    else:
        print("copying " + vidSrc + " to " + dest)
        shutil.copy(vidSrc, dest)

def ensurePath(filePath):
    if not os.path.exists(filePath):
        ensurePath(os.path.split(filePath)[0])
        os.mkdir(filePath)

def createPlexPath(srcPath, destPath):
    file = splitExtension(os.path.split(srcPath)[1])
    filename_split = file[0].split(findDivider(file[0]))
    filename_cleaned = []
    for word in filename_split:
        word_cleaned = removeSymbols(word)
        if word_cleaned != "" and not isTag(word_cleaned):
            filename_cleaned.append(word_cleaned)

    if isShow(filename_cleaned):
        filename = formatShowTitle(filename_cleaned)
        return createShowPath(destPath, filename + '.' + file[1])
    if isMovie(filename_cleaned):
        filename = formatMovieTitle(filename_cleaned)
        return createMoviePath(destPath, filename + '.' + file[1])
    return ""

def removeSymbols(string):
    newStr = ""
    for ch in string:
        if ch.isalnum():
            newStr += ch
    return newStr

def main(args):
    src = os.path.expanduser(args.src)
    dest = os.path.expanduser(args.dest)
    video_paths = findVideos(src)

    for vid in video_paths:
        output_path = createPlexPath(vid, dest)
        if output_path == "":
            print("could not process " + vid)
        else:
            copyFile(vid, output_path)

parser = argparse.ArgumentParser("Copy video files from one directory to another and format them for use in Plex.")
parser.add_argument("src", default=os.path.join("~", "Downloads"), nargs='?', help="Source directory or file to be copied. Defaults to User/Downloads.")
parser.add_argument("dest", default=os.path.join("~", "Videos"), nargs='?', help="Destination folder for formatted copies of any video files in src. Defaults to User/Videos.")
args = parser.parse_args()
main(args)
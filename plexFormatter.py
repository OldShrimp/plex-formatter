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
            _findVideos(os.path.join(filePath, file), videos)

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
    tags = ["4k", "2160", "2160p", "1080", "1080p", "720", "720p", "brrip", "web", "webrip", "hdtv", 
            "amzn", "nf", "x264", "h264", "hevc", "h", "264", "265", "h265", "av1"]
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
        if len(word) == 3 or len(word) == 6:
            word_lowercase = word.lower()
            if word_lowercase[0] == 's' and word_lowercase[1].isdigit() and word_lowercase[2].isdigit():
                season_found = True
            if word_lowercase[-3] == 'e' and word_lowercase[-2].isdigit() and word_lowercase[-1].isdigit():
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
    season_index = -1
    episode_index = -1
    first_tag_index = -1
    for word in vid:
        word_lowercase = word.lower()
        if len(word) > 2 and word_lowercase[0] == 's' and word_lowercase[1].isdigit() and word_lowercase[2].isdigit():
            season_index = vid.index(word)
        elif len(word) > 2 and word_lowercase[len(word)-3] == 'e' and word_lowercase[len(word)-2].isdigit() and word_lowercase[len(word)-1].isdigit():
            episode_index_index = vid.index(word)
        elif isTag(word):
            first_tag_index = vid.index(word)
            break

    show = " ".join(vid[:season_index]).title()
    if len(vid[season_index]) == 6:
        episode_index = season_index
        show += " - " + vid[season_index].lower() + " - "
    else:
        show += " - " + vid[season_index].lower() + vid[episode_index].lower() + " - "
    if (first_tag_index == -1):
        show += " ".join(vid[episode_index+1:]).title()
    else:
        show += " ".join(vid[episode_index+1:first_tag_index]).title()
    return show

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
        if word_cleaned != "":
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

def processPath(src, dest):
    video_paths = findVideos(src)

    for vid in video_paths:
        output_path = createPlexPath(vid, dest)
        if output_path == "":
            print("could not process " + vid)
        else:
            print("processing " + vid)
            copyFile(vid, output_path)
            print("completed " + output_path)

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
#main(args)
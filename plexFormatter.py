import os, shutil
import argparse
# arguments: source and destination folders. source defaults to ~/Downloads destination defaults to ~/Videos 
# check to see if destination/Movies and destination/Shows exist, make if not
# recursively check folders for movie files. split filenames on . then check last for extension
# 

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
    match ext:
        case "mp4":
            return True
        case "mkv":
            return True
        case _: 
            return False

def removeSymbols(string):
    newStr = ""
    for ch in string:
        if ch.isalnum():
            newStr += ch
    return newStr

def isTag(word):
    match word.lower():
        case "1080":
            return True
        case "1080p":
            return True
        case "720":
            return True
        case "720p":
            return True
        case "brrip":
            return True
        case "webrip":
            return True
        case "hdtv":
            return True
        case "amzn":
            return True
        case _:
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
        elif isTag(word_lowercase) and first_tag == "":
            first_tag = word
   
    show = " ".join(vid[:vid.index(season)]).title()
    episode_name = ""
    if (first_tag == ""):
        episode_name = " ".join(vid[vid.index(episode):]).title()
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
        if word_cleaned != "":
            filename_cleaned.append(word_cleaned)

    if isShow(filename_cleaned):
        filename = formatShowTitle(filename_cleaned)
        return createShowPath(destPath, filename + '.' + file[1])
    if isMovie(filename_cleaned):
        filename = formatMovieTitle(filename_cleaned)
        return createMoviePath(destPath, filename + '.' + file[1])
    return ""

parser = argparse.ArgumentParser("Copy video files from one directory to another and format them for use in Plex.")
parser.add_argument("src", default="~/Downloads", nargs='?')
parser.add_argument("dest", default="~/Videos", nargs='?')
args = parser.parse_args()

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

main(args)
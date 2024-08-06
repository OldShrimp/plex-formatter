import os, shutil, logging
import argparse
from logging.handlers import RotatingFileHandler
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from time import sleep

def findVideos(filePath):
    videos = []
    if os.path.exists(filePath):
        _findVideos(filePath, videos)
        logger.info(findVideos.__name__ + ": " + filePath +" complete\n")
    else:
        logger.warning(findVideos.__name__ + ": " + filePath + " not a valid path.")
    return videos

def _findVideos(filePath, videos):
    if os.path.isfile(filePath):
        if isVideo(os.path.split(filePath)[-1]):
            logger.info("video file found at " + filePath)
            videos.append(filePath)
    elif os.path.isdir(filePath):
        for file in os.listdir(filePath):
            #logger.debug("searching directory " + filePath)
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
    if splitExtension(filename)[1].lower() in config.extensions:
        return True
    return False

def isTag(word):
    if word.lower() in config.tags:
        return True
    return False

def isMovie(split_filename):
    for word in split_filename:
        if len(word) == 4 and word.isdigit() and not isTag(word):
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
        if len(word) == 4 and word.isdigit() and not isTag(word):
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
        logger.info(dest + " already exists")
    else:
        shutil.copyfile(vidSrc, dest)
        logger.info("completed " + dest)

def moveFile(vidSrc, dest):
    ensurePath(os.path.split(dest)[0])
    if os.path.exists(dest):
        logger.info(dest + " already exists")
    else:
        shutil.move(vidSrc, dest)
        logger.info("completed " + dest)

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

def processPath(src, dest, move=False):
    video_paths = findVideos(src)
    relocate = copyFile
    if(move):
        relocate = moveFile
    for vid in video_paths:
        output_path = createPlexPath(vid, dest)
        if output_path == "":
            logger.warning("could not process " + vid)
        else:
            logger.info("processing " + vid)
            relocate(vid, output_path)

def generateDefaultConfig():
    ensurePath(os.path.split(FormatterConfig.configPath)[-1])
    with open(FormatterConfig.configPath, mode="w") as conf:
        conf.write("# config for Plex Formatter daemon\n\n# source directories for unformatted files, separated by commas\nCOPYSRC=~/Downloads\nMOVESRC=\n\n# destination directory for formatted files\nDEST=~/Videos\n\nLOGLEVEL=info\n\n# any tags to be cut out of the file name\nTAGS=4k,2160,2160p,1080,1080p,720,720p,brrip,webrip,hdtv,amzn,x264,h264,hevc,h,264,265,h265,av1,bluray\n\n# acceptable file extensions\nEXTENSIONS=mp4,mkv,wmv,avi,mov,avchd,flv,f4v,swf")

def loadConfig():
    options = {}
    if not os.path.exists(FormatterConfig.configPath):
        generateDefaultConfig()
    with open(FormatterConfig.configPath) as config:
        while True:
            line = config.readline().lstrip('\t ')
            if len(line) == 0:
                break
            if line[0] == "\n" or line[0] == "#":
                continue

            splitLine = line.removesuffix("\n").split("=")
            if len(splitLine) >= 2:
                options[splitLine[0].lower()] = splitLine[1].split(",")
            if line[-1] != "\n":
                break
    return options

class FormatterConfig:
    def __init__(self):
        options = loadConfig()
        self.copysrc = options.get("copysrc")
        if self.copysrc:
            for src in self.copysrc:
                src = os.path.expanduser(src)
        else:
            self.copysrc = []
        self.movesrc = options.get("movesrc")
        if self.movesrc:
            for src in self.movesrc:
                src = os.path.expanduser(src)
        else:
            self.movesrc = []
        self.dest = options.get("dest")
        if self.dest:
            self.dest = os.path.expanduser(self.dest[0])
        match options.get("loglevel")[0]:
            case "debug":
                self.loglevel = logging.DEBUG
            case "info":
                self.loglevel = logging.INFO
            case _:
                self.loglevel = logging.WARNING

        self.tags = options.get("tags")
        self.extensions = options.get("extensions")
    configPath = os.path.expanduser(os.path.join("~", ".config", "plexFormatter", "plexFormatter.conf"))
    logPath = os.path.expanduser(os.path.join("~", ".log", "plexFormatter", "plexFormatter.log"))

def main(args):
    logger.debug(args)
    if (args.copy):
        processPath(args.copy[0], args.copy[1])
    if (args.move):
        processPath(args.move[0], args.move[1], move=True)
    if (args.daemon):
        match args.daemon:
            case "start":
                daemonLoop()
            case "stop":
                pass
            case "restart":
                pass
            case "config":
                os.system("nano " + config.configPath)

class CopyHandler(FileSystemEventHandler):
    def on_created(self, event):
        processPath(event.src_path, config.dest)
class MoveHandler(FileSystemEventHandler):
    def on_created(self, event):
        processPath(event.src_path, config.dest, move=True)

def daemonLoop():
    logger.debug("DaemonLoop started")
    # Create observer and event handlers
    observer = Observer()
    copy_handler = CopyHandler()
    move_handler = MoveHandler()

    all_paths_valid = False
    failed_count = 0
    while not all_paths_valid:
        all_paths_valid = True
        all_paths_valid = all_paths_valid and os.path.exists(config.dest)
        for path in config.copysrc:
            all_paths_valid = all_paths_valid and os.path.exists(path)
        for path in config.movesrc:
            all_paths_valid = all_paths_valid and os.path.exists(path)
        if not all_paths_valid:
            failed_count += 1
            if failed_count > 20:
                exit(1)
            logger.warning("could not find all source/destination paths. trying again in 10 seconds")
            sleep(10)

    # Set up observer to watch specified directories and do initial scan
    for path in config.copysrc:
        logger.info("Now observing " + path)
        observer.schedule(copy_handler, path)
        processPath(path, config.dest)
    for path in config.movesrc:
        logger.info("Now observing " + path)
        observer.schedule(move_handler, path)
        processPath(path, config.dest)
    observer.start()
    logger.debug("Daemon initialized")
    try:
        while True:
            sleep(10)
    except:
        observer.stop()
    logger.info("Daemon Stopped")
    observer.join()

config = FormatterConfig()
# set up the logger
ensurePath(os.path.split(config.logPath)[0])
logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=config.loglevel)
logger = logging.getLogger(__name__)
handler = RotatingFileHandler(config.logPath, maxBytes=1000000, backupCount=5)
handler.setFormatter(logging.Formatter(fmt="%(asctime)s %(levelname)s: %(message)s"))

logger.addHandler(handler)
logger.info("\nPlex Formatter initialized\n\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy video files from one directory to another and format them for use in Plex.")
    parser.add_argument("--move", "-m", nargs=2, metavar=("[source]", "[destination]"), help="Format and move files from source to destination. Source can be a file or directory")
    parser.add_argument("--copy", "-c", nargs=2, metavar=("[source]", "[destination]"), help="Format and copy files from source to destination. Source can be a file or directory")
    parser.add_argument("--daemon", "-d", choices=["start", "stop", "restart", "config"], help="Run as a daemon, using the configuration provided")
    args = parser.parse_args()
    main(args)
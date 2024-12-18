import os
import shutil
import logging
import logging.handlers
import time
import signal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Config Class
class FormatterConfig:
    def __init__(self):
        self.extensions = [
            'mkv', 'mp4', 'mov', 'avi', 'wmv', 'flv', 'webm',
            'vob', 'ogv', 'ogg', 'drc', 'mng', 'mts', 'm2ts',
            'ts', '3gp', 'm4v', 'mpg', 'mpeg', 'f4v', 'f4p',
            'f4a', 'f4b'
        ]
        self.extensions_to_delete = [
            'txt', 'exe', 'parts'
        ]
        self.tags = [
            'av1', 'x264', 'hdtv', 'bluray', 'bdrip', 'dvdrip', 'brrip',
            '4k', '2160', '2160p', '1080', '1080p', '720', '720p',
            'webrip', 'amzn', 'h264', 'hevc', 'h', '264' ,'265' ,'h265',
            'proper', 'remastered', 'theatrical', 'rarbg'
        ]
        self.watch_directory = '/path/to/watch'
        self.show_destination_directory = '/path/to/destination'
        self.movie_destination_directory = '/path/to/destination'
        self.misc_destination_directory = '/path/to/destination'
        self.non_video_destination_directory = '/path/to/destination'
        self.log_level = logging.INFO
        self.log_location = '/path/to/destination'

# FileFormatter Class
class FileFormatter:
    def __init__(self, config: FormatterConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def split_extension(self, filename: str) -> list[str]:
        extension = filename.split('.')[-1]
        if extension == filename:
            return [filename, '']
        extension = '.' + extension
        return [filename[:-(len(extension))],  extension]

    def is_video(self, filename: str) -> bool:
        extension = self.split_extension(filename)[1]
        if extension == '':
            return False
        return extension.removeprefix('.').lower() in self.config.extensions

    def is_deletable(self, filename: str) -> bool:
        extension = self.split_extension(filename)[1]
        return extension.removeprefix('.').lower() in self.config.extensions_to_delete

    def is_tag(self, word: str) -> bool:
        return word.lower() in self.config.tags
    
    def find_year(self, file_name: str) -> str:
        split_filename = file_name.split(' ')
        for word in split_filename[1:]:
            if len(word) == 4 and word.isdigit() and not self.is_tag(word):
                return word
        return None

    def find_episode_info(self, file_name: str) -> str:
        split_filename = file_name.split(' ')
        season = None
        episode = None
        for word in split_filename:
            if len(word) == 3:
                if word[0].lower() == 's' and word[1].isdigit() and word[2].isdigit():
                    season = word
                elif word[0].lower() == 'e' and word[1].isdigit() and word[2].isdigit():
                    episode = word
                if season and episode:
                    return [season, episode]
            elif len(word) == 6:
                if (word[0].lower() == 's' and word[1].isdigit() and word[2].isdigit() 
                    and word[3].lower() == 'e' and word[4].isdigit() and word[5].isdigit()):
                    return [word[:3], word[3:]]
        return None

    def change_symbols(self, word: str, char: chr ='') -> str:
        return ''.join([self.convert_symbol(character, char) for character in word])

    def convert_symbol(self, originalchar: chr, replacementchar: chr ='') -> chr:
        if originalchar.isalnum():
            return originalchar
        return replacementchar
    
    def format_filename(self, file_name: str) -> str:
        name_and_extension = self.split_extension(file_name)
        file_name_no_extension = name_and_extension[0].lower()
        file_extension = name_and_extension[1]
        
        name_parts = [part for part in self.change_symbols(file_name_no_extension, ' ').split(' ') if part != '']
        first_tag_index = 0
        for part in name_parts:
            if self.is_tag(part):
                name_parts = name_parts[:first_tag_index]
                break
            first_tag_index += 1
        
        formatted_name = ' '.join(name_parts)
        
        return formatted_name + file_extension
    
    def create_destination_path(self, file_name: str) -> str:
        if self.is_video(file_name):
            name_and_extension = self.split_extension(file_name)
            file_name_no_extension = name_and_extension[0]
            file_extension = name_and_extension[1]
            
            # dest/showname/Season xx/show name - sxx exx.ext
            episode_info = self.find_episode_info(file_name_no_extension)
            if episode_info:
                show_name = file_name_no_extension[:file_name_no_extension.find(episode_info[0])-1].title()
                return os.path.join(self.config.show_destination_directory,
                                    show_name,
                                    f'Season {episode_info[0][1:]}',
                                    show_name + f' - {episode_info[0]}{episode_info[1]}' + file_extension)
            
            # dest/moviename (year)/moviename (year).ext
            year = self.find_year(file_name_no_extension)
            if year:
                movie_name = file_name_no_extension[:file_name_no_extension.find(year)].title() + f'({year})'
                return os.path.join(self.config.movie_destination_directory,
                                    movie_name,
                                    movie_name + file_extension)
            
            return os.path.join(self.config.misc_destination_directory, file_name)
        return os.path.join(self.config.non_video_destination_directory, file_name)
  
# TrackedFile Class
class TrackedFile():
    def __init__(self):
        self.last_modification = time.time()
        self.file_name = ''
        self.src_path = ''
        self.dest_path = ''

# Daemon Class
class Daemon(FileSystemEventHandler):
    def __init__(self, config: FormatterConfig, file_formatter: FileFormatter, logger: logging.Logger):
        self.config = config
        self.file_formatter = file_formatter
        self.logger = logger
        self.observer = Observer()
        self.tracked_files = []
        self.delay_before_moving = 60

    def on_modified(self, event):
        if not event.is_directory:
            self.logger.debug(f"Modification detected: {event.src_path}")
            for file in self.tracked_files:
                if file.src_path == event.src_path:
                    file.last_modification = time.time()
                    break

    def on_created(self, event):
        if not event.is_directory:
            self.logger.info(f"New file detected: {event.src_path}")
            self.add_file(event.src_path)
    
    def add_file(self, file_path: str):
        file = TrackedFile()
        file.src_path = file_path
        file.file_name = self.file_formatter.format_filename(os.path.basename(file_path))
        file.dest_path = self.file_formatter.create_destination_path(file.file_name)
        self.tracked_files.append(file)
        
    def find_files(self, file_path: str):
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                self.logger.info(f"File found at {file_path}")
                self.add_file(file_path)
            elif os.path.isdir(file_path):
                for file in os.listdir(file_path):
                    self.find_files(os.path.join(file_path, file))
        else:
            self.logger.warning(f"{self.find_files.__name__}: {file_path} is not a valid path.")

    def is_empty_directory_tree(self, directory: str):
        if os.path.exists(directory) and os.path.isdir(directory):
            subfolders = []
            for file in os.listdir(directory):
                file = os.path.join(directory, file)
                if os.path.isdir(file):
                    subfolders.append(file)
                else:
                    return False
            result = True
            for folder in subfolders:
                result = result and self.is_empty_directory_tree(folder)
                if result == False: return result
            return result
        else:
            return False

    def find_empty_directories(self, directory):
        return [os.path.join(directory, dir) for dir in os.listdir(directory) if self.is_empty_directory_tree(os.path.join(directory, dir))]

    def clean_watch_folder(self):
        for dir in self.find_empty_directories(self.config.watch_directory):
            shutil.rmtree(dir)

    def check_tracked_files(self):
        current_time = time.time()
        to_remove = []
        for file in self.tracked_files:
            if current_time - file.last_modification > self.delay_before_moving:
                if self.file_formatter.is_deletable(file.src_path):
                    os.remove(file.src_path)
                    self.logger.info(f'deleted {file.src_path}')
                else:
                    self.move_file(file)
                to_remove.append(file)
        for file in to_remove:
            self.tracked_files.remove(file)
        
    def move_file(self, file: TrackedFile):
        if not os.path.exists(os.path.dirname(file.dest_path)):
            os.makedirs(os.path.dirname(file.dest_path))
        shutil.move(file.src_path, file.dest_path)
        self.logger.info(f"Moved {file.src_path} to {file.dest_path}")
        
    def signal_handler(self, signum, frame):
        signame = signal.Signals(signum).name
        self.logger.info(f'Signal handler called with signal {signame} ({signum})')
        self.stop()

    def start(self):
        failed_count = 0
        missing_paths = [path for path in [self.config.watch_directory, self.config.misc_destination_directory,
                                     self.config.movie_destination_directory, self.config.show_destination_directory,
                                     self.config.non_video_destination_directory, self.config.log_location]
                                    if not os.path.exists(path)]
        while len(missing_paths) > 0:
            self.logger.warn(f'cannot find paths: {missing_paths}')
            time.sleep(10)
            failed_count = failed_count + 1
            if failed_count > 10: exit(1)
        event_handler = self
        self.observer.schedule(event_handler, self.config.watch_directory, recursive=True)
        self.observer.start()
        self.logger.info("Daemon started. Watching directory for changes...")
        signal.signal(signal.SIGTERM, self.signal_handler)
        self.find_files(self.config.watch_directory)
        try:
            while self.observer.is_alive():
                time.sleep(1)
                self.check_tracked_files()
                self.clean_watch_folder()
        except KeyboardInterrupt:
            self.observer.stop()
            self.logger.info("Daemon stopped by user.")
        self.observer.join()
        
    def stop(self):
        self.observer.stop()
        self.observer.join()
        self.logger.info("Daemon stopped.")

# Logger Setup
def setup_logger(config: FormatterConfig) -> logging.Logger:
    logger = logging.getLogger('FileFormatterDaemon')
    logger.setLevel(config.log_level)
    log_file_handler = logging.handlers.RotatingFileHandler(os.path.join(config.log_location, 'file_formatter.log'), maxBytes=262144, backupCount=4)
    log_file_handler.setLevel(config.log_level)
    log_file_format = logging.Formatter('%(asctime)s - %(message)s')
    log_file_handler.setFormatter(log_file_format)
    logger.addHandler(log_file_handler)
    return logger

# Main Execution
def main():
    config = FormatterConfig()
    logger = setup_logger(config)
    file_formatter = FileFormatter(config, logger)
    daemon = Daemon(config, file_formatter, logger)
    daemon.start()

if __name__ == '__main__':
    main()
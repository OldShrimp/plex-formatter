import unittest
import logging
import os
import os.path
import shutil
import time
import watchdog
import plexFormatter

class FileFormatterTestCase(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.config = plexFormatter.FormatterConfig()
        self.config.tags.append('tag')
        self.config.misc_destination_directory = '/misc/'
        self.config.movie_destination_directory = '/movie/'
        self.config.show_destination_directory = '/show/'
        self.config.non_video_destination_directory = '/non_video/'
        self.formatter = plexFormatter.FileFormatter(self.config, self.logger)
        self.daemon = plexFormatter.Daemon(self.config, self.formatter, self.logger)

    def test_split_extension(self):
        self.assertEqual(self.formatter.split_extension('test.ext'), ['test', '.ext'], 'extension split incorrectly')
        self.assertEqual(self.formatter.split_extension('test'), ['test', ''], 'extension split incorrectly')
    
    def test_is_video(self):
        self.assertTrue(self.formatter.is_video('test.mp4'), 'Correct extension returned False')
        self.assertFalse(self.formatter.is_video('test.exe'), 'Incorrect extension returned True')
    
    def test_is_tag(self):
        self.assertTrue(self.formatter.is_tag('1080p'), 'Matching Word returned False')
        self.assertFalse(self.formatter.is_tag('test'), 'Non-matching word returned True')
    
    def test_find_year(self):
        self.assertEqual(self.formatter.find_year('test 1080p 1080 1995'), '1995', 'Failed to parse year')
    
    def test_find_episode_info(self):
        self.assertEqual(self.formatter.find_episode_info('test s01e99'), ['s01', 'e99'], 'Failed to parse episode info')
        self.assertEqual(self.formatter.find_episode_info('test s01 e99'), ['s01', 'e99'], 'Failed to parse episode info')
        self.assertEqual(self.formatter.find_episode_info('test s01'), None, 'Incorrectly returned something other than None')
    
    def test_remove_symbols(self):
        self.assertEqual(self.formatter.remove_symbols('    tes>t12+34.?'), 'test1234', 'Failed to remove symbols')
    
    def test_format_filename(self):
        self.assertEqual(self.formatter.format_filename('Alien.1979.PROPER.REMASTERED.THEATRICAL.1080p.BluRay.x265-RARBG.mp4'),
                        'alien 1979.mp4',
                        'Failed to format file name')
        self.assertEqual(self.formatter.format_filename('Stranger.Things.S01E01.1080p.BluRay.x265-RARBG.mp4'),
                        'stranger things s01e01.mp4',
                        'Failed to format file name')
    
    def test_create_destination_path(self):
        self.assertEqual(self.formatter.create_destination_path('Alien 1979.mp4'),
                        '/movie/Alien (1979)/Alien (1979).mp4',
                        'Failed to create destination path')
        self.assertEqual(self.formatter.create_destination_path('Stranger Things s01e01.mp4'),
                        '/show/Stranger Things/Season 01/Stranger Things - s01e01.mp4',
                        'Failed to create destination path')
        self.assertEqual(self.formatter.create_destination_path('test.mp4'),
                        '/misc/test.mp4',
                        'Failed to create destination path')
        
    def test_add_file(self):
        self.daemon.add_file('/Alien.1979.PROPER.REMASTERED.THEATRICAL.1080p.BluRay.x265-RARBG.mp4')
        correct_file = ['/Alien.1979.PROPER.REMASTERED.THEATRICAL.1080p.BluRay.x265-RARBG.mp4', 'alien 1979.mp4', '/movie/Alien (1979)/Alien (1979).mp4']
        self.assertListEqual(correct_file, [self.daemon.tracked_files[0].src_path, self.daemon.tracked_files[0].file_name, self.daemon.tracked_files[0].dest_path])

        self.daemon.add_file('/Alien.1979.PROPER.REMASTERED.THEATRICAL.1080p.BluRay.x265-RARBG.exe')
        correct_file = ['/Alien.1979.PROPER.REMASTERED.THEATRICAL.1080p.BluRay.x265-RARBG.exe', 'alien 1979.exe', '/non_video/alien 1979.exe']
        self.assertListEqual(correct_file, [self.daemon.tracked_files[1].src_path, self.daemon.tracked_files[1].file_name, self.daemon.tracked_files[1].dest_path])

        self.daemon.add_file('/Alien.PROPER.REMASTERED.THEATRICAL.1080p.BluRay.x265-RARBG.mp4')
        correct_file = ['/Alien.PROPER.REMASTERED.THEATRICAL.1080p.BluRay.x265-RARBG.mp4', 'alien.mp4', '/misc/alien.mp4']
        self.assertListEqual(correct_file, [self.daemon.tracked_files[2].src_path, self.daemon.tracked_files[2].file_name, self.daemon.tracked_files[2].dest_path])

class DaemonTestCase(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.config = plexFormatter.FormatterConfig()
        self.root_folder = os.path.abspath('./daemon_test/')
        self.config.misc_destination_directory = os.path.join(self.root_folder, 'misc/')
        self.config.movie_destination_directory = os.path.join(self.root_folder, 'movie/')
        self.config.show_destination_directory = os.path.join(self.root_folder, 'show/')
        self.config.non_video_destination_directory = os.path.join(self.root_folder, 'non_video/')
        self.config.watch_directory = os.path.join(self.root_folder, 'watch/')
        if not os.path.exists(self.root_folder):
            os.mkdir(self.root_folder)
        if not os.path.exists(self.config.watch_directory):
            os.mkdir(self.config.watch_directory)
        if not os.path.exists(self.config.misc_destination_directory):
            os.mkdir(self.config.misc_destination_directory)
        if not os.path.exists(self.config.movie_destination_directory):
            os.mkdir(self.config.movie_destination_directory)
        if not os.path.exists(self.config.show_destination_directory):
            os.mkdir(self.config.show_destination_directory)
        if not os.path.exists(self.config.non_video_destination_directory):
            os.mkdir(self.config.non_video_destination_directory)
        if not os.path.exists(os.path.join(self.config.watch_directory, 'empty')):
            os.mkdir(os.path.join(self.config.watch_directory, 'empty'))
        if not os.path.exists(os.path.join(self.config.watch_directory, 'empty', 'empty')):
            os.mkdir(os.path.join(self.config.watch_directory, 'empty', 'empty'))
        with open(os.path.join(self.config.watch_directory, 'Alien.1979.PROPER.REMASTERED.THEATRICAL.1080p.BluRay.x265-RARBG.mp4'), 'w+') as file:
            file.write('test')
        with open(os.path.join(self.config.watch_directory, 'Stranger.Things.S01E01.1080p.BluRay.x265-RARBG.mp4'), 'w+') as file:
            file.write('test')
        with open(os.path.join(self.config.watch_directory, 'test.mp4'), 'w+') as file:
            file.write('test')
        with open(os.path.join(self.config.watch_directory, 'test'), 'w+') as file:
            file.write('test')
        self.formatter = plexFormatter.FileFormatter(self.config, self.logger)
        self.daemon = plexFormatter.Daemon(self.config, self.formatter, self.logger)
        self.daemon.delay_before_moving = 0
    
    def tearDown(self):
        shutil.rmtree(os.path.abspath(self.root_folder))
    
    def test_find_files(self):
        self.daemon.find_files(self.config.watch_directory)
        found_files = {file.file_name for file in self.daemon.tracked_files}
        correct_files = {'alien 1979.mp4', 'stranger things s01e01.mp4', 'test.mp4', 'test'}
        self.assertSetEqual(found_files, correct_files, 'Failed to find files')
    
    def test_move_file(self):
        self.daemon.find_files(self.config.watch_directory)
        for file in self.daemon.tracked_files:
            self.daemon.move_file(file)
        time.sleep(0.01)
        dir_contents = [os.listdir(self.config.watch_directory),
                        os.listdir(self.config.misc_destination_directory),
                        os.listdir(os.path.join(self.config.movie_destination_directory, 'Alien (1979)')),
                        os.listdir(os.path.join(self.config.show_destination_directory, 'Stranger Things', 'Season 01')),
                        os.listdir(self.config.non_video_destination_directory)]
        correct_dir_contents = [['empty'], ['test.mp4'], ['Alien (1979).mp4'], ['Stranger Things - s01e01.mp4'], ['test']]
        self.assertListEqual(dir_contents, correct_dir_contents, 'failed to move all files correctly')
    
    def test_check_tracked_files(self):
        self.daemon.find_files(self.config.watch_directory)
        time.sleep(0.01)
        self.daemon.check_tracked_files()
        dir_contents = [os.listdir(self.config.watch_directory), os.listdir(self.config.misc_destination_directory),
                        os.listdir(os.path.join(self.config.movie_destination_directory, 'Alien (1979)')),
                        os.listdir(os.path.join(self.config.show_destination_directory, 'Stranger Things', 'Season 01')),
                        os.listdir(self.config.non_video_destination_directory)]
        correct_dir_contents = [['empty'], ['test.mp4'], ['Alien (1979).mp4'], ['Stranger Things - s01e01.mp4'], ['test']]
        self.assertListEqual(dir_contents, correct_dir_contents, 'not all tracked files were checked')
    
    def test_is_empty_directory_tree(self):
        self.assertTrue(self.daemon.is_empty_directory_tree(os.path.join(self.config.watch_directory, 'empty')))
        self.assertFalse(self.daemon.is_empty_directory_tree(self.config.watch_directory))
    
    def test_find_empty_directories(self):
        correct_directory = [os.path.join(self.config.watch_directory, 'empty')]
        self.assertListEqual(self.daemon.find_empty_directories(self.config.watch_directory), correct_directory, 'empty directory search failed')

    def test_clean_watch_folder(self):
        self.daemon.clean_watch_folder()
        correct_dir_contents = ['test',
                                'Alien.1979.PROPER.REMASTERED.THEATRICAL.1080p.BluRay.x265-RARBG.mp4',
                                'Stranger.Things.S01E01.1080p.BluRay.x265-RARBG.mp4',
                                'test.mp4']
        self.assertListEqual(os.listdir(self.config.watch_directory), correct_dir_contents, 'failed to clean watch folder')

class DaemonHandlersTestCase(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.config = plexFormatter.FormatterConfig()
        self.root_folder = os.path.abspath('./daemon_test/')
        self.config.misc_destination_directory = os.path.join(self.root_folder, 'misc/')
        self.config.movie_destination_directory = os.path.join(self.root_folder, 'movie/')
        self.config.show_destination_directory = os.path.join(self.root_folder, 'show/')
        self.config.watch_directory = os.path.join(self.root_folder, 'watch/')
        self.watch_nested_directory = os.path.join(self.config.watch_directory, 'watch2/')
        if not os.path.exists(os.path.abspath(self.root_folder)):
            os.mkdir(os.path.abspath(self.root_folder))
        if not os.path.exists(self.config.watch_directory):
            os.mkdir(self.config.watch_directory)
        if not os.path.exists(self.watch_nested_directory):
            os.mkdir(self.watch_nested_directory)
        if not os.path.exists(self.config.misc_destination_directory):
            os.mkdir(self.config.misc_destination_directory)
        if not os.path.exists(self.config.movie_destination_directory):
            os.mkdir(self.config.movie_destination_directory)
        if not os.path.exists(self.config.show_destination_directory):
            os.mkdir(self.config.show_destination_directory)
        with open(os.path.join(self.config.watch_directory, 'Alien.1979.PROPER.REMASTERED.THEATRICAL.1080p.BluRay.x265-RARBG.mp4'), 'w+') as file:
            file.write('test')
        with open(os.path.join(self.config.watch_directory, 'Stranger.Things.S01E01.1080p.BluRay.x265-RARBG.mp4'), 'w+') as file:
            file.write('test')
        with open(os.path.join(self.config.watch_directory, 'test.mp4'), 'w+') as file:
            file.write('test')
        with open(os.path.join(self.watch_nested_directory, 'test2.mp4'), 'w+') as file:
            file.write('test')
        self.formatter = plexFormatter.FileFormatter(self.config, self.logger)
        self.daemon = plexFormatter.Daemon(self.config, self.formatter, self.logger)
        self.daemon.delay_before_moving = 0
        self.daemon.observer.schedule(self.daemon, self.config.watch_directory, recursive=True)
        self.daemon.observer.start()
    
    def tearDown(self):
        self.daemon.stop()
        shutil.rmtree(self.root_folder)
    
    def test_on_modified(self):
        self.daemon.add_file(os.path.join(self.config.watch_directory, 'Alien.1979.PROPER.REMASTERED.THEATRICAL.1080p.BluRay.x265-RARBG.mp4'))
        self.daemon.add_file(os.path.join(self.watch_nested_directory, 'test2.mp4'))
        initial_time_0 = self.daemon.tracked_files[0].last_modification
        initial_time_1 = self.daemon.tracked_files[0].last_modification
        time.sleep(0.01)
        with open(self.daemon.tracked_files[0].src_path, 'w+') as file:
            file.write('testing testing')
        with open(self.daemon.tracked_files[1].src_path, 'w+') as file:
            file.write('testing testing')
        self.assertNotEqual(self.daemon.tracked_files[0].last_modification, initial_time_0, 'failed to detect modified file')
        self.assertNotEqual(self.daemon.tracked_files[1].last_modification, initial_time_1, 'failed to detect modified file recursively')
    
    def test_on_created(self):
        os.mkdir(os.path.join(self.config.watch_directory, 'test_deeper'))
        with open(self.config.watch_directory + 'test.mkv', 'w+') as file:
            file.write('testing testing')
        with open(self.config.watch_directory + 'test', 'w+') as file:
            file.write('testing testing')
        time.sleep(0.01)
        self.assertEqual(len(self.daemon.tracked_files), 2, 'failed to detect new file')

        with open(os.path.join(self.config.watch_directory, 'test_deeper') + 'test_deeper.mkv', 'w+') as file:
            file.write('testing testing')
        time.sleep(0.01)
        self.assertEqual(len(self.daemon.tracked_files), 3, 'failed to detect new file recursively')

    
    def test_signal_handler(self):
        pass
    
    def test_start(self):
        pass

if __name__ == '__main__':
    unittest.main()
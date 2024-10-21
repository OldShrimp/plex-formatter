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
        self.formatter = plexFormatter.FileFormatter(self.config, self.logger)
        self.daemon = plexFormatter.Daemon(self.config, self.formatter, self.logger)

    def test_split_extension(self):
        self.assertEqual(self.formatter.split_extension('test.ext'), ['test', '.ext'], 'extension split incorrectly')
        self.assertEqual(self.formatter.split_extension('test'), ['test', None], 'extension split incorrectly')
    
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
                        '/show/Stranger Things/Season 01/Stranger Things - s01e01 -.mp4',
                        'Failed to create destination path')
        self.assertEqual(self.formatter.create_destination_path('test.mp4'),
                        '/misc/test.mp4',
                        'Failed to create destination path')
        
    def test_add_video(self):
        self.daemon.add_video('/Alien.1979.PROPER.REMASTERED.THEATRICAL.1080p.BluRay.x265-RARBG.mp4')
        correct_video = ['/Alien.1979.PROPER.REMASTERED.THEATRICAL.1080p.BluRay.x265-RARBG.mp4', 'alien 1979.mp4', '/movie/Alien (1979)/Alien (1979).mp4']
        self.assertListEqual(correct_video, [self.daemon.videos[0].src_path, self.daemon.videos[0].file_name, self.daemon.videos[0].dest_path])

class DaemonTestCase(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.config = plexFormatter.FormatterConfig()
        self.root_folder = os.path.abspath('./daemon_test/')
        self.config.misc_destination_directory = os.path.join(self.root_folder, 'misc/')
        self.config.movie_destination_directory = os.path.join(self.root_folder, 'movie/')
        self.config.show_destination_directory = os.path.join(self.root_folder, 'show/')
        self.config.watch_directory = os.path.join(self.root_folder, 'watch/')
        if not os.path.exists(os.path.abspath(self.root_folder)):
            os.mkdir(os.path.abspath(self.root_folder))
        if not os.path.exists(self.config.watch_directory):
            os.mkdir(self.config.watch_directory)
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
        self.formatter = plexFormatter.FileFormatter(self.config, self.logger)
        self.daemon = plexFormatter.Daemon(self.config, self.formatter, self.logger)
        self.daemon.delay_before_moving = 0
    
    def tearDown(self):
        shutil.rmtree(os.path.abspath(self.root_folder))
    
    def test_find_videos(self):
        self.daemon.find_videos(self.config.watch_directory)
        found_videos = {video.file_name for video in self.daemon.videos}
        correct_videos = {'alien 1979.mp4', 'stranger things s01e01.mp4', 'test.mp4'}
        self.assertSetEqual(found_videos, correct_videos, 'Failed to find videos')
    
    def test_move_video_file(self):
        self.daemon.find_videos(self.config.watch_directory)
        for video in self.daemon.videos:
            self.daemon.move_video_file(video)
        dir_contents = [os.listdir(self.config.watch_directory), os.listdir(self.config.misc_destination_directory),
                        os.listdir(os.path.join(self.config.movie_destination_directory, 'Alien (1979)')),
                        os.listdir(os.path.join(self.config.show_destination_directory, 'Stranger Things', 'Season 01'))]
        correct_dir_contents = [[], ['test.mp4'], ['Alien (1979).mp4'], ['Stranger Things - s01e01 -.mp4']]
        self.assertListEqual(dir_contents, correct_dir_contents, 'failed to move all files correctly')
    
    def test_check_videos(self):
        self.daemon.find_videos(self.config.watch_directory)
        time.sleep(0.1)
        self.daemon.check_videos()
        dir_contents = [os.listdir(self.config.watch_directory), os.listdir(self.config.misc_destination_directory),
                        os.listdir(os.path.join(self.config.movie_destination_directory, 'Alien (1979)')),
                        os.listdir(os.path.join(self.config.show_destination_directory, 'Stranger Things', 'Season 01'))]
        correct_dir_contents = [[], ['test.mp4'], ['Alien (1979).mp4'], ['Stranger Things - s01e01 -.mp4']]
        self.assertListEqual(dir_contents, correct_dir_contents, 'not all videos were checked')

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
        self.daemon.add_video(os.path.join(self.config.watch_directory, 'Alien.1979.PROPER.REMASTERED.THEATRICAL.1080p.BluRay.x265-RARBG.mp4'))
        self.daemon.add_video(os.path.join(self.watch_nested_directory, 'test2.mp4'))
        initial_time_0 = self.daemon.videos[0].last_modification
        initial_time_1 = self.daemon.videos[0].last_modification
        time.sleep(0.1)
        with open(self.daemon.videos[0].src_path, 'w+') as file:
            file.write('testing testing')
        with open(self.daemon.videos[1].src_path, 'w+') as file:
            file.write('testing testing')
        self.assertNotEqual(self.daemon.videos[0].last_modification, initial_time_0, 'failed to detect modified file')
        self.assertNotEqual(self.daemon.videos[1].last_modification, initial_time_1, 'failed to detect modified file recursively')
    
    def test_on_created(self):
        os.mkdir(os.path.join(self.config.watch_directory, 'test_deeper'))
        with open(self.config.watch_directory + 'test.mkv', 'w+') as file:
            file.write('testing testing')
        with open(self.config.watch_directory + 'test', 'w+') as file:
            file.write('testing testing')
        time.sleep(0.1)
        self.assertEqual(len(self.daemon.videos), 1, 'failed to detect new file')

        with open(os.path.join(self.config.watch_directory, 'test_deeper') + 'test_deeper.mkv', 'w+') as file:
            file.write('testing testing')
        time.sleep(0.1)
        self.assertEqual(len(self.daemon.videos), 2, 'failed to detect new file recursively')

    
    def test_signal_handler(self):
        pass
    
    def test_start(self):
        pass

if __name__ == '__main__':
    unittest.main()
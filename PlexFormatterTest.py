import unittest
import logging
import plexFormatter

class FileFormatterTestCase(unittest.TestCase):

    def setup(self):
        self.logger = logging.getLogger(__name__)
        self.config = plexFormatter.FormatterConfig()
        self.config.tags.append('tag')
        self.formatter = plexFormatter.FileFormatter(self.config, self.logger)
    
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
        self.assertEqual(self.formatter.format_filename(''), '', 'Failed to format file name')
        self.assertEqual(self.formatter.format_filename(''), '', 'Failed to format file name')
    
    def test_create_destination_path(self):
        pass

class DaemonTestCase(unittest.TestCase):

    def setup(self):
        pass
    
    def teardown(self):
        pass
    
    def test_add_video(self):
        pass
    
    def test_find_videos(self):
        pass
    
    def test_move_video_file(self):
        pass
    
    def test_check_videos(self):
        pass
    

class DaemonHandlersTestCase(unittest.TestCase):

    def setup(self):
        pass
    
    def teardown(self):
        pass
    
    def test_on_modified(self):
        pass
    
    def test_on_created(self):
        pass
    
    def test_signal_handler(self):
        pass
    
    def test_start(self):
        pass
    
    def test_stop(self):
        pass



if __name__ == '__main__':
    unittest.main()

import functools
import math
import unittest
import unittest.mock

from soundcurses.curses import (regions, windows)

class ContentRegionTestCase(unittest.TestCase):
    def setUp(self):
        self._curses_mock = unittest.mock.NonCallableMock()
        self._window_mock = unittest.mock.NonCallableMock()
        self._window_mock.lines = 34
        self._window_mock.cols = 100

    @unittest.mock.patch('soundcurses.curses.windows.CursesString')
    def test_initialization(self, curses_string):
        curses_string_mock = unittest.mock.Mock()
        curses_string.return_value = curses_string_mock
        string_factory = windows.CursesStringFactory(self._curses_mock)
        content_region = regions.ContentRegion(
            self._window_mock, self._curses_mock, string_factory)

        self.assertEqual(len(content_region.page_numbers), 1)
        self.assertEqual(curses_string.call_count, 1)
        self.assertEqual(len(curses_string_mock.method_calls), 1)
        self.assertEqual(curses_string_mock.method_calls[0][0], 'write')

    @unittest.mock.patch('soundcurses.curses.windows.CursesString')
    def test_set_empty_content(self, curses_string):
        curses_string_mock = unittest.mock.Mock()
        curses_string.return_value = curses_string_mock
        string_factory = windows.CursesStringFactory(self._curses_mock)
        content_region = regions.ContentRegion(
            self._window_mock, self._curses_mock, string_factory)
        content_region.content_lines = []

        self.assertEqual(len(content_region.page_numbers), 1)
        self.assertEqual(curses_string.call_count, 2)
        self.assertEqual(len(curses_string_mock.method_calls), 2)
        for call in curses_string_mock.method_calls:
            self.assertEqual(call[0], 'write')

    @unittest.mock.patch('soundcurses.curses.windows.CursesString')
    def test_single_partial_page_content(self, curses_string):
        avail_strings = [unittest.mock.Mock()]
        curses_string.side_effect = avail_strings
        string_factory = windows.CursesStringFactory(self._curses_mock)
        content_region = regions.ContentRegion(
            self._window_mock, self._curses_mock, string_factory)

        # Initialize list with single Mock to account for initialization line.
        # I usually wouldn't use a private attribute but I feel an exception
        # here is inconsequential. If the content_region attempts to create
        # more than the allocated strings, a StopIteration exception is raised,
        # failing the test.
        lines_list = []
        for i in range(0, math.floor(content_region._avail_lines / 2)):
            avail_strings.append(unittest.mock.Mock())
            lines_list.append(str(i))

        content_region.content_lines = lines_list

        self.assertEqual(len(content_region.page_numbers), 1)
        self.assertEqual(curses_string.call_count, len(avail_strings))
        for curses_string_mock in avail_strings:
            self.assertEqual(len(curses_string_mock.method_calls), 1)
            self.assertEqual(curses_string_mock.method_calls[0][0], 'write')

    @unittest.mock.patch('soundcurses.curses.windows.CursesString')
    def test_single_full_page_content(self, curses_string):
        avail_strings = [unittest.mock.Mock()]
        curses_string.side_effect = avail_strings
        string_factory = windows.CursesStringFactory(self._curses_mock)
        content_region = regions.ContentRegion(
            self._window_mock, self._curses_mock, string_factory)

        # Initialize list with single Mock to account for initialization line.
        # I usually wouldn't use a private attribute but I feel an exception
        # here is inconsequential. If the content_region attempts to create
        # more than the allocated strings, a StopIteration exception is raised,
        # failing the test.
        lines_list = []
        for i in range(0, content_region._avail_lines):
            avail_strings.append(unittest.mock.Mock())
            lines_list.append(str(i))

        content_region.content_lines = lines_list

        self.assertEqual(len(content_region.page_numbers), 1)
        self.assertEqual(curses_string.call_count, len(avail_strings))
        for curses_string_mock in avail_strings:
            self.assertEqual(len(curses_string_mock.method_calls), 1)
            self.assertEqual(curses_string_mock.method_calls[0][0], 'write')

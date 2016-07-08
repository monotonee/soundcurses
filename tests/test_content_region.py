
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
        """
        Test creating the default empty lines set at construction.

        """
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
        """
        Test setting no lines (an empty line set).

        """
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
        """
        Test enough lines to partially fill only a single page.

        """
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
        """
        Test enough lines to fill only a single page.

        """
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

    @unittest.mock.patch('soundcurses.curses.windows.CursesString')
    def test_double_partial_page_content(self, curses_string):
        """
        Test enough lines to fill first page and part of second page.

        """
        avail_strings = [unittest.mock.Mock()]
        curses_string.side_effect = avail_strings
        string_factory = windows.CursesStringFactory(self._curses_mock)
        content_region = regions.ContentRegion(
            self._window_mock, self._curses_mock, string_factory)

        lines_count = math.floor(content_region._avail_lines * 1.5)
        lines_list = [str(i) for i in range(0, lines_count)]

        first_page = [unittest.mock.Mock() \
            for i in range(0, content_region._avail_lines)]
        second_page = [unittest.mock.Mock() \
            for i in range(0, content_region._avail_lines)]

        avail_strings.extend(first_page)
        avail_strings.extend(second_page)
        content_region.content_lines = lines_list

        self.assertEqual(len(content_region.page_numbers), 2)
        self.assertEqual(curses_string.call_count, len(avail_strings))
        for i in range(0, content_region._avail_lines):
            self.assertEqual(len(first_page[i].method_calls), 1)
            self.assertEqual(first_page[i].method_calls[0][0], 'write')
            self.assertEqual(len(second_page[i].method_calls), 0)

    @unittest.mock.patch('soundcurses.curses.windows.CursesString')
    def test_multiple_page_content(self, curses_string):
        """
        Test enough lines to fill more than two pages.

        """
        avail_strings = [unittest.mock.Mock()]
        curses_string.side_effect = avail_strings
        string_factory = windows.CursesStringFactory(self._curses_mock)
        content_region = regions.ContentRegion(
            self._window_mock, self._curses_mock, string_factory)

        page_count = 4
        lines_count = math.floor(
            content_region._avail_lines * (page_count - 0.5))
        lines_list = [str(i) for i in range(0, lines_count)]

        pages = []
        for page_number in range(0, page_count):
            pages.append(
                [unittest.mock.Mock() \
                    for i in range(0, content_region._avail_lines)])
            avail_strings.extend(pages[page_number])

        content_region.content_lines = lines_list

        self.assertEqual(len(content_region.page_numbers), page_count)
        self.assertEqual(curses_string.call_count, len(avail_strings))
        for i in range(0, content_region._avail_lines):
            self.assertEqual(len(pages[0][i].method_calls), 1)
            self.assertEqual(pages[0][i].method_calls[0][0], 'write')
            for page_number in range(1, page_count):
                self.assertEqual(len(pages[page_number][i].method_calls), 0)

    @unittest.mock.patch('soundcurses.curses.windows.CursesString')
    def test_highlighting_next_line(self, curses_string):
        """
        Test highlighting the line after current.

        """
        pass

    @unittest.mock.patch('soundcurses.curses.windows.CursesString')
    def test_highlighting_previous_line(self, curses_string):
        """
        Test highlighting the line before current.

        """
        pass

    @unittest.mock.patch('soundcurses.curses.windows.CursesString')
    def test_page_down(self, curses_string):
        """
        Test loading next page of content.

        """
        pass

    @unittest.mock.patch('soundcurses.curses.windows.CursesString')
    def test_page_up(self, curses_string):
        """
        Test loading next page of content.

        """
        pass


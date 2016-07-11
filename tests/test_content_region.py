
import functools
import math
import unittest
import unittest.mock

from soundcurses.curses import (regions, windows)

class ContentRegionTestCase(unittest.TestCase):
    def setUp(self):
        self._curses_mock = unittest.mock.NonCallableMock()
        self._string_factory = windows.CursesStringFactory(self._curses_mock)
        self._window_mock = unittest.mock.NonCallableMock()
        self._window_mock.lines = 34
        self._window_mock.cols = 100

    @staticmethod
    def _use_string_pool(string_pool, window, string, y, x, attr=None):
        """
        Return CursesString from an iterator.

        Designed to be used with functtools.partial to bind string_pool from a
        local scope.

        Args:
            string_pool (iter): An iterator of CursesString objects.

        Returns:
            soundcurses.curses.windows.CursesString

        """
        string_object = next(string_pool)
        string_object.move(y, x)
        string_object.attr = attr
        return string_object

    def test_initialization(self):
        """
        Test creating the default empty lines set at construction.

        """
        string_pool = [
            self._string_factory.create_string(
                self._window_mock, '', 0, 0)]
        string_factory_mock = unittest.mock.NonCallableMock(
            spec=windows.CursesStringFactory)
        string_factory_mock.create_string.side_effect = functools.partial(
            self._use_string_pool, iter(string_pool))
        content_region = regions.ContentRegion(
            self._window_mock, self._curses_mock, string_factory_mock)

        self.assertEqual(content_region.page_count, 1)
        self.assertEqual(string_factory_mock.create_string.call_count, 1)
        self.assertTrue(string_pool[0].is_written)

    def test_set_empty_content(self):
        """
        Test setting no lines (an empty line set).

        """
        string_pool = [
            self._string_factory.create_string(
                self._window_mock, '', 0, 0),
            self._string_factory.create_string(
                self._window_mock, '', 0, 0)]
        string_factory_mock = unittest.mock.NonCallableMock(
            spec=windows.CursesStringFactory)
        string_factory_mock.create_string.side_effect = functools.partial(
            self._use_string_pool, iter(string_pool))
        content_region = regions.ContentRegion(
            self._window_mock, self._curses_mock, string_factory_mock)

        content_region.content_lines = []

        self.assertEqual(content_region.page_count, 1)
        self.assertEqual(string_factory_mock.create_string.call_count, 2)
        self.assertFalse(string_pool[0].is_written)
        self.assertTrue(string_pool[1].is_written)

    def test_single_partial_page_content(self):
        """
        Test enough lines to partially fill only a single page.

        """
        string_pool = [
            self._string_factory.create_string(
                self._window_mock, '', 0, 0)]
        string_factory_mock = unittest.mock.NonCallableMock(
            spec=windows.CursesStringFactory)
        string_factory_mock.create_string.side_effect = functools.partial(
            self._use_string_pool, iter(string_pool))
        content_region = regions.ContentRegion(
            self._window_mock, self._curses_mock, string_factory_mock)

        lines_list = []
        for i in range(0, math.floor(content_region._avail_lines / 2)):
            string_pool.append(
                self._string_factory.create_string(
                    self._window_mock, '', 0, 0))
            lines_list.append(str(i))
        content_region.content_lines = lines_list

        self.assertEqual(content_region.page_count, 1)
        self.assertEqual(
            string_factory_mock.create_string.call_count, len(string_pool))
        self.assertFalse(string_pool[0].is_written)
        for i in range(1, len(string_pool)):
            self.assertTrue(string_pool[i].is_written)

    def test_single_full_page_content(self):
        """
        Test enough lines to fill only a single page.

        """
        string_pool = [
            self._string_factory.create_string(
                self._window_mock, '', 0, 0)]
        string_factory_mock = unittest.mock.NonCallableMock(
            spec=windows.CursesStringFactory)
        string_factory_mock.create_string.side_effect = functools.partial(
            self._use_string_pool, iter(string_pool))
        content_region = regions.ContentRegion(
            self._window_mock, self._curses_mock, string_factory_mock)

        lines_list = []
        for i in range(0, content_region._avail_lines):
            string_pool.append(
                self._string_factory.create_string(
                    self._window_mock, '', 0, 0))
            lines_list.append(str(i))
        content_region.content_lines = lines_list

        self.assertEqual(content_region.page_count, 1)
        self.assertEqual(
            string_factory_mock.create_string.call_count, len(string_pool))
        self.assertFalse(string_pool[0].is_written)
        for i in range(1, len(string_pool)):
            self.assertTrue(string_pool[i].is_written)

    def test_double_partial_page_content(self):
        """
        Test enough lines to fill first page and part of second page.

        """
        string_pool = [
            self._string_factory.create_string(
                self._window_mock, '', 0, 0)]
        string_factory_mock = unittest.mock.NonCallableMock(
            spec=windows.CursesStringFactory)
        string_factory_mock.create_string.side_effect = functools.partial(
            self._use_string_pool, iter(string_pool))
        content_region = regions.ContentRegion(
            self._window_mock, self._curses_mock, string_factory_mock)

        page_count = 2
        lines_count = math.floor(
            content_region._avail_lines * (page_count - 0.5))
        lines_list = [str(i) for i in range(0, lines_count)]

        pages = []
        for page_number in range(0, page_count):
            pages.append(
                [self._string_factory.create_string(
                    self._window_mock, '', 0, 0) \
                    for i in range(0, content_region._avail_lines)])
            string_pool.extend(pages[page_number])

        content_region.content_lines = lines_list

        self.assertEqual(content_region.page_count, page_count)
        self.assertEqual(
            string_factory_mock.create_string.call_count, len(string_pool))
        self.assertFalse(string_pool[0].is_written)
        for i in range(0, content_region._avail_lines):
            self.assertTrue(pages[0][i].is_written)
            for page_number in range(1, page_count):
                self.assertFalse(pages[page_number][i].is_written)

    def test_multiple_page_content(self):
        """
        Test enough lines to fill more than two pages.

        """
        string_pool = [
            self._string_factory.create_string(
                self._window_mock, '', 0, 0)]
        string_factory_mock = unittest.mock.NonCallableMock(
            spec=windows.CursesStringFactory)
        string_factory_mock.create_string.side_effect = functools.partial(
            self._use_string_pool, iter(string_pool))
        content_region = regions.ContentRegion(
            self._window_mock, self._curses_mock, string_factory_mock)

        page_count = 4
        lines_count = math.floor(
            content_region._avail_lines * (page_count - 0.5))
        lines_list = [str(i) for i in range(0, lines_count)]

        pages = []
        for page_number in range(0, page_count):
            pages.append(
                [self._string_factory.create_string(
                    self._window_mock, '', 0, 0) \
                    for i in range(0, content_region._avail_lines)])
            string_pool.extend(pages[page_number])

        content_region.content_lines = lines_list

        self.assertEqual(content_region.page_count, page_count)
        self.assertEqual(
            string_factory_mock.create_string.call_count, len(string_pool))
        self.assertFalse(string_pool[0].is_written)
        for i in range(0, content_region._avail_lines):
            self.assertTrue(pages[0][i].is_written)
            for page_number in range(1, page_count):
                self.assertFalse(pages[page_number][i].is_written)

    # def test_highlighting_next_line(self):
        # """
        # Test highlighting the line after current.

        # """
        # pass

    # def test_highlighting_previous_line(self):
        # """
        # Test highlighting the line before current.

        # """
        # pass

    def test_paging(self):
        """
        Test loading next page of content.

        """
        string_pool = [
            self._string_factory.create_string(
                self._window_mock, '', 0, 0)]
        string_factory_mock = unittest.mock.NonCallableMock(
            spec=windows.CursesStringFactory)
        string_factory_mock.create_string.side_effect = functools.partial(
            self._use_string_pool, iter(string_pool))
        content_region = regions.ContentRegion(
            self._window_mock, self._curses_mock, string_factory_mock)

        page_count = 2
        lines_count = math.floor(
            content_region._avail_lines * (page_count - 0.5))
        lines_list = [str(i) for i in range(0, lines_count)]

        pages = []
        for page_number in range(0, page_count):
            pages.append(
                [self._string_factory.create_string(
                    self._window_mock, '', 0, 0) \
                    for i in range(0, content_region._avail_lines)])
            string_pool.extend(pages[page_number])

        content_region.content_lines = lines_list

        self.assertEqual(content_region.page_count, page_count)
        self.assertFalse(string_pool[0].is_written)
        for line in pages[0]:
            self.assertTrue(line.is_written)
        for line in pages[1]:
            self.assertFalse(line.is_written)
        content_region.page_next()
        for line in pages[0]:
            self.assertFalse(line.is_written)
        for line in pages[1]:
            self.assertTrue(line.is_written)
        content_region.page_previous()
        for line in pages[0]:
            self.assertTrue(line.is_written)
        for line in pages[1]:
            self.assertFalse(line.is_written)

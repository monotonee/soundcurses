"""
A module in which tests for the WindowRenderQueue are defined.

"""

import unittest
import unittest.mock

from soundcurses.curses import (screen, windows)

class RenderQueueTestCase(unittest.TestCase):
    def setUp(self):
        self._window_bottom = unittest.mock.NonCallableMock(
            spec=windows.CursesWindow)
        self._window_bottom.render_layer = 1

        self._window_middle = unittest.mock.NonCallableMock(
            spec=windows.CursesWindow)
        self._window_middle.render_layer = 2

        self._window_top = unittest.mock.NonCallableMock(
            spec=windows.CursesWindow)
        self._window_top.render_layer = 3

    def test_add_window(self):
        render_queue = screen.RenderQueue()
        render_queue.add(self._window_bottom)
        self.assertEqual(len(render_queue), 1)

    def test_clear(self):
        render_queue = screen.RenderQueue()
        render_queue.add(self._window_bottom)
        self.assertEqual(len(render_queue), 1)
        render_queue.clear()
        self.assertEqual(len(render_queue), 0)

    def test_contains(self):
        render_queue = screen.RenderQueue()
        render_queue.add(self._window_bottom)
        self.assertIn(self._window_bottom, render_queue)

    def test_duplicates(self):
        render_queue = screen.RenderQueue()
        render_queue.add(self._window_bottom)
        render_queue.add(self._window_top)
        render_queue.add(self._window_middle)
        render_queue.add(self._window_middle)
        self.assertEqual(len(render_queue), 3)
        self.assertCountEqual(
            list(render_queue),
            [self._window_bottom, self._window_middle, self._window_top])

    def test_iter(self):
        render_queue = screen.RenderQueue()
        render_queue.add(self._window_bottom)
        self.assertListEqual(
            list(render_queue),
            [self._window_bottom])

    def test_len(self):
        render_queue = screen.RenderQueue()
        self.assertEqual(len(render_queue), 0)

    def test_order(self):
        render_queue = screen.RenderQueue()
        render_queue.add(self._window_bottom)
        render_queue.add(self._window_top)
        render_queue.add(self._window_middle)
        self.assertSequenceEqual(
            list(render_queue),
            [self._window_bottom, self._window_middle, self._window_top])

    def test_remove(self):
        render_queue = screen.RenderQueue()
        render_queue.add(self._window_bottom)
        render_queue.add(self._window_middle)
        self.assertEqual(len(render_queue), 2)
        render_queue.remove(self._window_bottom)
        self.assertEqual(len(render_queue), 1)
        self.assertIs(list(render_queue)[0], self._window_middle)


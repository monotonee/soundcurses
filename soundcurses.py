""" Main entry point

"""

# Standard library imports.
import curses
import locale
import sys
import time

# Local imports.
import soundcurses.controller
import soundcurses.view

def main(stdscr):
    # Compose curses windows and pads.
    stdscr_window = soundcurses.view.StdscrWindow(curses, stdscr)
    header_window = soundcurses.view.HeaderWindow(
        curses,
        curses.newwin(1, curses.COLS, 0, 0))
    nav_window = soundcurses.view.NavWindow(
        curses,
        curses.newwin(3, curses.COLS, 1, 0))
    content_window = soundcurses.view.ContentWindow(
        curses,
        curses.newwin(curses.LINES - 4, curses.COLS, 4, 0))

    # Compose view.
    view = soundcurses.view.CursesView(
        curses,
        locale,
        stdscr_window,
        header_window,
        nav_window,
        content_window)

    controller = soundcurses.controller.CursesController(stdscr_window, view)

    # time.sleep(2)



curses.wrapper(main)

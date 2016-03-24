""" Main entry point

"""

# Standard library imports.
import curses
import locale
import sys
import time

# Local imports.
import soundcurses.views.curses

def main(stdscr):
    # Compose curses windows and pads.
    srdscr_window = soundcurses.views.curses.StdscrWindow(curses, stdscr)
    header_window = soundcurses.views.curses.HeaderWindow(
        curses,
        curses.newwin(1, curses.COLS, 0, 0))
    nav_window = soundcurses.views.curses.NavWindow(
        curses,
        curses.newwin(3, curses.COLS, 1, 0))
    content_window = soundcurses.views.curses.ContentWindow(
        curses,
        curses.newwin(curses.LINES - 4, curses.COLS, 4, 0))

    # Compose view.
    view = soundcurses.views.curses.CursesView(
        curses,
        locale,
        srdscr_window,
        header_window,
        nav_window,
        content_window)
    time.sleep(2)

    key = 0
    stdscr.nodelay(1)
    while key != 'q':
        try:
            key = stdscr.getkey()
        except Exception:
            pass

curses.wrapper(main)

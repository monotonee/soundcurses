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
    view = soundcurses.views.curses.CursesView(curses, stdscr, locale)
    time.sleep(2)

curses.wrapper(main)

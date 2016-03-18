""" Main entry point

"""

# Standard library imports.
import curses
import locale
import sys
import time

# Local imports.
from soundcurses.views import CursesView



def main(stdscr):

    # Temporary try/catch during testing
    # This is bad form.
    view = CursesView(curses, stdscr, locale)

curses.wrapper(main)

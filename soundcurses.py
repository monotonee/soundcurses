""" Main entry point

"""

# Standard library imports.
import curses
import locale
import sys
import time

# Third-party imports.
import soundcloud

# Local imports.
import soundcurses.controller
import soundcurses.model
import soundcurses.view

def main(stdscr):
    """ Compose curses windows and pads.

    """

    # Instantiate main window (stdscr) and subwindows.
    # The order of curses window refresh is important. To avoid the standard
    # (main) screen overwriting subwindows, initialize it first.
    stdscr_window = soundcurses.view.StdscrWindow(curses, stdscr)
    header_window = soundcurses.view.HeaderWindow(
        curses,
        curses.newwin(3, curses.COLS, 0, 0))
    nav_window = soundcurses.view.NavWindow(
        curses,
        curses.newwin(3, curses.COLS, 3, 0))
    content_window = soundcurses.view.ContentWindow(
        curses,
        curses.newwin(curses.LINES - 6, curses.COLS, 6, 0))

    # Compose view.
    view = soundcurses.view.CursesView(
        curses,
        locale,
        stdscr_window,
        header_window,
        nav_window,
        content_window)

    # Compose controller.
    controller = soundcurses.controller.CursesController(
        stdscr_window,
        view)

    # Compose model.
    soundcloud_client = soundcloud.Client(
        client_id='e9cd65934510bf631372af005c2f37b5',
        use_ssl=True)
    print(
        soundcloud_client.get(
            '/resolve', url='https://soundcloud.com/monotonee'))

    model = soundcurses.model.CursesModel(soundcloud_client)

curses.wrapper(main)

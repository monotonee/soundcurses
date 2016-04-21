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

    Note that stdscr is passed into the main function by curses.wrapper().

    """

    # Instantiate main window (stdscr) and subwindows.
    # The order of curses window refresh is important. To avoid the standard
    # (main) screen overwriting subwindows, initialize it first.
    window_stdscr = soundcurses.view.StdscrWindow(curses, stdscr)
    window_header = soundcurses.view.HeaderWindow(
        curses,
        curses.newwin(3, curses.COLS, 0, 0))
    window_nav = soundcurses.view.NavWindow(
        curses,
        curses.newwin(3, curses.COLS, 3, 0))
    window_content = soundcurses.view.ContentWindow(
        curses,
        curses.newwin(curses.LINES - 6, curses.COLS, 6, 0))
    curses_screen = soundcurses.view.CursesScreen(
        curses,
        window_stdscr,
        window_header,
        window_nav,
        window_content
    )

    # Compose view.
    view = soundcurses.view.CursesView(
        curses,
        locale,
        curses_screen)

    # Compose controller.
    controller = soundcurses.controller.MainController(view)
    controller.start_application()

    # Compose model.
    # soundcloud_client = soundcloud.Client(
        # client_id='e9cd65934510bf631372af005c2f37b5',
        # use_ssl=True)
    # print(
        # soundcloud_client.get(
            # '/resolve', url='https://soundcloud.com/monotonee'))

    # model = soundcurses.model.CursesModel(soundcloud_client)

curses.wrapper(main)

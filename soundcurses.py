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
    curses_wrapper = soundcurses.view.CursesWrapper(curses, locale)
    window_stdscr = soundcurses.view.StdscrWindow(curses_wrapper, stdscr)
    window_header = soundcurses.view.HeaderWindow(
        curses_wrapper,
        curses_wrapper.newwin(3, curses_wrapper.COLS, 0, 0))
    window_nav = soundcurses.view.NavWindow(
        curses_wrapper,
        curses_wrapper.newwin(3, curses_wrapper.COLS, 3, 0))
    window_content = soundcurses.view.ContentWindow(
        curses_wrapper,
        curses_wrapper.newwin(
            curses_wrapper.LINES - 6,
            curses_wrapper.COLS, 6, 0))
    curses_screen = soundcurses.view.CursesScreen(
        curses_wrapper,
        window_stdscr,
        window_header,
        window_nav,
        window_content)

    # Compose view.
    view = soundcurses.view.CursesView(
        curses_wrapper,
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

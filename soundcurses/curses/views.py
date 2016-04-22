""" This module defines view classes that are designed to expose coarse
interfaces to controller classes for the manipulation of the curses TUI.


"""

from collections import deque

class MainView:
    """ Highest-level view designed to control broad functions often associated
    with curses' stdscr. Manipulated by the main controller class.

    """

    def __init__(self, input_source, screen):
        """ Constructor.

        input_source - Provides an interface for receiving input events from
            the curses library.
        screen - An abstracted interface for the display of the various curses
            components in a "composited" TUI view.

        """
        # Declare instance attributes.
        self._input_source = input_source
        self._screen = screen

    def start(self):
        """ Render virtual curses state to physical screen.

        """
        self._screen.render()

    def start_input_polling(self):
        """ Starts polling for input from curses windows.

        """
        self._input_source.start()

    def stop_input_polling(self):
        self._input_source.stop()

    def stop(self):
        """ Relinquish control of the screen. Also returns window settings
        not set by curses.wrapper() to original values.

        """
        self._screen.destroy()


class HeaderRegionView:
    """ Class designed to expose an interface to the controllers for
    manipulating the content and appearance of the header region. Rendering
    is not managed by this class but instead through the main view via the
    curses screen abstraction class.

    """

    def __init__(self, window_header):
        self._state_current_sound = None
        self._state_current_user = None
        self._window_header = window_header

    @property
    def current_sound(self):
        return self._state_current_sound

    @current_sound.setter
    def current_sound(self, new_current_sound):
        self._state_current_sound = new_current_sound

    @property
    def current_user(self):
        return self._state_current_user

    @current_user.setter
    def current_user(self, new_current_user):
        self._state_current_user = new_current_user


class NavRegionView:
    """ Class designed to expose an interface to the controllers for
    manipulating the content and appearance of the navigation region. Rendering
    is not managed by this class but instead through the main view via the
    curses screen abstraction class.

    """

    def __init__(self, window_nav):
        self._state_nav_menu_items = []
        self._window_nav = window_nav

    @property
    def nav_menu_items(self):
        return self._state_nav_menu_items

    @nav_menu_items.setter
    def nav_menu_items(self, new_nav_menu_items):
        self._state_nav_menu_items = new_nav_menu_items


class ContentRegionView:
    """ Class designed to expose an interface to the controllers for
    manipulating the content and appearance of the content region. Rendering
    is not managed by this class but instead through the main view via the
    curses screen abstraction class.

    """

    def __init__(self, window_content):
        self._state_sound_list = []
        self._window_content = window_content

    @property
    def sound_list(self):
        return self._state_sound_list

    @sound_list.setter
    def sound_list(self, new_sound_list):
        self._state_sound_list = new_sound_list

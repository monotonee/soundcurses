""" Defines classes that act as application or GUI component controllers.

"""

import abc

class MainController:
    """ Top-evel interface for application controller actions.

    Implements a basic state pattern to provide state switching for TUI region
    focus. For instance, arrow key presses when the nav region has focus will
    highlight nav options while arrow keys will scroll track list when content
    region is in focus.

    """

    def __init__(self, main_view, controller_nav, controller_content):
        """ Constructor.

        """

        self._controller_nav = controller_nav
        self._controller_content = controller_content
        self._main_view = main_view
        self._state_region_context = self._controller_nav

    def handle_input_keypress(self, code_point, **kwargs):
        """ Slot that handles keypress events from the view.

        code_point - The integer code point representing the keyboard key.

        """
        if code_point == ord('q'):
            self._main_view.stop_input_polling()

    def start_application(self):
        self._main_view.start()
        self._main_view.start_input_polling()
        self._main_view.stop()


class RegionController(metaclass=abc.ABCMeta):
    """ An abstract base class for a specialized "subcontroller" that is
    designed to manipulate an individual region or "window" of the TUI.

    """

    def __init__(self, region_view):
        self._region_view = region_view

    @abc.abstractmethod
    def handle_input_keypress(self, code_point):
        """ Accept an integer code point from a keypress and take action.

        """
        pass


class NavRegionController(RegionController):
    """ Designed for specialized control of the navigation region of the TUI.

    """

    def handle_input_keypress(self, code_point):
        pass


class ContentRegionController(RegionController):
    """ Designed for specialized control of the content region of the TUI.

    """

    def handle_input_keypress(self, code_point):
        pass



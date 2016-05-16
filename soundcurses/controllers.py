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

    def __init__(self, view, model, controller_nav, controller_content):
        """ Constructor.

        """

        self._application_is_running = False
        self._controller_content = controller_content
        self._controller_nav = controller_nav
        self._model = model
        self._region_context = self._controller_nav
        self._view = view

    def _run_main_loop(self):
        while self._application_is_running:
            input_string = self._view.sample_input()
            self._handle_input(input_string)
            self._view.render()

    def _handle_input(self, input_string):
        """
        Begin necessary tasks in reaction to user input.
        """
        if input_string == 'q':
            self.stop_application()
        elif input_string == 'u':
            username = self._view.prompt_username()
            self._view.display_spinner()
            # user = self._model.resolve_username(username)

    def start_application(self):
        """
        Start the application.
        """
        self._application_is_running = True
        self._view.start()
        self._run_main_loop()
        self._view.stop()

    def stop_application(self):
        """
        Stop the application. Public but likely called internally.
        """
        self._application_is_running = False


class RegionController(metaclass=abc.ABCMeta):
    """ An abstract base class for a specialized "subcontroller" that is
    designed to manipulate an individual region or "window" of the TUI.

    """

    def __init__(self, view):
        self._view = view

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



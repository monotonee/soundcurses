""" Defines classes that act as application or GUI component controllers.

"""

class MainController:
    """ Top-evel interface for application controller actions.

    Implements a basic state pattern to provide state switching for TUI region
    focus. For instance, arrow key presses when the nav region has focus will
    highlight nav options while arrow keys will scroll track list when content
    region is in focus.

    """

    def __init__(self, main_view):
        """ Constructor.

        """

        self._main_view = main_view

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


# class NavController
    # """ Handles logic behind nav window.

    # """

    # def __init__(self, nav_view):
        # """

        # """
        # self._nav_view = nav_view

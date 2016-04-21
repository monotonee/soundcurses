""" Defines classes that act as application or GUI component controllers.

"""

class MainController:
    """ Top-evel interface for application controller actions.

    Implements a basic state pattern to provide state switching for TUI region
    focus. For instance, arrow key presses when the nav region has focus will
    highlight nav options while arrow keys will scroll track list when content
    region is in focus.

    """

    def __init__(self, view):
        """ Constructor.

        """

        self._view = view

    def _poll_input(self):
        """ Starts the view's input polling loop, essentially starting the app.

        """
        self._view.render()
        self._view.poll_input()
        self._view.destroy()

    def start_application(self):
        self._poll_input()


# class NavController
    # """ Handles logic behind nav window.

    # """

    # def __init__(self, nav_view):
        # """

        # """
        # self._nav_view = nav_view

""" Defines classes that act as application or GUI component controllers.

"""

import abc
import math
import time

class MainController:
    """
    Top-evel interface for application controller actions.

    Implements a basic state pattern context to provide dynamic behavior change.
    """
    def __init__(self, view, input_resolver, model):
        """
        Constructor.
        """
        self._application_is_running = False
        self._current_state = None
        self._input_resolver = input_resolver
        self._model = model
        self._view = view
        self._view_render_interval = 0.5

    def _run_main_loop(self):
        while self._application_is_running:
            input_string = self._view.sample_input()
            action = self._input_resolver.resolve_input(input_string)
            self._handle_input(input_string)
            self._render_view()

    def _render_view(self):
        timestamp_new = math.trunc(time.time())
        timestmap_last_render = math.trunc(self._view.last_render_timestamp)
        if timestamp_new - timestmap_last_render >= self._view_render_interval:
            self._view.render()

    def _handle_input(self, input_string):
        """
        Begin necessary tasks in reaction to user input.
        """
        if input_string == 'q':
            self.stop_application()
        elif input_string == 'u':
            username = self._view.prompt_username()
            self._view.show_loading_animation()
            # user = self._model.resolve_username(username)

    def start_application(self):
        """
        Start the application.
        """
        self._application_is_running = True
        self._view.render()
        self._run_main_loop()

    def stop_application(self):
        """
        Stop the application. Public but likely called internally.
        """
        self._application_is_running = False
        self._view.destroy()


class StateFactory:
    """
    Factory to hide creation details of state objects.
    """
    def __init__(self, view, model):
        self._view = view
        self._model = model


class BaseState(metaclass=abc.ABCMeta):
    """
    Provides specialized functionality to the main controller class.

    Designed so that a main controller can respond to application events by
    changing or augmenting its internal state, changing the application's
    behavior dynamically.
    """
    def __init__(self, view, model):
        """
        Constructor.
        """
        self._view = view
        self._model = model

    @abc.abstractmethod
    def enable(self):
        """
        Perform main tasks.

        The subcontroller's main tasks. Designed to be called in response to
        application events such as user input events.
        """
        pass

    @abc.abstractmethod
    def run_interval_tasks(self):
        """
        Run tasks that are required to be run on regular interval.

        As long as the subcontroller remains active, this method will be called
        once per main loop cycle. Do not depend on any specific execution
        interval.
        """
        pass

    @abc.abstractmethod
    def disable(self):
        """
        Run tasks before subcontroller is removed from use in main controller.
        """
        pass


class MainSubcontroller(BaseState):
    """
    Enabled at application start, handles state changes.
    """
    def __init__(self):
        pass


class InputActionResolver:
    """
    Responsible for resolving raw user input to application actions.

    Contains a series of constants that can be used by the application instead
    of raw character strings or code points, allowing for more flexible key
    mapping in the future. While currently very rudimentary, collecting this
    functionality in a class will make user-configurable mapping much easier to
    implement.

    Currently key mapping is constrained to one-to-one relationships.
    """
    ACTION_ENTER_USER = 0
    ACTION_QUIT = 1

    def __init__(self):
        """
        Establish instance input-to-action mapping.
        """
        self._keymap = {}

        self._populate_keymap()

    def _populate_keymap(self):
        """
        Determine key mappings and populate the keymap dictionary.

        Listed in ascending alphanumerical order by key.
        """
        self._keymap['q'] = self.ACTION_QUIT
        self._keymap['u'] = self.ACTION_ENTER_USER

    def resolve_input(self, input_string):
        """
        Translate a raw input string into an action constant.

        An input string is typically the string representation of a keypress
        or mouse event.

        Returns:
            Class ACTION_* constant if mapping exists, None otherwise.
        """
        return self._keymap.get(input_string, None)

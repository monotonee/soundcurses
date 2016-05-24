"""
Classes for the implementation of the state pattern.

This module defines the constituent parts of a basic finite state machine
implemented with the state pattern. The main controller acts as the state
context and switches state according to user interactions.

I make an exception to local, relative imports here in order to import
module-level constants.

"""

import abc

from . import user_input

class BaseState(metaclass=abc.ABCMeta):
    """
    An ABC for use in a basic state pattern implementation.

    """
    def __init__(self, controller, state_factory):
        """
        Constructor.

        Args:
            controller: The state pattern context object. Currently this is the
                main controller object.
            state_factory (StateFactory): From local states module.

        """
        self._controller = controller
        self._state_factory = state_factory

    @abc.abstractmethod
    def enter(self):
        """
        Perform main tasks when state is loaded.

        """
        pass

    @abc.abstractmethod
    def exit(self):
        """
        Perform tasks immediately before state is unloaded.

        """
        pass

    @abc.abstractmethod
    def handle_input(self, action):
        """
        Perform tasks in response to user input.

        Args:
            action: A constant value from the local user input module.

        """
        pass

    @abc.abstractmethod
    def run_interval_tasks(self):
        """
        Run tasks that are required to be run on regular interval.

        As long as the state remains loaded, this method will be called once per
        main loop cycle. Do not depend on any specific execution interval. In
        a given main loop iteration, this method will be called before the call
        to the screen's render method.

        """
        pass


class NoUsernameState(BaseState):
    """
    The application has not yet been given a valid SoundCloud username.

    Primarily loaded at application start and when user has entered invalid
    username.

    Possible actions are:
        quit
        input username

    """
    def __init__(self, controller, state_factory, model, view):
        """
        Constructor. Override parent.

        Args:
            model (MainModel): From local models module.
            view (MainView): From local views module.

        """
        super().__init__(controller, state_factory)
        self._model = model
        self._view = view

    def _prompt_username_callback(self, user, **kwargs):
        self._view.hide_loading_animation()

    def _prompt_username(self):
        username = self._view.prompt_username()
        self._view.show_loading_animation()
        self._model.resolve_username(
            username,
            self._prompt_username_callback)

    def enter(self):
        """
        Override parent.

        """
        pass

    def exit(self):
        """
        Override parent.

        """
        pass

    def handle_input(self, action):
        """
        Override parent.

        """
        if action == user_input.ACTION_QUIT:
            self._controller.stop_application()
        elif action == user_input.ACTION_ENTER_USERNAME:
            self._prompt_username()

    def run_interval_tasks(self):
        """
        Override parent.

        """
        pass


class StateFactory:
    """
    Factory to hide creation details of state objects.

    """
    def __init__(self, model, view):
        """
        Constructor.

        Args:
            model (MainModel): From local models module.
            view (MainView): From local views module.

        """
        self._model = model
        self._view = view

    def create_no_username(self, context):
        """
        Create a "no username" state object.

        Args:
            context: The state pattern context object.

        """
        return NoUsernameState(context, self, self._model, self._view)

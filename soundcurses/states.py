"""
Classes for the implementation of the state pattern.

This module defines the constituent parts of a basic finite state machine
implemented with the state pattern. The main controller acts as the state
context and switches state according to user interactions.

Note that I have grudgingly allowed tigher coupling between the state objects
and the controller. Previously, the state objects were only aware of a "context"
interface but states need the ability to call controller-level functions such as
stopping the application. Therefore, the state objects are now aware of the
controller and its public interface. The other option was to pass in a command
factory from which the state objects could create and execute commands such as
"stop application". If many such commands are needed beyond the one or two, then
the command factory will probably be implemented instead.

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
        Perform main tasks immediately after state is loaded.

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

    Can transition to states:
        username loaded

    """
    def __init__(self, controller, state_factory, souncloud_wrapper, view):
        """
        Constructor. Override parent.

        Args:
            souncloud_wrapper (SoundcloudWrapper): From local models module.
            view (MainView): From local views module.

        """
        super().__init__(controller, state_factory)
        self._future_resolve_username = None
        self._souncloud_wrapper = souncloud_wrapper
        self._view = view

    def _prompt_username(self):
        username = self._view.prompt_username()
        self._view.show_loading_animation()
        self._future_resolve_username = \
            self._souncloud_wrapper.resolve_username(username)

    def _verify_username(self):
        """
        Verify the results of a username resolution call.

        """
        self._view.hide_loading_animation()

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

        user_input is a module namespace containing module-level constants.

        """
        if action == user_input.ACTION_QUIT:
            self._controller.stop_application()
        elif action == user_input.ACTION_ENTER_USERNAME:
            self._prompt_username()

    def run_interval_tasks(self):
        """
        Override parent.

        """
        if self._future_resolve_username \
            and self._future_resolve_username.done():
            self._verify_username()


class StateFactory:
    """
    Factory to hide and centralize creation details of state objects.

    """
    def __init__(self, souncloud_wrapper, view):
        """
        Constructor.

        Args:
            souncloud_wrapper (SoundcloudWrapper): From local models module.
            view (MainView): From local views module.

        """
        self._souncloud_wrapper = souncloud_wrapper
        self._view = view

    def create_no_username(self, context):
        """
        Create a "no username" state object.

        Args:
            context: The state pattern context object.

        """
        return NoUsernameState(
            context,
            self,
            self._souncloud_wrapper,
            self._view)

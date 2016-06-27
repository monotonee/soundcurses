"""
Classes for the implementation of the state pattern.

This module defines the constituent parts of a basic finite state machine
implemented with the state pattern. The main controller acts as the state
context and switches state according to user interactions.

Note that I have grudgingly allowed tighter coupling between the state objects
and the controller. Previously, the state objects were only aware of a "context"
interface but states need the ability to call controller-level functions such as
stopping the application. Therefore, the state objects are now aware of the
controller and its public interface.

The other option was to pass in a command factory from which the state objects
could create and execute commands such as "stop application". If many such
commands are needed beyond the one or two, then the command factory will
probably be implemented instead.

"""

import abc
import time

class BaseState(metaclass=abc.ABCMeta):
    """
    An ABC for use in a basic state pattern implementation.

    """

    def __init__(self, input_mapper, controller, state_factory,
        previous_state=None):
        """
        Constructor.

        Args:
            input_mapper (UserInputMapper): Necessary for the use of user action
                constants.
            controller: The state pattern context object. Currently this is the
                main controller object.
            state_factory (StateFactory): From local states module.

        """
        self._controller = controller
        self._input_mapper = input_mapper
        self._previous_state = previous_state
        self._state_factory = state_factory

    def start(self):
        """
        Perform main tasks immediately after state is loaded.

        """
        pass

    def stop(self):
        """
        Perform tasks immediately before state is unloaded.

        """
        pass

    @abc.abstractmethod
    def handle_action(self, action):
        """
        Perform tasks in response to user input.

        Args:
            action: A constant value from the local user input module.

        """
        pass

    def run_interval_tasks(self):
        """
        Run tasks that are required to be run on regular interval.

        As long as the state remains loaded, this method will be called once per
        main loop cycle. Do not depend on any specific execution interval. In
        a given main loop iteration, this method will be called before the call
        to the screen's render method.

        """
        pass


class HelpState(BaseState):
    """
    Class that defines the application's help state.

    When in this state, application is displaying a modal window containing
    key-to-action mappings.

    Possible actions are:
        close help window

    Can transition to states:
        previous state (state that loaded the help state)

    """

    def __init__(self, input_mapper, controller, state_factory, view,
        previous_state=None):
        """
        Constructor.

        """
        super().__init__(input_mapper, controller, state_factory,
            previous_state=previous_state)

        self._view = view

    def start(self):
        """
        Perform main tasks immediately after state is loaded.

        """
        self._view.show_help()

    def stop(self):
        """
        Perform tasks immediately before state is unloaded.

        """
        self._view.hide_help()

    def handle_action(self, action):
        """
        Perform tasks in response to user input.

        Args:
            action: A constant value from the local user input module.

        """
        if action == self._input_mapper.ACTION_CLOSE:
            self._controller.set_state(self._previous_state)


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

    def __init__(self, input_mapper, controller, state_factory,
        model, view, previous_state=None):
        """
        Constructor. Override parent.

        Args:
            model (SoundcloudWrapper): From local models module.
                Necessary for exception checking.
            view (MainView): From local views module. Necessary in order to
                start and stop loading animation.

        """
        super().__init__(input_mapper, controller, state_factory,
            previous_state=previous_state)
        self._future_resolve_username = None
        self._model = model
        self._view = view

    def _prompt_username(self):
        """
        Attempt to get a username from the user.

        """
        username = self._view.prompt_username()
        self._view.show_loading_indicator()
        self._future_resolve_username = self._model.get_user(username=username)

    def _verify_username(self):
        """
        Verify the results of a username resolution call.

        If the username was invalid, briefly display a message to the user
        indicating such. Does not automatically re-prompt the user.

        If the attempt to get user data failed in some other way, re-raises
        the exception and allows it to propagate.

        """
        # Reset future attribute since the future has been consumed.
        future = self._future_resolve_username
        self._future_resolve_username = None

        # The self._model.HTTP_ERROR indicates that username could not be
        # resolved.
        if future.exception():
            username_not_resolved = isinstance(
                future.exception(), self._model.HTTP_ERROR)
            if username_not_resolved:
                # Manual rendering must be performed since this function will be
                # blocking this thread's main loop that contains the interval
                # render call.
                self._view.hide_loading_indicator()
                self._view.show_message('Username not found. Please try again.')
                self._view.render()
                time.sleep(2)
                self._view.hide_message()
            else:
                raise future.exception()
        else:
            user = future.result()
            self._model.current_user = user
            self._view.hide_loading_indicator()
            self._controller.set_state(
                self._state_factory.create_username(
                    self._controller, previous_state=self))

    def handle_action(self, action):
        """
        Override parent.

        user_input is a module namespace containing module-level constants.

        """
        if action == self._input_mapper.ACTION_QUIT:
            self._controller.stop_application()
        elif action == self._input_mapper.ACTION_ENTER_USERNAME:
            self._prompt_username()
        elif action == self._input_mapper.ACTION_HELP:
            self._controller.set_state(
                self._state_factory.create_help(
                    self._controller, previous_state=self))

    def run_interval_tasks(self):
        """
        Override parent.

        """
        if self._future_resolve_username \
            and self._future_resolve_username.done():
            self._verify_username()


class UsernameState(BaseState):
    """
    Class that defines the application's state when it has a valid username.

    When in this state, application has received a valid username and has
    retreived the user's complete data object. This state is invalid and will
    not function without a username and user data present in the model.

    With this username, this state will load the user's data for the currently-
    selected nav item (a user's subresource). Currently, only a single
    subresource set will be loaded at a time and other will be loaded only
    when required at runtime.

    Possible actions are:
        close help window

    Can transition to states:
        previous state (state that loaded the help state)

    Attributes:
        SUBRESOURCE_LOADING_DELAY (float): The delay after which a selected
            subresource's data will be loaded.

    """

    SUBRESOURCE_LOADING_DELAY = 1.0

    def __init__(self, input_mapper, controller, state_factory, view,
        previous_state=None):
        """
        Constructor.

        """
        super().__init__(input_mapper, controller, state_factory,
            previous_state=previous_state)

        self._nav_item_cycle_timestamp = None
        self._nav_item_cycled = False
        self._view = view

    def _check_subresource_load_timer(self):
        """
        Execute subresource loading if the nav item delay has elapsed.

        When cycling through nav items (each corresponding to a user
        subresource), the subresource will nto be immediately loaded into the
        content region. Once a given nav item has been selected for a certain
        amount of time, only then will the corresponding subresource be loaded.

        """
        if self._nav_item_cycled:
            time_elapsed = time.time() - self._nav_item_cycle_timestamp
            if time_elapsed >= self.SUBRESOURCE_LOADING_DELAY:
                self._nav_item_cycle_timestamp = None
                self._nav_item_cycled = False

    def _cycle_nav_item(self):
        """
        Select the next nav item and start subresource loading timer.

        """
        self._view.select_next_nav_item()
        self._nav_item_cycled = True
        self._nav_item_cycle_timestamp = time.time()

    def start(self):
        """
        Perform main tasks immediately after state is loaded.

        """
        pass

    def stop(self):
        """
        Perform tasks immediately before state is unloaded.

        """
        pass

    def handle_action(self, action):
        """
        Perform tasks in response to user input.

        Args:
            action: A constant value from the local user input module.

        """
        if action == self._input_mapper.ACTION_QUIT:
            self._controller.stop_application()
        elif action == self._input_mapper.ACTION_CYCLE_NAV:
            self._cycle_nav_item()

    def run_interval_tasks(self):
        """
        Override parent.

        """
        self._check_subresource_load_timer()


class StateFactory:
    """
    Factory to hide and centralize creation details of state objects.

    """

    def __init__(self, input_mapper, model, view):
        """
        Constructor.

        Args:
            input_mapper (UserInputMapper)
            model (SoundcloudWrapper): From local models module.
            view (MainView): From local views module.

        """
        self._input_mapper = input_mapper
        self._model = model
        self._view = view

    def create_help(self, context, previous_state=None):
        """
        Create a "no username" state object.

        Args:
            context: The state pattern context object.

        """
        return HelpState(
            self._input_mapper,
            context,
            self,
            self._view,
            previous_state=previous_state)

    def create_no_username(self, context, previous_state=None):
        """
        Create a "no username" state object.

        Args:
            context: The state pattern context object.

        """
        return NoUsernameState(
            self._input_mapper,
            context,
            self,
            self._model,
            self._view,
            previous_state=previous_state)

    def create_username(self, context, previous_state=None):
        """
        Create a "username" state object.

        Args:
            context: The state pattern context object.

        """
        return UsernameState(
            self._input_mapper,
            context,
            self,
            self._view,
            previous_state=previous_state)

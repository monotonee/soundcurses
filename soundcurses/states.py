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
import datetime
import time

class BaseState(metaclass=abc.ABCMeta):
    """
    An ABC for use in a basic state pattern implementation.

    """

    def __init__(self, input_mapper, controller, state_factory, view,
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
        self._view = view

    def _display_temp_message(self, message):
        """
        Display a message window in the view for a few seconds.

        Manual rendering must be performed since this function will be
        blocking this thread's main loop that contains the interval
        render call.

        Args:
            message (str): The message to display in the window.

        """
        self._view.show_message(message)
        self._view.render()
        time.sleep(2)
        self._view.hide_message()

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
        super().__init__(input_mapper, controller, state_factory, view,
            previous_state=previous_state)

        self._view = view

    def handle_action(self, action):
        """
        Perform tasks in response to user input.

        Args:
            action: A constant value from the local user input module.

        """
        if action == self._input_mapper.ACTION_CLOSE:
            self._controller.set_state(self._previous_state)

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
        view, model, previous_state=None):
        """
        Constructor. Override parent.

        Args:
            model (SoundcloudWrapper): From local models module.
                Necessary for exception checking.
            view (MainView): From local views module. Necessary in order to
                start and stop loading animation.

        """
        super().__init__(input_mapper, controller, state_factory, view,
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
                self._display_temp_message(
                    'Username not found. Please try again.')
            else:
                raise future.exception()
        else:
            user = future.result()
            self._model.current_user = user
            self._view.hide_loading_indicator()
            self._controller.set_state(
                self._state_factory.create_subresource_state(
                    self._view.selected_nav_item,
                    self._controller,
                    previous_state=self))

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

    def start(self):
        """
        Override parent.

        """
        self._prompt_username()


class SubresourceState(BaseState):
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
        user_subresrc_future (concurrent.futures.Future): A future from the
            model that returns requested subresource data.

    """

    SUBRESOURCE_LOADING_DELAY = 1.0

    def __init__(self, input_mapper, controller, state_factory, view, model,
        previous_state=None):
        """
        Constructor.

        """
        super().__init__(input_mapper, controller, state_factory, view,
            previous_state=previous_state)

        self._model = model
        self._nav_item_cycle_timestamp = None
        self._nav_item_cycled = False
        self._view = view

    def _check_nav_item_cycle_timer(self):
        """
        Execute subresource loading if the nav item delay has elapsed.

        When cycling through nav items (each corresponding to a user
        subresource), the subresource will not be immediately loaded into the
        content region. Once a given nav item remains selected for a certain
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
        self._nav_item_cycle_timestamp = time.time()
        self._nav_item_cycled = True

    def _format_track_line_list(self, tracks_list):
        """
        Format a list of track metadata strings for display to the user.

        Args:
            tracks_list (list): A list of track subresource objects as returned
                by the model.

        Returns:
            list: A list of strings suitable for display to the user.

        """
        lines_list = []
        list_item_number = 0
        max_number_length = len(str(len(tracks_list) - 1))
        max_title_length =  len(max(
            tracks_list, key=lambda track: len(track.title)).title)
        for track in tracks_list:
            track_number = str(list_item_number).rjust(max_number_length, '0')
            track_title = track.title.ljust(max_title_length)
            track_duration = str(
                datetime.timedelta(seconds=round(track.duration / 1000, 0)))
            lines_list.append(
                track_number + '. '
                + track_title + ' '
                + track_duration)
            list_item_number += 1

        return lines_list

    def _load_user_subresource(self, subresource):
        """
        Fetch subresource data from model and set to current subresource.

        The view responds to changes in the current subresource by displaying
        the new data in the content region.

        Args:
            subresource (str): A subresource name. The string should always
                correspond to one of the available subresource strings found
                in the model and displayed in the view's nav region.

        """
        return self._model.get_user_subresource(
            str(self._model.current_user.id), subresource)

    def handle_action(self, action):
        """
        Perform tasks in response to user input.

        Args:
            action: A constant value from the local user input module.

        """
        if action == self._input_mapper.ACTION_QUIT:
            self._controller.stop_application()
        elif action == self._input_mapper.ACTION_ENTER_USERNAME:
            self._controller.set_state(
                self._state_factory.create_no_username(
                    self._controller, previous_state=self))
        elif action == self._input_mapper.ACTION_CYCLE_NAV:
            self._cycle_nav_item()
        elif action == self._input_mapper.ACTION_HELP:
            self._controller.set_state(
                self._state_factory.create_help(
                    self._controller, previous_state=self))

    def run_interval_tasks(self):
        """
        Override parent.

        """
        self._check_nav_item_cycle_timer()
        # self._check_user_subresrc_future()

    def start(self):
        """
        Perform main tasks immediately after state is loaded.

        """
        if not self._model.current_user:
            raise RuntimeError('Invalid state. No user data loaded.')

    def stop(self):
        """
        Perform tasks immediately before state is unloaded.

        """
        pass


class TracksLoadedState(SubresourceState):
    """
    A class that represents a state in which a user's tracks subresrc is loaded.

    """

    def __init__(self, input_mapper, controller, state_factory, view, model,
        previous_state=None):
        """
        Constructor

        """
        super().__init__(input_mapper, controller, state_factory, view, model,
        previous_state=previous_state)

        self._tracks_future = None
        self._tracks_loaded = False

    @property
    def _tracks_future_ready(self):
        """
        Get the status of the internal tracks future object.

        Returns:
            bool: True if future is present and done, false otherwise.

        """
        return self._tracks_future and self._tracks_future.done()

    def _process_tracks_future_results(self):
        """
        Performs operations on the tracks data for display.

        If an exception was raised in the data retrieval, display a message to
        the user.

        """
        self._view.hide_loading_indicator()
        future = self._tracks_future
        if future.exception():
            tracks_loading_failed = isinstance(
                future.exception(), self._model.HTTP_ERROR)
            if tracks_loading_failed:
                self._display_temp_message('Tracks data could not be loaded.')
            else:
                raise future.exception()
        else:
            tracks_data = future.result()
            self._model.set_current_user_subresource(
                self._model.USER_SUBRESRC_01_TRACKS, tracks_data)
            content_lines = []
            if tracks_data:
                content_lines = self._format_track_line_list(tracks_data)
            self._view.content_lines = content_lines
        self._tracks_future = None
        self._tracks_loaded = True

    def handle_action(self, action):
        """
        Override parent.

        """
        if self._tracks_loaded:
            if action == self._input_mapper.ACTION_CONTENT_LINE_NEXT:
                self._view.content_line_next()
            elif action == self._input_mapper.ACTION_CONTENT_LINE_PREV:
                self._view.content_line_previous()
            elif action == self._input_mapper.ACTION_CONTENT_PAGE_NEXT:
                self._view.content_page_next()
            elif action == self._input_mapper.ACTION_CONTENT_PAGE_PREV:
                self._view.content_page_previous()
            else:
                super().handle_action(action)

    def run_interval_tasks(self):
        """
        Override parent.

        """
        super().run_interval_tasks()
        if self._tracks_future_ready:
            self._process_tracks_future_results()

    def start(self):
        """
        Override parent.

        """
        super().start()
        self._view.show_loading_indicator()
        self._tracks_future = self._load_user_subresource(
            self._model.USER_SUBRESRC_01_TRACKS)


class StateFactory:
    """
    Factory to hide and centralize creation details of state objects.

    """

    def __init__(self, input_mapper, view, model):
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
            self._view,
            self._model,
            previous_state=previous_state)

    def create_subresource_state(self, subresource, context,
        previous_state=None):
        """
        Create a "subresource" state object.

        Args:
            subresource (str): A valid subresource name string.
            context: The state pattern context object.
            previous_state: A state object.

        Raises:
            ValueError: If a state cannot be found for given subresource name.

        """
        if subresource == self._model.USER_SUBRESRC_01_TRACKS:
            state = TracksLoadedState
        else:
            raise RuntimeError(
                'No state available for subresource "' + subresource + '"')

        return state(
            self._input_mapper,
            context,
            self,
            self._view,
            self._model,
            previous_state=previous_state)

""" Main entry point

"""

# Standard library imports.
import concurrent.futures
import curses
import locale

# Third-party imports.
import requests
import signalslot
import soundcloud

# Local imports.
from soundcurses import (controllers, models, states, user_input)
from soundcurses.curses import (components, effects, screen, views, windows)

def main(stdscr):
    """ Compose curses windows and pads.

    Note that stdscr is passed into the main function by curses.wrapper().

    """

    curses_wrapper = components.CursesWrapper(curses, locale)

    # Compose curses window wrappers.
    curses_string_factory = windows.CursesStringFactory(curses_wrapper)
    signal_window_render_layer_changed = signalslot.Signal(
        args=['window', 'delta'])
    window_stdscr = windows.StdscrWindow(
        stdscr,
        signal_window_render_layer_changed,
        curses_wrapper)
    window_header = windows.HeaderWindow(
        curses_wrapper.newwin(3, curses_wrapper.COLS, 0, 0),
        signal_window_render_layer_changed)
    window_nav = windows.NavWindow(
        curses_wrapper.newwin(3, curses_wrapper.COLS, 3, 0),
        signal_window_render_layer_changed,
        curses_string_factory)
    window_content = windows.ContentWindow(
        curses_wrapper.newwin(
            curses_wrapper.LINES - 6,
            curses_wrapper.COLS,
            6, 0),
        signal_window_render_layer_changed,
        curses_wrapper)

    # Compose screen.
    signal_rendered = signalslot.Signal()
    render_queue = screen.WindowRenderQueue()
    curses_screen = screen.CursesScreen(
        curses_wrapper,
        render_queue,
        signal_rendered,
        window_stdscr,
        window_header,
        window_nav,
        window_content)

    # Create reusable modal window 40% of screen size, centered in screen.
    # Is hidden by default.
    simple_spinner_animation = effects.SimpleSpinner(
        curses_screen)
    window_modal_dim_y = round(curses_wrapper.LINES * 0.4)
    window_modal_dim_x = round(curses_wrapper.COLS * 0.4)
    window_modal = windows.ModalWindow(
        curses_wrapper.newwin(
            window_modal_dim_y,
            window_modal_dim_x,
            round((curses_wrapper.LINES - window_modal_dim_y) / 2),
            round((curses_wrapper.COLS - window_modal_dim_x) / 2)),
        signal_window_render_layer_changed,
        curses_wrapper,
        curses_string_factory,
        simple_spinner_animation)
    curses_screen.add_window(window_modal)

    # Compose input source.
    input_source = components.InputSource(window_stdscr)

    # IMPORTANT: This soundcloud.Client instance is not to be touched.
    # It is accessed exclusively by a separate thread. Its existence in the main
    # thread is solely to allow the composition of function partials which are
    # passed to the thread and executed.
    #
    # The "constant" HTTP_ERROR attribute is added to fix leaky abstraction
    # in the soundcloud interface. Calling code (other than the this) no longer
    # has to be aware of soundcloud's internal method of making HTTP requests.
    soundcloud_client = soundcloud.Client(
        client_id='e9cd65934510bf631372af005c2f37b5',
        use_ssl=True)
    soundcloud_client.HTTP_ERROR = requests.exceptions.HTTPError

    # Compose "model".
    network_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    souncloud_wrapper = models.SoundcloudWrapper(
        soundcloud_client,
        network_executor,
        signalslot.Signal(),
        signalslot.Signal())

    # Compose view(s).
    main_view = views.MainView(
        input_source,
        curses_screen,
        souncloud_wrapper,
        window_header,
        window_nav,
        window_content,
        window_modal)

    # Compose controllers.
    input_mapper = user_input.UserInputMapper()
    state_factory = states.StateFactory(
        input_mapper,
        souncloud_wrapper,
        main_view)
    main_controller = controllers.MainController(
        input_mapper,
        state_factory,
        main_view)

    main_controller.start_application()

curses.wrapper(main)

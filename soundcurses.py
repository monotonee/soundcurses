""" Main entry point

"""

# Standard library imports.
import curses
import locale
import queue
import threading

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
    signal_window_render_layer_changed = signalslot.Signal(
        args=['window', 'delta'])
    window_stdscr = windows.StdscrWindow(
        curses_wrapper,
        stdscr,
        signal_window_render_layer_changed)
    window_header = windows.HeaderWindow(
        curses_wrapper,
        curses_wrapper.newwin(3, curses_wrapper.COLS, 0, 0),
        signal_window_render_layer_changed)
    window_nav = windows.NavWindow(
        curses_wrapper,
        curses_wrapper.newwin(3, curses_wrapper.COLS, 3, 0),
        signal_window_render_layer_changed)
    window_content = windows.ContentWindow(
        curses_wrapper,
        curses_wrapper.newwin(
            curses_wrapper.LINES - 6,
            curses_wrapper.COLS,
            6, 0),
        signal_window_render_layer_changed)

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
        curses_wrapper,
        curses_wrapper.newwin(
            window_modal_dim_y,
            window_modal_dim_x,
            round((curses_wrapper.LINES - window_modal_dim_y) / 2),
            round((curses_wrapper.COLS - window_modal_dim_x) / 2)),
        signal_window_render_layer_changed,
        simple_spinner_animation)
    curses_screen.add_window(window_modal)

    # Compose input source.
    input_source = components.InputSource(window_stdscr)

    # Compose view(s).
    main_view = views.MainView(
        input_source,
        curses_screen,
        window_header,
        window_nav,
        window_content,
        window_modal)

    # The first queue is the network I/O thread's input queue.
    # The second queue is the network I/O thread's output queue.
    network_thread_input_queue = queue.Queue()
    network_thread_output_queue = queue.Queue()

    # Start network I/O thread.
    network_thread = threading.Thread(
        target=models.run_network_io,
        args=(network_thread_input_queue, network_thread_output_queue),
        daemon=True)

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

    # Compose model.
    main_model = models.MainModel(
        soundcloud_client,
        network_thread_input_queue,
        network_thread_output_queue)

    # Compose controllers.
    state_factory = states.StateFactory(main_model, main_view)
    input_mapper = user_input.UserInputMapper()
    main_controller = controllers.MainController(
        input_mapper,
        main_model,
        state_factory,
        main_view)

    main_controller.start_application()

curses.wrapper(main)

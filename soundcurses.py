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
from soundcurses import (config, controllers, models, states)
from soundcurses.curses import (effects, regions, screen, user_input, views,
    windows)

def main(stdscr):
    """
    Compose all objects.

    This is the composition root. All constructor injection is handled here.

    Note that stdscr is passed into the main function by curses.wrapper().

    """

    # Wrap curses
    curses_wrapper = screen.CursesWrapper(curses, locale)

    # Compose screen.
    curses_screen = screen.CursesScreen(
        curses_wrapper, screen.RenderQueue(), signalslot.Signal())

    # Compose window factory.
    window_factory = windows.CursesWindowFactory(
        curses_wrapper, curses_screen, signalslot)

    # Compose string factory.
    string_factory = windows.CursesStringFactory(curses_wrapper)

    # IMPORTANT: This soundcloud.Client instance is not to be touched.
    # It is accessed exclusively by a separate thread. Its existence in the main
    # thread is solely to allow the composition of function partials which are
    # passed to the thread and executed.
    #
    # The "constant" HTTP_ERROR attribute is added to fix leaky abstraction
    # in the soundcloud interface. Calling code (other than this) no longer
    # has to be aware of soundcloud's internal method of making HTTP requests.
    soundcloud_client = soundcloud.Client(
        client_id='e9cd65934510bf631372af005c2f37b5',
        use_ssl=True)
    soundcloud_client.HTTP_ERROR = requests.exceptions.HTTPError

    # Compose model.
    thread_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    soundcloud_wrapper = models.SoundcloudWrapper(
        soundcloud_client, thread_executor)
    model = models.Model(soundcloud_wrapper, signalslot.Signal())

    # Begin composing view regions.
    y_coord_offset = 0

    # Compose stdscr window and pass to screen. No associated region.
    stdscr_window = window_factory.wrap_window(stdscr)
    curses_screen.add_window(stdscr_window)

    # Compose header region.
    header_window = window_factory.create_window(
        1, curses_wrapper.COLS,
        y_coord_offset, 0,
        render_layer=curses_screen.RENDER_LAYER_REGIONS)
    curses_screen.add_window(header_window)
    header_region = regions.HeaderRegion(header_window, curses_wrapper)
    y_coord_offset += header_window.lines

    # Compose status region.
    status_window = window_factory.create_window(
        3, curses_wrapper.COLS,
        y_coord_offset, 0,
        render_layer=curses_screen.RENDER_LAYER_REGIONS)
    curses_screen.add_window(status_window)
    status_region = regions.StatusRegion(status_window, string_factory)
    y_coord_offset += status_window.lines

    # Compose nav region.
    nav_window = window_factory.create_window(
        3, curses_wrapper.COLS,
        y_coord_offset, 0,
        render_layer=curses_screen.RENDER_LAYER_REGIONS)
    curses_screen.add_window(nav_window)
    nav_region = regions.NavRegion(nav_window, string_factory, model)
    y_coord_offset += nav_window.lines

    # Compose content region.
    content_window = window_factory.create_window(
        curses_wrapper.LINES - y_coord_offset, curses_wrapper.COLS,
        y_coord_offset, 0,
        render_layer=curses_screen.RENDER_LAYER_REGIONS)
    curses_screen.add_window(content_window)
    content_region = regions.ContentRegion(
        content_window,
        curses_wrapper,
        string_factory)

    # Compose input source.
    input_source = user_input.InputSource(curses_wrapper, stdscr_window)

    # Compose view(s).
    input_mapper = config.UserInputMapper()
    modal_factory = regions.ModalRegionFactory(
        curses_wrapper,
        curses_screen,
        window_factory,
        string_factory,
        effects.SimpleSpinner(curses_screen),
        input_mapper)
    view = views.MainView(
        input_source,
        curses_screen,
        model,
        status_region,
        nav_region,
        content_region,
        modal_factory)

    # Compose controllers.
    state_factory = states.StateFactory(
        input_mapper,
        view,
        model)
    controller = controllers.MainController(
        input_mapper,
        state_factory,
        view,
        model)

    controller.start_application()

curses.wrapper(main)

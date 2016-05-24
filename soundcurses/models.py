"""
Defines the application model components.

"""

import functools
import queue

class MainModel:
    """
    Main model interface for the application.

    Behind the scenes, manages communication with a separate network I/O
    thread in which the communication with the SoundCloud API takes place.

    Attributes:
        _SC_DOMAIN_NAME (string): Simply used to build SoundCloud permalink URLs
            when necessary for API calls.
        _network_thread_input_queue (queue.Queue): The queue from which the
            network I/O thread takes its tasks.
        _network_thread_output_queue (queue.Queue): The queue onto which the
            network I/O thread places its output when tasks are completed.
        _soundcloud_client (soundcloud.Client): Used for building partial
            functions to pass to network thread. The soundcloud.Client is
            assumed to be non-thread-safe. Do not actually call any methods
            on the Client in this class. Leave execution to the recipient
            of objects pushed into the output_queue.
        _soundcloud_domain_name (string):

    """

    _SC_DOMAIN_NAME = 'soundcloud.com'

    def __init__(self, soundcloud_client, input_queue, output_queue):
        """
        Constructor.

        Args:
            soundcloud_client (soundcloud.Client): Used for building partial
                functions to pass to network thread. The soundcloud.Client is
                assumed to be non-thread-safe. Do not actually call any methods
                on the Client in this class. Leave execution to the recipient
                of objects pushed into the output_queue.

        """
        self._network_thread_input_queue = input_queue
        self._network_thread_output_queue = output_queue
        self._soundcloud_client = soundcloud_client

    def _construct_permalink_url(self, path):
        """ Given a soundcloud.com URL path, returns a string containing
        the full soundcloud.com URL.

        An example resource path is the username "/monotonee". The
        resulting soundcloud.com permalink URL under the TLS protocol would be
        "https://soundcloud.com/monotonee".

        """
        return self._soundcloud_client.scheme \
            + self._SC_DOMAIN_NAME \
            + path

    def run_interval_tasks(self):
        """
        Run tasks on each iteration of the main loop.

        Do not count on any specific interval length.

        Check the network thread output queue for new output and process it.
        All output is expected to be a callable. Since this class is the only
        one currently feeding input to the network I/O thread, this can be
        safely assumed.

        """
        try:
            callback = self._network_thread_output_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            callback()
            self._network_thread_output_queue.task_done()

    def resolve_username(self, username, callback):
        """
        Contacts the SoundCloud API in an attempt to resolve a username string
        to a SoundCloud API user ID.

        See: https://developers.soundcloud.com/docs/api/reference#resolve

        """
        target = functools.partial(
            self._soundcloud_client.get,
            '/resolve',
            url=self._construct_permalink_url('/' + str(username)))
        self._network_thread_input_queue.put((target, callback))

    # def handle_resolve_username(self, user, **kwargs):
        # return_value = None
        # if kwargs['exception']:
            # if isinstance(kwargs['exception'], self._soundcloud_client.HTTP_ERROR):
        # else:


def run_network_io(input_queue, output_queue):
    """
    Make calls to the SoundCloud API.

    Intended to be run as the target of a separate thread.

    Input consists of a tuple containing:
        target (callable): The callable to, well... call.
        callback: A function object that will be placed into output queue
            when API call is complete.

    Args:
        client: The soundcloud.Client instance used to make API requests.
        input_queue (queue.Queue) The queue from which to receive tasks.
        output_queue (queue.Queue) The queue to which to place output.

    """
    while True:
        kwargs = {}
        result = None
        target, callback = input_queue.get()

        try:
            result = target()
        except Exception as exception:
            kwargs['exception'] = exception

        callback_with_result = functools.partial(callback, result, **kwargs)
        output_queue.put(callback_with_result)
        input_queue.task_done()











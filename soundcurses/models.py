"""
Defines the application model components.

"""

import concurrent.futures

class SoundcloudWrapper:
    """
    Wrapper for Soundcloud library.

    Behind the scenes, manages communication with a separate network I/O
    thread in which the communication with the SoundCloud API takes place.
    Presents a coarser interface to the other application components.

    The data objects created and returned by the Soundcloud library comprise
    the domain model and I therefore believe that no further classes or
    interfaces are necessary at this time.

    As this wrapper class is intended to be rather thin, I find it reasonable
    to allow the async nature of network API calls to leak through the
    abstraction. concurrent.futures.Future instances are returned from the
    coarse method calls, exposing more implementation but providing simplicity.
    It is my opinion that callbacks, events, and/or observers flying
    every which way are also leaked abstraction so I have chosen the option
    with the least impact on code maintainability and testability.

    Attributes:
        _SC_DOMAIN_NAME (string): Simply used to build SoundCloud permalink URLs
            when necessary for API calls.
        _soundcloud_client (soundcloud.Client): Used for building partial
            functions to pass to network thread. The soundcloud.Client is
            assumed to be non-thread-safe. Do not actually call any methods
            on the Client in this class. Leave execution to the recipient
            of objects pushed into the output_queue.
        _soundcloud_domain_name (string): The SoundCloud domain name.

        signal_current_tracks (signalslot.Signal): Indicates that current track
            set has been changed.
        signal_current_user (signalslot.Signal): Indicates that current user has
            been changed.

    """

    _SC_DOMAIN_NAME = 'soundcloud.com'

    def __init__(self, soundcloud_client, network_executor,
        signal_current_user, signal_current_track_set):
        """
        Constructor.

        Args:
            soundcloud_client (soundcloud.Client): Used for building partial
                functions to pass to network thread. The soundcloud.Client is
                assumed to be non-thread-safe. Do not actually call any methods
                on the Client in this class. Leave execution to the recipient
                of objects pushed into the output_queue.

        """
        self._current_user = None
        self._network_executor = network_executor
        self._soundcloud_client = soundcloud_client

        self.signal_change_current_track_set = signal_current_track_set
        self.signal_change_current_user = signal_current_user

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

    @property
    def current_user(self):
        return self._current_user

    @current_user.setter
    def current_user(self, user):
        self._current_user = user
        self.signal_change_current_user.emit()

    def get_user_by_username(self, username):
        """
        Contact the SoundCloud API and attempt to resolve a username string
        to a SoundCloud API user ID.

        By default, the soundcloud library follows any HTTP redirects to a
        resolved user and will return a user data object. The user data object
        is documented in the SoundCloud API Reference.

        If a user cannot be resolved from the username, soundcloud lets its
        underlying HTTP library, "request", leak through the abstraction by
        allowing its HTTPException bubble.

        See:
            https://developers.soundcloud.com/docs/api/reference#resolve
            https://developers.soundcloud.com/docs/api/reference#users

        """
        future = self._network_executor.submit(
            self._soundcloud_client.get,
            '/resolve',
            url=self._construct_permalink_url('/' + str(username)))

        # import time
        # future = self._network_executor.submit(time.sleep, 3)

        return future

    @property
    def HTTP_ERROR(self):
        """
        Get the wrapper's constant HTTP exception property.

        """
        return self._soundcloud_wrapper.HTTP_ERROR












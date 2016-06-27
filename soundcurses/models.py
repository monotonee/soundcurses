"""
Defines the application model components.

"""

import collections
import concurrent.futures
import functools

class Model:
    """
    The application model.

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
        _SC_DOMAIN_NAME (str): Simply used to build SoundCloud permalink URLs
            when necessary for API calls.
        AVAIL_USER_SUBRESOURCE_* (str): The subresources of a SoundCloud user
            that are available for the user to choose.
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

    AVAIL_USER_SUBRESOURCE_01 = 'tracks'
    AVAIL_USER_SUBRESOURCE_02 = 'playlists'
    AVAIL_USER_SUBRESOURCE_03 = 'favorites'
    AVAIL_USER_SUBRESOURCE_04 = 'followings'
    AVAIL_USER_SUBRESOURCE_05 = 'followers'

    def __init__(self, soundcloud_client, signal_current_user,
        signal_current_track_set):
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
        self._soundcloud_client = soundcloud_client

        self.signal_change_current_track_set = signal_current_track_set
        self.signal_change_current_user = signal_current_user

    @property
    def HTTP_ERROR(self):
        """
        Get the wrapper's constant HTTP exception property.

        """
        return self._soundcloud_client.HTTP_ERROR

    @property
    def avail_user_subresources(self):
        """
        Get the available user subresources.

        Examples include a user's tracks, playlists, favorites, etc.

        Returns:
            list: A list of subresource name strings.

        """
        subresource_strings = []
        for attribute in dir(self):
            if attribute.startswith('AVAIL_USER_SUBRESOURCE_'):
                subresource_strings.append(getattr(self, attribute))

        return subresource_strings

    @property
    def current_user(self):
        return self._current_user

    @current_user.setter
    def current_user(self, user):
        self._current_user = user
        self.signal_change_current_user.emit()

    def get_user(self, user_id=None, username=None):
        """
        Get the user data object for a given user identifier.

        Args:
            user_id (str): A SoundCloud API user ID.
            username (str): A SoundCloud.com username.

        Returns:
            concurrent.futures.Future: A future object wrapping the async
                network I/O.

        """
        return self._soundcloud_client.get_user(
            user_id=user_id,
            username=username)

    def run_interval_tasks(self):
        """
        Run tasks once per main loop iteration. Called in main loop.

        """
        self._soundcloud_client.run_interval_tasks()


class SoundcloudWrapper:
    """
    A class that fetches and maintains SoundCloud data.

    This is designed to fetch necessary SoundCloud data, to organize fetched
    SoundCloud data, and to avoid redundant network I/O through caching.

    Currently, caching is done in memory but this separate layer of abstraction
    will allow for persistent storage in the future.

    Attributes:
        _cached_usernames (dict): A mapping of usernames to user IDs.
        _cached_users (dict): Map of user IDs to the respective user data. Data is
            contained primarily in soundcloud.Resource objects.

    """

    _SC_DOMAIN_NAME = 'soundcloud.com'

    def __init__(self, soundcloud_client, thread_executor):
        """
        Constructor.

        """
        self._cache_queue = collections.deque()
        self._cached_usernames = {}
        self._cached_users = {}
        self._soundcloud_client = soundcloud_client
        self._thread_executor = thread_executor

    @property
    def HTTP_ERROR(self):
        """
        Get the wrapper's constant HTTP exception property.

        """
        return self._soundcloud_client.HTTP_ERROR

    def _cache_user(self, future):
        """
        Cache user data object returned by SoundCloud API.

        Designed to be called as part of the main loop (interval tasks). Will
        only cache data if future is done and no exceptions were raised.

        Returns:
            bool: True if cached, false otherwise.

        """
        cache_completed = False
        if future.done():
            cache_completed = True
            if not future.exception():
                user = future.result()
                self._cached_usernames[user.username] = user.id
                self._cached_users[user.id] = user

        return cache_completed

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

    def _execute_cache_stack(self):
        """
        Execute the required caching functions in the queue.

        If a caching function returns true, remove it from the queue and execute
        next function in queue. Break as soon as a function returns false.

        """
        while self._cache_queue:
            cache_completed = self._cache_queue[-1]()
            if cache_completed:
                self._cache_queue.pop()
            else:
                break

    def get_user(self, user_id=None, username=None):
        """
        Get the user data object for a given user identifier.

        Either a user ID or a username string can be given, but not both. If
        user ID, a simple user GET request will be made. If username, then a
        resolve API request will be made. Any errors will be attached to the
        future.

        By default, the soundcloud library follows any HTTP redirects to a
        resolved user and will return a user data object. The user data object
        is documented in the SoundCloud API Reference.

        If a user cannot be resolved from the username, soundcloud lets its
        underlying HTTP library, "request", leak through the abstraction by
        allowing its HTTPException to propagate.

        If available, cached data will be returned instead of making a new
        network request to the remote API.

        See:
            https://developers.soundcloud.com/docs/api/reference#resolve
            https://developers.soundcloud.com/docs/api/reference#users

        Args:
            user_id (str): A SoundCloud API user ID.
            username (str): A SoundCloud.com username.

        Returns:
            concurrent.futures.Future: A future object.

        Raises:
            RuntimeError: If both or neither keyword arguments are passed.

        """
        # Validate arguments.
        if (user_id and username) or (not user_id and not username):
            raise RuntimeError('Must pass only a single user identifier.')

        # Check cache first. The concurrent.futures.Future documentaion states
        # that futures should not be created directly so, to produce a future,
        # even cache fetches are submitted to executor for now. This smells.
        cached_data_used = False
        if username and username in self._cached_usernames:
            user_id = self._cached_usernames[username]
        if user_id and user_id in self._cached_users:
            bound_callable = functools.partial(
                lambda user: user, self._cached_users[user_id])
            future = self._thread_executor.submit(bound_callable)
            cached_data_used = True

        # If neccesary, choose API call and execute.
        if not cached_data_used:
            if username:
                future = self._thread_executor.submit(
                    self._soundcloud_client.get,
                    '/resolve',
                    url=self._construct_permalink_url('/' + str(username)))
                self._cache_queue.append(
                    functools.partial(self._cache_user, future))
            else:
                future = self._thread_executor.submit(
                    self._soundcloud_client.get,
                    '/users/' + user_id)
                self._cache_queue.append(
                    functools.partial(self._cache_user, future))

        return future

    def run_interval_tasks(self):
        """
        Run tasks once per main loop iteration.

        """
        self._execute_cache_stack()








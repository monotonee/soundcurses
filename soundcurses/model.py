""" Defines a model abstraction for the SoundCloud API.

"""

class CursesModel:

    def __init__(self, soundcloud_client):
        self._soundcloud_client = soundcloud_client

    def get_user(self, username):
        """ Searches for SoundCloud user and returns data.

        """
        pass


""" Defines the application model components.

"""

# Necessary to catch unresolved URL exceptions from SoundCloud.
import requests

class MainModel:

    def __init__(self, soundcloud_client):
        self._soundcloud_client = soundcloud_client
        self._soundcloud_domain_name = 'soundcloud.com'

    def _construct_permalink_url(self, path):
        """ Given a soundcloud.com URL path, returns a string containing
        the full soundcloud.com URL.

        An example resource path is the username "/monotonee". The
        resulting soundcloud.com permalink URL under the TLS protocol would be
        "https://soundcloud.com/monotonee".

        """
        return self._soundcloud_client.scheme \
            + self._soundcloud_domain_name \
            + path

    def resolve_username(self, username):
        """ Contacts the SoundCloud API in an attempt to resolve a username
        string to a SoundCloud API user ID.

        See: https://developers.soundcloud.com/docs/api/reference#resolve

        """
        user = self._soundcloud_client.get(
            '/resolve', url=self._construct_permalink_url('/' + str(username)))

        return user


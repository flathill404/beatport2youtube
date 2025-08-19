import os
from typing import Any
from urllib.parse import urljoin

import requests
from requests.auth import HTTPBasicAuth


class BeatportClientError(Exception):
    """Custom exception for BeatportClient errors."""

    pass


class BeatportClient:
    """
    A Python client for the Beatport API v4.

    This client handles the OAuth 2.0 Client Credentials Grant Flow for
    authentication and provides methods to interact with various Beatport API
    endpoints.
    """

    _TOKEN_URL = "https://api.beatport.com/v4/auth/o/token/"
    _BASE_API_URL = "https://api.beatport.com/v4/"

    def __init__(self, client_id: str, client_secret: str):
        """
        Initializes the BeatportClient.

        It's recommended to load credentials from environment variables
        or a secure configuration manager rather than hardcoding them.

        Args:
            client_id: Your Beatport application's client ID.
            client_secret: Your Beatport application's client secret.

        Raises:
            ValueError: If client_id or client_secret are not provided.
            BeatportClientError: If authentication fails.
        """
        if not client_id or not client_secret:
            raise ValueError("Client ID and Client Secret must be provided.")

        self.client_id = client_id
        self.client_secret = client_secret
        self.session = requests.Session()
        self.access_token: str | None = None

        if True:
            self.access_token = os.environ.get("BEATPORT_ACCESS_TOKEN")
            self.session.headers.update(
                {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json",
                }
            )
            return

        self._authenticate()

    def _authenticate(self) -> None:
        """
        Authenticates with the Beatport API using Client Credentials Flow
        and sets the authorization header for the session.

        Raises:
            BeatportClientError: If authentication request fails or token is not in response.
        """
        auth = HTTPBasicAuth(self.client_id, self.client_secret)
        data = {"grant_type": "client_credentials"}

        try:
            response = requests.post(self._TOKEN_URL, auth=auth, data=data)
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data.get("access_token")

            if not self.access_token:
                raise BeatportClientError(
                    "Failed to retrieve access token from Beatport's response."
                )

            self.session.headers.update(
                {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json",
                }
            )
        except requests.exceptions.RequestException as e:
            raise BeatportClientError(f"Authentication failed: {e}") from e

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """
        Makes a request to the Beatport API.

        Handles token refresh on 401 Unauthorized error by re-authenticating
        and retrying the request once.

        Args:
            method: HTTP method (e.g., 'GET', 'POST').
            endpoint: API endpoint path (e.g., 'catalog/search/').
            **kwargs: Additional arguments for the request (e.g., params, json).

        Returns:
            The JSON response from the API as a dictionary.

        Raises:
            BeatportClientError: If the API request fails after potential retry.
        """
        url = urljoin(self._BASE_API_URL, endpoint)

        try:
            response = self.session.request(method, url, **kwargs)

            if response.status_code == 401:
                # Token might have expired, re-authenticate and retry once.
                self._authenticate()
                response = self.session.request(method, url, **kwargs)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_message = (
                f"HTTP Error: {e.response.status_code} for URL: {e.response.url}"
            )
            try:
                # Try to get more detailed error from Beatport's response
                error_detail = e.response.json().get("detail", e.response.text)
                error_message += f"\nDetail: {error_detail}"
            except requests.exceptions.JSONDecodeError:
                error_message += f"\nResponse body: {e.response.text}"
            raise BeatportClientError(error_message) from e
        except requests.exceptions.RequestException as e:
            raise BeatportClientError(
                f"An error occurred during the request: {e}"
            ) from e

    # --- Public API Methods ---

    def search(
        self, q: str, search_type: str = "track", page: int = 1, per_page: int = 50
    ) -> dict[str, Any]:
        """
        Search for items on Beatport.

        Args:
            q: The search query.
            search_type: The type of item to search for.
                         Valid types: 'track', 'release', 'artist', 'label', 'chart'.
            page: The page number of the results.
            per_page: The number of results per page (max 150).

        Returns:
            A dictionary containing the search results.
        """
        params = {"q": q, "type": search_type, "page": page, "per_page": per_page}
        return self._request("GET", "catalog/search/", params=params)

    def get_track(self, track_id: int) -> dict[str, Any]:
        """
        Get details for a specific track.

        Args:
            track_id: The ID of the track.

        Returns:
            A dictionary containing the track details.
        """
        return self._request("GET", f"catalog/tracks/{track_id}/")

    def get_release(self, release_id: int) -> dict[str, Any]:
        """
        Get details for a specific release.

        Args:
            release_id: The ID of the release.

        Returns:
            A dictionary containing the release details.
        """
        return self._request("GET", f"catalog/releases/{release_id}/")

    def get_artist(self, artist_id: int) -> dict[str, Any]:
        """
        Get details for a specific artist.

        Args:
            artist_id: The ID of the artist.

        Returns:
            A dictionary containing the artist details.
        """
        return self._request("GET", f"catalog/artists/{artist_id}/")

    def get_label(self, label_id: int) -> dict[str, Any]:
        """
        Get details for a specific label.

        Args:
            label_id: The ID of the label.

        Returns:
            A dictionary containing the label details.
        """
        return self._request("GET", f"catalog/labels/{label_id}/")

    def get_genres(self) -> dict[str, Any]:
        """
        Get a list of available genres.

        Returns:
            A dictionary containing the list of genres.
        """

        return self._request("GET", "catalog/genres/")

    def get_genre(self, genre_id: int) -> dict[str, Any]:
        return self._request("GET", f"catalog/genres/{genre_id}/")

    def get_genre_topN(self, genre_id: int, num: int = 100) -> dict[str, Any]:
        return self._request("GET", f"catalog/genres/{genre_id}/top/{num}")

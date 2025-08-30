import json
import os

from beatport2youtube.api.beatport import BeatportClient, BeatportClientError


def main():
    """Example usage of the BeatportClient."""
    # It's recommended to use environment variables for credentials.
    client_id = os.environ.get("BEATPORT_CLIENT_ID") or "dummy"
    client_secret = os.environ.get("BEATPORT_CLIENT_SECRET") or "dummy"

    if not client_id or not client_secret:
        print(
            "Error: Please set BEATPORT_CLIENT_ID and BEATPORT_CLIENT_SECRET environment variables."
        )
        return

    try:
        client = BeatportClient(client_id=client_id, client_secret=client_secret)

        # 13 is psytrance
        print(json.dumps(client.get_genre_topN(13, 100)))

    except (ValueError, BeatportClientError) as e:
        print(f"\nAn error occurred: {e}")


if __name__ == "__main__":
    main()

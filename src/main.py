import json
import os
import time

from beatport2youtube.api.beatport import BeatportClient, BeatportClientError
from beatport2youtube.api.youtube import YouTubeClient


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


def get_search_query(beatport_result):
    """Construct a search string for YouTube based on Beatport results."""
    search_string = f"{beatport_result['name']} {beatport_result['isrc']}"

    return search_string


def main2():
    """Example usage of the YouTubeClient."""
    api_key = os.environ.get("YOUTUBE_API_KEY") or "dummy"
    if not api_key:
        print("Error: Please set YOUTUBE_API_KEY environment variable.")
        return

    client = YouTubeClient(api_key=api_key)

    beatport_results = json.load(open("202508301426JST.json"))["results"]

    for result in beatport_results:
        query = get_search_query(result)
        print(f"Search query for YouTube: {query}")

        # Search for videos related to a specific query
        videos = client.search_videos(query, max_results=1)
        time.sleep(1)

        video = videos[0] if videos else None
        if video:
            print(
                f"Found video: {video['snippet']['title']} ({video['id']['videoId']})"
            )
        else:
            print("No video found.")


if __name__ == "__main__":
    main2()

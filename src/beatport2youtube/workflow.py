import datetime
import os
import time

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


from beatport2youtube.api.beatport import BeatportClient
from beatport2youtube.api.youtube import YouTubeClient
from beatport2youtube.utils import get_search_query

# psytrance
BEATPORT_GENRE_ID = 13

beatport_results = []


def step1():
    print("Step 1: Download recent top 100 tracks from Beatport")
    client_id = os.environ.get("BEATPORT_CLIENT_ID") or "dummy"
    client_secret = os.environ.get("BEATPORT_CLIENT_SECRET") or "dummy"
    client = BeatportClient(client_id=client_id, client_secret=client_secret)
    res = client.get_genre_topN(BEATPORT_GENRE_ID)
    global beatport_results
    beatport_results = res["results"]
    print("Step 1 completed")


def step2():
    print("Step 2: Clean youtube playlist and update comment")
    # When running locally, disable OAuthlib's HTTPs verification. When
    # running in production *do not* leave this option enabled.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secrets.json",
        scopes=["https://www.googleapis.com/auth/youtube"],
    )

    flow.run_local_server()

    credentials = flow.credentials

    with build("youtube", "v3", credentials=credentials) as youtube_service:
        # Get the playlist ID from the environment variable
        playlist_id = os.environ.get("YOUTUBE_PLAYLIST_ID") or "dummy"

        # Get the playlist items
        playlist_items = (
            youtube_service.playlistItems()
            .list(part="snippet", playlistId=playlist_id)
            .execute()
        )

        print(f"Found {len(playlist_items['items'])} items in the playlist.")

        # Delete current playlist items
        for item in playlist_items["items"]:
            youtube_service.playlistItems().delete(id=item["id"]).execute()

        # Update playlist description
        current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        youtube_service.playlists().update(
            part="snippet",
            body={
                "id": playlist_id,
                "snippet": {
                    "title": "Psy-Trance BeatportTop100",
                    "description": f"A curated playlist of the top 100 psytrance tracks on Beatport. last updated on {current_time}.",
                },
            },
        ).execute()

        # Initialize YouTube client for video search
        api_key = os.environ.get("YOUTUBE_API_KEY") or "dummy"
        youtube_client = YouTubeClient(api_key=api_key)

        for result in beatport_results:
            query = get_search_query(result)
            print(f"Search query for YouTube: {query}")

            # Search for videos related to a specific query
            videos = youtube_client.search_videos(query, max_results=1)
            time.sleep(3)

            video = videos[0] if videos else None
            if video:
                print(
                    f"Found video: {video['snippet']['title']} ({video['id']['videoId']})"
                )

                # Add video to playlist
                youtube_service.playlistItems().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "playlistId": playlist_id,
                            "resourceId": video["id"],
                        }
                    },
                ).execute()
            else:
                print("No video found.")

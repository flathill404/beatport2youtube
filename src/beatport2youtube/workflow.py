import datetime
import os
import re
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


def _get_beatport_id_from_note(note: str) -> str | None:
    if not note:
        return None
    match = re.search(r"beatport_track_id:(\d+)", note)
    if match:
        return match.group(1)
    return None


def step2():
    print("Step 2: Sync youtube playlist with Beatport Top 100")
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

        # 1. Get existing items from YouTube playlist
        print("Fetching existing items from YouTube playlist...")
        existing_items = {}  # {beatport_id: playlist_item_id}
        next_page_token = None
        while True:
            request = youtube_service.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token,
            )
            response = request.execute()

            for item in response["items"]:
                note = item.get("contentDetails", {}).get("note")
                beatport_id = _get_beatport_id_from_note(note)
                if beatport_id:
                    existing_items[beatport_id] = item["id"]

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
        print(f"Found {len(existing_items)} items with Beatport IDs in the playlist.")

        # 2. Get new track IDs from Beatport
        new_beatport_ids = {str(track["id"]) for track in beatport_results}

        # 3. Compare and find diffs
        existing_beatport_ids = set(existing_items.keys())
        ids_to_add = new_beatport_ids - existing_beatport_ids
        ids_to_remove = existing_beatport_ids - new_beatport_ids

        print(f"Tracks to add: {len(ids_to_add)}, Tracks to remove: {len(ids_to_remove)}")

        # 4. Remove old items
        if ids_to_remove:
            print(f"Removing {len(ids_to_remove)} tracks...")
            for beatport_id in ids_to_remove:
                playlist_item_id = existing_items[beatport_id]
                try:
                    youtube_service.playlistItems().delete(id=playlist_item_id).execute()
                    print(f"Removed track (Beatport ID: {beatport_id})")
                    time.sleep(1)  # Be nice to the API
                except Exception as e:
                    print(f"Failed to remove track (Beatport ID: {beatport_id}): {e}")

        # 5. Add new items
        if ids_to_add:
            print(f"Adding {len(ids_to_add)} new tracks...")
            tracks_to_add = [
                track for track in beatport_results if str(track["id"]) in ids_to_add
            ]

            api_key = os.environ.get("YOUTUBE_API_KEY") or "dummy"
            youtube_client = YouTubeClient(api_key=api_key)

            for result in tracks_to_add:
                query = get_search_query(result)
                print(f"Searching YouTube for: {query}")

                videos = youtube_client.search_videos(query, max_results=1)
                time.sleep(1)

                video = videos[0] if videos else None
                if video:
                    print(
                        f"Found video: {video['snippet']['title']} ({video['id']['videoId']})"
                    )
                    try:
                        youtube_service.playlistItems().insert(
                            part="snippet,contentDetails",
                            body={
                                "snippet": {
                                    "playlistId": playlist_id,
                                    "resourceId": video["id"],
                                },
                                "contentDetails": {
                                    "note": f"beatport_track_id:{result['id']}"
                                },
                            },
                        ).execute()
                        print(f"Added video for Beatport track {result['id']}")
                    except Exception as e:
                        print(f"Failed to add video for Beatport track {result['id']}: {e}")
                else:
                    print(f"No video found for query: {query}")

        # 6. Update playlist description
        print("Updating playlist description...")
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

        print("Step 2 completed")

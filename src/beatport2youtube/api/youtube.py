from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class YouTubeClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("YouTube API key must be provided.")
        self.youtube = build("youtube", "v3", developerKey=self.api_key)

    def search_videos(self, query: str, max_results: int = 5):
        try:
            request = self.youtube.search().list(
                q=query, part="id,snippet", maxResults=max_results, type="video"
            )
            response = request.execute()
            return response.get("items", [])
        except HttpError as e:
            print(f"An HTTP error occurred: {e}")
            return []

    def get_video_details(self, video_id: str):
        try:
            request = self.youtube.videos().list(
                part="snippet,contentDetails,statistics", id=video_id
            )
            response = request.execute()
            items = response.get("items", [])
            return items[0] if items else None
        except HttpError as e:
            print(f"An HTTP error occurred: {e}")

from datetime import datetime, timedelta
from typing import List
from googleapiclient.discovery import build
from ingest.base import BaseFetcher, RawPostData
from config import YOUTUBE_API_KEY, YOUTUBE_SEARCH_QUERIES

class YouTubeFetcher(BaseFetcher):
    def __init__(self):
        self._service = None

    def _get_service(self):
        if self._service is None:
            self._service = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        return self._service

    def _search_video_ids(self, query: str, max_results: int = 10) -> List[str]:
        since = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        response = (
            self._get_service()
            .search()
            .list(
                q=query,
                type="video",
                part="id",
                maxResults=max_results,
                publishedAfter=since,
                relevanceLanguage="ta",
                regionCode="IN",
            )
            .execute()
        )
        return [item["id"]["videoId"] for item in response.get("items", [])]

    def _fetch_comments(self, video_id: str, max_results: int = 100) -> List[RawPostData]:
        try:
            response = (
                self._get_service()
                .commentThreads()
                .list(videoId=video_id, part="snippet", maxResults=max_results, order="relevance")
                .execute()
            )
        except Exception:
            return []

        posts = []
        for item in response.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            posts.append(RawPostData(
                source="youtube",
                post_id=item["snippet"]["topLevelComment"]["id"],
                text=top["textOriginal"],
                url=f"https://youtube.com/watch?v={video_id}",
                author=top.get("authorDisplayName"),
                engagement=top.get("likeCount", 0),
                posted_at=datetime.fromisoformat(top["publishedAt"].replace("Z", "+00:00")).replace(tzinfo=None),
            ))
        return posts

    def fetch(self) -> List[RawPostData]:
        all_posts: List[RawPostData] = []
        seen_ids: set = set()
        for query in YOUTUBE_SEARCH_QUERIES:
            try:
                for video_id in self._search_video_ids(query):
                    if video_id not in seen_ids:
                        seen_ids.add(video_id)
                        all_posts.extend(self._fetch_comments(video_id))
            except Exception:
                continue
        return all_posts

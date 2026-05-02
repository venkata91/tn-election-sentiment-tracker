from datetime import datetime, timedelta
from typing import List, Optional
from googleapiclient.discovery import build
from ingest.base import BaseFetcher, RawPostData
from config import YOUTUBE_API_KEY, YOUTUBE_SEARCH_QUERIES, YOUTUBE_CHANNELS

_DAYS_BACK = 7
_SEARCH_MAX_RESULTS = 50
_COMMENTS_PER_PAGE = 100
_MAX_COMMENT_PAGES = 3


class YouTubeFetcher(BaseFetcher):
    def __init__(self):
        self._service = None

    def _get_service(self):
        if self._service is None:
            self._service = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        return self._service

    def _search_video_ids(self, query: str) -> List[str]:
        since = (datetime.utcnow() - timedelta(days=_DAYS_BACK)).strftime("%Y-%m-%dT%H:%M:%SZ")
        response = (
            self._get_service()
            .search()
            .list(
                q=query,
                type="video",
                part="id",
                maxResults=_SEARCH_MAX_RESULTS,
                publishedAfter=since,
                relevanceLanguage="ta",
                regionCode="IN",
            )
            .execute()
        )
        return [item["id"]["videoId"] for item in response.get("items", [])]

    def _channel_video_ids(self, channel_id: str) -> List[str]:
        """Fetch recent video IDs from a channel via uploads playlist (1 quota unit vs 100 for search)."""
        try:
            ch_response = (
                self._get_service()
                .channels()
                .list(id=channel_id, part="contentDetails")
                .execute()
            )
            items = ch_response.get("items", [])
            if not items:
                return []
            uploads_playlist = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
        except Exception:
            return []

        since = datetime.utcnow() - timedelta(days=_DAYS_BACK)
        video_ids: List[str] = []
        page_token: Optional[str] = None
        try:
            while True:
                kwargs = dict(playlistId=uploads_playlist, part="snippet", maxResults=50)
                if page_token:
                    kwargs["pageToken"] = page_token
                pl_response = self._get_service().playlistItems().list(**kwargs).execute()
                for item in pl_response.get("items", []):
                    published = item["snippet"].get("publishedAt", "")
                    if published:
                        pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00")).replace(tzinfo=None)
                        if pub_dt < since:
                            return video_ids
                    vid = item["snippet"].get("resourceId", {}).get("videoId")
                    if vid:
                        video_ids.append(vid)
                page_token = pl_response.get("nextPageToken")
                if not page_token:
                    break
        except Exception:
            pass
        return video_ids

    def _fetch_comments(self, video_id: str) -> List[RawPostData]:
        posts: List[RawPostData] = []
        page_token: Optional[str] = None
        pages_fetched = 0
        try:
            while pages_fetched < _MAX_COMMENT_PAGES:
                kwargs = dict(
                    videoId=video_id,
                    part="snippet",
                    maxResults=_COMMENTS_PER_PAGE,
                    order="relevance",
                )
                if page_token:
                    kwargs["pageToken"] = page_token
                response = self._get_service().commentThreads().list(**kwargs).execute()
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
                pages_fetched += 1
                page_token = response.get("nextPageToken")
                if not page_token:
                    break
        except Exception:
            pass
        return posts

    def fetch(self) -> List[RawPostData]:
        all_posts: List[RawPostData] = []
        seen_video_ids: set = set()

        for query in YOUTUBE_SEARCH_QUERIES:
            try:
                for video_id in self._search_video_ids(query):
                    if video_id not in seen_video_ids:
                        seen_video_ids.add(video_id)
                        all_posts.extend(self._fetch_comments(video_id))
            except Exception:
                continue

        for channel_id in YOUTUBE_CHANNELS.values():
            try:
                for video_id in self._channel_video_ids(channel_id):
                    if video_id not in seen_video_ids:
                        seen_video_ids.add(video_id)
                        all_posts.extend(self._fetch_comments(video_id))
            except Exception:
                continue

        return all_posts

from datetime import datetime
from typing import List
import praw
from ingest.base import BaseFetcher, RawPostData
from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, REDDIT_SUBREDDITS, REDDIT_SEARCH_TERMS

class RedditFetcher(BaseFetcher):
    def __init__(self):
        self._reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )

    def fetch(self) -> List[RawPostData]:
        posts: List[RawPostData] = []
        for sub_name in REDDIT_SUBREDDITS:
            sub = self._reddit.subreddit(sub_name)
            for term in REDDIT_SEARCH_TERMS:
                try:
                    for submission in sub.search(term, time_filter="week", limit=20):
                        post_text = f"{submission.title}\n{submission.selftext}".strip()
                        if len(post_text) > 20:
                            posts.append(RawPostData(
                                source="reddit",
                                post_id=f"post_{submission.id}",
                                text=post_text,
                                url=f"https://reddit.com{submission.permalink}",
                                author=str(submission.author) if submission.author else None,
                                engagement=submission.score,
                                posted_at=datetime.utcfromtimestamp(submission.created_utc),
                            ))
                        submission.comments.replace_more(limit=0)
                        for comment in submission.comments.list()[:15]:
                            if len(comment.body) > 20:
                                posts.append(RawPostData(
                                    source="reddit",
                                    post_id=f"comment_{comment.id}",
                                    text=comment.body,
                                    url=f"https://reddit.com{submission.permalink}",
                                    author=str(comment.author) if comment.author else None,
                                    engagement=comment.score,
                                    posted_at=datetime.utcfromtimestamp(comment.created_utc),
                                ))
                except Exception:
                    continue
        return posts

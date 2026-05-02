import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from telethon import TelegramClient
from ingest.base import BaseFetcher, RawPostData
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_CHANNELS

log = logging.getLogger(__name__)

_DAYS_BACK = 7
_MSG_LIMIT = 500


class TelegramFetcher(BaseFetcher):
    def fetch(self) -> List[RawPostData]:
        return asyncio.run(self._async_fetch())

    async def _async_fetch(self) -> List[RawPostData]:
        posts: List[RawPostData] = []
        cutoff = datetime.utcnow() - timedelta(days=_DAYS_BACK)
        async with TelegramClient("elections_session", TELEGRAM_API_ID, TELEGRAM_API_HASH) as client:
            for channel in TELEGRAM_CHANNELS:
                channel_posts = 0
                try:
                    async for message in client.iter_messages(channel, limit=_MSG_LIMIT):
                        if not message.date:
                            continue
                        msg_time = message.date.replace(tzinfo=None)
                        if msg_time < cutoff:
                            break
                        if message.text and len(message.text) > 20:
                            posts.append(RawPostData(
                                source="telegram",
                                post_id=f"{channel}_{message.id}",
                                text=message.text,
                                url=f"https://t.me/{channel}/{message.id}",
                                engagement=getattr(message, "views", 0) or 0,
                                posted_at=msg_time,
                            ))
                            channel_posts += 1
                    log.info(f"Telegram {channel}: {channel_posts} posts")
                except Exception as e:
                    log.warning(f"Telegram {channel} failed: {e}")
                    continue
        return posts

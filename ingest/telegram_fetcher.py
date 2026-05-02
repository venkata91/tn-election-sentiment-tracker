import asyncio
from datetime import datetime, timedelta
from typing import List
from telethon import TelegramClient
from ingest.base import BaseFetcher, RawPostData
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_CHANNELS

class TelegramFetcher(BaseFetcher):
    def fetch(self) -> List[RawPostData]:
        return asyncio.run(self._async_fetch())

    async def _async_fetch(self) -> List[RawPostData]:
        posts: List[RawPostData] = []
        cutoff = datetime.utcnow() - timedelta(hours=24)
        async with TelegramClient("elections_session", TELEGRAM_API_ID, TELEGRAM_API_HASH) as client:
            for channel in TELEGRAM_CHANNELS:
                try:
                    async for message in client.iter_messages(channel, limit=200):
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
                except Exception:
                    continue
        return posts

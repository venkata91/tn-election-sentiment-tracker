from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class RawPostData:
    source: str
    post_id: str
    text: str
    url: Optional[str] = None
    lang: Optional[str] = None
    author: Optional[str] = None
    engagement: int = 0
    posted_at: Optional[datetime] = None

class BaseFetcher(ABC):
    @abstractmethod
    def fetch(self) -> List[RawPostData]:
        """Fetch posts and return as RawPostData list."""
        ...

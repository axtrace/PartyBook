from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class ReadingSession:
    """Represents a user's reading session for a specific book."""
    user_id: int
    book_id: int
    pos: int = 0
    updated_at: Optional[datetime] = None

    def touch(self) -> None:
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "userId": self.user_id,
            "bookId": self.book_id,
            "pos": self.pos,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


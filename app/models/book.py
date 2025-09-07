# app/models/book.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Book:
    id: int
    name: str
    pos: int
    mode: Optional[str] = None

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "pos": self.pos, "mode": self.mode}
        
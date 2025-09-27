# app/models/__init__.py
"""
Модели данных
Определяют структуру данных для пользователей, книг и сессий чтения
"""

from .user import User
from .book import Book
from .reading_session import ReadingSession

__all__ = ['User', 'Book', 'ReadingSession']
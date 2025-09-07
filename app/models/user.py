"""
Модель пользователя
Представляет пользователя Telegram бота для чтения книг
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class User:
    """
    Модель пользователя системы
    
    Атрибуты:
        id (int): Уникальный идентификатор записи в БД
        user_id (int): ID пользователя в Telegram
        chat_id (int): ID чата в Telegram
        is_auto_send (bool): Включена ли автоматическая отправка книг
        lang (str): Язык интерфейса пользователя ('ru', 'en')
        time (str): Время для автоматической отправки (формат HH:MM)
    """
    
    id: Optional[int] = None
    user_id: int = 0
    chat_id: int = 0
    is_auto_send: bool = False
    lang: str = "ru"
    time: str = ""
    
    def __post_init__(self):
        """Валидация данных после инициализации"""
        if self.user_id <= 0:
            raise ValueError("user_id должен быть положительным числом")
        
        if self.chat_id <= 0:
            raise ValueError("chat_id должен быть положительным числом")
        
        if self.lang not in ["ru", "en"]:
            raise ValueError("lang должен быть 'ru' или 'en'")
        
        if self.time and not self._is_valid_time_format(self.time):
            raise ValueError("time должен быть в формате HH:MM или пустой строкой")
    
    def _is_valid_time_format(self, time_str: str) -> bool:
        """Проверяет корректность формата времени"""
        if not time_str:
            return True
        
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False
    
    def set_auto_send_time(self, time_str: str) -> None:
        """
        Устанавливает время для автоматической отправки
        
        Args:
            time_str (str): Время в формате HH:MM
        """
        if not self._is_valid_time_format(time_str):
            raise ValueError("Время должно быть в формате HH:MM")
        
        self.time = time_str
    
    def enable_auto_send(self) -> None:
        """Включает автоматическую отправку"""
        self.is_auto_send = True
    
    def disable_auto_send(self) -> None:
        """Отключает автоматическую отправку"""
        self.is_auto_send = False
    
    def switch_language(self) -> None:
        """Переключает язык интерфейса"""
        self.lang = "en" if self.lang == "ru" else "ru"
    
    def to_dict(self) -> dict:
        """
        Преобразует объект в словарь для сохранения в БД
        
        Returns:
            dict: Словарь с данными пользователя
        """
        return {
            "id": self.id,
            "userId": self.user_id,
            "chatId": self.chat_id,
            "isAutoSend": self.is_auto_send,
            "lang": self.lang,
            "time": self.time
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """
        Создает объект User из словаря данных БД
        
        Args:
            data (dict): Данные из БД
            
        Returns:
            User: Объект пользователя
        """
        return cls(
            id=data.get("id"),
            user_id=data.get("userId", 0),
            chat_id=data.get("chatId", 0),
            is_auto_send=data.get("isAutoSend", False),
            lang=data.get("lang", "ru"),
            time=data.get("time", "")
        )
    
    @classmethod
    def create_new(cls, user_id: int, chat_id: int, lang: str = "ru") -> 'User':
        """
        Создает нового пользователя
        
        Args:
            user_id (int): ID пользователя в Telegram
            chat_id (int): ID чата в Telegram
            lang (str): Язык интерфейса
            
        Returns:
            User: Новый объект пользователя
        """
        return cls(
            user_id=user_id,
            chat_id=chat_id,
            lang=lang,
            is_auto_send=False,
            time=""
        )
    
    def __str__(self) -> str:
        """Строковое представление пользователя"""
        return f"User(id={self.id}, user_id={self.user_id}, chat_id={self.chat_id}, lang={self.lang}, auto_send={self.is_auto_send})"
    
    def __repr__(self) -> str:
        """Представление для отладки"""
        return self.__str__()

import re
import json

def _text_to_json(self, text):
    """Надежный парсер для текста из YDB с исправлением кавычек"""
    if not isinstance(text, str):
        return text
    
    # Исправляем проблемные кавычки в значениях
    def fix_quotes_in_value(match):
        key = match.group(1)
        value = match.group(2)
        # Экранируем все кавычки в значении, кроме первой и последней
        if len(value) > 2:
            inner_value = value[1:-1]  # Убираем внешние кавычки
            inner_value = inner_value.replace('"', '\\"')  # Экранируем внутренние кавычки
            return f'"{key}": "{inner_value}"'
        return match.group(0)
    
    # Паттерн для поиска строковых значений с кавычками внутри
    pattern = r'"([^"]+)":\s*"([^"]*"[^"]*)"'
    
    # Применяем исправление кавычек
    text = re.sub(pattern, fix_quotes_in_value, text)
    
    # Обрабатываем остальные замены
    text = text.replace("'", '"')
    text = text.replace('True', 'true')
    text = text.replace('False', 'false')
    text = text.replace('None', 'null')
    text = text.replace('\n', '')
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Problematic text: {text}")
        return None

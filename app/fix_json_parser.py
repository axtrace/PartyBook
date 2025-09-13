import re
import json

def fix_json_parsing(text):
    """Исправляет JSON с неэкранированными кавычками в значениях"""
    if not isinstance(text, str):
        return text
    
    # Сначала экранируем кавычки внутри значений
    # Ищем паттерн: "ключ": "значение с кавычками"
    def escape_quotes_in_values(match):
        key = match.group(1)
        value = match.group(2)
        # Экранируем кавычки в значении
        escaped_value = value.replace('"', '\\"')
        return f'"{key}": "{escaped_value}"'
    
    # Паттерн для поиска ключ-значение пар
    pattern = r'"([^"]+)":\s*"([^"]*(?:"[^"]*)*[^"]*)"'
    
    # Применяем экранирование
    text = re.sub(pattern, escape_quotes_in_values, text)
    
    # Обрабатываем остальные замены
    text_dict = {
        "'": '"',
        'b"': '"',
        '\n': '',
        'False': 'false',
        'True': 'true'
    }
    
    for old, new in text_dict.items():
        text = text.replace(old, new)
    
    # Обрабатываем ключи с точками
    re_dict = {r'([a-zA-Z_][a-zA-Z0-9_.]*):': r'"\1":'}
    for pattern, replacement in re_dict.items():
        text = re.sub(pattern, replacement, text)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Problematic text: {text}")
        return None

# Тестируем
test_text = '{"ub.bookId": 1, "b.bookName": "35846529_emotsional"nyj_intellekt_rebenka.txt", "ub.pos": 2, "ub.mode": "bm9ybWFs"}'
print("Original:", test_text)
result = fix_json_parsing(test_text)
print("Result:", result)

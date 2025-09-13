import ast
import json

def simple_text_to_json(text):
    """Простой парсер для текста из YDB"""
    if not isinstance(text, str):
        return text
    
    try:
        # Пытаемся использовать ast.literal_eval для безопасного парсинга
        # Сначала заменяем одинарные кавычки на двойные
        text = text.replace("'", '"')
        
        # Заменяем Python-стиль на JSON-стиль
        text = text.replace('True', 'true')
        text = text.replace('False', 'false')
        text = text.replace('None', 'null')
        
        # Убираем переносы строк
        text = text.replace('\n', '')
        
        # Пытаемся распарсить как JSON
        return json.loads(text)
        
    except (json.JSONDecodeError, ValueError) as e:
        print(f"JSON parsing failed: {e}")
        print(f"Text: {text}")
        
        # Fallback: пытаемся использовать ast.literal_eval
        try:
            # Заменяем обратно для ast.literal_eval
            text = text.replace('true', 'True')
            text = text.replace('false', 'False')
            text = text.replace('null', 'None')
            text = text.replace('"', "'")
            
            return ast.literal_eval(text)
        except Exception as e2:
            print(f"ast.literal_eval also failed: {e2}")
            return None

# Тестируем
test_text = '{"ub.bookId": 1, "b.bookName": "35846529_emotsional"nyj_intellekt_rebenka.txt", "ub.pos": 2, "ub.mode": "bm9ybWFs"}'
print("Original:", test_text)
result = simple_text_to_json(test_text)
print("Result:", result)

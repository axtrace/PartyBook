import json
import re

def analyze_problematic_chars():
    """Анализ символов, которые могут сломать JSON парсинг"""
    
    # Проблемные символы в контексте YDB и текстовых данных
    problematic_chars = {
        'quotes': ['"', "'", '`', '«', '»', '"', '"', ''', '''],
        'backslashes': ['\\', '\\\\'],
        'newlines': ['\n', '\r', '\r\n'],
        'tabs': ['\t'],
        'control_chars': ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', 
                         '\x08', '\x0b', '\x0c', '\x0e', '\x0f', '\x10', '\x11', '\x12', 
                         '\x13', '\x14', '\x15', '\x16', '\x17', '\x18', '\x19', '\x1a', 
                         '\x1b', '\x1c', '\x1d', '\x1e', '\x1f'],
        'unicode_quotes': ['\u201c', '\u201d', '\u2018', '\u2019', '\u201a', '\u201b', 
                          '\u201e', '\u201f', '\u2039', '\u203a'],
        'special_chars': ['{', '}', '[', ']', ',', ':', ';', '|', '&', '%', '#', '@', '$', '^', '*', '+', '=', '~', '`']
    }
    
    print("=== Анализ проблемных символов для JSON парсинга ===\n")
    
    for category, chars in problematic_chars.items():
        print(f"**{category.upper()}:**")
        for char in chars:
            # Тестируем каждый символ
            test_value = f"test{char}value"
            test_json = f'{{"key": "{test_value}"}}'
            
            try:
                json.loads(test_json)
                status = "✅ OK"
            except json.JSONDecodeError as e:
                status = f"❌ ERROR: {str(e)[:50]}..."
            
            print(f"  '{char}' (\\x{ord(char):02x}) -> {status}")
        print()
    
    # Тестируем реальные примеры из ваших данных
    print("=== Тестирование реальных примеров ===\n")
    
    real_examples = [
        '{"ub.bookId": 1, "b.bookName": "35846529_emotsional"nyj_intellekt_rebenka.txt", "ub.pos": 2}',
        '{"ub.bookId": 1, "b.bookName": "book with \'single quotes\'", "ub.pos": 2}',
        '{"ub.bookId": 1, "b.bookName": "book with \\"escaped quotes\\"", "ub.pos": 2}',
        '{"ub.bookId": 1, "b.bookName": "book with \\n newlines", "ub.pos": 2}',
        '{"ub.bookId": 1, "b.bookName": "book with \\t tabs", "ub.pos": 2}',
        '{"ub.bookId": 1, "b.bookName": "book with {brackets}", "ub.pos": 2}',
        '{"ub.bookId": 1, "b.bookName": "book with [square] brackets", "ub.pos": 2}',
        '{"ub.bookId": 1, "b.bookName": "book with unicode "quotes"", "ub.pos": 2}',
    ]
    
    for i, example in enumerate(real_examples, 1):
        print(f"Пример {i}: {example[:60]}...")
        try:
            result = json.loads(example)
            print(f"  ✅ OK: {result}")
        except json.JSONDecodeError as e:
            print(f"  ❌ ERROR: {e}")
        print()

if __name__ == "__main__":
    analyze_problematic_chars()

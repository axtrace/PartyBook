#!/usr/bin/env python3
"""
Тестовый скрипт для проверки создания чанков по предложениям
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from text_separator import TextSeparator

def test_sentence_separation():
    """Тестируем разбивку текста на предложения"""
    
    # Тестовый текст
    test_text = """
    Это первое предложение. Это второе предложение! А это третье предложение?
    Четвертое предложение тоже важно. Пятое предложение завершает первую группу.
    Шестое предложение начинается новую группу. Седьмое предложение продолжает мысль.
    Восьмое предложение развивает тему. Девятое предложение добавляет детали.
    Десятое предложение завершает вторую группу.
    """
    
    print("🧪 Тестируем разбивку текста на предложения")
    print("=" * 60)
    print(f"📝 Исходный текст:\n{test_text}")
    print("=" * 60)
    
    # Тестируем TextSeparator
    separator = TextSeparator(test_text, mode='by_sense')
    sentences = separator.get_sentences()
    
    print(f"📊 Получено {len(sentences)} предложений:")
    for i, sentence in enumerate(sentences, 1):
        print(f"{i:02d}: {sentence}")
    
    print("=" * 60)
    
    # Тестируем создание чанков по 5 предложений
    sentences_per_chunk = 5
    chunks = []
    
    for i in range(0, len(sentences), sentences_per_chunk):
        chunk_sentences = sentences[i:i + sentences_per_chunk]
        chunk_text = ' '.join(chunk_sentences)
        chunks.append({
            'sentences': chunk_sentences,
            'text': chunk_text,
            'length': len(chunk_text)
        })
    
    print(f"📚 Создано {len(chunks)} чанков по {sentences_per_chunk} предложений:")
    for i, chunk in enumerate(chunks, 1):
        print(f"\n📄 ЧАНК #{i}")
        print(f"📊 Длина: {chunk['length']} символов")
        print(f"📝 Предложений: {len(chunk['sentences'])}")
        print(f"📖 Текст: {chunk['text']}")
        print("-" * 40)

def test_epub_reading():
    """Тестируем чтение EPUB файла"""
    epub_path = "/Users/matvey/Documents/books/Martyinenko_S._Bayiki_Dlya_Orujenosca.epub"
    
    if not os.path.exists(epub_path):
        print(f"❌ Файл не найден: {epub_path}")
        return
    
    print("\n🧪 Тестируем чтение EPUB файла")
    print("=" * 60)
    
    try:
        import warnings
        from bs4 import BeautifulSoup as bs, XMLParsedAsHTMLWarning
        import ebooklib
        from ebooklib import epub
        
        warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
        
        # Загружаем EPUB
        book = epub.read_epub(epub_path)
        print(f"📚 Книга: {book.title}")
        
        # Получаем элементы
        item_ids = []
        doc_item_list = book.get_items_of_type(ebooklib.ITEM_DOCUMENT)
        for elem in doc_item_list:
            item_ids.append(elem.id)
        
        print(f"📋 Найдено {len(item_ids)} элементов")
        
        # Обрабатываем первые 3 элемента
        for i, item_id in enumerate(item_ids[:3]):
            print(f"\n📖 Элемент {i+1}: {item_id}")
            
            try:
                item_doc = book.get_item_with_id(item_id)
                if item_doc is None:
                    print(f"⚠️ Элемент не найден")
                    continue
                
                soup = bs(item_doc.content.decode('utf-8'), "xml")
                if soup.body:
                    text = soup.body.get_text()
                else:
                    text = soup.get_text()
                
                text = ' '.join(text.split())
                
                if text.strip():
                    print(f"📄 Длина текста: {len(text)} символов")
                    print(f"📝 Превью: {text[:200]}...")
                    
                    # Тестируем разбивку на предложения
                    separator = TextSeparator(text, mode='by_sense')
                    sentences = separator.get_sentences()
                    print(f"📊 Получено {len(sentences)} предложений")
                    
                    # Показываем первые 5 предложений
                    for j, sentence in enumerate(sentences[:5], 1):
                        print(f"  {j}: {sentence[:100]}{'...' if len(sentence) > 100 else ''}")
                    
                    if len(sentences) > 5:
                        print(f"  ... и еще {len(sentences) - 5} предложений")
                else:
                    print("⚠️ Пустой текст")
                    
            except Exception as e:
                print(f"❌ Ошибка: {e}")
    
    except Exception as e:
        print(f"❌ Ошибка загрузки EPUB: {e}")

def main():
    """Основная функция"""
    print("🚀 Тестирование создания чанков по предложениям")
    print("=" * 60)
    
    # Тест 1: Разбивка на предложения
    test_sentence_separation()
    
    # Тест 2: Чтение EPUB
    test_epub_reading()
    
    print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    main()

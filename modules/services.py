# 建議檔名: modules/services.py

import uuid
from datetime import date
from typing import List, Optional
from .models import Book, BookStatus
from . import database
from . import scraper
from . import ai_agent

def add_book(url: str) -> Optional[Book]:
    """
    核心功能：從網址新增書籍
    """
    print(f"🚀 開始處理書籍：{url}")
    raw_data = scraper.scrape_book(url)
    
    if not raw_data:
        print(f"❌ 爬蟲失敗，無法新增書籍")
        return None

    ai_result = ai_agent.analyze_book(raw_data)
    
    tags = []
    ai_summary = "AI 尚未分析"
    ai_plot = "AI 尚未分析"
    
    if ai_result:
        tags = ai_result.tags
        ai_summary = ai_result.summary
        ai_plot = ai_result.plot
    
    book_id = str(uuid.uuid4())
    
    # // 【關鍵修正點】 建立 Book 物件時，移除 word_count 與 chapters 參數
    new_book = Book(
        id=book_id,
        title=raw_data.title,
        author=raw_data.author,
        source=raw_data.source_name,
        url=url,
        status=BookStatus.UNREAD,
        tags=tags,
        ai_summary=ai_summary,
        official_desc=raw_data.description,
        ai_plot_analysis=ai_plot,
        added_date=date.today(),
        user_rating=0
    )
    
    try:
        database.insert_book(new_book)
        print(f"✅ 書籍已存入資料庫：{new_book.title}")
        return new_book
    except Exception as e:
        print(f"❌ 資料庫寫入失敗: {e}")
        return None

def get_books() -> List[Book]:
    """取得所有書籍"""
    return database.get_all_books()

def update_book_status(book: Book, new_status: BookStatus) -> Book:
    """更新狀態"""
    book.status = new_status
    if new_status == BookStatus.COMPLETED and not book.completed_date:
        book.completed_date = date.today()
    database.update_book(book)
    return book

def save_book_changes(book: Book):
    """儲存書籍變更"""
    database.update_book(book)

def remove_book(book_id: str):
    """移除書籍"""
    database.delete_book(book_id)

# // 功能: 業務邏輯層 (同步移除字數欄位)
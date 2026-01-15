# 修正 [modules/services.py] 區塊 A: 整合爬蟲與 AI 實作真實入庫
# 修正原因：移除 Mock Data，串接 Scraper 與 AI Agent 實現自動化書籍建立。
# 替換/新增指示：請完全取代原有的 modules/services.py。

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
    流程：爬蟲 -> AI 分析 -> 建立物件 -> 存入 DB
    """
    # 1. 執行爬蟲
    print(f"🚀 開始處理書籍：{url}")
    raw_data = scraper.scrape_book(url)
    
    if not raw_data:
        print(f"❌ 爬蟲失敗，無法新增書籍")
        return None

    # 2. 執行 AI 分析 (容錯處理：如果 AI 失敗，還是可以建立書籍，只是沒分析資料)
    ai_result = ai_agent.analyze_book(raw_data)
    
    # 準備欄位資料
    tags = []
    ai_summary = "AI 尚未分析"
    ai_plot = "AI 尚未分析"
    
    if ai_result:
        tags = ai_result.tags
        ai_summary = ai_result.summary
        ai_plot = ai_result.plot
    
    # 3. 建立 Book 物件
    book_id = str(uuid.uuid4())
    
    new_book = Book(
        id=book_id,
        title=raw_data.title,
        author=raw_data.author,
        source=raw_data.source_name,
        url=url,
        word_count="未知", # 部分網站沒抓字數，暫時留空
        chapters="未知",
        status=BookStatus.UNREAD,
        tags=tags,
        ai_summary=ai_summary,
        official_desc=raw_data.description,
        ai_plot_analysis=ai_plot,
        added_date=date.today(),
        user_rating=0
    )
    
    # 4. 寫入資料庫
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
    """更新狀態，並自動處理完食日期"""
    book.status = new_status
    if new_status == BookStatus.COMPLETED and not book.completed_date:
        book.completed_date = date.today()
    database.update_book(book)
    return book

def save_book_changes(book: Book):
    """儲存書籍的任何變更 (評分、心得等)"""
    database.update_book(book)

def remove_book(book_id: str):
    """移除書籍"""
    database.delete_book(book_id)

# // 功能: 業務邏輯層 (真實版)
# // input: URL
# // output: 整合爬蟲與 AI 後的 Book 物件
# // 其他補充: 已移除所有 Mock Data 相關程式碼
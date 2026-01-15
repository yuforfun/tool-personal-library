import uuid
import random
from datetime import date
from typing import List
from .models import Book, BookStatus
from . import database

# 模擬資料來源
MOCK_TITLES = ["重生之豪門千金", "星際種田日常", "無限流：生存遊戲", "某某修仙傳", "霸道總裁愛上我"]
MOCK_AUTHORS = ["晉江一姐", "半夏微涼", "吃瓜路人", "天蠶土豆絲", "顧漫漫"]
MOCK_SOURCES = ["晉江", "半夏", "小說狂人"]
MOCK_TAGS = ["重生", "甜文", "爽文", "HE", "強強", "星際", "系統"]

def create_mock_book(url: str) -> Book:
    """生成一本模擬書籍資料 (Phase 2 測試用)"""
    book_id = str(uuid.uuid4())
    # 【關鍵修正點】 移除書名後面的 ID 後綴，保持介面乾淨
    title = random.choice(MOCK_TITLES) 
    
    # 隨機生成 3-5 個標籤
    tags = random.sample(MOCK_TAGS, k=random.randint(3, 5))
    
    new_book = Book(
        id=book_id,
        title=title,
        author=random.choice(MOCK_AUTHORS),
        source=random.choice(MOCK_SOURCES),
        url=url,
        word_count=f"{random.randint(20, 300)}萬字",
        chapters=f"{random.randint(50, 500)}章",
        status=BookStatus.UNREAD,
        tags=tags,
        ai_summary="這是一本由 AI 模擬生成的書籍，用於測試系統介面與資料庫連線功能。",
        official_desc="這是官方文案的佔位符。這裡通常會顯示爬蟲抓取到的詳細簡介。",
        ai_plot_analysis="這是 AI 生成的劇情分析佔位符。Phase 3 將會串接 Gemini 進行真正的內容生成。",
        added_date=date.today(),
        user_rating=0
    )
    
    # 寫入資料庫
    database.insert_book(new_book)
    return new_book

def get_books() -> List[Book]:
    """取得所有書籍"""
    return database.get_all_books()

def update_book_status(book: Book, new_status: BookStatus) -> Book:
    """更新狀態，並自動處理完食日期"""
    book.status = new_status
    
    # 自動化邏輯：如果是「已完食」，且沒有完成日，則填入今天
    if new_status == BookStatus.COMPLETED and not book.completed_date:
        book.completed_date = date.today()
    # 如果不是已完食，清除完成日 (可選，視需求而定，這裡暫時保留記錄)
    
    database.update_book(book)
    return book

def save_book_changes(book: Book):
    """儲存書籍的任何變更 (評分、心得等)"""
    database.update_book(book)

def remove_book(book_id: str):
    """移除書籍"""
    database.delete_book(book_id)

# // 功能: 業務邏輯層
# // input: UI 操作
# // output: 處理後的資料與資料庫互動
# // 其他補充: 包含 create_mock_book 用於測試
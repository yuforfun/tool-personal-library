import sqlite3
import json
import os
from typing import List, Optional
from datetime import date
from .models import Book, BookStatus

DB_PATH = os.path.join("data", "library.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 讓我們可以用欄位名稱存取
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT,
            source TEXT,
            url TEXT,
            word_count TEXT,
            chapters TEXT,
            status TEXT,
            tags TEXT,
            ai_summary TEXT,
            official_desc TEXT,
            ai_plot_analysis TEXT,
            added_date TEXT,
            completed_date TEXT,
            user_rating INTEGER,
            user_review TEXT
        )
    ''')
    conn.commit()
    conn.close()

# --- 輔助函式 ---
def _row_to_book(row: sqlite3.Row) -> Book:
    """將資料庫 Row 轉換為 Book 物件"""
    data = dict(row)
    # 處理 JSON 欄位
    data['tags'] = json.loads(data['tags']) if data['tags'] else []
    # 處理日期欄位 (字串 -> date 物件)
    if data.get('added_date'):
        data['added_date'] = date.fromisoformat(data['added_date'])
    if data.get('completed_date'):
        data['completed_date'] = date.fromisoformat(data['completed_date'])
    else:
        data['completed_date'] = None
        
    return Book(**data)

# --- CRUD 操作 ---

def insert_book(book: Book):
    """新增書籍"""
    conn = get_connection()
    c = conn.cursor()
    
    # 準備資料字典
    data = book.model_dump()
    # 序列化特殊欄位
    data['tags'] = json.dumps(data['tags'], ensure_ascii=False)
    data['status'] = data['status'].value  # Enum -> str
    data['added_date'] = data['added_date'].isoformat() if data['added_date'] else None
    data['completed_date'] = data['completed_date'].isoformat() if data['completed_date'] else None
    
    c.execute('''
        INSERT OR REPLACE INTO books (
            id, title, author, source, url, word_count, chapters, 
            status, tags, ai_summary, official_desc, ai_plot_analysis,
            added_date, completed_date, user_rating, user_review
        ) VALUES (
            :id, :title, :author, :source, :url, :word_count, :chapters, 
            :status, :tags, :ai_summary, :official_desc, :ai_plot_analysis,
            :added_date, :completed_date, :user_rating, :user_review
        )
    ''', data)
    
    conn.commit()
    conn.close()

def get_all_books() -> List[Book]:
    """取得所有書籍"""
    conn = get_connection()
    c = conn.cursor()
    # 【關鍵修正】 加入 secondary sort key (title ASC)，確保順序固定不亂跳
    c.execute('SELECT * FROM books ORDER BY added_date DESC, title ASC')
    rows = c.fetchall()
    conn.close()
    return [_row_to_book(row) for row in rows]

def update_book(book: Book):
    """更新書籍 (包含狀態、評分、心得等)"""
    # 其實 insert_book 使用了 INSERT OR REPLACE，所以可以直接複用
    # 但為了語意清晰，我們保留這個函式介面
    insert_book(book)

def delete_book(book_id: str):
    """刪除書籍"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM books WHERE id = ?', (book_id,))
    conn.commit()
    conn.close()

# // 功能: 資料庫 CRUD 實作
# // input: Book 物件或 ID
# // output: 資料庫寫入或 Book 物件列表
# // 其他補充: 使用 INSERT OR REPLACE 簡化更新邏輯
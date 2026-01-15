# 建議檔名: modules/database.py

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
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # // 【關鍵修正點】 CREATE TABLE 移除 word_count 與 chapters
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT,
            source TEXT,
            url TEXT,
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
    
    # // 【關鍵修正點】 為了相容舊資料庫，如果讀取到已刪除的欄位，將其移除以免報錯
    data.pop('word_count', None)
    data.pop('chapters', None)

    # 處理 JSON 欄位
    data['tags'] = json.loads(data['tags']) if data['tags'] else []
    # 處理日期欄位
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
    
    data = book.model_dump()
    data['tags'] = json.dumps(data['tags'], ensure_ascii=False)
    data['status'] = data['status'].value
    data['added_date'] = data['added_date'].isoformat() if data['added_date'] else None
    data['completed_date'] = data['completed_date'].isoformat() if data['completed_date'] else None
    
    # // 【關鍵修正點】 INSERT 語句移除 :word_count 與 :chapters
    # 注意：即便舊資料庫有這兩個欄位，這裡不寫入也不會報錯 (會填入 NULL)
    c.execute('''
        INSERT OR REPLACE INTO books (
            id, title, author, source, url, 
            status, tags, ai_summary, official_desc, ai_plot_analysis,
            added_date, completed_date, user_rating, user_review
        ) VALUES (
            :id, :title, :author, :source, :url, 
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
    c.execute('SELECT * FROM books ORDER BY added_date DESC, title ASC')
    rows = c.fetchall()
    conn.close()
    return [_row_to_book(row) for row in rows]

def update_book(book: Book):
    """更新書籍"""
    insert_book(book)

def delete_book(book_id: str):
    """刪除書籍"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM books WHERE id = ?', (book_id,))
    conn.commit()
    conn.close()

# // 功能: 資料庫層 (同步移除字數欄位)
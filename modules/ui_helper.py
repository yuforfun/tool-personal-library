# 新增 [modules/ui_helper.py] 區塊 A: 書封生成邏輯
# 修正原因：實作「Data as Art」核心，根據書籍標籤動態生成 CSS 漸層書封。
# 替換/新增指示：這是全新檔案，請放置於 modules 資料夾。

import random
from .models import Book, BookStatus

# === 視覺資產庫 ===

# 莫蘭迪色系預設盤 (Morandi Palette) - 用於無特徵書籍
MORANDI_GRADIENTS = [
    "linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)", # 淺紫藍
    "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)", # 銀白灰
    "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)", # 薄荷粉
    "linear-gradient(135deg, #e6e9f0 0%, #eef1f5 100%)", # 極簡白
    "linear-gradient(135deg, #accbee 0%, #e7f0fd 100%)", # 天空藍
]

# 主題映射規則 (Keyword to Gradient)
THEME_MAPPING = {
    # 優先級 1: 強烈氛圍
    "恐怖": "linear-gradient(to bottom, #434343 0%, black 100%)",
    "懸疑": "linear-gradient(to bottom, #09203f 0%, #537895 100%)",
    "暗黑": "linear-gradient(to bottom, #232526 0%, #414345 100%)",
    
    # 優先級 2: 情感導向
    "甜文": "linear-gradient(120deg, #f6d365 0%, #fda085 100%)", # 暖橘
    "寵文": "linear-gradient(to top, #ff9a9e 0%, #fecfef 99%, #fecfef 100%)", # 粉嫩
    "HE":   "linear-gradient(120deg, #a1c4fd 0%, #c2e9fb 100%)", # 清爽藍
    "爽文": "linear-gradient(120deg, #f093fb 0%, #f5576c 100%)", # 亮紅紫
    
    # 優先級 3: 類型導向
    "科幻": "linear-gradient(to right, #243949 0%, #517fa4 100%)", # 科技藍
    "星際": "linear-gradient(to top, #30cfd0 0%, #330867 100%)", # 深紫極光
    "古言": "linear-gradient(to top, #c79081 0%, #dfa579 100%)", # 大地色/水墨
    "武俠": "linear-gradient(to right, #4ca1af 0%, #c4e0e5 100%)", # 青綠
    "系統": "linear-gradient(to right, #4facfe 0%, #00f2fe 100%)", # 數位藍
}

def _get_cover_background(book: Book) -> str:
    """根據標籤決定書封背景 CSS，確保無標籤時顏色固定"""
    
    # 1. 檢查標籤關鍵字
    search_text = " ".join(book.tags).lower() if book.tags else ""
    
    for key, gradient in THEME_MAPPING.items():
        if key in search_text:
            return gradient
            
    # 2. // 【關鍵修正點】 使用 title 加上 id 的前幾碼進行 Hash，確保重複輸入或 AI 失敗時顏色一致
    # 不使用 random.choice，改用固定索引
    seed_string = f"{book.title}_{book.id[:8]}"
    hash_idx = sum(ord(c) for c in seed_string) % len(MORANDI_GRADIENTS)
    return MORANDI_GRADIENTS[hash_idx]

# // 功能: 視覺生成引擎 (固定顏色版)

def _get_title_size_style(title: str) -> str:
    """根據書名長度調整字體大小"""
    if len(title) > 10:
        return "font-size: 1rem;"
    return "font-size: 1.2rem;"

def render_book_card_html(book: Book) -> str:
    """
    生成單本書的 HTML 卡片 (純視覺層)
    """
    bg_style = _get_cover_background(book)
    title_style = _get_title_size_style(book.title)
    
    # 棄坑狀態的視覺處理：降低飽和度
    filter_style = "filter: grayscale(80%); opacity: 0.7;" if book.status == BookStatus.DROPPED else ""
    
    status_badge = f'<div class="book-status-stamp">{book.status.value}</div>'
    
    return f"""
    <div class="book-cover-container" style="{filter_style}">
        <div class="book-cover" style="background: {bg_style};">
            <div class="book-spine"></div>
            <div class="book-title-overlay">
                <div class="book-title-text" style="{title_style}">{book.title}</div>
                <div class="book-author-text">{book.author}</div>
            </div>
            {status_badge}
        </div>
    </div>
    """
# // 功能: 視覺生成引擎
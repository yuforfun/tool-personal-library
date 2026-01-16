# 修正 [modules/ui_helper.py] 區塊 B: 莫蘭迪色系與置中書封 (New Design)
# 修正原因：落實 Phase 2 視覺優化，採用莫蘭迪狀態色、置中排版、動態文字色與星級顯示。
# 替換/新增指示：請完全替換 modules/ui_helper.py。

from .models import Book, BookStatus

# === 視覺資產庫 (Morandi Status Palette) ===
# 格式: Status: (Background_Color, Text_Color)
STATUS_THEME = {
    BookStatus.UNREAD:    ("#F2F0EB", "#5a5a5a"), # 亞麻白 / 深灰字
    BookStatus.READING:   ("#E6D3C3", "#5a5a5a"), # 裸膚杏 / 深灰字
    BookStatus.COMPLETED: ("#94A79E", "#FFFFFF"), # 莫蘭迪綠 / 白字
    BookStatus.DROPPED:   ("#A8A29E", "#FFFFFF"), # 暖灰色 / 白字
}

# 預設備案
DEFAULT_THEME = ("#E0E0E0", "#5a5a5a")

def _get_theme(status: BookStatus):
    """取得該狀態對應的 (背景色, 文字色)"""
    return STATUS_THEME.get(status, DEFAULT_THEME)

def _get_star_html(rating: int) -> str:
    """生成星級 HTML，若 0 星則回傳空字串"""
    if rating <= 0:
        return ""
    # 使用實心星號，顏色統一用微暖的金色，但在莫蘭迪色上不要太刺眼
    stars = "★" * rating
    return f'<div class="book-stars">{stars}</div>'

def render_book_card_html(book: Book) -> str:
    """
    生成單本書的 HTML 卡片 (Phase 2: 莫蘭迪/置中/星級)
    修正：移除縮排以避免 Markdown 渲染錯誤
    """
    bg_color, text_color = _get_theme(book.status)
    stars_html = _get_star_html(book.user_rating)
    
    # 書名長度截斷處理
    display_title = book.title
    if len(display_title) > 20:
        display_title = display_title[:19] + "…"

    # // 【關鍵修正點】 移除 HTML 字串前的縮排，全部頂格寫
    return f"""<div class="book-card-container">
<div class="book-cover" style="background-color: {bg_color}; color: {text_color};">
{stars_html}
<div class="book-title-group">
<div class="book-title-text">{display_title}</div>
</div>
<div class="book-author-text">by {book.author}</div>
<div class="book-status-micro">{book.status.value}</div>
</div>
</div>"""

# // 功能: 視覺生成引擎 (修復縮排 Bug)
# // input: Book 物件
# // output: 頂格的 HTML String
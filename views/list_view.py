# 建議檔名: views/list_view.py

import streamlit as st
from modules.models import Book, BookStatus

def render_status_badge(status: BookStatus):
    """渲染狀態標籤樣式 (確保置中)"""
    colors = {
        BookStatus.UNREAD: ("#e8dcd5", "#5a5a5a"), 
        BookStatus.READING: ("#a89080", "white"),  
        BookStatus.COMPLETED: ("#7ba08f", "white"),
        BookStatus.DROPPED: ("#b8a99a", "white"),  
    }
    bg, text = colors.get(status, ("#e8dcd5", "#5a5a5a"))
    
    return f"""
        <div style="
            background-color: {bg}; 
            color: {text}; 
            padding: 4px 0px; 
            border-radius: 6px; 
            font-size: 0.8rem; 
            font-weight: 600;
            text-align: center;
            width: 85px;
            margin: 0 auto;
        ">
            {status.value}
        </div>
    """

def render_rating(rating: int):
    """渲染星級評分 (置中)"""
    if rating == 0:
        return '<div style="color: #b8a99a; font-size: 0.8rem; text-align: center;">-</div>'
    stars = "★" * rating
    return f'<div style="color: #d89c6f; font-size: 0.9rem; letter-spacing: 1px; text-align: center;">{stars}</div>'

def render_view(books: list[Book]):
    """渲染列表視圖"""
    if not books:
        st.info("目前沒有書籍。")
        return

    # 表頭全面置中 (除了書名)
    st.markdown("""
    <div style="display: flex; margin-bottom: 8px; color: #8b7866; font-size: 0.85rem; font-weight: bold; padding: 0 12px; border-bottom: 1px solid #eee; padding-bottom: 5px;">
        <div style="flex: 3;">書名 / 作者</div>
        <div style="flex: 1.5; text-align: center;">狀態</div>
        <div style="flex: 1.5; text-align: center;">評分</div>
        <div style="flex: 3; text-align: center;">AI 劇情分析</div>
        <div style="flex: 1; text-align: center;">操作</div>
    </div>
    """, unsafe_allow_html=True)

    for book in books:
        with st.container(border=True):
            # 建立比例，與表頭一致
            col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1.5, 3, 1], gap="small")
            
            # 使用統一的垂直置中容器 CSS
            cell_style = "display: flex; flex-direction: column; justify-content: center; height: 60px;"
            center_cell_style = "display: flex; align-items: center; justify-content: center; height: 60px;"

            with col1: # 書名作者
                st.markdown(f"""
                <div style='{cell_style}'>
                    <div style='font-size: 1rem; font-weight: bold; color: #5a5a5a; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'>{book.title}</div>
                    <div style='color: #8b7866; font-size: 0.75rem; margin-top: 2px;'>{book.author}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2: # 狀態
                st.markdown(f"<div style='{center_cell_style}'>{render_status_badge(book.status)}</div>", unsafe_allow_html=True)
            
            with col3: # 評分
                st.markdown(f"<div style='{center_cell_style}'>{render_rating(book.user_rating)}</div>", unsafe_allow_html=True)

            with col4: # AI劇情
                preview_text = book.ai_summary if book.ai_summary and book.ai_summary != "AI 尚未分析" else book.official_desc
                st.markdown(f"""
                <div style="{center_cell_style} color: #a89080; font-size: 0.8rem; text-align: center;">
                    <div style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; line-height: 1.3; width: 90%;">
                        {preview_text}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col5: # 操作 (移除 Markdown 包裝按鈕，改用容器內直接放置)
                # // 【關鍵修正點】 移除導致標籤洩漏的 HTML 封裝，直接在 col 內放置按鈕
                # 為了垂直對齊，我們在按鈕上方加一個微小的 padding (Streamlit 按鈕預設有 margin)
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                def select_book(b=book):
                    st.session_state.selected_book = b
                st.button("📝", key=f"btn_{book.id}", on_click=select_book, use_container_width=True)

# // 功能: 渲染列表視圖 (修復標籤洩漏與置中優化)
# 修正 [views/list_view.py] 區塊 H: 強制重置編輯狀態 (Reset on Open)
# 修正原因：在點擊詳情按鈕的瞬間強制重置 is_editing = False，確保每次開啟彈窗都是唯讀狀態。
# 替換/新增指示：請完全替換 views/list_view.py。

import streamlit as st
from modules.models import Book, BookStatus
from modules import ui_helper 

def render_status_badge(status: BookStatus):
    """渲染狀態標籤 (使用統一的莫蘭迪色，移除縮排以防 Bug)"""
    bg_color, text_color = ui_helper._get_theme(status)
    return f"""<div style="background-color: {bg_color}; color: {text_color}; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; text-align: center; min-width: 60px; display: inline-block;">{status.value}</div>"""

def render_rating(rating: int):
    """渲染星級"""
    if rating == 0:
        return '<span style="color: #ccc;">-</span>'
    return f'<span style="color: #D4AF37; font-size: 1rem;">{"★" * rating}</span>'

def render_view(books: list[Book]):
    """渲染列表視圖 (List Item Style)"""
    if not books:
        st.info("📚 找不到符合條件的書籍。")
        return

    # 表頭
    st.markdown("""
    <div style="
        display: flex; 
        padding: 8px 12px; 
        border-bottom: 2px solid #e0e0e0; 
        color: #888; 
        font-size: 0.85rem; 
        font-weight: bold;
        margin-bottom: 10px;
    ">
        <div style="flex: 3;">書名 / 作者</div>
        <div style="flex: 1.5; text-align: center;">狀態</div>
        <div style="flex: 1.5; text-align: center;">評分</div>
        <div style="flex: 3; text-align: left; padding-left: 10px;">短評 / 簡介</div>
        <div style="flex: 1; text-align: center;">操作</div>
    </div>
    """, unsafe_allow_html=True)

    # 列表內容
    for book in books:
        st.markdown("<div class='list-item-separator'></div>", unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1.5, 3, 1], gap="small")
        
        cell_style = "display: flex; flex-direction: column; justify-content: center; min-height: 50px;"
        center_style = "display: flex; align-items: center; justify-content: center; min-height: 50px;"

        with col1: # 書名
            st.markdown(f"""
            <div style='{cell_style}'>
                <div style='font-size: 1rem; font-weight: 600; color: #444; margin-bottom: 2px;'>{book.title}</div>
                <div style='font-size: 0.8rem; color: #888;'>{book.author}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2: # 狀態
            st.markdown(f"<div style='{center_style}'>{render_status_badge(book.status)}</div>", unsafe_allow_html=True)
            
        with col3: # 評分
            st.markdown(f"<div style='{center_style}'>{render_rating(book.user_rating)}</div>", unsafe_allow_html=True)
            
        with col4: # 短評
            text = book.ai_summary if (book.ai_summary and book.ai_summary != "AI 尚未分析") else book.official_desc
            if len(text) > 40: text = text[:38] + "..."
            
            st.markdown(f"""
            <div style='{center_style} justify-content: flex-start; padding-left: 10px; color: #666; font-size: 0.85rem;'>
                {text}
            </div>
            """, unsafe_allow_html=True)
            
        with col5: # 按鈕
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            
            # // 【關鍵修正點】 定義 Callback：同時設定書籍與重置編輯狀態
            def select_book(b=book):
                st.session_state.selected_book = b
                st.session_state.is_editing = False # 強制重置！
            
            if st.button("📝", key=f"list_btn_{book.id}", on_click=select_book, use_container_width=True):
                pass 

# // 功能: 列表視圖渲染 (含狀態重置邏輯)
# 修正 [views/gallery_view.py] 區塊 B: 強制重置編輯狀態 (Reset on Open)
# 修正原因：確保從畫廊點擊詳情時，也強制重置為唯讀模式。
# 替換/新增指示：請完全替換 views/gallery_view.py。

import streamlit as st
from modules.models import Book
from modules import ui_helper

def render_view(books: list[Book], cols_num: int = 5):
    """
    渲染畫廊視圖 (Pure Renderer)
    修正：預設欄位改為 5
    """
    
    if not books:
        st.info("📚 找不到符合條件的書籍。")
        return

    cols = st.columns(cols_num)
    
    for i, book in enumerate(books):
        col = cols[i % cols_num] 
        
        with col:
            # A. 渲染視覺書封
            html_code = ui_helper.render_book_card_html(book)
            st.markdown(html_code, unsafe_allow_html=True)
            
            # B. 渲染互動按鈕
            # // 【關鍵修正點】 定義 Callback：同時設定書籍與重置編輯狀態
            def select_book(b=book):
                st.session_state.selected_book = b
                st.session_state.is_editing = False # 強制重置！
            
            st.button(
                "📖 詳情", 
                key=f"gallery_btn_{book.id}", 
                on_click=select_book,
                use_container_width=True
            )
            
            # 間距
            st.markdown("<div style='height: 15px'></div>", unsafe_allow_html=True)

# // 功能: 畫廊視圖渲染 (含狀態重置邏輯)
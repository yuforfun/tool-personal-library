# 新增 [views/gallery_view.py] 區塊 A: 畫廊模式視圖邏輯
# 修正原因：實作分頁與格線佈局，整合 HTML 書封與互動按鈕。
# 替換/新增指示：這是全新檔案，請放置於 views 資料夾。

import streamlit as st
from modules.models import Book
from modules import ui_helper

# 設定每頁顯示數量 (12 是 3, 4, 6 的公倍數)
ITEMS_PER_PAGE = 12

def render_view(books: list[Book], cols_num: int = 4):
    """
    渲染畫廊視圖
    
    Args:
        books: 書籍列表
        cols_num: 格線欄數 (預設 4)
    """
    
    if not books:
        st.info("📚 找不到符合條件的書籍。")
        return

    # --- 1. 分頁控制器 (Pagination) ---
    total_pages = (len(books) - 1) // ITEMS_PER_PAGE + 1
    
    # 確保 session state 中有頁碼
    if "gallery_page" not in st.session_state:
        st.session_state.gallery_page = 1
        
    # 如果篩選後數量變少，頁碼可能越界，需重置
    if st.session_state.gallery_page > total_pages:
        st.session_state.gallery_page = 1

    # 工具列
    c1, c2 = st.columns([8, 4])
    with c1:
        st.caption(f"共 {len(books)} 本，第 {st.session_state.gallery_page} / {total_pages} 頁")
    with c2:
        if total_pages > 1:
            new_page = st.number_input(
                "跳轉頁碼", 
                min_value=1, 
                max_value=total_pages, 
                value=st.session_state.gallery_page,
                label_visibility="collapsed"
            )
            st.session_state.gallery_page = new_page

    # 切片取得當前頁面的書籍
    start_idx = (st.session_state.gallery_page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_page_books = books[start_idx:end_idx]

    # --- 2. 格線佈局迴圈 ---
    cols = st.columns(cols_num)
    
    for i, book in enumerate(current_page_books):
        col = cols[i % cols_num] 
        
        with col:
            # A. 渲染視覺書封
            html_code = ui_helper.render_book_card_html(book)
            st.markdown(html_code, unsafe_allow_html=True)
            
            # B. 渲染互動按鈕
            def select_book(b=book):
                st.session_state.selected_book = b
            
            st.button(
                "📖 詳情", 
                key=f"gallery_btn_{book.id}", 
                on_click=select_book,
                use_container_width=True
            )
            
            # 間距
            st.markdown("<div style='height: 15px'></div>", unsafe_allow_html=True)

# // 功能: 畫廊渲染邏輯
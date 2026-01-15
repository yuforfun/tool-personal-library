# 修正 [views/book_detail.py] 區塊 A: 自然流動佈局 (Natural Layout)
# 修正原因：移除固定高度限制，解決內容被截斷與輸入框消失的問題。

import streamlit as st
from modules.models import Book, BookStatus
from modules import services

def render_detail_panel():
    """渲染詳細資訊面板 (自然流動佈局版)"""
    book: Book = st.session_state.get("selected_book")
    
    if not book:
        return

    # --- 1. 頂部資訊 (Action Bar) ---
    c_title, c_close = st.columns([8, 2])
    with c_title:
        st.markdown(f"<h3 style='margin:0; padding:0; font-size:1.2rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{book.title}</h3>", unsafe_allow_html=True)
    with c_close:
        if st.button("✖", key="close_btn", use_container_width=True):
            st.session_state.selected_book = None
            st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True) 

    # 操作按鈕群
    c_save, c_del, c_link = st.columns([4, 2, 2], gap="small")
    
    with c_save:
        save_clicked = st.button("💾 儲存變更", type="primary", use_container_width=True, key="top_save")
    
    with c_del:
        if st.button("🗑️", type="secondary", use_container_width=True, key="top_del", help="刪除書籍"):
            services.remove_book(book.id)
            st.session_state.selected_book = None
            st.toast("✅ 書籍已刪除")
            st.rerun()
            
    with c_link:
        st.link_button("🔗", book.url, use_container_width=True, help="前往原始網站")

    st.divider()

    # --- 2. 內容編輯區 (Content Area) ---
    # 【關鍵修正】 移除了 height 參數，改為 border=False
    # 這會讓內容自然向下延伸，頁面會出現捲軸，但保證所有元件功能正常
    with st.container(border=False):
        
        # 狀態
        new_status = st.selectbox(
            "閱讀狀態", 
            options=[s for s in BookStatus],
            index=[s for s in BookStatus].index(book.status),
            format_func=lambda x: x.value,
            key="edit_status"
        )
        
        # 評分
        new_rating = st.slider("評分", 0, 5, value=book.user_rating, key="edit_rating")
        
        # 心得
        # 因為外層沒有高度限制，這裡可以放心地設定固定高度，不會被切掉
        st.caption("心得筆記")
        new_review = st.text_area(
            "心得筆記", 
            value=book.user_review, 
            height=250,  
            key="edit_review", 
            placeholder="請在此輸入閱讀心得...",
            label_visibility="collapsed"
        )
        
        # 儲存邏輯
        if save_clicked:
            book.status = new_status
            book.user_rating = new_rating
            book.user_review = new_review
            
            services.update_book_status(book, new_status)
            services.save_book_changes(book)
            st.toast("✅ 資料已成功儲存！", icon="💾")

        st.markdown("---")
        
        # 資訊展示區
        st.caption("標籤")
        if book.tags:
            st.markdown(" ".join([f"<span style='background:#f0ebe6;padding:2px 6px;border-radius:4px;font-size:0.8rem;color:#8b7866'>#{t}</span>" for t in book.tags]), unsafe_allow_html=True)
        else:
            st.text("無標籤")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.caption("🤖 AI 劇情分析")
        st.info(book.ai_plot_analysis if book.ai_plot_analysis else "尚無 AI 分析資料")
        
        st.caption("原始簡介")
        st.text(book.official_desc)

# // 功能: 詳情面板 (標準佈局版)
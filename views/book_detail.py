# 修正 [views/book_detail.py] 區塊 B: 新增完食日期選擇器
# 修正原因：當書籍狀態設為「已完食」時，允許使用者手動指定日期，而非強制使用當天。
# 替換/新增指示：請完全取代 views/book_detail.py。

import streamlit as st
from datetime import date
from modules.models import Book, BookStatus
from modules import services

def render_detail_panel():
    """渲染詳細資訊面板"""
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

    # --- 2. 內容編輯區 ---
    with st.container(border=False):
        
        # A. 狀態與日期 (動態連動)
        col_status, col_date = st.columns([1, 1])
        
        with col_status:
            new_status = st.selectbox(
                "閱讀狀態", 
                options=[s for s in BookStatus],
                index=[s for s in BookStatus].index(book.status),
                format_func=lambda x: x.value,
                key="edit_status"
            )
            
        with col_date:
            # 【關鍵修正】 只有在狀態為「已完食」時，才顯示日期選擇器
            new_completed_date = book.completed_date
            
            if new_status == BookStatus.COMPLETED:
                # 如果原本沒有日期，預設為今天；如果有，使用原本的
                default_date = book.completed_date if book.completed_date else date.today()
                
                new_completed_date = st.date_input(
                    "完食日期",
                    value=default_date,
                    key="edit_completed_date"
                )
            else:
                # 非完食狀態，清空日期顯示 (或顯示為無)
                st.text_input("完食日期", value="-", disabled=True, key="disabled_date")
                new_completed_date = None

        # B. 評分
        new_rating = st.slider("評分", 0, 5, value=book.user_rating, key="edit_rating")
        
        # C. 心得
        st.caption("心得筆記")
        new_review = st.text_area(
            "心得筆記", 
            value=book.user_review, 
            height=250,  
            key="edit_review", 
            placeholder="請在此輸入閱讀心得...",
            label_visibility="collapsed"
        )
        
        # D. 儲存邏輯
        if save_clicked:
            # 更新記憶體中的物件
            book.status = new_status
            book.user_rating = new_rating
            book.user_review = new_review
            
            # 特別處理日期：確保 UI 選擇的日期被寫入
            if new_status == BookStatus.COMPLETED:
                book.completed_date = new_completed_date
            else:
                book.completed_date = None
            
            # 呼叫業務邏輯存檔
            services.save_book_changes(book)
            st.toast("✅ 資料已成功儲存！", icon="💾")
            # 重新整理以更新介面 (例如列表上的狀態徽章)
            st.rerun()

        st.markdown("---")
        
        # E. 資訊展示區
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

# // 功能: 詳情面板 (含日期選擇器修正)
# // input: selected_book
# // output: 編輯介面
# // 其他補充: 解決已完食無法指定日期的問題
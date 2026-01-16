# 修正 [views/book_detail.py] 區塊 F: 優化原始連結按鈕 (UX Fix)
# 修正原因：當 book.url 為空時，禁用「前往原始網站」按鈕，避免誤導使用者。
# 替換/新增指示：請完全替換 views/book_detail.py。

import streamlit as st
from datetime import date
from modules.models import Book, BookStatus
from modules import services, ui_helper

@st.dialog("書籍詳情", width="large")
def render_detail_dialog():
    """
    渲染書籍詳情彈窗 (Modal)
    包含：Read Mode (預設) 與 Edit Mode (切換)
    """
    if "selected_book" not in st.session_state or not st.session_state.selected_book:
        st.rerun()
        return

    book: Book = st.session_state.selected_book

    if "is_editing" not in st.session_state:
        st.session_state.is_editing = False

    # --- Header Area ---
    c_title, c_edit = st.columns([8, 2], gap="small")
    
    with c_title:
        st.markdown(f"""
        <div style="font-size: 1.5rem; font-weight: bold; color: #5a5a5a; line-height: 1.2;">
            {book.title}
        </div>
        <div style="font-size: 1rem; color: #888; margin-top: 4px;">
            by {book.author}
        </div>
        """, unsafe_allow_html=True)

    with c_edit:
        if not st.session_state.is_editing:
            if st.button("✏️ 編輯", key="btn_enter_edit", use_container_width=True):
                st.session_state.is_editing = True
                st.rerun()
        else:
            if st.button("❌ 取消", key="btn_cancel_edit", use_container_width=True):
                st.session_state.is_editing = False
                st.rerun()

    st.divider()

    # --- Body Area ---
    if not st.session_state.is_editing:
        _render_read_mode(book)
    else:
        _render_edit_mode(book)

# --- Sub Components ---

def _render_read_mode(book: Book):
    """唯讀模式 UI"""
    # 1. 資訊概覽
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.caption("閱讀狀態")
        bg, text = ui_helper._get_theme(book.status)
        st.markdown(f"""
        <div style="background-color: {bg}; color: {text}; padding: 4px 12px; border-radius: 12px; display: inline-block; font-weight: bold; font-size: 0.9rem;">
            {book.status.value}
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.caption("評分")
        stars = "★" * book.user_rating if book.user_rating > 0 else "-"
        color = "#D4AF37" if book.user_rating > 0 else "#ccc"
        st.markdown(f"<div style='color: {color}; font-size: 1.2rem;'>{stars}</div>", unsafe_allow_html=True)

    with c3:
        st.caption("完食日期")
        date_str = book.completed_date.strftime("%Y-%m-%d") if book.completed_date else "-"
        st.markdown(f"<div style='color: #5a5a5a; font-size: 1rem;'>{date_str}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. 標籤
    if book.tags:
        st.caption("標籤")
        tags_html = " ".join([f"""
            <span style="background-color: #f0f2f6; color: #5a5a5a; padding: 4px 10px; border-radius: 16px; font-size: 0.85rem; margin-right: 6px;">
                #{tag}
            </span>
        """ for tag in book.tags])
        st.markdown(tags_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # 3. 內容區塊
    if book.user_review:
        st.info(f"**📝 心得筆記**\n\n{book.user_review}")
    
    with st.expander("🤖 AI 劇情分析", expanded=True):
        if book.ai_plot_analysis:
            st.markdown(book.ai_plot_analysis)
        else:
            st.caption("尚無 AI 分析資料")

    with st.expander("📄 原始文案", expanded=False):
        st.text(book.official_desc)

    st.divider()
    
    # 4. 底部操作
    bc1, bc2 = st.columns([1, 1])
    with bc1:
        # // 【關鍵修正點】 判斷 url 是否存在，若無則顯示 Disabled 按鈕
        if book.url:
            st.link_button("🔗 前往原始網站", book.url, use_container_width=True)
        else:
            st.button("🔗 前往原始網站", disabled=True, use_container_width=True, key="btn_link_disabled")
            
    with bc2:
        if st.button("🗑️ 刪除書籍", key="btn_delete", type="primary", use_container_width=True):
            _delete_book(book)

def _render_edit_mode(book: Book):
    """編輯模式 UI"""
    with st.form("edit_book_form"):
        # 狀態與日期
        c1, c2 = st.columns(2)
        with c1:
            new_status = st.selectbox(
                "閱讀狀態", 
                options=[s for s in BookStatus],
                index=[s for s in BookStatus].index(book.status),
                format_func=lambda x: x.value
            )
        with c2:
            default_date = book.completed_date if book.completed_date else date.today()
            new_date = st.date_input("完食日期", value=default_date)

        # 評分
        new_rating = st.slider("評分", 0, 5, value=book.user_rating)
        
        # 心得
        new_review = st.text_area("心得筆記", value=book.user_review, height=150)
        
        # 網址編輯
        st.markdown("---")
        new_url = st.text_input("來源網址", value=book.url, placeholder="https://...")

        # 儲存按鈕
        submitted = st.form_submit_button("💾 儲存變更", use_container_width=True, type="primary")
        
        if submitted:
            # 更新物件
            book.status = new_status
            book.user_rating = new_rating
            book.user_review = new_review
            book.url = new_url 
            
            if new_status == BookStatus.COMPLETED:
                book.completed_date = new_date
            else:
                book.completed_date = None
            
            services.save_book_changes(book)
            
            st.session_state.is_editing = False
            st.toast("✅ 資料已更新！")
            st.rerun()

def _delete_book(book: Book):
    services.remove_book(book.id)
    st.session_state.selected_book = None
    st.toast("✅ 書籍已刪除")
    st.rerun()

# // 功能: 詳情彈窗 (含網址按鈕防呆與編輯)
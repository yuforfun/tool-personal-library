# 修正 [views/book_detail.py] 區塊 L: 刪除防呆機制 (Safety Lock)
# 修正原因：將刪除功能改為兩段式確認，防止使用者誤觸導致資料遺失。
# 替換/新增指示：請完全替換 views/book_detail.py。

import streamlit as st
import time
import traceback
from datetime import date
from modules.models import Book, BookStatus
from modules import services, ui_helper, ai_agent

# === 定義模擬爬蟲資料 (Mock Object) ===
class MockScrapedData:
    def __init__(self, title, author, description, url=""):
        self.title = title if title else "未知標題"
        self.author = author if author else "未知作者"
        self.description = description if description else "（無內容）"
        self.url = url
        self.content = self.description     
        self.site_name = "手動編輯"          
        self.source_name = "手動編輯"        
        self.publish_date = None            
        self.status = "未知"                

@st.dialog("書籍詳情", width="large")
def render_detail_dialog():
    """書籍詳情彈窗"""
    
    if "selected_book" not in st.session_state or not st.session_state.selected_book:
        st.rerun()
        return

    book: Book = st.session_state.selected_book

    # 上下文檢查
    if "last_viewed_book_id" not in st.session_state:
        st.session_state.last_viewed_book_id = None
        
    if st.session_state.last_viewed_book_id != book.id:
        st.session_state.is_editing = False
        st.session_state.last_viewed_book_id = book.id
        # 重置刪除確認狀態
        st.session_state.delete_confirm_mode = False 

    if "is_editing" not in st.session_state:
        st.session_state.is_editing = False
        
    # 初始化刪除確認狀態
    if "delete_confirm_mode" not in st.session_state:
        st.session_state.delete_confirm_mode = False

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
                st.session_state.delete_confirm_mode = False # 切換模式時重置
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
    c1, c2, c3 = st.columns(3)
    with c1:
        st.caption("閱讀狀態")
        bg, text = ui_helper._get_theme(book.status)
        st.markdown(f"<div style='background-color: {bg}; color: {text}; padding: 4px 12px; border-radius: 12px; display: inline-block; font-weight: bold; font-size: 0.9rem;'>{book.status.value}</div>", unsafe_allow_html=True)
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

    if book.tags:
        st.caption("標籤")
        tags_html = " ".join([f"<span style='background-color: #f0f2f6; color: #5a5a5a; padding: 4px 10px; border-radius: 16px; font-size: 0.85rem; margin-right: 6px;'>#{tag}</span>" for tag in book.tags])
        st.markdown(tags_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

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
    
    # 底部按鈕區
    bc1, bc2 = st.columns([1, 1])
    with bc1:
        if book.url:
            st.link_button("🔗 前往原始網站", book.url, use_container_width=True)
        else:
            st.button("🔗 前往原始網站", disabled=True, use_container_width=True, key="btn_link_disabled")
            
    with bc2:
        # // 【關鍵修正點】 兩段式刪除防呆機制
        if not st.session_state.delete_confirm_mode:
            # 第一階段：普通按鈕 (非 Primary)，防止誤觸
            if st.button("🗑️ 刪除書籍", key="btn_del_trigger", use_container_width=True):
                st.session_state.delete_confirm_mode = True
                st.rerun()
        else:
            # 第二階段：確認區塊 (紅色警示)
            with st.container(border=True):
                st.markdown("<div style='text-align: center; color: #d9534f; font-weight: bold; margin-bottom: 8px;'>⚠️ 確定刪除此書？</div>", unsafe_allow_html=True)
                dc1, dc2 = st.columns(2)
                with dc1:
                    if st.button("取消", key="btn_del_cancel", use_container_width=True):
                        st.session_state.delete_confirm_mode = False
                        st.rerun()
                with dc2:
                    if st.button("確認刪除", key="btn_del_confirm", type="primary", use_container_width=True):
                        _delete_book(book)

def _render_edit_mode(book: Book):
    """編輯模式 UI"""
    
    k_desc = f"edit_desc_{book.id}"
    k_title = f"edit_title_{book.id}"
    k_author = f"edit_author_{book.id}"
    
    # AI 重跑功能
    with st.expander("🤖 進階功能：重新觸發 AI 分析", expanded=False):
        st.caption("使用下方輸入框的內容進行分析 (不需先存檔)。")
        
        if st.button("🚀 僅重跑 AI 分析", use_container_width=True):
            draft_desc = st.session_state.get(k_desc, book.official_desc)
            draft_title = st.session_state.get(k_title, book.title)
            draft_author = st.session_state.get(k_author, book.author)
            
            if not draft_desc:
                st.error("錯誤：文案內容為空，無法進行分析。")
            else:
                with st.spinner("🤖 AI 正在閱讀草稿..."):
                    try:
                        mock_data = MockScrapedData(draft_title, draft_author, draft_desc, url=book.url)
                        ai_res = ai_agent.analyze_book(mock_data)
                        if ai_res:
                            book.tags = ai_res.tags
                            book.ai_summary = ai_res.summary
                            book.ai_plot_analysis = ai_res.plot
                            services.save_book_changes(book)
                            st.success("✅ AI 分析成功！")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("AI 回傳空值 (None)。")
                            st.markdown("### 🛠️ Debug Info")
                            st.json({
                                "title": mock_data.title,
                                "author": mock_data.author,
                                "source_name": mock_data.source_name
                            })
                    except Exception as e:
                        st.error(f"執行錯誤: {str(e)}")
                        st.text(traceback.format_exc())

    st.markdown("---")

    # 主要編輯表單
    with st.form("edit_book_form"):
        st.markdown("#### 📖 基本資訊")
        ec1, ec2 = st.columns([2, 1])
        with ec1:
            new_title = st.text_input("書名", value=book.title, key=k_title)
        with ec2:
            new_author = st.text_input("作者", value=book.author, key=k_author)
            
        new_url = st.text_input("來源網址", value=book.url, placeholder="https://...")
        new_official_desc = st.text_area("官方文案 (AI 分析依據)", value=book.official_desc, height=150, key=k_desc)

        st.markdown("#### ✍️ 閱讀紀錄")
        c1, c2 = st.columns(2)
        with c1:
            new_status = st.selectbox("閱讀狀態", options=[s for s in BookStatus], index=[s for s in BookStatus].index(book.status), format_func=lambda x: x.value)
        with c2:
            default_date = book.completed_date if book.completed_date else date.today()
            new_date = st.date_input("完食日期", value=default_date)

        new_rating = st.slider("評分", 0, 5, value=book.user_rating)
        new_review = st.text_area("心得筆記", value=book.user_review, height=100)
        
        submitted = st.form_submit_button("💾 儲存所有變更", use_container_width=True, type="primary")
        
        if submitted:
            book.title = new_title
            book.author = new_author
            book.url = new_url
            book.official_desc = new_official_desc
            book.status = new_status
            book.user_rating = new_rating
            book.user_review = new_review
            book.completed_date = new_date if new_status == BookStatus.COMPLETED else None
            
            services.save_book_changes(book)
            st.session_state.is_editing = False
            st.toast("✅ 資料已更新！")
            st.rerun()

def _delete_book(book: Book):
    services.remove_book(book.id)
    st.session_state.selected_book = None
    st.toast("✅ 書籍已刪除")
    st.rerun()
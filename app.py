# 修正 [app.py] 區塊 A: 介面串接真實邏輯
# 修正原因：將側邊欄的按鈕動作指向新的 services.add_book 函式。
# 替換/新增指示：請完全取代原有的 app.py。

import streamlit as st
import os
from modules.database import init_db
from modules.models import BookStatus
from modules import services
import views.list_view
import views.book_detail

# 1. 頁面設定
st.set_page_config(
    page_title="Personal Digital Library",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CSS 載入
def load_css():
    css_path = os.path.join("config", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 3. 初始化
if "init_done" not in st.session_state:
    init_db()
    st.session_state.init_done = True
    
if "selected_book" not in st.session_state:
    st.session_state.selected_book = None
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "list"

load_css()

# --- UI 結構 ---

# A. 側邊欄 (Sidebar)
with st.sidebar:
    st.title("快速入庫")
    
    with st.form("quick_add_form", clear_on_submit=True):
        url_input = st.text_input("請輸入書籍網址", placeholder="支援：晉江 / 半夏 / 小說狂人...")
        submitted = st.form_submit_button("啟動 AI 智慧抓取", use_container_width=True)
        
        if submitted and url_input:
            # 顯示載入動畫
            with st.spinner("🤖 正在爬取網頁並進行 AI 分析 (Gemini 2.5)..."):
                try:
                    # 【關鍵修正】 呼叫真實的 add_book
                    new_book = services.add_book(url_input)
                    
                    if new_book:
                        st.toast(f"✅ 成功入庫：《{new_book.title}》", icon="🎉")
                        # 自動重新整理頁面以顯示新書
                        st.rerun()
                    else:
                        st.error("入庫失敗：爬蟲無法解析此網址，或 AI 暫時無法連線。")
                except Exception as e:
                    st.error(f"發生未預期的錯誤: {e}")
    
    st.divider()
    
    st.title("篩選器")
    search_query = st.text_input("關鍵字搜尋", placeholder="書名或作者...")
    # sort_order = st.selectbox("日期排序", ["最新入庫", "最早入庫"]) # 暫時隱藏，目前預設最新
    status_filter = st.multiselect(
        "閱讀狀態",
        options=[s for s in BookStatus],
        format_func=lambda x: x.value,
        default=[]
    )
    
    # 取得資料庫中的真實書籍
    all_books = services.get_books()
    st.divider()
    st.caption(f"共收錄 {len(all_books)} 本書")

# B. 主畫面
col_stats, col_space, col_view = st.columns([3, 3, 3])

with col_stats:
    total_count = len(all_books)
    # 計算本月新增 (簡易版，先顯示總數)
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; color: #5a5a5a; padding-top: 10px;">
            <span style="font-size: 0.9rem;">總藏書 <b>{total_count}</b></span>
        </div>
        """, 
        unsafe_allow_html=True
    )

with col_view:
    view_mode = st.radio(
        "view_mode_selector",
        options=["list", "gallery", "calendar"],
        format_func=lambda x: "列表模式" if x == "list" else ("畫廊模式" if x == "gallery" else "日曆模式"),
        horizontal=True,
        label_visibility="collapsed"
    )
    st.session_state.view_mode = view_mode

st.divider()

if st.session_state.view_mode == "list":
    if st.session_state.selected_book:
        col_list, col_detail = st.columns([7, 3], gap="medium")
    else:
        col_list = st.container()
        col_detail = None

    with col_list:
        filtered_books = all_books
        if status_filter:
            filtered_books = [b for b in filtered_books if b.status in status_filter]
        if search_query:
            filtered_books = [b for b in filtered_books if search_query in b.title or search_query in b.author]
            
        views.list_view.render_view(filtered_books)

    if st.session_state.selected_book and col_detail:
        with col_detail:
            with st.container(border=True):
                views.book_detail.render_detail_panel()

elif st.session_state.view_mode == "gallery":
    st.info("🎨 畫廊模式將於 Phase 4 實作")
else:
    st.info("📅 日曆模式將於 Phase 4 實作")
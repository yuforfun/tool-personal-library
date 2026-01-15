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
    
# 【關鍵修正】 確保變數存在，防止 AttributeError
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
        url_input = st.text_input("請輸入書籍網址", placeholder="支援：晉江 / 半夏 / 小說狂人")
        submitted = st.form_submit_button("啟動 AI 智慧抓取", use_container_width=True)
        
        if submitted and url_input:
            with st.spinner("🤖 AI 正在分析網頁與生成標籤..."):
                new_book = services.create_mock_book(url_input)
                st.toast(f"✅ 成功入庫：《{new_book.title}》")
                st.rerun()
    
    st.divider()
    
    st.title("篩選器")
    search_query = st.text_input("關鍵字搜尋", placeholder="書名或作者...")
    sort_order = st.selectbox("日期排序", ["最新入庫", "最早入庫"])
    status_filter = st.multiselect(
        "閱讀狀態",
        options=[s for s in BookStatus],
        format_func=lambda x: x.value,
        default=[]
    )
    
    all_books = services.get_books()
    st.divider()
    st.caption(f"共收錄 {len(all_books)} 本書")

# B. 主畫面 - 分割視窗邏輯 (Split View Logic)

# 頂部控制列 (Top Bar)
col_stats, col_space, col_view = st.columns([3, 3, 3])

with col_stats:
    total_count = len(all_books)
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; color: #5a5a5a; padding-top: 10px;">
            <span style="font-size: 0.9rem;">總藏書 <b>{total_count}</b></span>
            <span style="margin: 0 15px; color: #b8a99a;">|</span>
            <span style="font-size: 0.9rem;">本月新增 <b>0</b></span>
        </div>
        """, 
        unsafe_allow_html=True
    )

with col_view:
    # 視圖切換 (Phase 1.7 修正版)
    view_mode = st.radio(
        "view_mode_selector",
        options=["list", "gallery", "calendar"],
        format_func=lambda x: "列表模式" if x == "list" else ("畫廊模式" if x == "gallery" else "日曆模式"),
        horizontal=True,
        label_visibility="collapsed"
    )
    st.session_state.view_mode = view_mode

st.divider()

# 核心顯示區：使用 columns 實現 Master-Detail 佈局
if st.session_state.view_mode == "list":
    
    # 判斷是否開啟了詳情面板
    if st.session_state.selected_book:
        # 【關鍵修正】 開啟詳情時：左 70% (列表), 右 30% (詳情)
        col_list, col_detail = st.columns([7, 3], gap="medium")
    else:
        # 未開啟詳情時：左 100% (列表) - 使用一個 column 占滿
        col_list = st.container()
        col_detail = None

    # 1. 渲染列表 (在左側)
    with col_list:
        # 過濾邏輯
        filtered_books = all_books
        if status_filter:
            filtered_books = [b for b in filtered_books if b.status in status_filter]
        if search_query:
            filtered_books = [b for b in filtered_books if search_query in b.title or search_query in b.author]
            
        views.list_view.render_view(filtered_books)

    # 2. 渲染詳情 (在右側，如果有)
    if st.session_state.selected_book and col_detail:
        with col_detail:
            # 這裡我們使用一個固定高度的 container 來裝詳情，讓它看起來像 Sidebar
            with st.container(border=True):
                views.book_detail.render_detail_panel()

elif st.session_state.view_mode == "gallery":
    st.info("🎨 畫廊模式將於 Phase 4 實作")
else:
    st.info("📅 日曆模式將於 Phase 4 實作")
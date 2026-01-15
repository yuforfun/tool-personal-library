# 修正 [app.py] 區塊 B: 整合 Phase 5 日曆視圖
# 修正原因：引入 calendar_view 並替換原本的日曆模式佔位符。
# 替換/新增指示：請完全取代 app.py。

import streamlit as st
import os
from datetime import date
from modules.database import init_db
from modules.models import BookStatus
from modules import services
import views.list_view
import views.book_detail
import views.gallery_view 
import views.calendar_view # [新增] 引入日曆視圖

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

# --- 資料準備 ---
all_books = services.get_books()

# 統計數據 (簡易版，給 Top Bar 使用)
total_count = len(all_books)
this_month_count = len([
    b for b in all_books 
    if b.added_date and b.added_date.year == date.today().year and b.added_date.month == date.today().month
])

all_tags = sorted(list(set(tag for book in all_books for tag in book.tags)))

# --- UI 結構 ---

# A. 側邊欄
with st.sidebar:
    st.title("快速入庫")
    
    with st.form("quick_add_form", clear_on_submit=True):
        url_input = st.text_input("請輸入書籍網址", placeholder="支援：晉江 / 半夏 / 小說狂人")
        submitted = st.form_submit_button("啟動 AI 智慧抓取", use_container_width=True)
        
        if submitted and url_input:
            with st.spinner("🤖 正在爬取網頁並進行 AI 分析 (Gemini 2.5)..."):
                try:
                    new_book = services.add_book(url_input)
                    if new_book:
                        st.toast(f"✅ 成功入庫：《{new_book.title}》", icon="🎉")
                        st.rerun()
                    else:
                        st.error("入庫失敗：爬蟲無法解析或 AI 連線異常。")
                except Exception as e:
                    st.error(f"錯誤: {e}")
    
    st.divider()
    
# --- 側邊欄篩選器區塊 ---
    st.title("篩選器")
    search_query = st.text_input("關鍵字搜尋", placeholder="書名或作者...")
    tag_filter = st.multiselect("標籤篩選", options=all_tags, default=[])
    
    # // 【關鍵修正點】 補回排序選項
    sort_order = st.selectbox("排序方式", ["最新入庫", "最早入庫"])

    status_filter = st.multiselect("閱讀狀態", options=[s for s in BookStatus], format_func=lambda x: x.value)


    
    st.divider()
    st.caption(f"資料庫版本: v0.5 (Local)")

# B. 主畫面
col_stats, col_space, col_view = st.columns([4, 2, 3])

with col_stats:
    st.markdown(
        f"""
        <div style="
            display: flex; align-items: center; background: white; 
            padding: 8px 16px; border-radius: 8px; border: 1px solid #e8dcd5;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05); width: fit-content;
        ">
            <span style="font-size: 0.9rem; color: #5a5a5a;">總藏書 <b style="color: #a89080;">{total_count}</b></span>
            <span style="margin: 0 12px; color: #d9c9ba;">|</span>
            <span style="font-size: 0.9rem; color: #5a5a5a;">本月新增 <b style="color: #a89080;">{this_month_count}</b></span>
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

# --- 全域篩選 ---
filtered_books = all_books

if tag_filter:
    filtered_books = [b for b in filtered_books if any(tag in b.tags for tag in tag_filter)]
if status_filter:
    filtered_books = [b for b in filtered_books if b.status in status_filter]
if search_query:
    filtered_books = [b for b in filtered_books if search_query in b.title or search_query in b.author]
# 4. 二次排序邏輯 (依日期，同日期則依作者)
if sort_order == "最新入庫":
    # reverse=(True, False) 代表日期降序(最新在後)，作者升序(A-Z)
    filtered_books.sort(key=lambda x: (x.added_date, x.author), reverse=True)
else:
    filtered_books.sort(key=lambda x: (x.added_date, x.author), reverse=False)
# --- 視圖渲染 ---

if st.session_state.view_mode == "list":
    if st.session_state.selected_book:
        col_list, col_detail = st.columns([7, 3], gap="medium")
    else:
        col_list = st.container()
        col_detail = None

    with col_list:
        views.list_view.render_view(filtered_books)

    if st.session_state.selected_book and col_detail:
        with col_detail:
            with st.container(border=True):
                views.book_detail.render_detail_panel()

elif st.session_state.view_mode == "gallery":
    if st.session_state.selected_book:
        col_list, col_detail = st.columns([6, 4], gap="medium")
        gallery_cols = 4 
    else:
        col_list = st.container()
        col_detail = None
        gallery_cols = 6 
        
    with col_list:
        views.gallery_view.render_view(filtered_books, cols_num=gallery_cols)
        
    if st.session_state.selected_book and col_detail:
        with col_detail:
            with st.container(border=True):
                views.book_detail.render_detail_panel()

elif st.session_state.view_mode == "calendar":
    # 【新增】 日曆模式
    # 日曆模式下，若點擊書籍，我們使用 Dialog (st.dialog) 或是直接在下方顯示詳情
    # 但為了保持一致性，我們這裡可以暫時只顯示視圖，
    # 點擊日曆中的書會觸發 selected_book，我們可以選擇跳轉回 list/gallery 顯示詳情，
    # 或者直接在日曆下方顯示。這裡採用 Master-Detail 結構：
    
    if st.session_state.selected_book:
        col_cal, col_detail = st.columns([6, 4], gap="medium")
    else:
        col_cal = st.container()
        col_detail = None
        
    with col_cal:
        # 注意：日曆統計通常基於「所有書籍」而非「篩選後的書籍」，
        # 但為了彈性，我們傳入 filtered_books，這樣使用者可以用 Tag 篩選日曆內容
        views.calendar_view.render_view(filtered_books)
        
    if st.session_state.selected_book and col_detail:
        with col_detail:
            with st.container(border=True):
                views.book_detail.render_detail_panel()

# // 功能: 整合 Phase 5 閱讀軌跡功能
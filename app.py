# 修正 [app.py] 區塊 E: 移除分割視圖並整合彈窗 (Phase 3 Final)
# 修正原因：配合 Phase 3 彈窗化，移除舊的 Master-Detail 分割佈局，改為全寬度顯示並觸發 Dialog。
# 替換/新增指示：請完全替換 app.py 的內容。

import streamlit as st
import os
import math
from datetime import date
from modules.database import init_db
from modules.models import BookStatus
from modules import services
import views.list_view
import views.book_detail
import views.gallery_view 
import views.calendar_view

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

# 3. 初始化 Session State
if "init_done" not in st.session_state:
    init_db()
    st.session_state.init_done = True
    
if "selected_book" not in st.session_state:
    st.session_state.selected_book = None
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "list"

# 初始化分頁狀態
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "items_per_page" not in st.session_state:
    st.session_state.items_per_page = 20

load_css()

# --- Helper Functions (State Sync) ---

def update_page_state(new_page):
    """
    統一更新頁碼與 Widget 顯示狀態
    修正：同時清除選中的書籍，防止彈窗在換頁時自動彈出
    """
    st.session_state.current_page = new_page
    
    # 同步導航列輸入框
    st.session_state["nav_top_input"] = new_page
    st.session_state["nav_bottom_input"] = new_page
    
    # // 【關鍵修正點】 換頁時，視為使用者想看新列表，強制關閉/清除當前選中的書
    st.session_state.selected_book = None

def reset_page():
    """當篩選條件改變時，強制重置回第一頁"""
    update_page_state(1)

def change_page(delta, total_pages):
    target = st.session_state.current_page + delta
    if 1 <= target <= total_pages:
        update_page_state(target)

def set_page(page_num):
    update_page_state(page_num)

# --- 資料準備 ---
all_books = services.get_books()

total_count = len(all_books)
this_month_count = len([
    b for b in all_books 
    if b.added_date and b.added_date.year == date.today().year and b.added_date.month == date.today().month
])
all_tags = sorted(list(set(tag for book in all_books for tag in book.tags)))

# --- UI 結構: 側邊欄 ---
with st.sidebar:
    st.title("快速入庫")
    with st.form("quick_add_form", clear_on_submit=True):
        url_input = st.text_input("請輸入書籍網址", placeholder="支援：晉江 / 半夏 / 小說狂人")
        submitted = st.form_submit_button("啟動 AI 智慧抓取", use_container_width=True)
        if submitted and url_input:
            with st.spinner("🤖 正在爬取網頁並進行 AI 分析..."):
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
    
    st.title("顯示設定")
    try:
        st.pills("每頁顯示筆數", options=[10, 20, 50], key="items_per_page", on_change=reset_page)
    except AttributeError:
        st.radio("每頁顯示筆數", options=[10, 20, 50], horizontal=True, key="items_per_page", on_change=reset_page)

    st.divider()

    st.title("篩選器")
    search_query = st.text_input("關鍵字搜尋", placeholder="書名或作者...", on_change=reset_page)
    tag_filter = st.multiselect("標籤篩選", options=all_tags, default=[], on_change=reset_page)
    sort_order = st.selectbox("排序方式", ["最新入庫", "最早入庫"], on_change=reset_page)
    status_filter = st.multiselect("閱讀狀態", options=[s for s in BookStatus], format_func=lambda x: x.value, on_change=reset_page)
    
    st.divider()
    st.caption(f"資料庫版本: v0.7 (Dialog)")

# --- 主畫面頂部資訊 ---
col_stats, col_space, col_view = st.columns([4, 2, 3])
with col_stats:
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; background: white; 
            padding: 8px 16px; border-radius: 8px; border: 1px solid #e0e0e0;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05); width: fit-content;">
            <span style="font-size: 0.9rem; color: #5a5a5a;">總藏書 <b style="color: #a89080;">{total_count}</b></span>
            <span style="margin: 0 12px; color: #ddd;">|</span>
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
        label_visibility="collapsed",
        on_change=reset_page
    )
    st.session_state.view_mode = view_mode

st.divider()

# --- 資料過濾與排序 ---
filtered_books = all_books
if tag_filter:
    filtered_books = [b for b in filtered_books if any(tag in b.tags for tag in tag_filter)]
if status_filter:
    filtered_books = [b for b in filtered_books if b.status in status_filter]
if search_query:
    filtered_books = [b for b in filtered_books if search_query in b.title or search_query in b.author]

if sort_order == "最新入庫":
    filtered_books.sort(key=lambda x: (x.added_date, x.author), reverse=True)
else:
    filtered_books.sort(key=lambda x: (x.added_date, x.author), reverse=False)

# --- 分頁運算 ---
items_limit = st.session_state.items_per_page
total_items = len(filtered_books)
total_pages = math.ceil(total_items / items_limit) if total_items > 0 else 1

if st.session_state.current_page > total_pages:
    st.session_state.current_page = total_pages

start_idx = (st.session_state.current_page - 1) * items_limit
end_idx = start_idx + items_limit
current_page_books = filtered_books[start_idx:end_idx]

# --- 導航列元件 ---
def render_pagination(position="bottom"):
    """渲染混合式導航列"""
    if total_pages <= 1:
        return

    # 7 欄位佈局: [Spacer, First, Prev, InputArea, Next, Last, Spacer]
    _, c1, c2, c3, c4, c5, _ = st.columns([3, 0.8, 0.8, 1.8, 0.8, 0.8, 3], gap="small")
    
    key_prefix = f"nav_{position}"
    
    with c1:
        st.button("⏮", key=f"{key_prefix}_first", on_click=set_page, args=(1,), disabled=(st.session_state.current_page == 1), use_container_width=True)
    with c2:
        st.button("◀", key=f"{key_prefix}_prev", on_click=change_page, args=(-1, total_pages), disabled=(st.session_state.current_page == 1), use_container_width=True)
    
    with c3:
        col_in, col_lbl = st.columns([1.2, 1], gap="small")
        with col_in:
            def on_input_change():
                val = st.session_state[f"{key_prefix}_input"]
                if 1 <= val <= total_pages:
                    update_page_state(val)
            
            st.number_input(
                "Page", 
                min_value=1, 
                max_value=total_pages, 
                key=f"{key_prefix}_input", 
                label_visibility="collapsed",
                on_change=on_input_change
            )
        with col_lbl:
            st.markdown(f"<div style='padding-top: 6px; color: #5a5a5a; font-size: 0.9rem; white-space: nowrap;'>/ {total_pages}</div>", unsafe_allow_html=True)
            
    with c4:
        st.button("▶", key=f"{key_prefix}_next", on_click=change_page, args=(1, total_pages), disabled=(st.session_state.current_page == total_pages), use_container_width=True)
    with c5:
        st.button("⏭", key=f"{key_prefix}_last", on_click=set_page, args=(total_pages,), disabled=(st.session_state.current_page == total_pages), use_container_width=True)

# --- 視圖渲染 ---

# 1. 上方導航列
if total_items > 0 and st.session_state.view_mode in ["list", "gallery"]:
    render_pagination(position="top")
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

# 2. 主要內容區 (全寬度)
if st.session_state.view_mode == "list":
    views.list_view.render_view(current_page_books)

elif st.session_state.view_mode == "gallery":
    # 畫廊模式：全螢幕 5 欄
    views.gallery_view.render_view(current_page_books, cols_num=5)

elif st.session_state.view_mode == "calendar":
    # 日曆視圖通常不需分頁，傳入 filtered_books 即可
    views.calendar_view.render_view(filtered_books)

# 3. 下方導航列
if total_items > 0 and st.session_state.view_mode in ["list", "gallery"]:
    st.divider()
    render_pagination(position="bottom")

# --- 4. 詳情彈窗觸發區 (Phase 3 核心) ---
# 當使用者在列表/畫廊點擊按鈕設定 selected_book 後，這裡會偵測到並觸發彈窗
if st.session_state.selected_book:
    views.book_detail.render_detail_dialog()

# // 功能: 應用程式入口 (整合彈窗與全寬視圖)
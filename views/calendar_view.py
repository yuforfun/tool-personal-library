# 修正 [views/calendar_view.py] 區塊 B: 強制重置編輯狀態 (Reset on Open)
# 修正原因：確保從日曆點擊書籍時，也強制重置為唯讀模式。
# 替換/新增指示：請完全替換 views/calendar_view.py。

import streamlit as st
import calendar
from datetime import date
from modules.models import Book, BookStatus
from modules import stats_helper

def render_dashboard(books: list[Book]):
    """渲染數據儀表板 (Tab 1)"""
    # ... (儀表板邏輯保持不變，省略以節省篇幅，請保留原有的 kpi 計算與圖表) ...
    kpi = stats_helper.get_kpi_stats(books)
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📚 總藏書", kpi["total"])
        c2.metric("✅ 已完食", kpi["completed"])
        c3.metric("📅 本月戰績", f"+{kpi['this_month']}", help="本月新增的完食紀錄")
        c4.metric("⭐ 平均評分", f"{kpi['avg_rating']}")
    st.markdown("<br>", unsafe_allow_html=True)
    c_chart1, c_chart2 = st.columns([1, 1], gap="medium")
    with c_chart1:
        st.subheader("📈 月度閱讀量")
        st.caption(f"{date.today().year} 年度閱讀趨勢")
        df_monthly = stats_helper.get_monthly_completed_df(books, date.today().year)
        st.bar_chart(df_monthly, color="#a89080")
    with c_chart2:
        st.subheader("🏷️ 閱讀偏好 (Top 10)")
        st.caption("最常閱讀的標籤類型")
        df_tags = stats_helper.get_tag_distribution_df(books)
        if not df_tags.empty:
            st.bar_chart(df_tags, horizontal=True, color="#d9c9ba")
        else:
            st.info("尚無標籤數據，請多加幾本書吧！")

def render_calendar(books: list[Book]):
    """渲染互動式日曆 (Tab 2)"""
    if "cal_year" not in st.session_state:
        st.session_state.cal_year = date.today().year
        st.session_state.cal_month = date.today().month

    # ... (導航列邏輯保持不變) ...
    c_prev, c_title, c_next = st.columns([1, 6, 1])
    with c_prev:
        if st.button("◀", key="cal_prev"):
            st.session_state.cal_month -= 1
            if st.session_state.cal_month == 0:
                st.session_state.cal_month = 12
                st.session_state.cal_year -= 1
            st.rerun()
    with c_title:
        st.markdown(f"<h3 style='text-align: center; margin: 0; color: #5a5a5a;'>{st.session_state.cal_year} 年 {st.session_state.cal_month} 月</h3>", unsafe_allow_html=True)
    with c_next:
        if st.button("▶", key="cal_next"):
            st.session_state.cal_month += 1
            if st.session_state.cal_month == 13:
                st.session_state.cal_month = 1
                st.session_state.cal_year += 1
            st.rerun()
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    # ... (資料準備與格線渲染) ...
    daily_books = {}
    for book in books:
        if (book.status == BookStatus.COMPLETED and book.completed_date and 
            book.completed_date.year == st.session_state.cal_year and 
            book.completed_date.month == st.session_state.cal_month):
            d = book.completed_date.day
            if d not in daily_books: daily_books[d] = []
            daily_books[d].append(book)

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(st.session_state.cal_year, st.session_state.cal_month)
    
    cols = st.columns(7)
    weekdays = ["週日", "週一", "週二", "週三", "週四", "週五", "週六"]
    for i, w in enumerate(weekdays):
        cols[i].markdown(f"<div style='text-align: center; font-weight: bold; color: #8b7866; font-size: 0.9rem;'>{w}</div>", unsafe_allow_html=True)

    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
                    continue
                
                books_today = daily_books.get(day, [])
                bg_style = "background-color: #fcfaf8;" if books_today else "background-color: #ffffff;"
                border_style = "border: 1px solid #d9c9ba;" if books_today else "border: 1px solid #f0ebe6;"
                
                st.markdown(f"""
                <div style="min-height: 80px; {border_style} {bg_style} border-radius: 8px; padding: 4px; margin-bottom: 8px;">
                    <div style="font-size: 0.8rem; color: #aaa; text-align: right; margin-bottom: 4px;">{day}</div>
                """, unsafe_allow_html=True)
                
                for b in books_today:
                    # // 【關鍵修正點】 定義 Callback：同時設定書籍與重置編輯狀態
                    def select_cal_book(book=b):
                        st.session_state.selected_book = book
                        st.session_state.is_editing = False # 強制重置！
                    
                    btn_label = f"📕 {b.title[:4]}.." if len(b.title) > 4 else f"📕 {b.title}"
                    st.button(btn_label, key=f"cal_{day}_{b.id}", on_click=select_cal_book, use_container_width=True, help=f"完食：《{b.title}》")
                
                st.markdown("</div>", unsafe_allow_html=True)

def render_view(books: list[Book]):
    """日曆模式主入口"""
    tab1, tab2 = st.tabs(["📊 數據儀表板", "🗓️ 閱讀日曆"])
    with tab1: render_dashboard(books)
    with tab2: render_calendar(books)

# // 功能: 包含 KPI 儀表板與互動式日曆 (含狀態重置邏輯)
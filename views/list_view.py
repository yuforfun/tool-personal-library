import streamlit as st
from modules.models import Book, BookStatus

def render_status_badge(status: BookStatus):
    colors = {
        BookStatus.UNREAD: ("#e8dcd5", "#5a5a5a"), 
        BookStatus.READING: ("#a89080", "white"),  
        BookStatus.COMPLETED: ("#7ba08f", "white"),
        BookStatus.DROPPED: ("#b8a99a", "white"),  
    }
    bg, text = colors.get(status, ("#e8dcd5", "#5a5a5a"))
    
    return f"""
        <div style="
            background-color: {bg}; 
            color: {text}; 
            padding: 2px 8px; 
            border-radius: 6px; 
            font-size: 0.8rem; 
            font-weight: 600;
            display: inline-block;
            text-align: center;
            width: 100%;
        ">
            {status.value}
        </div>
    """

def render_rating(rating: int):
    if rating == 0:
        return '<span style="color: #b8a99a; font-size: 0.8rem;">-</span>'
    stars = "★" * rating
    return f'<span style="color: #d89c6f; font-size: 0.9rem; letter-spacing: 1px;">{stars}</span>'

def render_view(books: list[Book]):
    if not books:
        st.info("目前沒有書籍。請在左側貼上網址並點擊「啟動 AI 智慧抓取」來新增測試資料。")
        return

    # 表頭 (更緊湊)
    st.markdown("""
    <div style="display: flex; margin-bottom: 5px; color: #8b7866; font-size: 0.8rem; font-weight: bold; padding: 0 12px;">
        <div style="flex: 5;">書名 / 作者</div>
        <div style="flex: 2; text-align: center;">狀態</div>
        <div style="flex: 2; text-align: center;">評分</div>
        <div style="flex: 1; text-align: right;">編輯</div>
    </div>
    """, unsafe_allow_html=True)

    for book in books:
        with st.container(border=True):
            # 【關鍵修正】 調整欄位比例：5:2:2:1，讓最後一欄更窄，按鈕更靠右
            col1, col2, col3, col4 = st.columns([5, 2, 2, 1], gap="small")
            
            with col1:
                st.markdown(f"""
                <div style='line-height: 1.2;'>
                    <div style='font-size: 1rem; font-weight: bold; color: #5a5a5a; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'>{book.title}</div>
                    <div style='color: #8b7866; font-size: 0.75rem; margin-top: 2px;'>{book.author} · {book.word_count}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"<div style='margin-top: 2px;'>{render_status_badge(book.status)}</div>", unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"<div style='text-align: center; margin-top: 4px;'>{render_rating(book.user_rating)}</div>", unsafe_allow_html=True)
            
            with col4:
                # 使用 callback 直接設定 session_state
                def select_book(b=book):
                    st.session_state.selected_book = b
                
                # 按鈕寬度設為 container width 讓它填滿這 1 等份的空間
                st.button("📝", key=f"btn_{book.id}", on_click=select_book, use_container_width=True)
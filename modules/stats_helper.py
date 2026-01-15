# 新增 [modules/stats_helper.py] 區塊 A: 統計運算邏輯
# 修正原因：為儀表板提供數據清洗與計算功能 (KPI, Monthly Stats, Tag Distribution)。
# 替換/新增指示：這是全新檔案，請放置於 modules 資料夾。

import pandas as pd
from collections import Counter
from datetime import date
from .models import Book, BookStatus

def get_kpi_stats(books: list[Book]):
    """計算關鍵績效指標 (Dashboard KPI)"""
    total = len(books)
    completed = len([b for b in books if b.status == BookStatus.COMPLETED])
    
    # 計算本月完食
    today = date.today()
    this_month_completed = len([
        b for b in books 
        if b.status == BookStatus.COMPLETED 
        and b.completed_date 
        and b.completed_date.year == today.year 
        and b.completed_date.month == today.month
    ])
    
    # 計算平均評分 (排除 0 分/未評分的書籍)
    rated_books = [b for b in books if b.user_rating > 0]
    avg_rating = sum(b.user_rating for b in rated_books) / len(rated_books) if rated_books else 0.0
    
    return {
        "total": total,
        "completed": completed,
        "this_month": this_month_completed,
        "avg_rating": round(avg_rating, 1)
    }

def get_monthly_completed_df(books: list[Book], year: int) -> pd.DataFrame:
    """生成月度完食趨勢圖資料 (回傳 Pandas DataFrame)"""
    # 初始化 1-12 月數據 (確保圖表X軸完整)
    monthly_counts = {month: 0 for month in range(1, 13)}
    
    for book in books:
        if book.status == BookStatus.COMPLETED and book.completed_date and book.completed_date.year == year:
            monthly_counts[book.completed_date.month] += 1
            
    # 轉為 Streamlit 圖表所需的 DataFrame 格式
    # index 設為 "1月", "2月"...
    df = pd.DataFrame([
        {"月份": f"{m}月", "完食數量": c} 
        for m, c in monthly_counts.items()
    ])
    return df.set_index("月份")

def get_tag_distribution_df(books: list[Book], top_n=10) -> pd.DataFrame:
    """生成標籤分佈資料 (Top N)"""
    all_tags = []
    for book in books:
        # 排除空標籤
        if book.tags:
            all_tags.extend(book.tags)
        
    if not all_tags:
        return pd.DataFrame(columns=["標籤", "數量"])
        
    # 計算頻次
    counts = Counter(all_tags).most_common(top_n)
    df = pd.DataFrame(counts, columns=["標籤", "數量"])
    return df.set_index("標籤")

# // 功能: 數據統計輔助函式
# // input: Book 列表
# // output: 統計字典或 Pandas DataFrame
# 修正 [modules/data_manager.py] 區塊 B: CSV 全欄位支援與邏輯優化
# 修正原因：補齊 CSV 缺漏欄位 (簡介/AI分析)，使其具備完整編輯能力；優化匯入邏輯。
# 替換/新增指示：請完全替換 modules/data_manager.py。

import json
import pandas as pd
import uuid
from datetime import date
from typing import List, Dict, Any, Tuple
from .models import Book, BookStatus
from . import services
from . import database

# === 匯出功能 (Export) ===

def export_json() -> str:
    """匯出所有書籍為 JSON 字串 (完整備份用)"""
    books = services.get_books()
    books_data = [b.model_dump(mode='json') for b in books]
    return json.dumps(books_data, ensure_ascii=False, indent=2)

def export_csv() -> bytes:
    """
    匯出所有書籍為 CSV (Excel 可讀範本)
    修正：包含所有欄位，支援完整資料遷移
    """
    books = services.get_books()
    data_list = []
    
    for b in books:
        data_list.append({
            "標題": b.title,
            "作者": b.author,
            "網址": b.url,
            "狀態": b.status.value,
            "評分": b.user_rating,
            "標籤": ",".join(b.tags) if b.tags else "",
            "完食日期": b.completed_date,
            "心得": b.user_review,
            # [新增] 完整內容欄位，讓使用者可以用 Excel 編輯文案
            "AI簡介": b.ai_summary,
            "AI分析": b.ai_plot_analysis,
            "官方文案": b.official_desc,
            "入庫日期": b.added_date, # 參考用
            "來源": b.source
        })
    
    # 定義標準欄位順序
    cols = ["標題", "作者", "網址", "狀態", "評分", "標籤", "完食日期", "心得", "AI簡介", "AI分析", "官方文案", "入庫日期", "來源"]
    
    if not data_list:
        df = pd.DataFrame(columns=cols)
    else:
        df = pd.DataFrame(data_list, columns=cols)
        
    return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

# === 匯入功能 (Import) ===

def import_json(json_content: str) -> Dict[str, Any]:
    """從 JSON 還原資料庫"""
    try:
        data = json.loads(json_content)
        success = 0
        error = 0
        
        for item in data:
            try:
                book = Book(**item)
                database.insert_book(book)
                success += 1
            except Exception as e:
                print(f"JSON Import Error: {e}")
                error += 1
                
        return {"status": "success", "msg": f"還原成功 {success} 筆，失敗 {error} 筆"}
    except Exception as e:
        return {"status": "error", "msg": f"JSON 解析失敗: {str(e)}"}

def process_csv_import(file_buffer) -> Dict[str, Any]:
    """
    智慧處理 CSV 匯入 (增強版)
    支援：純網址爬取 OR 完整資料覆蓋
    """
    try:
        df = pd.read_csv(file_buffer)
        
        # 1. 欄位對應 (中英對照)
        col_map = {
            "標題": "title", "title": "title",
            "作者": "author", "author": "author",
            "網址": "url", "url": "url", "link": "url",
            "狀態": "status", "status": "status",
            "評分": "user_rating", "rating": "user_rating",
            "標籤": "tags", "tag": "tags", "tags": "tags",
            "完食日期": "completed_date", "date": "completed_date",
            "心得": "user_review", "review": "user_review",
            "AI簡介": "ai_summary", "summary": "ai_summary",
            "AI分析": "ai_plot_analysis", "analysis": "ai_plot_analysis",
            "官方文案": "official_desc", "desc": "official_desc",
            "來源": "source"
        }
        
        df.rename(columns=col_map, inplace=True)
        
        # 2. 模式判斷
        # 若無「title」欄位，視為「純網址匯入清單」
        is_full_import = "title" in df.columns
        
        if not is_full_import:
            if "url" not in df.columns:
                return {"status": "error", "msg": "CSV 格式錯誤：缺少「標題」或「網址」欄位。"}
            
            # 純網址模式
            urls = df["url"].dropna().astype(str).tolist()
            valid_urls = [u.strip() for u in urls if u.strip().startswith("http")]
            return {
                "status": "success",
                "mode": "crawl_list",
                "crawl_urls": valid_urls,
                "msg": f"解析出 {len(valid_urls)} 個網址"
            }
            
        else:
            # 完整匯入模式
            success = 0
            fail = 0
            
            for _, row in df.iterrows():
                try:
                    if pd.isna(row.get("title")): continue
                    
                    title = str(row["title"]).strip()
                    # 若只有標題沒網址，給空字串
                    url = str(row.get("url", "")).strip() 
                    if pd.isna(row.get("url")): url = ""

                    # 狀態轉換
                    status_str = str(row.get("status", "未讀")).strip()
                    status_enum = BookStatus.UNREAD
                    for s in BookStatus:
                        if s.value == status_str:
                            status_enum = s
                            break
                    
                    # 標籤轉換
                    tags_str = str(row.get("tags", ""))
                    if pd.isna(tags_str): tags_str = ""
                    tags_list = [t.strip() for t in tags_str.split(",") if t.strip()]
                    
                    # 數值與日期安全轉換
                    rating = 0
                    if "user_rating" in row and pd.notna(row["user_rating"]):
                        try:
                            rating = int(float(row["user_rating"]))
                        except: pass
                        
                    comp_date = None
                    if "completed_date" in row and pd.notna(row["completed_date"]):
                        try:
                            comp_date = pd.to_datetime(row["completed_date"]).date()
                        except: pass
                    
                    # 處理長文本 (處理 NaN)
                    def clean_str(val):
                        if pd.isna(val): return ""
                        return str(val).strip()

                    new_book = Book(
                        id=str(uuid.uuid4()), # 匯入皆視為新書 (可優化：若 URL 重複則更新)
                        title=title,
                        author=clean_str(row.get("author", "未知")),
                        url=url,
                        source=clean_str(row.get("source", "CSV匯入")),
                        status=status_enum,
                        tags=tags_list,
                        user_rating=rating,
                        user_review=clean_str(row.get("user_review")),
                        completed_date=comp_date,
                        added_date=date.today(),
                        # 如果 CSV 有提供就用，沒有就填預設
                        ai_summary=clean_str(row.get("ai_summary")) or "CSV 匯入資料",
                        official_desc=clean_str(row.get("official_desc")) or "由 CSV 匯入",
                        ai_plot_analysis=clean_str(row.get("ai_plot_analysis")) or "待補完 (請點擊重新分析)"
                    )
                    
                    database.insert_book(new_book)
                    success += 1
                    
                except Exception as e:
                    print(f"Row Import Failed: {e}")
                    fail += 1
            
            return {
                "status": "success", 
                "mode": "direct_insert",
                "inserted_count": success,
                "msg": f"匯入完成：成功 {success} 筆，失敗 {fail} 筆"
            }

    except Exception as e:
        return {"status": "error", "msg": f"CSV 讀取失敗: {str(e)}"}

# // 功能: 資料治理核心 (增強版 CSV 支援)
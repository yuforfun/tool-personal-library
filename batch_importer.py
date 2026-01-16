# 修正 [batch_importer.py] 區塊 G: 實作暴力防呆與括號清洗
# 修正原因：透過正則表達式移除書名中的括號與備註內容，確保比對時只針對核心書名，防止重複匯入。
# 替換/新增指示：請完全覆蓋 batch_importer.py。

import os
import time
import pandas as pd
import uuid
import random
import re
from datetime import datetime, date, timedelta
from difflib import SequenceMatcher
from opencc import OpenCC
from dataclasses import dataclass
from typing import Optional, List

from modules import scraper, ai_agent, database
from modules.scraper import RawBookData
from modules.models import Book, BookStatus

cc = OpenCC('s2twp')

# ==========================================
# 0. 使用者設定
# ==========================================
DATE_STRATEGY = "NONE" 
DEFAULT_RATING_SOURCE_B = 0 

# ==========================================
# 1. 資料結構與比對
# ==========================================
@dataclass
class CsvBookCandidate:
    title: str
    author: str
    url: str
    description_text: str
    user_rating: int
    status: BookStatus
    tags: List[str]
    original_source: str
    completed_date: Optional[date] = None

def normalize_text(text: str, aggressive=False) -> str:
    """
    正規化字串
    aggressive=True: 暴力模式，移除所有括號及其內容 (ex: "書名(全)" -> "書名")
    """
    if not text: return ""
    text = cc.convert(str(text))
    
    if aggressive:
        # 移除括號內的內容 (包含括號本身)
        # 支援: (), [], {}, 【】, （）
        text = re.sub(r'[\(\[\{【（].*?[\)\]\}】）]', '', text)
        # 移除常見後綴
        text = re.sub(r'(全文完|完結|連載中|番外)', '', text)

    # 移除標點與空白
    for char in [" ", "　", "，", ",", "《", "》", "【", "】", "[", "]", "「", "」", ":", "："]:
        text = text.replace(char, "")
        
    return text.lower()

def to_traditional(text: str) -> str:
    if not text: return ""
    return cc.convert(str(text))

def verify_identity(csv_book: CsvBookCandidate, scraped_data: RawBookData) -> tuple[bool, str]:
    # 作者比對
    csv_auth_norm = normalize_text(csv_book.author)
    web_auth_norm = normalize_text(scraped_data.author)
    
    if csv_auth_norm and web_auth_norm and "未知" not in csv_auth_norm and "未知" not in web_auth_norm:
        if csv_auth_norm != web_auth_norm:
            if csv_auth_norm not in web_auth_norm and web_auth_norm not in csv_auth_norm:
                return False, f"作者不符 (CSV: {csv_book.author} vs Web: {scraped_data.author})"

    # 標題比對 (開啟暴力清洗模式)
    csv_title_norm = normalize_text(csv_book.title, aggressive=True)
    web_title_norm = normalize_text(scraped_data.title, aggressive=True)
    
    # 計算相似度
    similarity = SequenceMatcher(None, csv_title_norm, web_title_norm).ratio()
    
    # 提高閥值到 0.7，因為已經做了暴力清洗，理論上要很像
    if similarity < 0.7 and (csv_title_norm not in web_title_norm) and (web_title_norm not in csv_title_norm): 
        return False, f"標題差異過大 ({csv_title_norm} vs {web_title_norm}, sim={similarity:.2f})"
        
    return True, "身份驗證通過"

# ==========================================
# 2. CSV 讀取器
# ==========================================
def get_legacy_date():
    if DATE_STRATEGY == "FIXED": return date(2025, 12, 31)
    elif DATE_STRATEGY == "RANDOM":
        start = date(2025, 1, 1)
        return start + timedelta(days=random.randrange((date(2025, 12, 31) - start).days))
    else: return None

def load_source_a_gaming(file_path: str) -> List[CsvBookCandidate]:
    try: df = pd.read_csv(file_path, encoding='utf-8')
    except: df = pd.read_csv(file_path, encoding='big5')
    candidates = []
    for _, row in df.iterrows():
        url = str(row.get('Link', ''))
        if url == 'nan': url = ""
        tag_raw = str(row.get('備註', ''))
        tags = [tag_raw.replace('【', '').replace('】', '').strip()] if (tag_raw and tag_raw != 'nan') else []
        candidates.append(CsvBookCandidate(
            title=str(row.get('書名', '未知標題')).strip(),
            author=str(row.get('作者', '未知作者')).strip(),
            url=url,
            description_text=str(row.get('評論', '')) if str(row.get('評論', '')) != 'nan' else "",
            user_rating=str(row.get('推薦度', '')).count('★'),
            status=BookStatus.COMPLETED,
            tags=tags,
            original_source="Gaming_CSV",
            completed_date=get_legacy_date()
        ))
    return candidates

def load_source_b_booklist(file_path: str) -> List[CsvBookCandidate]:
    try: df = pd.read_csv(file_path, encoding='utf-8')
    except: df = pd.read_csv(file_path, encoding='big5')
    candidates = []
    for _, row in df.iterrows():
        c_date = None
        d_str = str(row.get('日期', ''))
        if d_str and d_str != 'nan':
            try: c_date = datetime.strptime(d_str.strip(), '%Y/%m/%d').date()
            except: pass
        
        status = BookStatus.COMPLETED if (c_date or '完' in str(row.get('狀態', ''))) else BookStatus.UNREAD
        if status == BookStatus.COMPLETED and not c_date: c_date = get_legacy_date()

        tags = []
        t_col = str(row.get('類別Tag', ''))
        if t_col and t_col != 'nan':
            tags = [t.strip().replace('（', '(').replace('）', ')') for t in t_col.replace('，', ',').split(',') if t.strip()]

        url = str(row.get('來源', ''))
        if url == 'nan': url = ""
        candidates.append(CsvBookCandidate(
            title=str(row.get('書名', '未知標題')).strip(),
            author=str(row.get('作者', '未知作者')).strip(),
            url=url,
            description_text=str(row.get('文案', '')) if str(row.get('文案', '')) != 'nan' else "",
            user_rating=DEFAULT_RATING_SOURCE_B,
            status=status,
            tags=tags,
            original_source="Booklist_CSV",
            completed_date=c_date
        ))
    return candidates

# ==========================================
# 3. 主匯入邏輯
# ==========================================
def process_candidate(candidate: CsvBookCandidate, existing_books: dict, report_list: list):
    print(f"\n📘 正在處理：{candidate.title} / {candidate.author}")
    
    # --- 1. 暴力重複檢查 ---
    cand_key_norm = f"{normalize_text(candidate.title, aggressive=True)}_{normalize_text(candidate.author)}"
    
    for b in existing_books.values():
        # 如果網址完全一樣 -> 擋
        if candidate.url and "http" in candidate.url and b.url == candidate.url:
            print(f"   ⏭️ 跳過：網址已存在")
            return "SKIPPED_URL_EXIST"
            
        # 如果 書名+作者 (經過清洗) 一樣 -> 擋
        db_key_norm = f"{normalize_text(b.title, aggressive=True)}_{normalize_text(b.author)}"
        if cand_key_norm == db_key_norm:
             print(f"   ⏭️ 跳過：書名與作者已存在 ({b.title})")
             return "SKIPPED_TITLE_EXIST"

    # --- 2. 爬取與驗證 ---
    scraped_data = None
    verification_passed = False
    failure_reason = None
    is_egg_blog = "egg19910707" in candidate.url or "blog.fc2.com" in candidate.url
    
    if candidate.url and "http" in candidate.url and "drive.google" not in candidate.url:
        try:
            print(f"   🕷️ 嘗試爬取：{candidate.url[:40]}...")
            scraped_data = scraper.scrape_book(candidate.url)
            if scraped_data:
                passed, msg = verify_identity(candidate, scraped_data)
                if passed:
                    print(f"   ✅ 驗證成功")
                    verification_passed = True
                else:
                    print(f"   ⚠️ 驗證失敗：{msg}")
                    failure_reason = f"身份不符: {msg}"
                    verification_passed = False
            else:
                 print("   ⚠️ 爬蟲回傳空值")
                 failure_reason = "網站無法連線"
        except Exception as e:
            print(f"   ⚠️ 爬取異常 ({e})")
            failure_reason = f"爬蟲錯誤: {e}"
    elif candidate.url and "drive.google" in candidate.url:
        failure_reason = "Google Drive"

    if candidate.url and failure_reason and "http" in candidate.url and not is_egg_blog:
        report_list.append({
            "書名": candidate.title,
            "原始網址": candidate.url,
            "失敗原因": failure_reason
        })

    # --- 3. 資料準備 ---
    final_title = candidate.title
    final_author = candidate.author
    final_desc = ""
    final_url = ""
    final_source_name = "CSV匯入"
    
    if verification_passed and scraped_data:
        final_title = scraped_data.title
        final_author = scraped_data.author
        final_desc = scraped_data.description
        final_url = scraped_data.url
        final_source_name = scraped_data.source_name
    else:
        # 降級保護
        if is_egg_blog:
            final_url = candidate.url
            final_source_name = "Egg (保留)"
        else:
            final_url = ""
        
        if candidate.original_source == "Booklist_CSV":
            final_desc = candidate.description_text
    
    final_user_review = ""
    if candidate.original_source == "Gaming_CSV":
        final_user_review = candidate.description_text

    # --- 4. AI 決策 ---
    ai_prompt_desc = final_desc
    if final_user_review: ai_prompt_desc += f"\n{final_user_review}"
    
    ai_result = None
    if len(ai_prompt_desc) > 20: 
        raw_data_for_ai = RawBookData(title=final_title, author=final_author, description=ai_prompt_desc, source_name=final_source_name, url=final_url)
        try:
            time.sleep(1.0)
            ai_result = ai_agent.analyze_book(raw_data_for_ai)
        except: pass
    else:
        print("   🛑 資訊不足，跳過 AI 分析")

    final_tags = list(set(candidate.tags + (ai_result.tags if ai_result else [])))
    final_tags = [to_traditional(t) for t in final_tags]

    final_date = candidate.completed_date
    if DATE_STRATEGY == "NONE" and final_date is None:
        final_date = None 

    new_book = Book(
        id=str(uuid.uuid4()),
        title=to_traditional(final_title),
        author=to_traditional(final_author),
        source=to_traditional(final_source_name),
        url=final_url,
        status=candidate.status,
        tags=final_tags,
        ai_summary=to_traditional(ai_result.summary) if ai_result else "待補完 (請點擊重新分析)",
        official_desc=to_traditional(final_desc),
        ai_plot_analysis=to_traditional(ai_result.plot) if ai_result else "資訊不足，AI 暫未分析",
        added_date=date.today(),
        completed_date=final_date,
        user_rating=candidate.user_rating,
        user_review=to_traditional(final_user_review)
    )
    
    try:
        database.insert_book(new_book)
        print(f"   💾 入庫成功！(ID: {new_book.id[:6]})")
        return "SUCCESS"
    except Exception: return "DB_ERROR"

def main():
    database.init_db()
    existing_books = {b.id: b for b in database.get_all_books()}
    candidates = []
    if os.path.exists("source_a.csv"): candidates.extend(load_source_a_gaming("source_a.csv"))
    if os.path.exists("source_b.csv"): candidates.extend(load_source_b_booklist("source_b.csv"))

    if not candidates:
        print("⚠️ 找不到來源 CSV")
        return

    failure_report = []
    print(f"📊 開始匯入 {len(candidates)} 筆資料...")
    stats = {"SUCCESS": 0, "SKIPPED": 0, "ERROR": 0}
    
    for i, cand in enumerate(candidates):
        try:
            result = process_candidate(cand, existing_books, failure_report)
            if "SKIPPED" in result: stats["SKIPPED"] += 1
            elif result == "SUCCESS": stats["SUCCESS"] += 1
            else: stats["ERROR"] += 1
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            stats["ERROR"] += 1
            
    if failure_report:
        pd.DataFrame(failure_report).to_csv("import_failures.csv", index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    main()
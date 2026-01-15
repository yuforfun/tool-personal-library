# 新增 [test_ai_agent.py] 區塊 A: AI 模組獨立測試
# 修正原因：驗證爬蟲與 AI 模組的串接，並測試 gemini-2.5-pro 的回應效果。
# 替換/新增指示：這是新檔案，請放置於專案根目錄。

from modules.scraper import scrape_book
from modules.ai_agent import analyze_book
import sys
import io

# 強制設定標準輸出編碼為 utf-8 (避免 Windows 終端機亂碼)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    print("=== 開始進行 AI 毒舌書評測試 ===\n")
    
    # 測試網址：隨便挑一本看起來很套路的書來測試毒舌效果
    # 這裡預設使用剛剛測試過的晉江網址，您也可以換成其他的
    test_url = "https://www.banxia.la/books/349286.html" 
    
    # 1. 先爬蟲
    print(f"STEP 1: 爬取網頁 {test_url}")
    raw_data = scrape_book(test_url)
    
    if not raw_data:
        print("❌ 爬蟲失敗，無法進行 AI 分析")
        return

    print(f"✅ 爬取成功：{raw_data.title} / {raw_data.author}\n")

    # 2. 再 AI 分析
    print(f"STEP 2: 呼叫 Gemini-2.5-pro 進行毒舌分析...")
    ai_result = analyze_book(raw_data)
    
    if ai_result:
        print("\n" + "="*40)
        print(f"書名：{raw_data.title}")
        print("="*40)
        print(f"🏷️  標籤：{', '.join(ai_result.tags)}")
        print(f"😈 毒舌短評：{ai_result.summary}")
        print("-" * 40)
        print(f"📖 劇情摘要：\n{ai_result.plot}")
        print("="*40 + "\n")
    else:
        print("❌ AI 分析失敗")

if __name__ == "__main__":
    main()

# // 功能: AI 功能驗證腳本
# // input: 內建測試網址
# // output: 終端機列印 AI 毒舌評論
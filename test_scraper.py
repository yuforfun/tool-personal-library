# 新增 [test_scraper.py] 區塊 A: 獨立測試腳本 (Runner)
# 修正原因：提供一個乾淨的環境測試 modules/scraper.py，不依賴 Streamlit 介面。
# 替換/新增指示：這是新檔案，請放置於專案根目錄。

from modules.scraper import scrape_book

def main():
    print("=== 開始進行爬蟲模組測試 ===\n")
    
    # 這裡可以替換成您想測試的實際網址
    # 為了避免無效連結，請手動填入您目前想測試的網址
    test_urls = [
        "https://www.popo.tw/books/871979",
        "https://www.popo.tw/books/883652",
        
        # 範例 1: 晉江 (請填入一本您喜歡的晉江小說網址)
        # "",
        
        # 範例 2: 半夏
        # "https://www.banxia.co/...",

        # 範例 3: 小說狂人
        # "https://czbooks.net/n/...",
        
        # "https://www.bookwalker.com.tw/product/79083?srsltid=AfmBOoohX2ZeNvwAiHIF2zR3khZOMFR89AgGRiDWexMeCWUGyPSjHNaf",
        # "https://www.books.com.tw/products/0010625673?sloc=main",
        # "https://czbooks.net/n/cpg8epe",
        # "https://www.jjwxc.net/onebook.php?novelid=3370619",
        # "https://www.xbanxia.cc/books/13654.html",
        # "https://uukanshu.cc/book/8036/",
        # "https://ixdzs.tw/read/12386/",
        # "http://egg19910707.blog.fc2.com/blog-entry-12961.html#more",

    ]

    if not test_urls:
        print("⚠️ 警告：測試列表為空。")
        url = input("請輸入一個書籍網址進行測試: ").strip()
        if url:
            test_urls.append(url)
    
    for url in test_urls:
        print(f"\n測試網址: {url}")
        print("-" * 30)
        
        data = scrape_book(url)
        
        if data:
            print(f"✅ 抓取成功！")
            print(f"來源: {data.source_name}")
            print(f"書名: {data.title}")
            print(f"作者: {data.author}")
            print(f"簡介預覽 (前 100 字):")
            print(f"{data.description[:100]}...")
        else:
            print("❌ 抓取失敗")
            
    print("\n=== 測試結束 ===")

if __name__ == "__main__":
    main()

# // 功能: 爬蟲功能驗證腳本
# // input: 寫在 list 中的網址或手動輸入
# // output: 終端機列印抓取結果
# // 其他補充: 測試前請確保已安裝 requirements.txt
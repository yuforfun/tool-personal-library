# [tool-personal-library] - 專案情境總結 (v1.0)

## 1. 專案目標與核心功能
本專案為一個 **Local-First (本地優先)** 的個人數位圖書館，旨在解決網路小說（如晉江、半夏、小說狂人）缺乏統一管理介面、無封面視覺、以及閱讀軌跡難以追蹤的痛點。

* **核心價值**：透過自動化爬蟲與 AI 分析，將雜亂的網址轉化為結構化的書籍資料庫。
* **主要功能**：
    1.  **AI 智慧入庫**：輸入網址，自動抓取內文並生成標籤、短評與劇情分析 (Gemini AI)。
    2.  **視覺化管理**：提供類似 Figma 設計質感的列表、畫廊模式，解決網文無封面問題。
    3.  **閱讀成就追蹤**：透過互動式日曆與 KPI 儀表板，回顧每月的閱讀量與評分分佈。
    4.  **資料自主**：所有資料儲存於本地 SQLite，不依賴雲端服務，確保資料擁有權。

## 2. 系統架構與資訊流
本專案採用 Python **Streamlit** 框架開發，架構上遵循 **三層式架構 (3-Tier Architecture)** 變體，將 UI 表現層、業務邏輯層與資料存取層分離。

* **架構組成**：
    * **前端/介面層 (Presentation)**：Streamlit (`app.py`, `views/`) + 客製化 CSS (`styles.css`)。
    * **業務邏輯層 (Business Logic)**：Python Modules (`modules/services.py`, `scraper.py`, `ai_agent.py`)。
    * **資料層 (Data Layer)**：SQLite (`data/library.db`) + Pydantic Models (`modules/models.py`)。

* **典型資訊流**：

    * **流程一：書籍入庫 (Import)**
        1.  **UI**: 使用者在側邊欄輸入 URL -> 點擊「啟動 AI 智慧抓取」。
        2.  **Controller**: `app.py` 呼叫 `services.add_book(url)`。
        3.  **Scraper**: `scraper.py` 判斷網域策略 -> 抓取並回傳 `RawBookData`。
        4.  **AI Agent**: `ai_agent.py` 將 `RawBookData` 傳送至 Google Gemini -> 回傳 JSON 格式分析 (Tags, Summary)。
        5.  **DB**: `services.py` 整合資料 -> `database.py` 寫入 SQLite。
        6.  **UI**: 觸發 `st.toast` 顯示成功訊息並刷新頁面。

    * **流程二：檢視詳情 (Master-Detail View)**
        1.  **UI**: 使用者在列表/畫廊點擊「詳情」按鈕。
        2.  **State**: 更新 `st.session_state.selected_book` 為目標書籍物件。
        3.  **Render**: `app.py` 偵測到 State 變化 -> 觸發重繪，畫面分割為左右兩欄 (Split View) 或彈出層，呼叫 `views.book_detail.render_detail_panel()`。

    * **流程三：更新狀態 (Update Status)**
        1.  **UI**: 使用者在詳情面板修改狀態 (如：閱讀中 -> 已完食)。
        2.  **Logic**: 觸發 `services.update_book_status()`，若狀態為「已完食」，自動填入 `completed_date` 為今日。
        3.  **DB**: 呼叫 `database.update_book()` 寫入變更。
        4.  **UI**: 介面即時反映新狀態 Badge 顏色。

## 3. 專案檔案結構與職責

* **入口與配置**：
    * `app.py`: **[核心入口]** 負責路由控制、Session State 初始化、Global Layout (側邊欄、Top Bar) 與視圖切換邏輯。
    * `config/styles.css`: **[視覺規範]** 定義全站配色 (藕粉色系)、卡片陰影、輸入框樣式與去除 Streamlit 原生樣式的 Hack。
    * `.streamlit/secrets.toml`: **[機密]** 存放 Gemini API Key。

* **業務模組 (`modules/`)**：
    * `services.py`: **[業務中樞]** 串接 UI 與底層模組，處理如「入庫流程」、「狀態連動」等複合邏輯。
    * `scraper.py`: **[爬蟲策略]** 實作 Strategy Pattern。包含 `BaseScraper` 及針對 Jjwxc, Banxia, Czbooks 的具體實作。
    * `ai_agent.py`: **[AI 介面]** 封裝 Google GenAI SDK (`google-genai`)，負責 Prompt 組裝與 JSON 回傳處理。
    * `database.py`: **[資料存取]** 處理 SQLite 連線、Table 初始化、JSON 欄位序列化/反序列化。
    * `models.py`: **[資料模型]** 定義 `Book` (Pydantic Model) 與 `BookStatus` (Enum)。

* **視圖元件 (`views/`)**：
    * `list_view.py`: **[列表]** 使用 `st.container` + HTML/CSS 手刻卡片，取代原生 Dataframe 以呈現 Badge 與互動按鈕。
    * `book_detail.py`: **[詳情]** 採用「自然流動佈局」，包含 Sticky Header (操作區) 與可捲動的內容編輯區。
    * `gallery_view.py`: **[畫廊]** 實作分頁邏輯 (Pagination) 與動態生成 HTML 書封。
    * `calendar_view.py`: **[日曆]** 包含 KPI 統計區塊與互動式月曆渲染。

## 4. 模組溝通協議 (Module Interfaces)
由於本專案為 Monolithic App，API 定義為 Python Function Call 介面。

* **`modules.scraper.scrape_book(url: str) -> RawBookData`**
    * **功能**: 根據 URL 自動選擇對應爬蟲策略，回傳標準化原始資料。
    * **回傳**: `RawBookData(title, author, description, source_name, url)`
    * **例外**: 若爬取失敗回傳 `None` 或拋出 Exception。

* **`modules.ai_agent.analyze_book(raw_data: RawBookData) -> AIAnalysisResult`**
    * **功能**: 呼叫 Gemini 2.5 Flash 模型進行分析。
    * **輸入**: 包含書名與文案的原始資料物件。
    * **回傳**: `AIAnalysisResult(tags: List[str], summary: str, plot: str)`
    * **特點**: 強制輸出 JSON 格式。

* **`modules.database.insert_book(book: Book)` / `update_book(book: Book)`**
    * **功能**: 資料庫寫入操作。
    * **協議**: `tags` 欄位在寫入前會自動序列化為 JSON String，讀取時反序列化為 List。

## 5. 關鍵決策與歷史包袱 (重要)

1.  **詳情面板採用「自然流動佈局 (Natural Layout)」**：
    * **決策**：在 `views/book_detail.py` 中移除 `st.container(height=...)` 的固定高度限制。
    * **原因**：早期嘗試固定高度以模擬 App 內捲動，導致在不同螢幕解析度下，下方的 `st.text_area` (心得區) 會被截斷或無法顯示。改為自然流動雖然會讓整體頁面變長，但保證了元件的可見性與穩定性。

2.  **爬蟲採用「策略模式 (Strategy Pattern)」**：
    * **決策**：`modules/scraper.py` 不使用單一巨型函式，而是依網域拆分為 `JjwxcScraper`, `BanxiaScraper` 等類別。
    * **原因**：不同小說網站的 DOM 結構差異巨大且常變動，策略模式允許單獨維護某個網站的爬蟲而不影響其他功能。

3.  **UI 樣式採用 CSS Injection 而非原生元件參數**：
    * **決策**：在 `config/styles.css` 中大量使用 `!important` 覆蓋 Streamlit 預設樣式。
    * **原因**：Streamlit 原生元件樣式過於工程化（直角、藍色框），為了還原 Figma 的現代化設計（圓角、藕粉色系、卡片陰影），必須使用侵入式 CSS。

4.  **AI SDK 遷移**：
    * **決策**：使用 `google-genai` (New SDK) 而非舊版 `google.generativeai`。
    * **原因**：Google 已發布舊版棄用警告，新版 SDK 對 `Gemini 2.0/2.5` 模型的支援度更好，且 `Client` 物件管理更清晰。

## 6. 嚴格護欄 (Guard Rails) (最重要)

* **[禁止] 修改詳情面板的高度限制**：
    * **嚴格禁止**在 `views/book_detail.py` 的內容容器中加入 `height` 參數。這會導致輸入框在特定縮放比例下消失 (Regression: Phase 2 Debug 4)。
* **[禁止] 移除 `scraper.py` 中的 `DOMAIN_NAME_MAP`**：
    * 此對照表負責將 `69shuba.com` 轉譯為「69書吧」等中文名稱，移除將導致介面顯示醜陋的英文網域。
* **[禁止] 變更 `database.py` 的 JSON 序列化邏輯**：
    * SQLite 不支援 Array 型別，`tags` 欄位依賴 `json.dumps` 存入與 `json.loads` 讀出。若改為直接存取 List 會導致資料庫崩潰。
* **[禁止] 直接在 `app.py` 撰寫爬蟲或資料庫 SQL**：
    * 所有業務邏輯必須封裝在 `modules/services.py`，資料庫操作必須在 `modules/database.py`。`app.py` 僅負責 UI 呈現與路由。
* **[禁止] 提交 `.streamlit/secrets.toml` 到 Git**：
    * 該檔案包含 API Key，必須嚴格保留在 `.gitignore` 中。

---
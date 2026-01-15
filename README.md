```markdown
# 修正 [README.md] 區塊 A: 專案說明文件 (初始化專案文件)
# 修正原因：建立專案基礎文件，包含安裝、設定與執行指南。
# 替換/新增指示：這是全新檔案，請放置於專案根目錄。

# Personal Digital Library (tool-personal-library)

這是一個基於 **Local-First** 理念的個人數位圖書館工具，旨在解決網路小說（如晉江、半夏等）無封面、無統一管理的痛點。透過 **Streamlit** 構建介面，結合 **Python 爬蟲** 與 **Google Gemini AI**，實現自動化的書籍資訊整理、標籤生成與視覺化回顧。

## 核心功能

* **AI 智慧入庫**：貼上網址，自動爬取簡介，並透過 Gemini AI 生成毒舌短評與標準化標籤。
* **高效管理**：類似 Excel 的列表模式，支援多維度篩選與排序。
* **自動書封畫廊**：根據書籍標籤與氛圍，自動生成動態色塊封面，解決網文無圖問題。
* **閱讀日曆**：視覺化呈現每月的閱讀成就與評分分佈。
* **資料自主**：所有資料儲存於本地 SQLite (`data/library.db`)，無需擔心雲端服務終止。

## 技術架構

* **語言**: Python 3.10+
* **介面**: Streamlit
* **AI 模型**: Google Gemini Pro (透過 `google-generativeai`)
* **資料庫**: SQLite
* **爬蟲**: Requests + BeautifulSoup4
```
## 安裝指南

### 1. 環境設定 (Conda)

```bash
# 建立環境
conda create -n tool-personal-library python=3.10 -y

# 啟動環境
conda activate tool-personal-library

# 安裝依賴
pip install -r requirements.txt

```

### 2. API 金鑰設定

本專案使用 Google Gemini API。請在專案根目錄建立 `.streamlit/secrets.toml` 檔案（此檔案已被 `.gitignore` 排除，請勿上傳）：

```toml
# .streamlit/secrets.toml

[gemini]
api_key = "您的_GOOGLE_GEMINI_API_KEY"

```

### 3. Git 初始化

```bash
git init
git add .
git commit -m "Initial commit"

```

## 執行專案

在 `conda activate tool-personal-library` 狀態下執行：

```bash
streamlit run app.py

```

## 目錄結構

```text
tool-personal-library/
├── app.py                   # 主程式 (已完成 UI 路由與佈局)
├── requirements.txt         # 依賴 (已包含 beautifulsoup4, requests, google-generativeai)
├── data/library.db          # SQLite 資料庫
├── config/styles.css        # UI 樣式
├── views/
│   ├── list_view.py         # 列表視圖
│   └── book_detail.py       # 詳細資訊面板 (編輯/檢視)
└── modules/
    ├── models.py            # Pydantic 模型 (Book, BookStatus)
    ├── database.py          # SQLite 操作
    └── services.py          # 業務邏輯 (目前 add_book 使用的是 Mock Data)
```

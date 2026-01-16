# Personal Digital Library (tool-personal-library)

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![Python](https://img.shields.io/badge/python-3.10+-green) ![Streamlit](https://img.shields.io/badge/streamlit-1.40+-red)

這是一個基於 **Local-First (本地優先)** 理念的個人數位圖書館工具，旨在解決網路小說（如晉江、半夏、小說狂人）無封面、無統一管理的痛點。

透過 **Streamlit** 構建現代化介面，結合 **Python 策略模式爬蟲** 與 **Google Gemini 2.5 AI**，實現自動化的書籍資訊整理、標籤生成、毒舌短評與視覺化閱讀軌跡回顧。

## ✨ 核心功能

* **🤖 AI 智慧入庫**：
    * 支援 **晉江、半夏、小說狂人** 等網站網址。
    * 自動爬取書名與簡介，並透過 Gemini AI 生成標準化標籤、劇情分析與毒舌短評。
* **📋 高效管理 (List View)**：
    * 類似 Excel 的清單模式，支援狀態 (未讀/閱讀中/已完食) 與標籤的多維度篩選。
    * 客製化 HTML 卡片呈現，包含評分星星與狀態色塊。
* **🎨 自動書封畫廊 (Gallery View)**：
    * 解決網文無圖痛點，程式自動生成帶有書名與氛圍色的動態書封。
    * 支援分頁瀏覽。
* **📅 閱讀軌跡 (Calendar View)**：
    * **KPI 儀表板**：統計總藏書、本月完食量與閱讀偏好分佈。
    * **互動日曆**：視覺化呈現每月的「完食成就」，點擊日期即可回顧該書籍。
* **🔒 資料自主**：
    * 所有資料儲存於本地 SQLite (`data/library.db`)。
    * 支援 JSON 格式的標籤序列化儲存。

## 🛠️ 技術架構

* **語言**: Python 3.10+
* **介面**: Streamlit (搭配 CSS Injection 進行 UI 優化)
* **AI 模型**: Google Gemini 2.5 Flash (使用 `google-genai` New SDK)
* **資料庫**: SQLite
* **爬蟲**: Requests + BeautifulSoup4 (實作 Strategy Pattern)

## 🚀 安裝指南

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

本專案使用 Google Gemini API。請在專案根目錄建立 `.streamlit/secrets.toml` 檔案：

```toml
# .streamlit/secrets.toml

[gemini]
api_key = "您的_GOOGLE_GEMINI_API_KEY"

```

### 3. 啟動專案

```bash
streamlit run app.py

```

## 📂 目錄結構

```text
tool-personal-library/
├── app.py                   # [核心入口] 應用程式路由、狀態管理與全域 UI 佈局
├── requirements.txt         # 專案依賴清單
├── .streamlit/
│   ├── config.toml          # Streamlit 主題設定
│   └── secrets.toml         # API 金鑰 (Git Ignored)
├── config/
│   └── styles.css           # [UI] 客製化 CSS (還原 Figma 設計風格)
├── data/
│   └── library.db           # [Data] SQLite 資料庫 (自動生成)
├── modules/
│   ├── models.py            # [Data] Pydantic 資料模型與 Enums
│   ├── database.py          # [Data] 資料庫 CRUD 操作
│   ├── scraper.py           # [Logic] 策略模式爬蟲 (Jjwxc, Banxia, Czbooks)
│   ├── ai_agent.py          # [Logic] Gemini AI 串接 (google-genai SDK)
│   ├── services.py          # [Logic] 業務邏輯層 (整合爬蟲、AI 與 DB)
│   ├── stats_helper.py      # [Logic] 統計數據計算邏輯
│   └── ui_helper.py         # [UI] 輔助 HTML 生成器
└── views/
    ├── list_view.py         # [View] 列表清單元件
    ├── gallery_view.py      # [View] 書封畫廊元件
    ├── calendar_view.py     # [View] 閱讀日曆與儀表板元件
    └── book_detail.py       # [View] 書籍詳情與編輯面板 (自然流動佈局)

```

## 📝 版本紀錄

* **v1.0.0** (Current): 完成核心爬蟲、AI 分析、三大視圖 (列表/畫廊/日曆) 與 CRUD 功能。

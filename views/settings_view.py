# 修正 [views/settings_view.py] 區塊 B: 整合式介面與 AI 關鍵字修正
# 修正原因：移除 Tabs，改為一目瞭然的儀表板佈局；修正 AI 修復判定關鍵字。
# 替換/新增指示：請完全替換 views/settings_view.py。

import streamlit as st
import time
from modules import data_manager, services, ai_agent, scraper

def render_view():
    """渲染設定與管理頁面 (整合版)"""
    st.header("⚙️ 資料設定與管理")
    st.caption("在此管理您的數位資產，進行匯入匯出或系統維護。")
    
    st.divider()

    # === Part 1: 資料交換中心 (Data Exchange) ===
    st.subheader("1. 資料交換中心")
    
    col_csv, col_json = st.columns(2, gap="large")
    
    # --- 左側: 通用格式 (Excel/CSV) ---
    with col_csv:
        st.markdown("### 📊 Excel / CSV 通用格式")
        st.info("適合「批次編輯」、「資料遷移」或「爬蟲清單」。")
        
        # 1. 匯出
        csv_data = data_manager.export_csv()
        st.download_button(
            label="📥 下載 CSV 報表",
            data=csv_data,
            file_name="library_export.csv",
            mime="text/csv",
            use_container_width=True,
            help="包含所有欄位，您可以在 Excel 編輯後重新匯入。"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 2. 匯入
        st.markdown("#### 📤 匯入 CSV")
        csv_file = st.file_uploader("上傳 CSV", type=["csv"], key="csv_up", label_visibility="collapsed")
        
        if csv_file:
            result = data_manager.process_csv_import(csv_file)
            
            if result["status"] == "error":
                st.error(result["msg"])
            
            elif result["status"] == "success":
                mode = result.get("mode")
                
                if mode == "direct_insert":
                    st.success(f"✅ 資料寫入成功！{result['msg']}")
                    if st.button("🔄 重新整理列表", key="refresh_csv"):
                        st.rerun()
                        
                elif mode == "crawl_list":
                    urls = result.get("crawl_urls", [])
                    st.warning(f"📋 偵測到 {len(urls)} 個網址 (純爬蟲模式)")
                    
                    if st.button(f"🚀 開始批次抓取 ({len(urls)} 本)", type="primary", use_container_width=True):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        success_count = 0
                        
                        for i, url in enumerate(urls):
                            status_text.text(f"正在處理 ({i+1}/{len(urls)}): {url} ...")
                            try:
                                if services.add_book(url):
                                    success_count += 1
                            except: pass
                            progress_bar.progress((i + 1) / len(urls))
                            time.sleep(0.5)
                        
                        status_text.text("處理完成！")
                        st.success(f"🎉 批次結束：成功 {success_count} 本")
                        time.sleep(1)
                        st.rerun()

    # --- 右側: 系統備份 (JSON) ---
    with col_json:
        st.markdown("### 💾 系統完整備份 (JSON)")
        st.warning("適合「整機備份」或「還原」。包含系統 ID。")
        
        # 1. 匯出
        json_str = data_manager.export_json()
        st.download_button(
            label="📦 下載系統備份 (.json)",
            data=json_str,
            file_name="library_backup.json",
            mime="application/json",
            use_container_width=True
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 2. 還原
        st.markdown("#### ♻️ 系統還原")
        json_file = st.file_uploader("上傳備份檔", type=["json"], key="json_up", label_visibility="collapsed")
        
        if json_file:
            content = json_file.getvalue().decode("utf-8")
            if st.button("⚠️ 確認覆蓋/還原資料庫", type="primary", use_container_width=True):
                res = data_manager.import_json(content)
                if res.get("status") == "success":
                    st.success(res.get("msg"))
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(res.get("msg"))

    st.divider()

    # === Part 2: 系統維護 (System Ops) ===
    st.subheader("2. 系統批次維護")
    
    # 掃描條件修正：使用使用者指定的關鍵字
    target_keyword = "待補完 (請點擊重新分析)"
    
    books = services.get_books()
    # 邏輯：掃描 AI 分析欄位是否包含該關鍵字，或是空的
    target_books = [
        b for b in books 
        if not b.ai_plot_analysis 
        or target_keyword in b.ai_plot_analysis 
        or b.ai_summary == "CSV 匯入資料"
    ]
    
    col_ops_Info, col_ops_Action = st.columns([3, 1])
    
    with col_ops_Info:
        st.markdown("#### 🤖 AI 資料補全")
        if not target_books:
            st.success("✨ 目前資料庫健康，沒有需要修復的書籍。")
        else:
            st.info(f"🔍 掃描發現 **{len(target_books)}** 本書籍需要 AI 分析。")
            with st.expander("查看清單"):
                for b in target_books:
                    st.text(f"- {b.title}")

    with col_ops_Action:
        st.markdown("<br>", unsafe_allow_html=True)
        if target_books:
            if st.button(f"🚀 啟動修復 ({len(target_books)})", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_box = st.empty()
                success = 0
                
                for i, book in enumerate(target_books):
                    status_box.markdown(f"**正在分析**: {book.title} ...")
                    
                    # 嘗試重新爬取 + AI
                    raw_data = scraper.scrape_book(book.url)
                    if raw_data:
                        ai_res = ai_agent.analyze_book(raw_data)
                        if ai_res:
                            book.title = raw_data.title
                            book.author = raw_data.author
                            book.official_desc = raw_data.description
                            book.tags = ai_res.tags
                            book.ai_summary = ai_res.summary
                            book.ai_plot_analysis = ai_res.plot
                            services.save_book_changes(book)
                            success += 1
                    
                    progress_bar.progress((i + 1) / len(target_books))
                    time.sleep(1)
                
                status_box.success(f"✅ 修復完成！成功 {success} 本")
                time.sleep(2)
                st.rerun()

# // 功能: 設定頁面 UI (整合版)
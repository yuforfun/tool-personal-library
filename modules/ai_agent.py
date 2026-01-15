# 修正 [modules/ai_agent.py] 區塊 D: 遷移至 Google GenAI SDK (Final)
# 修正原因：響應 Google 官方棄用警告，遷移至 google-genai 新版 SDK。
# 新增功能：使用 Client 物件、types.GenerateContentConfig 進行設定。

from google import genai
from google.genai import types
import streamlit as st
import json
import os
import re
from typing import List, Optional
from pydantic import BaseModel
from .scraper import RawBookData

class AIAnalysisResult(BaseModel):
    tags: List[str]
    summary: str
    plot: str

def _get_api_key():
    try:
        return st.secrets["gemini"]["api_key"]
    except Exception:
        return os.getenv("GEMINI_API_KEY")

def analyze_book(raw_data: RawBookData) -> Optional[AIAnalysisResult]:
    api_key = _get_api_key()
    if not api_key:
        print("❌ 錯誤: 找不到 Gemini API Key")
        return None

    # 【遷移重點 1】 建立 Client 物件 (舊版是隱式 configure)
    client = genai.Client(api_key=api_key)
    
    model_name = "gemini-2.5-flash" # 先用目前新 SDK 支援度最穩定的 2.0 Flash 測試，確認後可改 2.5
    # 注意：如果您的帳號有權限使用 gemini-2.5-pro，也可以填入 "gemini-2.5-pro"

    # 【遷移重點 2】 設定檔改用 types.GenerateContentConfig
    # 新版 SDK 將 generation_config 和 safety_settings 整合在這裡
    config = types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.95,
        top_k=40,
        response_mime_type="application/json",
        
        # 安全設定：全面解除 (BLOCK_NONE)
        safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_NONE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_NONE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_NONE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_NONE"
            ),
        ]
    )

    try:
        prompt = f"""
        你是一位閱讀量豐富的資深小說愛好者。
        你對各類網文套路非常熟悉，品味中肯，擅長用精練的語言向朋友推薦或介紹書籍。
        
        請閱讀以下這本小說的資訊，並回傳 JSON 格式的分析結果。

        【書籍資訊】
        書名：{raw_data.title}
        作者：{raw_data.author}
        來源：{raw_data.source_name}
        文案：
        {raw_data.description}

        【任務要求】
        1. **tags (標籤)**：提取 3-6 個最核心的元素標籤（例如：重生, 系統, 甜寵, 娛樂圈, 懸疑, HE...）。請使用台灣讀者習慣的用語。
        2. **summary (精闢短評)**：
           - 這是要顯示在列表上的短評。
           - 用一句話 (40字內) 點評這本書的核心看點。
           - 風格要像一般讀者看完書後的真實感想。
        3. **plot (劇情摘要)**：
           - 用 150 字以內，客觀總結這本書的主線劇情。

        請直接回傳 JSON。
        """

        print(f"🤖 AI ({model_name}) 正在閱讀《{raw_data.title}》...")
        
        # 【遷移重點 3】 呼叫 client.models.generate_content
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )
        
        # 新版 SDK 其實有 response.parsed (如果我們定義了 schema)，
        # 但為了保持彈性處理 Markdown JSON，我們還是先讀 text 再手動 parse
        if not response.text:
            print("⚠️ AI 回應為空。")
            return None

        # 解析 JSON
        try:
            result_json = json.loads(response.text)
        except json.JSONDecodeError:
            # 清洗 Markdown 格式 (```json ... ```)
            clean_text = re.sub(r"```json|```", "", response.text).strip()
            result_json = json.loads(clean_text)
        
        return AIAnalysisResult(
            tags=result_json.get("tags", []),
            summary=result_json.get("summary", "AI 暫無評論"),
            plot=result_json.get("plot", "無法生成摘要")
        )

    except Exception as e:
        print(f"❌ AI 分析失敗: {e}")
        # 如果是 404，提示使用者可能需要確認模型名稱
        if "404" in str(e):
             print(f"💡 提示: 請確認模型名稱 '{model_name}' 是否對您的 API Key 開放。")
        return None

# // 功能: AI 分析代理人 (Google GenAI SDK 版)
# // input: RawBookData
# // output: AIAnalysisResult
# // 其他補充: 完全遷移至新版 SDK，架構更穩定
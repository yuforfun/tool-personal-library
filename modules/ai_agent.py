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
        1. 僅輸出 JSON 格式，嚴禁任何解釋性文字。
        2. 語系：繁體中文 (台灣)。
        3. 若簡介內容極少，請根據標題進行合理推測，若完全無法判斷請填入 "未知"。

        # Output 
        1. "tags": "類別", "背景", "屬性1", "屬性2,
        2. "summary": "40字內讀者視角評論",
        3. "plot": "150字內客觀劇情大綱"


        # Tagging Logic
        - 第一個標籤必須是【核心類別】(言情/非言情/耽美/輕小說/無CP/同人)。
        - 第二個標籤必須是【時代背景】(古代/現代/未來/民國/異世架空)。
        - 後續標籤為【核心屬性】(優先用: 重生, 系統, 甜寵, 虐戀, 破鏡重圓, 馬甲文, 娛樂圈, 校園, 職場, 種田文, 網遊, 豪門, 升級流, 救贖)。

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
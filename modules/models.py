# 修正 [modules/models.py] 區塊 A: 核心資料結構 (Data Models)
# 修正原因：使用 Pydantic 定義書籍物件與狀態 Enum，確保資料傳遞時的型別安全。
# 替換/新增指示：這是新檔案，請放置於 modules 資料夾。

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date

# 【關鍵修正點】 定義閱讀狀態列舉，防止 Magic String 錯誤
class BookStatus(str, Enum):
    UNREAD = "未讀"
    READING = "閱讀中"
    COMPLETED = "已完食"
    DROPPED = "棄坑"

class Book(BaseModel):
    """
    書籍資料模型 (移除字數版)
    """
    id: str = Field(..., description="UUID 主鍵")
    title: str
    author: str
    source: str = Field(default="未知來源")
    url: str
    # // 【關鍵修正點】 移除 word_count 與 chapters，由 ai_summary 負擔列表顯示
    status: BookStatus = Field(default=BookStatus.UNREAD)
    tags: List[str] = Field(default_factory=list)
    
    # AI 分析相關
    ai_summary: str = Field(default="", description="一句話短評")
    official_desc: str = Field(default="", description="官方文案")
    ai_plot_analysis: str = Field(default="", description="詳細劇情分析")
    
    # 使用者互動
    added_date: date = Field(default_factory=date.today)
    completed_date: Optional[date] = None
    user_rating: int = Field(default=0, ge=0, le=5)
    user_review: str = Field(default="")

    # // 功能: 定義書籍資料結構
    # // input: 無
    # // output: Pydantic Model Class
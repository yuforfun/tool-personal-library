# 修正 [modules/scraper.py] 區塊 I: 網域對照表優化 (Final)
# 修正原因：在不增加新 Class 的前提下，讓通用爬蟲能顯示漂亮的中文來源名稱。
# 新增功能：DOMAIN_NAME_MAP 對照表。

import requests
import cloudscraper
from bs4 import BeautifulSoup
from dataclasses import dataclass
from fake_useragent import UserAgent
import re
from urllib.parse import urlparse

# 定義統一的資料結構
@dataclass
class RawBookData:
    title: str
    author: str
    description: str
    source_name: str
    url: str

# --- 基礎爬蟲類別 ---
class BaseScraper:
    def parse(self, html_content: str, url: str) -> RawBookData:
        raise NotImplementedError

    def _clean_text(self, text: str) -> str:
        if not text: return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'&[a-zA-Z]+;', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _clean_title(self, raw_title: str) -> str:
        if not raw_title: return "未知標題"
        title = re.sub(r'[《》【】\[\]]', '', raw_title).strip()
        title = re.split(r'[|_]', title)[0].strip()
        seo_keywords = r"(小說|全文|閱讀|最新|章節|下載|txt|筆趣閣|半夏|晉江|起點|無彈窗|手機版|online|read)"
        pattern = fr"([-,\s]+.*{seo_keywords}.*$)"
        title = re.sub(pattern, "", title, flags=re.IGNORECASE).strip()
        if "," in title:
            parts = title.split(",")
            if len(parts) > 1 and len(parts[0]) > 1 and parts[0].strip() in parts[1]:
                title = parts[0].strip()
        return title

    def _clean_author(self, raw_author: str) -> str:
        if not raw_author or raw_author == "未知作者": return "未知作者"
        author = re.sub(r'^(作者|Author|著|编)\s*[：:︰]?\s*', '', raw_author, flags=re.IGNORECASE).strip()
        return author if author else "未知作者"

    def _is_spam_description(self, text: str) -> bool:
        spam_keywords = ["情節跌宕起伏", "扣人心弦", "免費提供", "清爽乾淨", "無彈窗", "最新章節", "全文閱讀"]
        count = 0
        for kw in spam_keywords:
            if kw in text: count += 1
        return count >= 2

    def _parse_info_from_text(self, text: str) -> dict:
        result = {"author": None, "description": None}
        author_match = re.search(r"作者[：:︰]\s*([^\s]+)", text)
        if author_match: result["author"] = author_match.group(1).strip()
        desc_match = re.search(r"(作品簡介|內容簡介|簡介)[：:︰]\s*(.*)", text, re.DOTALL)
        if desc_match:
            desc_text = desc_match.group(2).strip()
            if "最新章節" in desc_text: desc_text = desc_text.split("最新章節")[0].strip()
            result["description"] = desc_text
        return result

    def _extract_meta_data(self, soup, url):
        """增強版 Metadata 解析器 (含網域對照)"""
        
        # --- 1. 來源名稱解析 (Source Name) ---
        source_name = "未知來源"
        domain = ""
        try:
            domain = urlparse(url).netloc.replace("www.", "")
        except: pass

        # 【新增】網域對照表：在此維護您常用的網站名稱
        # 只要加在這裡，GenericScraper 就會自動顯示漂亮的中文名
        DOMAIN_NAME_MAP = {
            "ixdzs8.com": "愛下電子書",
            "tw.ixdzs8.com": "愛下電子書",
            "69shu.com": "69書吧",
            "69shuba.com": "69書吧",
            "sto.cx": "思兔閱讀",
            "sto520.com": "思兔閱讀",
            "qidian.com": "起點中文網",
            "popo.tw": "POPO原創",
            "books.com.tw": "博客來",
            # 您可以隨時在此追加...
        }

        # A. 優先查表
        if domain in DOMAIN_NAME_MAP:
            source_name = DOMAIN_NAME_MAP[domain]
        # B. 查 Meta og:site_name
        elif soup.find("meta", property="og:site_name"):
            meta_site = soup.find("meta", property="og:site_name").get("content")
            if meta_site: source_name = meta_site.strip()
        # C. 最後用網域
        elif domain:
            source_name = domain

        # --- 2. Title ---
        raw_title = ""
        meta_title = soup.find("meta", property="og:title")
        if meta_title: raw_title = meta_title.get("content", "")
        elif soup.title: raw_title = soup.title.string
        title = self._clean_title(raw_title)

        # --- 3. Author ---
        raw_author = "未知作者"
        for tag in [soup.find("meta", property="og:novel:author"), soup.find("meta", property="book:author"), soup.find("meta", attrs={"name": "author"})]:
            if tag and tag.get("content"):
                raw_author = tag["content"]
                break
        if raw_author == "未知作者" and "_" in raw_title:
             parts = raw_title.split("_")
             if len(parts) >= 3:
                 candidate = parts[1].strip()
                 if 1 < len(candidate) < 10: raw_author = candidate
        author = self._clean_author(raw_author)

        # --- 4. Description ---
        description = "無法抓取文案"
        meta_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content") and not self._is_spam_description(meta_desc["content"]):
            description = self._clean_text(meta_desc["content"])

        # --- 5. Blind Search ---
        if author == "未知作者" or description == "無法抓取文案":
            for selector in ["div.book-detail", "div.book-info", "div.detail", "div.intro", "div.main"]:
                element = soup.select_one(selector)
                if element:
                    full_text = self._clean_text(element.get_text())
                    parsed = self._parse_info_from_text(full_text)
                    if author == "未知作者" and parsed["author"]: 
                        author = self._clean_author(parsed["author"])
                    if description == "無法抓取文案" and parsed["description"]:
                        description = parsed["description"]
                        if description != "無法抓取文案": break

        return RawBookData(title, author, description, source_name, url)

# --- 具體策略: 晉江 (Jjwxc) ---
class JjwxcScraper(BaseScraper):
    def parse(self, html_content: str, url: str) -> RawBookData:
        soup = BeautifulSoup(html_content, 'lxml')
        try:
            title_tag = soup.find('h1', itemprop='name') or soup.find('span', class_='bigtext')
            title = self._clean_title(title_tag.get_text(strip=True)) if title_tag else None
            author_tag = soup.find('span', itemprop='author')
            author = self._clean_author(author_tag.get_text(strip=True)) if author_tag else None
            intro_tag = soup.find('div', id='novelintro')
            description = self._clean_text(intro_tag.get_text()) if intro_tag else None
            if title and description:
                description = description.replace("文案：", "").strip()
                return RawBookData(title, author or "未知", description, "晉江文學城", url)
        except: pass
        data = self._extract_meta_data(soup, url)
        data.source_name = "晉江文學城 (Meta)"
        return data

# --- 具體策略: 半夏 (Banxia) ---
class BanxiaScraper(BaseScraper):
    def parse(self, html_content: str, url: str) -> RawBookData:
        soup = BeautifulSoup(html_content, 'lxml')
        try:
            info_block = soup.find('div', class_='book-describe') or soup.find('div', class_='book-info')
            if info_block:
                title_tag = info_block.find('h1')
                title = self._clean_title(title_tag.get_text(strip=True)) if title_tag else None
                if title and "半夏小說" in title and len(title) < 6: title = None
                full_text = self._clean_text(info_block.get_text())
                parsed = self._parse_info_from_text(full_text)
                if title:
                    return RawBookData(
                        title=title,
                        author=self._clean_author(parsed["author"] or "未知作者"),
                        description=parsed["description"] or "無法抓取文案",
                        source_name="半夏小說",
                        url=url
                    )
        except Exception: pass 
        
        info_div = soup.find('div', class_='book-info') or soup.find('div', class_='detail')
        if info_div and not soup.find('div', class_='book-describe'):
            title_node = info_div.find('h1')
            title = self._clean_title(title_node.get_text(strip=True)) if title_node else "未知標題"
            author_tag = info_div.find('a', href=lambda x: x and '/author/' in x)
            author = self._clean_author(author_tag.get_text(strip=True)) if author_tag else "未知作者"
            desc_tag = soup.find('div', class_='intro') or soup.find('p', class_='intro')
            description = self._clean_text(desc_tag.get_text()) if desc_tag else "無法抓取文案"
            return RawBookData(title, author, description, "半夏小說", url)
        
        data = self._extract_meta_data(soup, url)
        data.source_name = "半夏小說 (Meta)"
        return data

# --- 具體策略: 小說狂人 (Czbooks) ---
class CzbooksScraper(BaseScraper):
    def parse(self, html_content: str, url: str) -> RawBookData:
        soup = BeautifulSoup(html_content, 'lxml')
        try:
            title = self._clean_title(soup.find('span', class_='title').get_text(strip=True))
            author = self._clean_author(soup.find('span', class_='author').get_text(strip=True))
            description = self._clean_text(soup.find('div', class_='description').get_text())
            return RawBookData(title, author, description, "小說狂人", url)
        except AttributeError:
            data = self._extract_meta_data(soup, url)
            data.source_name = "小說狂人 (Meta)"
            return data

# --- 通用爬蟲 (Generic) ---
class GenericScraper(BaseScraper):
    def parse(self, html_content: str, url: str) -> RawBookData:
        soup = BeautifulSoup(html_content, 'lxml')
        return self._extract_meta_data(soup, url)

# --- 工廠與主程式 ---
def _get_scraper(url: str) -> BaseScraper:
    if "jjwxc" in url: return JjwxcScraper()
    # 69shu 可以給半夏處理，也可以給 Generic，這裡看您偏好，Generic 其實也夠了
    elif "banxia" in url or "69shu" in url: return BanxiaScraper()
    elif "czbooks" in url: return CzbooksScraper()
    else: return GenericScraper()

def scrape_book(url: str) -> RawBookData:
    scraper_strategy = _get_scraper(url)
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    try:
        print(f"正在連線至: {url}...")
        response = scraper.get(url, timeout=15)
        response.raise_for_status()
        if "jjwxc" in url: response.encoding = 'gb18030'
        else: response.encoding = response.apparent_encoding
        return scraper_strategy.parse(response.text, url)
    except Exception as e:
        print(f"❌ 抓取失敗: {e}")
        return None

# // 功能: 爬蟲核心模組 (含網域對照表)
# // input: URL
# // output: RawBookData
# // 其他補充: 內建 DOMAIN_NAME_MAP，方便維護常用網站名稱
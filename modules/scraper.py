# 修正 [modules/scraper.py] 區塊 K: 增強作者解析 (Title by Author)
# 修正原因：解決類似 "書名 by 作者" 格式導致作者欄位為 "未知" 的問題。
# 新增功能：在 _extract_meta_data 中加入 Regex 反查邏輯，自動分離標題與作者。

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
    def perform_request(self, scraper, url: str):
        """執行網路請求的策略方法"""
        response = scraper.get(url, timeout=15)
        response.raise_for_status()
        if "jjwxc" in url:
            response.encoding = 'gb18030'
        else:
            response.encoding = response.apparent_encoding
        return response

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
        seo_keywords = r"(小說|全文|閱讀|最新|章節|下載|txt|筆趣閣|半夏|晉江|起點|無彈窗|手機版|online|read|fc2|blog)"
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
        spam_keywords = ["情節跌宕起伏", "扣人心弦", "免費提供", "清爽乾淨", "無彈窗", "最新章節", "全文閱讀", "密碼認證", "輸入管理人設定的密碼"]
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
        """增強版 Metadata 解析器"""
        source_name = "未知來源"
        domain = ""
        try:
            domain = urlparse(url).netloc.replace("www.", "")
        except: pass

        DOMAIN_NAME_MAP = {
            "ixdzs8.com": "愛下電子書",
            "tw.ixdzs8.com": "愛下電子書",
            "69shu.com": "69書吧",
            "69shuba.com": "69書吧",
            "sto.cx": "思兔閱讀",
            "sto520.com": "思兔閱讀",
            "qidian.com": "起點中文網",
            "popo.tw": "POPO原創",
            "fc2.com": "FC2部落格",
            "blog.fc2.com": "FC2部落格"
        }
        
        if domain in DOMAIN_NAME_MAP:
            source_name = DOMAIN_NAME_MAP[domain]
        else:
            for key, name in DOMAIN_NAME_MAP.items():
                if key in domain:
                    source_name = name
                    break
            if source_name == "未知來源" and domain:
                source_name = domain

        raw_title = ""
        meta_title = soup.find("meta", property="og:title")
        if meta_title: raw_title = meta_title.get("content", "")
        elif soup.title: raw_title = soup.title.string
        title = self._clean_title(raw_title)

        raw_author = "未知作者"
        for tag in [soup.find("meta", property="og:novel:author"), soup.find("meta", property="book:author"), soup.find("meta", attrs={"name": "author"})]:
            if tag and tag.get("content"):
                raw_author = tag["content"]
                break
        
        # 1. 嘗試從標題中的 '_' 解析 (舊有邏輯)
        if raw_author == "未知作者" and "_" in raw_title:
             parts = raw_title.split("_")
             if len(parts) >= 3:
                 candidate = parts[1].strip()
                 if 1 < len(candidate) < 10: raw_author = candidate
        
        author = self._clean_author(raw_author)

        # 2. 【新增】嘗試從標題中的 'by' 解析 (新邏輯)
        # 針對: "書名 by 作者" 或 "書名 BY 作者"
        if author == "未知作者":
            match = re.search(r'(.*)\s+by\s+(.*)', title, re.IGNORECASE)
            if match:
                potential_title = match.group(1).strip()
                potential_author = match.group(2).strip()
                # 簡單防呆：作者名字不應該太長
                if len(potential_author) > 1 and len(potential_author) < 20:
                    title = self._clean_title(potential_title)
                    author = self._clean_author(potential_author)

        description = "無法抓取文案"
        meta_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content") and not self._is_spam_description(meta_desc["content"]):
            description = self._clean_text(meta_desc["content"])

        if author == "未知作者" or description == "無法抓取文案":
            for selector in ["div.book-detail", "div.book-info", "div.detail", "div.intro", "div.main", "div.entry_body", "div.entry-content", "div.sub_main"]:
                element = soup.select_one(selector)
                if element:
                    full_text = self._clean_text(element.get_text())
                    parsed = self._parse_info_from_text(full_text)
                    if author == "未知作者" and parsed["author"]: 
                        author = self._clean_author(parsed["author"])
                    
                    blind_desc = parsed["description"]
                    if not blind_desc:
                        blind_desc = full_text
                    
                    if blind_desc and len(blind_desc) > len(description) and not self._is_spam_description(blind_desc):
                        description = blind_desc
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
                    return RawBookData(title, self._clean_author(parsed["author"] or "未知作者"), parsed["description"] or "無法抓取文案", "半夏小說", url)
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

# --- 具體策略: FC2 部落格 (含密碼破解) ---
class Fc2Scraper(BaseScraper):
    def perform_request(self, scraper, url: str):
        """處理 FC2 密碼登入"""
        print(f"    -> [FC2] 正在嘗試連線...")
        response = scraper.get(url, timeout=15)
        response.encoding = response.apparent_encoding 
        soup = BeautifulSoup(response.text, 'lxml')
        
        pass_input = soup.find('input', {'name': 'pass'})
        if pass_input:
            print(f"    -> [FC2] 偵測到密碼鎖，正在嘗試自動解鎖 (密碼: egg)...")
            payload = {'pass': 'egg', 'mode': 'secret'}
            for hidden in soup.find_all('input', type='hidden'):
                if hidden.get('name'):
                    payload[hidden.get('name')] = hidden.get('value')
            post_response = scraper.post(url, data=payload)
            post_response.encoding = post_response.apparent_encoding
            if 'name="pass"' not in post_response.text:
                print(f"    -> [FC2] ✅ 解鎖成功！")
                return post_response
            else:
                print(f"    -> [FC2] ❌ 解鎖失敗")
                return response
        return response

    def parse(self, html_content: str, url: str) -> RawBookData:
        soup = BeautifulSoup(html_content, 'lxml')
        data = self._extract_meta_data(soup, url)
        if data.description == "無法抓取文案" or self._is_spam_description(data.description):
            for selector in ['div.entry_body', 'div.entry-body', 'div.entry_content', 'div.main-content']:
                body = soup.select_one(selector)
                if body:
                    data.description = self._clean_text(body.get_text())
                    break
        return data

# --- 通用爬蟲 (Generic) ---
class GenericScraper(BaseScraper):
    def parse(self, html_content: str, url: str) -> RawBookData:
        soup = BeautifulSoup(html_content, 'lxml')
        return self._extract_meta_data(soup, url)

# --- 工廠與主程式 ---
def _get_scraper(url: str) -> BaseScraper:
    if "jjwxc" in url: return JjwxcScraper()
    elif "banxia" in url or "69shu" in url: return BanxiaScraper()
    elif "czbooks" in url: return CzbooksScraper()
    elif "fc2.com" in url: return Fc2Scraper()
    else: return GenericScraper()

def scrape_book(url: str) -> RawBookData:
    scraper_strategy = _get_scraper(url)
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    try:
        print(f"正在連線至: {url}...")
        response = scraper_strategy.perform_request(scraper, url)
        if response.status_code >= 400:
            print(f"連線錯誤: {response.status_code}")
            return None
        return scraper_strategy.parse(response.text, url)
    except Exception as e:
        print(f"❌ 抓取失敗: {e}")
        return None

# // 功能: 爬蟲核心模組 (Final: 增強作者解析)
# // input: URL
# // output: RawBookData
# // 其他補充: 支援 FC2 密碼登入 + 標題 "Title by Author" 自動解析
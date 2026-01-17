# 修正 [modules/scraper.py] 區塊 T: POPO 深度優化版
# 修正原因：
# 1. 根據使用者提供的原始碼，POPO 作者改從 Meta 抓取最準確。
# 2. 簡介改抓 div.book-intro 以取得完整內容 (非 Meta 的截斷版)。
# 3. 確保全形直線 `｜` 能被正確清洗。

import requests
import cloudscraper
from bs4 import BeautifulSoup
from dataclasses import dataclass
from fake_useragent import UserAgent
import re
from urllib.parse import urlparse
import json
from opencc import OpenCC

# 初始化轉換器
cc = OpenCC('s2t')

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
        headers = {}
        if "books.com.tw" in url:
             headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        response = scraper.get(url, headers=headers, timeout=15)
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
        return cc.convert(text.strip())

    def _clean_title(self, raw_title: str) -> str:
        if not raw_title: return "未知標題"
        
        # 1. 簡轉繁
        raw_title = cc.convert(raw_title)
        
        # 2. 去除符號 (包含全形直線 ｜)
        title = re.sub(r'[《》【】\[\]〈〉]', '', raw_title).strip()
        
        # 3. 分割網站後綴
        # POPO 標題通常是 "書名｜POPO小說原創"，這裡用 split 切割
        title = re.split(r'[|_｜]', title)[0].strip()
        
        seo_keywords = r"(小說|全文|閱讀|最新|章節|下載|txt|筆趣閣|半夏|晉江|起點|無彈窗|手機版|online|read|fc2|blog|博客來|誠品|eslite|books|bookwalker|套書|POPO|原創)"
        pattern = fr"([-,\s]+.*{seo_keywords}.*$)"
        title = re.sub(pattern, "", title, flags=re.IGNORECASE).strip()
        
        if "," in title:
            parts = title.split(",")
            if len(parts) > 1 and len(parts[0]) > 1 and parts[0].strip() in parts[1]:
                title = parts[0].strip()
        return title

    def _clean_author(self, raw_author: str) -> str:
        if not raw_author or raw_author == "未知作者": return "未知作者"
        raw_author = cc.convert(raw_author)
        
        author = re.sub(r'^(作者|Author|著|编|繪|譯|插畫)\s*[：:︰]?\s*', '', raw_author, flags=re.IGNORECASE).strip()
        if "BOOKWALKER" in author or "電子書" in author or "出版社" in author or "POPO" in author:
            return "未知作者"
        return author if author else "未知作者"

    def _is_spam_description(self, text: str) -> bool:
        spam_keywords = ["情節跌宕起伏", "扣人心弦", "免費提供", "最新章節", "全文閱讀", "密碼認證", "出版社：", "ISBN：", "出版日期：", "點數兌換"]
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

    def _extract_json_ld(self, soup):
        try:
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if not isinstance(data, list): data = [data]
                    for item in data:
                        if item.get('@type') in ['Book', 'Product', 'ItemPage', 'Novel']:
                            return item
                except: continue
        except: pass
        return None

    def _extract_meta_data(self, soup, url):
        source_name = "未知來源"
        domain = ""
        try:
            domain = urlparse(url).netloc.replace("www.", "")
        except: pass

        DOMAIN_NAME_MAP = {
            "ixdzs8.com": "愛下電子書", "tw.ixdzs8.com": "愛下電子書",
            "69shu.com": "69書吧", "69shuba.com": "69書吧",
            "sto.cx": "思兔閱讀", "sto520.com": "思兔閱讀",
            "popo.tw": "POPO原創",
            "fc2.com": "FC2部落格", "blog.fc2.com": "FC2部落格",
            "books.com.tw": "博客來", "bookwalker.com.tw": "BOOKWALKER"
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
        
        author = self._clean_author(raw_author)
        
        if author == "未知作者":
            match = re.search(r'(.*)\s+by\s+(.*)', title, re.IGNORECASE)
            if match:
                potential_title = match.group(1).strip()
                potential_author = match.group(2).strip()
                if len(potential_author) > 1 and len(potential_author) < 20:
                    title = self._clean_title(potential_title)
                    author = self._clean_author(potential_author)

        description = "無法抓取文案"
        meta_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content") and not self._is_spam_description(meta_desc.get("content")):
            description = self._clean_text(meta_desc["content"])

        if author == "未知作者" or description == "無法抓取文案":
            for selector in ["div.book-detail", "div.book-info", "div.detail", "div.intro", "div.main", "div.entry_body", "div.entry-content", "div.sub_main"]:
                element = soup.select_one(selector)
                if element:
                    full_text = self._clean_text(element.get_text())
                    parsed = self._parse_info_from_text(full_text)
                    if author == "未知作者" and parsed["author"]: author = self._clean_author(parsed["author"])
                    
                    blind_desc = parsed["description"]
                    if not blind_desc: blind_desc = full_text
                    if blind_desc and len(blind_desc) > len(description) and not self._is_spam_description(blind_desc):
                        description = blind_desc
                        if description != "無法抓取文案": break

        return RawBookData(title, author, description, source_name, url)

# --- 具體策略實作 ---
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

class Fc2Scraper(BaseScraper):
    def perform_request(self, scraper, url: str):
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

class BooksScraper(BaseScraper):
    def parse(self, html_content: str, url: str) -> RawBookData:
        soup = BeautifulSoup(html_content, 'lxml')
        json_data = self._extract_json_ld(soup)
        if json_data:
            title = json_data.get('name')
            author_data = json_data.get('author', [])
            author = "未知作者"
            if isinstance(author_data, list) and len(author_data) > 0:
                author = author_data[0].get('name')
            elif isinstance(author_data, dict):
                author = author_data.get('name')
            description = self._clean_text(json_data.get('description', ''))
            if description: 
                 return RawBookData(self._clean_title(title), self._clean_author(author), description, "博客來", url)

        title_tag = soup.select_one('div.mod_type02_t01 h1') or soup.select_one('h1')
        title = self._clean_title(title_tag.get_text(strip=True)) if title_tag else "未知標題"
        author_tag = soup.select_one('a[href*="adv_author"]') or soup.select_one('li.author a')
        author = self._clean_author(author_tag.get_text(strip=True)) if author_tag else "未知作者"
        
        description = "無法抓取文案"
        intro_h3 = soup.find(lambda tag: tag.name == "h3" and "內容簡介" in tag.get_text())
        if intro_h3:
            content_div = intro_h3.find_next("div", class_="content")
            if content_div: description = self._clean_text(content_div.get_text())
        
        if description == "無法抓取文案":
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc: description = self._clean_text(meta_desc.get("content"))

        return RawBookData(title, author, description, "博客來", url)

# --- 【最終定版】POPO 原創 (通用穩定版) ---
class PopoScraper(BaseScraper):
    def parse(self, html_content: str, url: str) -> RawBookData:
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 預設值
        title = "未知標題"
        author = "未知作者"
        description = "無法抓取文案"

        # --- 策略 1: Meta Keywords (最優先，最乾淨) ---
        # 適用於絕大多數正常頁面
        meta_kw = soup.find("meta", attrs={"name": "keywords"})
        if meta_kw:
            content = meta_kw.get("content", "")
            parts = [p.strip() for p in content.split(",") if p.strip()]
            
            if len(parts) >= 1:
                title = self._clean_title(parts[0])
            
            if len(parts) >= 2:
                potential = parts[1]
                ignore = ["輕小說", "愛情", "原創", "戰鬥", "冒險", "架空", "穿越", "重生"]
                if potential not in ignore and len(potential) < 20:
                    author = self._clean_author(potential)

        # --- 策略 2: 智慧補救 (當 Keywords 失效時) ---
        
        # 2.1 準備原始資料
        raw_page_title = soup.title.string if soup.title else ""
        meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
        raw_desc = meta_desc.get("content", "") if meta_desc else ""

        # 2.2 從簡介中逆向提取 (針對 Keywords 消失的特殊頁面)
        # 模式: "書名(作者)：..." 或 "書名（作者）：..."
        if author == "未知作者" and raw_desc:
            match = re.search(r'^(.+?)[（\(]([^）\)]+)[）\)]：', raw_desc)
            if match:
                potential_title = match.group(1).strip()
                potential_author = match.group(2).strip()
                
                # 如果標題還沒抓到，或者目前抓到的標題不完整，就用這個
                if title == "未知標題" or len(title) < len(potential_title):
                    title = self._clean_title(potential_title)
                
                if len(potential_author) < 20:
                    author = self._clean_author(potential_author)

        # 2.3 從網頁標題 (<title>) 補救
        if title == "未知標題" and raw_page_title:
            clean_page_title = re.split(r'[|_｜]', raw_page_title)[0].strip()
            
            # 如果作者已知，從標題中扣除作者
            if author != "未知作者" and author in clean_page_title:
                clean_page_title = clean_page_title.replace(f"（{author}）", "").replace(f"({author})", "").strip()
                title = self._clean_title(clean_page_title)
            
            # 如果作者未知，嘗試解析 "書名（作者）"
            elif author == "未知作者":
                match = re.search(r'^(.*)[（\(]([^）\)]+)[）\)]$', clean_page_title)
                if match:
                    potential_title = match.group(1).strip()
                    potential_author = match.group(2).strip()
                    if len(potential_author) < 10:
                        author = self._clean_author(potential_author)
                        title = self._clean_title(potential_title)
                    else:
                        title = self._clean_title(clean_page_title)
                else:
                    title = self._clean_title(clean_page_title)
            else:
                 title = self._clean_title(clean_page_title)

        # 2.4 DOM 作者補救 (最後防線)
        if author == "未知作者":
            author_tag = soup.select_one('.book-data a[href*="/users/"]') or \
                         soup.select_one('.book-info a[href*="/users/"]') or \
                         soup.select_one('.author-name a')
            if author_tag:
                author = self._clean_author(author_tag.get_text(strip=True))

        # 3. Description 最終確認
        # 優先抓 DOM (完整)，其次 Meta (截斷)
        dom_desc = soup.select_one('div.book-intro') or soup.select_one('div.book_intro')
        if dom_desc:
            description = self._clean_text(dom_desc.get_text())
        elif raw_desc:
            description = self._clean_text(raw_desc)

        return RawBookData(title, author, description, "POPO原創", url)

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
    elif "books.com.tw" in url: return BooksScraper()
    elif "bookwalker.com.tw" in url: return BookwalkerScraper()
    elif "popo.tw" in url: return PopoScraper()
    else: return GenericScraper()

def scrape_book(url: str) -> RawBookData:
    # 黑名單攔截
    if "eslite.com" in url or "qidian.com" in url:
        print(f"⚠️ 跳過不支援的網站: {url}")
        return None

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

# // 功能: 爬蟲核心模組 (Final: POPO+OpenCC+Blacklist)
# // input: URL
# // output: RawBookData
# // 其他補充: 完整支援 POPO 並優化標題清洗
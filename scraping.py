import re
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI 
from fastapi import HTTPException

from article import Article

# 상수 정의
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

SELECTORS = {
    'aitimes': {
        'title': {'tag': 'h3', 'attrs': {'class': 'heading'}},
        'content': {'tag': 'article', 'attrs': {'id': 'article-view-content-div'}},
    },
    'venturebeat': {
        'title': {'tag': 'h1', 'attrs': {'class': 'article-title'}},
        'content': {'tag': 'div', 'attrs': {'class': 'article-content'}},
    },
    'techcrunch': {
        'title': {'tag': 'h1', 'attrs': {'class': 'article-hero__title wp-block-post-title'}},
        'content': {'tag': 'div', 'attrs': {'class': 'entry-content wp-block-post-content is-layout-constrained wp-block-post-content-is-layout-constrained'}},
    },
    'zdnet': {
        'title': {'tag': 'h1', 'attrs': {'class': None}},
        'content': {'tag': 'div', 'attrs': {'class': 'view_cont'}},
    }
}

# OpenAI 클라이언트 초기화
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_current_month_and_week() -> tuple[int, int]:
    """현재 월과 주차를 반환"""
    today = datetime.today()
    current_month = today.month
    current_week = (today.day - 1) // 7 + 1
    return current_month, current_week

class NewsScraperBase:
    """뉴스 스크래핑 기본 클래스"""
    
    def __init__(self, site_key: str):
        self.site_key = site_key
        self.selectors = SELECTORS[site_key]
    
    async def fetch_html(self, article_url: str) -> BeautifulSoup:
        """URL에서 HTML을 비동기적으로 가져와 BeautifulSoup 객체로 반환"""
        async with aiohttp.ClientSession() as session:
            async with session.get(article_url, headers=HEADERS) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail=f"Failed to fetch news: {response.status}")
                html = await response.text()
                return BeautifulSoup(html, 'html.parser')

    async def extract_article_content(self, soup: BeautifulSoup) -> str:
        """본문 내용을 추출"""
        content_div = soup.find(
            self.selectors['content']['tag'], 
            self.selectors['content']['attrs']
        )
        if not content_div:
            raise HTTPException(status_code=404, detail='본문을 찾을 수 없습니다.')
        paragraphs = content_div.find_all('p')
        return "\n\n".join([p.get_text(strip=True) for p in paragraphs])

    async def extract_article_title(self, soup: BeautifulSoup) -> str:
        """기사 제목을 추출"""
        title = soup.find(
            self.selectors['title']['tag'], 
            self.selectors['title']['attrs']
        )
        if not title:
            raise HTTPException(status_code=404, detail='제목을 찾을 수 없습니다.')
        return title.get_text(strip=True)

    async def extract_date(self, soup: BeautifulSoup) -> str:
        """날짜 추출 (하위 클래스에서 구현)"""
        raise NotImplementedError

    async def summarize_article(self, content: str) -> str:
        """기사 내용을 요약"""
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """다음 기사 내용을 핵심만 두 문장으로 요약하되, 아래 형식과 조건을 반드시 지켜서 출력하세요.

조건:
1. 반드시 한국어로 작성하세요.
2. 각 문장은 앞에 '- '로 시작하며, 두 문장은 한 줄씩 차지해야 합니다.
3. 각 문장은 기사의 핵심적인 기술적 내용이나 영향력을 중심으로 간결하게 요약하세요.
4. 영어로 된 전문 용어는 원문 그대로 표기하되 필요한 경우 작은따옴표로 묶어주세요.

예시 형식:
- 앤트로픽은 AI 에이전트 간 상호 연결성과 보안성을 강화하는 'MCP'를 업데이트했고, 이는 AI 에이전트 연동을 위한 새로운 표준으로 자리잡고 있다.
- 이번 MCP 업데이트는 'OAuth 2.1', '스트리머블 HTTP', 'JSON-RPC 배칭', '도구 주석' 기능을 추가하여 상호작용 효율성과 보안성을 향상시켰다."""},
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"기사 요약 중 오류 발생: {str(e)}")
            return content

    async def scrape(self, article_url: str) -> Article:
        """기사 스크래핑 메인 메서드"""
        soup = await self.fetch_html(article_url)
        title = await self.extract_article_title(soup)
        content = await self.extract_article_content(soup)
        date = await self.extract_date(soup)
        content = await self.summarize_article(content)
        return Article(title=title, url=article_url, date=date, content=content)

class AITimesScraper(NewsScraperBase):
    """AI Times 스크래퍼"""
    
    async def extract_date(self, soup: BeautifulSoup) -> str:
        date_icon = soup.find('i', class_='icon-clock-o')
        if date_icon:
            date_item = date_icon.find_parent('li')
            if date_item:
                date_text = date_item.get_text(strip=True)
                date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2}) \d{2}:\d{2}', date_text)
                if date_match:
                    return f"{date_match.group(2)}/{date_match.group(3)}"
        return ''

class VentureBeatScraper(NewsScraperBase):
    """VentureBeat 스크래퍼"""
    
    async def extract_date(self, soup: BeautifulSoup) -> str:
        date_tag = soup.find('time', class_='the-time')
        if date_tag:
            date_text = date_tag.get_text(strip=True)
            try:
                date_extract = datetime.strptime(date_text, "%B %d, %Y %I:%M %p")
                return date_extract.strftime("%m/%d")
            except ValueError:
                pass
        return ''

class TechCrunchScraper(NewsScraperBase):
    """TechCrunch 스크래퍼"""
    
    async def extract_date(self, soup: BeautifulSoup) -> str:
        date_tag = soup.find('time', attrs={'datetime': True})
        if date_tag:
            datetime_value = date_tag['datetime']
            try:
                date_extract = datetime.fromisoformat(datetime_value)
                return date_extract.strftime("%m/%d")
            except ValueError:
                pass
        return ''

class ZDNetScraper(NewsScraperBase):
    """ZDNet 스크래퍼"""
    
    async def extract_date(self, soup: BeautifulSoup) -> str:
        date_tag = soup.find('p', class_='meta')
        if date_tag:
            date_text = date_tag.get_text(strip=True)
            try:
                input_date = date_text.split("입력 :")[1].split(" ")[0]
                date_extract = datetime.strptime(input_date, "%Y/%m/%d")
                return date_extract.strftime("%m/%d")
            except (ValueError, IndexError):
                pass
        return ''

# 스크래핑 함수들
async def scrape_aitimes(article_url: str) -> Article:
    """AI Times 기사 스크래핑"""
    scraper = AITimesScraper('aitimes')
    return await scraper.scrape(article_url)

async def scrape_venturebeat(article_url: str) -> Article:
    """VentureBeat 기사 스크래핑"""
    scraper = VentureBeatScraper('venturebeat')
    return await scraper.scrape(article_url)

async def scrape_techcrunch(article_url: str) -> Article:
    """TechCrunch 기사 스크래핑"""
    scraper = TechCrunchScraper('techcrunch')
    return await scraper.scrape(article_url)

async def scrape_zdnet(article_url: str) -> Article:
    """ZDNet 기사 스크래핑"""
    scraper = ZDNetScraper('zdnet')
    return await scraper.scrape(article_url)
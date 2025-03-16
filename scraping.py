import re
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup

from article import Article

# User-Agent 설정
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0'
}


async def fetch_html(article_url: str) -> BeautifulSoup:
    """URL에서 HTML을 비동기적으로 가져와 BeautifulSoup 객체로 반환"""
    async with aiohttp.ClientSession() as session:
        async with session.get(article_url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"오류: {response.status} 상태 코드")
            html = await response.text()
            return BeautifulSoup(html, 'html.parser')


async def extract_article_content(soup: BeautifulSoup, content_selector: dict) -> str:
    """본문 내용을 추출"""
    content_div = soup.find(content_selector.get('tag'), content_selector.get('attrs'))
    if not content_div:
        raise Exception('본문을 찾을 수 없습니다.')
    paragraphs = content_div.find_all('p')
    return "\n\n".join([p.get_text(strip=True) for p in paragraphs])


async def extract_article_title(soup: BeautifulSoup, title_selector: dict) -> str:
    """기사 제목을 추출"""
    title = soup.find(title_selector.get('tag'), title_selector.get('attrs'))
    if not title:
        raise Exception('제목을 찾을 수 없습니다.')
    return title.get_text(strip=True)


async def extract_date_aitimes(soup: BeautifulSoup) -> str:
    """Aitimes의 날짜를 추출"""
    date_icon = soup.find('i', class_='icon-clock-o')
    if date_icon:
        date_item = date_icon.find_parent('li')
        if date_item:
            date_text = date_item.get_text(strip=True)
            date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2}) \d{2}:\d{2}', date_text)
            if date_match:
                return f"{date_match.group(2)}/{date_match.group(3)}"
            else:
                print("날짜 형식에 맞는 데이터를 찾지 못했습니다.")
    print("날짜 정보를 찾을 수 없습니다.")
    return ''


async def extract_date_venturebeat(soup: BeautifulSoup) -> str:
    """VentureBeat의 날짜를 추출"""
    date_tag = soup.find('time', class_='the-time')
    if date_tag:
        date_text = date_tag.get_text(strip=True)
        try:
            date_extract = datetime.strptime(date_text, "%B %d, %Y %I:%M %p")
            return date_extract.strftime("%m/%d")
        except ValueError:
            print("날짜 형식이 맞지 않습니다.")
    print("시간 정보를 찾을 수 없습니다.")
    return ''


async def extract_date_techcrunch(soup: BeautifulSoup) -> str:
    """TechCrunch의 날짜를 추출"""
    date_tag = soup.find('time', attrs={'datetime': True})
    if date_tag:
        # HTML의 datetime 속성을 활용하여 날짜 정보 추출
        datetime_value = date_tag['datetime']
        try:
            # datetime 속성을 ISO 형식으로 처리
            date_extract = datetime.fromisoformat(datetime_value)
            return date_extract.strftime("%m/%d")
        except ValueError:
            print("날짜 형식이 맞지 않습니다.")
    print("시간 정보를 찾을 수 없습니다.")
    return ''


async def extract_date_zdnet(soup: BeautifulSoup) -> str:
    """ZDNet의 날짜를 추출"""
    date_tag = soup.find('p', class_='meta')
    if date_tag:
        # 텍스트에서 "입력 :YYYY/MM/DD" 부분을 찾기
        date_text = date_tag.get_text(strip=True)
        try:
            # "입력 :YYYY/MM/DD" 패턴에서 날짜를 추출
            input_date = date_text.split("입력 :")[1].split(" ")[0]
            date_extract = datetime.strptime(input_date, "%Y/%m/%d")
            # 원하는 형식으로 출력 (MM/DD)
            return date_extract.strftime("%m/%d")
        except (ValueError, IndexError):
            print("날짜 형식이 맞지 않거나 정보를 찾을 수 없습니다.")
    else:
        print("날짜 정보를 포함하는 태그를 찾을 수 없습니다.")
    return ''



async def scrape_aitimes(article_url: str) -> Article:
    """Aitimes에서 기사 스크래이핑"""
    soup = await fetch_html(article_url)
    article_title = await extract_article_title(soup, {'tag': 'h3', 'attrs': {'class': 'heading'}})
    article_content = await extract_article_content(soup,
                                                    {'tag': 'article', 'attrs': {'id': 'article-view-content-div'}})
    article_date = await extract_date_aitimes(soup)

    return Article(
        title=article_title,
        url=article_url,
        date=article_date,
        content=article_content
    )


async def scrape_venturebeat(article_url: str) -> Article:
    """VentureBeat에서 기사 스크래이핑"""
    soup = await fetch_html(article_url)
    article_title = await extract_article_title(soup, {'tag': 'h1', 'attrs': {'class': 'article-title'}})
    article_content = await extract_article_content(soup, {'tag': 'div', 'attrs': {'class': 'article-content'}})
    article_date = await extract_date_venturebeat(soup)

    return Article(
        title=article_title,
        url=article_url,
        date=article_date,
        content=article_content
    )


async def scrape_techcrunch(article_url: str) -> Article:
    """TechCrunch에서 기사 스크래이핑"""
    soup = await fetch_html(article_url)
    article_title = await extract_article_title(soup, {'tag': 'h1', 'attrs': {'class': 'article-hero__title wp-block-post-title'}})
    article_content = await extract_article_content(soup, {'tag': 'div', 'attrs': {'class': 'entry-content wp-block-post-content is-layout-constrained wp-block-post-content-is-layout-constrained'}})
    article_date = await extract_date_techcrunch(soup)

    return Article(
        title=article_title,
        url=article_url,
        date=article_date,
        content=article_content
    )


async def scrape_zdnet(article_url: str) -> Article:
    """zdnet에서 기사 스크래이핑"""
    soup = await fetch_html(article_url)
    article_title = await extract_article_title(soup, {'tag': 'h1', 'attrs': {'class': None}, 'parent': {'tag': 'div', 'attrs': {'class': 'news_head'}}})
    article_content = await extract_article_content(soup, {'tag': 'div', 'attrs': {'class': 'view_cont'}})
    article_date = await extract_date_zdnet(soup)

    return Article(
        title=article_title,
        url=article_url,
        date=article_date,
        content=article_content
    )
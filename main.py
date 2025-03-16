import json
from typing import List
import asyncio
import aiohttp
import csv
from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from scraping import scrape_aitimes, scrape_venturebeat, scrape_techcrunch, scrape_zdnet

app = FastAPI()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0'
}

templates = Jinja2Templates(directory="templates")

# 전역 변수로 URL 목록을 임시 저장
url_list: List[str] = []


@app.get("/", response_class=HTMLResponse)
def main(request: Request):
    """메인 페이지 렌더링"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/result")
async def result(file: UploadFile = File(...)):
    """CSV 파일에서 URL 목록을 읽어 전역 변수에 저장한 후 result.html로 리디렉션"""
    global url_list
    
    # CSV 파일 읽기
    content = await file.read()
    text = content.decode('utf-8-sig')  # UTF-8 with BOM 처리
    
    # 줄 단위로 분리하고 빈 줄 제거
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # URL 추출 (첫 번째 열)
    urls = []
    for line in lines:
        # 첫 번째 열만 추출 (쉼표가 있는 경우에도 첫 번째 부분만 사용)
        url = line.split(',')[0].strip()
        # BOM이나 다른 특수 문자 제거
        url = url.replace('\ufeff', '').strip()
        if url:
            urls.append(url)
            print(f"추출된 URL: {url}")  # 디버깅용 로그
    
    # URL 유효성 검사
    valid_urls = [url for url in urls if any(domain in url for domain in 
                  ['aitimes.com', 'aitimes.kr', 'venturebeat.com', 'techcrunch.com', 'zdnet.co.kr'])]
    
    print(f"유효한 URL 목록: {valid_urls}")  # 디버깅용 로그
    
    if not valid_urls:
        return RedirectResponse(url="/?error=no_valid_urls", status_code=302)
    
    url_list = valid_urls
    return RedirectResponse(url="/result_page", status_code=302)


@app.get("/result_page", response_class=HTMLResponse)
async def result_page(request: Request):
    """result.html 페이지 렌더링"""
    return templates.TemplateResponse("result.html", {"request": request})


@app.get("/result_stream")
async def result_stream():
    """SSE 엔드포인트: 저장된 URL 목록에 대해 비동기 작업 후 실시간 전송"""
    global url_list

    async def scrape_url(url):
        try:
            if "aitimes.com" in url or "aitimes.kr" in url:
                article = await scrape_aitimes(url)
            elif "venturebeat.com" in url:
                article = await scrape_venturebeat(url)
            elif "techcrunch.com" in url:
                article = await scrape_techcrunch(url)
            elif "zdnet.co.kr" in url:
                article = await scrape_zdnet(url)
            else:
                return {'error': f'The URL {url} is not supported', 'url': url}
            return {'title': article.title, 'date': article.date, 'content': article.content, 'url': article.url}
        except Exception as e:
            return {'error': str(e), 'url': url}

    async def event_stream():
        # 모든 URL에 대한 스크래핑 작업을 동시에 시작
        tasks = []
        for url in url_list:
            # 각 URL에 대해 처리 중 상태 전송
            yield f"data: {json.dumps({'status': 'processing', 'url': url}, ensure_ascii=False)}\n\n"
            # 스크래핑 작업 시작
            tasks.append(scrape_url(url))
        
        # 완료된 작업부터 결과 전송
        for completed_task in asyncio.as_completed(tasks):
            result = await completed_task
            yield f"data: {json.dumps({'status': 'completed', **result}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

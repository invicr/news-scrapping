import json
import asyncio
from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from scraping import scrape_aitimes, scrape_venturebeat, scrape_techcrunch, scrape_zdnet
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import os
import csv
import io

app = FastAPI()

# 전역 변수로 URL 목록 저장
url_list = []

# 정적 파일 서빙 설정 (디렉토리가 존재할 때만 마운트)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# 템플릿 설정
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """메인 페이지 렌더링"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/result")
async def result(file: UploadFile = File(...)):
    """CSV 파일에서 URL 목록을 읽어 전역 변수에 저장한 후 result.html로 리디렉션"""
    global url_list
    
    try:
        # CSV 파일 읽기
        content = await file.read()
        text = content.decode('utf-8-sig')  # UTF-8 with BOM 처리
        
        # 줄 단위로 분리하고 빈 줄 제거
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        
        # URL 추출 (첫 번째 열)
        urls = []
        for line in lines:
            # 쉼표로 분리하고 첫 번째 열만 가져오기
            parts = line.split(',')
            if parts:  # 빈 줄이 아닌 경우
                url = parts[0].strip().replace('\ufeff', '')  # BOM 제거
                if url and url.startswith(('http://', 'https://')):  # URL 형식 검사
                    urls.append(url)
        
        if not urls:
            raise HTTPException(status_code=400, detail="CSV 파일에 유효한 URL이 없습니다.")
        
        # URL 유효성 검사
        valid_urls = [url for url in urls if any(domain in url for domain in 
                    ['aitimes.com', 'aitimes.kr', 'venturebeat.com', 'techcrunch.com', 'zdnet.co.kr'])]
        
        if not valid_urls:
            raise HTTPException(status_code=400, detail="지원하는 도메인의 URL이 없습니다. (aitimes.com, venturebeat.com, techcrunch.com, zdnet.co.kr)")
        
        url_list = valid_urls
        return RedirectResponse(url="/result_page", status_code=302)
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV 파일이 UTF-8 형식이 아닙니다.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV 파일 처리 중 오류가 발생했습니다: {str(e)}")

@app.get("/result_page", response_class=HTMLResponse)
async def result_page(request: Request):
    """result_card.html 페이지 렌더링"""
    try:
        # 모든 뉴스 사이트에서 기사를 스크래핑
        tasks = []
        for url in url_list:
            if "aitimes.com" in url or "aitimes.kr" in url:
                tasks.append(scrape_aitimes(url))
            elif "venturebeat.com" in url:
                tasks.append(scrape_venturebeat(url))
            elif "techcrunch.com" in url:
                tasks.append(scrape_techcrunch(url))
            elif "zdnet.co.kr" in url:
                tasks.append(scrape_zdnet(url))
        
        articles = await asyncio.gather(*tasks)
        
        # 현재 날짜 포맷팅
        current_date = datetime.now().strftime("%Y년 %m월 %d일")
        
        return templates.TemplateResponse(
            "result_card.html",
            {
                "request": request,
                "articles": articles,
                "current_date": current_date
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

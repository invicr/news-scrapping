# 뉴스 스크래핑 및 요약 서비스

이 프로젝트는 다양한 뉴스 사이트에서 기사를 스크래핑하여 보여주는 웹 애플리케이션입니다.

## 주요 기능

- CSV 파일을 통한 URL 일괄 업로드
- 여러 뉴스 사이트 지원 (aitimes.com, aitimes.kr, venturebeat.com, techcrunch.com, zdnet.co.kr)
- 실시간 스크래핑 진행 상황 표시
- 뉴스 기사 정렬 및 삭제 기능
- 결과 페이지 HTML 복사 기능

## 설치 방법

1. 저장소 클론
```bash
git clone <repository-url>
cd news
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

## 실행 방법

```bash
uvicorn main:app --reload
```

서버가 시작되면 브라우저에서 `http://localhost:8000`으로 접속할 수 있습니다.

## 사용 방법

1. 메인 페이지에서 CSV 파일 업로드
   - CSV 파일은 첫 번째 열에 URL이 포함되어 있어야 합니다
   - 지원되는 도메인: aitimes.com, aitimes.kr, venturebeat.com, techcrunch.com, zdnet.co.kr

2. 결과 페이지에서 스크래핑 진행 상황 확인
   - 각 URL은 실시간으로 처리되며 결과가 표시됩니다
   - 처리 중인 URL은 스피너로 표시됩니다

3. 결과 관리
   - 기사를 드래그하여 순서 변경 가능
   - 기사에 마우스를 올리면 삭제 버튼이 표시됩니다
   - "페이지 복사" 버튼으로 결과를 HTML 형식으로 복사할 수 있습니다

## 기술 스택

- **Backend**: FastAPI, Python
- **Frontend**: HTML, CSS, JavaScript
- **Libraries**: 
  - BeautifulSoup4 (웹 스크래핑)
  - aiohttp (비동기 HTTP 요청)
  - Jinja2 (템플릿 렌더링)
  - Sortable.js (드래그 앤 드롭 정렬)

## 파일 구조

- `main.py`: 메인 애플리케이션 코드
- `scaping.py`: 뉴스 사이트별 스크래핑 로직
- `templates/`: HTML 템플릿 파일
  - `index.html`: 메인 페이지 (URL 입력)
  - `result.html`: 결과 페이지 (스크래핑 결과)
- `requirements.txt`: 의존성 목록

## 라이센스

MIT License 
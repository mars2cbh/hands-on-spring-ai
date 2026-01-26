# PDF 생성 스크립트

마크다운 챕터들을 하나의 PDF 책으로 변환합니다.

## 사전 요구사항

### macOS

```bash
# Pango 설치 (WeasyPrint 의존성)
brew install pango

# Python 패키지 설치
pip install -r requirements.txt
```

### Linux (Ubuntu/Debian)

```bash
# 시스템 패키지 설치
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0

# Python 패키지 설치
pip install -r requirements.txt
```

## 사용법

```bash
# 기본 사용 (output/ 폴더에 생성)
python generate_pdf.py

# 출력 경로 지정
python generate_pdf.py /path/to/output.pdf
```

## 출력

- **PDF 파일**: `output/바로_써먹는_Spring_AI_YYYYMMDD.pdf`
- **HTML 파일**: `output/book.html` (디버깅용)

## PDF 구성

1. **표지**: 책 표지 이미지
2. **저작권 페이지**: 저자, 출판사 정보
3. **목차**: Part 1 ~ 5 목록
4. **본문**: 각 챕터 내용 (이미지, 코드, 테이블 포함)

## 커스터마이징

### 스타일 수정

`generate_pdf.py` 파일의 `BOOK_CSS` 변수를 수정하여 PDF 스타일을 변경할 수 있습니다.

### 메타데이터 수정

`BOOK_METADATA` 딕셔너리에서 제목, 저자 등을 변경할 수 있습니다.

```python
BOOK_METADATA = {
    "title": "바로 써먹는 Spring AI",
    "subtitle": "실전 AI 애플리케이션 개발 가이드",
    "author": "황민호(Robin)",
    "publisher": "RevFactory",
    "year": "2026",
}
```

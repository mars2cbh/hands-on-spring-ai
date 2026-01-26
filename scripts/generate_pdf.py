#!/usr/bin/env python3
"""
바로 써먹는 Spring AI - PDF 생성 스크립트

이 스크립트는 마크다운 챕터들을 하나의 PDF 책으로 변환합니다.

필요한 패키지 설치:
    pip install markdown weasyprint pygments

macOS에서 weasyprint 설치 시:
    brew install pango
    pip install weasyprint
"""

import os
import sys
import markdown
from pathlib import Path
from datetime import datetime

# WeasyPrint import (PDF 생성용)
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
except ImportError:
    print("WeasyPrint가 설치되지 않았습니다.")
    print("설치 방법:")
    print("  macOS: brew install pango && pip install weasyprint")
    print("  Linux: apt-get install libpango-1.0-0 && pip install weasyprint")
    sys.exit(1)

# 프로젝트 경로 설정
BOOK_DIR = Path(__file__).parent.parent
CHAPTERS_DIR = BOOK_DIR / "chapters"
IMAGES_DIR = BOOK_DIR / "images"
OUTPUT_DIR = BOOK_DIR / "output"

# 챕터 순서
CHAPTERS = [
    "part1-foundation.md",
    "part2-prompt-engineering.md",
    "part3-function-calling.md",
    "part4-agentic-patterns.md",
    "part5-mcp.md",
]

# 책 메타데이터
BOOK_METADATA = {
    "title": "바로 써먹는 Spring AI",
    "subtitle": "실전 AI 애플리케이션 개발 가이드",
    "author": "황민호(Robin)",
    "publisher": "RevFactory",
    "year": "2026",
    "version": "최신 판",
}

# CSS 스타일 (책 스타일)
BOOK_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500&display=swap');

@page {
    size: A4;
    margin: 2.5cm 2cm 2.5cm 2cm;

    @top-center {
        content: string(chapter-title);
        font-size: 9pt;
        color: #666;
    }

    @bottom-center {
        content: counter(page);
        font-size: 10pt;
        color: #333;
    }
}

@page :first {
    @top-center { content: none; }
    @bottom-center { content: none; }
}

@page cover {
    margin: 0;
    @top-center { content: none; }
    @bottom-center { content: none; }
}

@page toc {
    @top-center { content: "목차"; }
}

* {
    box-sizing: border-box;
}

body {
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 11pt;
    line-height: 1.8;
    color: #333;
    text-align: justify;
    word-break: keep-all;
}

/* 표지 페이지 */
.cover-page {
    page: cover;
    page-break-after: always;
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: white;
    margin: -2.5cm -2cm;
    padding: 2cm;
}

.cover-page img {
    max-width: 70%;
    max-height: 60vh;
    margin-bottom: 2cm;
    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
}

.cover-page h1 {
    font-size: 28pt;
    font-weight: 700;
    margin: 0;
    color: #6DB33F;
}

.cover-page .subtitle {
    font-size: 14pt;
    margin-top: 0.5cm;
    color: #aaa;
}

.cover-page .author {
    font-size: 12pt;
    margin-top: 2cm;
    color: #ddd;
}

.cover-page .publisher {
    font-size: 10pt;
    margin-top: 0.5cm;
    color: #888;
}

/* 목차 페이지 */
.toc-page {
    page: toc;
    page-break-after: always;
}

.toc-page h1 {
    font-size: 24pt;
    text-align: center;
    margin-bottom: 1cm;
    color: #1a1a2e;
}

.toc-page ul {
    list-style: none;
    padding: 0;
}

.toc-page > ul > li {
    margin: 0.8cm 0;
    font-size: 12pt;
    font-weight: 500;
}

.toc-page > ul > li > ul {
    margin-top: 0.3cm;
    margin-left: 1cm;
}

.toc-page > ul > li > ul > li {
    font-size: 10pt;
    font-weight: 400;
    color: #555;
    margin: 0.2cm 0;
}

.toc-page a {
    color: inherit;
    text-decoration: none;
}

.toc-page a:hover {
    color: #6DB33F;
}

/* 챕터 스타일 */
.chapter {
    page-break-before: always;
}

.chapter:first-of-type {
    page-break-before: auto;
}

h1 {
    string-set: chapter-title content();
    font-size: 24pt;
    font-weight: 700;
    color: #1a1a2e;
    margin-top: 0;
    margin-bottom: 1cm;
    padding-bottom: 0.5cm;
    border-bottom: 3px solid #6DB33F;
    page-break-after: avoid;
}

h2 {
    font-size: 18pt;
    font-weight: 600;
    color: #16213e;
    margin-top: 1.5cm;
    margin-bottom: 0.5cm;
    page-break-after: avoid;
}

h3 {
    font-size: 14pt;
    font-weight: 600;
    color: #333;
    margin-top: 1cm;
    margin-bottom: 0.4cm;
    page-break-after: avoid;
}

h4 {
    font-size: 12pt;
    font-weight: 600;
    color: #444;
    margin-top: 0.8cm;
    margin-bottom: 0.3cm;
    page-break-after: avoid;
}

/* 코드 블록 */
pre {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-left: 4px solid #6DB33F;
    border-radius: 4px;
    padding: 1em;
    overflow-x: auto;
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 9pt;
    line-height: 1.5;
    page-break-inside: avoid;
}

code {
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 9pt;
    background: #f1f3f4;
    padding: 0.15em 0.4em;
    border-radius: 3px;
}

pre code {
    background: none;
    padding: 0;
}

/* 테이블 */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
    font-size: 10pt;
    page-break-inside: avoid;
}

th, td {
    border: 1px solid #ddd;
    padding: 0.6em 0.8em;
    text-align: left;
}

th {
    background: #f8f9fa;
    font-weight: 600;
    color: #1a1a2e;
}

tr:nth-child(even) {
    background: #fafafa;
}

/* 이미지 */
img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
    page-break-inside: avoid;
}

/* 인용문 */
blockquote {
    margin: 1em 0;
    padding: 0.8em 1.2em;
    background: #e8f5e9;
    border-left: 4px solid #6DB33F;
    border-radius: 0 4px 4px 0;
    font-style: normal;
    page-break-inside: avoid;
}

blockquote p {
    margin: 0;
}

/* 리스트 */
ul, ol {
    margin: 0.5em 0;
    padding-left: 1.5em;
}

li {
    margin: 0.3em 0;
}

/* 체크리스트 */
ul li {
    list-style-type: disc;
}

/* 강조 */
strong {
    font-weight: 600;
    color: #1a1a2e;
}

em {
    font-style: italic;
}

/* 링크 */
a {
    color: #6DB33F;
    text-decoration: none;
}

/* 수평선 */
hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 1.5em 0;
}

/* 저작권 페이지 */
.copyright-page {
    page-break-before: always;
    padding-top: 3cm;
}

.copyright-page h2 {
    font-size: 14pt;
    border: none;
    margin-bottom: 1cm;
}

.copyright-page p {
    font-size: 10pt;
    color: #666;
    margin: 0.3cm 0;
}
"""


def convert_markdown_to_html(md_content: str, base_path: Path) -> str:
    """마크다운을 HTML로 변환하고 이미지 경로를 절대 경로로 변환"""

    # 이미지 경로 변환 (상대 경로 -> 절대 경로)
    md_content = md_content.replace(
        "](../images/",
        f"]({IMAGES_DIR.as_uri()}/"
    )
    md_content = md_content.replace(
        "](images/",
        f"]({IMAGES_DIR.as_uri()}/"
    )

    # 마크다운 확장 기능 설정
    extensions = [
        'markdown.extensions.tables',
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc',
        'markdown.extensions.attr_list',
        'markdown.extensions.def_list',
    ]

    extension_configs = {
        'codehilite': {
            'css_class': 'highlight',
            'linenums': False,
        }
    }

    html = markdown.markdown(
        md_content,
        extensions=extensions,
        extension_configs=extension_configs
    )

    return html


def generate_cover_page() -> str:
    """표지 페이지 HTML 생성"""
    cover_image = IMAGES_DIR / "book-cover.png"
    cover_img_tag = ""

    if cover_image.exists():
        cover_img_tag = f'<img src="{cover_image.as_uri()}" alt="Book Cover">'

    return f"""
    <div class="cover-page">
        {cover_img_tag}
    </div>
    """


def generate_copyright_page() -> str:
    """저작권 페이지 HTML 생성"""
    return f"""
    <div class="copyright-page">
        <h2>{BOOK_METADATA['title']}</h2>
        <p><strong>{BOOK_METADATA['subtitle']}</strong></p>
        <br>
        <p>지은이: {BOOK_METADATA['author']}</p>
        <p>출판사: {BOOK_METADATA['publisher']}</p>
        <p>발행연도: {BOOK_METADATA['year']}년</p>
        <br><br>
        <p>이 책의 저작권은 저자에게 있습니다.</p>
        <p>이 책의 내용은 학습 목적으로 자유롭게 사용할 수 있습니다.</p>
        <br>
        <p>PDF 생성일: {datetime.now().strftime('%Y년 %m월 %d일')}</p>
    </div>
    """


def generate_toc(chapters_html: list) -> str:
    """목차 페이지 HTML 생성"""
    toc_items = []

    part_titles = {
        "part1-foundation.md": "Part 1: Spring AI 입문",
        "part2-prompt-engineering.md": "Part 2: 프롬프트 엔지니어링",
        "part3-function-calling.md": "Part 3: Function Calling과 도구 통합",
        "part4-agentic-patterns.md": "Part 4: Agentic Patterns",
        "part5-mcp.md": "Part 5: Model Context Protocol (MCP)",
    }

    for chapter_file in CHAPTERS:
        title = part_titles.get(chapter_file, chapter_file)
        toc_items.append(f"<li><a href='#{chapter_file}'>{title}</a></li>")

    return f"""
    <div class="toc-page">
        <h1>목차</h1>
        <ul>
            {''.join(toc_items)}
        </ul>
    </div>
    """


def load_chapters() -> list:
    """챕터 파일들을 로드하고 HTML로 변환"""
    chapters = []

    for chapter_file in CHAPTERS:
        chapter_path = CHAPTERS_DIR / chapter_file

        if not chapter_path.exists():
            print(f"경고: {chapter_file} 파일을 찾을 수 없습니다.")
            continue

        print(f"처리 중: {chapter_file}")

        with open(chapter_path, 'r', encoding='utf-8') as f:
            md_content = f.read()

        html_content = convert_markdown_to_html(md_content, chapter_path.parent)

        chapters.append({
            'file': chapter_file,
            'html': f'<div class="chapter" id="{chapter_file}">{html_content}</div>'
        })

    return chapters


def generate_full_html(chapters: list) -> str:
    """전체 HTML 문서 생성"""

    cover = generate_cover_page()
    copyright_page = generate_copyright_page()
    toc = generate_toc(chapters)
    chapters_html = '\n'.join([ch['html'] for ch in chapters])

    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{BOOK_METADATA['title']}</title>
    </head>
    <body>
        {cover}
        {copyright_page}
        {toc}
        {chapters_html}
    </body>
    </html>
    """


def generate_pdf(output_path: Path):
    """PDF 파일 생성"""

    print("=" * 50)
    print(f"📚 {BOOK_METADATA['title']} PDF 생성")
    print("=" * 50)

    # 출력 디렉토리 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 챕터 로드
    print("\n📖 챕터 로드 중...")
    chapters = load_chapters()

    if not chapters:
        print("오류: 로드된 챕터가 없습니다.")
        sys.exit(1)

    # HTML 생성
    print("\n📝 HTML 생성 중...")
    full_html = generate_full_html(chapters)

    # HTML 파일 저장 (디버깅용)
    html_output = OUTPUT_DIR / "book.html"
    with open(html_output, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"   HTML 저장: {html_output}")

    # PDF 생성
    print("\n📄 PDF 생성 중...")
    font_config = FontConfiguration()

    html = HTML(string=full_html, base_url=str(BOOK_DIR))
    css = CSS(string=BOOK_CSS, font_config=font_config)

    html.write_pdf(
        output_path,
        stylesheets=[css],
        font_config=font_config
    )

    print(f"\n✅ PDF 생성 완료: {output_path}")
    print(f"   파일 크기: {output_path.stat().st_size / 1024 / 1024:.2f} MB")


def main():
    """메인 함수"""

    # 기본 출력 파일명
    timestamp = datetime.now().strftime('%Y%m%d')
    output_filename = f"바로_써먹는_Spring_AI_{timestamp}.pdf"
    output_path = OUTPUT_DIR / output_filename

    # 명령행 인자로 출력 경로 지정 가능
    if len(sys.argv) > 1:
        output_path = Path(sys.argv[1])

    generate_pdf(output_path)


if __name__ == "__main__":
    main()

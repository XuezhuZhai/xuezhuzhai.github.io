"""把 articles.xlsx 转换成文章列表 HTML，保存到 articles_output.html。

用法：python excel_to_html.py
然后把 articles_output.html 的全部内容，粘贴到 index.html 的两行 ARTICLES 标记之间。
需要 openpyxl：pip install openpyxl
"""
import sys
from html import escape
from pathlib import Path

from openpyxl import load_workbook

SITE = Path(__file__).resolve().parent
EXCEL_FILE = SITE / "articles.xlsx"
OUTPUT_FILE = SITE / "articles_output.html"
ME = "Zhai, X."  # 作者中需要高亮的名字

CARD = """        <div class="paper-card" onclick="togglePaper(this)">
          <div class="p-thumb">
            <div class="p-art" style="width:100px; height:70px; overflow:hidden; transition: all 0.3s;">{cover}</div>
          </div>
          <div class="p-meta">
            <div class="p-meta-body">
              <p class="p-venue">{venue}</p>
              <p class="p-title"><span class="t-en">{title_en}</span><span class="t-zh">{title_zh}</span></p>
              <p class="p-authors">{authors}</p>
            </div>{link}
            <div class="expand-btn"><svg viewBox="0 0 10 10" fill="none"><path d="M5 1v8M1 5h8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg></div>
          </div>
          <div class="p-abstract">
            <div class="p-abstract-inner">
              <div class="abs-lang-btns"></div>
              <div class="p-highlights-container">{highlights}{graphical_abstract}
              </div>
            </div>
          </div>
        </div>
"""

COVER = '\n              <img src="{}" alt="Paper Preview" style="width:100%; height:100%; object-fit: cover; display: block; transition: all 0.3s;">\n            '

LINK = """
            <div class="pill-links">
              <a href="{}" target="_blank" class="pill">
                <span class="t-en">Journal Website</span>
                <span class="t-zh">访问期刊官网</span>
              </a>
            </div>"""

HIGHLIGHTS = """
                <p class="p-highlights-label">
                  <span class="t-en">Research Highlights</span>
                  <span class="t-zh">研究亮点</span>
                </p>
                <div class="t-en"><ul class="highlights-list">{en}</ul></div>
                <div class="t-zh"><div style="display: block; width: 100%;"><ul class="highlights-list">{zh}</ul></div></div>"""

GRAPHICAL_ABSTRACT = """
                <div class="p-graphical-abstract"><img src="{}" alt="Graphical Abstract"></div>"""


def text(row, key):
    value = row.get(key)
    return "" if value is None else str(value).strip()


def list_items(value):
    return "".join(f"<li>{escape(line.strip())}</li>" for line in value.splitlines() if line.strip())


def read_rows():
    sheet = load_workbook(EXCEL_FILE, read_only=True, data_only=True)["articles"]
    rows = sheet.iter_rows(values_only=True)
    headers = next(rows)
    return [dict(zip(headers, values)) for values in rows if any(v not in (None, "") for v in values)]


def web_image(name):
    # 网页用 prepare_media.py 生成的低清版本
    return f"media/{Path(name).stem}.jpg"


def check_image(name, row_number, warnings):
    # 比较完整文件名：Windows 不区分大小写，但 GitHub Pages 区分
    if name and name not in {p.name for p in SITE.iterdir()}:
        warnings.append(f"第 {row_number} 行：找不到图片 {name}（注意大小写和扩展名）")


def render(row, row_number, warnings):
    title_en = text(row, "title_en")
    title_zh = text(row, "title_zh")
    if not title_en and not title_zh:
        warnings.append(f"第 {row_number} 行：没有标题")

    link = text(row, "link")
    if link and not link.lower().startswith(("http://", "https://")):
        warnings.append(f"第 {row_number} 行：链接不以 http 开头，已跳过：{link}")
        link = ""

    cover = text(row, "cover")
    abstract = text(row, "graphical_abstract")
    check_image(cover, row_number, warnings)
    check_image(abstract, row_number, warnings)

    en = list_items(text(row, "highlights_en"))
    zh = list_items(text(row, "highlights_zh"))
    venue = f"{text(row, 'journal')} · ({text(row, 'year')}) {text(row, 'volume')}".strip()
    authors = escape(text(row, "authors")).replace(escape(ME), f'<span class="me">{escape(ME)}</span>')

    return CARD.format(
        cover=COVER.format(escape(web_image(cover))) if cover else "",
        venue=escape(venue),
        title_en=escape(title_en or title_zh),
        title_zh=escape(title_zh or title_en),
        authors=authors,
        link=LINK.format(escape(link)) if link else "",
        highlights=HIGHLIGHTS.format(en=en or zh, zh=zh or en) if en or zh else "",
        graphical_abstract=GRAPHICAL_ABSTRACT.format(escape(web_image(abstract))) if abstract else "",
    )


def main():
    sys.stdout.reconfigure(errors="replace")
    warnings = []
    # 第 1 行是列名，文章从第 2 行开始
    cards = [render(row, number, warnings) for number, row in enumerate(read_rows(), 2)]
    OUTPUT_FILE.write_text("\n".join(cards), encoding="utf-8")

    print(f"已生成 {OUTPUT_FILE.name}，共 {len(cards)} 篇文章。")
    print("请把它的全部内容粘贴到 index.html 的两行 ARTICLES 标记之间。")
    if warnings:
        print("\n请检查：")
        for warning in warnings:
            print(" - " + warning)


if __name__ == "__main__":
    main()

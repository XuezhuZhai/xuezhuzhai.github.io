"""把 news.xlsx 第一条内容转换成首页最新动态卡片 HTML，保存到 news_output.html。

用法：python news_to_html.py
然后把 news_output.html 的全部内容，粘贴到 index.html 的两行 NEWS 标记之间。
需要 openpyxl：pip install openpyxl
"""
import sys
from html import escape
from pathlib import Path

from openpyxl import load_workbook

SITE = Path(__file__).resolve().parent
EXCEL_FILE = SITE / "news.xlsx"
OUTPUT_FILE = SITE / "news_output.html"

CARD = """        <div class="news-card">
          <p class="news-label"><span class="t-en">Latest</span><span class="t-zh">最新动态</span></p>
          <p class="news-text t-en">{text_en}{link_en}</p>
          <p class="news-text t-zh">{text_zh}{link_zh}</p>
        </div>
"""

LINK = ' <a href="{}" target="_blank">{}</a>'


def text(row, key):
    value = row.get(key)
    return "" if value is None else str(value).strip()


def read_rows():
    sheet = load_workbook(EXCEL_FILE, read_only=True, data_only=True)["news"]
    rows = sheet.iter_rows(values_only=True)
    headers = next(rows)
    return [dict(zip(headers, values)) for values in rows if any(v not in (None, "") for v in values)]


def render(row, warnings):
    en, zh = text(row, "text_en"), text(row, "text_zh")
    if not en and not zh:
        warnings.append("第一条内容没有文字")

    link = text(row, "link")
    if link and not link.lower().startswith(("http://", "https://")):
        warnings.append(f"链接不以 http 开头，已跳过：{link}")
        link = ""

    def link_html(lang, default):
        label = text(row, f"link_text_{lang}") or default
        return LINK.format(escape(link), escape(label)) if link else ""

    return CARD.format(
        text_en=escape(en or zh),
        text_zh=escape(zh or en),
        link_en=link_html("en", "More →"),
        link_zh=link_html("zh", "查看详情 →"),
    )


def main():
    sys.stdout.reconfigure(errors="replace")
    rows = read_rows()
    if not rows:
        raise SystemExit("news.xlsx 没有内容")
    warnings = []
    # 卡片只显示表格里最上面的一条
    OUTPUT_FILE.write_text(render(rows[0], warnings), encoding="utf-8")

    print(f"已生成 {OUTPUT_FILE.name}")
    print("请把它的全部内容粘贴到 index.html 的两行 NEWS 标记之间。")
    if warnings:
        print("\n请检查：")
        for warning in warnings:
            print(" - " + warning)


if __name__ == "__main__":
    main()

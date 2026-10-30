"""把 talks.xlsx 转换成特邀报告卡片 HTML，保存到 talks_output.html。

用法：python talks_to_html.py
然后把 talks_output.html 的全部内容，粘贴到 index.html 的两行 TALKS 标记之间。
需要 openpyxl：pip install openpyxl
"""
import sys
from datetime import date
from html import escape
from pathlib import Path

from openpyxl import load_workbook

SITE = Path(__file__).resolve().parent
EXCEL_FILE = SITE / "talks.xlsx"
OUTPUT_FILE = SITE / "talks_output.html"

SLIDE = """      <div class="conf-slide talk-slide">
        <div class="conf-slide-inner">
          <p class="conf-slide-badge">{year}</p>
          <p class="conf-slide-event">{location}</p>
          <h3 class="conf-slide-title"><span class="t-en">{title_en}</span><span class="t-zh">{title_zh}</span></h3>
          <p class="conf-slide-venue"><span class="t-en">{venue_en}</span><span class="t-zh">{venue_zh}</span></p>{audience}{link}
          <div class="conf-slide-footer">
            <span class="conf-slide-type"><span class="t-en">{type_en}</span><span class="t-zh">{type_zh}</span></span>
            <span class="conf-slide-date">{date}</span>
          </div>
        </div>
      </div>
"""

AUDIENCE = """
          <div class="talk-audience">
            <p class="talk-audience-label"><span class="t-en">Audience</span><span class="t-zh">听众</span></p>
            <p class="talk-audience-text"><span class="t-en">{en}</span><span class="t-zh">{zh}</span></p>
          </div>"""

LINK = """
          <a href="{}" target="_blank" class="conf-slide-link"><span class="t-en">Event Page</span><span class="t-zh">活动页面</span> →</a>"""


def text(row, key):
    value = row.get(key)
    # Excel 可能把 June 2025 自动转成日期，这里转回文字
    if isinstance(value, date):
        return value.strftime("%B %Y")
    return "" if value is None else str(value).strip()


def read_rows():
    sheet = load_workbook(EXCEL_FILE, read_only=True, data_only=True)["talks"]
    rows = sheet.iter_rows(values_only=True)
    headers = next(rows)
    return [dict(zip(headers, values)) for values in rows if any(v not in (None, "") for v in values)]


def render(row, index, row_number, warnings):
    if not text(row, "title_en") and not text(row, "title_zh"):
        warnings.append(f"第 {row_number} 行：没有标题")

    link = text(row, "link")
    if link and not link.lower().startswith(("http://", "https://")):
        warnings.append(f"第 {row_number} 行：链接不以 http 开头，已跳过：{link}")
        link = ""

    def both(key):
        en, zh = text(row, f"{key}_en"), text(row, f"{key}_zh")
        return {f"{key}_en": escape(en or zh), f"{key}_zh": escape(zh or en)}

    audience = both("audience")
    audience = AUDIENCE.format(en=audience["audience_en"], zh=audience["audience_zh"]) if any(audience.values()) else ""

    return SLIDE.format(
        year=escape(text(row, "year")),
        location=escape(text(row, "location")),
        date=escape(text(row, "date")),
        link=LINK.format(escape(link)) if link else "",
        audience=audience,
        **both("title"),
        **both("venue"),
        **both("type"),
    )


def main():
    sys.stdout.reconfigure(errors="replace")
    warnings = []
    # 第 1 行是列名，报告从第 2 行开始
    slides = [render(row, i, i + 2, warnings) for i, row in enumerate(read_rows())]
    OUTPUT_FILE.write_text("\n".join(slides), encoding="utf-8")

    print(f"已生成 {OUTPUT_FILE.name}，共 {len(slides)} 条。")
    print("请把它的全部内容粘贴到 index.html 的两行 TALKS 标记之间。")
    if warnings:
        print("\n请检查：")
        for warning in warnings:
            print(" - " + warning)


if __name__ == "__main__":
    main()

"""把 conferences.xlsx 转换成会议卡片 HTML，保存到 conferences_output.html。

用法：python conferences_to_html.py
然后把 conferences_output.html 的全部内容，粘贴到 index.html 的两行 CONFERENCES 标记之间。
需要 openpyxl：pip install openpyxl
"""
import sys
from datetime import date
from html import escape
from pathlib import Path

from openpyxl import load_workbook

SITE = Path(__file__).resolve().parent
EXCEL_FILE = SITE / "conferences.xlsx"
OUTPUT_FILE = SITE / "conferences_output.html"

# 卡片背景色，按行循环使用
GRADIENTS = [
    ("#2a6e8e", "#0a7c6e"),
    ("#1a5878", "#0e6e7a"),
    ("#2a7e7a", "#0a8c80"),
    ("#1e6472", "#0a7c6e"),
    ("#246878", "#0e7c6a"),
]

SLIDE = """      <div class="conf-slide" style="background:linear-gradient(135deg,{color1},{color2})">
        <div class="conf-slide-inner">
          <p class="conf-slide-badge">{year}</p>
          <p class="conf-slide-event">{location}</p>
          <h3 class="conf-slide-title"><span class="t-en">{title_en}</span><span class="t-zh">{title_zh}</span></h3>
          <p class="conf-slide-venue"><span class="t-en">{venue_en}</span><span class="t-zh">{venue_zh}</span></p>
          <div class="conf-slide-footer">
            <span class="conf-slide-type"><span class="t-en">{type_en}</span><span class="t-zh">{type_zh}</span></span>
            <span class="conf-slide-date">{date}</span>
          </div>
        </div>
      </div>
"""


def text(row, key):
    value = row.get(key)
    # Excel 可能把 June 2025 自动转成日期，这里转回文字
    if isinstance(value, date):
        return value.strftime("%B %Y")
    return "" if value is None else str(value).strip()


def read_rows():
    sheet = load_workbook(EXCEL_FILE, read_only=True, data_only=True)["conferences"]
    rows = sheet.iter_rows(values_only=True)
    headers = next(rows)
    return [dict(zip(headers, values)) for values in rows if any(v not in (None, "") for v in values)]


def render(row, index, row_number, warnings):
    if not text(row, "title_en") and not text(row, "title_zh"):
        warnings.append(f"第 {row_number} 行：没有标题")

    def both(key):
        en, zh = text(row, f"{key}_en"), text(row, f"{key}_zh")
        return {f"{key}_en": escape(en or zh), f"{key}_zh": escape(zh or en)}

    color1, color2 = GRADIENTS[index % len(GRADIENTS)]
    return SLIDE.format(
        color1=color1,
        color2=color2,
        year=escape(text(row, "year")),
        location=escape(text(row, "location")),
        date=escape(text(row, "date")),
        **both("title"),
        **both("venue"),
        **both("type"),
    )


def main():
    sys.stdout.reconfigure(errors="replace")
    warnings = []
    # 第 1 行是列名，会议从第 2 行开始
    slides = [render(row, i, i + 2, warnings) for i, row in enumerate(read_rows())]
    OUTPUT_FILE.write_text("\n".join(slides), encoding="utf-8")

    print(f"已生成 {OUTPUT_FILE.name}，共 {len(slides)} 个会议。")
    print("请把它的全部内容粘贴到 index.html 的两行 CONFERENCES 标记之间。")
    if warnings:
        print("\n请检查：")
        for warning in warnings:
            print(" - " + warning)


if __name__ == "__main__":
    main()

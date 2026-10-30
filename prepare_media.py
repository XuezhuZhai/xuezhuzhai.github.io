"""把原图和原视频转换成网页用的低清版本，并加水印，保存到 media/ 文件夹。

用法：python prepare_media.py
index.html 只引用 media/ 里的文件；原图和原视频留在本地，不上传。
期刊封面只降低清晰度，不加水印，因为封面版权属于期刊。
需要 Pillow 和 ffmpeg。
"""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

SITE = Path(__file__).resolve().parent
MEDIA = SITE / "media"
WATERMARK = "©XuezhuZhai"
FONT = r"C:\Windows\Fonts\arial.ttf"

COVERS = ["IUCN.png", "JoDLA.png", "LAF045.png", "LAF081.png", "Landscape Ecology.png",
          "Urban Ecosystems.png", "Wetlands.png", "npj Urban Sustainability.png"]
VIDEOS = ["rural.mp4", "urban.mp4"]
COVER_WIDTH = 200
PHOTO_SIZE = 1200
ABSTRACT_SIZE = 1400
VIDEO_WIDTH = 854


def watermark_layer(width, height):
    """透明图层，水印在右下角；白字深边，浅色和深色背景上都看得清。"""
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    size = max(14, round(min(width, height) * 0.035))
    font = ImageFont.truetype(FONT, size)
    draw = ImageDraw.Draw(layer)
    left, top, right, bottom = draw.textbbox((0, 0), WATERMARK, font=font)
    margin = round(size * 0.7)
    position = (width - (right - left) - margin - left, height - (bottom - top) - margin - top)
    draw.text(position, WATERMARK, font=font, fill=(255, 255, 255, 190),
              stroke_width=max(1, size // 14), stroke_fill=(0, 0, 0, 130))
    return layer


def save_image(source, size, stamp=True, quality=78):
    image = ImageOps.exif_transpose(Image.open(source)).convert("RGBA")
    # 透明背景的图垫成白色
    background = Image.new("RGBA", image.size, (255, 255, 255, 255))
    image = Image.alpha_composite(background, image)
    image.thumbnail((size, size), Image.LANCZOS)
    if stamp:
        image = Image.alpha_composite(image, watermark_layer(*image.size))
    # 不写入 EXIF，相机和位置信息不会上传
    image.convert("RGB").save(MEDIA / f"{source.stem}.jpg", quality=quality, optimize=True, progressive=True)


def save_video(source):
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height", "-of", "csv=p=0", str(source)],
                           capture_output=True, text=True, check=True)
    width, height = map(int, probe.stdout.strip().split(",")[:2])
    out_width = min(width, VIDEO_WIDTH)
    out_height = round(height * out_width / width / 2) * 2
    layer = MEDIA / f"_{source.stem}_watermark.png"
    watermark_layer(out_width, out_height).save(layer)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(source), "-i", str(layer), "-filter_complex",
                    f"[0:v]scale={out_width}:{out_height}[v];[v][1:v]overlay=0:0,format=yuv420p",
                    "-c:v", "libx264", "-crf", "30", "-preset", "medium", "-c:a", "aac", "-b:a", "96k",
                    "-map_metadata", "-1", "-movflags", "+faststart", str(MEDIA / source.name)], check=True)
    layer.unlink()


def main():
    MEDIA.mkdir(exist_ok=True)
    for name in COVERS:
        save_image(SITE / name, COVER_WIDTH, stamp=False)
    for source in sorted(SITE.glob("Graphical Abstract_*")):
        save_image(source, ABSTRACT_SIZE, quality=82)
    save_image(SITE / "XZ.png", 600)
    photos = [*SITE.glob("NZJL_*.png"), *SITE.glob("YGC_*.jpg"), *(SITE / "from the field").glob("*.JPG")]
    for source in sorted(photos):
        save_image(source, PHOTO_SIZE)
    for name in VIDEOS:
        save_video(SITE / name)
    print(f"已生成 {len(list(MEDIA.iterdir()))} 个文件，保存在 media/")


if __name__ == "__main__":
    main()

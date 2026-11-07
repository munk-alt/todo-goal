"""生成扁平现代风格的「便签」应用图标（参考微软便签）。

输出：
  assets/app.png  （256，用于预览/快捷方式）
  assets/app.ico  （16/24/32/48/64/128/256 多尺寸，供 exe 与快捷方式）

用法： python scripts/make_icon.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
S = 1024  # 先大图绘制，再缩放，保证小尺寸清晰

# 配色（扁平暖黄，贴近微软便签）
BODY = (255, 209, 74, 255)
BODY_DARK = (242, 178, 34, 255)
FOLD_LIGHT = (255, 241, 178, 255)
LINE = (255, 255, 255, 235)
BOX = [66, 66, 958, 958]
RADIUS = 148
FOLD = 250


def build() -> Image.Image:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    # 柔和投影
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([80, 100, 950, 970], radius=RADIUS, fill=(20, 20, 20, 95))
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    img = Image.alpha_composite(img, shadow)

    # 便签主体
    body = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    bd.rounded_rectangle(BOX, radius=RADIUS, fill=BODY)

    # 右下角折角
    bd.polygon(
        [(BOX[2] - FOLD, BOX[3]), (BOX[2], BOX[3]), (BOX[2], BOX[3] - FOLD)],
        fill=BODY_DARK,
    )
    # 折角高光边
    bd.line([(BOX[2] - FOLD, BOX[3]), (BOX[2], BOX[3] - FOLD)], fill=FOLD_LIGHT, width=8)
    img = Image.alpha_composite(img, body)

    # 文本线条
    d = ImageDraw.Draw(img)
    for index, y in enumerate((300, 470, 640)):
        width = 470 if index < 2 else 300
        d.rounded_rectangle([152, y, 152 + width, y + 56], radius=28, fill=LINE)

    return img


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    img = build()
    img.resize((256, 256), Image.LANCZOS).save(OUT / "app.png")
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(OUT / "app.ico", sizes=sizes)
    print(f"written: {OUT / 'app.png'}")
    print(f"written: {OUT / 'app.ico'}  sizes={sizes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

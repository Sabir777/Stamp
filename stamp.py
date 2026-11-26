import os
import random
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Папка для рекурсивного хранения папок с фото
INPUT_DIR = Path("Input")

# Папка для сохранения результата
OUTPUT_DIR = Path("Output")
JPG_EXTS = {".jpg"}
STAMP_NAME = "stamp.txt"

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    os.path.expandvars("$PREFIX/share/fonts/TTF/DejaVuSans.ttf"),
    "/system/fonts/Roboto-Regular.ttf",
    "/system/fonts/DroidSans.ttf",
]


def find_font() -> str:
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("Шрифт не найден, поправьте FONT_CANDIDATES")


FONT = find_font()


def jitter_date(base: datetime, max_minutes: int = 2) -> datetime:
    return base + timedelta(seconds=random.randint(0, max_minutes * 60))


def parse_stamp_txt(path: Path) -> datetime:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"datetime\(\s*([0-9,\s]+)\)", text)
    if not m:
        raise ValueError(f"Не удалось разобрать дату в {path}")
    parts = [int(x) for x in m.group(1).split(",")]
    return datetime(*parts)


def stamp(src: Path, dst: Path, dt: datetime) -> None:
    img = Image.open(src).convert("RGB")
    w, h = img.size
    font = ImageFont.truetype(FONT, size=int(h * 0.022))
    text = dt.strftime("%d.%m.%Y   %H:%M")

    draw = ImageDraw.Draw(img)
    box = draw.textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    x = w - tw - int(w * 0.04)
    y = h - th - int(h * 0.03)

    # тонкая тень для читаемости на светлом фоне
    draw.text((x + 2, y + 2), text, font=font, fill=(90, 90, 90))
    draw.text((x, y), text, font=font, fill=(255, 255, 255))
    img.save(dst, quality=95)


if __name__ == "__main__":
    random.seed()
    # Сначала создаём все директории из Input в Output (включая пустые)
    for d in INPUT_DIR.rglob("*"):
        if d.is_dir():
            (OUTPUT_DIR / d.relative_to(INPUT_DIR)).mkdir(parents=True, exist_ok=True)

    # Все файлы, кроме stamp.txt, сгруппированные по папке
    files = sorted(
        p for p in INPUT_DIR.rglob("*") if p.is_file() and p.name != STAMP_NAME
    )
    by_dir: dict[Path, list[Path]] = {}
    for src in files:
        by_dir.setdefault(src.parent, []).append(src)

    for d, srcs in by_dir.items():
        stamp_txt = d / STAMP_NAME
        has_stamp = stamp_txt.exists()
        base = parse_stamp_txt(stamp_txt) if has_stamp else None

        for src in srcs:
            rel = src.relative_to(INPUT_DIR)
            dst = OUTPUT_DIR / rel
            dst.parent.mkdir(parents=True, exist_ok=True)

            if has_stamp and src.suffix.lower() in JPG_EXTS:
                dt = jitter_date(base)
                base = dt
                stamp(src, dst, dt)
                print(f"{rel}  ->  {dt.strftime('%d.%m.%Y %H:%M')}")
            else:
                shutil.copy2(src, dst)
                tag = "без штампа" if has_stamp else "нет stamp.txt"
                print(f"{rel}  ->  (копия, {tag})")

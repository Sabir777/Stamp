import os
import random
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Базовая дата
BASE_DT = datetime(2026, 11, 24, 14, 45)

# Папка для рекурсивного хранения папок с фото
INPUT_DIR = Path("Input")

# Папка для сохранения результата
OUTPUT_DIR = Path("Output")
JPG_EXTS = {".jpg"}

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


def random_date(start: datetime, end: datetime) -> datetime:
    delta = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, delta))


def jitter_date(base: datetime, max_minutes: int = 10) -> datetime:
    return base + timedelta(seconds=random.randint(0, max_minutes * 60))


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
    base = BASE_DT
    files = sorted(p for p in INPUT_DIR.rglob("*") if p.is_file())
    for src in files:
        rel = src.relative_to(INPUT_DIR)
        dst = OUTPUT_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)

        if src.suffix.lower() in JPG_EXTS:
            dt = jitter_date(base)
            base = dt
            stamp(src, dst, dt)
            print(f"{rel}  ->  {dt.strftime('%d.%m.%Y %H:%M')}")
        else:
            shutil.copy2(src, dst)
            print(f"{rel}  ->  (копия без штампа)")

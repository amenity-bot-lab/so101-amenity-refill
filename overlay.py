"""
動画映えのためのオーバーレイ描画（日本語フォント対応）。
判定結果の枠と、画面上部のステータス帯を描く。
"""
from __future__ import annotations

import platform
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

_FONT_CANDIDATES = {
    "Windows": [
        r"C:\Windows\Fonts\meiryob.ttc",
        r"C:\Windows\Fonts\meiryo.ttc",
        r"C:\Windows\Fonts\YuGothB.ttc",
        r"C:\Windows\Fonts\msgothic.ttc",
    ],
    "Darwin": [
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ],
    "Linux": [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
}

GREEN = (46, 204, 113)
RED = (231, 76, 60)
YELLOW = (241, 196, 15)
WHITE = (255, 255, 255)


@lru_cache(maxsize=8)
def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_CANDIDATES.get(platform.system(), []):
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # 古い Pillow
        return ImageFont.load_default()


def _to_pil(frame_bgr: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))


def _to_bgr(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def draw_slot_boxes(frame_bgr: np.ndarray, slots: list[dict]) -> np.ndarray:
    """slots: [{"slot": "A", "filled": True/False, "box_2d": [ymin, xmin, ymax, xmax] (0-1000)}]"""
    img = _to_pil(frame_bgr)
    draw = ImageDraw.Draw(img)
    h, w = frame_bgr.shape[:2]
    font = _font(max(18, h // 30))
    for s in slots:
        box = s.get("box_2d")
        if not box or len(box) != 4:
            continue
        y0, x0, y1, x1 = box
        x0, x1 = int(x0 / 1000 * w), int(x1 / 1000 * w)
        y0, y1 = int(y0 / 1000 * h), int(y1 / 1000 * h)
        filled = s.get("filled")
        color = GREEN if filled else RED if filled is False else YELLOW
        draw.rectangle([x0, y0, x1, y1], outline=color, width=4)
        label = f"{s.get('slot', '?')}: {'あり' if filled else '空' if filled is False else '?'}"
        tw = draw.textlength(label, font=font)
        draw.rectangle([x0, max(0, y0 - font.size - 8), x0 + tw + 12, y0], fill=color)
        draw.text((x0 + 6, max(0, y0 - font.size - 6)), label, fill=WHITE, font=font)
    return _to_bgr(img)


def draw_status(frame_bgr: np.ndarray, title: str, lines: list[str] | None = None,
                color: tuple[int, int, int] = (20, 20, 20)) -> np.ndarray:
    """画面上部に半透明の帯を敷き、タイトルと数行のテキストを描く。"""
    lines = lines or []
    h, w = frame_bgr.shape[:2]
    big = _font(max(22, h // 22))
    small = _font(max(16, h // 32))
    band_h = big.size + 16 + len(lines) * (small.size + 6) + 8

    overlay = frame_bgr.copy()
    cv2.rectangle(overlay, (0, 0), (w, band_h), color, -1)
    blended = cv2.addWeighted(overlay, 0.65, frame_bgr, 0.35, 0)

    img = _to_pil(blended)
    draw = ImageDraw.Draw(img)
    y = 8
    draw.text((16, y), title, fill=WHITE, font=big)
    y += big.size + 10
    for line in lines:
        draw.text((20, y), line, fill=(230, 230, 230), font=small)
        y += small.size + 6
    return _to_bgr(img)


def annotate(frame_bgr: np.ndarray, title: str, slots: list[dict] | None = None,
             lines: list[str] | None = None) -> np.ndarray:
    out = frame_bgr
    if slots:
        out = draw_slot_boxes(out, slots)
    return draw_status(out, title, lines)

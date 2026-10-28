"""
客室トレイの各区画に物があるかを AI（VLM）で判定する。

使い方:
  python detect.py --camera                       # カメラで1枚撮って判定
  python detect.py --image runs/capture_xxx.jpg    # 保存済みの画像で判定
  python detect.py --image a.jpg --backend ollama  # ローカル（Ollama）で判定
  python detect.py --image a.jpg --out annotated.jpg   # 判定結果を描いた画像も保存
  python detect.py --camera --mock-empty A,C       # AI を呼ばず A と C が空だったことにする（配線テスト用）
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from pydantic import BaseModel, Field

import config
from ai_backend import generate_json
from overlay import annotate


class SlotState(BaseModel):
    slot: str = Field(description="区画ラベル（A, B, C のいずれか）")
    filled: bool = Field(description="区画に物が入っていれば true、空なら false")
    item: Optional[str] = Field(default=None, description="見えた物の種類（例: 歯ブラシ）。空なら null")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="判定の確信度 0〜1")
    box_2d: Optional[list[int]] = Field(
        default=None, description="区画を囲む矩形 [ymin, xmin, ymax, xmax]。画像の高さ・幅を1000とした整数")


class TrayState(BaseModel):
    slots: list[SlotState]
    notes: str = Field(default="", description="気づいたことがあれば日本語で一言")


def build_prompt() -> str:
    tmpl = (config.PROMPTS_DIR / "detect_prompt.txt").read_text(encoding="utf-8")
    items = "、".join(sorted({s.item for s in config.SLOTS.values()}))
    return tmpl.format(
        n_slots=len(config.SLOTS),
        slot_list="・".join(config.SLOT_ORDER),
        items=items,
    )


def normalize(state: TrayState) -> TrayState:
    """設定にある区画が全部そろうように整える。足りない区画は『判定できず』として filled=True（触らない）扱い。"""
    by_id = {s.slot.strip().upper(): s for s in state.slots}
    out: list[SlotState] = []
    for sid in config.SLOT_ORDER:
        s = by_id.get(sid)
        if s is None:
            out.append(SlotState(slot=sid, filled=True, item=None, confidence=0.0))
        else:
            s.slot = sid
            out.append(s)
    state.slots = out
    return state


def detect(image_bgr: np.ndarray, backend: str = config.AI_BACKEND,
           mock_empty: list[str] | None = None) -> TrayState:
    """画像から区画の状態を返す。backend="mock" なら AI を呼ばず mock_empty を空とする。"""
    if backend == "mock":
        mock_empty = [m.strip().upper() for m in (mock_empty or [])]
        slots = [SlotState(slot=sid, filled=sid not in mock_empty,
                           item=None if sid in mock_empty else config.SLOTS[sid].item,
                           confidence=1.0, box_2d=_mock_box(i, len(config.SLOT_ORDER)))
                 for i, sid in enumerate(config.SLOT_ORDER)]
        return TrayState(slots=slots, notes="mock")
    state = generate_json(build_prompt(), TrayState, image_bgr=image_bgr, backend=backend)
    return normalize(state)


def _mock_box(i: int, n: int) -> list[int]:
    # 画面右半分に n 個の区画が横に並んでいる想定のダミー矩形（描画テスト用）
    x0 = 520 + int(i * (460 / n))
    x1 = x0 + int(460 / n) - 20
    return [300, x0, 760, x1]


def empty_slots(state: TrayState) -> list[str]:
    return [s.slot for s in state.slots if s.filled is False]


def summarize(state: TrayState) -> str:
    parts = []
    for s in state.slots:
        mark = "あり" if s.filled else "空"
        parts.append(f"{s.slot}:{mark}({s.confidence:.2f})")
    return "  ".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser(description="区画の在庫判定")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--camera", action="store_true")
    src.add_argument("--image", type=Path)
    ap.add_argument("--backend", default=config.AI_BACKEND, choices=["gemini", "ollama", "mock"])
    ap.add_argument("--mock-empty", default="", help="mock のとき空にする区画。例: A,C")
    ap.add_argument("--out", type=Path, default=None, help="判定結果を描いた画像の保存先")
    args = ap.parse_args()

    if args.camera:
        from capture import grab_frame
        print(f"カメラ {config.CAMERA_INDEX} で撮影中…", flush=True)
        frame = grab_frame()
    else:
        frame = cv2.imread(str(args.image))
        if frame is None:
            raise SystemExit(f"画像を読めません: {args.image}")

    t0 = time.time()
    state = detect(frame, args.backend, [m for m in args.mock_empty.split(",") if m])
    dt = time.time() - t0
    print(json.dumps(state.model_dump(), ensure_ascii=False, indent=2))
    print(f"\n判定: {summarize(state)}   空の区画: {empty_slots(state) or 'なし'}   ({dt:.1f}s, {args.backend})")

    out = args.out or config.RUNS_DIR / f"detect_{datetime.now():%Y%m%d_%H%M%S}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    annotated = annotate(frame, f"判定結果（{args.backend}）", [s.model_dump() for s in state.slots],
                         [f"空の区画: {', '.join(empty_slots(state)) or 'なし'}", f"{dt:.1f}s"])
    cv2.imwrite(str(out), annotated)
    print(f"描画した画像: {out}")


if __name__ == "__main__":
    main()

"""
USB カメラから1枚撮る。

使い方:
  python capture.py                    # runs/capture_<時刻>.jpg に保存
  python capture.py --out test.jpg     # 保存先を指定
  python capture.py --index 1          # カメラ番号を指定（既定は config.CAMERA_INDEX）

Windows では、カメラの読み込みが固まって Ctrl+C も効かなくなることがあるので、
読み込みは別スレッドで行い、一定時間で打ち切る（固まらずにエラーになる）。
"""
from __future__ import annotations

import argparse
import platform
import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

import config

READ_TIMEOUT_S = 5.0


def _backends() -> list[int]:
    """試す順番。Windows は MSMF（lerobot と同じ）を先に、だめなら DSHOW。"""
    if platform.system() == "Windows":
        return [cv2.CAP_MSMF, cv2.CAP_DSHOW]
    return [cv2.CAP_ANY]


def _run_with_timeout(fn, timeout_s: float):
    """fn() を別スレッドで実行し、timeout_s を過ぎたら TimeoutError。"""
    box: dict = {}

    def _target():
        try:
            box["value"] = fn()
        except Exception as e:  # noqa: BLE001
            box["error"] = e

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout_s)
    if t.is_alive():
        raise TimeoutError(f"カメラが {timeout_s:.0f} 秒応答しません")
    if "error" in box:
        raise box["error"]
    return box.get("value")


class Camera:
    """開いたままにして何度もフレームを取るためのラッパー。with 文で使う。"""

    def __init__(self, index: int = config.CAMERA_INDEX,
                 width: int = config.CAPTURE_WIDTH, height: int = config.CAPTURE_HEIGHT):
        self.index = index
        self.width = width
        self.height = height
        self.cap: cv2.VideoCapture | None = None

    def _try_open(self, backend: int, set_size: bool) -> bool:
        cap = _run_with_timeout(lambda: cv2.VideoCapture(self.index, backend), 10.0)
        if cap is None or not cap.isOpened():
            return False
        if set_size:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        try:
            ok, frame = _run_with_timeout(cap.read, READ_TIMEOUT_S)
        except TimeoutError:
            ok, frame = False, None
        if not ok or frame is None:
            try:
                cap.release()
            except Exception:  # noqa: BLE001
                pass
            return False
        self.cap = cap
        return True

    def open(self) -> "Camera":
        # 指定解像度で開く → だめなら解像度を指定せずに開く、を各方式で試す
        for backend in _backends():
            for set_size in (True, False):
                if self._try_open(backend, set_size):
                    for _ in range(5):          # 自動露出が落ち着くまで数フレーム捨てる
                        self.read()
                    return self
        raise RuntimeError(
            f"カメラ {self.index} から映像を取れません。番号（lerobot-find-cameras opencv）と、"
            "他のアプリ（lerobot-record・preview.py など）がカメラを使っていないかを確認し、"
            "USBを挿し直してから再実行してください。"
        )

    def read(self) -> np.ndarray:
        assert self.cap is not None, "open() を先に呼ぶ"
        ok, frame = _run_with_timeout(self.cap.read, READ_TIMEOUT_S)
        if not ok or frame is None:
            raise RuntimeError("カメラからフレームを取得できません")
        return frame

    def close(self) -> None:
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:  # noqa: BLE001
                pass
            self.cap = None

    def __enter__(self) -> "Camera":
        return self.open()

    def __exit__(self, *exc) -> None:
        self.close()


def grab_frame(index: int = config.CAMERA_INDEX, warmup: int = 10) -> np.ndarray:
    """カメラを開いて1枚撮って閉じる。判定用の静止画はこれで十分。"""
    with Camera(index) as cam:
        frame = None
        for _ in range(warmup):
            frame = cam.read()
        assert frame is not None
        return frame


def save_frame(frame: np.ndarray, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description="USBカメラから1枚撮って保存する")
    ap.add_argument("--index", type=int, default=config.CAMERA_INDEX)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    t0 = time.time()
    print(f"カメラ {args.index} で撮影中…", flush=True)
    frame = grab_frame(args.index)
    out = args.out or config.RUNS_DIR / f"capture_{datetime.now():%Y%m%d_%H%M%S}.jpg"
    save_frame(frame, out)
    h, w = frame.shape[:2]
    print(f"保存しました: {out}  ({w}x{h}, {time.time() - t0:.1f}s)")


if __name__ == "__main__":
    main()

"""
カメラ位置合わせ用のライブプレビュー。中心線と三分割のガイドを重ねて表示する。

使い方:
  python preview.py            # q で終了、s で runs/ に保存、g でガイド線の表示切替
  python preview.py --index 1
"""
from __future__ import annotations

import argparse
from datetime import datetime

import cv2

import config
from capture import Camera, save_frame


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=int, default=config.CAMERA_INDEX)
    args = ap.parse_args()

    guide = True
    with Camera(args.index) as cam:
        print("q: 終了 / s: 保存 / g: ガイド線の切替")
        while True:
            frame = cam.read()
            h, w = frame.shape[:2]
            view = frame.copy()
            if guide:
                c = (0, 255, 255)
                cv2.line(view, (w // 2, 0), (w // 2, h), c, 1)
                cv2.line(view, (0, h // 2), (w, h // 2), c, 1)
                for k in (1, 2):
                    cv2.line(view, (w * k // 3, 0), (w * k // 3, h), (0, 180, 255), 1)
                    cv2.line(view, (0, h * k // 3), (w, h * k // 3), (0, 180, 255), 1)
                cv2.putText(view, f"{w}x{h}  left: supply holder / right: room tray",
                            (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imshow("preview", view)
            key = cv2.waitKey(30) & 0xFF
            if key == ord("q"):
                break
            if key == ord("g"):
                guide = not guide
            if key == ord("s"):
                out = save_frame(frame, config.RUNS_DIR / f"preview_{datetime.now():%Y%m%d_%H%M%S}.jpg")
                print(f"保存: {out}")
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

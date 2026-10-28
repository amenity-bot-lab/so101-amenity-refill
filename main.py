"""
通し実行: 撮影 → AI判定 → AI手順決定 → 再生 → 再撮影で確認（閉ループ）

使い方（よく使う順）:
  python main.py --dry-run --backend mock --mock-empty A,C   # ロボットもAPIも使わず配線確認
  python main.py --dry-run                                    # Gemini で判定だけ本物、ロボットは動かさない
  python main.py                                              # 本番（各再生の前に Enter で確認）
  python main.py --auto --show                                # 本番・確認なし・オーバーレイ表示（撮影用）
  python main.py --auto --show --instruction "歯ブラシは A と C だけ補充して"

出力: runs/<日時>/ に 撮影画像・判定JSON・計画JSON・ログ・注釈付き画像 を保存
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

import config
from capture import Camera, save_frame
from detect import TrayState, detect, empty_slots, summarize
from execute import replay_slot
from overlay import annotate
from plan import make_plan


class Session:
    """1回の通し実行。ログ・画像・表示ウィンドウを面倒みる。"""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.dir = config.RUNS_DIR / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.dir / "log.txt"
        self.cam: Camera | None = None
        self.last_frame: np.ndarray | None = None
        self.last_slots: list[dict] = []
        self.window = "amenity-refill"
        self.step = 0
        self.log(f"run dir: {self.dir}")
        self.log(f"args: {vars(args)}")

    # ---- ログ ----
    def log(self, msg: str) -> None:
        line = f"[{datetime.now():%H:%M:%S}] {msg}"
        print(line, flush=True)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    # ---- カメラ ----
    def frame(self) -> np.ndarray:
        if self.args.image is not None:
            img = cv2.imread(str(self.args.image))
            if img is None:
                raise SystemExit(f"画像を読めません: {self.args.image}")
            return img
        if self.cam is None:
            self.cam = Camera().open()
        return self.cam.read()

    def snapshot(self, name: str) -> np.ndarray:
        self.step += 1
        f = self.frame()
        save_frame(f, self.dir / f"{self.step:02d}_{name}.jpg")
        self.last_frame = f
        self.last_slots = []      # 前回の判定枠は消す
        return f

    # ---- 表示 ----
    def show(self, title: str, lines: list[str] | None = None, frame: np.ndarray | None = None,
             slots: list[dict] | None = None, save_as: str | None = None) -> None:
        if slots is not None:
            self.last_slots = slots
        base = frame if frame is not None else self.last_frame
        if base is None:
            return
        img = annotate(base, title, self.last_slots, lines)
        if save_as:
            save_frame(img, self.dir / save_as)
        if self.args.show:
            try:
                if not getattr(self, "_win_ready", False):
                    # 画面の左半分に置く（ターミナルは Win+→ で右半分へ）。.env の WINDOW_X / WINDOW_Y / WINDOW_W で調整可
                    import os
                    wx, wy = int(os.getenv("WINDOW_X", "0")), int(os.getenv("WINDOW_Y", "0"))
                    ww = int(os.getenv("WINDOW_W", "960"))
                    h, w = img.shape[:2]
                    cv2.namedWindow(self.window, cv2.WINDOW_NORMAL)
                    cv2.resizeWindow(self.window, ww, int(ww * h / w))
                    cv2.moveWindow(self.window, wx, wy)
                    self._win_ready = True
                cv2.imshow(self.window, img)
                cv2.waitKey(1)
            except cv2.error:
                self.args.show = False
                self.log("表示ウィンドウを開けないので --show を無効化します")

    def tick_live(self, title: str, lines: list[str]) -> None:
        """再生中にライブ映像をウィンドウに流す（撮影用）。"""
        if not self.args.show or self.args.image is not None or self.cam is None:
            return
        try:
            self.show(title, lines, frame=self.cam.read())
        except RuntimeError:
            pass

    def close(self) -> None:
        if self.cam is not None:
            self.cam.close()
        if self.args.show:
            try:
                cv2.destroyAllWindows()
            except cv2.error:
                pass

    # ---- 1ラウンド ----
    def detect_round(self, name: str) -> TrayState:
        frame = self.snapshot(name)
        self.show(f"判定中…（{self.args.backend}）", ["トレイを撮影しました"])
        t0 = time.time()
        state = detect(frame, self.args.backend, self.args.mock_empty)
        dt = time.time() - t0
        (self.dir / f"{self.step:02d}_{name}.json").write_text(
            json.dumps(state.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
        self.log(f"判定({name}) {dt:.1f}s: {summarize(state)}  空={empty_slots(state) or 'なし'}  {state.notes}")
        self.show("判定結果", [f"空の区画: {', '.join(empty_slots(state)) or 'なし'}", f"{dt:.1f}s"],
                  slots=[s.model_dump() for s in state.slots], save_as=f"{self.step:02d}_{name}_annotated.jpg")
        return state

    def run(self) -> int:
        a = self.args
        self.log("=== 開始 ===")
        # カメラの起動を待つ間も、すぐにウィンドウを出しておく（後ろのデスクトップが映らないように）
        self.show("準備中…", ["カメラを起動しています"],
                  frame=np.full((config.CAPTURE_HEIGHT, config.CAPTURE_WIDTH, 3), 30, np.uint8))
        state = self.detect_round("before")

        plan = make_plan(state, a.instruction, a.backend, force_llm=a.always_llm)
        (self.dir / "plan.json").write_text(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2),
                                            encoding="utf-8")
        self.log(f"計画: {plan.actions}  理由: {plan.reason}")
        self.show("補充計画", [f"指示: {a.instruction or '（なし）'}",
                            f"動作: {' → '.join(plan.actions) if plan.actions else 'なし'}", plan.reason])

        if not plan.actions:
            self.log("補充する区画はありません。終了。")
            self.show("補充の必要なし", ["すべての区画に物があります"])
            self.pause(2.0)
            return 0

        results: dict[str, bool] = {}
        for i, sid in enumerate(plan.actions, 1):
            if not a.auto and not a.dry_run:
                input(f"\n>>> 区画 {sid} の補充動作を再生します。ロボットがホームポーズにあることを確認して Enter: ")
            self.log(f"--- 再生 {i}/{len(plan.actions)}: 区画 {sid} ({config.SLOTS[sid].dataset} ep{config.SLOTS[sid].episode})")
            title = f"補充中: 区画 {sid}（{i}/{len(plan.actions)}）"
            lines = [f"{config.SLOTS[sid].item} を補充元ホルダーから区画 {sid} へ"]
            self.show(title, lines)
            ok = replay_slot(sid, dry_run=a.dry_run, on_line=self.log,
                             on_tick=lambda t=title, l=lines: self.tick_live(t, l))
            results[sid] = ok
            self.log(f"再生 {sid}: {'成功' if ok else '失敗'}")
            if ok and a.backend == "mock" and sid in a.mock_empty:
                a.mock_empty.remove(sid)      # mock では再生が成功したら埋まったことにする
            if not ok and not a.keep_going:
                self.log("失敗したので中断します（--keep-going で続行可）")
                break
            self.pause(a.settle_s)   # 腕が止まって画面が落ち着くまで待つ

        if a.no_verify:
            self.log("確認撮影はスキップ")
            return 0 if all(results.values()) else 1

        # ---- 確認（閉ループ） ----
        # 確認するのは「計画で補充すると決めた区画」だけ（指示で外した区画が空でも、やり直さない）
        targets = set(plan.actions)
        rounds = 1
        while True:
            state = self.detect_round("after")
            empty_now = empty_slots(state)
            remaining = [s for s in empty_now if s in targets]
            skipped = [s for s in empty_now if s not in targets]
            if not remaining:
                if skipped:
                    msg = f"補充対象の区画 {', '.join(plan.actions)} はすべて埋まりました（指示により {', '.join(skipped)} は補充しない）"
                else:
                    msg = "すべての区画に物があります"
                self.log(f"=== 補充完了：{msg} ===")
                self.show("補充完了", [msg], save_as="final.jpg")
                self.pause(3.0)
                self.summary(results, state, "complete")
                return 0
            if rounds >= a.max_rounds or a.dry_run:
                self.log(f"=== 未完了: 空の区画 {remaining} が残っています ===")
                self.show("未完了", [f"空の区画: {', '.join(remaining)}"], save_as="final.jpg")
                self.pause(3.0)
                self.summary(results, state, "incomplete")
                return 1
            rounds += 1
            self.log(f"--- 再補充ラウンド {rounds}: {remaining}")
            for sid in remaining:
                if not a.auto:
                    input(f"\n>>> 区画 {sid} を再補充します。ホームポーズを確認して Enter: ")
                title = f"再補充中: 区画 {sid}"
                self.show(title, ["1回目で入らなかったのでもう一度"])
                results[sid] = replay_slot(sid, dry_run=a.dry_run, on_line=self.log,
                                           on_tick=lambda t=title: self.tick_live(t, []))
                self.pause(a.settle_s)

    def pause(self, seconds: float) -> None:
        """待ち時間中もウィンドウを更新する。"""
        t0 = time.time()
        while time.time() - t0 < seconds:
            if self.args.show:
                try:
                    cv2.waitKey(50)
                except cv2.error:
                    pass
            else:
                time.sleep(0.05)

    def summary(self, results: dict[str, bool], final: TrayState, status: str) -> None:
        (self.dir / "summary.json").write_text(json.dumps({
            "status": status,
            "replays": results,
            "final_state": final.model_dump(),
            "backend": self.args.backend,
            "instruction": self.args.instruction,
        }, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="アメニティ補充の通し実行")
    ap.add_argument("--backend", default=config.AI_BACKEND, choices=["gemini", "ollama", "mock"])
    ap.add_argument("--instruction", default="", help="作業指示（例: 歯ブラシは A だけ補充して）")
    ap.add_argument("--always-llm", action="store_true", help="指示がなくても手順決定に LLM を使う")
    ap.add_argument("--dry-run", action="store_true", help="ロボットを動かさない（再生コマンドを表示するだけ）")
    ap.add_argument("--auto", action="store_true", help="再生前の Enter 確認を省略（撮影用）")
    ap.add_argument("--show", action="store_true", help="オーバーレイ付きの映像ウィンドウを出す")
    ap.add_argument("--image", type=Path, default=None, help="カメラの代わりに画像ファイルを使う")
    ap.add_argument("--mock-empty", default="", help="backend=mock のとき空とみなす区画。例: A,C")
    ap.add_argument("--max-rounds", type=int, default=2, help="確認して空が残っていたら再補充する最大回数")
    ap.add_argument("--no-verify", action="store_true", help="最後の確認撮影をしない")
    ap.add_argument("--keep-going", action="store_true", help="再生が失敗しても次の区画へ進む")
    ap.add_argument("--settle-s", type=float, default=1.5, help="再生後に待つ秒数")
    args = ap.parse_args()
    args.mock_empty = [m.strip() for m in args.mock_empty.split(",") if m.strip()]
    return args


def main() -> int:
    args = parse_args()
    s = Session(args)
    try:
        return s.run()
    except KeyboardInterrupt:
        s.log("中断しました")
        return 130
    finally:
        s.close()


if __name__ == "__main__":
    raise SystemExit(main())

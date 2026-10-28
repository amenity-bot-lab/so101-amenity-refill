"""
記録済みのエピソードを replay.py で再生する（ロボットを実際に動かす部分）。

使い方:
  python execute.py --slot A                 # 区画 A の補充動作を再生
  python execute.py --slot A --episode 2     # エピソード番号を指定
  python execute.py --slot A --dry-run       # コマンドを表示するだけ
"""
from __future__ import annotations

import argparse
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable

import config


def lerobot_cmd(name: str) -> str:
    """lerobot-replay などの実行ファイルのパスを返す。LEROBOT_BIN が空なら PATH 任せ。"""
    if config.LEROBOT_BIN:
        p = Path(config.LEROBOT_BIN) / name
        if platform.system() == "Windows":
            p = p.with_suffix(".exe")
        return str(p)
    return name


def replay_command(slot: config.Slot, episode: int | None = None) -> list[str]:
    """再生コマンド。lerobot-replay ではなく replay.py（ゆっくり開始・強めに握る・終了後も脱力しない）を使う。"""
    ep = slot.episode if episode is None else episode
    return [sys.executable, "-u", str(config.ROOT / "replay.py"), "--slot", slot.id, "--episode", str(ep)]


def run_streaming(cmd: list[str], timeout_s: int, on_line: Callable[[str], None] | None = None,
                  on_tick: Callable[[], None] | None = None, tick_s: float = 0.05) -> int:
    """サブプロセスを実行し、出力行を on_line に流しつつ、待ち時間中は on_tick を呼び続ける。"""
    import os
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")  # 子プロセスの日本語が化けないように
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace", bufsize=1, env=env)

    def _reader() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            if on_line:
                on_line(line.rstrip())

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    t0 = time.time()
    while proc.poll() is None:
        if time.time() - t0 > timeout_s:
            proc.kill()
            if on_line:
                on_line(f"[timeout] {timeout_s}s を超えたので強制終了")
            return -9
        if on_tick:
            on_tick()
        time.sleep(tick_s)
    t.join(timeout=2)
    return proc.returncode


def replay_slot(slot_id: str, episode: int | None = None, dry_run: bool = False,
                on_line: Callable[[str], None] | None = print,
                on_tick: Callable[[], None] | None = None) -> bool:
    slot = config.SLOTS[slot_id]
    cmd = replay_command(slot, episode)
    if on_line:
        on_line("$ " + " ".join(cmd))
    if dry_run:
        # ロボットなしの通し確認用。本番の再生時間に近い待ち時間を入れる
        for _ in range(40):
            if on_tick:
                on_tick()
            time.sleep(0.05)
        return True
    rc = run_streaming(cmd, config.REPLAY_TIMEOUT_S, on_line, on_tick)
    if on_line:
        on_line(f"[replay {slot_id}] 終了コード {rc}")
    return rc == 0


def main() -> None:
    ap = argparse.ArgumentParser(description="区画の補充動作を再生")
    ap.add_argument("--slot", required=True, choices=list(config.SLOTS))
    ap.add_argument("--episode", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    ok = replay_slot(args.slot, args.episode, args.dry_run)
    print("成功" if ok else "失敗")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()

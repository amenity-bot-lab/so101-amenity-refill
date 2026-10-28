"""
記録したエピソードを再生する（lerobot-replay の代わり）。lerobot-replay との違い:
  1. 再生の前に、記録の最初の姿勢まで 2 秒かけてゆっくり移動する（いきなり飛ばない）
  2. つかむ場面でグリッパーを記録より少し強く閉じる（歯ブラシが滑って落ちるのを防ぐ）
  3. 再生が終わっても力を抜かない（アームが落ちない）
  4. --check で、記録と再生の位置のずれを表示できる

使い方:
  python replay.py --slot A --episode 0
  python replay.py --slot A --episode 0 --grip-boost 30     # もっと強く握る
  python replay.py --slot A --episode 0 --check             # ずれを表示
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np

import config

NAMES = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
GRIP = NAMES.index("gripper")


def dataset_root(repo_id: str) -> Path:
    home = os.getenv("HF_LEROBOT_HOME")
    base = Path(home) if home else Path.home() / ".cache" / "huggingface" / "lerobot"
    return base / repo_id


def load_episode(repo_id: str, episode: int) -> tuple[np.ndarray, np.ndarray, int]:
    import json
    import pandas as pd
    root = dataset_root(repo_id)
    files = sorted((root / "data").rglob("*.parquet"))
    if not files:
        raise SystemExit(f"データが見つかりません: {root}")
    df = pd.concat([pd.read_parquet(p) for p in files])
    df = df[df["episode_index"] == episode].sort_values("frame_index")
    if df.empty:
        raise SystemExit(f"エピソード {episode} がありません: {root}")
    fps = int(json.loads((root / "meta" / "info.json").read_text(encoding="utf-8")).get("fps", 30))
    acts = np.stack(df["action"].to_numpy()).astype(float)
    rec = np.stack(df["observation.state"].to_numpy()).astype(float)
    return acts, rec, fps


def boost_grip(acts: np.ndarray, boost: float) -> np.ndarray:
    """グリッパーが閉じている場面（開閉幅の半分より閉じている場面）だけ、さらに boost だけ閉じる指令にする。
    物をはさんでいれば、指令と実際の差が大きくなる分だけ強く握る（モーター側の上限で頭打ち）。"""
    if boost <= 0:
        return acts
    out = acts.copy()
    g = out[:, GRIP]
    lo, hi = float(g.min()), float(g.max())
    if hi - lo < 5:            # ほとんど開閉していない
        return out
    closing = g < lo + 0.5 * (hi - lo)
    out[closing, GRIP] = np.maximum(g[closing] - boost, 0.0)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="記録したエピソードを再生する")
    ap.add_argument("--slot", required=True, choices=list(config.SLOTS))
    ap.add_argument("--episode", type=int, default=None)
    ap.add_argument("--grip-boost", type=float, default=None,
                    help="つかむ場面でグリッパーを追加で閉じる量（0〜100 のうち）。0 で記録どおり")
    ap.add_argument("--check", action="store_true", help="記録と再生の位置のずれを表示")
    args = ap.parse_args()

    slot = config.SLOTS[args.slot]
    ep = slot.episode if args.episode is None else args.episode
    acts, rec, fps = load_episode(slot.dataset, ep)
    if args.grip_boost is None:
        args.grip_boost = slot.grip_boost if slot.grip_boost is not None else config.GRIP_BOOST
    acts = boost_grip(acts, args.grip_boost)
    print(f"[replay] {slot.dataset} episode {ep}: {len(acts)} frames ({len(acts) / fps:.0f}s), "
          f"grip-boost {args.grip_boost:g}", flush=True)

    from lerobot.robots.so_follower import SOFollower, SOFollowerRobotConfig
    robot = SOFollower(SOFollowerRobotConfig(
        port=config.ROBOT_PORT, id=config.ROBOT_ID,
        num_read_retries=10, disable_torque_on_disconnect=False))
    robot.connect()
    got: list[list[float]] = []
    try:
        # 1) 最初の姿勢へゆっくり移動
        o = robot.get_observation()
        cur = np.array([o[f"{n}.pos"] for n in NAMES])
        steps = 2 * fps
        for k in range(1, steps + 1):
            tgt = cur + (acts[0] - cur) * k / steps
            robot.send_action({f"{n}.pos": float(v) for n, v in zip(NAMES, tgt)})
            time.sleep(1 / fps)
        time.sleep(0.3)
        # 2) 記録どおりに再生
        for a in acts:
            t0 = time.perf_counter()
            if args.check:
                o = robot.get_observation()
                got.append([o[f"{n}.pos"] for n in NAMES])
            robot.send_action({f"{n}.pos": float(v) for n, v in zip(NAMES, a)})
            time.sleep(max(1 / fps - (time.perf_counter() - t0), 0.0))
        time.sleep(0.5)
    except KeyboardInterrupt:
        print("[replay] 中断しました", flush=True)
        return 130
    finally:
        robot.disconnect()
    print("[replay] 完了", flush=True)

    if args.check and got:
        g = np.array(got)
        n = min(len(g), len(rec))
        err = g[:n] - rec[:n]
        print("\njoint          mean|err|  max|err|   (replay - recorded)")
        for i, nm in enumerate(NAMES):
            print(f"  {nm:13s} {np.abs(err[:, i]).mean():7.1f}  {np.abs(err[:, i]).max():8.1f}")
        print("\n  t   " + " | ".join(f"{nm[:8]:>8s} R/P" for nm in NAMES))
        for k in range(0, n, fps):
            print(f"{k / fps:4.0f}s " + " | ".join(f"{rec[k, i]:5.0f}/{g[k, i]:5.0f}" for i in range(len(NAMES))))
    return 0


if __name__ == "__main__":
    sys.exit(main())

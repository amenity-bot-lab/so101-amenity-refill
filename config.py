"""
設定ファイル。
値は .env（同じフォルダ）か環境変数で上書きできる。 .env.example をコピーして .env を作る。
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value not in (None, "") else default


# ---------------------------------------------------------------------------
# ロボット（LeRobot の CLI にそのまま渡す値）
# ---------------------------------------------------------------------------
ROBOT_TYPE = "so101_follower"
ROBOT_PORT = _env("ROBOT_PORT", "COM5")          # フォロワーのポート。lerobot-find-port で確認
ROBOT_ID = _env("ROBOT_ID", "my_follower")       # キャリブレーション時に使った id と同じにする
TELEOP_TYPE = "so101_leader"
TELEOP_PORT = _env("TELEOP_PORT", "COM4")        # リーダーのポート
TELEOP_ID = _env("TELEOP_ID", "my_leader")       # キャリブレーション時に使った id と同じにする

# lerobot-record / lerobot-replay などの置き場。空なら PATH から探す。
# Windows でユーザー領域に pip install した場合の例: %APPDATA%\Python\Python313\Scripts
LEROBOT_BIN = os.path.expandvars(_env("LEROBOT_BIN", ""))

# 再生1回あたりの上限時間（秒）。これを超えたら強制終了して失敗扱い
REPLAY_TIMEOUT_S = int(_env("REPLAY_TIMEOUT_S", "120"))

# 再生でつかむ場面のグリッパーを、記録より追加で閉じる量（0〜100 のうち）。歯ブラシが滑るときに大きくする
GRIP_BOOST = float(_env("GRIP_BOOST", "20"))

# ---------------------------------------------------------------------------
# カメラ（真上から補充元ホルダーと客室トレイを1枚に収める）
# ---------------------------------------------------------------------------
CAMERA_INDEX = int(_env("CAMERA_INDEX", "0"))    # lerobot-find-cameras opencv で確認
CAPTURE_WIDTH = int(_env("CAPTURE_WIDTH", "1280"))
CAPTURE_HEIGHT = int(_env("CAPTURE_HEIGHT", "720"))

# ---------------------------------------------------------------------------
# AI
# ---------------------------------------------------------------------------
AI_BACKEND = _env("AI_BACKEND", "gemini")        # gemini | ollama | mock
GEMINI_MODEL = _env("GEMINI_MODEL", "gemini-3.8-flash")
# 混雑（503）や上限（429）で失敗したときに、順に切り替えて試すモデル
GEMINI_FALLBACK_MODELS = [m.strip() for m in _env(
    "GEMINI_FALLBACK_MODELS", "gemini-3.6-flash,gemini-3.5-flash-lite,gemini-2.5-flash").split(",") if m.strip()]
OLLAMA_URL = _env("OLLAMA_URL", "http://localhost:11434")
OLLAMA_VLM = _env("OLLAMA_VLM", "qwen2.5vl:7b")  # 画像判定に使うローカルモデル
OLLAMA_LLM = _env("OLLAMA_LLM", "qwen2.5vl:7b")  # 手順決定に使うローカルモデル（同じでよい）
AI_TIMEOUT_S = int(_env("AI_TIMEOUT_S", "60"))


# ---------------------------------------------------------------------------
# 区画（スロット）の定義
#   dataset: lerobot-record で記録したデータセットの repo_id
#   episode: 再生に使うエピソード番号（再生テストで一番安定したものを選ぶ）
#   再生テスト結果(10/27): A ep0 3/4, B ep1 2/3, C ep0 2/5 → grip_boost 40 で改善（A・B・C とも 40）
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Slot:
    id: str
    item: str
    dataset: str
    episode: int = 0
    grip_boost: float | None = None   # None なら GRIP_BOOST を使う。滑りやすい区画だけ大きくする


SLOTS: dict[str, Slot] = {
    "A": Slot("A", "歯ブラシ", "pai/refill_A", 0, grip_boost=40),
    "B": Slot("B", "歯ブラシ", "pai/refill_B", 1, grip_boost=40),
    "C": Slot("C", "歯ブラシ", "pai/refill_C", 0, grip_boost=40),
}
SLOT_ORDER = ["A", "B", "C"]   # 迷ったときの補充順（補充元ホルダーの 1→2→3 と対応）

RUNS_DIR = ROOT / "runs"       # 実行ログ・画像の保存先
PROMPTS_DIR = ROOT / "prompts"

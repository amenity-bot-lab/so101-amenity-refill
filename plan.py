"""
判定結果と作業指示から、実行する補充動作の順番を決める。

  - 指示がなければルール（空いている区画を A→B→C の順）
  - 指示があれば LLM に決めさせ、返答を検証する（壊れていたらルールに戻す）

使い方:
  python plan.py --state runs/.../detect.json --instruction "歯ブラシは A だけ補充して"
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pydantic import BaseModel, Field

import config
from ai_backend import generate_json
from detect import TrayState, empty_slots


class Plan(BaseModel):
    actions: list[str] = Field(description="実行する動作名（区画ラベル）を順番どおりに並べたもの。何もしないなら空配列")
    reason: str = Field(default="", description="判断理由（日本語で1〜2文）")


def plan_rule(state: TrayState, exclude: set[str] | None = None) -> Plan:
    exclude = exclude or set()
    acts = [s for s in config.SLOT_ORDER if s in empty_slots(state) and s not in exclude]
    reason = f"空の区画 {acts} を既定の順で補充" if acts else "空の区画はないので何もしない"
    return Plan(actions=acts, reason=reason)


def _validate(plan: Plan, state: TrayState) -> Plan | None:
    allowed = set(empty_slots(state))
    seen: list[str] = []
    for a in plan.actions:
        a = a.strip().upper()
        if a not in config.SLOTS:
            return None                       # 存在しない動作名
        if a not in allowed:
            continue                          # 物がある区画は黙って落とす
        if a not in seen:
            seen.append(a)
    plan.actions = seen
    return plan


def build_prompt(state: TrayState, instruction: str | None) -> str:
    tmpl = (config.PROMPTS_DIR / "plan_prompt.txt").read_text(encoding="utf-8")
    descs = "\n".join(f"- {sid}: 区画 {sid} に {config.SLOTS[sid].item} を1つ補充する" for sid in config.SLOT_ORDER)
    state_json = json.dumps(
        [{"slot": s.slot, "filled": s.filled, "item": s.item, "confidence": round(s.confidence, 2)}
         for s in state.slots], ensure_ascii=False)
    return tmpl.format(
        slot_descriptions=descs,
        state_json=state_json,
        instruction=(instruction or "").strip() or "（指示なし）",
        default_order="→".join(config.SLOT_ORDER),
    )


def make_plan(state: TrayState, instruction: str | None = None,
              backend: str = config.AI_BACKEND, force_llm: bool = False) -> Plan:
    use_llm = backend != "mock" and (force_llm or bool((instruction or "").strip()))
    if not use_llm:
        return plan_rule(state)
    try:
        raw = generate_json(build_prompt(state, instruction), Plan, image_bgr=None, backend=backend)
    except Exception as e:  # noqa: BLE001
        print(f"  [plan] LLM 失敗のためルールで決定: {type(e).__name__}: {str(e)[:120]}")
        return plan_rule(state)
    plan = _validate(raw, state)
    if plan is None:
        print(f"  [plan] LLM の返答が不正のためルールで決定: {raw.actions}")
        return plan_rule(state)
    return plan


def main() -> None:
    ap = argparse.ArgumentParser(description="補充動作の計画")
    ap.add_argument("--state", type=Path, required=True, help="detect の JSON")
    ap.add_argument("--instruction", default="")
    ap.add_argument("--backend", default=config.AI_BACKEND, choices=["gemini", "ollama", "mock"])
    args = ap.parse_args()
    state = TrayState.model_validate(json.loads(args.state.read_text(encoding="utf-8")))
    plan = make_plan(state, args.instruction, args.backend)
    print(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

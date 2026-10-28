"""
AI 呼び出しの共通部分。Gemini（クラウド）と Ollama（ローカル）を同じ関数で呼べる。

    result = generate_json(prompt, Schema, image_bgr=frame, backend="gemini")

戻り値は Schema（pydantic）のインスタンス。失敗時は例外。
"""
from __future__ import annotations

import base64
import json
import re
import time
from typing import Type, TypeVar

import cv2
import numpy as np
from pydantic import BaseModel

import config

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# 共通ユーティリティ
# ---------------------------------------------------------------------------
def encode_jpeg(image_bgr: np.ndarray, max_side: int = 1280, quality: int = 90) -> bytes:
    """送信用に JPEG へ。長辺が max_side を超えていたら縮小する。"""
    h, w = image_bgr.shape[:2]
    scale = max_side / max(h, w)
    if scale < 1.0:
        image_bgr = cv2.resize(image_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", image_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError("JPEG エンコードに失敗")
    return buf.tobytes()


def parse_json_text(text: str, schema: Type[T]) -> T:
    """モデルの返答テキストから JSON を取り出して schema で検証する。コードフェンス付きでも通す。"""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return schema.model_validate(json.loads(text))


def _retry(fn, attempts: int = 3, wait_s: float = 2.0):
    last: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 - 何が来ても再試行したい
            last = e
            print(f"  [ai] 失敗 ({i + 1}/{attempts}): {type(e).__name__}: {str(e)[:200]}")
            time.sleep(wait_s * (i + 1))
    assert last is not None
    raise last


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------
def _gemini_client():
    try:
        from google import genai  # pip install google-genai
    except ImportError as e:
        raise RuntimeError("google-genai が未インストールです: python -m pip install google-genai") from e
    import os
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY が設定されていません（.env に書く）")
    from google.genai import types
    # 応答がないまま待ち続けないよう、1回の問い合わせに上限時間を付ける（ミリ秒）
    return genai.Client(http_options=types.HttpOptions(timeout=config.AI_TIMEOUT_S * 1000))


def generate_json_gemini(prompt: str, schema: Type[T], image_bgr: np.ndarray | None = None,
                         model: str = config.GEMINI_MODEL) -> T:
    """Gemini で JSON を生成する。混雑などで失敗したら、別のモデルに切り替えて試す。"""
    from google.genai import types

    client = _gemini_client()
    contents: list = []
    if image_bgr is not None:
        contents.append(types.Part.from_bytes(data=encode_jpeg(image_bgr), mime_type="image/jpeg"))
    contents.append(prompt)

    def _call(m: str, with_thinking: bool):
        kwargs = dict(response_mime_type="application/json", response_schema=schema, temperature=0.0)
        if with_thinking:
            # Gemini 3 系は thinking_level で思考量を絞ると速い（低でも判定には十分）
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="low")
        cfg = types.GenerateContentConfig(**kwargs)
        resp = client.models.generate_content(model=m, contents=contents, config=cfg)
        parsed = getattr(resp, "parsed", None)
        if isinstance(parsed, schema):
            return parsed
        return parse_json_text(resp.text or "", schema)

    def _once(m: str):
        print(f"  [ai] Gemini（{m}）に問い合わせ中…", flush=True)
        try:
            return _call(m, with_thinking=True)
        except Exception as e:  # noqa: BLE001
            msg = str(e).lower()
            # thinking_level 非対応のモデルなら外してもう一度
            if "thinking" in msg or isinstance(e, (TypeError, ValueError)):
                return _call(m, with_thinking=False)
            raise

    models = [model] + [m for m in config.GEMINI_FALLBACK_MODELS if m != model]
    last: Exception | None = None
    for i, m in enumerate(models):
        try:
            return _retry(lambda m=m: _once(m), attempts=2, wait_s=2.0)
        except Exception as e:  # noqa: BLE001
            last = e
            text = str(e)
            if "API key" in text or "API_KEY" in text or "PERMISSION_DENIED" in text:
                raise RuntimeError("APIキーが無効です。.env の GEMINI_API_KEY を確認してください") from e
            if i + 1 < len(models):
                print(f"  [ai] {m} が使えないので {models[i + 1]} に切り替えます", flush=True)
    assert last is not None
    raise last


# ---------------------------------------------------------------------------
# Ollama（ローカル）
# ---------------------------------------------------------------------------
def generate_json_ollama(prompt: str, schema: Type[T], image_bgr: np.ndarray | None = None,
                         model: str | None = None) -> T:
    import requests

    model = model or (config.OLLAMA_VLM if image_bgr is not None else config.OLLAMA_LLM)
    message: dict = {"role": "user", "content": prompt}
    if image_bgr is not None:
        message["images"] = [base64.b64encode(encode_jpeg(image_bgr, max_side=1024)).decode()]
    payload = {
        "model": model,
        "messages": [message],
        "format": schema.model_json_schema(),   # Ollama は JSON スキーマで出力を制約できる
        "stream": False,
        "options": {"temperature": 0},
    }

    def _once():
        r = requests.post(f"{config.OLLAMA_URL}/api/chat", json=payload, timeout=config.AI_TIMEOUT_S)
        r.raise_for_status()
        return parse_json_text(r.json()["message"]["content"], schema)

    return _retry(_once)


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
def generate_json(prompt: str, schema: Type[T], image_bgr: np.ndarray | None = None,
                  backend: str = config.AI_BACKEND) -> T:
    if backend == "gemini":
        return generate_json_gemini(prompt, schema, image_bgr)
    if backend == "ollama":
        return generate_json_ollama(prompt, schema, image_bgr)
    raise ValueError(f"未知の backend: {backend}（gemini / ollama / mock）")

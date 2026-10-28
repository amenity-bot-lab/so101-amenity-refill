"""テレオペ・記録のとき、フォロワーの手首の回転（wrist_roll）を固定角度にする。
.env の LOCK_WRIST_ROLL=0 （度。0 = キャリブレーション時の基準の向き＝ハサミが横に開く向き）で有効。
LOCK_WRIST_ROLL を消す（空にする）と、元どおりリーダーに追従する。
元に戻すとき: python tools/patch_wrist_lock.py --undo
"""
import pathlib, sys
import lerobot.teleoperators.so_leader.so_leader as sl

p = pathlib.Path(sl.__file__)
bak = p.with_name(p.name + ".bak")
if "--undo" in sys.argv:
    if bak.exists():
        p.write_text(bak.read_text(encoding="utf-8"), encoding="utf-8")
        print("restored:", p)
    sys.exit(0)

s = p.read_text(encoding="utf-8")
anchor = '        action = {f"{motor}.pos": val for motor, val in action.items()}\n'
inject = (anchor +
          '        import os as _os\n'
          '        _lock = _os.environ.get("LOCK_WRIST_ROLL", "").strip()\n'
          '        if _lock and "wrist_roll.pos" in action:\n'
          '            action["wrist_roll.pos"] = float(_lock)\n')
if "LOCK_WRIST_ROLL" in s:
    print("already patched:", p)
elif anchor not in s:
    print("ERROR: patch point not found (lerobot version differs)"); sys.exit(1)
else:
    if not bak.exists():
        bak.write_text(s, encoding="utf-8")
    p.write_text(s.replace(anchor, inject, 1), encoding="utf-8")
    print("patched:", p)

env = pathlib.Path(__file__).resolve().parent.parent / ".env"   # プロジェクト直下の .env
if env.exists():
    t = env.read_text(encoding="utf-8")
    if "LOCK_WRIST_ROLL" not in t:
        with env.open("a", encoding="utf-8") as fh:
            fh.write(("" if t.endswith("\n") else "\n") + "# 手首の回転を固定（度）。空にするとリーダーに追従\nLOCK_WRIST_ROLL=0\n")
        print("added LOCK_WRIST_ROLL=0 to .env")
    else:
        print(".env already has LOCK_WRIST_ROLL")

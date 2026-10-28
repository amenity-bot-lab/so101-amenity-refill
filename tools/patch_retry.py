"""lerobot のモーター通信で、失敗したときに自動でやり直す回数を 0 -> 5 にする。
元に戻すときは: python tools/patch_retry.py --undo
"""
import pathlib, sys
import lerobot.motors.motors_bus as mb
import lerobot.motors.feetech.feetech as ft

undo = "--undo" in sys.argv
for mod in (mb, ft):
    p = pathlib.Path(mod.__file__)
    bak = p.with_name(p.name + ".bak")
    if undo:
        if bak.exists():
            p.write_text(bak.read_text(encoding="utf-8"), encoding="utf-8")
            print("restored:", p)
        continue
    s = p.read_text(encoding="utf-8")
    n = s.count("num_retry: int = 0")
    if n == 0:
        print("already patched:", p)
        continue
    if not bak.exists():
        bak.write_text(s, encoding="utf-8")
    p.write_text(s.replace("num_retry: int = 0", "num_retry: int = 5"), encoding="utf-8")
    print(f"patched {n} places:", p)

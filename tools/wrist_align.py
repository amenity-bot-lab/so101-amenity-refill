"""手首の回転（5番）の位置を、リーダーとフォロワー両方リアルタイムで表示する（20秒）。
フォロワーは力を抜いた状態なので、手で回せる。真ん中（2047）がキャリブレーション時の基準の向き。
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import config  # ポートは .env の ROBOT_PORT / TELEOP_PORT

import time
from scservo_sdk import PortHandler, PacketHandler

pk = PacketHandler(0)
lead = PortHandler(config.TELEOP_PORT); lead.openPort(); lead.setBaudRate(1000000)
fol = PortHandler(config.ROBOT_PORT); fol.openPort(); fol.setBaudRate(1000000)
pk.write1ByteTxRx(fol, 5, 40, 0)   # フォロワー手首の力を抜く

def mark(v):
    if v is None:
        return "  NG  "
    d = v - 2047
    return f"{v:5d} ({'OK ' if abs(d) <= 100 else ('<<<' if d > 0 else '>>>')} {d:+5d})"

t0 = time.time()
while time.time() - t0 < 20:
    lv, r1, _ = pk.read2ByteTxRx(lead, 5, 56)
    fv, r2, _ = pk.read2ByteTxRx(fol, 5, 56)
    print(f"leader {mark(lv if r1 == 0 else None)}   follower {mark(fv if r2 == 0 else None)}", flush=True)
    time.sleep(0.3)
lead.closePort(); fol.closePort()

"""LeRobot が見ている角度（度）を、リーダーとフォロワーで並べて表示する（15秒）。
フォロワーは力を抜いたまま（動かない）。テレオペで『勝手に動く』関節を探すためのもの。
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import config  # ポートは .env の ROBOT_PORT / TELEOP_PORT

import time
from lerobot.robots.so_follower import SOFollower, SOFollowerRobotConfig
from lerobot.teleoperators.so_leader import SOLeader, SOLeaderTeleopConfig

f = SOFollower(SOFollowerRobotConfig(port=config.ROBOT_PORT, id=config.ROBOT_ID))
l = SOLeader(SOLeaderTeleopConfig(port=config.TELEOP_PORT, id=config.TELEOP_ID))
f.bus.connect(); l.bus.connect()
f.bus.disable_torque(num_retry=5)
print("calibration matches motors?  follower:", f.is_calibrated, "  leader:", l.is_calibrated)
goal = f.bus.sync_read("Goal_Position", normalize=False, num_retry=5)
pres = f.bus.sync_read("Present_Position", normalize=False, num_retry=5)
print("follower raw goal/present:", {m: (goal[m], pres[m]) for m in goal})
print("Do NOT move anything. Differences of more than ~15 deg are the joints that will jump.")
t0 = time.time()
while time.time() - t0 < 15:
    a = l.bus.sync_read("Present_Position", num_retry=5)
    b = f.bus.sync_read("Present_Position", num_retry=5)
    print(" | ".join(f"{m[:8]} L{a[m]:6.0f} F{b[m]:6.0f} d{a[m]-b[m]:+5.0f}" for m in a), flush=True)
    time.sleep(1.0)
f.bus.disconnect(False); l.bus.disconnect(False)

"""配置の平面図（真上図＋側面図）を SVG で生成する。単位 cm、1cm = 10px。"""
from pathlib import Path
import math

S = 10  # px per cm
OX, OY = 60, 60   # top-view origin offset (px)

def P(x, y):  # cm -> px (top view)
    return OX + x * S, OY + y * S

INK = "#1f2937"; MUTED = "#6b7280"; GRID = "#e5e7eb"; ACCENT = "#2563eb"; RED = "#dc2626"; GREEN = "#16a34a"; AMBER = "#d97706"
F = "font-family='Noto Sans CJK JP, Hiragino Sans, Meiryo, Yu Gothic, sans-serif'"

out = []
W, H = 980, 1000
out.append(f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' width='{W}' height='{H}' {F}>")
out.append(f"<rect x='0' y='0' width='{W}' height='{H}' fill='white'/>")

# ---------- 真上図 ----------
out.append(f"<text x='{OX}' y='34' font-size='22' font-weight='700' fill='{INK}'>配置の平面図（真上から・単位 cm）</text>")
out.append(f"<text x='{OX+440}' y='34' font-size='13' fill='{MUTED}'>マス目 = 5 cm。ロボット正面が図の上。</text>")

# desk 70 x 50
dw, dh = 70, 50
x0, y0 = P(0, 0); x1, y1 = P(dw, dh)
out.append(f"<rect x='{x0}' y='{y0}' width='{dw*S}' height='{dh*S}' fill='#fafafa' stroke='{INK}' stroke-width='2'/>")
for i in range(0, dw + 1, 5):
    x, _ = P(i, 0)
    out.append(f"<line x1='{x}' y1='{y0}' x2='{x}' y2='{y1}' stroke='{GRID}' stroke-width='1'/>")
    if i % 10 == 0:
        out.append(f"<text x='{x}' y='{y1+16}' font-size='11' fill='{MUTED}' text-anchor='middle'>{i}</text>")
for j in range(0, dh + 1, 5):
    _, y = P(0, j)
    out.append(f"<line x1='{x0}' y1='{y}' x2='{x1}' y2='{y}' stroke='{GRID}' stroke-width='1'/>")
    if j % 10 == 0:
        out.append(f"<text x='{x0-8}' y='{y+4}' font-size='11' fill='{MUTED}' text-anchor='end'>{j}</text>")

# camera frame 61 x 34 centered (35, 26)
cx, cy = 35, 24
fx, fy = P(cx - 30.5, cy - 17)
out.append(f"<rect x='{fx}' y='{fy}' width='{61*S}' height='{34*S}' fill='none' stroke='{ACCENT}' stroke-width='2' stroke-dasharray='8 6'/>")
tx, ty = P(cx - 30.5 + 0.8, cy - 17 + 1.6)
out.append(f"<text x='{tx}' y='{ty}' font-size='12' fill='{ACCENT}' font-weight='700'>カメラの写る範囲（高さ50cmのとき約61×34cm）</text>")
# camera center mark
ccx, ccy = P(cx, cy)
out.append(f"<circle cx='{ccx}' cy='{ccy}' r='5' fill='none' stroke='{ACCENT}' stroke-width='2'/>")
out.append(f"<line x1='{ccx-9}' y1='{ccy}' x2='{ccx+9}' y2='{ccy}' stroke='{ACCENT}' stroke-width='2'/>")
out.append(f"<line x1='{ccx}' y1='{ccy-9}' x2='{ccx}' y2='{ccy+9}' stroke='{ACCENT}' stroke-width='2'/>")
out.append(f"<text x='{ccx-12}' y='{ccy+22}' font-size='11' fill='{ACCENT}' text-anchor='end'>カメラ</text>")
out.append(f"<text x='{ccx-12}' y='{ccy+36}' font-size='11' fill='{ACCENT}' text-anchor='end'>中心</text>")

# robot base 12x12 at bottom center: x 29-41, y 38-50 ; base center (35, 44)
bx, by = P(29, 38)
out.append(f"<rect x='{bx}' y='{by}' width='{12*S}' height='{12*S}' fill='#e5e7eb' stroke='{INK}' stroke-width='2'/>")
bcx, bcy = P(35, 44)
out.append(f"<circle cx='{bcx}' cy='{bcy}' r='6' fill='{INK}'/>")
out.append(f"<text x='{bcx}' y='{by+12*S-8}' font-size='12' fill='{INK}' text-anchor='middle' font-weight='700'>SO-101 台座（テープで固定）</text>")
out.append(f"<text x='{bcx}' y='{bcy-14}' font-size='11' fill='{MUTED}' text-anchor='middle'>ホームポーズ：腕を畳んで台座の上</text>")

# reach arcs r=15 and r=28 from (35,44), only the upper half
for r, label in ((15, "15cm"), (28, "28cm")):
    ax0, ay0 = P(35 - r, 44); ax1, ay1 = P(35 + r, 44)
    out.append(f"<path d='M {ax0} {ay0} A {r*S} {r*S} 0 0 1 {ax1} {ay1}' fill='none' stroke='{AMBER}' stroke-width='1.5' stroke-dasharray='4 4'/>")
    lx, ly = P(35 + r * math.cos(math.radians(75)), 44 - r * math.sin(math.radians(75)))
    out.append(f"<text x='{lx+4}' y='{ly}' font-size='11' fill='{AMBER}'>{label}</text>")
lx, ly = P(56.8, 46.0)
out.append(f"<text x='{lx}' y='{ly}' font-size='11' fill='{AMBER}'>腕が無理なく届く範囲</text>")
lx, ly = P(56.8, 47.4)
out.append(f"<text x='{lx}' y='{ly}' font-size='11' fill='{AMBER}'>（15〜28cm）</text>")

# supply holder: ダイソー「仕切りケース 1」12.7 x 8.7cm、4マス（左の3マスを使う）
HX0, HY0, HW, HH = 15, 21, 12.7, 8.7
sx, sy = P(HX0, HY0)
out.append(f"<rect x='{sx}' y='{sy}' width='{HW*S}' height='{HH*S}' fill='#fff7ed' stroke='{INK}' stroke-width='2'/>")
cw = HW / 4
for i in range(4):
    cx0 = HX0 + i * cw
    gx0, gy0 = P(cx0 + 0.2, HY0 + 0.3)
    out.append(f"<rect x='{gx0}' y='{gy0}' width='{(cw-0.4)*S}' height='{(HH-0.6)*S}' fill='white' stroke='{INK}' stroke-width='1.2'/>")
    ccx_cm = cx0 + cw / 2
    if i < 3:
        tx0, ty0 = P(ccx_cm - 0.9, HY0 + HH / 2 - 0.5)
        out.append(f"<rect x='{tx0}' y='{ty0}' width='{1.8*S}' height='{1*S}' fill='{GREEN}'/>")
        lx, ly = P(ccx_cm, HY0 - 0.8)
        out.append(f"<text x='{lx}' y='{ly}' font-size='13' fill='{INK}' text-anchor='middle' font-weight='700'>{i+1}</text>")
    else:
        lx, ly = P(ccx_cm, HY0 - 0.8)
        out.append(f"<text x='{lx}' y='{ly}' font-size='10' fill='{MUTED}' text-anchor='middle'>予備</text>")
lx, ly = P(HX0 + HW / 2, HY0 + HH + 1.8)
out.append(f"<text x='{lx}' y='{ly}' font-size='12' fill='{INK}' text-anchor='middle' font-weight='700'>補充元ホルダー（仕切りケース 12.7×8.7cm）</text>")
lx, ly = P(HX0 + HW / 2, HY0 + HH + 3.2)
out.append(f"<text x='{lx}' y='{ly}' font-size='11' fill='{MUTED}' text-anchor='middle'>1マスに歯ブラシを1本ずつ立てる・両面テープで固定</text>")

# room tray: カトラリートレー 20 x 24cm、区画 6 x 22cm を3つ（長い辺をロボットに向けて縦置き）
TX0, TY0, TW, TH = 36, 11, 20, 24
tx, ty = P(TX0, TY0)
out.append(f"<rect x='{tx}' y='{ty}' width='{TW*S}' height='{TH*S}' fill='#e5e7eb' stroke='{INK}' stroke-width='2'/>")
comp_x = []
for i, lab in enumerate("ABC"):
    cx0 = TX0 + 0.5 + i * 6.5
    comp_x.append(cx0 + 3)
    rx, ry = P(cx0, TY0 + 1)
    out.append(f"<rect x='{rx}' y='{ry}' width='{6*S}' height='{22*S}' fill='#374151' stroke='{INK}' stroke-width='1.5'/>")
    # label at the robot-side end
    lx, ly = P(cx0 + 3, TY0 + 21.5)
    out.append(f"<rect x='{lx-13}' y='{ly-14}' width='26' height='19' fill='white' stroke='{INK}' stroke-width='1'/>")
    out.append(f"<text x='{lx}' y='{ly+1}' font-size='14' fill='{INK}' text-anchor='middle' font-weight='700'>{lab}</text>")
    if lab != "B":
        px, py = P(cx0 + 2.1, TY0 + 1.6)
        out.append(f"<rect x='{px}' y='{py}' width='{1.8*S}' height='{17.5*S}' fill='#f9fafb' stroke='{GREEN}' stroke-width='2'/>")
for k, line in enumerate(["客室トレイ", "（カトラリートレー）", "区画 6×22cm を3つ", "長い辺をロボット側に", "ラベルは手前の端に"]):
    lx, ly = P(TX0 + TW + 0.8, TY0 + 6 + k * 1.6)
    out.append(f"<text x='{lx}' y='{ly}' font-size='{12 if k == 0 else 11}' fill='{INK if k == 0 else MUTED}' font-weight='{700 if k == 0 else 400}'>{line}</text>")

# arrows 1->A, 2->B, 3->C
out.append(f"<defs><marker id='arr' markerWidth='8' markerHeight='8' refX='6' refY='4' orient='auto'><path d='M0,0 L8,4 L0,8 z' fill='{RED}'/></marker></defs>")
for i in range(3):
    g = HX0 + i * cw + cw / 2
    ax0, ay0 = P(g + 0.6, HY0 + HH / 2 - 0.6)
    ax1, ay1 = P(comp_x[i], TY0 + 6)
    mx = (ax0 + ax1) / 2
    out.append(f"<path d='M {ax0} {ay0} Q {mx} {min(ay0, ay1) - 60 - i*15} {ax1} {ay1}' fill='none' stroke='{RED}' stroke-width='1.5' marker-end='url(#arr)' opacity='0.85'/>")
lx, ly = P(28, 6.2)
out.append(f"<text x='{lx}' y='{ly}' font-size='11' fill='{RED}' text-anchor='middle'>記録する動作：1→A、2→B、3→C（各2〜3エピソード）</text>")

# distances from base center to holder / tray centers
import math as _m
for (ex, ey), (lx_cm, ly_cm, anchor) in (((HX0 + HW / 2, HY0 + HH / 2), (24.5, 37.5, "end")),
                                         ((TX0 + TW / 2, TY0 + TH / 2), (42.5, 37.5, "start"))):
    ex_px, ey_px = P(ex, ey)
    out.append(f"<line x1='{bcx}' y1='{bcy}' x2='{ex_px}' y2='{ey_px}' stroke='{MUTED}' stroke-width='1' stroke-dasharray='2 3'/>")
    d = _m.hypot(ex - 35, ey - 44)
    lx, ly = P(lx_cm, ly_cm)
    out.append(f"<text x='{lx}' y='{ly}' font-size='10' fill='{MUTED}' text-anchor='{anchor}'>約{d:.0f}cm</text>")

# mat note
lx, ly = P(1, 1.8)
out.append(f"<text x='{lx}' y='{ly}' font-size='11' fill='{MUTED}'>作業マット：無地（白か黒）。トレイ2つと台座の位置をテープでマーキング</text>")

# ---------- 側面図 ----------
sy0 = 640
out.append(f"<text x='{OX}' y='{sy0}' font-size='22' font-weight='700' fill='{INK}'>側面図（横から・単位 cm）</text>")
base_y = sy0 + 300  # desk surface line y
SX = 10
SZ = 5
def Q(x, z):  # x cm along desk (0..70), z cm height -> px (縦は 5px/cm)
    return OX + x * SX, base_y - z * SZ
# desk
dx0, dz0 = Q(0, 0); dx1, _ = Q(70, 0)
out.append(f"<rect x='{dx0}' y='{dz0}' width='{70*SX}' height='14' fill='#e5e7eb' stroke='{INK}'/>")
out.append(f"<text x='{dx1-4}' y='{dz0+11}' font-size='11' fill='{MUTED}' text-anchor='end'>天板</text>")
# robot base and arm folded (at x 29..41)
rx, rz = Q(29, 3)
out.append(f"<rect x='{rx}' y='{rz}' width='{12*SX}' height='{3*SZ}' fill='#d1d5db' stroke='{INK}'/>")
ax, az = Q(35, 3)
out.append(f"<path d='M {ax} {az} L {ax-14} {az-55} L {ax+30} {az-75}' fill='none' stroke='{INK}' stroke-width='6' stroke-linecap='round'/>")
out.append(f"<text x='{ax+8}' y='{az-88}' font-size='12' fill='{INK}' text-anchor='middle' font-weight='700'>SO-101（ホームポーズ）</text>")
# trays (seen from side: holder x 15..27.7, tray x 36..56)
hx, hz = Q(15, 7); out.append(f"<rect x='{hx}' y='{hz}' width='{12.7*SX}' height='{7*SZ}' fill='#fff7ed' stroke='{INK}'/>")
for i in range(3):
    g = 15 + i * 3.175 + 1.6
    gx, gz = Q(g - 0.5, 19); out.append(f"<rect x='{gx}' y='{gz}' width='{1*SX}' height='{19*SZ}' fill='{GREEN}' opacity='0.9'/>")
lx, lz = Q(19, -7.5); out.append(f"<text x='{lx}' y='{lz}' font-size='11' fill='{INK}' text-anchor='middle'>補充元：ケース高さ7cm、袋を立てる（約19cm）</text>")
tx, tz = Q(36, 4); out.append(f"<rect x='{tx}' y='{tz}' width='{20*SX}' height='{4*SZ}' fill='#e5e7eb' stroke='{INK}'/>")
lx, lz = Q(48, -7.5); out.append(f"<text x='{lx}' y='{lz}' font-size='11' fill='{INK}' text-anchor='middle'>客室トレイ：深さ3〜5cm、袋は寝かせて置く</text>")
# camera at (35, 50)
cx_px, cz_px = Q(35, 50)
out.append(f"<rect x='{cx_px-14}' y='{cz_px-10}' width='28' height='18' rx='4' fill='{ACCENT}'/>")
out.append(f"<circle cx='{cx_px}' cy='{cz_px+8}' r='4' fill='white'/>")
out.append(f"<text x='{cx_px+22}' y='{cz_px}' font-size='12' fill='{ACCENT}' font-weight='700'>USBカメラ（真下向き・アームで固定）</text>")
# view cone to desk: 61cm wide
vx0, vz0 = Q(35 - 30.5, 0); vx1, _ = Q(35 + 30.5, 0)
out.append(f"<path d='M {cx_px} {cz_px+12} L {vx0} {vz0} M {cx_px} {cz_px+12} L {vx1} {vz0}' stroke='{ACCENT}' stroke-width='1.5' stroke-dasharray='6 5' fill='none'/>")
# height dimension
hx0, hz0 = Q(66, 0); _, hz1 = Q(66, 50)
out.append(f"<line x1='{hx0}' y1='{hz0}' x2='{hx0}' y2='{hz1}' stroke='{MUTED}' stroke-width='1'/>")
out.append(f"<line x1='{hx0-5}' y1='{hz0}' x2='{hx0+5}' y2='{hz0}' stroke='{MUTED}'/><line x1='{hx0-5}' y1='{hz1}' x2='{hx0+5}' y2='{hz1}' stroke='{MUTED}'/>")
out.append(f"<text x='{hx0+8}' y='{(hz0+hz1)/2}' font-size='12' fill='{MUTED}'>50cm</text>")
# lights
for (lx_cm, flip) in ((6, 1), (64, -1)):
    lx_px, lz_px = Q(lx_cm, 42)
    out.append(f"<circle cx='{lx_px}' cy='{lz_px}' r='9' fill='#fde68a' stroke='{AMBER}'/>")
    tx_px, tz_px = Q(35, 2)
    out.append(f"<line x1='{lx_px}' y1='{lz_px+9}' x2='{tx_px - flip*60}' y2='{tz_px}' stroke='{AMBER}' stroke-width='1' stroke-dasharray='3 4'/>")
lx, lz = Q(10, 47.5); out.append(f"<text x='{lx}' y='{lz}' font-size='11' fill='{AMBER}' text-anchor='middle'>ライト（斜め上から2灯、テカリ防止）</text>")

out.append("</svg>")
Path(__file__).resolve().parent.mkdir(exist_ok=True)
(Path(__file__).resolve().parent / "layout.svg").write_text("\n".join(out), encoding="utf-8")
print("svg written")

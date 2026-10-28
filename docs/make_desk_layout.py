"""机全体の配置図（真上から・単位 cm、1cm = 5px）。"""
from pathlib import Path

S = 5
OX, OY = 70, 70
def P(x, y): return OX + x * S, OY + y * S

INK = "#1f2937"; MUTED = "#6b7280"; GRID = "#e5e7eb"; ACCENT = "#2563eb"; AMBER = "#d97706"; RED = "#dc2626"; GREEN = "#16a34a"
F = "font-family='Noto Sans CJK JP, Hiragino Sans, Meiryo, Yu Gothic, sans-serif'"
W, H = 860, 500
o = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' width='{W}' height='{H}' {F}>",
     f"<rect width='{W}' height='{H}' fill='white'/>",
     f"<text x='{OX}' y='36' font-size='20' font-weight='700' fill='{INK}'>机全体の配置（真上から・単位 cm）</text>",
     f"<text x='{OX+360}' y='36' font-size='12' fill='{MUTED}'>机 140×60cm。手前（図の下）に自分が座る。</text>"]

# desk
x0, y0 = P(0, 0)
o.append(f"<rect x='{x0}' y='{y0}' width='{140*S}' height='{60*S}' fill='#fafafa' stroke='{INK}' stroke-width='2'/>")
for i in range(0, 141, 10):
    x, _ = P(i, 0); o.append(f"<line x1='{x}' y1='{y0}' x2='{x}' y2='{y0+60*S}' stroke='{GRID}'/>")
    o.append(f"<text x='{x}' y='{y0+60*S+14}' font-size='10' fill='{MUTED}' text-anchor='middle'>{i}</text>")
for j in range(0, 61, 10):
    _, y = P(0, j); o.append(f"<line x1='{x0}' y1='{y}' x2='{x0+140*S}' y2='{y}' stroke='{GRID}'/>")
    o.append(f"<text x='{x0-6}' y='{y+4}' font-size='10' fill='{MUTED}' text-anchor='end'>{j}</text>")
o.append(f"<text x='{x0+140*S/2}' y='{y0-8}' font-size='11' fill='{MUTED}' text-anchor='middle'>奥（壁側）</text>")
o.append(f"<text x='{x0+140*S/2}' y='{y0+60*S+30}' font-size='11' fill='{MUTED}' text-anchor='middle'>手前（自分が座る側）</text>")

# clearance zone around follower (mat 5..75 x 10..60) -> no objects within 40cm of base front/sides: show dashed box 0..80 x 5..60
cx, cy = P(0, 5)
o.append(f"<rect x='{cx}' y='{cy}' width='{80*S}' height='{55*S}' fill='none' stroke='{AMBER}' stroke-width='1.5' stroke-dasharray='6 5'/>")
lx, ly = P(1.5, 8.2); o.append(f"<text x='{lx}' y='{ly}' font-size='11' fill='{AMBER}'>腕の可動域：ここにPCやコップを置かない</text>")

# follower mat 70x50 at (5,10)
mx, my = P(5, 10)
o.append(f"<rect x='{mx}' y='{my}' width='{70*S}' height='{50*S}' fill='#eef2ff' stroke='{INK}' stroke-width='1.5'/>")
lx, ly = P(40, 13.5); o.append(f"<text x='{lx}' y='{ly}' font-size='12' fill='{INK}' text-anchor='middle' font-weight='700'>フォロワー作業エリア 70×50cm（平面図の範囲）</text>")
# trays inside: supply (22..36, 32..40) tray (43..59, 30..42)   [mat coords +5,+10]
sx, sy = P(20, 31); o.append(f"<rect x='{sx}' y='{sy}' width='{12.7*S}' height='{8.7*S}' fill='#fff7ed' stroke='{INK}'/>")
lx, ly = P(26.3, 43); o.append(f"<text x='{lx}' y='{ly}' font-size='10' fill='{INK}' text-anchor='middle'>補充元</text>")
tx, ty = P(41, 21); o.append(f"<rect x='{tx}' y='{ty}' width='{20*S}' height='{24*S}' fill='#e5e7eb' stroke='{INK}'/>")
for i, lab in enumerate("ABC"):
    rx, ry = P(41.5 + i * 6.5, 22); o.append(f"<rect x='{rx}' y='{ry}' width='{6*S}' height='{22*S}' fill='#374151' stroke='{INK}' stroke-width='0.8'/>")
    lx, ly = P(44.5 + i * 6.5, 42.5); o.append(f"<text x='{lx}' y='{ly}' font-size='10' fill='white' text-anchor='middle'>{lab}</text>")
lx, ly = P(62.5, 32); o.append(f"<text x='{lx}' y='{ly}' font-size='10' fill='{INK}'>客室トレイ</text>")
lx, ly = P(62.5, 35); o.append(f"<text x='{lx}' y='{ly}' font-size='9' fill='{MUTED}'>（カトラリー</text>")
lx, ly = P(62.5, 37.6); o.append(f"<text x='{lx}' y='{ly}' font-size='9' fill='{MUTED}'>トレー）</text>")
# follower base clamped at front edge (34..46, 48..60)
bx, by = P(34, 48); o.append(f"<rect x='{bx}' y='{by}' width='{12*S}' height='{12*S}' fill='#d1d5db' stroke='{INK}' stroke-width='1.5'/>")
lx, ly = P(40, 55); o.append(f"<text x='{lx}' y='{ly}' font-size='10' fill='{INK}' text-anchor='middle' font-weight='700'>フォロワー</text>")
lx, ly = P(40, 58.5); o.append(f"<text x='{lx}' y='{ly}' font-size='9' fill='{MUTED}' text-anchor='middle'>手前の縁にクランプ</text>")
# camera over (40,36)
ccx, ccy = P(40, 36)
o.append(f"<circle cx='{ccx}' cy='{ccy}' r='7' fill='none' stroke='{ACCENT}' stroke-width='2'/><circle cx='{ccx}' cy='{ccy}' r='2' fill='{ACCENT}'/>")
# camera arm from back edge clamp at (40, 0)
ax, ay = P(40, 0)
o.append(f"<rect x='{ax-8}' y='{ay-4}' width='16' height='10' fill='{ACCENT}'/>")
o.append(f"<line x1='{ax}' y1='{ay+6}' x2='{ccx}' y2='{ccy-7}' stroke='{ACCENT}' stroke-width='3'/>")
lx, ly = P(7, 20); o.append(f"<text x='{lx}' y='{ly}' font-size='11' fill='{ACCENT}'>カメラアーム（奥の縁にクランプ、高さ50cm）</text>")
lx, ly = P(7, 23.5); o.append(f"<text x='{lx}' y='{ly}' font-size='10' fill='{ACCENT}'>レンズはトレイ2つの中間の真上</text>")

# lights at (3,3) and (78,3)
for (lx_cm, ly_cm) in ((3, 3), (78, 3)):
    px, py = P(lx_cm, ly_cm); o.append(f"<circle cx='{px}' cy='{py}' r='8' fill='#fde68a' stroke='{AMBER}'/>")
lx, ly = P(6, 4.5); o.append(f"<text x='{lx}' y='{ly}' font-size='10' fill='{AMBER}'>ライト2灯（斜め上から、左右の奥）</text>")

# PC at (85..120, 2..28)
px, py = P(85, 2); o.append(f"<rect x='{px}' y='{py}' width='{35*S}' height='{26*S}' fill='#f3f4f6' stroke='{INK}' stroke-width='1.5'/>")
lx, ly = P(102.5, 14); o.append(f"<text x='{lx}' y='{ly}' font-size='12' fill='{INK}' text-anchor='middle' font-weight='700'>ノートPC</text>")
lx, ly = P(102.5, 18); o.append(f"<text x='{lx}' y='{ly}' font-size='9' fill='{MUTED}' text-anchor='middle'>USBは両腕とカメラの3本</text>")

# leader at (95..125, 30..60), base clamped front edge (104..116, 48..60)
lx0, ly0 = P(95, 30); o.append(f"<rect x='{lx0}' y='{ly0}' width='{30*S}' height='{30*S}' fill='#ecfdf5' stroke='{INK}' stroke-width='1.5'/>")
bx, by = P(104, 48); o.append(f"<rect x='{bx}' y='{by}' width='{12*S}' height='{12*S}' fill='#d1d5db' stroke='{INK}' stroke-width='1.5'/>")
lx, ly = P(110, 35); o.append(f"<text x='{lx}' y='{ly}' font-size='12' fill='{INK}' text-anchor='middle' font-weight='700'>リーダー 30×30cm</text>")
lx, ly = P(110, 39); o.append(f"<text x='{lx}' y='{ly}' font-size='9' fill='{MUTED}' text-anchor='middle'>利き手側・手前の縁にクランプ</text>")

# operator chair and tripod (below desk)
ox, oy = P(110, 68); o.append(f"<ellipse cx='{ox}' cy='{oy}' rx='{10*S}' ry='{5*S}' fill='none' stroke='{MUTED}' stroke-dasharray='4 3'/>")
o.append(f"<text x='{ox}' y='{oy+4}' font-size='11' fill='{MUTED}' text-anchor='middle'>自分（記録のとき）</text>")
tpx, tpy = P(12, 70)
o.append(f"<circle cx='{tpx}' cy='{tpy}' r='9' fill='none' stroke='{RED}' stroke-width='2'/><circle cx='{tpx}' cy='{tpy}' r='3' fill='{RED}'/>")
o.append(f"<line x1='{tpx+7}' y1='{tpy-6}' x2='{tx-8}' y2='{ty+12*S+4}' stroke='{RED}' stroke-width='1' stroke-dasharray='3 3'/>")
o.append(f"<text x='{tpx+14}' y='{tpy+4}' font-size='11' fill='{RED}'>スマホ三脚（斜め前45°、撮影のとき）</text>")
o.append("</svg>")
(Path(__file__).resolve().parent / "desk_layout.svg").write_text("\n".join(o), encoding="utf-8")
print("ok")

"""Generates the app icons (PNG/ICO/ICNS) with Pillow: three dot-matrix progress lines.
Run: python tools/make_icons.py   (or replace with `npx tauri icon your-1024.png`)"""
import math, os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(__file__), "..", "src-tauri", "icons")
S = 1024
N = 13                       # dot grid size
AMBER = (255, 176, 0)

def master():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = 64
    d.rounded_rectangle([pad, pad, S - pad, S - pad], radius=200, fill=(20, 20, 22, 255))
    inner = S - 2 * pad - 120
    pitch = inner / N
    ox = oy = pad + 60
    c = (N - 1) // 2
    for gy in range(N):
        for gx in range(N):
            # A loading bar: rounded frame (rows 3-9) with the left 60% filled.
            # Three stacked progress lines (day / month / year), different lengths.
            fill = (gy == 3 and 1 <= gx <= 10) or (gy == 6 and 1 <= gx <= 7) or (gy == 9 and 1 <= gx <= 4)
            frame = gy in (3, 6, 9) and gx in (0, N - 1)
            lit = frame or fill
            r = pitch * 0.38
            x = ox + gx * pitch + pitch / 2
            y = oy + gy * pitch + pitch / 2
            col = AMBER + (255,) if lit else (54, 42, 19, 255)
            d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    return img

m = master()
os.makedirs(OUT, exist_ok=True)
for name, size in [("32x32.png", 32), ("128x128.png", 128), ("128x128@2x.png", 256), ("icon.png", 512)]:
    m.resize((size, size), Image.LANCZOS).save(os.path.join(OUT, name))
m.save(os.path.join(OUT, "icon.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
m.save(os.path.join(OUT, "icon.icns"))
print("icons written to", os.path.abspath(OUT))

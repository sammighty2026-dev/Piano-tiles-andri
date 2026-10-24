from PIL import Image, ImageDraw

BG = (18, 18, 28)
PINK = (255, 0, 140)
GOLD = (255, 200, 50)
LINE = (45, 45, 70)


def draw_icon(size):
    img = Image.new("RGB", (size, size), BG)
    d = ImageDraw.Draw(img)
    col = size // 4
    for i in range(1, 4):
        d.line([(i * col, 0), (i * col, size)], fill=LINE, width=max(2, size // 128))
    pad = size // 28
    r = size // 14
    tiles = [(0, 0.08, 0.50, PINK), (1, 0.38, 0.80, PINK), (2, 0.00, 0.34, GOLD), (3, 0.55, 0.95, PINK)]
    for c, top, bottom, color in tiles:
        x0 = c * col + pad
        x1 = (c + 1) * col - pad
        d.rounded_rectangle([x0, int(top * size), x1, int(bottom * size)], radius=r, fill=color)
    return img


draw_icon(512).save("icon.png")

pre = Image.new("RGB", (1024, 1024), BG)
small = draw_icon(384)
pre.paste(small, (320, 320))
pre.save("presplash.png")
print("icons made")

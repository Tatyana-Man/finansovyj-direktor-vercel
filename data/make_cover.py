#!/usr/bin/env python3
"""Обложка статьи data/img/stati-<slug>.jpg 1200×630 — в фирменном стиле, но каждый раз другая (цвет + рисунок справа).

Запуск: python3 data/make_cover.py <slug> "<Заголовок статьи>" <минут чтения> [тема]
Тему подбирать не нужно: скрипт берёт ту, что не встречалась у последних статей (журнал — data/covers.json).
Список тем: python3 data/make_cover.py --list
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
LOG = HERE / "covers.json"
F = "/System/Library/Fonts/Supplemental/Arial%s.ttf"
DARK = (20, 41, 42)

# тема: фон, акцент, цвет заголовка, второй цвет рисунка, рисунок
# порядок важен: подряд идут разные рисунки, следующая статья берёт самую давно не использованную тему
THEMES = {
    "teal-night":  ((20, 41, 42), (240, 140, 100), (255, 255, 255), (36, 64, 65), "stairs"),
    "paper":       ((250, 247, 241), (15, 110, 106), DARK, (228, 241, 238), "bars"),
    "coral":       ((253, 241, 228), (212, 87, 47), DARK, (250, 214, 196), "columns"),
    "sea":         ((15, 110, 106), (250, 215, 160), (255, 255, 255), (13, 92, 89), "line"),
    "sand":        ((243, 235, 222), (122, 74, 140), DARK, (226, 210, 232), "circles"),
    "ink-amber":   ((20, 41, 42), (217, 138, 31), (255, 255, 255), (36, 64, 65), "columns"),
    "mint-paper":  ((233, 244, 236), (47, 125, 79), DARK, (200, 230, 210), "line"),
    "steel":       ((232, 238, 244), (61, 90, 115), DARK, (200, 214, 228), "bars"),
}


def decor(d, kind, acc, alt):
    if kind == "bars":
        for y, x in ((120, 820), (260, 888), (400, 932)):
            d.rounded_rectangle((x, y, 1140, y + 50), 18, fill=acc)
    elif kind == "stairs":
        for i, x in enumerate((820, 858, 888, 914, 932, 944)):
            d.rounded_rectangle((x, 120 + i * 70, 1140, 170 + i * 70), 16, fill=acc if i % 2 == 0 else alt)
    elif kind == "columns":  # столбчатая диаграмма
        for i, h in enumerate((140, 210, 170, 280, 340)):
            x = 860 + i * 56
            d.rounded_rectangle((x, 520 - h, x + 40, 520), 10, fill=acc if i == 4 else alt)
        d.line((850, 524, 1150, 524), fill=acc, width=4)
    elif kind == "circles":
        d.ellipse((860, 110, 1140, 390), fill=alt)
        d.ellipse((960, 260, 1150, 450), fill=acc)
        d.ellipse((880, 400, 960, 480), outline=acc, width=8)
    elif kind == "line":  # растущий график
        pts = [(850, 470), (920, 410), (980, 440), (1050, 300), (1140, 180)]
        for x, y in pts:
            d.line((x, y, x, 520), fill=alt, width=3)
        d.line(pts, fill=acc, width=10, joint="curve")
        for x, y in pts:
            d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=acc)


def wrap(d, text, font, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= width or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    return lines + [cur]


def main():
    if "--list" in sys.argv:
        print("\n".join(THEMES)); return
    slug, title, read = sys.argv[1], sys.argv[2], sys.argv[3]
    log = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else []
    log = [x for x in log if x["slug"] != slug]
    if len(sys.argv) > 4:
        theme = sys.argv[4]
    else:  # самая давно не использованная тема
        used = [x["theme"] for x in log]
        theme = min(THEMES, key=lambda t: (max((i for i, u in enumerate(used) if u == t), default=-1), list(THEMES).index(t)))
    bg, acc, ink, alt, kind = THEMES[theme]
    im = Image.new("RGB", (1200, 630), bg)
    d = ImageDraw.Draw(im)
    dark_bg = sum(bg) < 300
    d.rounded_rectangle((60, 66, 150, 124), 6, fill=(212, 87, 47))
    d.text((105, 95), "CFO", font=ImageFont.truetype(F % " Bold", 26), fill=(255, 255, 255), anchor="mm")
    d.text((170, 95), "Журнал · CFO Навигатор", font=ImageFont.truetype(F % "", 24), fill=acc, anchor="lm")
    d.rectangle((0, 618, 1200, 630), fill=acc)
    decor(d, kind, acc, alt or acc)
    for size in (52, 46, 40):
        font = ImageFont.truetype(F % " Bold", size)
        lines = wrap(d, title, font, 740)
        if len(lines) <= 4:
            break
    step = int(size * 1.33)
    y0 = 330 - len(lines) * step // 2
    for i, l in enumerate(lines):
        d.text((60, y0 + i * step), l, font=font, fill=ink)
    d.text((60, 570), f"Читать {read} мин", font=ImageFont.truetype(F % "", 22), fill=acc, anchor="lm")
    im.save(HERE / "img" / f"stati-{slug}.jpg", quality=88)
    log.append({"slug": slug, "theme": theme})
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Обложка stati-{slug}.jpg, тема {theme}")


if __name__ == "__main__":
    main()

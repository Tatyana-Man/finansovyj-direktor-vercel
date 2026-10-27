#!/usr/bin/env python3
"""Скриншоты первого экрана страниц курсов -> data/img/<id>.jpg (модуль screenshotter из course_article_service).

Запуск интерпретатором course_article_service:
  "/Users/tatyana/Downloads/course_article_service 4/venv/bin/python" data/make_images.py [--force]
Уже снятые скриншоты не переснимаются без --force.
"""
import json, os, sys
from pathlib import Path

SERVICE = Path("/Users/tatyana/Downloads/course_article_service 4")
sys.path.insert(0, str(SERVICE))
os.chdir(SERVICE)  # модули сервиса читают data/ относительно своей папки
import screenshotter as shot  # noqa: E402

HERE = Path(__file__).parent
IMG = HERE / "img"


def main():
    IMG.mkdir(exist_ok=True)
    force = "--force" in sys.argv
    _d = json.loads((HERE / "courses.json").read_text(encoding="utf-8"))
    courses = _d["courses"] + _d.get("fm_courses", [])  # каталог + смежные направления
    # --shard K/N — снимать только каждый N-й курс начиная с K (для параллельного запуска нескольких процессов)
    shard = next((a.split("=")[1] for a in sys.argv if a.startswith("--shard=")), None)
    if shard:
        k, n = map(int, shard.split("/"))
        courses = courses[k::n]
    for c in courses:
        out = IMG / f"{c['id']}.jpg"
        if out.exists() and not force:
            continue
        try:
            png = shot.capture_png(c["url"], 1280, 800, wait=5.0, timeout=40)
            jpg, _ = shot._compress_jpeg(png, max_width=640, quality=75)
            out.write_bytes(jpg)
            print("OK ", c["id"])
        except Exception as e:
            print("-- ", c["id"], str(e).splitlines()[0][:100])
        finally:
            shot.close_driver()


if __name__ == "__main__":
    main()

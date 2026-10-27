#!/usr/bin/env python3
"""Еженедельная проверка курсов (запускается по понедельникам через launchd, см. README).

1. Открывает страницу каждого курса (каталог + смежные направления).
2. Страница ответила 200 → курсу ставится сегодняшняя дата проверки в data/verified.json.
   Не ответила / ошибка → дата НЕ обновляется, курс попадает в отчёт data/verify_report.txt.
3. Общая дата «Данные проверены» = дата последнего запуска.
4. Пересобирает сайт: site/ (просмотр) и deploy/ (публикация).

Дату не ставим «вслепую»: проверенной считается только страница, которая реально открылась.
"""
import datetime, json, ssl, subprocess, sys, urllib.request, concurrent.futures as cf
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
CTX = ssl._create_unverified_context()


def check(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40, context=CTX)
        return url, r.status, ""
    except Exception as e:
        return url, getattr(e, "code", None), str(e)[:120]


def main():
    today = datetime.date.today().isoformat()
    data = json.loads((DATA / "courses.json").read_text(encoding="utf-8"))
    items = data["courses"] + data.get("fm_courses", [])
    vpath = DATA / "verified.json"
    ver = json.loads(vpath.read_text(encoding="utf-8")) if vpath.exists() else {"last_run": None, "courses": {}}
    with cf.ThreadPoolExecutor(8) as ex:
        results = list(ex.map(check, [c["url"] for c in items]))
    bad = []
    for url, status, err in results:
        if status == 200:
            ver["courses"][url] = today
        else:
            bad.append(f"{status or 'ошибка'}\t{url}\t{err}")
    ver["last_run"] = today
    vpath.write_text(json.dumps(ver, ensure_ascii=False, indent=1), encoding="utf-8")
    report = [f"Проверка {today}: страниц {len(results)}, открылись {len(results) - len(bad)}, проблемы {len(bad)}"] + bad
    (DATA / "verify_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(report[0])
    for line in bad:
        print("  ", line)
    for args in ([], ["--prod"]):
        subprocess.run([sys.executable, str(ROOT / "build.py"), *args], check=True, cwd=ROOT)


if __name__ == "__main__":
    main()

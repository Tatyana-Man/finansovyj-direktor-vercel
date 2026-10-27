#!/usr/bin/env python3
"""Покрытие ключевых тем финансового директора: какие темы упоминаются на странице курса на сайте школы.

Скачивает страницу каждого курса каталога, убирает скрипты/стили и ищет темы по ключевым словам.
Тема считается упомянутой, если ключевые слова встречаются на странице не меньше 2 раз (одиночное
упоминание часто бывает в меню или списке других курсов школы). Результат — data/coverage.json.
Это не оценка качества курса, а сигнал «эта тема есть в описании программы».
"""
import json, re, ssl, html, time, urllib.request, concurrent.futures as cf
from pathlib import Path

HERE = Path(__file__).parent
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
CTX = ssl._create_unverified_context()

TOPICS = [
    ("budget", "Бюджетирование", r"бюджет"),
    ("cash", "Денежные потоки и платёжный календарь", r"денежн\w*\s+пото|cash[\s-]?flow|\bДДС\b|платёжн\w*\s+календар|платежн\w*\s+календар"),
    ("mgmt", "Управленческий учёт и отчётность", r"управленческ\w*\s+(?:учёт|учет|отчётн|отчетн)"),
    ("analysis", "Анализ финансовой отчётности", r"анализ\w*\s+(?:финансов\w*\s+)?отчётност|анализ\w*\s+(?:финансов\w*\s+)?отчетност|финансов\w*\s+анализ|коэффициент"),
    ("ifrs", "МСФО", r"МСФО|IFRS"),
    ("invest", "Оценка инвестпроектов и бизнеса (NPV, IRR, DCF)", r"\bNPV\b|\bIRR\b|\bDCF\b|оценк\w*\s+(?:бизнес|стоимост|инвестиц|проект)|инвестиционн\w*\s+(?:анализ|проект)"),
    ("model", "Финансовое моделирование", r"финансов\w*\s+модел"),
    ("funding", "Привлечение финансирования: кредиты, лизинг, инвесторы", r"кредит\w*|лизинг|облигаци|привлечени\w*\s+(?:финансир|инвестиц|капитал)"),
    ("tax", "Налоговое планирование", r"налогов\w*\s+(?:планир|нагрузк|оптимиз)|налогообложени"),
    ("risk", "Управление финансовыми рисками", r"риск"),
    ("team", "Организация финансовой службы", r"финансов\w*\s+служб|финансов\w*\s+отдел|регламент"),
    ("digital", "Цифровые инструменты: Excel, BI, ИИ", r"\bExcel\b|Power\s?BI|\bBI\b|нейросет|искусственн\w*\s+интеллект|\bИИ\b|автоматизац"),
]


def fetch(url):
    t = None
    for attempt in range(3):  # сайты иногда сбрасывают соединение при частых запросах — повторяем с паузой
        try:
            t = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40, context=CTX).read().decode("utf-8", "ignore")
            break
        except Exception:
            time.sleep(3 * (attempt + 1))
    if t is None:
        return url, None
    t = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", t)
    return url, re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def main():
    courses = json.loads((HERE / "courses.json").read_text(encoding="utf-8"))["courses"]
    with cf.ThreadPoolExecutor(3) as ex:
        pages = dict(ex.map(fetch, [c["url"] for c in courses]))
    out = {"topics": [[k, name] for k, name, _ in TOPICS], "courses": {}}
    for c in courses:
        t = pages.get(c["url"])
        if not t:
            continue
        out["courses"][c["url"]] = [k for k, _, rx in TOPICS if len(re.findall(rx, t, re.I)) >= 2]
    (HERE / "coverage.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for c in courses:
        cov = out["courses"].get(c["url"])
        print(f"{c['id'][:40]:40} {('нет страницы' if cov is None else str(len(cov)) + '/12 ' + ','.join(cov))}")


if __name__ == "__main__":
    main()

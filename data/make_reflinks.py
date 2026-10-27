#!/usr/bin/env python3
"""Добавляет реферальные ссылки в data/courses.json через модули ref-link-service (логика сетей не меняется).

keyword (sub2) — по правилу course_article_service (pipeline.apply_bulk_keyword): один keyword на весь
список; если у одной школы (домена ссылки курса) несколько курсов — к keyword добавляется номер 1, 2, 3…
по каждой школе отдельно; если курс у школы один — номер не добавляется.
Каталог (порядок показа: приоритет школ, затем цена) — keyword fin-dir; блок «Финансовый менеджмент» —
отдельный список с keyword fin-dir-dop (как extra_keyword в batch.py), нумерация в каждом списке своя.

Выданные keyword закреплены в data/keywords.json (url курса -> keyword) и при пересборке не меняются.
Новому курсу выдаётся следующий свободный номер его школы (домена) в своём списке: max(номеров) + 1,
где keyword без номера считается номером 1 (курс был у школы единственным). Номера удалённых курсов
не переиспользуются (остаются в реестре). Первый курс новой школы получает keyword без номера.

Запуск интерпретатором ref-link-service:
  /Users/tatyana/Downloads/ref-link-service/venv/bin/python data/make_reflinks.py
"""
import json, sys, urllib.parse
from pathlib import Path

SUB1, KEYWORD, KEYWORD_DOP = "vercel2", "fin-dir", "fin-dir-dop"
REF_SERVICE = Path("/Users/tatyana/Downloads/ref-link-service")
sys.path.insert(0, str(REF_SERVICE))
import referral_links as rl  # noqa: E402
import advcake_feed as af  # noqa: E402

ADVCAKE_KEY = "XW6Bxypl4NPZcjU4"  # тот же ключ по умолчанию, что в ref-link-service/app.py
HERE = Path(__file__).parent


def get_domain(url):
    """Как course_scraper.get_domain в course_article_service."""
    return urllib.parse.urlparse(url).netloc.replace("www.", "").strip("/")


def apply_bulk_keyword(urls, keyword):
    """Повтор pipeline.apply_bulk_keyword: нумерация keyword по домену, если курсов школы > 1."""
    counts = {}
    for u in urls:
        counts[get_domain(u)] = counts.get(get_domain(u), 0) + 1
    seen, out = {}, []
    for u in urls:
        d = get_domain(u)
        if counts[d] > 1:
            seen[d] = seen.get(d, 0) + 1
            out.append(f"{keyword}{seen[d]}")
        else:
            out.append(keyword)
    return out


def keyword_num(kw, base):
    """fin-dir -> 1, fin-dir3 -> 3; None, если keyword не из этого списка."""
    if kw == base:
        return 1
    tail = kw[len(base):] if kw.startswith(base) else ""
    return int(tail) if tail.isdigit() else None


def assign_keywords(items, base, registry):
    """Закреплённые keyword берём из реестра; новым курсам — следующий свободный номер школы."""
    out = []
    for c in items:
        u = c["url"]
        if u in registry:
            out.append(registry[u])
            continue
        d = get_domain(u)
        nums = [keyword_num(kw, base) for url, kw in registry.items() if get_domain(url) == d]
        nums = [n for n in nums if n is not None]
        kw = f"{base}{max(nums) + 1}" if nums else base
        registry[u] = kw
        out.append(kw)
    return out


def display_order(items, prio):
    return sorted(items, key=lambda c: (prio.get(c["domain"], 999), c["domain"], c["price"] if c["price"] is not None else 10**9))


def main():
    p = HERE / "courses.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    prio = {d: i for i, (_, ds) in enumerate(json.loads((HERE / "priorities.json").read_text(encoding="utf-8"))) for d in ds}
    main_items = display_order(data["courses"], prio)
    dop_items = display_order(data.get("fm_courses", []), prio)
    items = main_items + dop_items
    reg_path = HERE / "keywords.json"
    if reg_path.exists():
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
    else:  # первый запуск: нумерация по правилу apply_bulk_keyword, дальше номера закреплены
        reg = {"main": dict(zip([c["url"] for c in main_items], apply_bulk_keyword([c["url"] for c in main_items], KEYWORD))),
               "dop": dict(zip([c["url"] for c in dop_items], apply_bulk_keyword([c["url"] for c in dop_items], KEYWORD_DOP)))}
    keywords = assign_keywords(main_items, KEYWORD, reg["main"]) + assign_keywords(dop_items, KEYWORD_DOP, reg["dop"])
    reg_path.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    for c, kw in zip(items, keywords):
        net = rl.choose_network(c["domain"])
        base_url = erid = m = None
        if net == "advcake":
            base_url, erid, m = af.get_erid_for_domain(c["domain"], ADVCAKE_KEY)
        link, ok, note = rl.resolve_course_link(c["url"], c["domain"], SUB1, kw, base_url or "", erid or "", m or "5")
        c.update(ref_url=link, ref_keyword=kw, ref_network=net if ok else None, ref_note=note)
        print(f"{'OK ' if ok else '-- '}{get_domain(c['url']):22} {kw:10} {c['title'][:45]}")
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

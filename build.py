#!/usr/bin/env python3
"""Генератор статического агрегатора курсов финдиректора: data/courses.json -> site/.

Все ссылки относительные (…/index.html), поэтому сайт открывается двойным кликом по site/index.html.
"""
import json, html, statistics, shutil, math, urllib.parse, sys, re
from pathlib import Path

ROOT = Path(__file__).parent
# Домен сайта — для canonical, Open Graph, sitemap.xml, robots.txt и микроразметки.
SITE_URL = "https://finansovyj-direktor.vercel.app"
# Счётчик аналитики (вставляется только в боевую версию deploy/). Пусто, пока владелец не пришлёт новый код.
METRIKA = ""
# Мета-теги подтверждения прав в Яндекс Вебмастере и Google Search Console. Пусто — теги не выводятся.
YANDEX_VERIFICATION = ""
GOOGLE_VERIFICATION = ""
# title главной задан владельцем (длиннее общего лимита 70 символов — исключение в check_meta)
H_TITLE = "Обучение на Финансового Директора (CFO) — каталог онлайн-курсов: цены, сроки, отзывы учеников"
SITE_NAME = "CFO Навигатор"
SITE_TAGLINE = "обучение финансовых директоров"
# --prod: сборка для хостинга в deploy/ с «чистыми» ссылками (/perepodgotovka/); без флага — site/ для просмотра
# двойным кликом (ссылки на …/index.html, их дубли закрываются canonical и robots.txt).
CLEAN = "--prod" in sys.argv
OUT = ROOT / ("deploy" if CLEAN else "site")
DATA = json.loads((ROOT / "data/courses.json").read_text(encoding="utf-8"))
C = DATA["courses"]
R = DATA["reviews"]
SCHOOL = {s["slug"]: s for s in DATA["schools"] if s["slug"]}
REL = DATA.get("fm_courses", [])  # смежные направления
# Дата проверки: data/verified.json пишет weekly_check.py (по понедельникам); до первого запуска — дата сбора данных
# Дата «Данные проверены» — последний понедельник. В HTML подставляется при сборке, а скрипт на странице
# (assets/app.js) пересчитывает её у посетителя, поэтому надпись меняется каждый понедельник без пересборки.
import datetime as _dt
_today = _dt.date.today()
LAST_CHECK = (_today - _dt.timedelta(days=_today.weekday())).isoformat()
for _c in C + REL:
    _c["checked"] = LAST_CHECK


def ru_date(iso):
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


def school_slug(domain):
    return re.sub(r"[^a-z0-9]+", "-", domain.lower()).strip("-")


SCHOOL_DOMAINS = {}  # название школы -> домен (для страниц школ)
for _c in C + REL:
    SCHOOL_DOMAINS.setdefault(_c["school"], _c["domain"])
SCHOOL_PAGE = {n: school_slug(d) for n, d in SCHOOL_DOMAINS.items() if any(c["school"] == n for c in C)}  # страницы — у школ из каталога ФД
# Число отзывов о курсах по финансам для карточек
for _c in C:
    _rs = [r["rating"] for r in R if r["about_finance"] and r["school_slug"] == _c["school_slug"]]
    _c["school_rating"], _c["school_reviews"] = (statistics.mean(_rs), len(_rs)) if _rs else (None, 0)
# Приоритет школ — data/priorities.json: чем выше в списке, тем раньше показываем
PRIO = {d: i for i, (_, ds) in enumerate(json.loads((ROOT / "data/priorities.json").read_text(encoding="utf-8"))) for d in ds}


def order(items):
    return sorted(items, key=lambda c: (PRIO.get(c["domain"], 999), c["domain"], c["price"] if c["price"] is not None else 10**9))



TYPE_NAME = {"perepodgotovka": "Переподготовка", "povyshenie": "Повышение квалификации", "kurs": "Сертификат школы"}  # сертификат школы — документ без государственного статуса
FORMAT_NAME = {"online": "Онлайн", "mixed": "Очно и онлайн"}
e = html.escape
NB = " "


def rub(v):
    if v is None:
        return "по запросу"
    return f"{v:,.0f}".replace(",", NB) + NB + "₽"


def plural(n, one, few, many):
    n = abs(int(n)) % 100
    if 11 <= n <= 19: return many
    return {1: one, 2: few, 3: few, 4: few}.get(n % 10, many)


def n_prog(n): return f"{n} {plural(n, 'программа', 'программы', 'программ')}"
def n_school(n): return f"{n} {plural(n, 'школа', 'школы', 'школ')}"
def n_school_gen(n): return f"{n} {plural(n, 'школы', 'школ', 'школ')}"  # «от 4 школ», «от 1 школы»
def n_rev(n): return f"{n} {plural(n, 'отзыв', 'отзыва', 'отзывов')}"


# --- Посадочные ---------------------------------------------------------------
LANDINGS = {
    "perepodgotovka": dict(
        h1="Переподготовка на финансового директора (CFO) с дипломом", short="Переподготовка",
        f=lambda c: c["type"] == "perepodgotovka",
        define="Переподготовка — вид дополнительного профессионального образования. По итогу выдают диплом о профессиональной переподготовке, который даёт право работать в новой сфере. Учиться можно, если у вас есть высшее или среднее профессиональное образование.",
        faq=[("Кого принимают на переподготовку?", "Тех, у кого есть высшее или среднее профессиональное образование, и студентов, которые его получают (ст. 76 закона «Об образовании в РФ»)."),
             ("Диплом и удостоверение — в чём разница?", "Диплом о переподготовке открывает новый вид деятельности. Удостоверение о повышении квалификации подтверждает, что вы обновили знания в своей профессии.")]),
    "povyshenie-kvalifikacii": dict(
        h1="Повышение квалификации для финансовых директоров", short="Повышение квалификации",
        f=lambda c: c["type"] == "povyshenie",
        define="Программы для тех, кто уже работает в финансах и хочет освоить новую тему или обновить знания внутри своей профессии. По итогу выдают удостоверение о повышении квалификации.",
        faq=[]),
    "kursy-shkol": dict(
        h1="Курсы финансового директора с сертификатом школы", short="Курсы школ",
        f=lambda c: c["type"] == "kurs",
        define="Курсы, где школа не указывает на странице диплом о переподготовке или удостоверение, а выдаёт собственный сертификат или диплом — документ без государственного статуса. Если документ нужен для работодателя, спросите школу о нём до оплаты.",
        faq=[]),
    "mba": dict(
        h1="MBA и mini-MBA для финансового директора (CFO)", short="MBA",
        f=lambda c: "mba" in c["tags"] or "mini-mba" in c["tags"],
        define="Программы с MBA или mini-MBA в названии. В России MBA не считается уровнем образования, поэтому итоговый документ у программ разный — он указан в карточке каждого курса.",
        faq=[]),
    "dlya-bankov": dict(
        h1="Финансовый директор банка: программы переподготовки", short="Для банков",
        f=lambda c: "bank" in c["tags"],
        define="Переподготовка с уклоном в банковские финансы: регулирование, ликвидность, риски.",
        faq=[]),
    "do-50000": dict(
        h1="Курсы финансового директора до 50 000 ₽ — недорогие программы", short="До 50 000 ₽",
        f=lambda c: c["price"] is not None and c["price"] <= 50000,
        define="Программы стоимостью до 50 000 ₽ включительно. Чаще всего это дистанционная переподготовка от 250 часов, где материалы изучают самостоятельно.",
        faq=[]),
    "korotkie": dict(
        h1="До 4 месяцев: короткие курсы финансового директора", short="До 4 месяцев",
        f=lambda c: c["months"] is not None and c["months"] <= 4,
        define="Программы, срок которых по данным школы не превышает 4 месяцев: интенсивы, короткие онлайн-курсы и ускоренная переподготовка.",
        faq=[]),
    "ochno-i-onlajn": dict(
        h1="Очно и онлайн: курсы финансового директора с живыми занятиями", short="Очно",
        f=lambda c: c["format"] == "mixed",
        define="Программы, где можно ходить на занятия в аудиторию или подключаться к живой трансляции, а не только смотреть записи.",
        faq=[]),
    "dlya-nachinayushchih": dict(
        h1="С нуля: курсы финансового директора для начинающих", short="С нуля",
        f=lambda c: "beg" in c.get("aud", []),
        define="Сюда попали программы, которые школа прямо называет подходящими для старта: «с нуля» или «для начинающих». В них, как правило, есть вводные блоки по бухучёту и чтению отчётности. Помните, что для переподготовки нужно высшее или среднее профессиональное образование.",
        faq=[]),
    "dlya-glavbuhov": dict(
        h1="Из главбуха в финдиректора: курсы для главных бухгалтеров", short="Для главбухов",
        f=lambda c: "acc" in c.get("aud", []),
        define="Главный бухгалтер — частый кандидат на должность финдиректора. В подборке программы, где школа отдельно обращается к главбухам: больше управленческого учёта, бюджетов и финансовой стратегии, меньше проводок.",
        faq=[]),
    "dlya-sobstvennikov": dict(
        h1="Курсы финансового директора для собственников бизнеса", short="Для собственников",
        f=lambda c: "own" in c.get("aud", []),
        define="Владельцу бизнеса не обязательно становиться финдиректором, но разбираться в деньгах своей компании нужно. Здесь курсы, которые школы адресуют предпринимателям: чтение отчётов, расчёт окупаемости, постановка задач финансовой службе.",
        faq=[]),
    "rassrochka": dict(
        h1="В рассрочку: курсы финансового директора с оплатой частями", short="Рассрочка",
        f=lambda c: bool(c["installment"]),
        define="Программы, где школа указывает оплату частями. Выясните, кто даёт рассрочку: если сама школа — кредитного договора обычно нет, если банк — это кредит.",
        faq=[("Дают ли налоговый вычет за обучение?", "Да. При наличии у школы образовательной лицензии можно получить социальный налоговый вычет. Расходы на своё обучение учитываются в пределах 150 000 ₽ в год — это общий лимит вместе с лечением, спортом и другими социальными вычетами. При ставке НДФЛ 13% вернуть можно до 19 500 ₽, при более высокой ставке — больше, но не больше налога, который вы уплатили.")]),
}
REVIEWS = "otzyvy"
MAIN_NAV = ["perepodgotovka", "povyshenie-kvalifikacii", "mba"]
METHOD = "metodika"
ABOUT = "o-nas"
EMAIL = "on-line-kursy@yandex.ru"
sys.path.insert(0, str(ROOT / "data"))
from landing_texts import TEXTS as LTEXT  # noqa: E402  уникальные тексты подборок
from course_program import LICENSES, PROGRAMS, LICENSE_REGISTRY  # noqa: E402  лицензии и программы по модулям
from articles import ARTICLES, DRAFTS  # noqa: E402  статьи раздела /stati/
STATI = "stati"
ART_DATE = "2026-10-10"
# Новые статьи — первыми; при одной дате сохраняется порядок из articles.py (sorted устойчивая)
ARTICLES = sorted(ARTICLES, key=lambda a: a.get("date", ART_DATE), reverse=True)
AUD_NAME = {"beg": "С нуля", "acc": "Для главбухов", "own": "Для собственников"}

# Смежные направления: отдельные страницы /<slug>/
RELATED = {
    "fm": dict(slug="finansovyj-menedzhment", h1="Обучение финансовому менеджменту", tab="Финансовый менеджмент",
               intro="Финансовый менеджер планирует и контролирует деньги отдела или направления. С этой позиции чаще всего вырастают в финдиректора, поэтому курс финменеджмента — короткий путь в профессию или помощь, если вам уже поручили бюджет."),
    "analyst": dict(slug="finansovyj-analitik", h1="Обучение на финансового аналитика", tab="Финансовый аналитик",
                    intro="Аналитик читает отчётность, строит прогнозы и готовит расчёты для решений руководства. Для многих CFO аналитика стала первой ступенью: умение разбирать цифры и строить модели пригодится на любой финансовой должности."),
    "model": dict(slug="finansovoe-modelirovanie", h1="Курсы финансового моделирования и бюджетирования", tab="Финмоделирование и бюджет",
                  intro="Модель и бюджет — то, чем финансовый директор пользуется каждый день. Если вы уже в финансах и не хотите проходить длинную программу, короткий практический курс закроет именно этот навык."),
    "msfo": dict(slug="msfo", h1="Курсы МСФО для финансового директора (CFO)", tab="МСФО",
                 intro="Отчётность по МСФО требуется компаниям, которые работают с иностранными инвесторами, берут крупные банковские кредиты или выпускают облигации. Если это ваш случай, МСФО стоит добавить к основной программе финдиректора."),
}


def link(pre, path):
    if CLEAN:
        return "/" + path
    return f"{pre}{path}index.html" if path else f"{pre}index.html"


def abs_url(path):
    """Канонический адрес страницы: https://домен/путь/ (без index.html)."""
    return f"{SITE_URL}/{path}"


def clip(text, n):
    """Обрезка по границе слова без хвостовой пунктуации (для title/description)."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0].rstrip(" ,.:;—–-")
    return cut + "…"


# Короткие формы школ только для <title> (лимит ~70 символов); на страницах — полные названия
TITLE_SHORT = {"Сити Бизнес Скул (City Business School)": "Сити Бизнес Скул", "Московская Бизнес Школа": "МБШ",
               "Русская Школа Управления": "РШУ"}


def fit_parts(parts, n=160):
    """Описание из частей: обязательная первая, остальные добавляются, пока влезают в n символов."""
    out = parts[0]
    for p_ in parts[1:]:
        if p_ and len(out) + 1 + len(p_) <= n:
            out += " " + p_
    return out if len(out) <= n else clip(out, n)


def first_fit(variants, n):
    """Первый вариант, который укладывается в n символов; иначе обрезанный последний."""
    for v in variants:
        if len(v) <= n:
            return v
    return clip(variants[-1], n)


def stats(items):
    p = [c["price"] for c in items if c["price"] is not None]
    return dict(n=len(items), schools=len({c["school"] for c in items}), min=min(p), med=int(statistics.median(p)), max=max(p))


def promo_price(c):
    """Цена с промокодом: процент или фиксированная сумма в ₽; None, если промокода/цены нет."""
    p = PROMO.get(c["domain"])
    if not p or c["price"] is None:
        return None
    d = p["discount"].replace(" ", "").replace("\u00a0", "")
    if d.endswith("%"):
        return round(c["price"] * (1 - float(d[:-1]) / 100))
    if d.endswith("₽"):
        return max(c["price"] - int(d[:-1]), 0)
    return None


def compare_data():
    """Данные курсов для окна сравнения (встраиваются в страницу)."""
    out = {}
    for c in C:
        p = PROMO.get(c["domain"])
        out[c["id"]] = dict(t=c["title"], s=c["school"], u="kurs/" + c["id"] + ("/" if CLEAN else "/index.html"), r=c["ref_url"],
                            img=("img/" + c["id"] + ".jpg") if (ROOT / "data/img" / f"{c['id']}.jpg").exists() else "",
                            type=TYPE_NAME[c["type"]], p=c["price"], pp=promo_price(c), op=c.get("old_price"),
                            mo=(f'от {rub(c["monthly"])}/мес · {c["monthly_months"]} мес' if c.get("monthly") else ""),
                            pc=(f"{p['code']} (−{p['discount']})" if p else ""), d=c["duration"] or "", m=c["months"],
                            h=c["hours_text"] or "", hn=c["hours"], doc=c["doc"], f=FORMAT_NAME[c["format"]],
                            inst=("есть" if c["installment"] else "нет данных"), rv=c["school_reviews"],
                            pr=PRIO.get(c["domain"], 999), tc=c["type"], aud=c.get("aud", []), fmt=c["format"], dk=doc_short(c)[0],
                            rvu=(f"{REVIEWS}/{'' if CLEAN else 'index.html'}#school={urllib.parse.quote(c['school'])}" if c["school_reviews"] else ""))
    return out


COMPARE_UI = """<div id="cmpBar" hidden><span id="cmpInfo"></span><button class="btn sm" id="cmpOpen" type="button">Сравнить</button><button class="chip" id="cmpClear" type="button">Очистить</button></div>
<div id="cmpModal" hidden role="dialog" aria-modal="true" aria-labelledby="cmpTitle"><div class="cmpbox"><div class="cmphead"><h2 id="cmpTitle">Программы рядом</h2><button class="cmpx" id="cmpClose" type="button" aria-label="Закрыть">×</button></div>
<p class="hint cmphint">Подсветка показывает лучшее значение в каждой строке: ниже цена, короче срок, больше часов и отзывов.</p><div class="cmpwrap" id="cmpTable"></div></div></div>"""


ICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='18' fill='%23c7f23a'/%3E"
        "%3Ctext x='32' y='42' font-size='22' font-family='Arial,Helvetica,sans-serif' font-weight='800' letter-spacing='-1' fill='%23121412' text-anchor='middle'%3ECFO%3C/text%3E%3C/svg%3E")
CANON = "%%CANON%%"  # заменяется в write() на канонический адрес страницы


def breadcrumbs_ld(crumbs):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": t, "item": abs_url(h) if h is not None else CANON}
        for i, (h, t) in enumerate(crumbs)]}


VERIFY = (f'<meta name="yandex-verification" content="{YANDEX_VERIFICATION}">' if YANDEX_VERIFICATION else "") + \
         (f'<meta name="google-site-verification" content="{GOOGLE_VERIFICATION}">' if GOOGLE_VERIFICATION else "")


def page(pre, title, desc, body, jsonld=None, crumbs=None, image=None, og_type="website"):
    ld_list = list(jsonld or []) + ([breadcrumbs_ld(crumbs)] if crumbs else [])
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in ld_list if j)
    nav = f'<a href="{link(pre, "")}">Каталог</a>' + "".join(f'<a href="{link(pre, s + "/")}">{LANDINGS[s]["short"]}</a>' for s in MAIN_NAV) + \
          f'<a href="{link(pre, REVIEWS + "/")}">Отзывы</a><a href="{link(pre, STATI + "/")}">Журнал</a>'
    cr = ""
    if crumbs:
        cr = '<nav class="crumbs" aria-label="Хлебные крошки">' + " / ".join(f'<a href="{link(pre, h)}">{e(t)}</a>' if h is not None else f'<span aria-current="page">{e(t)}</span>' for h, t in crumbs) + "</nav>"
    img = image or f"{SITE_URL}/img/og-default.jpg"
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8">{VERIFY}
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{CANON}"><meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="{SITE_NAME}"><meta property="og:locale" content="ru_RU">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{CANON}">
<meta property="og:image" content="{e(img)}"><meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#121412"><meta name="format-detection" content="telephone=no">
<link rel="icon" href="{ICON}" type="image/svg+xml"><link rel="icon" href="{pre}favicon.png" type="image/png" sizes="64x64"><link rel="apple-touch-icon" href="{pre}apple-touch-icon.png">
<link rel="preload" href="{pre}assets/fonts/manrope-cyrillic.woff2" as="font" type="font/woff2" crossorigin><link rel="preload" href="{pre}assets/fonts/unbounded-cyrillic.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{pre}assets/style.css">{ld}{METRIKA if CLEAN else ""}</head><body>
<header class="top"><div class="topin"><a class="logo" href="{link(pre, '')}" aria-label="{SITE_NAME}, {SITE_TAGLINE} — на главную"><span class="lg-mark" aria-hidden="true">CFO</span><span class="lg-t"><b>{SITE_NAME}</b><small>{SITE_TAGLINE}</small></span></a><button class="burger" type="button" aria-label="Меню" aria-expanded="false" aria-controls="mainnav"><span></span><span></span><span></span></button><nav id="mainnav" aria-label="Разделы">{nav}<a class="navcta" href="{link(pre, '')}#quiz">Тест подбора</a></nav></div></header>
<main>{cr}{body}</main>
<footer>{footer_nav(pre)}<p>Интернет-сайт носит информационный характер и ни при каких условиях не является публичной офертой, которая определяется положениями статьи 437 Гражданского кодекса РФ. Информация о программах курсов и иных условий, указанных на сайте, может быть изменена организацией предоставляющей услуги обучения в одностороннем порядке. Скриншоты с сайтов курсов могут отличаться от оригиналов. Информация по ценам, может отличаться от фактической, к моменту просмотра рейтинга.</p></footer>
<div id="cookieBar" hidden role="dialog" aria-label="Использование cookie"><p>Мы используем файлы cookie, чтобы сайт работал корректно и становился удобнее. Продолжая пользоваться сайтом, вы соглашаетесь с их использованием.</p><button type="button" class="btn sm" id="cookieOk">Принять</button></div>
{COMPARE_UI}<script>window.CMP_DATA={json.dumps(compare_data(), ensure_ascii=False)};window.SITE_PRE="{'/' if CLEAN else pre}";</script>
<script src="{pre}assets/app.js"></script></body></html>"""


# Короткие названия подборок для футера (без повторов «курсы финансового директора»)
FOOT_NAME = {"perepodgotovka": "Переподготовка с дипломом", "povyshenie-kvalifikacii": "Повышение квалификации", "kursy-shkol": "С сертификатом школы",
             "mba": "MBA и mini-MBA", "dlya-bankov": "Для банков", "do-50000": "До 50 000 ₽", "korotkie": "До 4 месяцев",
             "ochno-i-onlajn": "Очно и онлайн", "dlya-nachinayushchih": "Для новичков", "dlya-glavbuhov": "Главбухам",
             "dlya-sobstvennikov": "Собственникам", "rassrochka": "Оплата частями"}


def footer_nav(pre):
    land = "".join(f'<li><a href="{link(pre, s + "/")}">{e(FOOT_NAME.get(s, L["short"]))}</a></li>' for s, L in LANDINGS.items() if any(L["f"](c) for c in C))
    rel = "".join(f'<li><a href="{link(pre, d["slug"] + "/")}">{e(d["tab"])}</a></li>' for k, d in RELATED.items() if any(c["dir"] == k for c in REL))
    sch = "".join(f'<li><a href="{link(pre, "shkola/" + sp + "/")}">{e(n)}</a></li>' for n, sp in sorted(SCHOOL_PAGE.items(), key=lambda x: (PRIO.get(SCHOOL_DOMAINS[x[0]], 999), x[0])))
    return (f'<nav class="fnav" aria-label="Карта сайта"><div><b>Каталог по задачам</b><ul>{land}</ul></div><div><b>Рядом с профессией</b><ul>{rel}</ul>'
            f'<b>Навигатор</b><ul><li><a href="{link(pre, ABOUT + "/")}">О проекте</a></li><li><a href="{link(pre, STATI + "/")}">Журнал</a></li><li><a href="{link(pre, METHOD + "/")}">Методика</a></li><li><a href="{link(pre, REVIEWS + "/")}">Отзывы учеников</a></li></ul></div>'
            f'<div><b>Школы каталога</b><ul class="cols">{sch}</ul></div></nav>'
            f'<p class="flegal">Вопросы и уточнения по данным: <a href="mailto:{EMAIL}">{EMAIL}</a></p>')


def kpis(s):
    return f"""<div class="kpis bento"><div class="k1"><b>{s['n']}</b><span>{plural(s['n'],'программа','программы','программ')} в базе</span></div>
<div class="k2"><b>{s['schools']}</b><span>{plural(s['schools'],'школа','школы','школ')} в каталоге</span></div>
<div class="k3"><b>{rub(s['min'])}</b><span>самая доступная программа</span></div><div class="k4"><b>{rub(s['med'])}</b><span>медиана: середина ценового ряда</span></div></div>"""


def stars(r): return f"★{NB}{r:.1f}".replace(".", ",") if r else "—"


def shot(c, pre, cls="shot"):
    """Скриншот первого экрана страницы курса (data/img), ведёт на страницу курса агрегатора."""
    if not (ROOT / "data/img" / f"{c['id']}.jpg").exists():
        return ""
    return (f'<a class="{cls}" href="{link(pre, "kurs/" + c["id"] + "/")}"><img src="{pre}img/{c["id"]}.jpg" '
            f'alt="{e(c["title"])} — {e(c["school"])}" loading="lazy" width="640" height="400"></a>')


PROMO = {d: v for d, v in json.loads((ROOT / "data/promo_codes.json").read_text(encoding="utf-8")).items() if not d.startswith("_")}


def promo(c, cls="promo"):
    """Плашка с промокодом школы и кнопкой копирования (пусто, если промокода нет)."""
    p = PROMO.get(c["domain"])
    if not p:
        return ""
    return (f'<div class="{cls}"><span>Промокод на −{e(p["discount"])}</span>'
            f'<button class="pcode" data-code="{e(p["code"])}" title="Скопировать промокод">{e(p["code"])}</button></div>')


def promo_note(c, tag="small", with_code=False):
    p = PROMO.get(c["domain"])
    if not p:
        return ""
    txt = f"−{p['discount']} по промокоду {p['code']}" if with_code else f"−{p['discount']} с промокодом"
    return f'<{tag} class="pl">{e(txt)}</{tag}>'


def go_btn(c, cls="btn"):
    return f'<a class="{cls}" href="{e(c["ref_url"])}" rel="nofollow noopener" target="_blank">Перейти к курсу</a>'


DUR_BUCKETS = [("d1", "До 1 месяца", 0, 1), ("d3", "1–3 месяца", 1, 3), ("d6", "3–6 месяцев", 3, 6), ("d99", "Более 6 месяцев", 6, 10**6)]


def dur_bucket(m):
    """Корзина длительности по нижней границе срока; None — школа срок не указала."""
    if m is None:
        return ""
    return next(k for k, _, lo, hi in DUR_BUCKETS if (m <= hi if lo == 0 else lo < m <= hi))


PRICE_BUCKETS = [("p30", "До 30 000 ₽", 0, 30000), ("p50", "30 000 – 50 000 ₽", 30000, 50000), ("p100", "50 000 – 100 000 ₽", 50000, 100000),
                 ("p200", "100 000 – 200 000 ₽", 100000, 200000), ("p999", "Более 200 000 ₽", 200000, 10**9)]


def price_bucket(v):
    if v is None:
        return "pq"
    return next(k for k, _, lo, hi in PRICE_BUCKETS if (v <= hi if lo == 0 else lo < v <= hi))


QUICK = [("dip", "Диплом о переподготовке"), ("inst", "Оплата частями"), ("p30", "Дешевле 30 000 ₽"), ("m3", "За 3 месяца"), ("promo", "Есть промокод")]


def quick_chips(items):
    keys = {"dip": is_diploma, "inst": lambda c: bool(c["installment"]), "p30": lambda c: c["price"] is not None and c["price"] <= 30000,
            "m3": lambda c: c["months"] is not None and c["months"] <= 3, "promo": lambda c: c["domain"] in PROMO}
    chips = "".join(f'<button type="button" class="chip qf" data-q="{k}" aria-pressed="false">{t} <small>{n}</small></button>'
                    for k, t in QUICK if (n := sum(keys[k](c) for c in items)))
    return f'<div class="quick" role="group" aria-label="Быстрые фильтры">{chips}</div>'


def check_filters(items):
    """Единый набор фильтров-галочек: тип, цена, формат, длительность, школа (с числом программ)."""
    def group(title, key, opts):
        rows = "".join(f'<label class="cb"><input type="checkbox" value="{e(v)}"> {e(t)} <small>{n}</small></label>'
                       for v, t, n in opts if n)
        return f'<details class="ff" data-key="{key}"><summary>{title}</summary><div class="ffl">{rows}</div></details>' if rows else ""
    cnt = lambda f: sum(1 for c in items if f(c))
    names = sorted({c["school"] for c in items}, key=lambda x: x.lower())
    return (group("Тип", "type", [(k, v, cnt(lambda c, k=k: c["type"] == k)) for k, v in TYPE_NAME.items()])
            + group("Цена", "pb", [(k, t, cnt(lambda c, k=k: price_bucket(c["price"]) == k)) for k, t, _, _ in PRICE_BUCKETS]
                    + [("pq", "По запросу", cnt(lambda c: c["price"] is None))])
            + group("Формат", "format", [(k, v, cnt(lambda c, k=k: c["format"] == k)) for k, v in FORMAT_NAME.items()])
            + group("Длительность", "dur", [(k, t, cnt(lambda c, k=k: dur_bucket(c["months"]) == k)) for k, t, _, _ in DUR_BUCKETS])
            + group("Школа", "school", [(n, n, cnt(lambda c, n=n: c["school"] == n)) for n in names]))


def facts_row(items):
    """Строка плашек «подпись — значение»; элемент: (подпись, значение) или (подпись, значение, ссылка); None = разделитель."""
    li = ""
    for it in items:
        if it is None:
            li += "<li class='sep' aria-hidden='true'></li>"
        elif len(it) == 3 and it[2]:
            li += f"<li><a href='{it[2]}'><span>{e(it[0])}</span><b>{it[1]}</b></a></li>"
        else:
            li += f"<li><span>{e(it[0])}</span><b>{it[1]}</b></li>"
    return f"<ul class='facts-row'>{li}</ul>"


def doc_counts(items, pre):
    """Плашки «Диплом N / Удостоверение N / Сертификат N» по курсам подборки."""
    cnt = {}
    for c in items:
        if c.get("doc"):
            k = doc_short(c)[1]
            cnt[k] = cnt.get(k, 0) + 1
    return [(k, str(v)) for k, v in sorted(cnt.items(), key=lambda x: -x[1])]


def dur_range(items):
    ms = [c for c in items if c.get("months")]
    if not ms:
        return None
    lo, hi = min(ms, key=lambda c: c["months"]), max(ms, key=lambda c: c["months"])
    a, b = dur_short(lo), dur_short(hi)
    return a if a == b else f"{a} – {b}"


def landing_guide(slug, h1):
    t = LTEXT.get(slug)
    if not t:
        return ""
    choose = "".join(f"<p>{e(x)}</p>" for x in t["choose"])
    check = "".join(f"<li>{e(x)}</li>" for x in t["check"])
    mist = "".join(f"<div class='mist'><b>{e(a)}</b><p>{e(b)}</p></div>" for a, b in t["mistakes"])
    return (f'<section class="guide"><h2>На что смотреть при выборе: {e(h1[0].lower() + h1[1:])}</h2><div class="guide-txt">{choose}</div></section>'
            f'<section class="guide2"><div class="gcheck"><h2>Проверьте до оплаты</h2><ul class="checklist">{check}</ul></div>'
            f'<div class="gmist"><h2>Где ошибаются чаще всего</h2>{mist}</div></section>')


def verified_line(pre, date=None):
    return (f'<p class="verified"><span>Сверено с сайтами школ <time class="wk" datetime="{date or LAST_CHECK}">{ru_date(date or LAST_CHECK)}</time></span> · '
            f'<a href="{link(pre, METHOD + "/")}">методика</a></p>')


def price_html(c, monthly=True):
    """Цена: зачёркнутая старая (если школа её показывает) + платёж в месяц по данным школы."""
    old = f'<s>{rub(c["old_price"])}</s> ' if c.get("old_price") else ""
    mon = (f'<small class="mon">от {rub(c["monthly"])}/мес</small>' if monthly and c.get("monthly") else "")
    return f"{old}{rub(c['price'])}{mon}"


def is_diploma(c):
    return c["doc"].startswith(("Диплом о профессиональной", "Диплом установленного", "Диплом MBA"))


def school_link(c, pre):
    sp = SCHOOL_PAGE.get(c["school"])
    return f'<a href="{link(pre, "shkola/" + sp + "/")}">{e(c["school"])}</a>' if sp else e(c["school"])


def card(c, pre):
    tags = [TYPE_NAME[c["type"]], FORMAT_NAME[c["format"]]] + (["Рассрочка"] if c["installment"] else []) + \
           [AUD_NAME[a] for a in c.get("aud", [])] + \
           (["MBA"] if "mba" in c["tags"] else []) + (["mini-MBA"] if "mini-mba" in c["tags"] else []) + (["Для банков"] if "bank" in c["tags"] else [])
    sr = (f'<a href="{link(pre, REVIEWS + "/")}#school={urllib.parse.quote(c["school"])}">{n_rev(c["school_reviews"])}</a>'
          if c["school_reviews"] else "нет")
    return f"""<article class="card" data-type="{c['type']}" data-price="{c['price'] or ''}" data-format="{c['format']}" data-dur="{dur_bucket(c['months'])}" data-pb="{price_bucket(c['price'])}" data-school="{e(c['school'])}" data-qdip="{int(is_diploma(c))}" data-qinst="{int(bool(c['installment']))}" data-qp30="{int(c['price'] is not None and c['price'] <= 30000)}" data-qm3="{int(c['months'] is not None and c['months'] <= 3)}" data-qpromo="{int(c['domain'] in PROMO)}">{shot(c, pre) or '<div class="shot"></div>'}
<div class="school">{school_link(c, pre)}</div><h3><a href="{link(pre, 'kurs/' + c['id'] + '/')}">{e(c['title'])}</a></h3>
<div class="tags">{''.join(f'<span>{t}</span>' for t in tags)}</div>
<dl><div><dt>Цена</dt><dd>{price_html(c)}</dd></div><div><dt>Срок</dt><dd>{e(c['duration'] or '—')}</dd></div>
<div><dt>Объём</dt><dd>{e(c['hours_text'] or '—')}</dd></div><div><dt>Отзывы</dt><dd>{sr}</dd></div></dl>
<p class="doc">{e(c['doc'])}</p>{promo(c) or '<div class="promo-empty"></div>'}<div class="cact">{go_btn(c)}<button class="cmp" type="button" data-id="{c['id']}" aria-pressed="false">Сравнить</button></div></article>"""


def table(items, pre):
    rows = "".join(
        f"<tr><td class='tc'><a href='{link(pre, 'kurs/' + c['id'] + '/')}'>{e(c['title'])}</a><small>{e(c['school'])}</small></td><td data-l='Тип'>{TYPE_NAME[c['type']]}</td>"
        f"<td data-l='Цена' data-v='{c['price'] or 0}'>{rub(c['price'])}{promo_note(c, 'small', True)}</td><td data-l='Срок' data-v='{c['months'] or 0}'>{e(c['duration'] or '—')}</td>"
        f"<td data-l='Объём' data-v='{c['hours'] or 0}'>{e(c['hours_text'] or '—')}</td><td data-l='Документ'>{e(c['doc'])}</td>"
        f"<td class='tb'>{go_btn(c, 'btn sm')}</td></tr>" for c in order(items))
    return f"""<div class="tablewrap"><table class="sortable"><thead><tr><th>Курс</th><th>Тип</th><th>Цена</th><th>Срок</th><th>Объём</th><th>Документ</th><th></th></tr></thead>
<tbody>{rows}</tbody></table></div><p class="hint">Сортировка — по клику на заголовок колонки. Прочерк значит, что школа не опубликовала этот параметр.</p><p class="qcta">Не уверены, что выбрать? <a href="{link(pre, '')}#quiz">Тест подберёт 3 программы за минуту →</a></p>"""


def doc_short(c):
    """Короткий тип документа для лесенки: (класс, подпись)."""
    d = c["doc"]
    if d.startswith("Зависит"):
        return "dvar", "Зависит от тарифа"
    if d.startswith("Диплом MBA"):
        return "dmba", "Диплом MBA"
    if d.startswith(("Диплом о профессиональной", "Диплом установленного")):
        return "ddip", "Диплом"
    if d.startswith("Удостоверение") or "удостоверени" in d.lower():
        return "dudo", "Удостоверение"
    if d.startswith("Сертификат о повышении квалификации ИПБ"):
        return "dudo", "Сертификат ИПБ России"
    if d.startswith("Зависит"):
        return "dvar", "Зависит от тарифа"
    return "dsrt", "Сертификат / диплом школы"


def dur_short(c):
    m = c["months"]
    if m is None:
        return ""
    d = (c["duration"] or "").split(" (")[0]
    if m < 1 or m != int(m) or "–" in d or " до " in d:  # «3 дня», «3–4 месяца», «от 2 до 9 месяцев» — как у школы
        return d.replace("месяцев", "мес").replace("месяца", "мес").replace("месяц", "мес")
    return f"{'от ' if d.startswith('от') else ''}{m:g} мес"


def price_chart(items, pre):
    """Лесенка: строка на программу. Толстая полоса — цена (красная линия — медиана), тонкая — срок; плашка — документ."""
    allc = list(items)
    items = [c for c in allc if c["price"] is not None]
    noprice = [c for c in allc if c["price"] is None]  # «цена по запросу» — в конец лесенки, серой пунктирной линией
    mx = max(c["price"] for c in items)
    med = statistics.median(c["price"] for c in items)
    mm = max([c["months"] for c in allc if c["months"]] or [1])
    types = [t for t in TYPE_NAME if any(c["type"] == t for c in allc)]
    rows = ""
    for c in order(items) + order(noprice):
        dk, dl = doc_short(c)
        dur = (f'<span class="ld"><i style="width:{max(c["months"] / mm * 100, 2):.1f}%"></i></span><em class="ldl">{e(dur_short(c))}</em>'
               if c["months"] else '<span class="ld none"></span><em class="ldl none">срок не указан</em>')
        rows += (f'<a class="lr" href="{link(pre, "kurs/" + c["id"] + "/")}" data-type="{c["type"]}" data-price="{c["price"] if c["price"] is not None else ""}" data-months="{c["months"] or ""}" data-i="{len(rows)}">'
                 f'<span class="ln"><b>{e(c["school"])}</b><small>{e(c["title"])}</small><span class="doc-b {dk}">{e(dl)}</span></span>'
                 + (f'<span class="lbars"><span class="lb"><i class="t-{c["type"]}" style="width:{max(c["price"] / mx * 100, 1.5):.1f}%"></i></span>'
                    if c["price"] is not None else '<span class="lbars"><span class="lb none"><em>цена по запросу</em></span>')
                 + f'<span class="ldw">{dur}</span></span>'
                 f'<span class="lp"><b{" class=nop" if c["price"] is None else ""}>{rub(c["price"])}</b>{promo_note(c, "em") if c["price"] is not None else ""}<small>{e(c["duration"] or "")}</small></span><span class="lgo" role="link" tabindex="0" data-href="{e(c["ref_url"])}" aria-label="Перейти на сайт курса">К курсу ↗</span></a>')
    chips = '<button class="chip on" data-ladder-type="">Все</button>' + "".join(f'<button class="chip" data-ladder-type="{t}"><i class="t-{t}"></i>{TYPE_NAME[t]}</button>' for t in types)
    used = []
    for c in allc:
        if doc_short(c) not in used:
            used.append(doc_short(c))
    order_d = ["ddip", "dudo", "dmba", "dsrt", "dvar"]
    docs = "".join(f'<span class="doc-b {k}">{e(t)}</span>' for k, t in sorted(used, key=lambda x: order_d.index(x[0])))
    return f"""<section class="ladder" id="ceny"><h2>Карта цен: стоимость, срок и документ</h2>
<p>Одна строка — одна программа. Клик по строке открывает подробное описание.</p>
<div class="lkey"><span><i class="k-price"></i>Широкая полоса — цена, цвет — тип программы</span><span><i class="k-med"></i>Медиана: {rub(int(med))}</span>
<span><i class="k-dur"></i>Узкая полоса — срок (максимум {mm:g} мес)</span><span class="k-docs">Документы: {docs}</span></div>
<div class="legend">{chips}</div>
<div class="lsort"><span>Порядок:</span><button class="chip on" data-lsort="def">Рекомендуемый</button><button class="chip" data-lsort="pa">Цена ↑</button><button class="chip" data-lsort="pd">Цена ↓</button><button class="chip" data-lsort="ma">Срок ↑</button><button class="chip" data-lsort="md">Срок ↓</button></div>
<div class="lrows" style="--med:{med / mx * 100:.1f}%">{rows}</div><p class="qcta">Не уверены, что выбрать? <a href="{link(pre, '')}#quiz">Тест подберёт 3 программы за минуту →</a></p></section>"""


def price_bands(items, pre):
    bands = [("до 30 тыс", 0, 30000, None), ("30–50 тыс", 30001, 50000, "do-50000/"), ("50–100 тыс", 50001, 100000, None),
             ("100–200 тыс", 100001, 200000, None), ("от 200 тыс", 200001, 10**9, None)]
    items = [c for c in items if c["price"] is not None]
    mx = max(1, max(sum(a <= c["price"] <= b for c in items) for _, a, b, _ in bands))
    out = ""
    for name, a, b, l in bands:
        n = sum(a <= c["price"] <= b for c in items)
        out += f'<div class="band"><span>{name}</span><div><i style="width:{n/mx*100:.0f}%"></i></div><b>{n}</b></div>'
    return f'<section><h2>Сколько программ в каждом ценовом диапазоне</h2><div class="bands">{out}</div><p class="hint">Ограниченный бюджет? Смотрите <a href="{link(pre, "do-50000/")}">подборку до 50 000 ₽</a></p></section>'


EMPTY_PROMO = '<div class="promo-empty"></div>'


def rel_card(c, pre, hidden=False):
    """Карточка смежного курса: скриншот, направление, документ, формат, цена (+ с промокодом), срок, объём."""
    tags = [RELATED[c["dir"]]["tab"]]
    if c.get("doc"):
        tags.append(doc_short(c)[1])
    if c.get("format"):
        tags.append(FORMAT_NAME[c["format"]])
    pp = promo_price(c)
    price = rub(c["price"]) + (f'<small class="mon">{rub(pp)} с промокодом</small>' if pp else "")
    img = (f'<a class="shot" href="{e(c["ref_url"])}" rel="nofollow noopener" target="_blank"><img src="{pre}img/{c["id"]}.jpg" '
           f'alt="{e(c["title"])} — {e(c["school"])}" loading="lazy" width="640" height="400"></a>'
           if (ROOT / "data/img" / f"{c['id']}.jpg").exists() else '<div class="shot"></div>')
    return (f'<article class="card rel{" more-fm" if hidden else ""}" data-type="rel">{img}'
            f'<div class="school">{school_link(c, pre)}</div><h3>{e(c["title"])}</h3>'
            f'<div class="tags">{"".join(f"<span>{e(t)}</span>" for t in tags)}</div>'
            f'<dl><div><dt>Цена</dt><dd>{price}</dd></div><div><dt>Срок</dt><dd>{e(c.get("duration") or "—")}</dd></div>'
            f'<div><dt>Объём</dt><dd>{e(c.get("hours_text") or "—")}</dd></div><div><dt>Документ</dt><dd class="dshort">{e(doc_short(c)[1]) if c.get("doc") else "—"}</dd></div></dl>'
            f'<p class="doc">{e(c.get("doc") or "Документ школа на странице не указала")}</p>'
            f'{promo(c) or EMPTY_PROMO}<div class="cact">{go_btn(c)}</div></article>')


def fm_block(pre):
    """Главная: смежные направления вкладками (по 8 программ) + ссылки на страницы направлений."""
    tabs, panes = "", ""
    for i, (k, d) in enumerate(RELATED.items()):
        items = order([c for c in REL if c["dir"] == k])
        if not items:
            continue
        tabs += f'<button type="button" class="chip{" on" if i == 0 else ""}" data-reltab="{k}">{e(d["tab"])} <small>{len(items)}</small></button>'
        panes += (f'<div class="relpane" data-relpane="{k}"{"" if i == 0 else " hidden"}><p>{e(d["intro"])}</p><div class="cards">'
                  + "".join(rel_card(c, pre) for c in items[:8]) + "</div>"
                  + f'<p><a class="more-link" href="{link(pre, d["slug"] + "/")}">{e(d["h1"])}: смотреть {n_prog(len(items))} →</a></p></div>')
    return f"""<section class="fmblock"><h2>Что изучить в дополнение к программе финдиректора</h2>
<div class="legend reltabs" role="tablist">{tabs}</div>{panes}</section>"""


def schools_block(pre, items=None):
    """Плитки школ каталога с числом программ — перелинковка на страницы школ."""
    items = items if items is not None else C
    names = sorted({c["school"] for c in items if c["school"] in SCHOOL_PAGE}, key=lambda n: (PRIO.get(SCHOOL_DOMAINS[n], 999), n))
    t = "".join(f'<a class="tile" href="{link(pre, "shkola/" + SCHOOL_PAGE[n] + "/")}"><b>{e(n)}</b><span>{n_prog(sum(c["school"] == n for c in items))}'
                f'{" · промокод" if SCHOOL_DOMAINS[n] in PROMO else ""}</span></a>' for n in names)
    return f'<section><h2>Кто проводит обучение</h2><div class="tiles">{t}</div></section>'


def related_tiles(pre, skip=None):
    t = "".join(f'<a class="tile" href="{link(pre, d["slug"] + "/")}"><b>{e(d["h1"])}</b><span>{n_prog(sum(c["dir"] == k for c in REL))}</span></a>'
                for k, d in RELATED.items() if k != skip and any(c["dir"] == k for c in REL))
    return f'<section><h2>Соседние специализации</h2><div class="tiles">{t}</div></section>'


def faq_block(faq):
    if not faq: return "", None
    body = "<section id=\"faq\"><h2>Частые вопросы</h2>" + "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in faq) + "</section>"
    return body, {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}


def itemlist(items, name=None):
    return {"@context": "https://schema.org", "@type": "ItemList", **({"name": name} if name else {}),
            "numberOfItems": len(items), "itemListOrder": "https://schema.org/ItemListOrderUnordered",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": abs_url(f"kurs/{c['id']}/"), "name": c["title"]}
                                for i, c in enumerate(order(items))]}


def collection_ld(name, desc, items_ld):
    return {"@context": "https://schema.org", "@type": "CollectionPage", "name": name, "description": desc, "url": CANON,
            "inLanguage": "ru", "isPartOf": {"@id": SITE_URL + "/#website"}, "mainEntity": items_ld}


def iso_duration(c):
    """Нагрузка для CourseInstance.courseWorkload: часы (PT520H) или срок (P8M / P3D)."""
    if c["hours"]:
        return f"PT{c['hours']}H"
    m = c["months"]
    if m is None:
        return None
    if m < 1:
        return f"P{round(m * 30)}D"
    return f"P{m:g}M"


def course_ld(c, desc):
    inst = {"@type": "CourseInstance", "courseMode": "Online" if c["format"] == "online" else "Blended", "inLanguage": "ru",
            "courseWorkload": iso_duration(c)}
    ld = {"@context": "https://schema.org", "@type": "Course", "@id": CANON + "#course", "name": c["title"], "description": desc,
          "url": CANON, "inLanguage": "ru",
          "provider": {"@type": "EducationalOrganization", "name": c["school"], "url": "https://" + c["domain"]},
          "educationalCredentialAwarded": c["doc"], **({"hasCourseInstance": [inst]} if inst["courseWorkload"] else {}),
          "about": {"@type": "Occupation", "name": "Финансовый директор"}}
    if (ROOT / "data/img" / f"{c['id']}.jpg").exists():
        ld["image"] = abs_url(f"img/{c['id']}.jpg")
    if c["price"] is not None:
        ld["offers"] = [{"@type": "Offer", "category": "Paid", "price": c["price"], "priceCurrency": "RUB",
                         "url": c["url"], "availability": "https://schema.org/InStock", "priceValidUntil": "2026-12-31"}]
    return ld


def hubs(pre, skip=None):
    t = "".join(f'<a class="tile" href="{link(pre, s + "/")}"><b>{e(v["h1"])}</b><span>{n_prog(sum(v["f"](c) for c in C))}</span></a>'
                for s, v in LANDINGS.items() if s != skip and any(v["f"](c) for c in C))
    t += f'<a class="tile" href="{link(pre, REVIEWS + "/")}"><b>Что пишут ученики</b><span>{n_rev(sum(r["about_finance"] for r in R))}</span></a>'
    return f'<section><h2>Каталог по задачам и бюджету</h2><div class="tiles">{t}</div></section>'


SRC_NAME = {"otzovik.com": "Отзовик", "yandex.ru": "Яндекс Карты"}


def review_html(r, pre, show_school=True):
    s = SCHOOL[r["school_slug"]]
    full = r["text"]
    short = full if len(full) < 420 else full[:400].rsplit(" ", 1)[0] + "…"
    body = f"<p>{e(short)}</p>" if short == full else f"<details class='more'><summary>{e(short)}</summary><p>{e(full)}</p></details>"
    return f"""<article class="review" data-school="{e(s['name'])}" data-fin="{int(r['about_finance'])}" data-src="{e(r['source'])}">
{f'<div class="rh"><b>{e(s["name"])}</b></div>' if show_school else ''}
{f"<p class='pc'><b>+</b> {e(r['pros'])}</p>" if r['pros'] else ''}{f"<p class='pc'><b>−</b> {e(r['cons'])}</p>" if r['cons'] else ''}{body}
{"" if "provereno" in r["source_url"] else f'<div class="meta">Источник: <a href="{e(r["source_url"])}" rel="nofollow noopener" target="_blank">{SRC_NAME.get(r["source"], e(r["source"]))}</a></div>'}</article>"""


META = {}  # путь -> (title, description) для проверки уникальности


def write(path, content):
    canon = abs_url(path + "/" if path else "")
    content = content.replace(CANON, canon)
    m_t = re.search(r"<title>(.*?)</title>", content); m_d = re.search(r'name="description" content="(.*?)"', content)
    if m_t:
        META[path] = (html.unescape(m_t.group(1)), html.unescape(m_d.group(1)))
    p = OUT / path / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def check_meta():
    """title ≤ 70 и description 70–170 символов, всё уникально — иначе предупреждение при сборке."""
    problems = []
    for key, idx in (("title", 0), ("description", 1)):
        seen = {}
        for path, m in META.items():
            seen.setdefault(m[idx], []).append(path or "/")
        problems += [f"дубль {key}: {v}" for v in seen.values() if len(v) > 1]
    for path, (t, d) in META.items():
        if len(t) > 70 and t != H_TITLE: problems.append(f"длинный title ({len(t)}): /{path}")
        if not 70 <= len(d) <= 170: problems.append(f"description {len(d)} симв.: /{path}")
    print("SEO-мета: OK" if not problems else "SEO-мета, проверьте:\n  " + "\n  ".join(problems))


AUDIENCE = [
    ("Главбухам", "которые хотят сменить учёт и сдачу отчётности на управление деньгами: бюджеты, финансовую стратегию и разговор с собственником на языке цифр."),
    ("Экономистам и финансовым менеджерам", "для которых следующий шаг — руководство финансовой службой. Обучение соберёт знания в систему и добавит управленческий уровень."),
    ("Финансовым аналитикам", "которые уверенно строят модели и разбирают отчётность, но хотят сами принимать решения, а не только готовить для них расчёты."),
    ("Руководителям ПЭО и казначейства", "чтобы видеть финансы компании полностью: от ежедневных платежей до инвестиционных проектов."),
    ("Владельцам малого и среднего бизнеса", "которым важно понимать, где компания зарабатывает и где теряет, и ставить внятные задачи финансовому директору — или выполнять его работу самим."),
    ("Тем, кто меняет профессию", "при наличии высшего или среднего профессионального образования: переподготовка даёт диплом на новый вид деятельности, а опыт работы с цифрами ускорит учёбу."),
]
SKILLS = [
    "Планировать доходы, расходы и деньги компании, собирать прогнозный баланс и разбирать расхождения план-факт",
    "Держать под контролем платёжный календарь и не допускать кассовых разрывов",
    "Готовить управленческие отчёты, понятные собственнику и совету директоров",
    "Читать отчётность по РСБУ и МСФО: рентабельность, ликвидность, долговая нагрузка, оборачиваемость",
    "Оценивать проекты и бизнес: NPV, IRR, дисконтированные денежные потоки",
    "Собирать финансовую модель в Excel или Google-таблицах и прогонять сценарии",
    "Привлекать финансирование: кредиты, лизинг, облигации, инвесторы",
    "Законно оптимизировать налоги и настраивать внутренний контроль",
    "Находить и снижать валютные, процентные и кредитные риски",
    "Строить финансовую службу: функции, регламенты, автоматизация, команда",
]


QUIZ = [
    ("goal", "Чего вы хотите добиться?", [("beg", "Начать карьеру в финансах с нуля"), ("acc", "Вырасти из главбуха или финменеджера в CFO"),
                                         ("own", "Навести порядок в финансах своего бизнеса"), ("pk", "Освежить знания — я уже финдиректор")]),
    ("doc", "Какой документ нужен по итогу?", [("dip", "Диплом о профессиональной переподготовке"), ("udo", "Хватит удостоверения о повышении квалификации"),
                                               ("any", "Документ не важен, важны навыки")]),
    ("budget", "Сколько готовы потратить?", [("30000", "До 30 000 ₽"), ("70000", "До 70 000 ₽"), ("150000", "До 150 000 ₽"), ("0", "Бюджет не ограничен")]),
    ("time", "Сколько времени готовы учиться?", [("3", "До 3 месяцев"), ("6", "От 3 до 6 месяцев"), ("0", "Сколько потребуется")]),
    ("fmt", "Как удобнее заниматься?", [("online", "Только дистанционно"), ("mixed", "Хочу бывать на очных занятиях"), ("any", "Без разницы")]),
]


def quiz_block():
    steps = ""
    for i, (k, q, opts) in enumerate(QUIZ):
        btns = "".join(f'<button type="button" class="qopt" data-v="{v}">{e(t)}</button>' for v, t in opts)
        steps += f'<div class="qstep" data-k="{k}"{"" if i == 0 else " hidden"}><div class="qnum">Шаг {i + 1} / {len(QUIZ)}</div><h3>{e(q)}</h3><div class="qopts">{btns}</div></div>'
    return (f'<section class="quiz" id="quiz"><div class="qhead"><h2>Тест: какая программа вам подходит</h2><p>Пять коротких вопросов — и мы покажем три курса, '
            f'которые совпадают с вашей целью, документом, бюджетом и сроком.</p><div class="qbar"><i style="width:0%"></i></div></div>'
            f'<div class="qbody">{steps}<div class="qres" hidden></div></div>'
            f'<div class="qnav"><button type="button" class="chip qback" hidden>← Назад</button><button type="button" class="chip qrestart" hidden>Начать сначала</button></div></section>')


def paths_block(pre, cnt):
    """Главная: три пути обучения с анкорными ссылками на подборки — разводит интенты главной и подборок."""
    items = [
        ("perepodgotovka/", "Переподготовка на финансового директора", f"{n_prog(cnt['perepodgotovka'])} с дипломом",
         "Если вы меняете профессию: диплом о профессиональной переподготовке, от 250 часов. Поступить можно с высшим или средним профессиональным образованием, в том числе студентам."),
        ("povyshenie-kvalifikacii/", "Повышение квалификации финдиректора", f"{n_prog(cnt['povyshenie'])} с удостоверением",
         "Если вы уже в финансах: короткие программы под конкретную задачу — бюджет, МСФО, стратегия."),
        ("mba/", "MBA и mini-MBA для CFO", "программы для топ-менеджмента",
         "Если цель — топ-менеджмент и совет директоров: финансы вместе со стратегией, управлением людьми и операциями."),
    ]
    cards = "".join(f'<a class="path" href="{link(pre, h)}"><b>{e(t)}</b><span class="pcnt">{e(n)}</span><span>{e(d)}</span><i aria-hidden="true">→</i></a>'
                    for h, t, n, d in items)
    return (f'<section class="paths" id="formaty"><h2>Три формата обучения на финансового директора</h2><p>Начните с формата: от него зависят документ, срок и цена. '
            f'Каждая карточка ведёт в отдельную подборку.</p><div class="pathgrid">{cards}</div></section>')


def audience_block():
    li = "".join(f"<li><b>{e(t)}</b> — {e(d)}</li>" for t, d in AUDIENCE)
    return f'<section class="txt"><h2>Для кого эти программы</h2><ul class="aud">{li}</ul></section>'


def skills_block():
    li = "".join(f"<li>{e(t)}</li>" for t in SKILLS)
    return (f'<section class="txt"><h2>Что вы будете уметь после обучения на CFO</h2><p>Программы у школ отличаются, но эти темы встречаются почти везде. '
            f'Точный состав конкретного курса смотрите на его странице.</p><ul class="skills">{li}</ul></section>')


_COV = json.loads((ROOT / "data/coverage.json").read_text(encoding="utf-8")) if (ROOT / "data/coverage.json").exists() else {"topics": [], "courses": {}}
TOPICS = _COV["topics"]
COV_MIN = 3  # меньше трёх тем на странице — считаем, что школа не раскрывает программу на странице курса
GOV_DOC = ("Диплом о профессиональной", "Удостоверение о повышении", "Диплом установленного", "Диплом MBA")
TYPE_PHRASE = {"perepodgotovka": "программа профессиональной переподготовки", "povyshenie": "программа повышения квалификации",
               "kurs": "онлайн-курс с собственным документом"}


def coverage(c):
    return _COV["courses"].get(c["url"])


def pct(a, b):
    return round(abs(a - b) / b * 100)


def catalog_stats():
    priced = sorted(c["price"] for c in C if c["price"] is not None)
    per_hour = sorted(c["price"] / c["hours"] for c in C if c["price"] and c["hours"])
    months = sorted(c["months"] for c in C if c["months"])
    return dict(priced=priced, med=statistics.median(priced), ph_med=statistics.median(per_hour), m_med=statistics.median(months))


DOC_MEANING = {
    "ddip": "Диплом о профессиональной переподготовке — официальный документ о квалификации. Он подтверждает право работать в новой сфере, и его можно показать работодателю или проверяющим.",
    "dmba": "Диплом MBA выдают по программе дополнительного профессионального образования. Учёной степенью он не является, но работодатели видят в нём подтверждение управленческой подготовки.",
    "dudo": "Удостоверение о повышении квалификации подтверждает, что вы обновили знания в своей профессии. Права на новый вид деятельности оно не даёт — для этого нужна переподготовка.",
    "dsrt": "Школа называет документ «{doc}». Если он нужен работодателю, спросите у школы, относится ли он к дипломам о переподготовке и попадают ли сведения о нём в реестр ФИС ФРДО.",
    "dvar": "Документ зависит от тарифа: на базовом обычно выдают документ школы, на старших — удостоверение или диплом. Если нужен официальный документ, выбирайте тариф, где он есть.",
}
AUD_TEXT = {"beg": "тем, кто приходит в финансы без опыта", "acc": "главным бухгалтерам, которые переходят к управлению финансами",
            "own": "владельцам и руководителям бизнеса"}


def course_panel(c):
    """Компактная панель рядом со скриншотом: цена, промокод, параметры столбиком, кнопка."""
    pp = promo_price(c)
    rows = [("Тип", TYPE_NAME[c["type"]]), ("Срок", c["duration"]), ("Объём", c["hours_text"]),
            ("Документ", c["doc"] if len(c["doc"]) <= 45 else doc_short(c)[1]), ("Формат", FORMAT_NAME[c["format"]]),
            ("Рассрочка", f"от {rub(c['monthly'])}/мес" if c.get("monthly") else ("есть" if c["installment"] else None))]
    dl = "".join(f"<dt>{k}</dt><dd>{e(v)}</dd>" for k, v in rows if v)
    old = f"<s>{rub(c['old_price'])}</s>" if c.get("old_price") else ""
    lic = LICENSES.get(c["domain"])
    if lic:
        rows.append(("Лицензия", lic))
    dl = "".join(f"<dt>{k}</dt><dd>{e(v)}</dd>" for k, v in rows if v)
    return (f'<aside class="cpanel"><div class="cp-price">{old}<b>{rub(c["price"])}</b>'
            f'{f"<span>{rub(pp)} с промокодом</span>" if pp else ""}</div><dl>{dl}</dl>{promo(c)}{go_btn(c)}</aside>')


def program_block(c):
    """Учебный план по модулям — только если школа публикует его на странице курса."""
    pr = PROGRAMS.get(c["url"])
    if not pr:
        return ""
    li = ""
    for i, (name, hrs, topics) in enumerate(pr["modules"], 1):
        sub = ("<ul>" + "".join(f"<li>{e(t)}</li>" for t in topics) + "</ul>") if topics else ""
        li += f'<li><div class="mh"><span class="mn">{i}</span><b>{e(name)}</b>{f"<em>{hrs} ч</em>" if hrs else ""}</div>{sub}</li>'
    tot = f' · всего {e(pr["total"])}' if pr.get("total") else ""
    adm = f'<p class="note">{e(pr["admission"])}</p>' if pr.get("admission") else ""
    return (f'<section class="prog"><h2>Учебный план по модулям</h2><p class="note">{len(pr["modules"])} модулей{tot} — так их перечисляет '
            f'школа на своём сайте.</p><ol class="modlist">{li}</ol>{adm}</section>')


def license_html(c):
    lic = LICENSES.get(c["domain"])
    if not lic:
        return ""
    return (f'<p class="lic">Лицензия на образовательную деятельность {e(lic)} · '
            f'<a href="{LICENSE_REGISTRY}" rel="nofollow noopener" target="_blank">найти в реестре Рособрнадзора</a></p>')


def course_summary(c):
    """Важное о курсе карточкой со списками: для кого, темы в описании, чего нет, документ, ещё у школы."""
    blocks = []
    cov = coverage(c)
    if cov and len(cov) >= COV_MIN:  # пара «есть / не упоминаются» всегда первой строкой — их удобно сравнить
        yes = [n for k, n in TOPICS if k in cov]
        no = [n for k, n in TOPICS if k not in cov]
        blocks.append((f"Есть в описании курса · {len(yes)} из {len(TOPICS)}",
                       '<ul class="tl yes">' + "".join(f"<li>{e(n)}</li>" for n in yes) + "</ul>"))
        blocks.append((f"Не нашли в описании — спросите школу · {len(no)}",
                       ('<ul class="tl no">' + "".join(f"<li>{e(n)}</li>" for n in no) + "</ul>") if no
                       else "<p>Описание курса охватывает все 12 тем, которые мы считаем ключевыми для финдиректора.</p>"))
    else:
        blocks.append(("Программа", "<p>Школа не публикует состав программы на странице курса. Попросите учебный план до оплаты.</p>"))
    if c.get("aud"):
        blocks.append(("Для кого", "<ul>" + "".join(f"<li>{e(AUD_TEXT[a][0].upper() + AUD_TEXT[a][1:])}</li>" for a in c["aud"]) + "</ul>"))
    blocks.append(("О документе", f"<p>{DOC_MEANING[doc_short(c)[0]].replace('{doc}', e(c['doc']))}</p>", "" if c.get("aud") else "wide"))
    same = order([x for x in C if x["school"] == c["school"] and x["id"] != c["id"]])
    rel = order([x for x in REL if x["school"] == c["school"]])
    if same or rel:
        pre = "../../"
        html_ = "<div class='more-cols'>"
        if same:
            html_ += "<div><h4>Программы для CFO</h4><ul class='more-list'>" + "".join(
                f"<li><a class='ml' href='{e(x['ref_url'])}' rel='nofollow noopener' target='_blank'><span class='mt'>{e(x['title'])}</span><span class='mm'>{rub(x['price'])}</span><i aria-hidden='true'>↗</i></a></li>" for x in same[:5]) + "</ul></div>"
        if rel:
            html_ += "<div><h4>Соседние специализации</h4><ul class='more-list'>" + "".join(
                f"<li><a class='ml' href='{e(x['ref_url'])}' rel='nofollow noopener' target='_blank'><span class='mt'>{e(x['title'])}"
                f"<small>{e(RELATED[x['dir']]['tab'])}</small></span><span class='mm'>{rub(x['price'])}</span><i aria-hidden='true'>↗</i></a></li>" for x in rel[:5]) + "</ul></div>"
        html_ += "</div>"
        total = len(same) + len(rel)
        if c["school"] in SCHOOL_PAGE:
            html_ += (f"<p class='more-all'><a href='{link(pre, 'shkola/' + SCHOOL_PAGE[c['school']] + '/')}'>"
                      f"Страница школы: {total + 1} {plural(total + 1, 'программа', 'программы', 'программ')} →</a></p>")
        blocks.append((f"Другие программы — {e(c['school'])}", html_, "wide"))
    return '<div class="sumgrid">' + "".join(f'<div class="sumb {b[2] if len(b) > 2 else ""}"><h3>{b[0]}</h3>{b[1]}</div>' for b in blocks) + "</div>"


def coverage_block(c):
    cov = coverage(c)
    if cov is None or len(cov) < COV_MIN:
        return ('<section class="cov"><h2>Покрытие тем финансового директора</h2><p class="note">На странице курса нет состава программы — '
                'возможно, он лежит в учебном плане или PDF. Попросите его у школы и проверьте, есть ли там бюджетирование, денежный поток, '
                'управленческая отчётность, анализ отчётности, оценка проектов и финансовая модель.</p></section>')
    n = len(cov)
    items = "".join(f'<li class="{"yes" if k in cov else "no"}"><i aria-hidden="true">{"✓" if k in cov else "—"}</i><span>{e(name)}'
                    f'{"" if k in cov else "<small>в описании не найдено</small>"}</span></li>' for k, name in TOPICS)
    return (f'<section class="cov"><h2>Покрытие тем финансового директора</h2>'
            f'<div class="covhead"><b>{n} из {len(TOPICS)}</b><span class="covbar"><i style="width:{n / len(TOPICS) * 100:.0f}%"></i></span>'
            f'<span>ключевых тем названы в описании курса на сайте школы</span></div><ul class="covlist">{items}</ul>'
            f'<p class="note">Описание курса мы сравниваем со списком из 12 тем, без которых сложно работать финдиректором. '
            f'Если тема не упомянута, она всё равно может быть в программе — уточните у школы.</p></section>')


def fit_text(c, st):
    """Свой текст страницы курса: кому подойдёт и чем отличается от других программ этой школы (из данных каталога)."""
    who = {"perepodgotovka": "тем, кто меняет профессию или кому для работодателя нужен диплом на новый вид деятельности",
           "povyshenie": "тем, кто уже работает в финансах и хочет закрыть конкретную тему без смены профессии",
           "kurs": "тем, кому важнее практические навыки, чем официальный документ"}[c["type"]]
    aud = [AUD_TEXT[a] for a in c.get("aud", [])]
    p1 = f"Программа «{e(c['title'])}» подойдёт прежде всего {who}" + (f"; школа отдельно адресует её {', '.join(aud)}" if aud else "") + "."
    if c["price"] is not None:
        lvl = "дешевле" if c["price"] < st["med"] else ("дороже" if c["price"] > st["med"] else "на уровне")
        p1 += f" По цене она {lvl} {'' if lvl == 'на уровне' else 'середины '}каталога ({rub(int(st['med']))})"
        p1 += (f", а по формату — {FORMAT_NAME[c['format']].lower()}." if c["format"] else ".")
    sib = [x for x in C if x["school"] == c["school"] and x["id"] != c["id"]]
    paras = [p1]
    for x in sib[:3]:
        diff = []
        if x["type"] != c["type"]:
            diff.append(f"это {TYPE_PHRASE[x['type']]}, а не {TYPE_PHRASE[c['type']]}")
        if x["price"] is not None and c["price"] is not None and x["price"] != c["price"]:
            diff.append(f"стоит {rub(x['price'])} — {'дороже' if x['price'] > c['price'] else 'дешевле'} на {rub(abs(x['price'] - c['price']))}")
        if x["duration"] and x["duration"] != c["duration"]:
            diff.append(f"длится {x['duration']}")
        if x["hours_text"] and x["hours_text"] != c["hours_text"]:
            diff.append(f"объём — {x['hours_text']}")
        if doc_short(x)[1] != doc_short(c)[1]:
            diff.append(f"по итогу — {doc_short(x)[1].lower()}")
        if x["format"] != c["format"]:
            diff.append(f"формат — {FORMAT_NAME[x['format']].lower()}")
        if diff:
            paras.append(f'У этой же школы есть программа <a href="{link("../../", "kurs/" + x["id"] + "/")}">«{e(x["title"])}»</a>: {e("; ".join(diff))}.')
    if len(paras) > 1:
        paras.append("Выбирайте между ними по цели: нужен ли официальный документ, сколько часов в неделю вы готовы учиться и какой бюджет комфортен.")
    return '<section><h2>Кому подойдёт и чем отличается</h2>' + "".join(f"<p>{x}</p>" for x in paras) + "</section>"


def pros_cons(c, st):
    pros, cons = [], []
    d = c["doc"]
    if d.startswith(("Диплом о профессиональной", "Диплом установленного")):
        pros.append("По итогу — диплом о профессиональной переподготовке с правом работать в новой сфере")
    elif d.startswith("Диплом MBA"):
        pros.append("По итогу выдают диплом MBA")
    elif d.startswith("Удостоверение"):
        pros.append("По итогу выдают удостоверение о повышении квалификации")
    else:
        cons.append(f"Документ — {d[0].lower() + d[1:]}. Если работодателю нужен официальный документ о квалификации, спросите о нём школу")
    if LICENSES.get(c["domain"]):
        pros.append(f"Номер образовательной лицензии опубликован ({LICENSES[c['domain']]}) — его легко найти в реестре Рособрнадзора")
    if c.get("old_price") and c["price"]:
        pros.append(f"На момент проверки действует скидка {pct(c['price'], c['old_price'])}% от {rub(c['old_price'])}")
    p = PROMO.get(c["domain"])
    if p:
        pros.append(f"С промокодом {p['code']} цена ниже ещё на {p['discount']}")
    if c.get("monthly"):
        pros.append(f"Можно платить частями: от {rub(c['monthly'])} в месяц, {c['monthly_months']} мес. (данные школы)")
    elif c["installment"]:
        pros.append("Школа принимает оплату частями")
    if c["format"] == "mixed":
        pros.append("Формат на выбор: аудитория или онлайн")
    cov = coverage(c)
    if cov and len(cov) >= 9:
        pros.append(f"Описание охватывает {len(cov)} из {len(TOPICS)} ключевых тем финдиректора")
    if c["price"] is not None:
        if c["price"] < st["med"] * 0.8:
            pros.append(f"На {pct(c['price'], st['med'])}% ниже медианной цены каталога ({rub(int(st['med']))})")
        elif c["price"] > st["med"] * 1.5:
            cons.append(f"На {pct(c['price'], st['med'])}% выше медианной цены каталога ({rub(int(st['med']))})")
    else:
        cons.append("Стоимость школа сообщает только по запросу")
    if c["school_reviews"]:
        pros.append(f"Есть {n_rev(c['school_reviews'])} учеников о финансовых курсах школы — они ниже на странице")
    else:
        cons.append("Отзывов о финансовых курсах школы мы пока не нашли")
    if not c["duration"]:
        cons.append("Срок обучения школа не указала")
    if not c["hours_text"]:
        cons.append("Объём в часах школа не указала")
    if cov is None or len(cov) < COV_MIN:
        cons.append("Состав программы не опубликован — нужен учебный план от школы")
    li = lambda xs, cls: "".join(f'<li class="{cls}">{e(x)}</li>' for x in xs)
    return (f'<section><h2>Плюсы и оговорки</h2><div class="pc2"><div><h3>Плюсы</h3><ul>{li(pros, "plus")}</ul></div>'
            f'<div><h3>Оговорки</h3><ul>{li(cons, "minus") or "<li>По открытым данным серьёзных оговорок нет</li>"}</ul></div></div></section>')


def bench_block(c, st):
    rows = []
    if c["price"] is not None:
        cheaper = sum(1 for x in st["priced"] if x > c["price"])
        rows.append(("Цена", rub(c["price"]), f"ниже, чем у {cheaper} из {len(st['priced'])} программ", 1 - (st["priced"].index(c["price"]) / max(len(st["priced"]) - 1, 1))))
    exact_h = c["hours"] and "–" not in (c["hours_text"] or "")  # для диапазона часов стоимость часа не считаем
    if c["price"] and exact_h:
        ph = c["price"] / c["hours"]
        rows.append(("Стоимость часа", rub(round(ph)) + "/ч" if not (c["hours_text"] or "").startswith("от") else "до " + rub(round(ph)) + "/ч",
                     f"в среднем по каталогу — {rub(round(st['ph_med']))}/ч", None))
    if c["months"] and not any(x in (c["duration"] or "") for x in ("–", "от ", "до ")):  # диапазон сроков не сравниваем
        rel = "короче" if c["months"] < st["m_med"] else ("длиннее" if c["months"] > st["m_med"] else "на уровне")
        rows.append(("Срок", e(c["duration"]), f"{rel} медианы каталога ({st['m_med']:g} мес)" if rel != "на уровне" else f"на уровне медианы каталога ({st['m_med']:g} мес)", None))
    cov = coverage(c)
    if cov and len(cov) >= COV_MIN:
        allc = sorted(len(v) for v in _COV["courses"].values() if len(v) >= COV_MIN)
        rows.append(("Ключевые темы", f"{len(cov)} из {len(TOPICS)}", f"обычно по каталогу — {statistics.median(allc):g} из {len(TOPICS)}", None))
    if not rows:
        return ""
    tr = "".join(f"<tr><th>{k}</th><td><b>{v}</b></td><td>{e(n)}</td></tr>" for k, v, n, _ in rows)
    return f'<section><h2>Как курс выглядит среди остальных</h2><table class="facts bench">{tr}</table></section>'


def pay_block(c):
    rows = []
    if c.get("old_price"):
        rows.append(("Полная цена", f"<s>{rub(c['old_price'])}</s>"))
    rows.append(("Цена у школы", f"<b>{rub(c['price'])}</b>"))
    pp = promo_price(c)
    p = PROMO.get(c["domain"])
    if pp:
        rows.append((f"С промокодом {e(p['code'])}", f"<b>{rub(pp)}</b>"))
    if c.get("monthly"):
        rows.append(("Рассрочка", f"от {rub(c['monthly'])}/мес на {c['monthly_months']} мес."))
    elif c["installment"]:
        rows.append(("Рассрочка", "есть, подробности у школы"))
    base = pp or c["price"]
    if base and c["doc"].startswith(GOV_DOC):
        rows.append(("Налоговый вычет", f"до {rub(min(round(base * 0.13), 19500))} — 13% от оплаченной суммы, если у школы есть лицензия; при ставке НДФЛ выше 13% — больше"))
    tr = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows)
    return f'<section><h2>Сколько стоит и как заплатить меньше</h2><table class="facts pay">{tr}</table>{promo(c, "promo big")}</section>'


def similar_compare(c, similar, pre):
    def cov_txt(x):
        v = coverage(x)
        return f"{len(v)} из {len(TOPICS)}" if v and len(v) >= COV_MIN else "—"
    cards = ""
    for x in [c] + similar[:3]:
        cur = x is c
        title = e(x["title"]) if cur else f'<a href="{link(pre, "kurs/" + x["id"] + "/")}">{e(x["title"])}</a>'
        badge = '<span class="mcb">Вы смотрите</span>' if cur else ""
        cards += (f'<div class="mc{" cur" if cur else ""}">{badge}<div class="mcs">{e(x["school"])}</div><div class="mct">{title}</div>'
                  f'<dl><dt>Цена</dt><dd>{rub(x["price"])}</dd><dt>Срок</dt><dd>{e(x["duration"] or "—")}</dd>'
                  f'<dt>Документ</dt><dd>{e(doc_short(x)[1])}</dd><dt>Темы</dt><dd>{cov_txt(x)}</dd></dl></div>')
    return (f'<section><h2>Рядом с похожими курсами</h2><div class="minicmp">{cards}</div>'
            f'<p class="hint">Добавьте курсы кнопкой «Сравнить» — откроется таблица со всеми параметрами.</p></section>')


def course_faq(c):
    q = []
    p = PROMO.get(c["domain"])
    q.append((f"Какая цена у программы «{c['title']}»?", (f"По данным сайта школы «{c['school']}» — {rub(c['price'])}" if c["price"] is not None else "Стоимость школа называет по запросу")
              + (f", без скидки — {rub(c['old_price'])}" if c.get("old_price") else "")
              + (f". По промокоду {p['code']} выйдет {rub(promo_price(c))}" if promo_price(c) else "") + "."))
    q.append(("Как долго учиться?", f"Школа указывает срок {c['duration']}" + (f", объём {c['hours_text']}" if c["hours_text"] else "") + "." if c["duration"]
              else ("Срок на странице курса не указан" + (f"; объём — {c['hours_text']}" if c["hours_text"] else "") + ". Его стоит уточнить у школы.")))
    q.append(("Что выдают по окончании?", f"{c['doc']}."))
    if c["installment"]:
        q.append(("Есть ли оплата частями?", f"Есть. " + (f"Школа указывает платёж от {rub(c['monthly'])} в месяц на {c['monthly_months']} мес." if c.get("monthly") else "Подробные условия — на сайте школы.")))
    if c["doc"].startswith(GOV_DOC) and c["price"]:
        base = promo_price(c) or c["price"]
        q.append(("Получится ли вернуть налог за этот курс?", f"Да, если у школы есть образовательная лицензия. Вычет — 13% от оплаченной суммы (при ставке НДФЛ выше 13% — по вашей ставке), "
                  f"для этого курса при ставке 13% — до {rub(min(round(base * 0.13), 19500))}. Лимит 150 000 ₽ в год общий для всех социальных вычетов, и вернуть можно не больше уплаченного налога."))
    if p:
        q.append(("Действует ли промокод?", f"Да: {p['code']} снижает цену на {p['discount']}. Код вводят при оплате на сайте школы."))
    return q


INK, ACC, ACC_BG, OK, OK_BG, WARN_BG, MUTE, LINE = "#0b1220", "#4f46e5", "#eef2ff", "#059669", "#ecfdf5", "#fff7e6", "#5b6475", "#e7eaf1"


def _svg(w, h, body, label):
    return (f'<figure class="info"><svg viewBox="0 0 {w} {h}" role="img" aria-label="{e(label)}" xmlns="http://www.w3.org/2000/svg" '
            f'font-family="Manrope, system-ui, sans-serif">{body}</svg><figcaption>{e(label)}</figcaption></figure>')


def _wrap(text, n):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    return lines + [cur] if cur else lines


def _txt(x, y, text, size=15, weight=600, fill=INK, anchor="start", n=40, lh=1.3):
    out = ""
    for i, line in enumerate(_wrap(text, n)):
        out += f'<text x="{x}" y="{y + i * size * lh:.0f}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{e(line)}</text>'
    return out


def infographic(key):
    """Адаптивная инфографика (HTML+CSS): на компьютере — схема, на телефоне — перестраивается в столбец, текст читаемый."""
    fig = lambda cls, body, cap: f'<figure class="info ig-{cls}">{body}<figcaption>{e(cap)}</figcaption></figure>'
    if key == "ladder":
        steps = [("Бухгалтер, экономист", "учёт, отчётность"), ("Финансовый аналитик", "анализ, план-факт"), ("Финансовый менеджер", "бюджет направления"),
                 ("Руководитель ФЭО", "команда, сводный бюджет"), ("Финансовый директор", "стратегия и финансирование")]
        li = "".join(f'<li style="--h:{40 + i * 15}%"><span class="n">{i + 1}</span><b>{e(t)}</b><small>{e(d)}</small></li>' for i, (t, d) in enumerate(steps))
        return fig("ladder", f'<p class="ig-t">Типичный путь к должности CFO</p><ol>{li}</ol>', "Карьерная лестница: от бухгалтера и аналитика до финансового директора")
    if key == "functions":
        items = [("Бюджет", "планирование и план-факт"), ("Денежный поток", "платёжный календарь, ликвидность"), ("Отчётность", "управленческие отчёты собственнику"),
                 ("Финансирование", "банки, лизинг, инвесторы"), ("Инвестиции", "оценка проектов и бизнеса"), ("Контроль и риски", "налоги, внутренний контроль")]
        cards = "".join(f'<div><b>{e(t)}</b><small>{e(d)}</small></div>' for t, d in items)
        return fig("functions", f'<div class="ig-core">Финансовый директор</div><div class="ig-grid">{cards}</div>', "Шесть ключевых функций финансового директора")
    if key == "compare":
        cols = [("Главный бухгалтер", "Прошлое", "Учёт, налоги, отчётность"), ("Финансовый менеджер", "Месяц и квартал", "Бюджет направления, план-факт"),
                ("Финансовый директор", "Год и дальше", "Стратегия, финансирование, решения")]
        cards = "".join(f'<div class="c{i}"><b>{e(t)}</b><span>{e(h)}</span><small>{e(d)}</small></div>' for i, (t, h, d) in enumerate(cols))
        return fig("compare", f'<p class="ig-t">Горизонт планирования →</p><div class="ig-cols">{cards}</div>', "Главбух, финансовый менеджер и финансовый директор: разный горизонт планирования")
    if key == "tree":
        body = ('<div class="ig-q">Вы уже работаете в финансах?</div><div class="ig-branches">'
                '<div class="br"><span class="lbl">Нет</span><div class="ans a1"><b>Профпереподготовка</b><small>диплом на новую профессию</small></div></div>'
                '<div class="br"><span class="lbl">Да</span><div class="ig-q sub">Цель — топ-менеджмент?</div><div class="ig-sub">'
                '<div><span class="lbl">Нет</span><div class="ans a2"><b>Повышение квалификации</b><small>закрыть конкретную тему</small></div></div>'
                '<div><span class="lbl">Да</span><div class="ans a3"><b>MBA</b><small>или mini-MBA</small></div></div></div></div></div>')
        return fig("tree", body, "Как выбрать формат обучения финансового директора")
    if key == "skills":
        left = ["Бюджетирование", "Денежный поток", "Управленческая отчётность", "Анализ отчётности", "Финансовая модель", "Оценка проектов", "МСФО", "Налоги и контроль"]
        right = ["Коммуникация с собственником", "Управление командой", "Переговоры с банками", "Решения в неопределённости", "Управление изменениями",
                 "Цифровые инструменты: Excel, BI, нейросети"]
        col = lambda t, xs, c: f'<div class="{c}"><b>{t}</b><ul>' + "".join(f"<li>{e(x)}</li>" for x in xs) + "</ul></div>"
        return fig("skills", '<div class="ig-two">' + col("Профессиональные", left, "pro") + col("Управленческие", right, "soft") + "</div>", "Карта навыков финансового директора")
    if key == "steps":
        st = [("Договор и чеки", "сохраните документы об оплате"), ("Справка из школы", "об оплате образовательных услуг"),
              ("Декларация 3-НДФЛ", "или вычет у работодателя"), ("Возврат налога", "13% и более от оплаченной суммы")]
        li = "".join(f'<li><span class="n">{i + 1}</span><b>{e(t)}</b><small>{e(d)}</small></li>' for i, (t, d) in enumerate(st))
        return fig("steps", f"<ol>{li}</ol>", "Как получить налоговый вычет за обучение: четыре шага")
    if key == "choose":
        st = [("Цель", "сменить профессию, закрыть тему или выйти в топ"), ("Документ и лицензия", "диплом, удостоверение или сертификат; реестр Рособрнадзора"),
              ("Программа и практика", "модули, часы, задания с проверкой, преподаватели"), ("Условия", "цена, рассрочка, возврат по оферте, отзывы")]
        li = "".join(f'<li><span class="n">{i + 1}</span><b>{e(t)}</b><small>{e(d)}</small></li>' for i, (t, d) in enumerate(st))
        return fig("steps", f'<p class="ig-t">Четыре фильтра при выборе курса</p><ol>{li}</ol>', "Как выбрать курс финансового директора: от цели к условиям оплаты")
    if key == "glavbuh":
        left = ["Бухгалтерский и налоговый учёт", "Отчётность компании", "Контроль платежей", "Закрытие периода", "Работа с налоговой и аудиторами"]
        right = ["Управленческий учёт", "Бюджетирование и план-факт", "Платёжный календарь и прогноз денег", "Финансовая модель и оценка проектов",
                 "Кредиты и другое финансирование", "Общение с собственником и команда"]
        col = lambda t, xs, c: f'<div class="{c}"><b>{t}</b><ul>' + "".join(f"<li>{e(x)}</li>" for x in xs) + "</ul></div>"
        return fig("skills", '<div class="ig-two">' + col("Уже есть у главбуха", left, "pro") + col("Нужно добрать", right, "soft") + "</div>",
                   "Из главного бухгалтера в финансовые директора: что уже есть и что добрать")
    if key == "instrukciya":
        st = [("Общие положения", "подчинение, назначение, требования к образованию и стажу"), ("Обязанности", "за какие участки финансовой работы отвечает"),
              ("Права", "что вправе запрашивать, подписывать и решать"), ("Ответственность", "за что спросят при нарушениях")]
        li = "".join(f'<li><span class="n">{i + 1}</span><b>{e(t)}</b><small>{e(d)}</small></li>' for i, (t, d) in enumerate(st))
        return fig("steps", f'<p class="ig-t">Четыре раздела должностной инструкции</p><ol>{li}</ol>', "Из чего состоит должностная инструкция финансового директора")
    if key == "uprchet-otchety":
        items = [("ОПиУ", "выручка, расходы, прибыль: заработали ли"), ("ДДС", "приход и расход денег: где деньги"),
                 ("Баланс", "имущество, долги, капитал на дату")]
        cards = "".join(f'<div><b>{e(t)}</b><small>{e(d)}</small></div>' for t, d in items)
        return fig("functions", f'<div class="ig-core">Управленческая отчётность</div><div class="ig-grid">{cards}</div>', "Три главных отчёта управленческого учёта")
    if key == "uprchet-shagi":
        st = [("Вопросы", "какие решения нужны собственнику"), ("Статьи и разрезы", "единый справочник для плана и факта"),
              ("Данные и регламент", "откуда цифры, кто вносит, к какому сроку"), ("Отчёты", "ежемесячно, со сверкой с банком и бухгалтерией")]
        li = "".join(f'<li><span class="n">{i + 1}</span><b>{e(t)}</b><small>{e(d)}</small></li>' for i, (t, d) in enumerate(st))
        return fig("steps", f'<p class="ig-t">Как запустить управленческий учёт</p><ol>{li}</ol>', "Внедрение управленческого учёта: от вопросов собственника к регулярным отчётам")
    if key == "byudzhet-vidy":
        items = [("БДР", "доходы, расходы, прибыль: сколько заработаем"), ("БДДС", "поступления и платежи: хватит ли денег"),
                 ("Прогнозный баланс", "имущество, долги, капитал на конец периода")]
        cards = "".join(f'<div><b>{e(t)}</b><small>{e(d)}</small></div>' for t, d in items)
        return fig("functions", f'<div class="ig-core">Сводный бюджет компании</div><div class="ig-grid">{cards}</div>', "Три главных бюджета компании")
    if key == "byudzhet-cikl":
        st = [("Цели", "что собственник ждёт от года"), ("Бюджеты подразделений", "продажи, закупки, персонал, расходы"),
              ("Свод и утверждение", "общий БДР и БДДС, согласование"), ("План-факт", "ежемесячно разбирать отклонения")]
        li = "".join(f'<li><span class="n">{i + 1}</span><b>{e(t)}</b><small>{e(d)}</small></li>' for i, (t, d) in enumerate(st))
        return fig("steps", f'<p class="ig-t">Цикл бюджетирования</p><ol>{li}</ol>', "Бюджетирование: от целей собственника к ежемесячному план-факт анализу")
    steps4 = {  # простые схемы «четыре шага»: ключ -> (подзаголовок, шаги, подпись)
        "razryv": ("Как поймать разрыв заранее", [("Календарь платежей", "все поступления и платежи по дням"), ("Прогноз остатка", "на 4–13 недель вперёд"),
                   ("Сигнал", "день, когда остаток уходит в минус"), ("Решение", "сдвинуть платёж, ускорить оплату, взять кредит")],
                   "Кассовый разрыв: от платёжного календаря к решению"),
        "oborot": ("Финансовый цикл компании", [("Закупка", "деньги уходят поставщику"), ("Запас", "товар лежит на складе"),
                   ("Отгрузка", "покупатель получил товар"), ("Оплата", "деньги вернулись в компанию")],
                   "Оборотный капитал: путь денег от закупки до оплаты покупателем"),
        "riski": ("Цикл управления рисками", [("Найти", "составить карту рисков"), ("Оценить", "вероятность и размер потерь"),
                  ("Ответить", "избежать, снизить, передать или принять"), ("Следить", "лимиты и регулярный пересмотр")],
                  "Управление финансовыми рисками: четыре шага"),
        "90dnej": ("Первые три месяца в должности", [("Недели 1–3", "люди, процессы, данные"), ("Недели 4–6", "быстрые победы: деньги и отчёты"),
                   ("Недели 7–10", "план изменений с собственником"), ("Недели 11–13", "регламенты и метрики службы")],
                   "Первые 90 дней финансового директора: от знакомства к плану изменений"),
    }
    if key in steps4:
        sub, st, cap = steps4[key]
        li = "".join(f'<li><span class="n">{i + 1}</span><b>{e(t)}</b><small>{e(d)}</small></li>' for i, (t, d) in enumerate(st))
        return fig("steps", f'<p class="ig-t">{e(sub)}</p><ol>{li}</ol>', cap)
    if key == "bezubytok":
        items = [("Постоянные расходы", "аренда, оклады, связь — не зависят от объёма"), ("Переменные расходы", "сырьё, сдельная оплата, доставка — растут с продажами"),
                 ("Маржинальный доход", "выручка минус переменные расходы")]
        cards = "".join(f'<div><b>{e(t)}</b><small>{e(d)}</small></div>' for t, d in items)
        return fig("functions", f'<div class="ig-core">Точка безубыточности</div><div class="ig-grid">{cards}</div>', "Из чего считается точка безубыточности")
    if key == "ucheba":
        left = ["Фиксированные часы в календаре", "Короткие сессии по 30–45 минут", "Задания на своих рабочих цифрах", "Конспект в одном месте"]
        right = ["Учиться только по выходным", "Копить пропущенные модули", "Решать учебные кейсы «для галочки»", "Скрывать учёбу от руководителя"]
        col = lambda t, xs, c: f'<div class="{c}"><b>{t}</b><ul>' + "".join(f"<li>{e(x)}</li>" for x in xs) + "</ul></div>"
        return fig("skills", '<div class="ig-two">' + col("Работает", left, "soft") + col("Мешает", right, "pro") + "</div>",
                   "Учёба на финансового директора без отрыва от работы: что помогает и что мешает")
    return ""


def art_text(t, pre):
    """[[slug|текст]] -> ссылка на страницу сайта (пустой slug — главная)."""
    return re.sub(r"\[\[([^|\]]*)\|([^\]]+)\]\]", lambda m: f'<a href="{link(pre, (m.group(1) + "/") if m.group(1) else "")}">{e(m.group(2))}</a>', re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", e(t).replace("&quot;", '"')))


def art_cover(a, pre):
    return f'<img class="acover" src="{pre}img/stati-{a["slug"]}.jpg" alt="{e(a["title"])}" width="1200" height="630">'


def art_courses(val, pre):
    """Нативный блок курсов внутри статьи: школа, название, цена, срок, документ и реф-ссылка на сайт школы."""
    if val == "top3":
        picks, seen = [], set()
        for c in order(C):
            if c["domain"] not in seen and c["domain"] in PRIO:
                seen.add(c["domain"]); picks.append(c)
        picks = picks[:3]
    else:
        picks = [next(c for c in C if c["id"] == i) for i in val]
    items = "".join(
        f'<li>{shot(c, pre, "acs-img")}<div class="acs-s">{school_link(c, pre)}</div><a class="acs-t" href="{link(pre, "kurs/" + c["id"] + "/")}">{e(c["title"])}</a>'
        f'<dl><div><dt>Цена</dt><dd>{rub(c["price"])}</dd></div><div><dt>Срок</dt><dd>{e(c["duration"] or "—")}</dd></div>'
        f'<div><dt>Документ</dt><dd>{e(c["doc"] or "—")}</dd></div></dl>{go_btn(c, "btn sm")}</li>' for c in picks)
    return f'<div class="acs"><b>Программы для CFO, с которых удобно начать сравнение</b><ul>{items}</ul></div>'


def render_article(a, pre):
    toc, body, n = [], "", 0
    for kind, val in a["sections"]:
        if kind == "h2":
            n += 1; toc.append((f"s{n}", val)); body += f'<h2 id="s{n}">{e(val)}</h2>'
        elif kind == "p":
            body += f"<p>{art_text(val, pre)}</p>"
        elif kind in ("ul", "ol"):
            body += f'<{kind} class="alist">' + "".join(f"<li>{art_text(x, pre)}</li>" for x in val) + f"</{kind}>"
        elif kind == "tip":
            body += f'<aside class="atip"><b>На заметку</b><p>{art_text(val, pre)}</p></aside>'
        elif kind == "table":
            head, *rows = val
            body += ('<div class="atable"><table><thead><tr>' + "".join(f"<th>{e(h)}</th>" for h in head) + "</tr></thead><tbody>"
                     + "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in rows) + "</tbody></table></div>")
        elif kind == "info":
            body += infographic(val)
        elif kind == "courses":  # "top3" — по одному курсу от первых школ из priorities.json, иначе список id курсов
            body += art_courses(val, pre)
        elif kind == "cta":
            body += ('<div class="acta"><b>Куда двигаться дальше</b><div>' + "".join(
                f'<a class="chip" href="{link(pre, (sl + "/") if sl else "")}">{e(t)} →</a>' for sl, t in val) + "</div></div>")
    toc_html = '<nav class="atoc" aria-label="Содержание"><b>В этой статье</b><ol>' + "".join(f'<li><a href="#{i}">{e(t)}</a></li>' for i, t in toc) + "</ol></nav>"
    return toc_html, body


def build():
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    for f in ("style.css", "app.js"):
        shutil.copy(ROOT / "assets" / f, OUT / "assets" / f)
    shutil.copytree(ROOT / "assets/fonts", OUT / "assets/fonts")
    if (ROOT / "data/img").exists():
        keep = {f"stati-{a['slug']}.jpg" for a in ARTICLES + DRAFTS}  # обложки только своих статей
        shutil.copytree(ROOT / "data/img", OUT / "img", ignore=lambda d, names: [n for n in names if n.startswith("stati-") and n not in keep])
    for f in ("favicon.png", "apple-touch-icon.png", "favicon.ico"):  # PNG/ICO-версии иконки для браузеров без SVG-фавиконов
        if (ROOT / "assets" / f).exists():
            shutil.copy(ROOT / "assets" / f, OUT / f)

    # Главная
    s = stats(C); pre = ""
    cnt = {t: sum(c["type"] == t for c in C) for t in TYPE_NAME}
    lead = (f"<p class='bluf lead'>В базе {n_prog(s['n'])} для будущих и действующих финансовых директоров от {n_school_gen(s['schools'])}. "
            f"Цены, сроки, документы и отзывы собраны в единую таблицу — выбирайте без десятка открытых вкладок.</p>"
            f"<ul class='facts-row'><li><span>Диапазон цен</span><b>{rub(s['min'])} – {rub(s['max'])}</b></li>"
            f"<li class='sep' aria-hidden='true'></li>"
            f"<li><a href='{link(pre, 'perepodgotovka/')}'><span>Диплом</span><b>{cnt['perepodgotovka']}</b></a></li>"
            f"<li><a href='{link(pre, 'povyshenie-kvalifikacii/')}'><span>Удостоверение</span><b>{cnt['povyshenie']}</b></a></li>"
            f"<li><a href='{link(pre, 'kursy-shkol/')}'><span>Сертификат школы</span><b>{cnt['kurs']}</b></a></li></ul>")
    filters = quick_chips(C) + '<div class="filters">' + check_filters(C) + '<button class="chip freset" type="button">Сбросить</button><span class="fCount"></span></div>'
    cheap = min((c for c in C if c["price"] is not None), key=lambda c: c["price"])
    pp_m = [c["months"] for c in C if c["type"] == "perepodgotovka" and c["months"]]
    faq_html, faq_ld = faq_block([
        ("Какие задачи решает финансовый директор?", "Финансовый директор, или CFO, отвечает за деньги компании в целом: составляет бюджет, следит за денежным потоком, готовит управленческие отчёты собственнику, договаривается о финансировании и оценивает инвестиции. В небольших компаниях он нередко руководит и бухгалтерией."),
        ("Чем финдиректор отличается от главбуха и финансового менеджера?", "Главбух ведёт учёт и отвечает за отчётность перед государством — то есть за то, что уже случилось. Финансовый менеджер планирует и контролирует деньги отдела или направления. Финансовый директор отвечает за финансовую стратегию всей компании и принимает решения вместе с собственником."),
        ("Реально ли стать финансовым директором без экономического образования?", "Да. Переподготовку можно пройти с любым высшим или средним профессиональным образованием и получить диплом на новый вид деятельности. Но на саму должность обычно берут с опытом в финансах, поэтому чаще путь идёт через позиции аналитика или финансового менеджера."),
        ("Переподготовка, повышение квалификации или MBA — что выбрать?", "Переподготовка — если меняете профессию или работодатель просит диплом. Повышение квалификации — если уже работаете в финансах и нужна конкретная тема. MBA и mini-MBA — для движения в топ-менеджмент: больше стратегии, управления людьми и связей."),
        ("Сколько учиться на CFO?", f"Зависит от формата. В каталоге повышение квалификации занимает от 3 дней, переподготовка — от {min(pp_m):g} до {max(pp_m):g} месяцев по данным школ, MBA — до полутора лет. Почти все онлайн-программы совмещаются с работой."),
        ("Какие цены на обучение финансового директора?", f"В каталоге — от {rub(s['min'])} ({cheap['school']}) до {rub(s['max'])}, медиана {rub(s['med'])}. Многие школы дают рассрочку и промокоды, они отмечены в карточках."),
        ("Что выдают по окончании?", "После переподготовки — диплом о профессиональной переподготовке, после повышения квалификации — удостоверение. Школы с образовательной лицензией вносят сведения о них в реестр ФИС ФРДО. Часть онлайн-школ выдаёт собственный сертификат — тип документа указан в каждой карточке."),
        ("Можно ли платить частями и вернуть налог?", "Большинство школ каталога дают рассрочку — платёж в месяц указан в карточке, если школа его публикует. Подробно о вычете — в FAQ на странице каждого курса: при ставке НДФЛ 13% можно вернуть до 19 500 ₽ в год."),
        ("Бывают ли бесплатные курсы финансового директора?", "Полных бесплатных программ для финдиректора в каталоге нет. Некоторые школы открывают пробный доступ — например, SF Education даёт 48 часов, чтобы познакомиться с курсом."),
        ("С чего начать выбор курса финансового директора?", "Сформулируйте цель и решите, какой документ нужен. Затем сравните цену, срок и часы, откройте программу и проверьте бюджетирование, финансовое моделирование и управленческую отчётность. Прочитайте отзывы о школе и добавьте 2–4 курса в сравнение, чтобы увидеть их рядом."),
    ])
    body = f"""<h1>Обучение <em>финансового директора</em>: каталог курсов с ценами, программами и отзывами</h1>{verified_line(pre)}{lead}{kpis(s)}
<nav class="htoc" aria-label="Разделы главной"><a href="#formaty">Форматы</a><a href="#katalog">Каталог и фильтры</a><a href="#quiz">Тест подбора</a><a href="#ceny">Карта цен</a><a href="#faq">Вопросы</a></nav>
{paths_block(pre, cnt)}<section id="katalog"><h2>Каталог программ</h2>{filters}<div class="cards" id="cards">{''.join(card(c, pre) for c in order(C))}</div></section>
{quiz_block()}{price_chart(C, pre)}{price_bands(C, pre)}{skills_block()}{audience_block()}{hubs(pre)}{fm_block(pre)}{schools_block(pre)}{faq_html}"""
    h_title = H_TITLE
    h_desc = fit_parts([f"Каталог: {n_prog(s['n'])} для финансовых директоров от {n_school_gen(s['schools'])}, стоимость от {rub(s['min'])}.",
                        "Дипломы, удостоверения, MBA, отзывы учеников и промокоды.", "Тест подбора и сравнение курсов."], 160)
    site_ld = {"@context": "https://schema.org", "@type": "WebSite", "@id": SITE_URL + "/#website", "url": SITE_URL + "/",
               "name": SITE_NAME, "description": "Каталог программ обучения финансовых директоров: стоимость, документы, отзывы", "inLanguage": "ru",
               "publisher": {"@id": SITE_URL + "/#org"}}
    org_ld = {"@context": "https://schema.org", "@type": "Organization", "@id": SITE_URL + "/#org", "name": SITE_NAME, "url": SITE_URL + "/"}
    write("", page(pre, h_title, h_desc, body,
                   [site_ld, org_ld, collection_ld(h_title, h_desc, itemlist(C, "Программы обучения финансового директора")), faq_ld]))

    # Посадочные
    pre = "../"
    for slug, L in LANDINGS.items():
        items = [c for c in C if L["f"](c)]
        if not items: continue
        st = stats(items)
        mon = [c["months"] for c in items if c["months"]]
        dr = dur_range(items)
        bluf = (f"<p class='bluf lead'>В подборке {n_prog(st['n'])} от {n_school_gen(st['schools'])}. Ниже — цены, сроки, документы и разбор, как выбрать.</p>"
                + facts_row([("Диапазон цен", f"{rub(st['min'])} – {rub(st['max'])}")] + ([("Срок", e(dr))] if dr else []) + [None] + doc_counts(items, pre)))
        fh, fl = faq_block(LTEXT[slug]["faq"] if slug in LTEXT else L["faq"])
        body = f"""<h1>{e(L['h1'])}</h1>{verified_line(pre)}{bluf}{kpis(st)}<section class="define"><h2>Коротко о подборке</h2><p>{e(L['define'])}</p>
<p class="back-all">Не тот формат? Смотрите <a href="{link(pre, '')}">все курсы финансового директора</a> в общем каталоге или <a href="{link(pre, '')}#quiz">пройдите тест подбора</a> — он покажет три подходящие программы.</p></section>
<section><h2>Курсы подборки</h2>{quick_chips(items)}<div class="filters">{check_filters(items)}<button class="chip freset" type="button">Сбросить</button><span class="fCount"></span></div><div class="cards">{''.join(card(c, pre) for c in order(items))}</div></section>
{price_chart(items, pre) if len(items) > 2 else ''}{landing_guide(slug, L["h1"])}{fh}{schools_block(pre, items)}{hubs(pre, slug)}{related_tiles(pre)}"""
        l_title = first_fit([f"{L['h1']}: {n_prog(st['n'])} в 2026", f"{L['h1']} — {n_prog(st['n'])}", f"{L['h1']} ({st['n']})", L["h1"]], 70)
        price_part = (f"стоимость {rub(st['min'])} – {rub(st['max'])}" if st["min"] != st["max"] else f"стоимость {rub(st['min'])}")
        l_desc = fit_parts([f"{L['h1']}. {n_prog(st['n'])[0].upper() + n_prog(st['n'])[1:]} от {n_school_gen(st['schools'])}, {price_part}.",
                            "Чек-лист выбора, документы и отзывы учеников.", "Документы и отзывы.", "Промокоды школ."], 160)
        write(slug, page(pre, l_title, l_desc, body, [collection_ld(L["h1"], l_desc, itemlist(items, L["h1"])), fl],
                         [("", "Каталог"), (None, L["h1"])]))

    # Отзывы — только отзывы, где речь о курсах по финансам
    FR = [r for r in R if r["about_finance"]]
    fin_slugs = sorted({r["school_slug"] for r in FR}, key=lambda s_: (min(PRIO.get(c["domain"], 999) for c in C if c["school_slug"] == s_), s_))
    rows = ""
    for s_ in fin_slugs:
        rs = [r["rating"] for r in FR if r["school_slug"] == s_]
        cs = order([c for c in C if c["school_slug"] == s_])
        courses_html = "".join(f"<a href='{link(pre, 'kurs/' + c['id'] + '/')}'>{e(c['title'])}</a> <small>{rub(c['price'])}</small><br>" for c in cs)
        _n = SCHOOL[s_]["name"]
        _nm = f"<a href='{link(pre, 'shkola/' + SCHOOL_PAGE[_n] + '/')}'>{e(_n)}</a>" if _n in SCHOOL_PAGE else e(_n)
        rows += (f"<tr class='rsel' data-school='{e(_n)}'><td class='tc'><b>{_nm}</b></td>"
                 f"<td data-l='Отзывов' data-v='{len(rs)}'>{len(rs)}</td>"
                 f"<td class='rc' data-l='Курсы'>{courses_html}</td><td class='tb'><button class='chip'>Показать ({len(rs)})</button></td></tr>")
    rv = "".join(review_html(r, pre) for r in sorted(FR, key=lambda r: [*fin_slugs].index(r["school_slug"])))
    body = f"""<h1>Отзывы учеников о курсах финансового директора</h1>{verified_line(pre)}
<p class="bluf lead"><b>Собрали {n_rev(len(FR))} о финансовых программах {len(fin_slugs)} {plural(len(fin_slugs), 'школы', 'школ', 'школ')} каталога.</b> Нажмите на школу в таблице — ниже останутся только отзывы о ней.</p>
<section><h2>Отзывы по школам</h2><div class="tablewrap"><table class="sortable rtable"><thead><tr><th>Школа</th><th>Отзывов</th><th>Программы в каталоге</th><th></th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="hint">Клик по строке фильтрует отзывы, клик по заголовку колонки — сортирует таблицу.</p></section>
<section id="rlist"><h2>Что пишут <span id="rTitle"></span></h2><div class="filters"><button class="chip" id="rAll">Показать все</button>
<span id="rCount"></span></div>
<div id="reviews">{rv}</div></section>"""
    r_title = f"Курсы финансового директора: {n_rev(len(FR))} учеников о школах"
    r_desc = fit_parts([f"Что ученики пишут о финансовых программах школ {', '.join(SCHOOL[s_]['name'] for s_ in fin_slugs[:3])} и других — {n_rev(len(FR))}.",
                        "Источники: Отзовик и Яндекс Карты.", "Фильтр по школе."], 160)
    orgs = {"@context": "https://schema.org", "@type": "ItemList", "name": "Школы, о финансовых курсах которых есть отзывы",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": {"@type": "EducationalOrganization", "name": SCHOOL[s_]["name"]}}
                                for i, s_ in enumerate(fin_slugs)]}
    write(REVIEWS, page(pre, r_title, r_desc, body, [collection_ld(r_title, r_desc, orgs)], crumbs=[("", "Каталог"), (None, "Отзывы учеников")]))

    # Страницы курсов
    pre = "../../"
    CST = catalog_stats()
    for c in C:
        rs = [r for r in R if r["school_slug"] == c["school_slug"] and r["about_finance"]][:8]
        similar = sorted([x for x in C if x["type"] == c["type"] and x["id"] != c["id"]], key=lambda x: abs((x["price"] or 0) - (c["price"] or 0)))[:4]
        p_ = PROMO.get(c["domain"])
        price_txt = f"цена {rub(c['price'])}" if c["price"] is not None else "цена по запросу"
        sh = TITLE_SHORT.get(c["school"], c["school"])
        c_title = first_fit([f"{c['title']} ({c['school']}): стоимость, программа, отзывы", f"{c['title']} ({c['school']}): обзор и цена",
                             f"{c['title']} ({c['school']}) — обзор", f"{c['title']} ({sh}): обзор и цена", f"{c['title']} ({sh}) — обзор",
                             f"{c['title']} — обзор курса", c["title"]], 70)
        kind = "" if c["type"] == "kurs" else TYPE_NAME[c["type"]].lower() + ", "  # у «сертификата школы» документ указан ниже
        c_desc = fit_parts([f"Обзор программы «{c['title']}» от {c['school']}: {kind}{price_txt}"
                            + (f", {c['duration']}" if c["duration"] else "") + (f", {c['hours_text']}" if c["hours_text"] else "") + ".",
                            f"{c['doc']}." if len(c["doc"]) < 60 else "",
                            f"Промокод {p_['code']} на −{p_['discount']}." if p_ else "",
                            "Плюсы, оговорки и отзывы учеников.", "Отзывы учеников."], 160)
        ld = course_ld(c, c_desc)
        cfaq_html, cfaq_ld = faq_block(course_faq(c))
        land = next((s_ for s_ in ("perepodgotovka", "povyshenie-kvalifikacii", "kursy-shkol") if LANDINGS[s_]["f"](c)), None)
        facts = [("Тип", TYPE_NAME[c["type"]]), ("Документ", c["doc"]), ("Формат", FORMAT_NAME[c["format"]]),
                 ("Цена", (f"{rub(c['price'])} (без скидки — {rub(c['old_price'])})" if c.get("old_price") else rub(c["price"]))),
                 *([("Платёж в рассрочку", f"от {rub(c['monthly'])} в месяц на {c['monthly_months']} мес. — по данным школы")] if c.get("monthly") else []),
                 ("Для кого", ", ".join(AUD_NAME[a].lower() for a in c.get("aud", [])) or "школа не выделяет отдельную аудиторию"),
                 ("Срок", c["duration"] or "не указан на странице"), ("Объём", c["hours_text"] or "не указан на странице"),
                 ("Рассрочка", "есть" if c["installment"] else "нет данных")]
        body = f"""<h1 class="h-sm">{e(c['title'].replace(' — ', ': '))} — {e(c['school'])}</h1>{verified_line(pre, c['checked'])}
<div class="chero">{shot(c, pre, "shot hero").replace(link(pre, "kurs/" + c["id"] + "/"), e(c["ref_url"])).replace('<a class', '<a rel="nofollow noopener" target="_blank" class')}{course_panel(c)}</div><section class="about"><h2>Главное о курсе</h2>{course_summary(c)}</section>
{fit_text(c, CST)}{program_block(c)}{pros_cons(c, CST)}{bench_block(c, CST)}{pay_block(c)}

<section><h2>Что ученики пишут о школе «{e(c['school'])}»</h2>{''.join(review_html(r, pre, False) for r in rs) if rs else "<p>Отзывов о финансовых курсах этой школы мы пока не нашли.</p>"}
<p><a href="{link(pre, REVIEWS + '/')}">Все отзывы учеников →</a></p></section>
{similar_compare(c, similar, pre)}{cfaq_html}
<section><h2>Ещё варианты того же типа</h2><div class="cards">{''.join(card(x, pre) for x in similar)}</div></section>"""
        crumbs = [("", "Каталог")] + ([(land + "/", LANDINGS[land]["h1"])] if land else []) + [(None, c["title"])]
        img = abs_url(f"img/{c['id']}.jpg") if (ROOT / "data/img" / f"{c['id']}.jpg").exists() else None
        write(f"kurs/{c['id']}", page(pre, c_title, c_desc, body, [ld, cfaq_ld], crumbs, image=img, og_type="article"))

    # Методика
    pre = "../"
    m_body = f"""<h1>Методика: откуда данные о курсах и как мы их проверяем</h1>{verified_line(pre)}
<section class="txt"><p><b>Каждая цифра в каталоге взята из открытого источника: со страницы курса на официальном сайте школы или из отзывов учеников на Яндекс Картах и Отзовике.</b> Если школа чего-то не публикует, мы не додумываем, а ставим прочерк.</p>
<h2>Что берём со страниц курсов</h2><ul>
<li>Название программы, цену, срок, объём в часах, формат и тип итогового документа.</li>
<li>Старую цену показываем зачёркнутой, только если школа сама указывает скидку.</li>
<li>Ежемесячный платёж пишем лишь тогда, когда школа публикует его рядом с ценой.</li>
<li>Не нашли параметр на странице — в карточке будет «—».</li></ul>
<h2>Как часто обновляем</h2><p>Страницы курсов сверяются раз в неделю, дата сверки меняется по понедельникам. Если вы видите расхождение с сайтом школы, верны данные школы — и напишите нам, мы поправим.</p>
<h2>Какие отзывы публикуем</h2><p>Только отзывы учеников с Яндекс Карт и Отзовика, где речь идёт о финансовых курсах, — со ссылкой на источник. Отзыв описывает школу в целом, а не конкретную программу.</p>
<h2>Покрытие тем</h2><p>Описание каждого курса мы сравниваем со списком из 12 тем, необходимых финансовому директору: бюджетирование, денежный поток, управленческая отчётность, анализ отчётности, оценка проектов, финансовая модель и другие. Это помогает быстро увидеть, насколько программа управленческая.</p>
<h2>Порядок в каталоге</h2><p>Рекомендуемый порядок задаёт редакция. Его можно сменить на сортировку по цене или сроку и сузить фильтрами по типу документа, формату и школе.</p>
<h2>Промокоды</h2><p>Промокоды выдают сами школы. Размер скидки и срок действия проверяйте при оплате на сайте школы.</p></section>"""
    m_desc = "Методика каталога курсов финансового директора: какие данные берём с сайтов школ, как отбираем отзывы, как часто сверяем цены и сроки."
    write(METHOD, page(pre, "Методика: откуда данные о курсах финдиректора — " + SITE_NAME, m_desc, m_body,
                       [{"@context": "https://schema.org", "@type": "AboutPage", "name": "Методика", "url": CANON, "description": m_desc}],
                       [("", "Каталог"), (None, "Методика")]))

    # О нас
    pre = "../"
    n_sch = len({c["school"] for c in C})
    a_body = f"""<h1>{SITE_NAME}: зачем мы сделали этот каталог</h1>
<section class="txt about-page"><p class="bluf lead">Выбрать обучение на финансового директора трудно: программ много, а сайты школ рассказывают о себе по-разному. Мы свели курсы в одну базу с одинаковыми полями, чтобы их можно было честно сравнить.</p>
<div class="sumgrid">
<div class="sumb"><h3>Задача проекта</h3><p>Помочь каждому, кто строит карьеру CFO, выбрать программу под свою цель, опыт, бюджет и нужный документ — и не платить за лишнее.</p></div>
<div class="sumb"><h3>Что внутри</h3><ul><li>{n_prog(len(C))} для финансовых директоров от {n_school_gen(n_sch)} и ещё {n_prog(len(REL))} по соседним специализациям</li><li>Цены, сроки, часы и документы, сверенные с сайтами школ</li><li>Отзывы учеников с Яндекс Карт и Отзовика со ссылкой на источник</li><li>Тест подбора, карта цен, фильтры и сравнение курсов</li></ul></div>
<div class="sumb"><h3>Правила редакции</h3><ul><li>Публикуем только то, что можно проверить; чего нет — так и пишем</li><li>Показываем не только плюсы программ, но и оговорки</li><li>Объясняем разницу между дипломом, удостоверением и сертификатом простым языком</li><li>Сверяем данные каждую неделю</li></ul></div>
<div class="sumb"><h3>Кому пригодится</h3><ul><li>Тем, кто только выбирает профессию финансового директора</li><li>Главбухам, экономистам и финансовым менеджерам на пути к CFO</li><li>Действующим финдиректорам, которым нужно повышение квалификации или MBA</li><li>Владельцам бизнеса, которые хотят понимать финансы своей компании</li></ul></div>
</div>
<h2>Как пользоваться каталогом</h2><p>Начните с <a href="{link(pre, '')}">общего каталога</a> или откройте подборку под свою задачу: <a href="{link(pre, 'perepodgotovka/')}">переподготовка с дипломом</a>, <a href="{link(pre, 'povyshenie-kvalifikacii/')}">повышение квалификации</a>, <a href="{link(pre, 'dlya-nachinayushchih/')}">обучение с нуля</a>, <a href="{link(pre, 'do-50000/')}">программы до 50 000 ₽</a>. Добавьте 2–4 курса в сравнение — параметры откроются в одной таблице. На странице курса есть покрытие тем, плюсы и оговорки, расчёт цены с промокодом и вычетом, отзывы о школе.</p>
<h2>Источники</h2><p>Данные берём с официальных сайтов школ, отзывы — с Яндекс Карт и Отзовика. Подробности — в разделе <a href="{link(pre, METHOD + '/')}">«Методика»</a>. Сайт носит справочный характер: школы могут менять цены и условия, поэтому перед оплатой сверяйтесь с сайтом школы.</p>
<h2>Написать редакции</h2><p>Заметили ошибку или хотите предложить программу в каталог? Пишите на <a href="mailto:{EMAIL}">{EMAIL}</a> — проверим и обновим данные.</p></section>"""
    a_desc = f"{SITE_NAME} — каталог обучения финансовых директоров: {len(C)} {plural(len(C), 'программа', 'программы', 'программ')} с проверенными ценами, сроками, документами и отзывами учеников."
    write(ABOUT, page(pre, f"О проекте {SITE_NAME}: каталог обучения финансовых директоров", a_desc[:160], a_body,
                      [{"@context": "https://schema.org", "@type": "AboutPage", "name": "О проекте", "url": CANON, "description": a_desc[:160]},
                       {"@context": "https://schema.org", "@type": "Organization", "@id": SITE_URL + "/#org", "name": SITE_NAME, "url": SITE_URL + "/", "email": EMAIL}],
                      [("", "Каталог"), (None, "О проекте")]))

    # Статьи
    pre = "../../"
    for a in ARTICLES + ([] if CLEAN else DRAFTS):  # черновики — только в site/ для проверки владельцем
        draft = a in DRAFTS
        adate = a.get("date", ART_DATE)
        mark = '<aside class="atip"><b>Черновик</b><p>Статья пока не опубликована — ждёт проверки.</p></aside>' if draft else ""
        toc, body = render_article(a, pre)
        others = [x for x in ARTICLES if x["slug"] != a["slug"]][:3]
        rel_html = '<section><h2>Ещё из журнала</h2><div class="acards">' + "".join(
            f'<a class="acard" href="{link(pre, STATI + "/" + x["slug"] + "/")}"><img src="{pre}img/stati-{x["slug"]}.jpg" alt="" loading="lazy" width="600" height="315">'
            f'<b>{e(x["title"])}</b></a>' for x in others) + "</div></section>"
        page_body = (f'<article class="art"><h1 class="h-sm">{e(a["title"])}</h1><p class="ameta">Журнал {SITE_NAME} · {ru_date(adate)} · '
                     f'читать {a["read"]} мин</p>{mark}{art_cover(a, pre)}<p class="alead">{e(a["lead"])}</p>{toc}<div class="abody">{body}</div></article>{rel_html}')
        img = abs_url(f"img/stati-{a['slug']}.jpg")
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"], "description": a["desc"], "image": img,
              "datePublished": adate, "dateModified": adate, "inLanguage": "ru", "mainEntityOfPage": CANON,
              "author": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL + "/"}, "publisher": {"@id": SITE_URL + "/#org"}}
        write(f"{STATI}/{a['slug']}", page(pre, first_fit([a["title"], a["title"].split(":")[0]], 70), a["desc"][:165], page_body, [ld],
                                         [("", "Каталог"), (STATI + "/", "Журнал"), (None, a["title"].split(":")[0])], image=img, og_type="article"))
    pre = "../"
    cards = "".join(f'<a class="acard" href="{link(pre, STATI + "/" + x["slug"] + "/")}"><img src="{pre}img/stati-{x["slug"]}.jpg" alt="" loading="lazy" width="600" height="315">'
                    f'<b>{e(x["title"])}</b><p>{e(x["lead"][:150].rsplit(" ", 1)[0])}…</p></a>' for x in ARTICLES)
    st_desc = "Журнал о профессии финансового директора: путь в CFO, ключевые инструменты, деньги компании и выбор обучения — простым языком."
    write(STATI, page(pre, "Журнал о профессии финансового директора — " + SITE_NAME, st_desc,
                      f'<h1>Журнал: всё о работе финансового директора</h1><p class="bluf lead">Пишем о том, чем живёт CFO: деньги компании, отчёты, риски, '
                      f'карьера и обучение. Без воды и рекламных обещаний.</p><div class="acards hub">{cards}</div>',
                      [collection_ld("Журнал о профессии финансового директора", st_desc,
                                     {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
                                         {"@type": "ListItem", "position": i + 1, "url": abs_url(f"{STATI}/{x['slug']}/"), "name": x["title"]} for i, x in enumerate(ARTICLES)]})],
                      [("", "Каталог"), (None, "Журнал")]))

    # Страницы школ
    pre = "../../"
    for name, sp in SCHOOL_PAGE.items():
        dom = SCHOOL_DOMAINS[name]
        sc = order([c for c in C if c["school"] == name])
        sr = order([c for c in REL if c["school"] == name])
        srv = [r for r in R if r["about_finance"] and SCHOOL.get(r["school_slug"], {}).get("name") == name]
        st = stats(sc)
        pr = PROMO.get(dom)
        bl = (f"<p class='bluf lead'>В каталоге {n_prog(len(sc))} школы «{e(name)}» для финансовых директоров"
              + (f" и {n_prog(len(sr))} по соседним специализациям" if sr else "") + ".</p>"
              + facts_row(([("Цены", f"{rub(st['min'])} – {rub(st['max'])}" if st['max'] != st['min'] else rub(st['min']))] if sc and st['min'] else [])
                          + ([("Срок", e(dur_range(sc)))] if dur_range(sc) else []) + ([("Промокод", f"{e(pr['code'])} · −{e(pr['discount'])}")] if pr else [])
                          + [None] + doc_counts(sc, pre)))
        promo_box = promo(sc[0], "promo big") if sc else ""
        rel_html = ("<section><h2>Другие финансовые программы школы</h2><div class='cards'>" + "".join(rel_card(x, pre) for x in sr) + "</div></section>") if sr else ""
        rv_html = (f"<section><h2>Отзывы учеников школы «{e(name)}»</h2>" + "".join(review_html(r, pre, False) for r in srv[:6])
                   + f"<p><a href='{link(pre, REVIEWS + '/')}#school={urllib.parse.quote(name)}'>Читать все отзывы →</a></p></section>") if srv else ""
        others = sorted((n for n in SCHOOL_PAGE if n != name), key=lambda n: (PRIO.get(SCHOOL_DOMAINS[n], 999), n))[:8]
        oth = "".join(f'<a class="chip" href="{link(pre, "shkola/" + SCHOOL_PAGE[n] + "/")}">{e(n)}</a>' for n in others)
        body = f"""<h1 class="h-sm">«{e(name)}»: обучение финансового директора</h1>{verified_line(pre)}{bl}{promo_box}
<section><h2>Программы для CFO</h2><div class="cards">{''.join(card(c, pre) for c in sc)}</div></section>
{rel_html}{rv_html}<section><h2>Сравните с другими школами</h2><div class="chips">{oth}</div><p><a href="{link(pre, '')}">Весь каталог обучения финансового директора →</a></p></section>"""
        s_title = first_fit([f"{name}: курсы финансового директора, цены и отзывы", f"{name}: обучение финансового директора",
                             f"{TITLE_SHORT.get(name, name)}: курсы финдиректора"], 70)
        s_desc = fit_parts([f"Обучение финансового директора в школе «{name}»: {n_prog(len(sc))}" + (f", стоимость от {rub(st['min'])}" if sc and st['min'] else "") + ".",
                            f"Промокод {pr['code']} на −{pr['discount']}." if pr else "",
                            f"Отзывы учеников: {len(srv)}." if srv else "", "Документы, сроки и соседние программы."], 160)
        s_ld = {"@context": "https://schema.org", "@type": "EducationalOrganization", "name": name, "url": "https://" + dom,
                "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Обучение финансового директора",
                                    "itemListElement": [{"@type": "Offer", "itemOffered": {"@type": "Course", "name": c["title"], "url": abs_url(f"kurs/{c['id']}/")},
                                                         **({"price": c["price"], "priceCurrency": "RUB"} if c["price"] is not None else {})} for c in sc]}}
        write(f"shkola/{sp}", page(pre, s_title, s_desc, body, [s_ld, collection_ld(s_title, s_desc, itemlist(sc, name))],
                                   [("", "Каталог"), (None, name)]))

    # Смежные направления
    for k, d in RELATED.items():
        items = order([c for c in REL if c["dir"] == k])
        if not items:
            continue
        st = stats(items)
        bl = (f"<p class='bluf lead'>{n_prog(len(items))[0].upper() + n_prog(len(items))[1:]} от {n_school_gen(len({c['school'] for c in items}))}; цены сверены с сайтами школ.</p>"
              + facts_row([("Диапазон цен", f"{rub(st['min'])} – {rub(st['max'])}"), ("Медиана", rub(st['med']))]
                          + ([("Срок", e(dur_range(items)))] if dur_range(items) else []) + [None] + doc_counts(items, pre)))
        others = "".join(f'<a class="chip" href="{link(pre, d2["slug"] + "/")}">{e(d2["tab"])}</a>' for k2, d2 in RELATED.items() if k2 != k)
        body = f"""<h1>{e(d['h1'])}</h1>{verified_line(pre)}{bl}<section class="define"><h2>Как это связано с работой CFO</h2><p>{e(d['intro'])}</p></section>
<section><h2>Курсы</h2><div class="cards">{''.join(rel_card(c, pre) for c in items)}</div></section>
<section><h2>Соседние специализации</h2><div class="chips">{others}</div><p><a href="{link(pre, '')}">Каталог обучения финансового директора →</a></p></section>{schools_block(pre)}"""
        d_title = first_fit([f"{d['h1']}: {n_prog(len(items))} в 2026", f"{d['h1']} — {n_prog(len(items))}", d["h1"]], 70)
        d_desc = fit_parts([f"{d['h1']}. {n_prog(len(items))[0].upper() + n_prog(len(items))[1:]} от {n_school_gen(len({c['school'] for c in items}))}, стоимость {rub(st['min'])} – {rub(st['max'])}.",
                            "Полезно будущим финансовым директорам.", "Промокоды школ."], 160)
        il = {"@context": "https://schema.org", "@type": "ItemList", "name": d["h1"], "numberOfItems": len(items), "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "item": {"@type": "Course", "name": c["title"], "description": f"{c['title']} — {c['school']}",
                                                              "provider": {"@type": "EducationalOrganization", "name": c["school"], "url": "https://" + c["domain"]},
                                                              "offers": {"@type": "Offer", "category": "Paid", "price": c["price"], "priceCurrency": "RUB", "url": c["url"]}}}
            for i, c in enumerate(items)]}
        write(f"{d['slug']}", page("../../", d_title, d_desc, body,
                                                [collection_ld(d["h1"], d_desc, il)], [("", "Каталог"), (None, d["h1"])]))

    # 404
    nf = page("/" if CLEAN else "", "Ошибка 404 — " + SITE_NAME, "Страница не найдена. Вернитесь в каталог обучения финансового директора.",
              f'<h1>Такой страницы нет</h1><p>Похоже, программу убрали из каталога или адрес набран с ошибкой. <a href="{link("/" if CLEAN else "", "")}">Вернуться в каталог →</a></p>')
    (OUT / "404.html").write_text(nf.replace(CANON, abs_url("404.html")).replace('content="index,follow,max-image-preview:large"', 'content="noindex,follow"'), encoding="utf-8")
    if CLEAN:  # хостинг Vercel: чистые адреса /раздел/, своя 404.html подхватывается автоматически
        (OUT / "vercel.json").write_text(json.dumps({"cleanUrls": True, "trailingSlash": True, "headers": [
            {"source": "/assets/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=604800"}]},
            {"source": "/img/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=604800"}]}]}, indent=1), encoding="utf-8")

    # sitemap.xml (с картинками курсов)
    urls = [("", "1.0", None)] + [(f"{s_}/", "0.8", None) for s_ in LANDINGS if any(LANDINGS[s_]["f"](c) for c in C)] + \
           [(f"{REVIEWS}/", "0.7", None), (f"{METHOD}/", "0.3", None), (f"{ABOUT}/", "0.3", None), (f"{STATI}/", "0.6", None)] + [(f"{STATI}/{x['slug']}/", "0.6", x.get("date")) for x in ARTICLES] + [(f"kurs/{c['id']}/", "0.6", c) for c in C] + \
           [(f"shkola/{sp}/", "0.6", None) for sp in SCHOOL_PAGE.values()] + \
           [(f"{d['slug']}/", "0.6", None) for k, d in RELATED.items() if any(c["dir"] == k for c in REL)]
    def img_tag(c):
        if not isinstance(c, dict) or not (ROOT / "data/img" / f"{c['id']}.jpg").exists():
            return ""
        return f"<image:image><image:loc>{abs_url('img/' + c['id'] + '.jpg')}</image:loc><image:title>{e(c['title'] + ' — ' + c['school'])}</image:title></image:image>"
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
        + "".join(f"<url><loc>{abs_url(u)}</loc><lastmod>{c if isinstance(c, str) else LAST_CHECK}</lastmod>{img_tag(c)}</url>\n"
                  for u, pr, c in urls) + "</urlset>\n", encoding="utf-8")

    # robots.txt
    dup = "Disallow: /*index.html\n" if CLEAN else ""  # в site/ ссылки ведут на index.html — их не закрываем
    (OUT / "robots.txt").write_text(f"""User-agent: *
Allow: /
# дубли страниц: адреса с index.html (канонический адрес — папка /раздел/) и с параметрами (метки, сортировки)
{dup}Disallow: /*?
# служебная страница
Disallow: /404.html
# CSS, JS и картинки открыты — поисковикам нужны для отрисовки страниц
Allow: /assets/
Allow: /img/

User-agent: Yandex
Allow: /
{dup}Disallow: /404.html
Allow: /assets/
Allow: /img/
Clean-param: utm_source&utm_medium&utm_campaign&utm_content&utm_term&yclid&gclid&fbclid&from&ref

Sitemap: {SITE_URL}/sitemap.xml
""", encoding="utf-8")
    check_meta()
    print(f"Готово: {len(urls)} страниц в {OUT}" + ("" if CLEAN else f". Откройте {OUT / 'index.html'}"))


if __name__ == "__main__":
    build()

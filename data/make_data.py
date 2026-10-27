#!/usr/bin/env python3
"""Собирает data/courses.json из проверенных источников.

Курсы: фиды AdvCake/EDPartners и sitemap школ (проект «Сервис подбора курсов из фидов», data/courses.json
и data/sitemap_courses.json, выгрузка 08.10.2026). Часы, срок, документ, формат, рассрочка — со страницы
курса (проверено 09.10.2026). Если на странице значения нет, поле = None (не выдумываем).
Отзывы: provereno.pro/schools/<slug>/testimonials/ (первоисточник — otzovik.com / Яндекс), файл data/provereno_reviews.json.
"""
import json, re
from pathlib import Path

HERE = Path(__file__).parent
CHECKED = "2026-10-09"

# school_slug — slug школы на provereno.pro (None — школы там нет)
SCHOOLS = {
    "eduson.academy": ("Eduson Academy", "eduson-academy"),
    "sf.education": ("SF Education", "sf-education"),
    "mbschool.ru": ("Moscow Business School", "moscow-business-school"),
    "kidpo.ru": ("КИДПО", None),
    "ecodpo.ru": ("ЭКОДПО", "ecodpo"),
    "vado-dpo.ru": ("ВАДО", "vysshaya-akademiya-dopolnitelnogo-obrazovaniya"),
    "mupp-dpo.ru": ("МУПП", "mezhdunarodnyy-universitet-professionalnoy-perepodgotovki"),
    "skillbox.ru": ("Skillbox", "skillbox"),
    "netology.ru": ("Нетология", "netology"),
    "uprav.ru": ("Русская школа управления", "russkaya-shkola-upravleniya"),
    "ncpo.ru": ("НЦПО", "ncpo"),
    "moscow.mba": ("Московская Бизнес Академия", "moscow-mba"),
    "mipo.msk.ru": ("МИПО", "mipo"),
    "mitm.institute": ("MITM", "moskovskiy-institut-tekhnologiy-i-upravleniya"),
    "mitu.institute": ("mitu.institute", None),
    "apokdpo.ru": ("АПОК", "apok"),
    "e-mba.ru": ("City Business School", "e-mba"),
    "nadpo.ru": ("НАДПО", "nadpo"),
    "appkk.ru": ("ЦАППКК", "akademiya-professionalnogo-obrazovaniya-kadrov"),
    # школы только из блока «Финансовый менеджмент»
    "brunoyam.com": ("Бруноям", None),
    "practicum.yandex.ru": ("Яндекс Практикум", None),
    "gb.ru": ("GeekBrains", None),
    "ipo.msk.ru": ("Институт профессионального образования (ИПО)", None),
    "niidpo.ru": ("НИУДПО имени К. Д. Ушинского", None),
    "karpov.courses": ("Karpov.Courses", None),
}

PP, PK, KURS = "perepodgotovka", "povyshenie", "kurs"
DPP = "Диплом о профессиональной переподготовке"
UPK = "Удостоверение о повышении квалификации"

# (domain, title, url, type, doc, format, price, price_src, months, duration_text, hours, hours_text, installment, tags)
# price_src: feed — цена из партнёрского фида 08.10.2026; page — со страницы курса 09.10.2026
RAW = [
    ("eduson.academy", "Финансовый директор + нейросети для финансиста", "https://eduson.academy/findir", PP, DPP, "online", 126400, "feed", None, None, None, None, True, []),
    ("eduson.academy", "Финансовый директор: тариф Премиум", "https://eduson.academy/findir-pro", KURS, "Диплом об окончании курса", "online", 165200, "feed", 3.5, "3–4 месяца", None, None, True, []),
    ("sf.education", "Финансовый директор + ИИ", "https://sf.education/finmanager", KURS, "Диплом ДПО", "online", 98000, "feed", 7, "7 месяцев (16 модулей)", None, None, True, []),
    ("sf.education", "Mini-MBA: Цифровой финансовый директор (Digital CFO)", "https://sf.education/digitalcfo", KURS, "Диплом ДПО", "online", 196000, "feed", 12, "12 месяцев (28 модулей)", None, None, True, ["mini-mba"]),
    ("sf.education", "Mini-MBA: Финансовый директор", "https://sf.education/minimba_finmanager", PK, UPK, "online", 180250, "feed", 10, "10 месяцев (16 модулей)", None, None, True, ["mini-mba"]),
    ("mbschool.ru", "Финансовый директор. Управление финансами организации", "https://mbschool.ru/seminars/7468/", PK, "Удостоверение о повышении квалификации или сертификат MBS", "mixed", 59900, "feed", 0.1, "3 дня", None, None, True, []),
    ("mbschool.ru", "Финансовый директор (CFO). Профпереподготовка", "https://mbschool.ru/seminars/intensive_mba/upravlenie-finansami/", PP, DPP, "mixed", 199000, "feed", 5, "5 месяцев", None, None, True, []),
    ("kidpo.ru", "Финансовый директор", "https://kidpo.ru/pp/finansovyy-direktor/", PP, DPP, "online", 24550, "page", None, None, 256, "от 256 ак. ч", True, []),
    ("kidpo.ru", "Финансовый директор банка", "https://kidpo.ru/pp/finansovyy-direktor-banka-pp/", PP, DPP, "online", 24550, "page", None, None, 256, "от 256 ак. ч", True, ["bank"]),
    ("ecodpo.ru", "Финансовый директор — переподготовка", "https://ecodpo.ru/finansovyy-direktor-pp/", PP, DPP, "online", 54980, "feed", 1.5, "от 1,5 месяца", 250, "от 250 ч", True, []),
    ("vado-dpo.ru", "Финансовый директор", "https://vado-dpo.ru/kursy/finansovyj_direktor", PP, DPP, "online", 11300, "feed", 3, "3 месяца", 520, "520 ч", True, []),
    ("mupp-dpo.ru", "Финансовый директор", "https://mupp-dpo.ru/kursy/finansovyj_direktor", PP, DPP, "online", 11500, "feed", 3, "3 месяца", 520, "520 ч", True, []),
    ("skillbox.ru", "Финансовый директор", "https://skillbox.ru/course/financial-director/", KURS, "Сертификат Skillbox", "online", 177282, "feed", 4, "4 месяца", 263, "33 ч теории + 230 ч практики", True, []),
    ("netology.ru", "Финансовый директор", "https://netology.ru/programs/financial_director", PK, UPK, "online", 107100, "feed", 4, "4 месяца", None, None, True, []),
    ("uprav.ru", "Финансовый директор (повышение квалификации)", "https://uprav.ru/finansy-economics/finansovyy-direktor/", PK, UPK, "mixed", 99000, "feed", None, None, 40, "40 ак. ч", True, []),
    ("uprav.ru", "Финансовый директор (профессиональная переподготовка)", "https://uprav.ru/finansy-economics/finansovyy-direktor-professionalnaya-perepodgotovka/", PP, DPP, "mixed", 350000, "page", None, None, 300, "300 ак. ч", True, []),
    ("ncpo.ru", "Профессиональная переподготовка «Финансовый директор»", "https://ncpo.ru/profperepodgotovka/pp-finansovyy-direktor/", PP, DPP, "online", 15850, "feed", 2, "от 2 до 9 месяцев", 256, "от 256 ак. ч", True, []),
    ("moscow.mba", "Финансовый директор", "https://moscow.mba/programs/profession/online/finansovyj-direktor", PP, DPP, "online", 211200, "feed", 8, "8 месяцев", None, None, True, []),
    ("mipo.msk.ru", "Финансовый директор", "https://mipo.msk.ru/professions/finansovyj-menedzhment/finansovyj-direktor", PP, DPP, "online", 42500, "feed", None, None, 1046, "1046 ч", True, []),
    ("mitm.institute", "Финансовый директор", "https://mitm.institute/programs/kursy/menedzhment/perepodgotovka/finansovyj-direktor", PP, DPP, "online", 192000, "feed", 8, "8 месяцев", 676, "676 ч", True, []),
    ("mitu.institute", "Финансовый директор", "https://mitu.institute/programs/dopolnitelnoe-obrazovanie/menedzhment/finansovyj-direktor", PP, DPP, "online", 192000, "feed", 8, "8 месяцев", None, None, True, []),
    ("apokdpo.ru", "Финансовый директор — курс переподготовки", "https://apokdpo.ru/professionalnaya-perepodgotovka/ekonomika-i-finansy/finansovyj-direktor/", PP, DPP, "online", 39910, "feed", None, None, 256, "от 256 ч", True, []),
    ("apokdpo.ru", "Финансовый директор банка", "https://apokdpo.ru/professionalnaya-perepodgotovka/bankovskoe-delo/finansovyy-direktor-banka-pp/", PP, DPP, "online", 39910, "page", None, None, 256, "от 256 ч", True, ["bank"]),
    ("e-mba.ru", "MBA: Финансовый директор (CFO)", "https://lp.e-mba.ru/findir", PP, DPP, "online", 109000, "feed", 8, "8 месяцев", 876, "876 ак. ч", True, ["mba"]),
    ("nadpo.ru", "Финансовый директор. Московский диплом", "https://psy.nadpo.ru/financial_director", PP, DPP, "online", 82600, "feed", 5, "5 месяцев", None, None, True, []),
    ("appkk.ru", "Финансовый директор", "https://appkk.ru/dist_ob/finansovyy-direktor/", PP, DPP, "online", 70700, "page", 5, "5 месяцев", 580, "580 ч", True, []),
    # добавлены 10.10.2026: «Директор по финансам» / «Директор по экономике и финансам» и MBA по списку пользователя
    ("eduson.academy", "Директор по экономике и финансам + ИИ", "https://eduson.academy/director-economy-finance", PP, DPP, "online", 165200, "feed", 6, "6 месяцев", None, None, True, []),
    ("eduson.academy", "Директор по экономике и финансам: тариф PRO", "https://eduson.academy/director-economy-finance-pro", PP, DPP, "online", 185200, "feed", None, None, None, None, True, []),
    ("mipo.msk.ru", "Директор по финансам", "https://mipo.msk.ru/professions/finansovyj-menedzhment/direktor-po-finansam", PP, DPP, "online", 43900, "page", 8, "8 месяцев", 692, "692 ч", True, []),
    ("mipo.msk.ru", "MBA: Управление финансами", "https://mipo.msk.ru/mba/mba/upravlenie-finansami-1", PP, "Диплом MBA", "online", None, None, 18, "1 год 6 месяцев", 2700, "2700 ч", None, ["mba"]),
    ("e-mba.ru", "Директор по финансам", "https://e-mba.ru/catalog/direktor-po-finansam", KURS, "Зависит от тарифа: диплом школы, удостоверение о повышении квалификации или диплом о переподготовке", "online", 54400, "page", 4, "4–6 месяцев", 166, "166–264 ак. ч", True, []),
]

# Данные со страниц курсов (проверено 09–10.10.2026), только то, что школа явно указала:
# price — актуальная цена, если на странице она ниже цены из фида (фид отдаёт полную цену); old — зачёркнутая цена;
# monthly — платёж в месяц из блока «Стоимость» (months — срок рассрочки); aud — для кого курс по разделу «Для кого/Кому подойдёт»:
# beg — с нуля / начинающим, acc — главным бухгалтерам, own — собственникам и предпринимателям.
PAGE_EXTRA = {
    "https://eduson.academy/findir-pro": dict(aud=["beg", "acc", "own"]),
    "https://eduson.academy/director-economy-finance": dict(aud=["own"]),
    "https://eduson.academy/director-economy-finance-pro": dict(aud=["acc", "own"]),
    "https://sf.education/finmanager": dict(aud=["beg"]),
    "https://sf.education/minimba_finmanager": dict(aud=["beg"]),
    "https://mbschool.ru/seminars/7468/": dict(aud=["acc"]),
    "https://mbschool.ru/seminars/intensive_mba/upravlenie-finansami/": dict(monthly=6208, months=24, aud=["own"]),
    "https://kidpo.ru/pp/finansovyy-direktor/": dict(old=30350, monthly=2045, months=12),
    "https://kidpo.ru/pp/finansovyy-direktor-banka-pp/": dict(old=30350, monthly=2045, months=12),
    "https://ecodpo.ru/finansovyy-direktor-pp/": dict(price=32980, old=54980, monthly=2749, months=12),
    "https://vado-dpo.ru/kursy/finansovyj_direktor": dict(old=17385, aud=["beg"]),
    "https://mupp-dpo.ru/kursy/finansovyj_direktor": dict(old=17700, aud=["beg", "own"]),
    "https://skillbox.ru/course/financial-director/": dict(monthly=5719, months=31, aud=["beg", "own"]),
    "https://netology.ru/programs/financial_director": dict(aud=["acc"]),
    "https://uprav.ru/finansy-economics/finansovyy-direktor/": dict(monthly=9900, months=10),
    "https://uprav.ru/finansy-economics/finansovyy-direktor-professionalnaya-perepodgotovka/": dict(monthly=35000, months=10),
    "https://ncpo.ru/profperepodgotovka/pp-finansovyy-direktor/": dict(old=17250, monthly=1320, months=12, aud=["acc", "own"]),
    "https://moscow.mba/programs/profession/online/finansovyj-direktor": dict(monthly=5866, months=36, aud=["beg"]),
    "https://mipo.msk.ru/professions/finansovyj-menedzhment/finansovyj-direktor": dict(old=65400, monthly=1750, months=24, aud=["beg", "acc", "own"]),
    "https://mipo.msk.ru/professions/finansovyj-menedzhment/direktor-po-finansam": dict(old=67500, monthly=1850, months=24),
    "https://mipo.msk.ru/mba/mba/upravlenie-finansami-1": dict(aud=["own"]),
    "https://mitm.institute/programs/kursy/menedzhment/perepodgotovka/finansovyj-direktor": dict(monthly=5330, months=36, aud=["beg", "own"]),
    "https://mitu.institute/programs/dopolnitelnoe-obrazovanie/menedzhment/finansovyj-direktor": dict(monthly=5330, months=36, aud=["own"]),
    "https://apokdpo.ru/professionalnaya-perepodgotovka/ekonomika-i-finansy/finansovyj-direktor/": dict(price=32980, old=39910, monthly=2748, months=12),
    "https://apokdpo.ru/professionalnaya-perepodgotovka/bankovskoe-delo/finansovyy-direktor-banka-pp/": dict(price=32980, old=39910, monthly=2748, months=12),
    "https://lp.e-mba.ru/findir": dict(old=278000, monthly=4542, months=24, aud=["acc", "own"]),
    "https://e-mba.ru/catalog/direktor-po-finansam": dict(old=136000, monthly=2267, months=24, aud=["own"]),
    "https://psy.nadpo.ru/financial_director": dict(old=119700, monthly=6883, months=12),
    "https://appkk.ru/dist_ob/finansovyy-direktor/": dict(old=141400, monthly=5892, months=12, aud=["acc", "own"]),
}

# Смежные направления (закрывают интент будущего финдиректора), цены из фидов школ 08.10.2026, страницы отвечают 200.
# (direction, domain, title, url, price)
RELATED_RAW = [
    ("msfo", "eduson.academy", "Основы МСФО", "https://eduson.academy/msfo", 36800),
    ("msfo", "sf.education", "МСФО от А до Я", "https://sf.education/msfocourse", 24990),
    ("msfo", "mbschool.ru", "МСФО (IAS) 7. Отчёт о движении денежных средств", "https://mbschool.ru/seminars/231440/", 23900),
    ("model", "sf.education", "Финансовое моделирование", "https://sf.education/basefinmod", 35000),
    ("model", "sf.education", "Расширенное финансовое моделирование", "https://sf.education/modeling", 60025),
    ("model", "eduson.academy", "Финансовое моделирование", "https://eduson.academy/fin-modeling", 42000),
    ("model", "skillbox.ru", "Финансовое моделирование", "https://skillbox.ru/course/financial-modeling/", 57136),
    ("model", "uprav.ru", "Финансовое моделирование", "https://uprav.ru/finansy-economics/finansovoe-modelirovanie-biznesa/", 18000),
    ("model", "uprav.ru", "Финансовое планирование и моделирование", "https://uprav.ru/finansy-economics/finansovoe-planirovanie/", 89000),
    ("model", "uprav.ru", "Бюджетирование", "https://uprav.ru/finansy-economics/byudzhetirovanie-praktika-razrabotki-i-vnedreniya/", 79000),
    ("model", "uprav.ru", "Бюджетирование и управленческий учёт в организации", "https://uprav.ru/finansy-economics/kurs-byudzhetirovanie-i-upravlencheskij-uchet-v-organizacii/", 89000),
    ("model", "mbschool.ru", "Финансовое моделирование инвестиционных проектов (практикум в Excel)", "https://mbschool.ru/seminars/251210/", 45900),
    ("model", "mbschool.ru", "Бюджетирование и управленческая отчётность с помощью Excel", "https://mbschool.ru/seminars/113266/", 45900),
    ("model", "mbschool.ru", "Бюджетирование и управленческий учёт в организации", "https://mbschool.ru/seminars/106529/", 49900),
    ("model", "mbschool.ru", "Бюджетирование и управленческий учёт в новой экономической реальности", "https://mbschool.ru/seminars/7983/", 45900),
    ("model", "mbschool.ru", "Финансовый анализ, бюджетирование и управление денежными потоками", "https://mbschool.ru/seminars/106327/", 49900),
    ("model", "niidpo.ru", "Управленческий учёт и финансовое планирование в организации", "https://niidpo.ru/seminar/upravlencheskij-uchet-i-finansovoe-planirovanie", 13100),
    ("analyst", "eduson.academy", "Финансовый аналитик + ИИ", "https://eduson.academy/fin-analyst", 85600),
    ("analyst", "sf.education", "Финансовый аналитик + ИИ", "https://sf.education/financialanalyst", 74998),
    ("analyst", "sf.education", "Mini-MBA: Финансовый аналитик", "https://sf.education/minimba_financialanalyst", 133000),
    ("analyst", "moscow.mba", "Финансовый аналитик", "https://moscow.mba/programs/profession/online/Finansovyj-analitik", 149000),
    ("analyst", "mipo.msk.ru", "Финансовый анализ", "https://mipo.msk.ru/professions/jekonomika/finansovyj-analiz", 46500),
    ("analyst", "mbschool.ru", "Финансовый аналитик / Руководитель финансово-аналитической службы", "https://mbschool.ru/seminars/8019/", 45900),
    ("analyst", "mbschool.ru", "Финансовый анализ: оценка финансового состояния компании", "https://mbschool.ru/seminars/23648/", 45900),
    ("analyst", "uprav.ru", "Финансовый аналитик", "https://uprav.ru/finansy-economics/finansovyy-analitik/", 79000),
    ("analyst", "uprav.ru", "Финансовый анализ", "https://uprav.ru/finansy-economics/finansovyy-analiz/", 59000),
    ("analyst", "skillbox.ru", "Финансовый аналитик", "https://skillbox.ru/course/financial-analyst/", 117106),
    ("analyst", "netology.ru", "Финансовый аналитик", "https://netology.ru/programs/professiya_financial_analyst", 70900),
    ("analyst", "karpov.courses", "Финансовая аналитика 2.0: от Excel к BI-системам", "https://karpov.courses/fin-data-analytics", 119000),
    ("analyst", "kidpo.ru", "Финансовый аналитик", "https://kidpo.ru/pp/finansovyy-analitik/", 24550),
    ("analyst", "ecodpo.ru", "Финансовый аналитик — переподготовка", "https://ecodpo.ru/finansovyy-analitik-pp/", 54980),
    ("analyst", "vado-dpo.ru", "Финансовый аналитик", "https://vado-dpo.ru/kursy/finansovyj_analitik", 11300),
    ("analyst", "mupp-dpo.ru", "Финансовый аналитик", "https://mupp-dpo.ru/kursy/finansovyj_analitik", 11500),
    ("analyst", "apokdpo.ru", "Финансовый аналитик — переподготовка", "https://apokdpo.ru/professionalnaya-perepodgotovka/ekonomika-i-finansy/finansovyj-analitik/", 39910),
]


# Смежные направления: данные со страниц курсов (10.10.2026). Только однозначные формулировки школы
# («Срок обучения», «Продолжительность», «Выдаваемые документы»); если на странице несколько тарифов
# или формулировка неоднозначна — поле не заполняем (на сайте «—»).
# url: (doc, duration, months, hours_text, format)
REL_EXTRA = {
    "https://moscow.mba/programs/profession/online/upravlenie-finansami": (None, "7 месяцев", 7, None, "online"),
    "https://moscow.mba/programs/mba/online/financial-management": (None, "18 месяцев", 18, None, "online"),
    "https://mitm.institute/programs/mba/ekonomika/upravlenie-finansami": ("Диплом о профессиональной переподготовке", "9 месяцев", 9, None, "online"),
    "https://mipo.msk.ru/professions/finansovyj-menedzhment/finansovyj-menedzhment": ("Диплом о профессиональной переподготовке", "7 месяцев", 7, "1046 ч", "online"),
    "https://mbschool.ru/seminars/128400/": ("Диплом о профессиональной переподготовке", "8 месяцев", 8, None, "mixed"),
    "https://mbschool.ru/seminars/7761/": ("Удостоверение о повышении квалификации или сертификат MBS", "4 дня", 0.13, None, "mixed"),
    "https://mbschool.ru/seminars/106017/": ("Сертификат о повышении квалификации ИПБ России", "3 дня", 0.1, "40 ак. ч", "mixed"),
    "https://uprav.ru/mba/mini-mba-upravlenie-finansami/": ("Диплом о профессиональной переподготовке", None, None, "300 ак. ч", None),
    "https://uprav.ru/rukovoditel/upravlenie-finansami-dlya-rukovoditelya/": ("Удостоверение о повышении квалификации", None, None, "16 ак. ч", None),
    "https://netology.ru/programs/financial_manager": (None, "от 4 до 8 месяцев (по тарифу)", 4, None, None),
    "https://lp.e-mba.ru/mba-intensive-finance": (None, "12 месяцев", 12, "1152 ч", None),
    "https://brunoyam.com/online-kursy/financial-management": ("Удостоверение о повышении квалификации", None, None, None, None),
    "https://practicum.yandex.ru/financial-management/": ("Два удостоверения о повышении квалификации: НИУ ВШЭ и Практикума", "3 месяца", 3, None, "online"),
    "https://ipo.msk.ru/professionalnaja-perepodgotovka/menedzhment/finansovyj-menedzhment-pp/": ("Диплом о профессиональной переподготовке", "12 месяцев", 12, "1046 ч", None),
    "https://ipo.msk.ru/professionalnaja-perepodgotovka/jekonomika/finansovyj-menedzhment-i-finansovyj-analiz/": ("Диплом о профессиональной переподготовке", "10 месяцев", 10, "870 ч", None),
    "https://ipo.msk.ru/professionalnaja-perepodgotovka/jekonomika/upravlenie-finansami/": ("Диплом о профессиональной переподготовке", "8 месяцев", 8, "706 ч", None),
    "https://ipo.msk.ru/povyshenie-kvalifikacii/menedzhment-cat-pk/finansovyj-menedzhment-pk/": ("Удостоверение о повышении квалификации", "до 1 месяца", 1, "72 ч", "online"),
    "https://appkk.ru/dist_ob/uchet_i_finansovyy_menedzhment/": ("Диплом о профессиональной переподготовке", "2 месяца", 2, "260 ч", "online"),
    "https://apokdpo.ru/professionalnaya-perepodgotovka/menedzhment/finansovyy-menedzhment-pp/": ("Диплом о профессиональной переподготовке", None, None, "от 256 ч", "online"),
    "https://ecodpo.ru/finansovyy-menedzhment-pp/": ("Диплом о профессиональной переподготовке", "от 1,5 месяца", 1.5, "от 250 ч", "online"),
    "https://kidpo.ru/pp/finansovyy-menedzhment-pp/": ("Диплом о профессиональной переподготовке", None, None, "от 256 ак. ч", "online"),
    "https://eduson.academy/msfo": (None, "1–2 месяца", 1, None, "online"),
    "https://mbschool.ru/seminars/231440/": ("Удостоверение о повышении квалификации или сертификат MBS", "1 день", 0.03, None, "mixed"),
    "https://eduson.academy/fin-modeling": (None, "1–2 месяца", 1, None, "online"),
    "https://uprav.ru/finansy-economics/finansovoe-modelirovanie-biznesa/": ("Удостоверение о повышении квалификации", None, None, "16 ак. ч", None),
    "https://uprav.ru/finansy-economics/finansovoe-planirovanie/": ("Удостоверение о повышении квалификации", None, None, "32 ак. ч", None),
    "https://uprav.ru/finansy-economics/byudzhetirovanie-praktika-razrabotki-i-vnedreniya/": ("Удостоверение о повышении квалификации", None, None, "24 ак. ч", None),
    "https://uprav.ru/finansy-economics/kurs-byudzhetirovanie-i-upravlencheskij-uchet-v-organizacii/": ("Удостоверение о повышении квалификации", None, None, "32 ак. ч", None),
    "https://mbschool.ru/seminars/251210/": ("Удостоверение о повышении квалификации или сертификат MBS", "4 недели", 1, None, "online"),
    "https://mbschool.ru/seminars/113266/": ("Удостоверение о повышении квалификации или сертификат MBS", "2 дня", 0.07, None, "mixed"),
    "https://mbschool.ru/seminars/106529/": ("Сертификат о повышении квалификации ИПБ России", "2 дня", 0.07, "20 ак. ч", "mixed"),
    "https://mbschool.ru/seminars/7983/": ("Удостоверение о повышении квалификации или сертификат MBS", "2 дня", 0.07, None, "mixed"),
    "https://mbschool.ru/seminars/106327/": ("Сертификат о повышении квалификации ИПБ России", "2 дня", 0.07, "40 ак. ч", "mixed"),
    "https://niidpo.ru/seminar/upravlencheskij-uchet-i-finansovoe-planirovanie": (None, "12 недель", 3, None, "online"),
    "https://eduson.academy/fin-analyst": (None, "2–3 месяца", 2, None, "online"),
    "https://moscow.mba/programs/profession/online/Finansovyj-analitik": (None, "6 месяцев", 6, None, "online"),
    "https://mipo.msk.ru/professions/jekonomika/finansovyj-analiz": ("Диплом о профессиональной переподготовке", "11 месяцев", 11, "924 ч", "online"),
    "https://mbschool.ru/seminars/8019/": ("Удостоверение о повышении квалификации или сертификат MBS", "2 дня", 0.07, None, "mixed"),
    "https://mbschool.ru/seminars/23648/": ("Удостоверение о повышении квалификации или сертификат MBS", "2 дня", 0.07, None, "mixed"),
    "https://uprav.ru/finansy-economics/finansovyy-analitik/": (None, None, None, "40 ак. ч", None),
    "https://uprav.ru/finansy-economics/finansovyy-analiz/": (None, None, None, "24 ак. ч", None),
    "https://netology.ru/programs/professiya_financial_analyst": ("Диплом о профессиональной переподготовке", None, None, None, None),
    "https://karpov.courses/fin-data-analytics": ("Удостоверение о повышении квалификации", "3 месяца", 3, None, "online"),
    "https://kidpo.ru/pp/finansovyy-analitik/": ("Диплом о профессиональной переподготовке", None, None, "от 256 ак. ч", "online"),
    "https://ecodpo.ru/finansovyy-analitik-pp/": ("Диплом о профессиональной переподготовке", "от 1,5 месяца", 1.5, "от 250 ч", "online"),
    "https://vado-dpo.ru/kursy/finansovyj_analitik": ("Диплом о профессиональной переподготовке", "3 месяца", 3, "520 ч", "online"),
    "https://mupp-dpo.ru/kursy/finansovyj_analitik": ("Диплом о профессиональной переподготовке", "3 месяца", 3, "520 ч", "online"),
    "https://apokdpo.ru/professionalnaya-perepodgotovka/ekonomika-i-finansy/finansovyj-analitik/": ("Диплом о профессиональной переподготовке", None, None, "от 256 ч", "online"),
}

# Блок «Вам могут быть интересны курсы по финансовому менеджменту»: (domain, title, url, price)
# Цены — из фидов школ 08.10.2026 (Яндекс Практикум и ИПО — со страниц 10.10.2026); все страницы отвечают 200
FM_RAW = [
    ("sf.education", "Финансовый менеджер", "https://sf.education/finman", 70000),
    ("sf.education", "Mini-MBA: Финансовый менеджер", "https://sf.education/minimbafinman", 120000),
    ("eduson.academy", "MBA Эксперт: Управление финансами с ИИ", "https://eduson.academy/mba-finance", 227600),
    ("moscow.mba", "Финансовый менеджер", "https://moscow.mba/programs/profession/online/upravlenie-finansami", 119200),
    ("moscow.mba", "MBA: Управление финансами", "https://moscow.mba/programs/mba/online/financial-management", 390500),
    ("mitm.institute", "MBA: Управление финансами", "https://mitm.institute/programs/mba/ekonomika/upravlenie-finansami", 286000),
    ("nadpo.ru", "Финансовый менеджмент", "https://psy.nadpo.ru/finansoviy-menedjer", 34500),
    ("mipo.msk.ru", "Финансовый менеджмент", "https://mipo.msk.ru/professions/finansovyj-menedzhment/finansovyj-menedzhment", 32500),
    ("mbschool.ru", "Финансовый менеджер. Профессия", "https://mbschool.ru/seminars/128400/", 219000),
    ("mbschool.ru", "Финансовый менеджер: корпоративные финансы, финмоделирование, оценка бизнеса", "https://mbschool.ru/seminars/7761/", 69900),
    ("mbschool.ru", "Финансовый менеджмент (повышение квалификации ИПБ России)", "https://mbschool.ru/seminars/106017/", 69900),
    ("uprav.ru", "Mini MBA: Управление финансами", "https://uprav.ru/mba/mini-mba-upravlenie-finansami/", 350000),
    ("uprav.ru", "Управление финансами для руководителя", "https://uprav.ru/rukovoditel/upravlenie-finansami-dlya-rukovoditelya/", 18000),
    ("skillbox.ru", "Профессия Финансовый менеджер", "https://skillbox.ru/course/profession-finance-manager/", 90514),
    ("netology.ru", "Финансовый менеджмент", "https://netology.ru/programs/financial_manager", 76100),
    ("e-mba.ru", "MBA: Управление финансами", "https://lp.e-mba.ru/mba-intensive-finance", 238400),
    ("brunoyam.com", "Финансовый менеджмент", "https://brunoyam.com/online-kursy/financial-management", 29900),
    ("practicum.yandex.ru", "Финансовый менеджмент", "https://practicum.yandex.ru/financial-management/", 95500),
    ("gb.ru", "Профессия Финансовый менеджер", "https://gb.ru/geek_university/management/finance-manager", 77238),
    # ИПО (ipo.msk.ru) — цены со страниц курсов 10.10.2026
    ("ipo.msk.ru", "Финансовый менеджмент — переподготовка", "https://ipo.msk.ru/professionalnaja-perepodgotovka/menedzhment/finansovyj-menedzhment-pp/", 50400),
    ("ipo.msk.ru", "Финансовый менеджмент и финансовый анализ", "https://ipo.msk.ru/professionalnaja-perepodgotovka/jekonomika/finansovyj-menedzhment-i-finansovyj-analiz/", 50400),
    ("ipo.msk.ru", "Управление финансами", "https://ipo.msk.ru/professionalnaja-perepodgotovka/jekonomika/upravlenie-finansami/", 44400),
    ("ipo.msk.ru", "Финансовый менеджмент — повышение квалификации", "https://ipo.msk.ru/povyshenie-kvalifikacii/menedzhment-cat-pk/finansovyj-menedzhment-pk/", 6400),
    ("appkk.ru", "Учёт и финансовый менеджмент", "https://appkk.ru/dist_ob/uchet_i_finansovyy_menedzhment/", 22200),
    ("apokdpo.ru", "Финансовый менеджмент — переподготовка", "https://apokdpo.ru/professionalnaya-perepodgotovka/menedzhment/finansovyy-menedzhment-pp/", 39910),
    ("ecodpo.ru", "Финансовый менеджмент — переподготовка", "https://ecodpo.ru/finansovyy-menedzhment-pp/", 54980),
    ("kidpo.ru", "Финансовый менеджмент", "https://kidpo.ru/pp/finansovyy-menedzhment-pp/", 24550),
]

# Названия школ — по правилам course_article_service (known_schools.py): promo_codes.json, затем
# school_name_rules.json (приоритетнее). Для доменов, которых там нет, остаётся название из SCHOOLS.
NAMES_DIR = Path("/Users/tatyana/Downloads/course_article_service 4/data")


def known_names():
    names = {d: e["school"] for d, e in json.loads((NAMES_DIR / "promo_codes.json").read_text(encoding="utf-8")).items()}
    names.update({d: r["correct"] for d, r in json.loads((NAMES_DIR / "school_name_rules.json").read_text(encoding="utf-8")).items()})
    return names


# Короткие названия для агрегатора (без расшифровки аббревиатуры) — приоритетнее справочников
SHORT_NAMES = {"nadpo.ru": "НАДПО", "appkk.ru": "ЦАППКК", "mipo.msk.ru": "МИПО", "mitm.institute": "MITM",
               "mbschool.ru": "Московская Бизнес Школа", "uprav.ru": "Русская Школа Управления"}

for _d, (_n, _slug) in list(SCHOOLS.items()):
    SCHOOLS[_d] = (SHORT_NAMES.get(_d) or known_names().get(_d, _n), _slug)

# Отзыв относится к курсам по финансам, только если в нём явно назван финансовый курс или тема
FIN = re.compile(r"финансов\w*\s+(?:директор|аналитик|менедж|модел|анализ|учет|учёт|отчетн|отчётн|контрол|грамотн)\w*|финдир|\bCFO\b|корпоративн\w+\s+финанс|управлени\w+\s+финанс|МСФО|бюджетирован|инвестиционн\w+\s+анализ|оценк\w+\s+бизнеса|курс\w*\s+по\s+финанс|финансов\w+\s+тематик|экономик\w+\s+и\s+финанс|\bфинанс(?:ы|ам|ах)\b", re.I)
# Совпали по словам, но не про курсы по финансам (проверено вручную 10.10.2026): обзоры всего каталога,
# MBA с финансами как одним из модулей, «финансы» в смысле денег, финтех-безопасность, госуправление
FIN_EXCLUDE = ["3218110189_18540_0af48cf02ff21481fbf9bd87f0449a61", "3218110189_18660_93a1eadbfbcb83522f61c623a31b20fd", "3218110189_30408_b58e9ad346d5f843dacb884e76c4c7c0", "3218110189_28493_540f92dc0860c75ddfc7a9e9d5ea2926", "3218110189_28632_2bc2dbb36be5e184edd9bfc58cc384ce", "3218110189_28751_b58e9ad346d5f843dacb884e76c4c7c0", "3218110189_28336_b172b17fdc0423641c75868328eacf0f", "3218110189_24555_0af48cf02ff21481fbf9bd87f0449a61", "3218110189_21992_b58e9ad346d5f843dacb884e76c4c7c0", "3218110189_22035_2bc2dbb36be5e184edd9bfc58cc384ce", "3218110189_22051_540f92dc0860c75ddfc7a9e9d5ea2926", "3218110189_24111_0af48cf02ff21481fbf9bd87f0449a61", "3218110189_24261_0af48cf02ff21481fbf9bd87f0449a61"]


def slugify(domain, url):
    return re.sub(r"[^a-z0-9]+", "-", (domain.split(".")[0] + "-" + url.rstrip("/").rsplit("/", 1)[-1]).lower()).strip("-")


def main():
    prov = json.loads((HERE / "provereno_reviews.json").read_text(encoding="utf-8"))
    sinfo = {s["slug"]: s for s in prov["schools"]}
    courses = []
    for d, title, url, typ, doc, fmt, price, psrc, months, dur, hours, htxt, inst, tags in RAW:
        x = PAGE_EXTRA.get(url, {})
        if x.get("price"):
            price, psrc = x["price"], "page"
        name, slug = SCHOOLS[d]
        si = sinfo.get(slug) if slug else None
        courses.append(dict(id=slugify(d, url), school=name, domain=d, school_slug=slug, title=title, url=url, type=typ,
                            doc=doc, format=fmt, price=price, price_src=psrc, months=months, duration=dur,
                            hours=hours, hours_text=htxt, installment=inst, tags=tags,
                            old_price=x.get("old"), monthly=x.get("monthly"), monthly_months=x.get("months"), aud=x.get("aud", []),
                            school_rating=si["rating"] if si else None, school_reviews=si["reviews_total"] if si else 0,
                            checked=CHECKED))
    fm = [dict(id=slugify(d, url), school=SCHOOLS[d][0], domain=d, title=title, url=url, price=price, dir="fm")
          for d, title, url, price in FM_RAW]
    fm += [dict(id=slugify(d, url), school=SCHOOLS[d][0], domain=d, title=title, url=url, price=price, dir=dr)
           for dr, d, title, url, price in RELATED_RAW]
    for c in fm:
        doc, dur, months, htxt, fmt = REL_EXTRA.get(c["url"], (None, None, None, None, None))
        c.update(doc=doc, duration=dur, months=months, hours_text=htxt, format=fmt)
    used = {c["school_slug"] for c in courses if c["school_slug"]}
    reviews = []
    for slug in used:
        rs = [r for r in prov["reviews"] if r["school_slug"] == slug]
        fin = [r for r in rs if FIN.search(r["pros"] + " | " + r["text"]) and r["id"] not in FIN_EXCLUDE]
        rest = [r for r in rs if r not in fin][:6]  # первые на странице = самые свежие
        for r in fin + rest:
            reviews.append(dict(r, about_finance=r in fin))
    schools = [dict(name=SCHOOLS[d][0], domain=d, slug=SCHOOLS[d][1],
                    rating=sinfo[SCHOOLS[d][1]]["rating"] if SCHOOLS[d][1] else None,
                    reviews_total=sinfo[SCHOOLS[d][1]]["reviews_total"] if SCHOOLS[d][1] else 0)
               for d in SCHOOLS]
    out = dict(updated=CHECKED, sources=dict(
        courses="Партнёрские фиды AdvCake и EDPartners + страницы курсов",
        reviews="provereno.pro (первоисточник — otzovik.com и Яндекс)"), schools=schools, courses=courses, fm_courses=fm, reviews=reviews)
    (HERE / "courses.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(courses), "курсов,", len(reviews), "отзывов")


if __name__ == "__main__":
    main()

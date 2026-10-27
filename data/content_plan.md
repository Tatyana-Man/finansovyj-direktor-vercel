# Контент-план журнала (/stati/) — CFO Навигатор (finansovyj-direktor.vercel.app)

Одна статья = один интент. Темы не пересекаются с журналом finansovyj-direktor.ru — не брать оттуда ни темы, ни тексты.
Черновик пишется в `data/drafts/<slug>.py`, после одобрения (`python3 data/approve_article.py <slug>`) уходит в `data/zhurnal/`.
Обложка: `python3 data/make_cover.py <slug> "<Заголовок>" <минут>`.

Статусы: в очереди · черновик · опубликовано · отложено

## Опубликовано
| slug | Тема | Куда ведём |
|------|------|-----------|
| kassovyj-razryv | Кассовый разрыв: как финдиректор его предупреждает | povyshenie-kvalifikacii, finansovoe-modelirovanie |
| tochka-bezubytochnosti | Точка безубыточности: расчёт для CFO | finansovoe-modelirovanie, dlya-sobstvennikov |
| oborotnyj-kapital | Оборотный капитал: запасы, дебиторка, кредиторка | perepodgotovka, finansovyj-menedzhment |
| finansovye-riski-kompanii | Финансовые риски компании и управление ими | mba, msfo |
| pervye-90-dnej-finansovogo-direktora | Первые 90 дней финдиректора в новой компании | mba, povyshenie-kvalifikacii |
| kak-uchitsya-bez-otryva-ot-raboty | Как учиться на финдиректора без отрыва от работы | korotkie, ochno-i-onlajn |

## Очередь
| # | slug | Тема (интент) | Куда ведём | Статус |
|---|------|---------------|-----------|--------|
| 1 | debitorskaya-zadolzhennost | Дебиторская задолженность: как ускорить оплату от клиентов | povyshenie-kvalifikacii | в очереди |
| 2 | yunit-ekonomika | Юнит-экономика для финансового директора | dlya-sobstvennikov | в очереди |
| 3 | finansovyj-kontrolling | Финансовый контроллинг: что это и кто им занимается | perepodgotovka | в очереди |
| 4 | ebitda-prostymi-slovami | EBITDA простыми словами: зачем её считают CFO и банки | msfo | в очереди |
| 5 | kaznachejstvo-kompanii | Казначейство: как устроить согласование платежей | povyshenie-kvalifikacii | в очереди |
| 6 | finansovaya-sluzhba-struktura | Структура финансовой службы в малой и средней компании | mba | в очереди |
| 7 | lizing-ili-kredit | Лизинг или кредит: как финдиректор сравнивает варианты | finansovyj-menedzhment | в очереди |
| 8 | stsenarnoe-planirovanie | Сценарное планирование: три сценария бюджета | finansovoe-modelirovanie | в очереди |

## Правила для каждой статьи
- Формат — как в `data/zhurnal/*.py` (блоки h2/p/ul/ol/tip/table/info/courses/cta), плюс поле `date`.
- 5–8 разделов, 6–10 минут чтения, минимум один список и одна таблица или «На заметку».
- Без непроверяемых цифр (зарплаты, проценты рынка); законы и лимиты — только проверенные.
- Названия документов — точно: «диплом о профессиональной переподготовке», «удостоверение о повышении квалификации», «сертификат школы».
- 2–3 внутренние ссылки [[slug|текст]] на подборки и другие статьи; блок cta в конце.
- title ≤ 70 знаков, desc 70–170 знаков, тема «финансовый директор / CFO» названа явно.
- Перед тем как вписать slug подборки — проверить, что он есть в `LANDINGS` или `RELATED` в `build.py`.

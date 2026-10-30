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
| 1 | debitorskaya-zadolzhennost | Дебиторская задолженность: как ускорить оплату от клиентов | povyshenie-kvalifikacii | опубликовано |
| 2 | yunit-ekonomika | Юнит-экономика для финансового директора | dlya-sobstvennikov | опубликовано |
| 3 | finansovyj-kontrolling | Финансовый контроллинг: что это и кто им занимается | perepodgotovka | черновик |
| 4 | ebitda-prostymi-slovami | EBITDA простыми словами: зачем её считают CFO и банки | msfo | в очереди |
| 5 | kaznachejstvo-kompanii | Казначейство: как устроить согласование платежей | povyshenie-kvalifikacii | в очереди |
| 6 | finansovaya-sluzhba-struktura | Структура финансовой службы в малой и средней компании | mba | в очереди |
| 7 | lizing-ili-kredit | Лизинг или кредит: как финдиректор сравнивает варианты | finansovyj-menedzhment | в очереди |
| 8 | stsenarnoe-planirovanie | Сценарное планирование: три сценария бюджета | finansovoe-modelirovanie | в очереди |
| 9 | platezhnyj-kalendar | Платёжный календарь: как CFO планирует деньги на месяц | finansovoe-modelirovanie | в очереди |
| 10 | upravlencheskaya-otchetnost-dlya-sobstvennika | Какие отчёты финдиректор готовит для собственника | dlya-sobstvennikov | в очереди |
| 11 | finansovye-koefficienty | Финансовые коэффициенты: какие смотрит CFO каждый месяц | finansovyj-analitik | в очереди |
| 12 | kreditnaya-nagruzka | Долговая нагрузка компании: как оценивает финансовый директор | dlya-bankov | в очереди |
| 13 | optimizaciya-zatrat | Сокращение затрат без вреда бизнесу: подход CFO | finansovyj-menedzhment | в очереди |
| 14 | cenoobrazovanie | Ценообразование: как финансовый директор считает цену | dlya-sobstvennikov | в очереди |
| 15 | marzhinalnost-produktov | Маржинальность продуктов: какой товар на самом деле приносит деньги | finansovoe-modelirovanie | в очереди |
| 16 | avtomatizaciya-finansovoj-sluzhby | Автоматизация финансовой службы: с чего начать | povyshenie-kvalifikacii | в очереди |
| 17 | investicionnyj-proekt-ocenka | Оценка инвестиционного проекта: NPV, IRR и срок окупаемости | finansovoe-modelirovanie | в очереди |
| 18 | sobesedovanie-finansovogo-direktora | Собеседование на финансового директора: вопросы и кейсы | perepodgotovka | в очереди |
| 19 | rezyume-finansovogo-direktora | Резюме финансового директора: что писать о достижениях | korotkie | в очереди |
| 20 | finansovyj-direktor-na-autsorse | Финдиректор на аутсорсе: когда бизнесу он нужен | dlya-sobstvennikov | в очереди |
| 21 | kpi-finansovogo-direktora | KPI финансового директора: по каким показателям оценивают CFO | mba | в очереди |
| 22 | due-diligence | Due diligence: что проверяет финансовый директор при сделке | mba | в очереди |
| 23 | valyutnye-riski | Валютный риск: как CFO защищает компанию от курса | msfo | в очереди |
| 24 | rabota-s-bankom | Как финансовый директор договаривается с банком о кредите | dlya-bankov | в очереди |
| 25 | finansovaya-model-startapa | Финансовая модель для привлечения инвестора | finansovoe-modelirovanie | в очереди |
| 26 | soft-skills-cfo | Каким навыкам общения нужно учиться финдиректору | korotkie | в очереди |
| 27 | perehod-iz-analitika-v-cfo | Из финансового аналитика в CFO: карьерный путь | dlya-nachinayushchih | в очереди |
| 28 | upravlenie-zapasami | Неликвидные запасы: как финдиректор находит и сокращает | finansovyj-menedzhment | в очереди |
| 29 | nalogovaya-nagruzka | Налоговая нагрузка: что должен контролировать CFO | dlya-glavbuhov | в очереди |
| 30 | otchet-o-dvizhenii-deneg | Отчёт о движении денежных средств: как читать финдиректору | perepodgotovka | в очереди |

Перед написанием проверить, что тема не повторяет статьи из `data/stati/` и `data/zhurnal/`. Slug подборки сверить с `LANDINGS`/`RELATED` в `build.py`.

## Правила для каждой статьи
- Формат — как в `data/zhurnal/*.py` (блоки h2/p/ul/ol/tip/table/info/courses/cta), плюс поле `date`.
- 5–8 разделов, 6–10 минут чтения, минимум один список и одна таблица или «На заметку».
- Без непроверяемых цифр (зарплаты, проценты рынка); законы и лимиты — только проверенные.
- Названия документов — точно: «диплом о профессиональной переподготовке», «удостоверение о повышении квалификации», «сертификат школы».
- 2–3 внутренние ссылки [[slug|текст]] на подборки и другие статьи; блок cta в конце.
- title ≤ 70 знаков, desc 70–170 знаков, тема «финансовый директор / CFO» названа явно.
- Перед тем как вписать slug подборки — проверить, что он есть в `LANDINGS` или `RELATED` в `build.py`.

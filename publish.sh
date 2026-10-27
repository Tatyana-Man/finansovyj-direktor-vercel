#!/bin/zsh
# Публикация на Vercel (https://finansovyj-direktor.vercel.app): пересборка + загрузка папки deploy/.
# Нужен Vercel CLI (npm i -g vercel) и один раз — вход и привязка: cd deploy && vercel link
# Запуск: zsh publish.sh
set -e
cd "$(dirname "$0")"
[ -f build.py ] && [ -f data/courses.json ] || { echo "ОШИБКА: в папке проекта нет файлов — публикация отменена"; exit 1; }
zsh backup.sh
python3 build.py
python3 build.py --prod
# Защита: не выкладывать почти пустую сборку
PAGES=$(find deploy -name "*.html" | wc -l)
[ "$PAGES" -ge 50 ] || { echo "ОШИБКА: в сборке только $PAGES страниц — публикация отменена"; exit 1; }
# build.py --prod пересоздаёт deploy/, поэтому привязку к проекту Vercel храним в корне и копируем внутрь
[ -d .vercel ] && cp -R .vercel deploy/
(cd deploy && vercel deploy --prod --yes)
[ -d deploy/.vercel ] && [ ! -d .vercel ] && cp -R deploy/.vercel .vercel
echo "Готово: https://finansovyj-direktor.vercel.app"

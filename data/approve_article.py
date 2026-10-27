#!/usr/bin/env python3
"""Одобрить черновик статьи: перенести data/drafts/<slug>.py в data/zhurnal/ с сегодняшней датой и пересобрать сайт.
Запуск: python3 data/approve_article.py <slug>      (публикация на хостинг — потом zsh publish.sh)
Без slug — показать список черновиков."""
import datetime, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
drafts = sorted(p.stem for p in (HERE / "drafts").glob("*.py"))
if len(sys.argv) < 2:
    print("Черновики на проверке:", *drafts or ["— нет"], sep="\n  ")
    sys.exit()
slug = sys.argv[1]
src = HERE / "drafts" / f"{slug}.py"
if not src.exists():
    sys.exit(f"Нет черновика {slug}. Есть: {', '.join(drafts) or 'нет'}")
text = re.sub(r'date="\d{4}-\d{2}-\d{2}"', f'date="{datetime.date.today()}"', src.read_text(encoding="utf-8"))
(HERE / "zhurnal" / f"{slug}.py").write_text(text, encoding="utf-8")
src.unlink()
root = HERE.parent
subprocess.run([sys.executable, "build.py"], cwd=root, check=True)
subprocess.run([sys.executable, "build.py", "--prod"], cwd=root, check=True)
print(f"Статья {slug} одобрена. Чтобы выложить на сайт: zsh publish.sh")

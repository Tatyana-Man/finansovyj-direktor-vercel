"""Статьи раздела /stati/. Каждая раскрывает один интент.

Блоки статьи (sections):
  ("h2", "Заголовок") · ("p", "Абзац") · ("ul", [...]) · ("ol", [...]) · ("tip", "Совет в рамке")
  ("table", [[заголовки], [строка], ...]) · ("info", "ключ инфографики из build.py") · ("cta", [(slug подборки, текст ссылки), ...])
Внутри текста допустимы ссылки вида [[slug|текст]] — превращаются в ссылки на страницы сайта.
Без непроверяемых цифр (зарплаты, «N% работодателей») — только общие и проверяемые утверждения.
"""

ARTICLES = []  # все статьи — отдельными файлами в data/zhurnal/


# Новые статьи хранятся отдельными файлами: data/drafts/<slug>.py — черновики на проверке у владельца
# (видны только в site/ с пометкой «Черновик», на хостинг не попадают), data/zhurnal/<slug>.py — одобренные.
# В каждом файле — переменная ARTICLE = dict(... как выше ..., date="ГГГГ-ММ-ДД"). Одобрение: python3 data/approve_article.py <slug>
import runpy as _rp
from pathlib import Path as _P


def _load(folder):
    return [_rp.run_path(str(f))["ARTICLE"] for f in sorted((_P(__file__).parent / folder).glob("*.py"))]


ARTICLES += sorted(_load("zhurnal"), key=lambda a: a.get("date", ""))
DRAFTS = _load("drafts")


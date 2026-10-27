// Фильтры карточек, легенда диаграммы, сортировка таблиц, фильтры отзывов
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];

// Фильтры карточек в каждой секции: группы-галочки details.ff[data-key] (тип, цена, формат, длительность, школа).
// Внутри группы — «или», между группами — «и».
function filterCards(sec) {
  const groups = $$('details.ff', sec).map(d => [d.dataset.key, $$('input:checked', d).map(x => x.value), d]);
  const quick = $$('.qf[aria-pressed="true"]', sec).map(b => 'q' + b.dataset.q);
  let n = 0;
  $$('.card', sec).forEach(c => {
    const ok = groups.every(([k, vals]) => !vals.length || vals.includes(c.dataset[k])) && quick.every(k => c.dataset[k] === '1');
    c.classList.toggle('hide', !ok); n += ok;
  });
  const cnt = $('.fCount', sec);
  if (cnt) cnt.textContent = `Найдено: ${n}`;
  groups.forEach(([, vals, d]) => $('summary', d).dataset.n = vals.length || '');
  const rs = $('.freset', sec);
  if (rs) rs.hidden = !groups.some(([, vals]) => vals.length) && !quick.length;
}
$$('section').filter(sec => $('.cards', sec) && $('details.ff', sec)).forEach(sec => {
  $$('details.ff input', sec).forEach(el => el.addEventListener('change', () => filterCards(sec)));
  $$('.qf', sec).forEach(b => b.addEventListener('click', () => { b.setAttribute('aria-pressed', b.getAttribute('aria-pressed') !== 'true'); filterCards(sec); }));
  $('.freset', sec)?.addEventListener('click', () => { $$('details.ff input', sec).forEach(x => x.checked = false); $$('.qf', sec).forEach(b => b.setAttribute('aria-pressed', 'false')); filterCards(sec); });
  // открыт только один список за раз; клик вне — закрыть
  $$('details.ff', sec).forEach(d => d.addEventListener('toggle', () => { if (d.open) $$('details.ff', sec).forEach(o => o !== d && (o.open = false)); }));
  filterCards(sec);
});
document.addEventListener('click', ev => { if (!ev.target.closest('details.ff')) $$('details.ff[open]').forEach(d => d.open = false); });

$$('[data-filter-type]').forEach(b => b.addEventListener('click', () => {
  b.classList.toggle('on');
  const on = $$('[data-filter-type].on', b.parentNode).map(x => x.dataset.filterType);
  $$('.dot', b.closest('section')).forEach(d => d.classList.toggle('hide', !on.includes(d.dataset.type)));
}));

$$('table.sortable').forEach(tbl => $$('th', tbl).forEach((th, i) => th.addEventListener('click', () => {
  const dir = th.dataset.dir === 'asc' ? -1 : 1; th.dataset.dir = dir > 0 ? 'asc' : 'desc';
  const val = tr => { const td = tr.children[i]; return td.dataset.v !== undefined ? +td.dataset.v : td.textContent.trim(); };
  const rows = $$('tbody tr', tbl).sort((a, b) => { const x = val(a), y = val(b); return (x > y ? 1 : x < y ? -1 : 0) * dir; });
  rows.forEach(r => tbl.tBodies[0].appendChild(r));
})));

// Отзывы: выбор школы в таблице
let rSchool = '';
function filterReviews() {
  let n = 0;
  $$('#reviews .review').forEach(el => {
    const ok = (!rSchool || el.dataset.school === rSchool);
    el.classList.toggle('hide', !ok); n += ok;
  });
  $$('tr.rsel').forEach(tr => tr.classList.toggle('active', tr.dataset.school === rSchool));
  if ($('#rAll')) $('#rAll').classList.toggle('on', !rSchool);
  if ($('#rTitle')) $('#rTitle').textContent = rSchool ? '— ' + rSchool : '';
  if ($('#rCount')) $('#rCount').textContent = `Отзывов: ${n}`;
}
$$('tr.rsel').forEach(tr => tr.addEventListener('click', ev => {
  if (ev.target.closest('a')) return;
  rSchool = rSchool === tr.dataset.school ? '' : tr.dataset.school;
  filterReviews();
  if (rSchool) $('#rlist').scrollIntoView({behavior: 'smooth'});
}));
$('#rAll')?.addEventListener('click', () => { rSchool = ''; filterReviews(); });
filterReviews();

// Лесенка цен: фильтр по типу и сортировка
$$('[data-ladder-type]').forEach(b => b.addEventListener('click', () => {
  const sec = b.closest('section'), t = b.dataset.ladderType;
  $$('[data-ladder-type]', sec).forEach(x => x.classList.toggle('on', x === b));
  $$('.lr', sec).forEach(r => r.classList.toggle('hide', !!t && r.dataset.type !== t));
}));
$$('[data-ladder-sort]').forEach(b => b.addEventListener('click', () => {
  const asc = b.dataset.ladderSort !== 'asc'; b.dataset.ladderSort = asc ? 'asc' : 'desc';
  b.textContent = asc ? 'Сначала дешёвые ↑' : 'Сначала дорогие ↓';
  const box = $('.lrows', b.closest('section'));
  $$('.lr', box).sort((x, y) => (x.dataset.price - y.dataset.price) * (asc ? 1 : -1)).forEach(r => box.appendChild(r));
}));

// Блок «Финансовый менеджмент»: показать все
$('#fmMore')?.addEventListener('click', e => { e.target.closest('section').classList.add('all'); e.target.remove(); });

// Промокоды: копирование по клику
$$('.pcode').forEach(b => b.addEventListener('click', ev => {
  ev.preventDefault(); ev.stopPropagation();
  const code = b.dataset.code, done = () => { b.classList.add('ok'); setTimeout(() => b.classList.remove('ok'), 2000); };
  if (navigator.clipboard) navigator.clipboard.writeText(code).then(done, done);
  else { const t = document.createElement('textarea'); t.value = code; document.body.appendChild(t); t.select(); document.execCommand('copy'); t.remove(); done(); }
}));

// Отзывы: школа из ссылки вида otzyvy/index.html#school=Название
(() => {
  const m = location.hash.match(/school=([^&]+)/);
  if (!m || !$('#reviews')) return;
  const name = decodeURIComponent(m[1]);
  if (!$$('tr.rsel').some(tr => tr.dataset.school === name)) return;
  rSchool = name; filterReviews();
  setTimeout(() => $('#rlist').scrollIntoView(), 50);
})();



// ---- Сравнение курсов: до 4 программ, выбор хранится между страницами ----
(() => {
  const DATA = window.CMP_DATA || {}, PRE = window.SITE_PRE || '', MAX = 4, KEY = 'fd-compare';
  const bar = $('#cmpBar'), modal = $('#cmpModal');
  if (!bar) return;
  const load = () => { try { return (JSON.parse(localStorage.getItem(KEY)) || []).filter(id => DATA[id]); } catch (e) { return []; } };
  let sel = load();
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(sel)); } catch (e) {} };
  const rub = v => v == null ? 'по запросу' : v.toLocaleString('ru-RU') + ' ₽';
  const esc = s => String(s).replace(/[&<>"]/g, ch => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'})[ch]);
  const plural = (n, a, b, c) => { const m = n % 100, k = n % 10; return m > 10 && m < 20 ? c : k === 1 ? a : k > 1 && k < 5 ? b : c; };

  function sync() {
    $$('.cmp').forEach(b => {
      const on = sel.includes(b.dataset.id);
      b.classList.toggle('on', on); b.setAttribute('aria-pressed', on);
      b.textContent = on ? '✓ В сравнении' : 'Сравнить';
      b.disabled = !on && sel.length >= MAX;
      b.title = b.disabled ? `Можно сравнить не больше ${MAX} программ` : '';
    });
    bar.hidden = !sel.length;
    $('#cmpInfo').textContent = sel.length < 2
      ? `Выбрана 1 программа — добавьте ещё одну`
      : `${sel.length} ${plural(sel.length, 'программа', 'программы', 'программ')} к сравнению`;
    $('#cmpOpen').disabled = sel.length < 2;
    $('#cmpOpen').textContent = `Сравнить (${sel.length})`;
    document.body.classList.toggle('has-cmp', !!sel.length);
  }

  function render() {
    const cs = sel.map(id => [id, DATA[id]]);
    const narrow = innerWidth <= 760, LW = narrow ? 88 : 140;
    // ширина колонки курса: на телефоне фиксированная (листается вбок внутри окна), на компьютере — делим ширину окна
    const CW = narrow ? 156 : Math.max(180, Math.floor((Math.min(innerWidth - 32, 1100) - 36 - LW) / cs.length));
    // лучшее значение: min или max среди известных; подсвечиваем, только если значения различаются
    const best = (get, dir) => {
      const vals = cs.map(([, c]) => get(c)).filter(v => v != null);
      if (vals.length < 2 || new Set(vals).size < 2) return null;
      return dir === 'min' ? Math.min(...vals) : Math.max(...vals);
    };
    const rows = [
      ['Цена', c => (c.op ? `<s>${rub(c.op)}</s> ` : '') + rub(c.p), c => c.p, 'min'],
      ['Платёж в месяц', c => esc(c.mo || '—')],
      ['Цена с промокодом', c => c.pp != null ? `${rub(c.pp)}<small>промокод ${esc(c.pc)}</small>` : (c.pc ? `промокод ${esc(c.pc)}` : '—'), c => c.pp, 'min'],
      ['Срок', c => esc(c.d || '—'), c => c.m, 'min'],
      ['Объём', c => esc(c.h || '—'), c => c.hn, 'max'],
      ['Тип', c => esc(c.type)],
      ['Документ', c => esc(c.doc)],
      ['Формат', c => esc(c.f)],
      ['Рассрочка', c => esc(c.inst)],
      ['Отзывы о школе', c => c.rv ? `<a href="${PRE + c.rvu}">${c.rv} ${plural(c.rv, 'отзыв', 'отзыва', 'отзывов')}</a>` : 'пока нет', c => c.rv || null, 'max'],
    ];
    const head = cs.map(([id, c]) => `<th scope="col"><button class="cmprm" data-id="${id}" type="button" aria-label="Убрать из сравнения">×</button>
      ${c.img ? `<img src="${PRE + c.img}" alt="">` : ''}<span class="cs">${esc(c.s)}</span>
      <a class="ct" href="${PRE + c.u}">${esc(c.t)}</a></th>`).join('');
    const body = rows.map(([label, show, get, dir]) => {
      const b = get ? best(get, dir) : null;
      return `<tr><th scope="row">${label}</th>${cs.map(([, c]) => `<td${b != null && get(c) === b ? ' class="best"' : ''}>${show(c)}</td>`).join('')}</tr>`;
    }).join('');
    const go = `<tr class="cgo"><th scope="row"></th>${cs.map(([, c]) => `<td><a class="btn sm" href="${esc(c.r)}" rel="nofollow noopener" target="_blank">На сайт курса</a></td>`).join('')}</tr>`;
    $('#cmpTable').innerHTML = `<table class="cmpt" style="width:${LW + CW * cs.length}px"><colgroup><col style="width:${LW}px">${cs.map(() => `<col style="width:${CW}px">`).join('')}</colgroup><thead><tr><th></th>${head}</tr></thead><tbody>${body}${go}</tbody></table>`;
  }

  const open = () => { if (sel.length < 2) return; render(); modal.hidden = false; document.body.classList.add('noscroll'); $('#cmpClose').focus(); };
  const close = () => { modal.hidden = true; document.body.classList.remove('noscroll'); };

  document.addEventListener('click', ev => {
    const b = ev.target.closest('.cmp');
    if (b) {
      const id = b.dataset.id;
      sel = sel.includes(id) ? sel.filter(x => x !== id) : sel.length < MAX ? [...sel, id] : sel;
      save(); sync(); return;
    }
    const rm = ev.target.closest('.cmprm');
    if (rm) {
      sel = sel.filter(x => x !== rm.dataset.id); save(); sync();
      sel.length < 2 ? close() : render(); return;
    }
    if (ev.target === modal) close();
  });
  $('#cmpOpen').addEventListener('click', open);
  $('#cmpClose').addEventListener('click', close);
  $('#cmpClear').addEventListener('click', () => { sel = []; save(); sync(); close(); });
  document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && !modal.hidden) close(); });
  window.addEventListener('storage', ev => { if (ev.key === KEY) { sel = load(); sync(); } });
  sync();
})();

// Смежные направления: вкладки
$$('[data-reltab]').forEach(b => b.addEventListener('click', () => {
  const sec = b.closest('section');
  $$('[data-reltab]', sec).forEach(x => x.classList.toggle('on', x === b));
  $$('[data-relpane]', sec).forEach(p => p.hidden = p.dataset.relpane !== b.dataset.reltab);
}));

// «Данные проверены …» — всегда последний понедельник (надпись обновляется сама каждую неделю)
(() => {
  const d = new Date(); d.setHours(0, 0, 0, 0); d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  const p = n => String(n).padStart(2, '0');
  const iso = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`, ru = `${p(d.getDate())}.${p(d.getMonth() + 1)}.${d.getFullYear()}`;
  $$('time.wk').forEach(t => { t.dateTime = iso; t.textContent = ru; });
})();

// Окно про cookie: показываем, пока пользователь не нажал «Принять»
(() => {
  const bar = $('#cookieBar'); if (!bar) return;
  let ok = false; try { ok = localStorage.getItem('fd-cookie') === '1'; } catch (e) {}
  if (ok) return;
  bar.hidden = false; document.body.classList.add('has-cookie');
  $('#cookieOk').addEventListener('click', () => { try { localStorage.setItem('fd-cookie', '1'); } catch (e) {} bar.hidden = true; document.body.classList.remove('has-cookie'); });
})();

// Мобильное меню: кнопка-бургер
(() => {
  const b = $('.burger'), nav = $('#mainnav'); if (!b || !nav) return;
  const set = open => { b.setAttribute('aria-expanded', open); document.body.classList.toggle('nav-open', open); };
  b.addEventListener('click', () => set(b.getAttribute('aria-expanded') !== 'true'));
  $$('a', nav).forEach(a => a.addEventListener('click', () => set(false)));
  document.addEventListener('keydown', e => { if (e.key === 'Escape') set(false); });
})();

// ---- Квиз подбора курса ----
(() => {
  const q = $('#quiz'); if (!q) return;
  const DATA = window.CMP_DATA || {}, PRE = window.SITE_PRE || '';
  const steps = $$('.qstep', q), res = $('.qres', q), bar = $('.qbar i', q), back = $('.qback', q), restart = $('.qrestart', q);
  const esc = s => String(s).replace(/[&<>"]/g, ch => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'})[ch]);
  const rub = v => v == null ? 'цена по запросу' : v.toLocaleString('ru-RU') + ' ₽';
  let i = 0; const ans = {};
  const show = n => { i = n; steps.forEach((s, k) => s.hidden = k !== n); res.hidden = true; bar.style.width = (n / steps.length * 100) + '%';
    back.hidden = n === 0; restart.hidden = true; };
  function score(c) {
    let s = 0; const why = [];
    const g = ans.goal;
    if (g === 'beg') { if (c.aud.includes('beg')) { s += 3; why.push('школа адресует курс новичкам'); } if (c.tc === 'perepodgotovka') s += 1; }
    if (g === 'acc') { if (c.aud.includes('acc')) { s += 3; why.push('подходит главбухам'); } if (c.tc === 'perepodgotovka') s += 1; }
    if (g === 'own') { if (c.aud.includes('own')) { s += 3; why.push('для собственников бизнеса'); } }
    if (g === 'pk') { if (c.tc === 'povyshenie') { s += 3; why.push('повышение квалификации'); } if (c.dk === 'dmba') s += 1; }
    if (ans.doc === 'dip') { if (c.dk === 'ddip' || c.dk === 'dmba') { s += 3; why.push('диплом о переподготовке'); } else s -= 6; }
    if (ans.doc === 'udo') { if (c.dk === 'dudo') { s += 3; why.push('удостоверение'); } else if (c.dk === 'ddip') s += 1; }
    const b = +ans.budget;
    if (b) { if (c.p != null && c.p <= b) { s += 2; why.push('в бюджете'); } else if (c.p == null) s -= 1; else s -= 5; }
    const t = +ans.time;
    if (t && c.m != null) { if ((t === 3 && c.m <= 3) || (t === 6 && c.m > 3 && c.m <= 6)) { s += 2; why.push('подходит по сроку'); } else s -= 1; }
    if (ans.fmt === 'mixed') { if (c.fmt === 'mixed') { s += 2; why.push('есть очные занятия'); } else s -= 2; }
    if (ans.fmt === 'online' && c.fmt === 'online') s += 1;
    if (c.pr < 999) s += Math.max(0.5, 5 - c.pr * 0.25);
    return [s, why];
  }
  function finish() {
    const ranked = Object.entries(DATA).map(([id, c]) => [id, c, ...score(c)]).sort((a, b) => b[2] - a[2] || a[1].pr - b[1].pr || (a[1].p ?? 1e9) - (b[1].p ?? 1e9));
    const seen = new Set(); const top = ranked.filter(r => r[2] > 0 && !seen.has(r[1].s) && seen.add(r[1].s)).slice(0, 3);
    steps.forEach(s => s.hidden = true); bar.style.width = '100%'; back.hidden = true; restart.hidden = false; res.hidden = false;
    if (!top.length) { res.innerHTML = '<p>Точных совпадений нет — попробуйте расширить бюджет или срок. А пока посмотрите <a href="#cards">все программы</a> с фильтрами.</p>'; return; }
    res.innerHTML = '<h3>Вам подойдут</h3><div class="qcards">' + top.map(([id, c, , why]) =>
      `<div class="qcard"><div class="school">${esc(c.s)}</div><a class="qt" href="${PRE + c.u}">${esc(c.t)}</a>
       <div class="qmeta"><b>${rub(c.p)}</b>${c.d ? ' · ' + esc(c.d) : ''}</div>
       <div class="qwhy">${why.map(w => `<span>✓ ${esc(w)}</span>`).join('')}</div>
       <div class="qbtns"><a class="btn sm" href="${esc(c.r)}" rel="nofollow noopener" target="_blank">На сайт курса</a><a class="chip" href="${PRE + c.u}">Подробнее</a></div></div>`).join('') +
      '</div>' + (top.length > 1 ? '<button type="button" class="btn qcmp">Сравнить подобранные курсы</button>' : '');
    const cb = $('.qcmp', res);
    if (cb) cb.addEventListener('click', () => {
      try { localStorage.setItem('fd-compare', JSON.stringify(top.map(r => r[0]))); } catch (e) {}
      window.dispatchEvent(new StorageEvent('storage', {key: 'fd-compare'}));
      setTimeout(() => $('#cmpOpen')?.click(), 50);
    });
  }
  steps.forEach((s, k) => $$('.qopt', s).forEach(b => b.addEventListener('click', () => {
    ans[s.dataset.k] = b.dataset.v; $$('.qopt', s).forEach(x => x.classList.toggle('on', x === b));
    k + 1 < steps.length ? show(k + 1) : finish();
  })));
  back.addEventListener('click', () => show(Math.max(0, i - 1)));
  restart.addEventListener('click', () => { Object.keys(ans).forEach(k => delete ans[k]); $$('.qopt', q).forEach(x => x.classList.remove('on')); show(0); });
})();

// Лесенка: сортировка и кнопка «На сайт»
$$('[data-lsort]').forEach(b => b.addEventListener('click', () => {
  const sec = b.closest('section'), box = $('.lrows', sec), k = b.dataset.lsort;
  $$('[data-lsort]', sec).forEach(x => x.classList.toggle('on', x === b));
  const num = (r, a) => r.dataset[a] === '' ? null : +r.dataset[a];
  const key = { def: r => +r.dataset.i, pa: r => num(r, 'price'), pd: r => num(r, 'price'), ma: r => num(r, 'months'), md: r => num(r, 'months') }[k];
  const dir = (k === 'pd' || k === 'md') ? -1 : 1;
  $$('.lr', box).sort((x, y) => { const a = key(x), c = key(y); if (a == null) return c == null ? 0 : 1; if (c == null) return -1; return (a - c) * dir; }).forEach(r => box.appendChild(r));
}));
$$('.lgo').forEach(b => { const go = ev => { ev.preventDefault(); ev.stopPropagation(); window.open(b.dataset.href, '_blank', 'noopener'); };
  b.addEventListener('click', go); b.addEventListener('keydown', ev => { if (ev.key === 'Enter' || ev.key === ' ') go(ev); }); });

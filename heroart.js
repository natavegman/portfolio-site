/* Живой круг в шапке vegman.dev. Три варианта:
   A network - узлы из реальных проектов, по связям бегут импульсы, курсор подсвечивает соседей;
   B motif   - спокойный мотив как на обложках блога, импульс идет по линии;
   C order   - "хаос -> система": частицы бродят и выстраиваются в потоки при наведении.
   Цвета берутся из CSS-переменных темы и перечитываются при переключении. */
(function () {
  const art = document.querySelector('.hero-art');
  const cv = document.getElementById('heroCanvas');
  if (!art || !cv) return;
  const ctx = cv.getContext('2d');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let W = 0, R = 0, dpr = 1, C = {}, mouse = { x: -1e4, y: -1e4, in: false }, running = true, t0 = performance.now();
  let variant = 'C';

  function readColors() {
    const s = getComputedStyle(document.documentElement);
    const v = n => s.getPropertyValue(n).trim();
    const light = document.documentElement.dataset.theme === 'light';
    C = { light, ink: v('--text'), muted: v('--muted'), faint: v('--faint'), accent: v('--accent'),
          accent2: v('--accent-2'), disc: light ? '#e2ddd2' : '#0c0a08' };
  }
  function resize() {
    const r = cv.getBoundingClientRect();
    dpr = Math.min(devicePixelRatio || 1, 2);
    W = r.width; R = W / 2;
    cv.width = W * dpr; cv.height = W * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    layout();
  }
  function alpha(hex, a) {
    if (hex.startsWith('#')) {
      const n = parseInt(hex.slice(1), 16);
      return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`;
    }
    return hex;
  }
  // детерминированный шум, чтобы композиция не прыгала между загрузками
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;

  /* ── A: сеть ── */
  const LABELS = ['Bnovo PMS', 'GigaChat', 'ChromaDB', 'Telegram', 'PostgreSQL', 'Notion', 'n8n', 'FastAPI', 'Bitrix24', 'RAG', 'Claude', 'SpeechKit'];
  let nodes = [], edges = [], pulses = [];
  function layoutA() {
    seed = 11; nodes = [];
    let guard = 0;
    while (nodes.length < LABELS.length && guard++ < 4000) {
      const a = rnd() * Math.PI * 2, d = Math.sqrt(rnd()) * R * .74;
      const x = R + Math.cos(a) * d, y = R + Math.sin(a) * d;
      if (nodes.every(n => Math.hypot(n.bx - x, n.by - y) > R * .27))
        nodes.push({ bx: x, by: y, x, y, ph: rnd() * 6.28, label: LABELS[nodes.length], glow: 0 });
    }
    edges = [];
    nodes.forEach((n, i) => {
      nodes.map((m, j) => ({ j, d: Math.hypot(n.bx - m.bx, n.by - m.by) })).filter(o => o.j !== i)
        .sort((p, q) => p.d - q.d).slice(0, 2)
        .forEach(o => { if (!edges.some(e => (e[0] === o.j && e[1] === i) || (e[0] === i && e[1] === o.j))) edges.push([i, o.j]); });
    });
    pulses = [];
  }
  function drawA(t) {
    nodes.forEach(n => {
      n.x = n.bx + Math.sin(t * .0004 + n.ph) * R * .025;
      n.y = n.by + Math.cos(t * .00033 + n.ph) * R * .025;
      const near = Math.max(0, 1 - Math.hypot(mouse.x - n.x, mouse.y - n.y) / (R * .45));
      n.glow += (near - n.glow) * .12;
    });
    if (!reduce && Math.random() < .045 && edges.length) {
      const e = edges[Math.floor(Math.random() * edges.length)];
      pulses.push({ e, t: 0, dir: Math.random() < .5, sp: .006 + Math.random() * .006 });
    }
    ctx.lineWidth = 1;
    edges.forEach(([i, j]) => {
      const a = nodes[i], b = nodes[j], g = Math.max(a.glow, b.glow);
      ctx.strokeStyle = g > .05 ? alpha(C.accent, .25 + g * .6) : alpha(C.muted, C.light ? .45 : .35);
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    });
    pulses = pulses.filter(p => (p.t += p.sp) < 1);
    pulses.forEach(p => {
      const [i, j] = p.dir ? p.e : [p.e[1], p.e[0]], a = nodes[i], b = nodes[j];
      const x = a.x + (b.x - a.x) * p.t, y = a.y + (b.y - a.y) * p.t;
      const tx = a.x + (b.x - a.x) * Math.max(0, p.t - .12), ty = a.y + (b.y - a.y) * Math.max(0, p.t - .12);
      const gr = ctx.createLinearGradient(tx, ty, x, y);
      gr.addColorStop(0, alpha(C.accent, 0)); gr.addColorStop(1, alpha(C.accent, .95));
      ctx.strokeStyle = gr; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(tx, ty); ctx.lineTo(x, y); ctx.stroke();
      if (!C.light) { ctx.shadowColor = C.accent; ctx.shadowBlur = 10; }
      ctx.fillStyle = C.accent; ctx.beginPath(); ctx.arc(x, y, 2.2, 0, 6.28); ctx.fill(); ctx.shadowBlur = 0;
    });
    ctx.font = `500 ${Math.max(10, R * .052)}px "JetBrains Mono", monospace`; ctx.textAlign = 'center';
    nodes.forEach(n => {
      const s = R * .045 + n.glow * R * .02;
      if (n.glow > .05 && !C.light) { ctx.shadowColor = C.accent; ctx.shadowBlur = 18 * n.glow; }
      ctx.fillStyle = C.disc; ctx.strokeStyle = n.glow > .05 ? C.accent : alpha(C.ink, C.light ? .7 : .5);
      ctx.lineWidth = 1.2 + n.glow;
      roundRect(n.x - s, n.y - s, s * 2, s * 2, s * .35); ctx.fill(); ctx.stroke(); ctx.shadowBlur = 0;
      ctx.fillStyle = n.glow > .05 ? C.accent : alpha(C.ink, .45 + (C.light ? .15 : 0));
      ctx.beginPath(); ctx.arc(n.x, n.y, 1.8 + n.glow, 0, 6.28); ctx.fill();
      ctx.fillStyle = n.glow > .05 ? (C.light ? C.accent2 : C.accent2) : alpha(C.muted, .9);
      ctx.fillText(n.label, n.x, n.y + s + R * .075);
    });
  }

  /* ── B: спокойный мотив ── */
  function drawB(t) {
    const y = R * 1.05, xs = [.17, .39, .61, .83].map(k => k * W), s = R * .1;
    ctx.lineWidth = 1.2;
    ctx.setLineDash([3, 6]); ctx.strokeStyle = alpha(C.muted, .6);
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(xs[0] - s, y); ctx.stroke(); ctx.setLineDash([]);
    ctx.strokeStyle = alpha(C.ink, C.light ? .75 : .45);
    for (let i = 0; i < 3; i++) {
      ctx.beginPath(); ctx.moveTo(xs[i] + s, y);
      ctx.bezierCurveTo(xs[i] + s + 20, y - R * .26, xs[i + 1] - s - 20, y - R * .26, xs[i + 1] - s, y); ctx.stroke();
    }
    const k = reduce ? .7 : (t * .00025) % 1, seg = Math.min(2, Math.floor(k * 3)), lt = k * 3 - seg;
    const bx = (u) => { const a = xs[seg] + s, b = xs[seg + 1] - s, c1 = a + 20, c2 = b - 20;
      const m = 1 - u; return [m*m*m*a + 3*m*m*u*c1 + 3*m*u*u*c2 + u*u*u*b, m*m*m*y + 3*m*m*u*(y - R*.26) + 3*m*u*u*(y - R*.26) + u*u*u*y]; };
    const [px, py] = bx(lt);
    if (!C.light) { ctx.shadowColor = C.accent; ctx.shadowBlur = 14; }
    ctx.fillStyle = C.accent; ctx.beginPath(); ctx.arc(px, py, 3, 0, 6.28); ctx.fill(); ctx.shadowBlur = 0;
    xs.forEach((x, i) => {
      const on = i === 3, ss = on ? s * 1.15 : s;
      if (on && !C.light) { ctx.shadowColor = C.accent; ctx.shadowBlur = 20; }
      ctx.fillStyle = C.disc; ctx.strokeStyle = on ? C.accent : alpha(C.ink, C.light ? .6 : .4); ctx.lineWidth = on ? 1.8 : 1.2;
      roundRect(x - ss, y - ss, ss * 2, ss * 2, ss * .3); ctx.fill(); ctx.stroke(); ctx.shadowBlur = 0;
      ctx.fillStyle = on ? C.accent : alpha(C.muted, .8); ctx.beginPath(); ctx.arc(x, y, on ? 3 : 2, 0, 6.28); ctx.fill();
    });
  }

  /* ── C: хаос -> система ── */
  let parts = [], order = 0;
  const LANES = 5;
  function layoutC() {
    seed = 23; parts = [];
    for (let i = 0; i < 170; i++) parts.push({ lane: i % LANES, u: rnd(), ph: rnd() * 6.28, sp: .5 + rnd(), x: R, y: R, r: .8 + rnd() * 1.4 });
  }
  function drawC(t) {
    const target = reduce ? 1 : (mouse.in ? 1 : (Math.sin(t * .00045) > .55 ? 1 : 0));
    order += (target - order) * .035;
    const e = order * order * (3 - 2 * order);
    const laneY = l => R + (l - (LANES - 1) / 2) * R * .26;
    // линии потоков проявляются вместе с порядком
    ctx.lineWidth = 1;
    for (let l = 0; l < LANES; l++) {
      ctx.strokeStyle = alpha(C.muted, .45 * e);
      ctx.beginPath(); ctx.moveTo(R * .05, laneY(l)); ctx.lineTo(W - R * .05, laneY(l)); ctx.stroke();
    }
    parts.forEach(p => {
      p.u = (p.u + .0009 * p.sp * (reduce ? 0 : 1)) % 1;
      const cx = R + Math.sin(t * .0003 * p.sp + p.ph) * R * .78 * Math.cos(p.ph * 3 + t * .00011);
      const cy = R + Math.cos(t * .00027 * p.sp + p.ph * 2) * R * .78 * Math.sin(p.ph + t * .00013);
      const ox = W * .06 + p.u * W * .88, oy = laneY(p.lane);
      p.x = cx + (ox - cx) * e; p.y = cy + (oy - cy) * e;
      const hot = e > .6 && p.lane === 2;
      ctx.fillStyle = hot ? C.accent : alpha(e > .5 ? C.ink : C.muted, C.light ? .8 : .7);
      if (hot && !C.light) { ctx.shadowColor = C.accent; ctx.shadowBlur = 8; }
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r * (hot ? 1.3 : 1), 0, 6.28); ctx.fill(); ctx.shadowBlur = 0;
    });
    // узлы на потоках: система проявилась
    if (e > .3) for (let l = 0; l < LANES; l++) [.3, .7].forEach(k => {
      const x = W * k, y = laneY(l), s = R * .035;
      ctx.globalAlpha = (e - .3) / .7;
      ctx.fillStyle = C.disc; ctx.strokeStyle = l === 2 ? C.accent : alpha(C.ink, .55); ctx.lineWidth = 1.2;
      roundRect(x - s, y - s, s * 2, s * 2, s * .3); ctx.fill(); ctx.stroke(); ctx.globalAlpha = 1;
    });
  }

  function roundRect(x, y, w, h, r) {
    ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  }
  function layout() { layoutA(); layoutC(); }
  function frame(now) {
    const t = now - t0;
    ctx.clearRect(0, 0, W, W);
    ctx.save(); ctx.beginPath(); ctx.arc(R, R, R - .5, 0, 6.28); ctx.clip();
    ctx.fillStyle = C.disc; ctx.fillRect(0, 0, W, W);
    ({ A: drawA, B: drawB, C: drawC })[variant](t);
    ctx.restore();
    ctx.strokeStyle = alpha(C.ink, C.light ? .5 : .25); ctx.lineWidth = 1;
    ctx.beginPath(); ctx.arc(R, R, R - .5, 0, 6.28); ctx.stroke();
    if (running && !reduce) requestAnimationFrame(frame);
  }
  function start() { if (reduce) { frame(performance.now()); return; } requestAnimationFrame(frame); }

  addEventListener('pointermove', e => {
    const r = cv.getBoundingClientRect();
    mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top;
    mouse.in = Math.hypot(mouse.x - R, mouse.y - R) < R * 1.15;
  }, { passive: true });
  addEventListener('resize', () => { resize(); if (reduce) frame(performance.now()); });
  new MutationObserver(() => { readColors(); if (reduce) frame(performance.now()); })
    .observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  // вне экрана не рисуем
  new IntersectionObserver(([en]) => { const was = running; running = en.isIntersecting; if (running && !was) start(); })
    .observe(cv);
  window.setHeroVariant = v => { variant = v; try { localStorage.setItem('heroVariant', v); } catch (e) {} if (reduce) frame(performance.now());
    document.querySelectorAll('[data-hv]').forEach(b => b.classList.toggle('on', b.dataset.hv === v)); };

  readColors(); resize(); start();
  document.querySelectorAll('[data-hv]').forEach(b => b.classList.toggle('on', b.dataset.hv === variant));
})();

/* Свет за курсором на карточках: координаты в CSS-переменные, рисует CSS */
document.querySelectorAll('.project-card, .featured-card, .skill-group, .about-aside').forEach(el => {
  el.addEventListener('pointermove', e => {
    const r = el.getBoundingClientRect();
    el.style.setProperty('--mx', (e.clientX - r.left) + 'px');
    el.style.setProperty('--my', (e.clientY - r.top) + 'px');
  });
  el.addEventListener('pointerleave', () => { el.style.setProperty('--mx', '-999px'); el.style.setProperty('--my', '-999px'); });
});

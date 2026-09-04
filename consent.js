/*
 * consent.js — cookie consent for vegman.dev
 * Vanilla JS, no dependencies. Bilingual RU/EN.
 *
 * REQUIRED: put this snippet in <head>, BEFORE any analytics or ad tag,
 * so Consent Mode defaults exist before a tag can fire:
 *
 *   <script>
 *     window.dataLayer = window.dataLayer || [];
 *     function gtag(){dataLayer.push(arguments);}
 *     gtag('consent', 'default', {
 *       ad_storage: 'denied', ad_user_data: 'denied',
 *       ad_personalization: 'denied', analytics_storage: 'denied',
 *       functionality_storage: 'granted', security_storage: 'granted',
 *       wait_for_update: 500
 *     });
 *   </script>
 *
 * Then load this file anywhere: <script src="/consent.js" defer></script>
 *
 * Public API:
 *   window.cookieConsent.open()            — reopen the panel (footer link)
 *   window.cookieConsent.get()             — current state or null
 *   window.cookieConsent.setLanguage('en') — follow the site's RU/EN switch
 *   document.addEventListener('cookieconsent', e => e.detail.analytics)
 */
(function () {
  'use strict';

  var STORAGE_KEY = 'vd_consent';
  var VERSION = 1;
  var MAX_AGE_DAYS = 180;
  var PRIVACY_URL = '/privacy/';

  var TEXT = {
    ru: {
      title: 'Куки на этом сайте',
      body: 'Необходимые куки нужны для работы сайта. Остальные — аналитика и реклама — включаются только с вашего согласия.',
      accept: 'Принять все',
      reject: 'Только необходимые',
      customize: 'Настроить',
      save: 'Сохранить выбор',
      policy: 'Политика конфиденциальности',
      close: 'Закрыть',
      groups: [
        { key: 'necessary', name: 'Необходимые', desc: 'Работа сайта и выбор языка. Отключить нельзя.' },
        { key: 'analytics', name: 'Аналитика', desc: 'Обезличенная статистика посещений — какие статьи читают.' },
        { key: 'ads', name: 'Реклама', desc: 'Показ и подбор рекламных объявлений.' }
      ]
    },
    en: {
      title: 'Cookies on this site',
      body: 'Necessary cookies keep the site working. Analytics and advertising cookies run only if you allow them.',
      accept: 'Accept all',
      reject: 'Necessary only',
      customize: 'Choose',
      save: 'Save choice',
      policy: 'Privacy policy',
      close: 'Close',
      groups: [
        { key: 'necessary', name: 'Necessary', desc: 'Site functionality and language choice. Always on.' },
        { key: 'analytics', name: 'Analytics', desc: 'Anonymous visit statistics — which posts get read.' },
        { key: 'ads', name: 'Advertising', desc: 'Serving and selecting ads.' }
      ]
    }
  };

  var CSS = [
    '.cc{position:fixed;left:1.5rem;bottom:1.5rem;z-index:2147483000;width:min(26rem,calc(100vw - 3rem));',
    'background:var(--cc-surface,#12151a);color:var(--cc-text,#e8eaed);',
    'border:1px solid var(--cc-line,rgba(255,255,255,.14));border-radius:.5rem;',
    'box-shadow:0 1.5rem 3rem rgba(0,0,0,.35);padding:1.25rem 1.25rem 1rem;',
    'font:400 .875rem/1.55 var(--cc-font,system-ui,-apple-system,"Segoe UI",sans-serif);',
    'opacity:0;transform:translateY(.5rem);transition:opacity .18s ease,transform .18s ease}',
    '.cc[data-open="1"]{opacity:1;transform:none}',
    '.cc h2{margin:0 0 .4rem;font-size:.9375rem;font-weight:600;letter-spacing:-.01em}',
    '.cc p{margin:0 0 .9rem;color:var(--cc-muted,#a9b0bb)}',
    '.cc a{color:inherit;text-underline-offset:.2em}',
    '.cc-actions{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center}',
    '.cc-btn{font:inherit;cursor:pointer;border-radius:.3125rem;padding:.5rem .85rem;border:1px solid transparent}',
    '.cc-btn:focus-visible{outline:2px solid var(--cc-accent,#5b9dff);outline-offset:2px}',
    '.cc-primary{background:var(--cc-accent,#5b9dff);color:var(--cc-accent-text,#0b0f14);font-weight:550}',
    '.cc-secondary{background:transparent;color:inherit;border-color:var(--cc-line,rgba(255,255,255,.22))}',
    '.cc-link{background:none;color:var(--cc-muted,#a9b0bb);padding:.5rem .25rem;text-decoration:underline;',
    'text-underline-offset:.2em;margin-left:auto}',
    '.cc-groups{margin:.25rem 0 1rem;border-top:1px solid var(--cc-line,rgba(255,255,255,.12))}',
    '.cc-group{display:flex;gap:.75rem;padding:.8rem 0;border-bottom:1px solid var(--cc-line,rgba(255,255,255,.08))}',
    '.cc-group label{font-weight:550;display:block;margin-bottom:.15rem}',
    '.cc-group span{color:var(--cc-muted,#a9b0bb);font-size:.8125rem;line-height:1.45;display:block}',
    '.cc-group input{margin:.25rem 0 0;width:1rem;height:1rem;accent-color:var(--cc-accent,#5b9dff);flex:0 0 auto}',
    '.cc-group input:disabled{opacity:.5}',
    '.cc[hidden]{display:none}',
    '@media (max-width:32rem){.cc{left:.75rem;right:.75rem;bottom:.75rem;width:auto}}',
    '@media (prefers-reduced-motion:reduce){.cc{transition:none}}',
    '@media (prefers-color-scheme:light){.cc{--cc-surface:#fff;--cc-text:#14181f;--cc-muted:#5a6472;',
    '--cc-line:rgba(0,0,0,.14);--cc-accent-text:#fff}}'
  ].join('');

  var root = null, state = null, lang = 'ru', expanded = false, lastFocus = null;

  function read() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      var s = JSON.parse(raw);
      if (s.v !== VERSION) return null;
      if (Date.now() - s.ts > MAX_AGE_DAYS * 864e5) return null;
      return s;
    } catch (e) { return null; }
  }

  function write(analytics, ads) {
    state = { v: VERSION, ts: Date.now(), analytics: !!analytics, ads: !!ads };
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (e) {}
    apply();
  }

  function apply() {
    if (!state) return;
    var g = window.gtag;
    if (typeof g === 'function') {
      g('consent', 'update', {
        analytics_storage: state.analytics ? 'granted' : 'denied',
        ad_storage: state.ads ? 'granted' : 'denied',
        ad_user_data: state.ads ? 'granted' : 'denied',
        ad_personalization: state.ads ? 'granted' : 'denied'
      });
    }
    document.dispatchEvent(new CustomEvent('cookieconsent', { detail: state }));
  }

  function detectLang() {
    var html = (document.documentElement.lang || '').toLowerCase();
    if (html.indexOf('en') === 0) return 'en';
    if (html.indexOf('ru') === 0) return 'ru';
    try {
      var saved = localStorage.getItem('lang') || localStorage.getItem('language');
      if (saved) return saved.toLowerCase().indexOf('en') === 0 ? 'en' : 'ru';
    } catch (e) {}
    return (navigator.language || 'ru').toLowerCase().indexOf('ru') === 0 ? 'ru' : 'en';
  }

  function el(tag, attrs, text) {
    var n = document.createElement(tag);
    for (var k in attrs) if (attrs[k] != null) n.setAttribute(k, attrs[k]);
    if (text != null) n.textContent = text;
    return n;
  }

  function render() {
    var t = TEXT[lang];
    root.textContent = '';
    root.appendChild(el('h2', { id: 'cc-title' }, t.title));

    var p = el('p');
    p.appendChild(document.createTextNode(t.body + ' '));
    p.appendChild(el('a', { href: PRIVACY_URL }, t.policy));
    root.appendChild(p);

    if (expanded) {
      var groups = el('div', { class: 'cc-groups' });
      t.groups.forEach(function (g) {
        var row = el('div', { class: 'cc-group' });
        var box = el('input', {
          type: 'checkbox', id: 'cc-' + g.key,
          checked: g.key === 'necessary' || (state && state[g.key]) ? 'checked' : null,
          disabled: g.key === 'necessary' ? 'disabled' : null
        });
        var wrap = el('div');
        wrap.appendChild(el('label', { for: 'cc-' + g.key }, g.name));
        wrap.appendChild(el('span', null, g.desc));
        row.appendChild(box);
        row.appendChild(wrap);
        groups.appendChild(row);
      });
      root.appendChild(groups);
    }

    var actions = el('div', { class: 'cc-actions' });

    if (expanded) {
      actions.appendChild(button('cc-btn cc-primary', t.save, function () {
        write(root.querySelector('#cc-analytics').checked, root.querySelector('#cc-ads').checked);
        close();
      }));
      actions.appendChild(button('cc-btn cc-secondary', t.accept, function () {
        write(true, true); close();
      }));
    } else {
      actions.appendChild(button('cc-btn cc-primary', t.accept, function () {
        write(true, true); close();
      }));
      actions.appendChild(button('cc-btn cc-secondary', t.reject, function () {
        write(false, false); close();
      }));
      actions.appendChild(button('cc-btn cc-link', t.customize, function () {
        expanded = true; render();
        var first = root.querySelector('#cc-analytics');
        if (first) first.focus();
      }));
    }

    root.appendChild(actions);
  }

  function button(cls, label, onClick) {
    var b = el('button', { type: 'button', class: cls }, label);
    b.addEventListener('click', onClick);
    return b;
  }

  function open() {
    if (!root) return;
    lastFocus = document.activeElement;
    expanded = !!state;
    render();
    root.hidden = false;
    requestAnimationFrame(function () { root.setAttribute('data-open', '1'); });
    var focusable = root.querySelector('button, input:not([disabled]), a');
    if (focusable) focusable.focus();
  }

  function close() {
    if (!root) return;
    root.removeAttribute('data-open');
    var done = function () { root.hidden = true; };
    setTimeout(done, 200);
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  function init() {
    var style = el('style');
    style.textContent = CSS;
    document.head.appendChild(style);

    root = el('div', {
      class: 'cc', role: 'dialog', 'aria-labelledby': 'cc-title',
      'aria-live': 'polite', hidden: 'hidden'
    });
    document.body.appendChild(root);

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !root.hidden) close();
    });

    lang = detectLang();
    state = read();

    if (state) apply(); else open();

    window.cookieConsent = {
      open: function () { open(); },
      get: function () { return state; },
      setLanguage: function (code) {
        lang = String(code).toLowerCase().indexOf('en') === 0 ? 'en' : 'ru';
        if (!root.hidden) render();
      }
    };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

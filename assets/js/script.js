// SWIFTYALATINO - JS mínimo, sin dependencias, para no afectar Core Web Vitals
document.addEventListener('DOMContentLoaded', function () {
  var yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  var header = document.querySelector('.site-header');
  var navBtn = document.querySelector('.nav-toggle');
  if (header && navBtn) {
    function setNav(open) {
      header.classList.toggle('nav-open', open);
      navBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    }
    navBtn.addEventListener('click', function () {
      setNav(!header.classList.contains('nav-open'));
    });
    header.querySelectorAll('.main-nav a').forEach(function (link) {
      link.addEventListener('click', function () { setNav(false); });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setNav(false);
    });
  }

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var revealNodes = document.querySelectorAll('.reveal');
  if (!reduceMotion && revealNodes.length && 'IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        entry.target.classList.remove('reveal-pending');
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.14, rootMargin: '0px 0px -8% 0px' });
    var viewHeight = window.innerHeight || 800;
    revealNodes.forEach(function (el) {
      var rect = el.getBoundingClientRect();
      if (rect.top < viewHeight * 0.92) {
        el.classList.add('is-in');
      } else {
        el.classList.add('reveal-pending');
        observer.observe(el);
      }
    });
  }

  // Tracking simple de clics en botones de WhatsApp (opcional, útil para medir conversiones)
  document.querySelectorAll('a[href*="wa.me"]').forEach(function (link) {
    link.addEventListener('click', function () {
      if (window.gtag) {
        window.gtag('event', 'click_whatsapp', {
          event_category: 'engagement',
          event_label: link.textContent.trim()
        });
      }
    });
  });

  /* ---------- Modo claro / oscuro ---------- */
  var themeBtn = document.getElementById('theme-toggle');
  function applyThemeIcon() {
    if (!themeBtn) return;
    var isLight = document.documentElement.classList.contains('light-theme');
    themeBtn.textContent = isLight ? '☀️' : '🌙';
  }
  applyThemeIcon();
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var html = document.documentElement;
      html.classList.toggle('light-theme');
      try {
        localStorage.setItem('swifty-theme', html.classList.contains('light-theme') ? 'light' : 'dark');
      } catch (e) {}
      applyThemeIcon();
    });
  }

  /* ---------- Conversor de moneda (referencial) ---------- */
  // Tasas aproximadas respecto al MXN. Actualizar periódicamente según tipo de cambio real.
  var RATE_FROM_MXN = {
    MXN: 1,
    USD: 0.0625,   // 1 MXN ≈ 0.0625 USD  (≈16 MXN por USD)
    CAD: 0.0625 * 1.36,
    EUR: 0.0625 * 0.92,
    COP: 0.0625 * 3900,
    PEN: 0.0625 * 3.7
  };
  var LOCALE_BY_CURRENCY = {
    MXN: 'es-MX', USD: 'en-US', CAD: 'en-CA', EUR: 'es-ES', COP: 'es-CO', PEN: 'es-PE'
  };

  function formatPrice(value, currency) {
    try {
      return new Intl.NumberFormat(LOCALE_BY_CURRENCY[currency] || 'es-MX', {
        style: 'currency',
        currency: currency,
        maximumFractionDigits: 0
      }).format(value);
    } catch (e) {
      return '$' + Math.round(value) + ' ' + currency;
    }
  }

  function updatePrices(currency) {
    document.querySelectorAll('.price[data-mxn]').forEach(function (el) {
      var mxn = parseFloat(el.getAttribute('data-mxn'));
      var exactUsd = el.getAttribute('data-usd');
      var value;

      if (currency === 'MXN') {
        // El precio en pesos publicado en la página es la fuente de verdad.
        value = mxn;
      } else if (currency === 'USD' && exactUsd) {
        value = parseFloat(exactUsd);
      } else if (exactUsd) {
        // Otras monedas salen del USD oficial cuando existe.
        var usdValue = parseFloat(exactUsd);
        value = usdValue * (RATE_FROM_MXN[currency] / RATE_FROM_MXN.USD);
      } else {
        value = mxn * RATE_FROM_MXN[currency];
      }
      el.textContent = formatPrice(value, currency) + (currency === 'MXN' ? '' : '*');
    });
  }

  function detectDefaultCurrency() {
    try {
      var saved = localStorage.getItem('swifty-currency');
      if (saved) return saved;
      var lang = (navigator.language || navigator.userLanguage || '').toLowerCase();
      if (lang.indexOf('pe') !== -1) return 'PEN';       // es-PE
      if (lang.indexOf('co') !== -1) return 'COP';       // es-CO
      if (lang.indexOf('es-es') !== -1) return 'EUR';    // es-ES
      if (lang.indexOf('ca') !== -1 && lang.indexOf('es') === -1) return 'CAD'; // en-CA
      if (lang.indexOf('us') !== -1 || lang === 'en-us') return 'USD';
      if (lang.indexOf('mx') !== -1) return 'MXN';
      return 'MXN';
    } catch (e) {
      return 'MXN';
    }
  }

  var currencySelect = document.getElementById('currency-select');
  if (currencySelect) {
    var defaultCurrency = detectDefaultCurrency();
    currencySelect.value = defaultCurrency;
    updatePrices(defaultCurrency);

    currencySelect.addEventListener('change', function () {
      var currency = currencySelect.value;
      try { localStorage.setItem('swifty-currency', currency); } catch (e) {}
      updatePrices(currency);
    });
  }
});

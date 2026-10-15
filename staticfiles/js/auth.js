/* Tower of Keys — behaviour for the sign in / sign up pages */
(function () {
  'use strict';

  var stage = document.querySelector('.auth-stage');
  if (!stage) return;

  var form = stage.querySelector('[data-auth-form]');
  var windowsEl = stage.querySelector('.tower-windows');
  var skyline = stage.querySelector('.skyline');
  var door = stage.querySelector('.tower-door');
  var card = stage.querySelector('.auth-card');
  var floorCount = stage.querySelector('[data-floor-count]');
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- build the tower ------------------------------------------------ */
  var TOTAL = 60;
  var wins = [];
  for (var i = 0; i < TOTAL; i++) {
    var w = document.createElement('span');
    w.className = 'win' + (Math.random() < 0.3 ? ' cool' : '') + (Math.random() < 0.22 ? ' tw' : '');
    w.style.setProperty('--tw', (3 + Math.random() * 5).toFixed(1) + 's');
    w.style.animationDelay = (-Math.random() * 6).toFixed(1) + 's';
    wins.push(w);
  }
  var order = wins.map(function (_, idx) { return idx; });
  for (var j = order.length - 1; j > 0; j--) {
    var k = Math.floor(Math.random() * (j + 1));
    var t = order[j]; order[j] = order[k]; order[k] = t;
  }
  wins.forEach(function (w) { windowsEl.appendChild(w); });

  function lightUp(count) {
    var lit = Math.max(0, Math.min(TOTAL, count));
    order.forEach(function (winIndex, pos) {
      wins[winIndex].classList.toggle('on', pos < lit);
    });
    if (floorCount) floorCount.textContent = String(Math.ceil(lit / 6));
  }

  /* ---- build the distant skyline ------------------------------------- */
  if (skyline) {
    var specs = [[34, 120], [48, 190], [30, 150], [56, 240], [40, 170], [52, 220], [36, 140], [46, 200], [32, 110]];
    specs.forEach(function (s, n) {
      var b = document.createElement('div');
      b.className = 'bldg';
      b.style.setProperty('--w', s[0] + 'px');
      b.style.setProperty('--h', s[1] + 'px');
      b.style.setProperty('--f', (4 + (n % 5) * 1.7) + 's');
      skyline.appendChild(b);
    });
  }

  /* ---- progress → lit windows ---------------------------------------- */
  var tracked = form ? Array.prototype.slice.call(form.querySelectorAll('input:not([type=hidden])')) : [];
  function filledRatio() {
    if (!tracked.length) return 0;
    var done = tracked.filter(function (el) {
      return el.type === 'checkbox' ? el.checked : el.value.trim() !== '';
    }).length;
    return done / tracked.length;
  }
  function refresh() { lightUp(10 + Math.round(filledRatio() * (TOTAL - 10))); }

  /* ---- password strength → beacon colour ----------------------------- */
  var BEACON = ['#2eff9a', '#ff4d4d', '#ffb020', '#d8e84a', '#2eff9a'];
  var LABELS = ['', 'Too weak — add more characters', 'Getting there', 'Strong', 'Fortress-grade'];
  var pw = form && form.querySelector('[data-strength]');
  var meter = form && form.querySelector('.meter');
  var meterLabel = form && form.querySelector('.meter-label');

  function score(v) {
    if (!v) return 0;
    var s = 0;
    if (v.length >= 8) s++;
    if (v.length >= 12) s++;
    if (/[a-z]/.test(v) && /[A-Z]/.test(v)) s++;
    if (/\d/.test(v) && /[^A-Za-z0-9]/.test(v)) s++;
    return Math.max(1, Math.min(4, s));
  }
  function onStrength() {
    var s = score(pw.value);
    stage.style.setProperty('--beacon', BEACON[s]);
    if (meter) meter.setAttribute('data-level', String(s));
    if (meterLabel) meterLabel.textContent = LABELS[s];
  }

  if (form) {
    form.addEventListener('input', function () { refresh(); if (pw) onStrength(); });
    form.addEventListener('change', refresh);
  }
  refresh();
  if (pw) onStrength();

  /* ---- show / hide password ------------------------------------------ */
  Array.prototype.forEach.call(stage.querySelectorAll('.pw-toggle'), function (btn) {
    btn.addEventListener('click', function () {
      var input = btn.parentElement.querySelector('input');
      var show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.setAttribute('aria-pressed', String(show));
      btn.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
    });
  });

  /* ---- parallax + card spotlight / tilt ------------------------------ */
  if (!reduceMotion) {
    stage.addEventListener('pointermove', function (e) {
      var r = stage.getBoundingClientRect();
      stage.style.setProperty('--px', ((e.clientX - r.left) / r.width - 0.5).toFixed(3));
      stage.style.setProperty('--py', ((e.clientY - r.top) / r.height - 0.5).toFixed(3));
    });
    if (card) {
      card.addEventListener('pointermove', function (e) {
        var r = card.getBoundingClientRect();
        var x = (e.clientX - r.left) / r.width;
        var y = (e.clientY - r.top) / r.height;
        card.style.setProperty('--mx', (x * 100).toFixed(1) + '%');
        card.style.setProperty('--my', (y * 100).toFixed(1) + '%');
        card.style.transform = 'rotateY(' + ((x - 0.5) * 6).toFixed(2) + 'deg) rotateX(' + ((0.5 - y) * 6).toFixed(2) + 'deg)';
      });
      card.addEventListener('pointerleave', function () { card.style.transform = ''; });
    }
  }

  /* ---- submit: the door swings open, then the form is sent ----------- */
  if (form && door) {
    var sending = false;
    form.addEventListener('submit', function (e) {
      if (sending) return;
      if (!form.checkValidity()) return;
      e.preventDefault();
      sending = true;
      lightUp(TOTAL);
      door.classList.add('open');
      var btn = form.querySelector('.key-btn');
      if (btn) btn.classList.add('loading');
      setTimeout(function () { form.submit(); }, reduceMotion ? 0 : 950);
    });
  }
})();

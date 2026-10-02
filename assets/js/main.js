/* ============================================================
   APRO GLOBAL REAL ESTATE — Main Script
   ============================================================ */

/* ── Tab switching ── */
function setTab(el) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
}

/* ── Filter tag toggle ── */
function toggleFilter(el) { el.classList.toggle('active-tag'); }

/* ── Mobile menu close (called inline & from JS) ── */
function closeMobileMenu() {
  const menu      = document.getElementById('mobileMenu');
  const hamburger = document.getElementById('hamburger');
  if (!menu || !menu.classList.contains('open')) return;

  // animate closed: remove open, keep is-animating so clip-path transitions back
  menu.classList.remove('open');
  menu.classList.add('is-animating');

  // once animation finishes, fully hide with display:none
  setTimeout(() => {
    menu.classList.remove('is-animating');
    // display:none is now restored by CSS (no open / no is-animating = display:none)
  }, 580);

  if (hamburger) {
    hamburger.classList.remove('open');
    hamburger.setAttribute('aria-expanded', 'false');
  }
  document.body.style.overflow = '';
  document.documentElement.style.overflow = '';
}

/* ============================================================
   DOM READY
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {

  /* ── Navbar scroll → glass ── */
  const navbar = document.getElementById('navbar');
  const scrollToTopBtn = document.getElementById('scrollToTop');
  const waBtn = document.querySelector('.fab-whatsapp');

  function updateNavbar() {
    const scrolled = window.scrollY > 60;
    navbar.classList.toggle('scrolled', scrolled);
    // scroll-to-top: show after 400px
    if (scrollToTopBtn) scrollToTopBtn.classList.toggle('visible', window.scrollY > 400);
    // whatsapp: show after hero height (approx window height)
    if (waBtn) waBtn.classList.toggle('visible', window.scrollY > window.innerHeight * 0.6);
  }
  window.addEventListener('scroll', updateNavbar, { passive: true });
  updateNavbar();

  // scroll to top click
  if (scrollToTopBtn) {
    scrollToTopBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ── Hamburger ── */
  const hamburger  = document.getElementById('hamburger');
  const mobileMenu = document.getElementById('mobileMenu');
  // support both old .mobile-menu-close and new .mm-close
  const menuClose  = document.getElementById('menuClose') || document.querySelector('.mm-close');

  hamburger.addEventListener('click', () => {
    const open = mobileMenu.classList.contains('open');
    if (open) {
      closeMobileMenu();
    } else {
      // Step 1: display:flex with clip at 0 (is-animating)
      mobileMenu.classList.add('is-animating');
      hamburger.classList.add('open');
      hamburger.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
      document.documentElement.style.overflow = 'hidden';
      // Step 2: next frame — add .open to trigger clip-path expand transition
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          mobileMenu.classList.add('open');
          mobileMenu.classList.remove('is-animating');
        });
      });
    }
  });
  if (menuClose) menuClose.addEventListener('click', closeMobileMenu);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMobileMenu(); });
  mobileMenu.addEventListener('click', e => { if (e.target === mobileMenu) closeMobileMenu(); });

  /* ── mm-link active highlight ── */
  document.querySelectorAll('.mm-link').forEach(link => {
    link.addEventListener('click', function () {
      document.querySelectorAll('.mm-link').forEach(l => l.classList.remove('active'));
      this.classList.add('active');
    });
  });

  /* ──────────────────────────────────────────────────────────
     HERO entrance animations
  ────────────────────────────────────────────────────────── */
  const heroEl      = document.querySelector('.hero');
  const heroContent = document.querySelector('.hero-content');
  if (heroContent) {
    setTimeout(() => {
      heroContent.classList.add('animate');
      heroEl.classList.add('loaded');
    }, 200);
  }

  /* ── Property pills ── */
  document.querySelectorAll('.property-pills .pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.property-pills .pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
    });
  });

  /* ── Wishlist hearts ── */
  document.querySelectorAll('.card-wishlist').forEach(btn => {
    btn.addEventListener('click', e => { e.stopPropagation(); btn.classList.toggle('liked'); });
  });

  /* ── Nav link active ── */
  document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', function () {
      document.querySelectorAll('.nav-links a').forEach(l => l.classList.remove('active'));
      this.classList.add('active');
    });
  });

  /* ──────────────────────────────────────────────────────────
     STATS COUNTER
  ────────────────────────────────────────────────────────── */
  const statEls = document.querySelectorAll('.stat-num');
  const rawVals = [250, 1500, 23, 2];
  let statsAnimated = false;

  function animateCount(el, target) {
    const duration = 1300;
    const start = performance.now();
    function step(now) {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      const val = Math.round(eased * target);
      el.innerHTML = (val >= 1000 ? val.toLocaleString() : val) + '<span>+</span>';
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  const statsBar = document.querySelector('.stats-bar');
  if (statsBar) {
    new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && !statsAnimated) {
        statsAnimated = true;
        statEls.forEach((el, i) => animateCount(el, rawVals[i]));
      }
    }, { threshold: 0.3 }).observe(statsBar);
  }

  /* ──────────────────────────────────────────────────────────
     LISTING CARDS FADE IN
  ────────────────────────────────────────────────────────── */
  const cards = document.querySelectorAll('.listing-card');
  cards.forEach(c => {
    c.style.opacity   = '0';
    c.style.transform = 'translateY(32px)';
    c.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
  });
  const cardObs = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const idx = Array.from(cards).indexOf(entry.target);
        setTimeout(() => {
          entry.target.style.opacity   = '1';
          entry.target.style.transform = 'translateY(0)';
        }, (idx % 3) * 90);
        cardObs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });
  cards.forEach(c => cardObs.observe(c));

  /* ──────────────────────────────────────────────────────────
     ABOUT METRICS FADE IN
  ────────────────────────────────────────────────────────── */
  document.querySelectorAll('.metric-card').forEach((c, i) => {
    c.style.opacity   = '0';
    c.style.transform = 'translateY(24px)';
    c.style.transition = `opacity 0.5s ${i * 0.1}s ease, transform 0.5s ${i * 0.1}s ease`;
    new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        c.style.opacity   = '1';
        c.style.transform = 'translateY(0)';
      }
    }, { threshold: 0.2 }).observe(c);
  });

  /* ──────────────────────────────────────────────────────────
     TESTIMONIALS — 3D rotating carousel
  ────────────────────────────────────────────────────────── */
  const tTrack    = document.querySelector('.tcarousel-track');
  const tCards    = document.querySelectorAll('.t-card');
  const tDots     = document.querySelectorAll('.tcarousel-dot');
  const tPrev     = document.querySelector('.tcarousel-btn.t-prev');
  const tNext     = document.querySelector('.tcarousel-btn.t-next');
  const tCounter  = document.querySelector('.tcarousel-counter span');
  const N         = tCards.length;
  let tCurrent    = 0;
  let tAutoTimer;
  let tDragging   = false;
  let tDragStartX = 0;

  function positionCards() {
    const angleStep = 360 / N;
    // radius shrinks on mobile
    const radius = window.innerWidth < 600 ? 220 : 320;
    tCards.forEach((card, i) => {
      const offset = i - tCurrent;
      // wrap around
      let angle = ((offset % N) + N) % N;
      if (angle > N / 2) angle -= N;
      const rot = angle * angleStep;
      const z   = Math.cos((rot * Math.PI) / 180) * radius - radius;
      const x   = Math.sin((rot * Math.PI) / 180) * radius;
      const scale = 1 - Math.abs(angle) * 0.14;
      const opacity = Math.max(0.35, 1 - Math.abs(angle) * 0.32);
      card.style.transform = `translateX(${x}px) translateZ(${z}px) scale(${scale})`;
      card.style.opacity   = opacity;
      card.style.zIndex    = Math.round(100 - Math.abs(angle) * 10);
      card.style.filter    = Math.abs(angle) > 0 ? 'blur(1px)' : 'none';
      card.classList.toggle('t-active', i === tCurrent);
    });
    tDots.forEach((d, i) => d.classList.toggle('active', i === tCurrent));
    if (tCounter) tCounter.textContent = tCurrent + 1;
  }

  function tGo(dir) {
    tCurrent = ((tCurrent + dir) + N) % N;
    positionCards();
  }
  function startTAuto() {
    clearInterval(tAutoTimer);
    tAutoTimer = setInterval(() => tGo(1), 4200);
  }

  if (tTrack && N > 0) {
    positionCards();
    startTAuto();
    tPrev?.addEventListener('click', () => { tGo(-1); startTAuto(); });
    tNext?.addEventListener('click', () => { tGo(1);  startTAuto(); });
    tDots.forEach((d, i) => d.addEventListener('click', () => { tCurrent = i; positionCards(); startTAuto(); }));

    /* swipe support */
    tTrack.addEventListener('pointerdown', e => {
      tDragging  = true;
      tDragStartX = e.clientX;
      tTrack.setPointerCapture(e.pointerId);
    });
    tTrack.addEventListener('pointerup', e => {
      if (!tDragging) return;
      tDragging = false;
      const dx = e.clientX - tDragStartX;
      if (Math.abs(dx) > 50) { tGo(dx < 0 ? 1 : -1); startTAuto(); }
    });

    /* reposition on resize */
    window.addEventListener('resize', positionCards, { passive: true });
  }

  /* ──────────────────────────────────────────────────────────
     BLOG CARDS FADE IN
  ────────────────────────────────────────────────────────── */
  document.querySelectorAll('.blog-card').forEach((c, i) => {
    c.style.opacity   = '0';
    c.style.transform = 'translateY(28px)';
    c.style.transition = `opacity 0.55s ${i * 0.08}s ease, transform 0.55s ${i * 0.08}s ease`;
    new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        c.style.opacity   = '1';
        c.style.transform = 'translateY(0)';
      }
    }, { threshold: 0.1 }).observe(c);
  });

});

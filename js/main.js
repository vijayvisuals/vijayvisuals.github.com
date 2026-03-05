/* ═══════════════════════════════════════════════════════════════
   main.js — OPTIMIZED: cursor glow (RAF-throttled), loader,
             nav scroll (passive + throttled), IntersectionObserver,
             hero name split, portrait parallax (RAF-throttled)
═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  /* ─── CURSOR GLOW — RAF with dirty-flag, skips idle frames ── */
  const cursorGlow = document.getElementById('cursor-glow');
  let mouseX = -999, mouseY = -999;
  let glowX = -999, glowY = -999;
  let cursorDirty = false;
  let cursorRAF = null;

  document.addEventListener('mousemove', e => {
    mouseX = e.clientX;
    mouseY = e.clientY;
    if (!cursorDirty) {
      cursorDirty = true;
      cursorRAF = requestAnimationFrame(animateCursor);
    }
  }, { passive: true });

  function animateCursor() {
    cursorRAF = null;
    const dx = mouseX - glowX;
    const dy = mouseY - glowY;
    // Stop looping when close enough (saves CPU when idle)
    if (Math.abs(dx) < 0.3 && Math.abs(dy) < 0.3) {
      cursorDirty = false;
      return;
    }
    glowX += dx * 0.10;
    glowY += dy * 0.10;
    cursorGlow.style.transform = `translate(${glowX}px, ${glowY}px) translate(-50%, -50%)`;
    cursorRAF = requestAnimationFrame(animateCursor);
  }

  /* ─── LOADING SCREEN — waits for hero image + min timer ──── */
  const loader = document.getElementById('loader');
  const heroPoster = new Image();
  heroPoster.src = 'assets/images/hero-poster.jpg';

  function hideLoader() {
    loader.classList.add('hidden');
    document.body.classList.remove('loading');
    document.body.classList.add('loaded');
    revealHeroName();
  }

  window.addEventListener('load', () => {
    // Minimum display time for loader (matches progress bar animation)
    const minWait = new Promise(resolve => setTimeout(resolve, 2600));
    // Wait for hero image to be fully decoded and ready
    const imgReady = heroPoster.complete
      ? Promise.resolve()
      : new Promise(resolve => {
        heroPoster.onload = resolve;
        heroPoster.onerror = resolve; // don't block if image fails
      });

    Promise.all([minWait, imgReady]).then(hideLoader);
  });

  /* ─── HERO NAME CHARACTER SPLIT ───────────────────────────── */
  function revealHeroName() {
    const lines = document.querySelectorAll('.hero-name .name-line');
    let delay = 0;
    lines.forEach(line => {
      const text = line.textContent;
      line.textContent = '';
      [...text].forEach(char => {
        const span = document.createElement('span');
        span.className = 'name-char';
        span.style.animationDelay = `${delay}s`;
        span.textContent = char === ' ' ? '\u00A0' : char;
        line.appendChild(span);
        delay += 0.04;
      });
    });
  }

  /* ─── NAVIGATION — throttled passive scroll ────────────────── */
  const nav = document.getElementById('main-nav');
  const menuBtn = document.getElementById('nav-menu-btn');
  const mobileNav = document.getElementById('mobile-nav');
  let scrollTicking = false;

  window.addEventListener('scroll', () => {
    if (!scrollTicking) {
      scrollTicking = true;
      requestAnimationFrame(() => {
        nav.classList.toggle('scrolled', window.scrollY > 60);
        scrollTicking = false;
      });
    }
  }, { passive: true });

  menuBtn.addEventListener('click', () => {
    mobileNav.classList.toggle('open');
    document.body.style.overflow = mobileNav.classList.contains('open') ? 'hidden' : '';
  });

  mobileNav.addEventListener('click', e => {
    if (e.target.tagName === 'A') {
      mobileNav.classList.remove('open');
      document.body.style.overflow = '';
    }
  });

  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', e => {
      const target = document.querySelector(link.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  /* ─── INTERSECTION OBSERVER — scroll reveals ──────────────── */
  const revealSelectors = [
    '.section-label', '.section-title', '.project-card',
    '.skill-card', '.credit-row', '.timeline-item',
    '.contact-link', '.sw-icon', '.about-portrait-wrap',
    '.about-content', '.showreel-player-wrap', '.imdb-link-wrap',
  ];

  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const siblings = [...el.parentElement.querySelectorAll(
          el.tagName + '.' + el.classList[0]
        )];
        const delay = siblings.indexOf(el) * 80;
        setTimeout(() => el.classList.add('visible'), delay);
        revealObserver.unobserve(el);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -60px 0px' });

  revealSelectors.forEach(sel => {
    document.querySelectorAll(sel).forEach(el => revealObserver.observe(el));
  });

  /* ─── SKILL BAR ANIMATION ─────────────────────────────────── */
  const skillBarObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const fill = entry.target;
        const width = fill.getAttribute('data-w');
        setTimeout(() => { fill.style.width = width + '%'; }, 300);
        skillBarObserver.unobserve(fill);
      }
    });
  }, { threshold: 0.3 });

  document.querySelectorAll('.skill-fill').forEach(el => skillBarObserver.observe(el));

  /* ─── PORTRAIT PARALLAX — RAF-throttled, passive ──────────── */
  const portraitImg = document.getElementById('portrait-img');
  let parallaxTicking = false;

  if (portraitImg) {
    window.addEventListener('scroll', () => {
      if (!parallaxTicking) {
        parallaxTicking = true;
        requestAnimationFrame(() => {
          const rect = portraitImg.getBoundingClientRect();
          const winH = window.innerHeight;
          // Only run when portrait is in viewport
          if (rect.bottom > 0 && rect.top < winH) {
            const progress = (winH - rect.top) / (winH + rect.height);
            const translateY = (progress - 0.5) * 50;
            portraitImg.style.transform = `translateY(${translateY}px) scale(1.05)`;
          }
          parallaxTicking = false;
        });
      }
    }, { passive: true });
  }

});

/* ═══════════════════════════════════════════════════════════════
   main.js — OPTIMIZED: cursor glow (RAF-throttled), loader,
             nav scroll (passive + throttled), IntersectionObserver,
             hero name split, portrait parallax (RAF-throttled)
═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {



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

  /* ─── STATS COUNTER ─────────────────────────────────────────── */
  function animateCount(el, target, duration = 1200) {
    const start = performance.now();
    const update = (now) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const ease = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(ease * target) + (target >= 40 ? '+' : '');
      if (progress < 1) requestAnimationFrame(update);
    };
    requestAnimationFrame(update);
  }

  const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const nums = entry.target.querySelectorAll('.stat-num');
        nums.forEach((el, i) => {
          const target = parseInt(el.getAttribute('data-target'), 10);
          setTimeout(() => animateCount(el, target), i * 120);
        });
        statsObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.4 });

  const statsStrip = document.getElementById('stats-strip');
  if (statsStrip) statsObserver.observe(statsStrip);

  /* ─── PROJECT CARD STAGGER REVEAL ───────────────────────────── */
  const cardObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry, idx) => {
      if (entry.isIntersecting) {
        const card = entry.target;
        const i = Array.from(document.querySelectorAll('.project-card')).indexOf(card);
        setTimeout(() => {
          card.classList.add('card-visible');
        }, (i % 3) * 80); // stagger by column position
        cardObserver.unobserve(card);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.project-card').forEach(card => cardObserver.observe(card));

  /* ─── FILTER TABS ────────────────────────────────────────────── */
  const filterBtns = document.querySelectorAll('.filter-btn');
  const projectCards = document.querySelectorAll('.project-card');

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      // Update active button
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.getAttribute('data-filter');

      projectCards.forEach(card => {
        const cat = card.getAttribute('data-category') || '';
        const show = filter === 'all' || cat.includes(filter);

        if (show) {
          card.classList.remove('card-hidden');
          // Re-trigger stagger if not yet visible
          if (!card.classList.contains('card-visible')) {
            card.classList.add('card-visible');
          }
        } else {
          card.classList.add('card-hidden');
        }
      });
    });
  });

});

/* ── HAMBURGER NAV ── */
const hamburger = document.getElementById('hamburger');
const navLinks  = document.querySelector('.nav-links');
if (hamburger && navLinks) {
  hamburger.addEventListener('click', (e) => {
    e.stopPropagation();
    navLinks.classList.toggle('open');
    hamburger.classList.toggle('open');
  });
  document.addEventListener('click', (e) => {
    if (!hamburger.contains(e.target) && !navLinks.contains(e.target)) {
      navLinks.classList.remove('open');
      hamburger.classList.remove('open');
    }
  });
  navLinks.querySelectorAll('a').forEach(a =>
    a.addEventListener('click', () => {
      navLinks.classList.remove('open');
      hamburger.classList.remove('open');
    })
  );
}

/* ── SCROLL-TO-TOP ── */
const scrollTopBtn = document.getElementById('scroll-top');
if (scrollTopBtn) {
  window.addEventListener('scroll', () => {
    scrollTopBtn.classList.toggle('visible', window.scrollY > 420);
  }, { passive: true });
  scrollTopBtn.addEventListener('click', () =>
    window.scrollTo({ top: 0, behavior: 'smooth' })
  );
}

/* ── SCROLL REVEAL ── */
(function () {
  // Auto-tag revealable elements
  document.querySelectorAll('.pub-year-group, .script-card, .tl-item, .stat-card').forEach(el => {
    el.classList.add('reveal');
  });

  const revealEls = document.querySelectorAll('.reveal');
  if (!revealEls.length) return;

  const ro = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('revealed');
        ro.unobserve(e.target);
      }
    });
  }, { threshold: 0.08 });

  revealEls.forEach(el => ro.observe(el));
})();

/* ── SCHOLAR STATS (index.html only) ── */
function animateCount(el, target) {
  if (!el || !target) return;
  let v = 0;
  const step = Math.max(1, Math.ceil(target / 50));
  const t = setInterval(() => {
    v = Math.min(v + step, target);
    el.textContent = v;
    if (v >= target) clearInterval(t);
  }, 25);
}

const aboutStats = document.querySelector('.about-stats');
if (aboutStats && document.getElementById('stat-cites')) {
  const so = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      fetch('scholar_stats.json?_=' + Date.now())
        .then(r => r.json())
        .then(d => {
          animateCount(document.getElementById('stat-pubs'),   25);
          animateCount(document.getElementById('stat-cites'),  d.citations || 0);
          animateCount(document.getElementById('stat-hindex'), d.h_index   || 0);
          const upd = document.getElementById('scholar-updated');
          if (upd && d.updated) upd.textContent = 'Updated: ' + d.updated;
        })
        .catch(() => animateCount(document.getElementById('stat-pubs'), 25));
      so.unobserve(aboutStats);
    }
  }, { threshold: 0.3 });
  so.observe(aboutStats);
}

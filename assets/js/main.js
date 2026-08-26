// Theme toggle, nav, reveal-on-scroll, clip players, tagline rotator,
// back-to-top. No dependencies. Initial theme is set inline in <head>.
//
// Every lookup below is guarded. The six chrome elements are on all sixteen
// pages today, but an unguarded querySelector near the top of the file takes
// the whole file down with it, and everything after it is a feature the reader
// can see. A page built from a partial template should lose one behaviour, not
// all of them.

const root = document.documentElement;
const $ = (sel, ctx = document) => ctx.querySelector(sel);

// Live, not a snapshot: this setting is toggled from Control Center on macOS
// and iOS, so it changes mid-session more often than it looks.
const motionQuery = matchMedia("(prefers-reduced-motion: reduce)");
let reducedMotion = motionQuery.matches;
const onMotionChange = [];
motionQuery.addEventListener("change", (e) => {
  reducedMotion = e.matches;
  onMotionChange.forEach((fn) => fn());
});

// --- Theme toggle ---
// aria-label names what the button turns on; aria-pressed carries the state,
// which is otherwise invisible: both icons are aria-hidden, so without it a
// screen reader could not tell which theme was active or what pressing did.
const themeToggle = $(".theme-toggle");
if (themeToggle) {
  const syncTheme = () =>
    themeToggle.setAttribute("aria-pressed", String(root.dataset.theme === "dark"));
  syncTheme();
  themeToggle.addEventListener("click", () => {
    root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
    syncTheme();
    // Writing throws where storage is blocked. The theme has already flipped on
    // screen by this point, so only the memory of it is lost.
    try {
      localStorage.setItem("theme", root.dataset.theme);
    } catch (e) {
      /* not persistable here; the choice still holds for this page */
    }
  });
}

// --- Footer year ---
const year = document.getElementById("year");
if (year) year.textContent = new Date().getFullYear();

// --- Mobile nav ---
// The button sits before the menu in the DOM so Tab reaches the menu next once
// it opens; CSS moves it back to the right edge at the mobile breakpoint.
const navToggle = $(".nav-toggle");
const menu = document.getElementById("nav-menu");

if (navToggle && menu) {
  const setOpen = (open, focusMenu = false) => {
    menu.classList.toggle("open", open);
    navToggle.setAttribute("aria-expanded", String(open));
    if (open && focusMenu) $("a", menu)?.focus();
  };

  navToggle.addEventListener("click", () =>
    setOpen(!menu.classList.contains("open"), true));

  menu.addEventListener("click", (e) => {
    if (e.target.matches("a")) setOpen(false);
  });

  // A disclosure menu has to be dismissible without choosing something, and
  // focus has to come back to the control that opened it.
  addEventListener("keydown", (e) => {
    if (e.key === "Escape" && menu.classList.contains("open")) {
      setOpen(false);
      navToggle.focus();
    }
  });

  addEventListener("pointerdown", (e) => {
    if (menu.classList.contains("open") &&
        !menu.contains(e.target) && !navToggle.contains(e.target)) {
      setOpen(false);
    }
  });
}

// --- Header shadow + back-to-top visibility ---
const header = $(".site-header");
const toTop = $(".to-top");
const SHADOW_AT = 8;      // px scrolled before the header earns its shadow
const TO_TOP_AT = 600;    // px scrolled before returning to the top is useful

if (header || toTop) {
  let ticking = false;
  const sync = () => {
    ticking = false;
    header?.classList.toggle("scrolled", scrollY > SHADOW_AT);
    toTop?.classList.toggle("show", scrollY > TO_TOP_AT);
  };
  addEventListener("scroll", () => {
    // Coalesce to one read per frame; a trackpad fires this far faster.
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(sync);
    }
  }, { passive: true });
  sync();
}

if (toTop) {
  toTop.addEventListener("click", () => {
    scrollTo({ top: 0, behavior: reducedMotion ? "auto" : "smooth" });
    // The button hides itself once the scroll passes the threshold, and focus
    // would otherwise fall back to <body>. main carries tabindex="-1" for this
    // and for the skip link; preventScroll keeps it out of the smooth scroll.
    document.getElementById("main")?.focus({ preventScroll: true });
  });
}

// --- Scroll spy: highlight the nav link for the section in view ---
// Only the two index pages have a nav that points at sections of the page it is
// on. Everywhere else the links point back to the home page, so there is
// nothing to highlight and no observer worth building.
const sections = [...document.querySelectorAll("main section[id]")];
const navLinks = new Map(
  menu
    ? [...menu.querySelectorAll("a[href]")]
        .map((a) => [a.getAttribute("href").split("#")[1], a])
        .filter(([id]) => id)
    : []
);

if (sections.some((s) => navLinks.has(s.id))) {
  const onScreen = new Set();
  const clear = () => navLinks.forEach((a) => {
    a.classList.remove("active");
    a.removeAttribute("aria-current");
  });

  const spy = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) onScreen.add(entry.target);
      else onScreen.delete(entry.target);
    });
    // The active band is narrow enough that two sections can occupy it at once,
    // and callback order is not document order. Take the first in the document
    // rather than whichever entry happened to land last in the array.
    const current = sections.find((s) => onScreen.has(s));
    clear();
    // The hero has an id but no nav link, so scrolling back to the top
    // correctly leaves nothing highlighted.
    const link = current && navLinks.get(current.id);
    if (link) {
      link.classList.add("active");
      link.setAttribute("aria-current", "true");
    }
  }, { rootMargin: "-40% 0px -55% 0px" });

  sections.forEach((s) => spy.observe(s));
}

// --- Reveal on scroll ---
// Tag content blocks below the hero; stagger siblings via --delay.
const revealTargets = document.querySelectorAll(
  ".section-title, .about p, .entry, .card, .skill-group, .languages, .contact .hero-actions"
);

if (revealTargets.length) {
  const siblingCount = new Map();
  revealTargets.forEach((el) => {
    const n = siblingCount.get(el.parentElement) ?? 0;
    siblingCount.set(el.parentElement, n + 1);
    el.style.setProperty("--delay", `${Math.min(n, 5) * 90}ms`);
    el.classList.add("reveal");
  });

  const showAll = () => revealTargets.forEach((el) => el.classList.add("visible"));

  if (reducedMotion) {
    showAll();
  } else {
    const revealer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          revealer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: "0px 0px -40px 0px" });
    revealTargets.forEach((el) => revealer.observe(el));
    // If the reader asks for less motion later, nothing should still be hidden.
    onMotionChange.push(() => {
      if (reducedMotion) {
        revealer.disconnect();
        showAll();
      }
    });
  }
}

// --- Clip players ---
// The clips are ambient: each one starts when it scrolls into view and stops
// when it leaves, so the page is never playing video the reader cannot see and
// never downloads a clip nobody scrolled to. One button governs the set,
// because auto-playing video has to offer a way to stop it and a badge on each
// clip would cover the phone screen it is there to show. Stopping them also
// hands the browser's controls back, so a halted clip becomes a player that can
// be scrubbed; while they run they carry no chrome, since the control scrim is
// a black gradient across the bottom third of a portrait video. That is the
// trade: a running clip is not focusable, and the toggle above the set is the
// keyboard's way in. Without this file the clips keep those controls from the
// start and the button stays hidden, having nothing to act on.
const clipFrames = [...document.querySelectorAll(".clip-frame")];
const clipsToggle = $(".clips-toggle");

if (clipFrames.length && clipsToggle) {
  const videos = clipFrames.map((frame) => $("video", frame)).filter(Boolean);
  const label = $("span", clipsToggle);
  const onScreen = new Set();
  // Nothing moves on its own for a reader who has asked for less motion; the
  // button still offers it.
  let running = !reducedMotion;

  const apply = () => {
    videos.forEach((video) => {
      video.controls = !running;
      // Autoplay can be refused (a data saver, iOS low power mode). There is
      // nothing to recover: the clip simply stays on its poster.
      if (running && onScreen.has(video)) video.play().catch(() => {});
      else video.pause();
    });
    clipsToggle.classList.toggle("is-paused", !running);
    clipsToggle.setAttribute("aria-pressed", String(running));
    const text = running ? clipsToggle.dataset.pauseLabel : clipsToggle.dataset.playLabel;
    if (label && text) label.textContent = text;
  };

  clipsToggle.classList.add("is-ready");
  clipsToggle.addEventListener("click", () => {
    running = !running;
    apply();
  });

  const watcher = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      const video = $("video", entry.target);
      if (!video) return;
      if (entry.isIntersecting) onScreen.add(video);
      else onScreen.delete(video);
    });
    apply();
  },
  // A third of a tall clip is enough to be worth playing, and low enough that
  // a clip taller than the viewport still qualifies.
  { threshold: 0.33 });
  clipFrames.forEach((frame) => watcher.observe(frame));

  onMotionChange.push(() => {
    if (reducedMotion && running) {
      running = false;
      apply();
    }
  });

  apply();
}

// --- Hero tagline rotator ---
// Phrases come from the element's data-phrases attribute so each language
// version of the page supplies its own without touching this file.
const rotator = document.getElementById("rotator");

let phrases = [];
try {
  phrases = JSON.parse(rotator?.dataset.phrases ?? "[]");
} catch {
  phrases = [];
}

if (rotator && !reducedMotion && phrases.length > 1) {
  const STEP = 3500;
  const FADE = 350;
  let i = 0;
  let timer = null;
  let swap = null;

  const stop = () => {
    clearInterval(timer);
    clearTimeout(swap);
    timer = swap = null;
  };

  const tick = () => {
    rotator.classList.add("swap");
    swap = setTimeout(() => {
      i = (i + 1) % phrases.length;
      rotator.textContent = phrases[i];
      rotator.classList.remove("swap");
      // One pass through the list, then it rests on the phrase it started on.
      // Indefinite motion would need a control of its own to stop it, and the
      // hero is not the place to put one.
      if (i === 0) stop();
    }, FADE);
  };

  const start = () => {
    if (!timer && i !== 0) timer = setInterval(tick, STEP);
  };

  timer = setInterval(tick, STEP);

  // Nothing to animate on a tab nobody is looking at.
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stop();
    else start();
  });
  onMotionChange.push(() => {
    if (reducedMotion) stop();
  });
}

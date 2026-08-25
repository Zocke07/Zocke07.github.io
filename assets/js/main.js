// Theme toggle, nav, reveal-on-scroll, tagline rotator, back-to-top.
// No dependencies. Initial theme is set inline in <head>.

const root = document.documentElement;
const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

// --- Theme toggle ---
document.querySelector(".theme-toggle").addEventListener("click", () => {
  const next = root.dataset.theme === "dark" ? "light" : "dark";
  root.dataset.theme = next;
  localStorage.setItem("theme", next);
});

// --- Footer year ---
document.getElementById("year").textContent = new Date().getFullYear();

// --- Mobile nav toggle ---
const navToggle = document.querySelector(".nav-toggle");
const menu = document.getElementById("nav-menu");

navToggle.addEventListener("click", () => {
  const open = menu.classList.toggle("open");
  navToggle.setAttribute("aria-expanded", String(open));
});

menu.addEventListener("click", (e) => {
  if (e.target.matches("a")) {
    menu.classList.remove("open");
    navToggle.setAttribute("aria-expanded", "false");
  }
});

// --- Header shadow + back-to-top visibility ---
const header = document.querySelector(".site-header");
const toTop = document.querySelector(".to-top");

addEventListener(
  "scroll",
  () => {
    header.classList.toggle("scrolled", scrollY > 8);
    toTop.classList.toggle("show", scrollY > 600);
  },
  { passive: true }
);

toTop.addEventListener("click", () => {
  scrollTo({ top: 0, behavior: reducedMotion ? "auto" : "smooth" });
});

// --- Scroll spy: highlight the nav link for the section in view ---
const sections = [...document.querySelectorAll("main section[id]")];
const navLinks = new Map(
  [...menu.querySelectorAll("a")].map((a) => [a.getAttribute("href").split("#")[1], a])
);

const spy = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      const link = navLinks.get(entry.target.id);
      if (link && entry.isIntersecting) {
        navLinks.forEach((a) => a.classList.remove("active"));
        link.classList.add("active");
      }
    });
  },
  { rootMargin: "-40% 0px -55% 0px" }
);

sections.forEach((s) => spy.observe(s));

// --- Reveal on scroll ---
// Tag content blocks below the hero; stagger siblings via --delay.
const revealTargets = document.querySelectorAll(
  ".section-title, .about p, .entry, .card, .skill-group, .languages, .contact p, .contact .hero-actions"
);

const siblingCount = new Map();
revealTargets.forEach((el) => {
  const n = siblingCount.get(el.parentElement) ?? 0;
  siblingCount.set(el.parentElement, n + 1);
  el.style.setProperty("--delay", `${Math.min(n, 5) * 90}ms`);
  el.classList.add("reveal");
});

if (reducedMotion) {
  revealTargets.forEach((el) => el.classList.add("visible"));
} else {
  const revealer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          revealer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
  );
  revealTargets.forEach((el) => revealer.observe(el));
}

// --- Clip players ---
// The clips are ambient: each one starts when it scrolls into view and stops
// when it leaves, so the page is never playing video the reader cannot see and
// never downloads a clip nobody scrolled to. One button governs the set,
// because auto-playing video has to offer a way to stop it and a badge on each
// clip would cover the phone screen it is there to show. Stopping them also
// hands the browser's controls back, so a halted clip becomes a player that can
// be scrubbed; while they run they carry no chrome, since the control scrim is
// a black gradient across the bottom third of a portrait video. Without this
// file the clips keep those controls from the start and the button stays
// hidden, having nothing to act on.
const clipFrames = [...document.querySelectorAll(".clip-frame")];
const clipsToggle = document.querySelector(".clips-toggle");

if (clipFrames.length && clipsToggle) {
  const videos = clipFrames.map((frame) => frame.querySelector("video")).filter(Boolean);
  const label = clipsToggle.querySelector("span");
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
    const text = running ? clipsToggle.dataset.pauseLabel : clipsToggle.dataset.playLabel;
    if (label && text) label.textContent = text;
  };

  clipsToggle.classList.add("is-ready");
  clipsToggle.addEventListener("click", () => {
    running = !running;
    apply();
  });

  const watcher = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const video = entry.target.querySelector("video");
        if (!video) return;
        if (entry.isIntersecting) onScreen.add(video);
        else onScreen.delete(video);
      });
      apply();
    },
    // A third of a tall clip is enough to be worth playing, and low enough that
    // a clip taller than the viewport still qualifies.
    { threshold: 0.33 }
  );
  clipFrames.forEach((frame) => watcher.observe(frame));

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
  let i = 0;
  setInterval(() => {
    rotator.classList.add("swap");
    setTimeout(() => {
      i = (i + 1) % phrases.length;
      rotator.textContent = phrases[i];
      rotator.classList.remove("swap");
    }, 350);
  }, 3500);
}

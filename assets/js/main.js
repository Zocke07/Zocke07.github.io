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
  ".section-title, .entry, .card, .skill-group, .languages, .contact p, .contact .hero-actions"
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

// --- Hero tagline rotator ---
const rotator = document.getElementById("rotator");
const phrases = [
  "QA & Test Automation",
  "Federated Learning Security",
  "Technical Program Management",
];

if (rotator && !reducedMotion) {
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

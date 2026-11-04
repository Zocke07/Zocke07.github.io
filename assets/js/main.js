// Theme switch, menu, header state, the reading rail, back-to-top, diagram
// notes, clip players, project chains and the start of the opening sequence. No
// dependencies. The initial theme and the .js class are set inline in <head>.
//
// Every lookup below is guarded: a page built from a partial template should
// lose one behaviour, not all of them. Strings the reader sees come from the
// markup, so this file holds no English or Chinese text.

const root = document.documentElement;
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

// Live, not a snapshot: this setting is toggled from Control Center on macOS
// and iOS, so it changes mid-session more often than it looks. Everything that
// answers it answers in one direction: something that was moving stops.
const motionQuery = matchMedia("(prefers-reduced-motion: reduce)");
let reducedMotion = motionQuery.matches;
const onReduced = [];
const whenReducedMotion = (fn) => onReduced.push(fn);
motionQuery.addEventListener("change", (e) => {
  reducedMotion = e.matches;
  if (reducedMotion) onReduced.forEach((fn) => fn());
});

// --- Theme switch ---
// aria-label names what the button turns on; aria-pressed carries the state.
const themeQuery = matchMedia("(prefers-color-scheme: dark)");
const systemTheme = () => (themeQuery.matches ? "dark" : "light");
const storedTheme = () => {
  try {
    return localStorage.getItem("theme");
  } catch (e) {
    return null;
  }
};

const themeToggle = $(".theme-toggle");
const syncTheme = () => {
  if (!themeToggle) return;
  const dark = root.dataset.theme === "dark";
  themeToggle.setAttribute("aria-pressed", String(dark));
  const label = dark ? themeToggle.dataset.labelLight : themeToggle.dataset.labelDark;
  if (label) themeToggle.setAttribute("aria-label", label);
};

// Only pages with no stored choice follow the OS when it flips at sunset.
themeQuery.addEventListener("change", () => {
  if (storedTheme()) return;
  root.dataset.theme = systemTheme();
  syncTheme();
});

const setTheme = (next) => {
  root.dataset.theme = next;
  syncTheme();
  // Storing only a choice that disagrees with the OS keeps "follow the system"
  // reachable. Writing throws where storage is blocked; the theme has already
  // flipped on screen, so only the memory of it is lost.
  try {
    if (next === systemTheme()) localStorage.removeItem("theme");
    else localStorage.setItem("theme", next);
  } catch (e) {
    /* not persistable here; the choice still holds for this page */
  }
};

if (themeToggle) {
  syncTheme();
  themeToggle.addEventListener("click", () => {
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    // The new theme spreads out from the button. A View Transition snapshots
    // both states, so nothing on the page has to know it is being animated.
    if (!document.startViewTransition || reducedMotion) {
      setTheme(next);
      return;
    }
    const r = themeToggle.getBoundingClientRect();
    const x = r.left + r.width / 2;
    const y = r.top + r.height / 2;
    const end = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
    const transition = document.startViewTransition(() => setTheme(next));
    transition.ready.then(() => {
      root.animate(
        { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${end}px at ${x}px ${y}px)`] },
        { duration: 720, easing: "cubic-bezier(.65,0,.35,1)", pseudoElement: "::view-transition-new(root)" }
      );
    }).catch(() => { /* the swap already happened; only the reveal is lost */ });
  });
}

// --- Footer year ---
const year = document.getElementById("year");
if (year) year.textContent = new Date().getFullYear();

// --- Menu (narrow screens) ---
// The button sits before the menu in the DOM so Tab reaches the menu next.
const navToggle = $(".nav-toggle");
const menu = document.getElementById("nav-menu");

if (navToggle && menu) {
  const setOpen = (open, refocus = false) => {
    menu.classList.toggle("open", open);
    navToggle.setAttribute("aria-expanded", String(open));
    if (open) setTimeout(() => $("a", menu)?.focus(), 50);
    else if (refocus) navToggle.focus();
  };
  navToggle.addEventListener("click", () => setOpen(!menu.classList.contains("open")));
  menu.addEventListener("click", (e) => {
    if (e.target.closest("a")) setOpen(false);
  });
  // A disclosure has to be dismissible without choosing something, and focus
  // has to come back to the control that opened it.
  addEventListener("keydown", (e) => {
    if (e.key === "Escape" && menu.classList.contains("open")) setOpen(false, true);
  });
  addEventListener("pointerdown", (e) => {
    if (menu.classList.contains("open") && !menu.contains(e.target) && !navToggle.contains(e.target)) setOpen(false);
  });
}

// --- Scroll spy: highlight the nav link for the section in view ---
// Only the two home pages have a nav that points at sections of the same page.
const sections = $$("main section[id]");
const navLinks = new Map(
  menu
    ? $$("a[href]", menu)
        .map((a) => [a.getAttribute("href").split("#")[1], a])
        .filter(([id]) => id && document.getElementById(id))
    : []
);
if (navLinks.size) {
  const onScreen = new Set();
  const spy = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) onScreen.add(entry.target);
      else onScreen.delete(entry.target);
    });
    const current = sections.find((s) => onScreen.has(s));
    navLinks.forEach((a) => {
      a.classList.remove("active");
      a.removeAttribute("aria-current");
    });
    const link = current && navLinks.get(current.id);
    if (link) {
      link.classList.add("active");
      link.setAttribute("aria-current", "true");
    }
  }, { rootMargin: "-40% 0px -55% 0px" });
  sections.forEach((s) => spy.observe(s));
}

// --- The reading rail ---
// A line in the left gutter that fills with reading progress. Each section
// heading is a port on it, and lights when the fill reaches it. The rail runs
// from the first port (the name on the home page, the first heading on a case
// study) to the last heading.
const rail = $(".rail");
const header = $(".site-header");
const toTop = $(".to-top");
const SHADOW_AT = 8;
const TO_TOP_AT = 600;

const ports = $$("main .section").filter((s) => $(".section-title", s));
const startPort = $(".port-main") || (ports[0] && $(".section-title", ports[0]));
let railTop = 0;
let railHeight = 1;
let target = 0;
let shown = 0;
let frame = 0;

const pageY = (el) => el.getBoundingClientRect().top + scrollY;
const portY = (heading) => pageY(heading) + parseFloat(getComputedStyle(heading).fontSize) * 0.55;

const measureRail = () => {
  if (!rail || !startPort || !ports.length) return;
  const main = rail.offsetParent || document.body;
  const offset = pageY(main);
  railTop = startPort.classList.contains("port-main")
    ? pageY(startPort) + startPort.offsetHeight / 2
    : portY(startPort);
  ports.forEach((s) => { s.portY = portY($(".section-title", s)); });
  const last = ports[ports.length - 1].portY;
  railHeight = Math.max(1, last - railTop);
  rail.style.top = `${railTop - offset}px`;
  rail.style.height = `${railHeight}px`;
};

const progress = () => {
  const max = root.scrollHeight - innerHeight;
  return max > 0 ? Math.min(1, Math.max(0, scrollY / max)) : 0;
};

const paint = (p) => {
  root.style.setProperty("--p", p.toFixed(4));
  const tip = railTop + p * railHeight;
  ports.forEach((s) => s.classList.toggle("is-on", s.portY <= tip + 1));
};

const step = () => {
  frame = 0;
  // Eased toward the scroll position rather than pinned to it, so a wheel's
  // steps arrive as one smooth motion.
  shown += (target - shown) * 0.14;
  if (Math.abs(target - shown) < 0.0004) shown = target;
  paint(shown);
  if (shown !== target) frame = requestAnimationFrame(step);
};

const onScroll = () => {
  header?.classList.toggle("scrolled", scrollY > SHADOW_AT);
  toTop?.classList.toggle("show", scrollY > TO_TOP_AT);
  if (!rail || !ports.length) return;
  target = progress();
  if (reducedMotion) {
    shown = target;
    paint(shown);
  } else if (!frame) {
    frame = requestAnimationFrame(step);
  }
};
addEventListener("scroll", onScroll, { passive: true });

if ("ResizeObserver" in window && rail) {
  let queued = 0;
  new ResizeObserver(() => {
    cancelAnimationFrame(queued);
    queued = requestAnimationFrame(() => { measureRail(); onScroll(); });
  }).observe(document.body);
} else {
  addEventListener("resize", () => { measureRail(); onScroll(); });
}
measureRail();
onScroll();
addEventListener("load", () => { measureRail(); onScroll(); });

if (toTop) {
  toTop.addEventListener("click", () => {
    scrollTo({ top: 0, behavior: reducedMotion ? "auto" : "smooth" });
    // The button hides itself, and focus would otherwise fall back to <body>.
    document.getElementById("main")?.focus({ preventScroll: true });
  });
}

// --- Project chains ---
// Each selected project plays problem, approach, result once, when it first
// comes into view; hovering replays it (CSS).
const pipes = $$(".pipe");
if (pipes.length && "IntersectionObserver" in window && !reducedMotion) {
  const seen = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      seen.unobserve(entry.target);
      entry.target.classList.add("run");
      setTimeout(() => entry.target.classList.remove("run"), 2200);
    });
  }, { threshold: 0.6 });
  pipes.forEach((p) => seen.observe(p));
}

// --- Diagram notes ---
// A dotted label in a flowchart explains itself: the text is the <desc> inside the
// node's group. Pointer, keyboard and finger all reach it, and it stays until the
// reader moves away, because a note on a timer can vanish mid-sentence. The pointer
// can cross onto the note, so it never has to be read at a run. The diagrams are
// plain pictures until this runs, so without it nothing here promises a note.
const notedNodes = $$(".fig-flow-noted");
if (notedNodes.length) {
  const tip = document.createElement("div");
  tip.className = "fig-flow-note";
  tip.id = "fig-flow-note";
  tip.setAttribute("role", "tooltip");
  let current = null;
  let closing = 0;
  let lastPointer = "";

  const place = (node) => {
    const figure = node.closest(".figure");
    tip.textContent = node.querySelector("desc").textContent;
    figure.append(tip);
    const box = node.getBoundingClientRect();
    const frame = figure.getBoundingClientRect();
    const header = $(".site-header");
    const ceiling = header ? header.getBoundingClientRect().bottom : 0;
    const below = box.top - tip.offsetHeight - 12 < ceiling + 4;
    const middle = box.left + box.width / 2;
    const left = Math.min(Math.max(middle - tip.offsetWidth / 2, 8), innerWidth - tip.offsetWidth - 8);
    tip.classList.toggle("is-below", below);
    tip.style.left = `${left - frame.left}px`;
    tip.style.top = `${(below ? box.bottom + 12 : box.top - tip.offsetHeight - 12) - frame.top}px`;
    tip.style.setProperty("--caret", `${Math.min(Math.max(middle - left, 18), tip.offsetWidth - 18)}px`);
  };
  const hide = () => {
    clearTimeout(closing);
    if (!current) return;
    current.classList.remove("is-open");
    current.setAttribute("aria-expanded", "false");
    current.removeAttribute("aria-describedby");
    current = null;
    tip.classList.remove("is-on");
  };
  const show = (node) => {
    clearTimeout(closing);
    if (current === node) return;
    hide();
    current = node;
    node.classList.add("is-open");
    node.setAttribute("aria-expanded", "true");
    node.setAttribute("aria-describedby", tip.id);
    place(node);
    tip.classList.add("is-on");
  };
  const hideSoon = () => { clearTimeout(closing); closing = setTimeout(hide, 140); };

  // Inside role="img" a child cannot be a control, so a drawing with notes becomes a
  // labeled group of them. Its own <title> goes too, or the browser's tooltip for
  // the whole drawing would appear on top of the note.
  new Set(notedNodes.map((node) => node.ownerSVGElement)).forEach((svg) => {
    const title = svg.querySelector(":scope > title");
    const desc = svg.querySelector(":scope > desc");
    if (title) svg.setAttribute("aria-label", title.textContent);
    svg.removeAttribute("aria-labelledby");
    if (desc) svg.setAttribute("aria-describedby", desc.id);
    if (title) title.remove();
    svg.setAttribute("role", "group");
    [...svg.children].forEach((child) => {
      if (child !== desc && !child.classList.contains("fig-flow-noted")) child.setAttribute("aria-hidden", "true");
    });
  });

  notedNodes.forEach((node) => {
    node.setAttribute("role", "button");
    node.setAttribute("tabindex", "0");
    node.setAttribute("aria-expanded", "false");
    node.addEventListener("pointerenter", (e) => { if (e.pointerType === "mouse") show(node); });
    node.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse" && !node.matches(":focus-visible")) hideSoon(); });
    node.addEventListener("focus", () => { if (node.matches(":focus-visible")) show(node); });
    node.addEventListener("blur", () => { if (current === node) hideSoon(); });
    node.addEventListener("click", () => {
      if (lastPointer === "mouse") return;
      if (current === node) hide(); else show(node);
    });
    node.addEventListener("keydown", (e) => {
      if (e.key !== "Enter" && e.key !== " ") return;
      e.preventDefault();
      if (current === node) hide(); else show(node);
    });
  });
  tip.addEventListener("pointerenter", () => clearTimeout(closing));
  tip.addEventListener("pointerleave", hideSoon);
  addEventListener("pointerdown", (e) => {
    lastPointer = e.pointerType;
    if (current && !e.target.closest(".fig-flow-noted, .fig-flow-note")) hide();
  });
  addEventListener("keydown", (e) => { if (e.key === "Escape") hide(); });
  // A phone's address bar sliding away is a resize too, and must not close a note.
  let noteWidth = innerWidth;
  addEventListener("resize", () => {
    if (innerWidth !== noteWidth) hide();
    noteWidth = innerWidth;
  });
}

// --- Clip players ---
// The clips are ambient: each starts when it scrolls into view and stops when
// it leaves. One button governs the set, because auto-playing video has to
// offer a way to stop it. Stopping them hands the browser's controls back, so
// a halted clip becomes a player that can be scrubbed. Without this file the
// clips keep those controls from the start and the button stays hidden.
const clipFrames = $$(".clip-frame");
const clipsToggle = $(".clips-toggle");

if (clipFrames.length && clipsToggle) {
  const videos = clipFrames.map((f) => $("video", f)).filter(Boolean);
  const label = $("span", clipsToggle);
  const onScreen = new Set();
  // `manual` stops the next scroll pausing a clip the reader pressed play on;
  // `selfStarted` marks the starts apply() makes itself.
  const manual = new Set();
  const selfStarted = new Set();
  let running = !reducedMotion;

  videos.forEach((video) => {
    video.addEventListener("play", () => {
      if (selfStarted.has(video)) selfStarted.delete(video);
      else manual.add(video);
    });
  });

  const apply = () => {
    videos.forEach((video) => {
      video.controls = !running;
      if (manual.has(video)) return;
      if (running && onScreen.has(video)) {
        if (!video.paused) return;
        selfStarted.add(video);
        // Autoplay can be refused (a data saver, iOS low power mode).
        video.play().catch(() => selfStarted.delete(video));
      } else video.pause();
    });
    clipsToggle.classList.toggle("is-paused", !running);
    clipsToggle.setAttribute("aria-pressed", String(running));
    const text = running ? clipsToggle.dataset.pauseLabel : clipsToggle.dataset.playLabel;
    if (label && text) label.textContent = text;
  };

  clipsToggle.classList.add("is-ready");
  clipsToggle.addEventListener("click", () => {
    running = !running;
    manual.clear();
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
  }, { threshold: 0.33 });
  clipFrames.forEach((f) => watcher.observe(f));

  whenReducedMotion(() => {
    if (!running) return;
    running = false;
    manual.clear();
    apply();
  });

  apply();
}

// --- The opening ---
// Reveal first, decorate second. The home page waits at most 0.6s for the
// font, so the name can morph in its own letters; every other page starts at
// once. path.js listens for "opening" to play the diagram.
let opened = false;
const open = () => {
  if (opened) return;
  opened = true;
  root.classList.add("go");
  measureRail();
  onScroll();
  document.dispatchEvent(new Event("opening"));
};
if ($(".port-main")) {
  const cap = new Promise((r) => setTimeout(r, 600));
  Promise.race([document.fonts ? document.fonts.ready : cap, cap]).then(open, open);
  addEventListener("load", open);
} else {
  open();
}

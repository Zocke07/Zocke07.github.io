// The path diagram on the two home pages: lays the wires out from wherever the
// boxes land, plays the opening (a signal runs the path and each box lights as
// it arrives), sends a quiet pulse every few seconds while the diagram is on
// screen, and opens each box's details for a pointer, a keyboard or a finger.
// Loaded only by index.html and zh/index.html, after main.js.

(() => {
  const root = document.documentElement;
  const graph = document.querySelector(".graph");
  const path = document.querySelector(".path");
  if (!graph || !path) return;

  const svg = graph.querySelector(".graph-wires");
  const span = graph.querySelector(".span-mark");
  const reduce = matchMedia("(prefers-reduced-motion: reduce)");
  const spring = () => getComputedStyle(root).getPropertyValue("--spring").trim() || "ease-out";
  // Must match the @container path (min-width: 1000px) rule in style.css.
  const WIDE = 1000;

  const wraps = {};
  const nodes = {};
  graph.querySelectorAll(".step-wrap[data-id]").forEach((w) => {
    wraps[w.dataset.id] = w;
    nodes[w.dataset.id] = w.querySelector(".step-node");
  });
  const EDGES = [
    ["origin", "bachelor"], ["bachelor", "sunbird"], ["bachelor", "master"],
    ["sunbird", "taiwanmobile"], ["taiwanmobile", "next"], ["master", "next"],
  ].filter(([a, b]) => nodes[a] && nodes[b]);
  const HOT = new Set(["taiwanmobile>next", "master>next"]);
  const TRACKS = [
    ["origin", "bachelor", "sunbird", "taiwanmobile", "next"],
    ["origin", "bachelor", "master", "next"],
  ];
  const ORDER = ["origin", "bachelor", "sunbird", "master", "taiwanmobile", "next"];
  if (!svg || !EDGES.length) return;

  const NS = "http://www.w3.org/2000/svg";
  const wires = {};
  EDGES.forEach(([a, b]) => {
    const p = document.createElementNS(NS, "path");
    p.setAttribute("class", HOT.has(`${a}>${b}`) ? "wire is-hot" : "wire");
    p.setAttribute("pathLength", "1");
    svg.appendChild(p);
    wires[`${a}>${b}`] = p;
  });

  let wide = false;
  let tracks = [];

  // Offsets rather than bounding boxes: a box lifted on hover, or still
  // mid-entrance, must not drag its wires with it.
  const box = (id) => {
    const w = wraps[id];
    const n = nodes[id];
    return { x: w.offsetLeft + n.offsetLeft, y: w.offsetTop + n.offsetTop, w: n.offsetWidth, h: n.offsetHeight };
  };
  const portOut = (id) => {
    const b = box(id);
    return wide ? [b.x + b.w, b.y + b.h / 2] : [b.x + b.w / 2, b.y + b.h];
  };
  const portIn = (id) => {
    const b = box(id);
    return wide ? [b.x, b.y + b.h / 2] : [b.x + b.w / 2, b.y];
  };
  const curve = ([ax, ay], [bx, by]) => {
    if (wide) {
      const dx = Math.max(16, (bx - ax) / 2);
      return `M${ax} ${ay} C${ax + dx} ${ay} ${bx - dx} ${by} ${bx} ${by}`;
    }
    const dy = Math.max(14, (by - ay) / 2);
    return `M${ax} ${ay} C${ax} ${ay + dy} ${bx} ${by - dy} ${bx} ${by}`;
  };

  const layout = () => {
    wide = path.clientWidth >= WIDE;
    const w = graph.offsetWidth;
    const h = graph.offsetHeight;
    svg.setAttribute("width", w);
    svg.setAttribute("height", h);
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    EDGES.forEach(([a, b]) => wires[`${a}>${b}`].setAttribute("d", curve(portOut(a), portIn(b))));
    // A pulse track runs along the wires and straight through each box, so the
    // signal visibly goes in one side and out the other.
    tracks = TRACKS.filter((ids) => ids.every((id) => nodes[id])).map((ids) => {
      let d = "";
      for (let i = 0; i < ids.length - 1; i++) {
        const a = portOut(ids[i]);
        const seg = curve(a, portIn(ids[i + 1]));
        d += i === 0 ? seg : ` L${a[0]} ${a[1]}${seg.replace(/^M[^C]+/, " ")}`;
      }
      return d;
    });
    if (wide && span && nodes.sunbird && nodes.taiwanmobile) {
      const s = box("sunbird");
      const t = box("taiwanmobile");
      span.style.left = `${s.x}px`;
      span.style.width = `${t.x + t.w - s.x}px`;
    }
  };

  // --- The opening ---
  const flash = (n, delay) => {
    try {
      n.animate([{ opacity: 0 }, { opacity: 1, offset: 0.3 }, { opacity: 0 }],
        { duration: 1100, delay, easing: "ease-out", pseudoElement: "::after" });
    } catch (e) { /* no pseudo-element animation here: skip the ring */ }
  };

  const play = () => {
    // Constant speed, so the signal reads as one continuous flow.
    const SPEED = wide ? 340 : 260;
    const HOLD = 0.16;
    const at = { origin: 1.0 };
    ORDER.forEach((id) => {
      EDGES.forEach(([a, b]) => {
        if (a !== id) return;
        const wire = wires[`${a}>${b}`];
        const t0 = at[a] + HOLD;
        const dur = Math.max(0.12, wire.getTotalLength() / SPEED);
        wire.animate([{ strokeDashoffset: 1 }, { strokeDashoffset: 0 }],
          { duration: dur * 1000, delay: t0 * 1000, easing: "linear", fill: "backwards" });
        const head = document.createElement("i");
        head.className = "sig-head";
        head.style.offsetPath = `path("${wire.getAttribute("d")}")`;
        graph.appendChild(head);
        head.animate([{ offsetDistance: "0%", opacity: 1 }, { offsetDistance: "100%", opacity: 1 }],
          { duration: dur * 1000, delay: t0 * 1000, easing: "linear" }).onfinish = () => head.remove();
        at[b] = Math.max(at[b] || 0, t0 + dur);
      });
    });
    Object.keys(nodes).forEach((id) => {
      const t = ((at[id] ?? 1) - 0.05) * 1000;
      nodes[id].animate([{ opacity: 0, transform: "translateY(8px) scale(.94)" }, { opacity: 1, transform: "none" }],
        { duration: 760, delay: t, easing: spring(), fill: "backwards" });
      flash(nodes[id], t + 40);
    });
    if (wide && span) {
      span.animate([{ opacity: 0, transform: "scaleX(.6)" }, { opacity: 1, transform: "none" }],
        { duration: 700, delay: ((at.taiwanmobile ?? 2) + 0.2) * 1000, easing: "cubic-bezier(.16,1,.3,1)", fill: "backwards" });
    }
    return at.next ?? 2.5;
  };

  // --- Ambient: one quiet pulse every few seconds, only while visible ---
  let visible = true;
  let beat = 0;
  if ("IntersectionObserver" in window) {
    new IntersectionObserver((es) => { visible = es[0].isIntersecting; }, { threshold: 0.25 }).observe(graph);
  }
  const pulse = () => {
    if (reduce.matches || document.hidden || !visible || !tracks.length) return;
    const s = document.createElement("i");
    s.className = "sig";
    s.style.offsetPath = `path("${tracks[beat++ % tracks.length]}")`;
    graph.appendChild(s);
    s.animate(
      [{ offsetDistance: "0%", opacity: 0 }, { opacity: 1, offset: 0.06 }, { opacity: 1, offset: 0.92 }, { offsetDistance: "100%", opacity: 0 }],
      { duration: 2800, easing: "cubic-bezier(.45,0,.55,1)" }
    ).onfinish = () => { s.remove(); if (nodes.next) flash(nodes.next, 0); };
  };

  // --- Pointer, keyboard and touch ---
  const light = (id) => {
    graph.classList.add("is-focus");
    wraps[id].classList.add("is-lit");
    EDGES.forEach(([a, b]) => {
      if (a !== id && b !== id) return;
      wires[`${a}>${b}`].classList.add("is-lit");
      wraps[a === id ? b : a].classList.add("is-near");
    });
  };
  const unlight = () => {
    graph.classList.remove("is-focus");
    graph.querySelectorAll(".is-lit, .is-near").forEach((x) => x.classList.remove("is-lit", "is-near"));
  };
  const openId = () => graph.querySelector(".step-wrap.is-open")?.dataset.id ?? null;
  const setOpen = (id) => {
    Object.keys(wraps).forEach((k) => {
      wraps[k].classList.toggle("is-open", k === id);
      nodes[k].setAttribute("aria-expanded", String(k === id));
    });
    unlight();
    if (id) light(id);
  };
  Object.keys(wraps).forEach((id) => {
    const w = wraps[id];
    w.addEventListener("pointerenter", (e) => { if (e.pointerType === "mouse" && !openId()) light(id); });
    w.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse" && !openId()) unlight(); });
    w.addEventListener("focusin", () => { if (!openId()) light(id); });
    w.addEventListener("focusout", (e) => { if (!w.contains(e.relatedTarget) && !openId()) unlight(); });
    nodes[id].addEventListener("click", () => setOpen(openId() === id ? null : id));
  });
  document.addEventListener("click", (e) => { if (openId() && !graph.contains(e.target)) setOpen(null); });
  addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const id = openId();
    if (id) {
      setOpen(null);
      nodes[id].focus();
    }
  });

  // --- Keep the wires on the boxes as the page changes size ---
  if ("ResizeObserver" in window) {
    let queued = 0;
    new ResizeObserver(() => {
      cancelAnimationFrame(queued);
      queued = requestAnimationFrame(layout);
    }).observe(graph);
  } else {
    addEventListener("resize", layout);
  }
  layout();

  // --- Start when main.js opens the page ---
  let started = false;
  const start = () => {
    if (started) return;
    started = true;
    layout();
    if (reduce.matches || !graph.animate) return;
    try {
      const done = play();
      setTimeout(function tick() { pulse(); setTimeout(tick, 6500); }, (done + 1.6) * 1000);
    } catch (e) {
      /* the diagram is already drawn in full; only the motion is lost */
    }
  };
  if (root.classList.contains("go")) start();
  else document.addEventListener("opening", start, { once: true });
})();

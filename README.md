# Portfolio: Rivan Wong

Personal portfolio site, built with plain HTML/CSS/JS (no framework, no build step)
and served directly from the repository root on GitHub Pages.

## Structure

```
index.html                       # landing page, one <section> per CV area
case-study-test-automation.html  # long-form case studies, linked from Experience
case-study-agentbase.html
case-study-ai-products.html
case-study-capstone.html
case-study-event-courier.html
case-study-lmad.html
case-study-makerspace.html
case-study-microprocessors.html
case-study-sky-scraper-escape.html
case-study-url-shortener.html
project-mobile-testing.html      # project notes, same layout as a case study
404.html                         # served for every bad URL, in both languages
sitemap.xml                      # generated; see tools/sitemap.py
robots.txt
zh/                              # Traditional Chinese twin of every page above
assets/
  css/style.css                  # design tokens + numbered per-component sections
  fonts/recursive.woff2          # the one web font, subset; OFL.txt beside it
  js/main.js                     # theme switch, menu, reading rail, clips, the opening
  js/path.js                     # the home page's path diagram, home pages only
  img/                           # in-page figures and the portrait
  img/og/                        # 1200x630 social cards, <slug>.png and <slug>-zh.png
  cv/rivan-wong-cv.pdf           # copy of CV/build/cv.pdf, see below
tools/serve.py                   # local preview, resolves URLs like GitHub Pages
tools/check.py                   # sixteen regression checks; run before every commit
tools/bump.py                    # stamps ?v= from a hash of the asset
tools/diff.py                    # git diff with the ?v= stamp churn filtered out
tools/cv.py                      # refreshes the CV copy from CV/build
tools/og.py                      # renders a page's social card from its own metadata
tools/sitemap.py                 # rebuilds sitemap.xml from the pages' own canonicals
tools/cjk.py                     # unwraps Chinese lines that would render a stray space
tools/og-cards.json              # generated; what each social card was drawn from
.githooks/pre-commit             # runs tools/check.py before a commit is written
.github/workflows/check.yml      # runs tools/check.py and node --check on every push
```

## URLs

GitHub Pages serves `foo.html` at `/foo`, so every page has a clean URL and the
site links to that form:

| Page                    | URL                     |
| ----------------------- | ----------------------- |
| `index.html`            | `/`                     |
| `case-study-lmad.html`  | `/case-study-lmad`      |
| `zh/index.html`         | `/zh/`                  |
| `zh/case-study-lmad.html` | `/zh/case-study-lmad` |

The `.html` forms still resolve, so older links keep working. Each page carries a
`<link rel="canonical">` naming its clean URL, so the two forms are not treated
as competing pages.

All in-page paths are root-relative (`/assets/...`, `/case-study-lmad`), which
keeps them identical from `/` and from `/zh/`. That ties the site to a domain
root, which is what it is: the repository is named `<username>.github.io`, so
it is a GitHub Pages *user site*. Serving it from a project-site subpath would
mean rewriting those paths.

Because links omit `.html`, a plain `python3 -m http.server` would 404 on them.
Use the preview server below instead.

## Both languages

Every page ships twice: `page.html` in English and `zh/page.html` in Traditional
Chinese. The pairing is asserted in four places, and all four have to stay in
step when a page is added or renamed:

- the `.lang-toggle` anchor in the header,
- the `<link rel="alternate" hreflang="...">` tags, three per page: `en`,
  `zh-Hant-TW` and `x-default`,
- `<link rel="canonical">`,
- `og:url`, which is absolute and language-specific.

The `alternates` check asserts the middle two against each other: each page's
canonical has to name that page, and both twins have to publish the same
alternate block naming each twin by the URL that twin claims for itself. That
is not something `sitemap` can cover, because `tools/sitemap.py` reads those
same canonicals as ground truth, so a wrong one is copied faithfully into the
expected output and the comparison still passes.

The header, footer and back-to-top wording must also stay identical *within* a
language. Seven of those strings had drifted into two spellings across the
Chinese pages before `tools/check.py` started asserting it.

The two files share `style.css`, `main.js` and `path.js`. Strings the JS needs
come from the markup (the theme switch reads `data-label-dark` and
`data-label-light`), so the scripts hold no English or Chinese text and neither
copy has its own script.

Language survives navigation: every link inside a Chinese page points at another
Chinese page, and the toggle swaps to the same page in the other language rather
than returning to the home page.

**Chinese paragraphs go on one line, however long.** HTML turns a newline in the
source into a space. Between two English words that is what you want, which is
why the English pages wrap freely; between two Chinese characters there is no
space to represent and the browser inserts one anyway. It had done so in 128
places, and the same hard wrap had also cut `NVIDIA` and `GUI` in half, so the
home page read "NVIDI A Jetson TX2". `tools/cjk.py` finds and joins these, and
`tools/check.py` fails if one comes back. Breaking between a Chinese character
and a Latin one is fine: that space is wanted, and the pages already write it.

## Editing content

All landing-page content lives in `index.html`, in commented sections: Intro,
Path, Selected work, Experience, About, Education, Skills, Languages and
Contact. Mirror every edit into `zh/index.html`.

**The path diagram** under the intro is six boxes, each a `<button
class="step-node">` inside a `.step-wrap` with a `data-id`, followed by the
`.step-more` panel it opens. `assets/js/path.js` draws the wires from wherever
the boxes land, so moving a box is a CSS change (`grid-area` per `data-id`) and
a new box needs its id added to `EDGES` and `TRACKS` there. The boxes use plain
words; the technical detail, with a short gloss, goes in the panel.

**Selected work** is six projects, each an `<article class="pipe">`: a title,
an origin line in plain words, tool chips, a visible "Read the case study" link
and a three-step chain (Problem, Approach, Result), one short sentence each,
drawn from the case study itself. Everything else goes in the three groups
under it, one line each, grouped by the reader they serve: Testing and
quality, Built for real users, Closer to the hardware. A project joins the six
only by displacing one.

**Experience and Education** are `<li class="entry">` items in an
`<ol class="entries">`: date first, then the role, the organization, an intro
and bullets. Each entry is a branch off the reading rail.

A card's title says what the project is, and the page it opens is free to lead
with a headline instead: "KITA Liturgi: A Guide for Altar Servers and Lectors"
on the home page, "Count Backwards From the Fixed Point" on the page. The
obligation runs the other way: the page must name what its card promised in its
first lines (the summary strip, the lead or the role line), so a click lands
where it said it would.

A skill tag in the Skills section is a link when a case study demonstrates it
and plain text when none does, and only the linked ones lift on hover. The bar
for appearing at all is code he wrote, which is why VHDL, FPGA, embedded Linux
and kernel modules sit in their own labeled group, "From team coursework",
linking once to the lab notebook instead of each tag: the microprocessors page
says in its own words that the labs were team work. AgentBase never backs a tag
either: an AI agent wrote its code, and the page says so. Before adding a link,
check the destination actually discusses the skill, and that the page
attributes it to him.

**Copy conventions**, beyond US spelling and straight apostrophes: labels and
buttons in sentence case, no ALL-CAPS eyebrow labels, no meta strings joined
with middle dots (use a comma or a definition list), no arrows on links (a link
says where it goes; `tools/check.py copy` enforces this in both languages), and
no em dashes anywhere.

### Case-study pages: four formats, one summary strip

Every case-study page opens with the same `<dl class="summary">`: format,
project, tools, dates, and the code link or why there is none. Then the
headline, the lead, the role line, the key numbers and the scope note. The body
takes one of four shapes, chosen by the kind of project rather than by habit:

| Format | Signature piece | Pages |
| --- | --- | --- |
| Case study | problem, what I did, result, what I would change | L-MAD, test infrastructure, AI products, AgentBase, capstone |
| Design notes | a `table.decision`: the options weighed, the chosen row marked | URL shortener, makerspace, KITA Liturgi, Sky Scraper Escape |
| Report | a `table.findings`: finding, exposure, fix, test (or a test summary) | event app, mobile testing |
| Lab notebook | the labs as an `ol.timeline`, the milestone marked `is-key` | microprocessors |

Every table is written from its page's own text. A finding has no severity
column unless the page itself rates severity.

### The design system

Colors, type, spacing and motion are custom properties at the top of
`assets/css/style.css`: `:root` for the light theme (drafting paper, graphite
ink), `:root[data-theme="dark"]` for the dark one (warm charcoal), one orange
(`--acc`) that means "live" in both. Every text color clears 4.5:1 and every
wire and box edge 3:1; `prefers-contrast: more` and `forced-colors` are
handled. Diagrams inside pages draw from the same tokens (`var(--acc)`,
`var(--edge)`, `var(--mut)`), so they follow the theme.

The only web font is Recursive (SIL Open Font License, `assets/fonts/OFL.txt`),
self-hosted as one 68 KB subset with two axes: weight, and MONO, which the
intro animates and code chips use. The casual axis is pinned at 0, which halved
the file. Chinese uses the system faces, so the Chinese pages download no font
beyond the Latin one.

Motion follows one rule: one orchestrated moment, then only what answers the
reader. On the home page the name morphs from code-style letters into the
normal face and a signal runs the path diagram, each box lighting as it
arrives. After that: a quiet pulse every 6.5 seconds while the diagram is on
screen, a reading rail that fills as you scroll and lights each section's port,
project chains that play once when they come into view, and a theme switch
that spreads from the button. Arrivals spring (`--spring`, CSS `linear()` with a
`cubic-bezier` fallback), flows run at a constant rate, exits are quicker than
entrances. Nothing is hidden unless scripts run, never for more than two
seconds (a CSS failsafe reveals everything), and `prefers-reduced-motion`
removes all of it.

Case-study pages reuse the same stylesheet, and no page carries a `<style>`
block of its own. Prefer a modifier (`.figure.is-loose`, `.backdrop.is-short`)
over redefining a shared class, so a class means one thing across the site.

`style.css`, `main.js` and `path.js` are linked as `?v=<hash>`, where the hash
comes from the file itself. Run `python3 tools/bump.py` after changing any of
them; it rewrites every page, and `tools/check.py` fails if a stamp is stale.
`path.js` is optional: only the two home pages load it.

That restamp touches every page whether or not it changed anything else,
which buries a real edit in noise. `python3 tools/diff.py` is `git diff` with
those stamp-only hunks dropped; it takes the same arguments (`--stat`,
`HEAD~1 HEAD`, a path). A page with a genuine edit still shows in full.

## Social cards

Each page points `og:image` at its own 1200x630 card in `assets/img/og/`:
`<slug>.png` in English, `<slug>-zh.png` in Chinese. All of them are drawn by
one script in the site's dark theme: warm charcoal, the dot grid, the orange
format line, the title, a wire, the description, and the ring with the name.

```sh
python3 tools/og.py --all            # every card, both languages
python3 tools/og.py zh/index.html    # just one
python3 tools/og.py --check          # used by tools/check.py
```

The text comes out of the page itself: the summary strip's format and project,
plus `og:title` and `og:description`, so a card cannot drift from what it
illustrates. The home card is the exception and carries its own two lines,
because the home page has no summary strip.

A rendered PNG is not reproducible byte for byte, so the staleness check
compares the text a card was drawn from instead, recorded in
`tools/og-cards.json` when it was last rendered. An edit to an `og:title` or a
summary strip fails the `cards` check until the card is redrawn.

`tools/check.py` fails if a Chinese page points at an English card.

## Search engines

`sitemap.xml` is generated, not written:

```sh
python3 tools/sitemap.py            # rebuild
python3 tools/sitemap.py --check    # used by tools/check.py
```

Each URL is read out of that page's own `<link rel="canonical">` and its
hreflang alternates out of its `<link rel="alternate">`, so the sitemap cannot
name a URL the page disagrees with. Hand-maintaining it would have been a fifth
place to remember when a page is added, next to the four above.

There is no `<lastmod>`, `<changefreq>` or `<priority>`. The latter two are
ignored, and a lastmod that is only the file's mtime claims a freshness nobody
verified. It also keeps the file stable, so a diff here means a page was added
or removed and nothing else.

Both home pages carry a `schema.org/Person` JSON-LD block. Everything in it is
also stated in the page body; it must not become the only place a claim lives.

`404.html` ships in one copy on purpose. GitHub Pages serves the root 404 for
every bad URL on the site, `/zh/` ones included, so there is no second file to
keep in step and it says its piece in both languages. `tools/check.py` knows
this through its `SINGLETON` set, which is what exempts it from `parity` and
`og` while still holding it to `structure`, `links`, `chrome` and `copy`.

## Preview locally

```sh
python3 tools/serve.py        # http://127.0.0.1:8000
python3 tools/serve.py 8080   # or pick a port
```

It is `http.server` with one added rule: a URL with no extension falls back to
`name.html`, then `name/index.html`, which is the order GitHub Pages tries. That
makes the preview resolve `/case-study-lmad` the way the deployed site does. It
binds to `127.0.0.1`, so the preview stays off the local network, and sends
`Cache-Control: no-store`, so an edit shows up on reload.

If the port is busy, either stop whatever holds it
(`lsof -nP -iTCP:8000 -sTCP:LISTEN`) or pass another one.

## Deploy

Pushes to `main` publish automatically once GitHub Pages is enabled:

1. In the repo: **Settings → Pages → Build and deployment**.
2. Source: **Deploy from a branch**, Branch: **main**, Folder: **/ (root)**.
3. Push. The site appears at <https://zocke07.github.io/>.

## Checks

```sh
python3 tools/check.py            # all sixteen
python3 tools/check.py links      # or just one
```

| check | asserts |
| --- | --- |
| `structure` | tag balance, no duplicate ids, one `<h1>`, no skipped heading levels, no malformed markup |
| `links` | every internal URL resolves on disk, absolute `og:image` and canonical forms included |
| `alternates` | each pair's `canonical` and three `hreflang` values agree in both directions |
| `parity` | each English page and its Chinese twin share an identical `id=` and `class=` sequence, in `<main>`, `<header>` and `<footer>` |
| `chrome` | seven shared strings are identical within each language, and present on every page |
| `css` | `style.css` braces and comment markers balance |
| `deadcss` | no class is declared in `style.css` without a user, or used in markup without `style.css` or `main.js` defining it |
| `assets` | every tracked file under `assets/` is referenced by some page |
| `tracked` | git tracks nothing outside the published site |
| `stamps` | every `?v=` matches the hash of the file it points at (`path.js` only where a page loads it) |
| `cv` | `assets/cv/rivan-wong-cv.pdf` still matches `CV/build/cv.pdf` |
| `og` | each page points at its own card and declares the right `og:locale` |
| `cards` | each social card still matches the page metadata it was drawn from |
| `copy` | English prose keeps one spelling and punctuation convention; no link in either language carries an arrow |
| `sitemap` | `sitemap.xml` still matches the pages' own canonical URLs |
| `cjk` | no Chinese line break renders as a stray space |

`parity` is the one worth understanding: it is what catches a change made to one
language and forgotten in the other. It compares structure, not prose, so the
Chinese text being shorter does not trip it.

Two of these are about the suite's own blind spots rather than the site's.
`tracked` asserts the repository manifest, because every other check scopes
itself to pages and assets it already knows about and so would pass on a commit
that staged an entire unrelated tree. `css` and the CI step that runs
`node --check assets/js/main.js` cover the two files nothing else parses: a
missing brace in either ships green otherwise, and takes the stylesheet or every
behaviour on the site with it.

The suite runs in about a third of a second, which is cheap enough to gate a
commit. GitHub Pages deploys the branch directly and concurrently with Actions,
so the workflow reports on a broken page after it is live; `.githooks/pre-commit`
is the gate that runs first. Switch it on once per clone:

```sh
git config core.hooksPath .githooks
```

`copy` holds the English pages to one convention: American spelling (defense,
center, -ize) and straight apostrophes. Six strays had accumulated, one of them
a page spelling the same claim two different ways.

## The CV

The hero and the contact section link `assets/cv/rivan-wong-cv.pdf`, which is a
**copy** of `CV/build/cv.pdf`, not a reference to it.

It has to be a copy. `CV/` is a separate git repository with its own remote, so
git treats it as a submodule boundary and will not track files inside it as
ordinary files. Un-excluding it would not help.

After rebuilding the CV:

```sh
python3 tools/cv.py          # refresh the copy
```

`tools/check.py` compares the two and fails when they differ, so a stale copy
cannot ship quietly. On a fresh clone or in CI there is no `CV/` to compare
against, and the check passes on the copy in the repo.

One local trap worth knowing: `.git/info/exclude` lists `/CV/` with a leading
slash. Without it the pattern also matched `assets/cv/`, because macOS sets
`core.ignorecase`, and the PDF silently refused to stage.

## Ideas for later

- Serve both languages from one URL. Worth revisiting only if editing two files
  becomes the real bottleneck: switching language already keeps your place, and
  the current split is what makes each language separately indexable.

## When to move to a framework

Deliberately none today. The site is 27 pages on one stylesheet and two
scripts, with no dependencies and no build step: `git push` deploys it, and it
will still build untouched in five years. The home page's first visit costs
about 32 KB gzipped of HTML, CSS and JS over zero external requests, plus the
68 KB font and the 71 KB portrait. (`style.css` and `main.js` are 18 KB gzipped
of that and shared, and the font is cached once, so every page after the first
costs only its own HTML.)

What that costs is real and worth naming: the head, header, footer and
back-to-top blocks are repeated on every page, about a third of all HTML in the
repo. `404.html` carries the full nav too, so adding a nav item is twenty-seven
edits; the redesign did it with a one-off script.

If that stops being worth it, the answer is **Astro**, not React or Vue. It
ships zero JavaScript by default and outputs static HTML to the same GitHub
Pages, so nothing above is traded away; a layout would erase the repeated
chrome, its i18n routing would compute the four bilingual sync points instead of
restating them, and `astro:assets` would hash filenames and generate WebP, which
retires `tools/bump.py` and the image-optimisation step. React or Vue would
spend a runtime bundle and hydration to render pages that are entirely static
prose, and would be slower on the phone a recruiter actually reads this on.

Migrate when any one of these is true:

1. A third language is added.
2. Unique page count passes about 12. It is 13 now, and the November 2026
   redesign weighed Astro and stayed with plain HTML: migrating would have been a
   second project during interviews, and visitors would not have seen a
   difference. The trigger still stands for the next large change.
3. Case studies would be better authored in Markdown than in hand-written HTML.
4. You catch yourself avoiding a change because of how many files it touches.

# Portfolio: Rivan Wong

Personal portfolio site, built with plain HTML/CSS/JS (no framework, no build step)
and served directly from the repository root on GitHub Pages.

## Structure

```
index.html                       # landing page, one <section> per CV area
case-study-test-automation.html  # long-form case studies, linked from Experience
case-study-ai-products.html
case-study-capstone.html
case-study-lmad.html
case-study-microprocessors.html
case-study-sky-scraper-escape.html
project-mobile-testing.html      # project notes, same layout as a case study
404.html                         # served for every bad URL, in both languages
sitemap.xml                      # generated; see tools/sitemap.py
robots.txt
zh/                              # Traditional Chinese twin of every page above
assets/
  css/style.css                  # design tokens + numbered per-component sections
  js/main.js                     # theme toggle, reveal-on-scroll, rotator, nav
  img/                           # in-page figures and the portrait
  img/og/                        # 1200x630 social cards, <slug>.png and <slug>-zh.png
  cv/rivan-wong-cv.pdf           # copy of CV/build/cv.pdf, see below
tools/serve.py                   # local preview, resolves URLs like GitHub Pages
tools/check.py                   # sixteen regression checks; run before every commit
tools/bump.py                    # stamps ?v= from a hash of the asset
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

The two files share `style.css` and `main.js`. Strings the JS needs come from
`data-` attributes in the markup (the hero rotator reads `data-phrases`), so
`main.js` holds no English or Chinese text and neither copy has its own script.

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

All landing-page content lives in `index.html`, organized into clearly commented
sections (Hero, About, Education, Experience, Projects, Skills, Contact). To add
an entry, copy an existing `<article class="entry">` (experience/education) or
`<article class="card">` (projects) block and edit the text. Mirror the same edit
into `zh/index.html`.

A skill tag in the Skills section is a link when a case study demonstrates it
and plain text when none does, and the hover lift belongs to the linked ones
only. It used to sit on every tag and promise a click that none could honor.

The bar for appearing at all is code he wrote. That is why there is no VHDL,
FPGA, Embedded Linux or Digital Logic Design here: their only evidence is the
microprocessors page, which says in its own words that nothing on it is offered
as his own work. They stay on that project's card, where the page explains the
group work around them. TypeScript went for the same reason, the AI products
page calling the product "the team's build"; it stays on that project's card,
where it names what the product was made of rather than what he wrote.

Before adding a link, check the destination actually discusses the skill, and
that the page attributes it to him.

Colors, fonts, and spacing are CSS custom properties at the top of
`assets/css/style.css` (`:root` for light mode, `:root[data-theme="dark"]`
for dark mode). A header toggle switches themes and remembers the choice.
All animations are disabled automatically for visitors who set
`prefers-reduced-motion`.

Case-study pages reuse the same stylesheet, and no page carries a `<style>`
block of its own. Section 11 holds every rule the long-form pages share,
including the `.figure` / `.fig-*` classes and the `.figure-doc` exhibit panel;
section 11b holds the components used by exactly one page and its Chinese twin
(the capstone chart, the thesis results table, the mobile-testing partition
table). Page-local CSS lived in the pages until the two copies of it drifted,
which is why it is here instead: one definition serves both languages.

Prefer a modifier (`.figure.is-loose`, `.figure-doc.is-wide`) over redefining a
shared class, so a class means one thing across the site. The raised-panel
chrome (border, radius, ground, shadow) comes from one shared selector list at
the top of section 11; a new panel joins that list rather than restating it.

`style.css` and `main.js` are linked as `?v=<hash>`, where the hash comes from
the file itself. Run `python3 tools/bump.py` after changing either one; it
rewrites all 17 pages, and `tools/check.py` fails if a stamp is stale. It used
to be a counter bumped by hand in 32 places.

## Social cards

Each page points `og:image` at its own 1200x630 card in `assets/img/og/`:
`<slug>.png` in English, `<slug>-zh.png` in Chinese. They share one template:
dark background, blue kicker, title, rule, two-line description, and the `RW`
badge with the name.

The Chinese cards are generated:

```sh
python3 tools/og.py                  # every Chinese page
python3 tools/og.py zh/index.html    # just one
python3 tools/og.py --check          # used by tools/check.py
```

The text comes out of the page itself, the hero kicker plus `og:title` and
`og:description`, so a card cannot drift from what it illustrates. The home card
is the exception and carries its own two lines, because its kicker is a location
and its description is a tagline, neither of which is card copy.

The English cards were drawn by hand before the generator existed and are close
but not identical to what it produces, so `tools/og.py` leaves them alone unless
`--all` is passed. Its palette and geometry were measured off `og/lmad.png`, so
the two sets sit in the same family.

A rendered PNG is not reproducible byte for byte, so the staleness check
compares the text a card was drawn from instead, recorded in
`tools/og-cards.json` when it was last rendered. That covers the hand-drawn
English cards too: `--record` adopts what is already in the repo without
re-rendering it, and after that an edit to an `og:title` fails the `cards`
check until the card is redrawn.

`tools/check.py` fails if a Chinese page points at an English card, which is
what it did for all eight of them until now.

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
| `chrome` | six shared strings are identical within each language, and present on every page |
| `css` | `style.css` braces and comment markers balance |
| `deadcss` | no class is declared in `style.css` without a user, or used in markup without `style.css` or `main.js` defining it |
| `assets` | every tracked file under `assets/` is referenced by some page |
| `tracked` | git tracks nothing outside the published site |
| `stamps` | every `?v=` matches the hash of the file it points at |
| `cv` | `assets/cv/rivan-wong-cv.pdf` still matches `CV/build/cv.pdf` |
| `og` | each page points at its own card and declares the right `og:locale` |
| `cards` | each social card still matches the page metadata it was drawn from |
| `copy` | English prose keeps one spelling and punctuation convention |
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

- Add a LinkedIn link once there is something on the profile worth linking.
- Serve both languages from one URL. Worth revisiting only if editing two files
  becomes the real bottleneck: switching language already keeps your place, and
  the current split is what makes each language separately indexable.

## When to move to a framework

Deliberately none today. The site is 16 pages on one stylesheet and one script,
with no dependencies and no build step: `git push` deploys it, the first visit
costs 24 to 35 KB gzipped of HTML, CSS and JS over zero external requests, plus
one 71 KB portrait on the home page, and it will still build untouched in five
years. (`style.css` and `main.js` are 17 KB gzipped of that and are shared, so
every page after the first costs only its own HTML.)

What that costs is real and worth naming: the head, header, footer and
back-to-top blocks are repeated on every page. Measured, 68 distinct lines
appear on 16 or more of the 17 pages, for 2,389 line-instances, about 32% of all
HTML in the repo. `404.html` carries the full nav too, so adding a nav item is
seventeen edits.

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
2. Unique page count passes about 12 (it is 8 now).
3. Case studies would be better authored in Markdown than in hand-written HTML.
4. You catch yourself avoiding a change because of how many files it touches.

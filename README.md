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
zh/                              # Traditional Chinese twin of every page above
assets/
  css/style.css                  # design tokens + numbered per-component sections
  js/main.js                     # theme toggle, reveal-on-scroll, rotator, nav
  img/                           # in-page figures and the portrait
  img/og/                        # 1200x630 social cards, <slug>.png and <slug>-zh.png
  cv/rivan-wong-cv.pdf           # copy of CV/build/cv.pdf, see below
tools/serve.py                   # local preview, resolves URLs like GitHub Pages
tools/check.py                   # eight regression checks; run before every commit
tools/bump.py                    # stamps ?v= from a hash of the asset
tools/cv.py                      # refreshes the CV copy from CV/build
tools/og.py                      # renders a page's social card from its own metadata
.github/workflows/check.yml      # runs tools/check.py on every push
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
- the `<link rel="alternate" hreflang="...">` tags,
- `<link rel="canonical">`,
- `og:url`, which is absolute and language-specific.

The header, footer and back-to-top wording must also stay identical *within* a
language. Seven of those strings had drifted into two spellings across the
Chinese pages before `tools/check.py` started asserting it.

The two files share `style.css` and `main.js`. Strings the JS needs come from
`data-` attributes in the markup (the hero rotator reads `data-phrases`), so
`main.js` holds no English or Chinese text and neither copy has its own script.

Language survives navigation: every link inside a Chinese page points at another
Chinese page, and the toggle swaps to the same page in the other language rather
than returning to the home page.

## Editing content

All landing-page content lives in `index.html`, organized into clearly commented
sections (Hero, About, Education, Experience, Projects, Skills, Contact). To add
an entry, copy an existing `<article class="entry">` (experience/education) or
`<article class="card">` (projects) block and edit the text. Mirror the same edit
into `zh/index.html`.

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
rewrites all 16 pages, and `tools/check.py` fails if a stamp is stale. It used
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
```

The text comes out of the page itself, the hero kicker plus `og:title` and
`og:description`, so a card cannot drift from what it illustrates. The home card
is the exception and carries its own two lines, because its kicker is a location
and its description is a tagline, neither of which is card copy.

The English cards were drawn by hand before the generator existed and are close
but not identical to what it produces, so `tools/og.py` leaves them alone unless
`--all` is passed. Its palette and geometry were measured off `og/lmad.png`, so
the two sets sit in the same family.

`tools/check.py` fails if a Chinese page points at an English card, which is
what it did for all eight of them until now.

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
python3 tools/check.py            # all nine
python3 tools/check.py links      # or just one
```

| check | asserts |
| --- | --- |
| `structure` | tag balance, no duplicate ids, one `<h1>`, no skipped heading levels, no malformed markup |
| `links` | every internal `href`/`src`/`poster` resolves on disk, using the extensionless convention |
| `parity` | each English page and its Chinese twin share an identical `id=` and `class=` sequence |
| `chrome` | the header, footer and control labels are identical within each language |
| `deadcss` | every class in `style.css` is used by a page or applied by `main.js` |
| `assets` | every tracked file under `assets/` is referenced by some page |
| `stamps` | every `?v=` matches the hash of the file it points at |
| `cv` | `assets/cv/rivan-wong-cv.pdf` still matches `CV/build/cv.pdf` |
| `og` | each page points at its own card and declares the right `og:locale` |

`parity` is the one worth understanding: it is what catches a change made to one
language and forgotten in the other. It compares structure, not prose, so the
Chinese text being shorter does not trip it.

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
- Add a `schema.org/Person` JSON-LD block, `sitemap.xml`,
  `robots.txt`, and a branded `404.html`.
- Chinese social cards. All eight `zh/` pages point `og:image` at the English
  card, so a Chinese page shared to LINE shows a Chinese title over an English
  image. Also worth adding `og:locale`.
- Serve both languages from one URL. Worth revisiting only if editing two files
  becomes the real bottleneck: switching language already keeps your place, and
  the current split is what makes each language separately indexable.

## When to move to a framework

Deliberately none today. The site is 16 pages on one stylesheet and one script,
with no dependencies and no build step: `git push` deploys it, the first visit
costs about 18 KB gzipped over zero external requests, and it will still build
untouched in five years.

What that costs is real and worth naming: the head, header, footer and
back-to-top blocks are repeated on every page, about 1,150 lines site-wide, of
which roughly 640 line-instances are 40 distinct lines copied sixteen times.
Adding a nav item is sixteen edits.

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

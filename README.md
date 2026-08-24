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
case-study-sky-scraper-escape.html
project-mobile-testing.html      # project notes, same layout as a case study
zh/                              # Traditional Chinese twin of every page above
assets/
  css/style.css                  # design tokens + numbered per-component sections
  js/main.js                     # theme toggle, reveal-on-scroll, rotator, nav
  img/                           # in-page figures and the portrait
  img/og/                        # 1200x630 social cards, one per page
tools/serve.py                   # local preview, resolves URLs like GitHub Pages
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

Case-study pages reuse the same stylesheet. Section 11 holds every rule the
long-form pages share, including the `.figure` / `.fig-*` classes and the
`.figure-doc` exhibit panel. A page keeps a `<style>` block only for layouts
nobody else uses: the chart on the capstone page, the results table on the
thesis page, the partition table on the mobile-testing notes. Prefer a modifier
(`.figure.is-loose`, `.figure-doc.is-wide`) over redefining a shared class, so a
class means one thing across the site.

The stylesheet is linked as `style.css?v=N`. Bump `N` in all 14 pages whenever
the CSS changes, or returning visitors keep the cached copy.

## Social cards

Each page points `og:image` at its own 1200x630 card in `assets/img/og/`. The
cards share one template: dark background, blue kicker in caps, title, rule,
two-line description, and the `RW` badge with the site name. Both language
versions of a page share a single English card.

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

## Ideas for later

- Link a downloadable PDF resume in the hero.
- Serve both languages from one URL. Worth revisiting only if editing two files
  becomes the real bottleneck: switching language already keeps your place, and
  the current split is what makes each language separately indexable.

# Portfolio: Rivan Wong

Personal portfolio site, built with plain HTML/CSS/JS (no framework, no build step)
and served directly from the repository root on GitHub Pages.

## Structure

```
index.html                            # landing page, one <section> per CV area
case-study-test-automation.html       # long-form case studies, linked from Experience
case-study-ai-products.html
case-study-capstone.html
case-study-lmad.html
case-study-sky-scraper-escape.html
project-mobile-testing.html           # project notes, same layout as a case study
*.zh.html                             # Traditional Chinese twin of every page above
assets/
  css/style.css                       # design tokens + numbered per-component sections
  js/main.js                          # theme toggle, reveal-on-scroll, rotator, nav
  img/                                # in-page figures and the portrait
  img/og/                             # 1200x630 social cards, one per page
```

Everything the site needs lives at the root, so GitHub Pages can publish the
branch as-is with no build step and no workflow. Page URLs are the file names,
so moving a page renames its public URL.

## Both languages

Every page ships twice: `page.html` in English and `page.zh.html` in Traditional
Chinese. The pair is linked in three places, and all three have to stay in step
when a page is added or renamed:

- the `.lang-toggle` anchor in the header,
- the `<link rel="alternate" hreflang="...">` tags in `<head>`,
- the `og:url` tag, which is absolute and language-specific.

The two files share `style.css` and `main.js`. Strings the JS needs come from
`data-` attributes in the markup (the hero rotator reads `data-phrases`), so
`main.js` holds no English or Chinese text and neither copy has its own script.

## Editing content

All landing-page content lives in `index.html`, organized into clearly commented
sections (Hero, About, Education, Experience, Projects, Skills, Contact). To add
an entry, copy an existing `<article class="entry">` (experience/education) or
`<article class="card">` (projects) block and edit the text. Mirror the same edit
into `index.zh.html`.

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
(`.figure.is-loose`, `.figure-doc.is-wide`) over redefining a shared class,
so a class means one thing across the site.

The stylesheet is linked as `style.css?v=N`. Bump `N` in all 14 pages whenever
the CSS changes, or returning visitors keep the cached copy.

## Social cards

Each page points `og:image` at its own 1200x630 card in `assets/img/og/`. The
cards share one template: dark background, blue kicker in caps, title, rule,
two-line description, and the `RW` badge with the site name. Both language
versions of a page share a single English card.

## Preview locally

```sh
python3 -m http.server 8000 --bind 127.0.0.1
# open http://localhost:8000
```

Run it from the repo root. There is no subfolder to point at. `--bind 127.0.0.1`
keeps the server off the local network and makes it print a usable URL; without it
Python prints `http://[::]:8000/`, the IPv6 wildcard address, which browsers
handle inconsistently. If the port is busy, either stop whatever holds it
(`lsof -nP -iTCP:8000 -sTCP:LISTEN`) or pick another one.

## Deploy

Pushes to `main` publish automatically once GitHub Pages is enabled:

1. In the repo: **Settings → Pages → Build and deployment**.
2. Source: **Deploy from a branch**, Branch: **main**, Folder: **/ (root)**.
3. Push. The site appears at <https://zocke07.github.io/>.

The repository is named `<username>.github.io`, which makes this a GitHub Pages
*user site* served from the domain root. All in-page paths are relative, so the
site would also work unchanged under a project-site subpath. The `og:url` and
`hreflang` tags are absolute, and would need rewriting if the domain changed.

## Ideas for later

- Link a downloadable PDF resume in the hero.
- Serve both languages from one URL, so switching language keeps your place
  instead of loading a second file.
- Add a blog via a static generator if writing becomes a priority.

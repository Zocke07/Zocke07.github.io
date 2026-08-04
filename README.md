# Portfolio: Rivan Wong

Personal portfolio site, built with plain HTML/CSS/JS (no framework, no build step)
and served directly from the repository root on GitHub Pages.

## Structure

```
index.html                       # landing page, one <section> per CV area
case-study-test-automation.html  # long-form case study linked from Experience/Projects
assets/
  css/style.css                  # design tokens (colors/spacing) + per-component sections
  js/main.js                     # theme toggle, reveal-on-scroll, tagline rotator, nav
```

Everything the site needs lives at the root, so GitHub Pages can publish the
branch as-is with no build step and no workflow.

## Editing content

All landing-page content lives in `index.html`, organized into clearly commented
sections (Hero, Experience, Projects, Education, Skills, Contact). To add an entry,
copy an existing `<article class="entry">` (experience/education) or
`<article class="card">` (projects) block and edit the text.

Colors, fonts, and spacing are CSS custom properties at the top of
`assets/css/style.css` (`:root` for light mode, `:root[data-theme="dark"]`
for dark mode). A header toggle switches themes and remembers the choice.
All animations are disabled automatically for visitors who set
`prefers-reduced-motion`.

The case study page reuses the same stylesheet and adds its own page-local
`<style>` block for the few layouts unique to it.

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
*user site* served from the domain root. All paths in the HTML are relative, so
the site would also work unchanged under a project-site subpath.

## Ideas for later

- Link a downloadable PDF resume in the hero.
- Add a dedicated project page per project with screenshots.
- Add a blog via a static generator if writing becomes a priority.

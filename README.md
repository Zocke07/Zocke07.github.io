# Portfolio — Rivan Wong

Personal portfolio site, built with plain HTML/CSS/JS (no framework, no build step)
and deployed to GitHub Pages via GitHub Actions.

## Structure

```
site/                      # everything that gets deployed
  index.html               # all page content, one <section> per CV area
  assets/
    css/style.css          # design tokens (colors/spacing) + per-component sections
    js/main.js             # theme toggle, reveal-on-scroll, tagline rotator, nav
.github/workflows/deploy.yml   # publishes site/ to GitHub Pages on push to main
```

## Editing content

All content lives in `site/index.html`, organized into clearly commented sections
(Hero, Experience, Projects, Education, Skills, Contact). To add an entry, copy an
existing `<article class="entry">` (experience/education) or `<article class="card">`
(projects) block and edit the text.

Colors, fonts, and spacing are CSS custom properties at the top of
`site/assets/css/style.css` (`:root` for light mode, `:root[data-theme="dark"]`
for dark mode — a header toggle switches themes and remembers the choice).
All animations are disabled automatically for visitors who set
`prefers-reduced-motion`.

## Preview locally

```sh
python3 -m http.server -d site 8000
# open http://localhost:8000
```

## Deploy

Pushes to `main` deploy automatically once GitHub Pages is enabled:

1. Create a GitHub repo and push this project to it.
2. In the repo: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Push (or re-run the workflow) — the site appears at
   `https://<username>.github.io/<repo>/`.

## Ideas for later

- Link a downloadable PDF resume in the hero.
- Add a dedicated project page per project with screenshots.
- Add a blog via a static generator if writing becomes a priority.

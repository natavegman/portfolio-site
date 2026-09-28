# Portfolio Site

Personal portfolio website — [natavegman.github.io/portfolio-site](https://natavegman.github.io/portfolio-site)

## Stack

Plain HTML, CSS, JavaScript — no frameworks, no build step.

## Run locally

```bash
open index.html
```

Or serve with any static server:

```bash
python3 -m http.server 8080
```

## Deploy

The site is a single `index.html` file — deploy to GitHub Pages, Netlify, or any static host.

To enable GitHub Pages: **Settings → Pages → Source: main / (root)**.


## Languages and search

The English homepage is `/`; the Russian homepage is `/ru/`. Update the existing
`T.en` / `T.ru` translations in `index.html`, then run `python3 tools/build_homepage.py`
(requires Node.js and BeautifulSoup) to refresh the static Russian page. Language
links, canonical URLs and navigation must remain reciprocal.

Blog sources and templates live in `/opt/blog-publisher` on the publishing server.
`render.py` generates RU `/blog/` and EN `/en/blog/`, feeds and `sitemap.xml`.
Do not edit generated article bodies directly; the source is the approved Notion card.

The `blog-publish` cron wrapper also runs `seo_notify.py`. It sends changed HTML
URLs to IndexNow only after the public response matches the committed page hash.
Acknowledgements are kept outside this repository. HTTP 200/202 means receipt,
not guaranteed indexing. Search Console and Yandex Webmaster ownership must be
verified separately by the site owner; submit `/sitemap.xml` there.

Publication refuses tracked local changes and unpushed commits rather than
resetting them. Use the portfolio-site deploy key only, never another project's token.

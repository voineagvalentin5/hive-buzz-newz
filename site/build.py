#!/usr/bin/env python3
"""Hive Buzz Newz build. Daily: python3 build.py ../YYYY-MM-DD.json
Rebuilds out/<day>/index.html for every ../*.json (plus the given file), out/index.html (latest),
out/archive/index.html, and copies the site's assets into out/."""
import os, glob, shutil, re
import json, sys, html, datetime
from urllib.parse import urlparse
from global_state import edition_navigation, read_signals, render_global_state, story_ids
e = lambda s: html.escape(str(s or ""))
def link(url, text):
    u = urlparse(url or "")
    # only real article links; bare homepages (e.g. https://x.com) render as plain text
    if u.scheme in ("http","https") and u.netloc and u.path.strip("/"):
        return f'<a href="{e(url)}" target="_blank" rel="noopener">{e(text)}</a>'
    return f'<span>{e(text)}</span>'
def fmt(d, f="%A, %B %-d, %Y"):
    return datetime.date.fromisoformat(d).strftime(f)

# Same Google Analytics tag as codex-hive.com. Required on every edition and the archive.
GA_TAG = (
    '<script async src="https://www.googletagmanager.com/gtag/js?id=G-DW4D6JPPB4"></script>'
    "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
    "gtag('js',new Date());gtag('config','G-DW4D6JPPB4');</script>"
)

# Drive-style breadcrumb (Codex Hive Labs › Hive Buzz Newz › edition).
# CSS lives in style.css (class .bc). Required on every edition and the archive.
# The official metallic logo in the first crumb links back to https://codex-hive.com.
import datetime as _dt

def _bc_short(iso, fmt="%b %-d, %Y"):
    return _dt.date.fromisoformat(iso).strftime(fmt)

def chl_nav(edition=None, edition_href=None):
    """edition: short label for the third crumb (e.g. 'Nov 21, 2026' or 'Archive')."""
    deep = " bc--deep" if edition else ""
    current_app = "" if edition else ' aria-current="page"'
    third = ""
    if edition:
        href = edition_href or "#"
        third = (
            f'<li class="bc__item bc__item--extra">'
            f'<a href="{href}" aria-current="page">{edition}</a></li>'
        )
    return f'''<!-- chl-bc -->
<nav class="bc{deep}" aria-label="Breadcrumb">
  <div class="bc__in">
    <ol class="bc__list" id="bc">
      <li class="bc__item bc__item--home"><a href="https://codex-hive.com" aria-label="Codex Hive Labs, codex-hive.com"><picture><source type="image/webp" srcset="/chl-assets/codex-hive-mark-1x.webp 1x, /chl-assets/codex-hive-mark-2x.webp 2x, /chl-assets/codex-hive-mark-3x.webp 3x"><img src="/chl-assets/codex-hive-mark-1x.png" srcset="/chl-assets/codex-hive-mark-1x.png 1x, /chl-assets/codex-hive-mark-2x.png 2x, /chl-assets/codex-hive-mark-3x.png 3x" width="26" height="32" alt="" decoding="async"></picture><span class="bc__t">Codex Hive <span class="bc__labs">Labs</span></span></a></li>
      <li class="bc__item bc__item--academy"><a href="/"{current_app} aria-label="Hive Buzz Newz"><span class="bc__t">Hive Buzz Newz</span><span class="bc__dots" aria-hidden="true">…</span></a></li>
      {third}
    </ol>
  </div>
</nav>
<!-- /chl-bc -->'''

# Backward-compatible alias used only if an older caller still interpolates CHL_NAV.
CHL_NAV = chl_nav()

HERE=os.path.dirname(os.path.abspath(__file__)); DATA=os.path.dirname(HERE); OUT=os.path.join(HERE,"out")
def nav_html(prev, nxt):
    p=f'<a href="/{prev}/index.html">← {fmt(prev,"%b %-d, %Y")}</a>' if prev else '<span class="off">← Earlier</span>'
    n=f'<a href="/{nxt}/index.html">{fmt(nxt,"%b %-d, %Y")} →</a>' if nxt else '<span class="off">Later →</span>'
    return f'<nav class="days"><h2>Earlier days</h2><p>{p} · <a href="/archive/index.html">All days (archive)</a> · {n}</p></nav>'
def render(d, nav):
    stories = d.get("stories", [])
    signals = read_signals(d["date"], [story.get("headline") for story in stories])
    ids = story_ids(signals)
    topics = {}
    for s in stories: topics.setdefault(s.get("topic") or "World", []).append(s)
    out = []
    for t, ss in topics.items():
        out.append(f'<h3 class="topic">{e(t)}</h3><div class="grid">')
        for s in ss:
            st = e(s.get("status"))
            srcs = " · ".join(link(x.get("url"), x.get("name")) for x in s.get("sources", []))
            anchor = ids.get(s.get("headline"))
            story_id = f' id="{anchor}"' if anchor else ""
            out.append(f'<article class="card"{story_id}><span class="badge {st.lower()}">{st}</span>'
                       f'<h4>{e(s.get("headline"))}</h4><p>{e(s.get("summary"))}</p>'
                       f'<p class="src">Sources: {srcs or "<em>none listed</em>"}</p></article>')
        out.append('</div>')
    rum = "".join(
        f'<article class="card rumor"><span class="badge {e(r.get("status")).lower()}">{e(r.get("status"))}</span>'
        f'<h4>{e(r.get("claim"))}</h4><p class="src">Where seen: {link((r.get("where_seen") or {}).get("url"), (r.get("where_seen") or {}).get("name"))}</p>'
        f'<p class="note">{e(r.get("status_note"))}</p></article>' for r in d.get("rumors", []))
    cal = "".join(
        f'<li><time>{fmt(c["date"], "%b %-d")}</time><span>{link(c.get("link"), c.get("event"))}</span></li>'
        for c in d.get("watch_calendar", []))
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Hive Buzz Newz · {e(d["date"])}</title><link rel="stylesheet" href="/style.css">
    <link rel="stylesheet" href="/global-state.css">
    <link rel="icon" href="/favicon.ico" sizes="any">
    <link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">
    <link rel="icon" type="image/png" sizes="192x192" href="/assets/favicon-192.png">
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">{GA_TAG}</head><body class="newz-edition">
    {chl_nav(_bc_short(d['date']), '/' + d['date'] + '/index.html')}<header><div class="wrap brand"><a class="brand-mark" href="/"><img src="/assets/hive-buzz-icon-320.png" srcset="/assets/hive-buzz-icon-320.png 320w, /assets/hive-buzz-icon.png 640w" sizes="(max-width:600px) 56px, 80px" width="80" height="80" alt="Hive Buzz" decoding="async"></a><div class="brand-text"><h1>Hive Buzz <span>Newz</span></h1></div>
    <p class="date"><time datetime="{e(d["date"])}">{fmt(d["date"])}</time></p></div></header>
    {edition_navigation()}
    <main class="wrap">
    {render_global_state(d["date"], signals)}
    <p class="disclosure"><strong>AI-written.</strong> {e(d.get("ai_disclosure"))}</p>
    <section id="stories"><h2>Today's stories</h2><p class="legend"><span class="badge confirmed">Confirmed</span> reported by established outlets · <span class="badge developing">Developing</span> details still emerging</p>{"".join(out)}</section>
    <section id="rumors" class="rumors"><h2>Hive Rumors</h2><p class="legend">Unverified claims seen online. Listed for transparency, not as fact, and updated as Confirmed or Debunked.</p><div class="grid">{rum}</div></section>
    <section id="watch"><h2>What to watch</h2><ul class="cal">{cal}</ul></section>
    </main><footer class="wrap">{nav}<p>Hive Buzz Newz · codex-hive.com</p></footer></body></html>'''
    return page

def main():
    files={}
    for f in glob.glob(os.path.join(DATA,"*.json"))+sys.argv[1:]:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.json", os.path.basename(f)): files[os.path.basename(f)[:10]]=f
    if not files: sys.exit("no YYYY-MM-DD.json found")
    published = {
        os.path.basename(os.path.dirname(path)): path
        for path in glob.glob(os.path.join(DATA, "????-??-??", "index.html"))
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", os.path.basename(os.path.dirname(path)))
    }
    days = sorted(published.keys() | files.keys())
    os.makedirs(OUT,exist_ok=True)
    for i,day in enumerate(days):
        if day in files:
            with open(files[day], encoding="utf-8") as source:
                d = json.load(source)
            if d["date"] != day:
                sys.exit(f"{files[day]}: edition date must match the filename")
            page = render(d, nav_html(days[i-1] if i else None, days[i+1] if i+1<len(days) else None))
        else:
            with open(published[day], encoding="utf-8") as source:
                page = source.read()
        os.makedirs(os.path.join(OUT,day),exist_ok=True)
        with open(os.path.join(OUT, day, "index.html"), "w", encoding="utf-8") as target:
            target.write(page)
        if day == days[-1]:
            with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as target:
                target.write(page)
    items="".join(f'<li><time>{fmt(x,"%b %-d")}</time><span><a href="/{x}/index.html">{fmt(x)}</a></span></li>' for x in reversed(days))
    arch=f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hive Buzz Newz · Archive</title><link rel="stylesheet" href="/style.css">
<link rel="stylesheet" href="/global-state.css">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="/assets/favicon-192.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">{GA_TAG}</head><body class="newz-edition">
{chl_nav('Archive', '/archive/index.html')}<header><div class="wrap brand"><a class="brand-mark" href="/"><img src="/assets/hive-buzz-icon-320.png" srcset="/assets/hive-buzz-icon-320.png 320w, /assets/hive-buzz-icon.png 640w" sizes="(max-width:600px) 56px, 80px" width="80" height="80" alt="Hive Buzz" decoding="async"></a><div class="brand-text"><h1>Hive Buzz <span>Newz</span></h1></div>
<p class="date">Edition archive</p></div></header>
<main class="wrap"><section><h2>All days</h2><ul class="cal">{items}</ul>
<p class="legend"><a href="/">← Today's edition</a></p></section></main>
<footer class="wrap"><p>Hive Buzz Newz · codex-hive.com</p></footer></body></html>'''
    os.makedirs(os.path.join(OUT,"archive"),exist_ok=True)
    open(os.path.join(OUT,"archive","index.html"),"w").write(arch)
    # Brand assets live at the site root (next to this file's parent: the published tree).
    root = os.path.dirname(HERE)
    for name in ("style.css", "global-state.css", "favicon.ico", "apple-touch-icon.png"):
        shutil.copy(os.path.join(root, name), os.path.join(OUT, name))
    for name in ("assets", "chl-assets"):
        shutil.copytree(os.path.join(root, name), os.path.join(OUT, name), dirs_exist_ok=True)
    print("built",len(days),"day(s); latest",days[-1],"->",OUT)
if __name__ == "__main__":
    main()

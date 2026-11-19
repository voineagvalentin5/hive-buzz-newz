#!/usr/bin/env python3
"""Hive Buzz Newz build. Daily: python3 build.py ../YYYY-MM-DD.json
Rebuilds out/<day>/index.html for every ../*.json (plus the given file), out/index.html (latest),
out/archive/index.html, and copies style.css into out/."""
import os, glob, shutil, re
import json, sys, html, datetime
from urllib.parse import urlparse
e = lambda s: html.escape(str(s or ""))
def link(url, text):
    u = urlparse(url or "")
    # only real article links; bare homepages (e.g. https://x.com) render as plain text
    if u.scheme in ("http","https") and u.netloc and u.path.strip("/"):
        return f'<a href="{e(url)}" target="_blank" rel="noopener">{e(text)}</a>'
    return f'<span>{e(text)}</span>'
def fmt(d, f="%A, %B %-d, %Y"):
    return datetime.date.fromisoformat(d).strftime(f)

# Codex Hive Labs top bar. Required on every edition and the archive.
CHL_NAV = r'''<!-- chl-lab-nav -->
<style>
:root{--chl-nav-h:calc(48px + env(safe-area-inset-top,0px))}
#chl-lab-nav,#chl-lab-nav *{box-sizing:border-box}
#chl-lab-nav{
  position:sticky;top:0;z-index:40;
  background:#141414;
  border-bottom:1px solid rgba(224,165,38,.42);
  color:#e9e6df;
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  -webkit-text-size-adjust:100%;
  padding-top:env(safe-area-inset-top,0px);
}
#chl-lab-nav .chl-lab-nav__bar{
  height:48px;display:flex;align-items:center;gap:12px;
  padding:0 16px;max-width:1600px;margin:0 auto;position:relative;
}
#chl-lab-nav a.chl-lab-nav__brand{
  display:flex;align-items:center;gap:9px;min-width:0;
  color:#f3f0ea;text-decoration:none;flex:0 1 auto;
}
#chl-lab-nav a.chl-lab-nav__brand:hover{color:#fff}
#chl-lab-nav a.chl-lab-nav__brand svg{display:block;flex-shrink:0;width:28px;height:31px}
#chl-lab-nav .chl-lab-nav__name{
  font-size:14px;font-weight:700;letter-spacing:.02em;line-height:1.15;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
#chl-lab-nav .chl-lab-nav__labs{color:#e0a526;font-weight:700}
#chl-lab-nav .chl-lab-nav__check{
  position:absolute;width:1px;height:1px;padding:0;margin:-1px;
  overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0;
}
#chl-lab-nav .chl-lab-nav__toggle{
  display:none;flex:0 0 auto;cursor:pointer;margin-left:auto;
  width:40px;height:40px;place-items:center;
  border:1px solid rgba(224,165,38,.4);border-radius:8px;color:#e0a526;background:transparent;
}
#chl-lab-nav .chl-lab-nav__toggle::after{content:"☰";font-size:20px;line-height:1}
#chl-lab-nav .chl-lab-nav__check:checked + .chl-lab-nav__toggle::after{content:"✕";font-size:18px}
#chl-lab-nav .chl-lab-nav__links{display:flex;align-items:center;gap:2px;margin-left:auto}
#chl-lab-nav .chl-lab-nav__links a{
  display:inline-flex;align-items:center;color:#e0a526;text-decoration:none;
  font-size:12px;font-weight:650;letter-spacing:.12em;text-transform:uppercase;
  padding:7px 11px;border-radius:6px;line-height:1;white-space:nowrap;
}
#chl-lab-nav .chl-lab-nav__links a:hover{color:#ffd36b;background:rgba(224,165,38,.08)}
#chl-lab-nav .chl-lab-nav__links a[aria-current="page"]{
  color:#ffd36b;box-shadow:inset 0 -2px 0 #e0a526;
}
#chl-lab-nav .chl-lab-nav__sr{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
#chl-lab-nav a:focus-visible,#chl-lab-nav .chl-lab-nav__toggle:focus-visible,
#chl-lab-nav .chl-lab-nav__check:focus-visible + .chl-lab-nav__toggle{
  outline:2px solid #e0a526;outline-offset:2px;
}
@media (max-width:700px){
  #chl-lab-nav .chl-lab-nav__bar{padding:0 12px}
  #chl-lab-nav .chl-lab-nav__toggle{display:grid}
  #chl-lab-nav .chl-lab-nav__links{
    display:none;position:absolute;top:100%;right:0;left:auto;margin-left:0;
    min-width:min(220px,calc(100vw - 24px));
    flex-direction:column;align-items:stretch;gap:0;
    background:#141414;border:1px solid rgba(224,165,38,.42);
    border-radius:0 0 10px 10px;padding:8px 0;box-shadow:0 12px 28px rgba(0,0,0,.45);
  }
  #chl-lab-nav .chl-lab-nav__check:checked ~ .chl-lab-nav__links{display:flex}
  #chl-lab-nav .chl-lab-nav__links a{padding:12px 16px;border-radius:0}
  #chl-lab-nav .chl-lab-nav__links a[aria-current="page"]{box-shadow:inset 3px 0 0 #e0a526}
}
</style>
<nav id="chl-lab-nav" aria-label="Codex Hive Labs">
  <div class="chl-lab-nav__bar">
    <a class="chl-lab-nav__brand" href="https://codex-hive.com">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 214 236" width="28" height="31" aria-hidden="true" focusable="false"><defs><linearGradient id="chlNavG1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F4F6F8"/><stop offset="1" stop-color="#C7CDD2"/></linearGradient><linearGradient id="chlNavG2" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#F1A500"/><stop offset="0.5" stop-color="#E79300"/><stop offset="1" stop-color="#934400"/></linearGradient><linearGradient id="chlNavG3" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#F5AE07"/><stop offset="1" stop-color="#F7B10A"/></linearGradient><linearGradient id="chlNavG4" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#F5B20E"/><stop offset="1" stop-color="#F6B10B"/></linearGradient><linearGradient id="chlNavG5" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#EEA400"/><stop offset="0.5" stop-color="#D17900"/><stop offset="1" stop-color="#904000"/></linearGradient></defs><path fill="url(#chlNavG1)" stroke="url(#chlNavG1)" stroke-width="1.20" stroke-linejoin="round" fill-rule="evenodd" d="M106.62,0.12L4.12,60.38L1.62,63.12L0.38,67.12L0.38,168.88L1.88,173.12L4.88,176.12L106.62,235.38L108.12,235.38L134.62,219.88L134.62,218.62L133.62,217.62L131.12,216.88L118.62,209.62L112.62,205.38L123.12,198.38L126.88,197.12L127.38,196.12L52.62,152.38L49.12,149.38L47.12,144.88L47.12,90.88L49.88,85.62L113.62,48.12L114.38,47.12L113.62,45.62L114.38,44.12L148.38,24.88L147.62,23.38L107.88,0.12Z"/><path fill="url(#chlNavG2)" stroke="url(#chlNavG2)" stroke-width="1.20" stroke-linejoin="round" fill-rule="evenodd" d="M113.88,45.12L115.88,48.12L160.88,77.38L213.38,77.12L214.12,75.88L213.88,48.12L161.38,17.62L136.12,31.62Z"/><path fill="url(#chlNavG3)" stroke="url(#chlNavG3)" stroke-width="1.20" stroke-linejoin="round" fill-rule="evenodd" d="M121.62,107.62L122.12,121.88L213.38,121.88L214.38,119.62L214.12,93.12L213.12,91.62L137.88,91.62Z"/><path fill="url(#chlNavG4)" stroke="url(#chlNavG4)" stroke-width="1.20" stroke-linejoin="round" fill-rule="evenodd" d="M121.62,131.38L121.88,145.62L137.88,161.12L213.88,160.62L214.38,135.12L213.88,131.38L212.62,130.62L122.88,130.62Z"/><path fill="url(#chlNavG5)" stroke="url(#chlNavG5)" stroke-width="1.20" stroke-linejoin="round" fill-rule="evenodd" d="M112.88,205.38L118.62,209.38L133.62,217.38L135.12,219.12L137.12,219.62L159.88,233.12L161.88,233.38L214.38,203.88L214.12,177.88L213.38,176.62L160.12,176.62Z"/></svg>
      <span class="chl-lab-nav__name">Codex Hive <span class="chl-lab-nav__labs">Labs</span></span>
    </a>
    <input type="checkbox" id="chl-lab-nav-toggle" class="chl-lab-nav__check" autocomplete="off">
    <label class="chl-lab-nav__toggle" for="chl-lab-nav-toggle"><span class="chl-lab-nav__sr">Open Codex Hive Labs menu</span></label>
    <div class="chl-lab-nav__links">
      <a href="https://codex-hive.com">Home</a>
      <a href="https://codex-hive.com/apps-1">Apps</a>
      <a href="https://newz.codex-hive.com" aria-current="page">Newz</a>
      <a href="https://www.patreon.com/c/Codex_Hive_Labs" target="_blank" rel="noopener noreferrer">Patreon</a>
    </div>
  </div>
</nav>
<!-- /chl-lab-nav -->'''

HERE=os.path.dirname(os.path.abspath(__file__)); DATA=os.path.dirname(HERE); OUT=os.path.join(HERE,"out")
def nav_html(prev, nxt):
    p=f'<a href="/{prev}/">← {fmt(prev,"%b %-d, %Y")}</a>' if prev else '<span class="off">← Earlier</span>'
    n=f'<a href="/{nxt}/">{fmt(nxt,"%b %-d, %Y")} →</a>' if nxt else '<span class="off">Later →</span>'
    return f'<nav class="days"><h2>Earlier days</h2><p>{p} · <a href="/archive/">All days (archive)</a> · {n}</p></nav>'
def render(d, nav):
    topics = {}
    for s in d.get("stories", []): topics.setdefault(s.get("topic") or "World", []).append(s)
    out = []
    for t, ss in topics.items():
        out.append(f'<h3 class="topic">{e(t)}</h3><div class="grid">')
        for s in ss:
            st = e(s.get("status"))
            srcs = " · ".join(link(x.get("url"), x.get("name")) for x in s.get("sources", []))
            out.append(f'<article class="card"><span class="badge {st.lower()}">{st}</span>'
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
    <title>Hive Buzz Newz · {e(d["date"])}</title><link rel="stylesheet" href="/style.css"></head><body>
    {CHL_NAV}<header><div class="wrap"><p class="kicker">Codex Hive</p><h1>Hive Buzz <span>Newz</span></h1>
    <p class="date">{fmt(d["date"])}</p></div></header>
    <div class="disclosure wrap"><strong>AI-written.</strong> {e(d.get("ai_disclosure"))}</div>
    <main class="wrap">
    <section><h2>Today's stories</h2><p class="legend"><span class="badge confirmed">Confirmed</span> reported by established outlets · <span class="badge developing">Developing</span> details still emerging</p>{"".join(out)}</section>
    <section class="rumors"><h2>Hive Rumors</h2><p class="legend">Unverified claims seen online. Listed for transparency, not as fact, and updated as Confirmed or Debunked.</p><div class="grid">{rum}</div></section>
    <section><h2>What to watch</h2><ul class="cal">{cal}</ul></section>
    </main><footer class="wrap">{nav}<p>Hive Buzz Newz · codex-hive.com</p></footer></body></html>'''
    return page

def main():
    files={}
    for f in glob.glob(os.path.join(DATA,"*.json"))+sys.argv[1:]:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.json", os.path.basename(f)): files[os.path.basename(f)[:10]]=f
    days=sorted(files)
    if not days: sys.exit("no YYYY-MM-DD.json found")
    os.makedirs(OUT,exist_ok=True)
    for i,day in enumerate(days):
        d=json.load(open(files[day]))
        page=render(d, nav_html(days[i-1] if i else None, days[i+1] if i+1<len(days) else None))
        os.makedirs(os.path.join(OUT,day),exist_ok=True)
        open(os.path.join(OUT,day,"index.html"),"w").write(page)
        if day==days[-1]: open(os.path.join(OUT,"index.html"),"w").write(page)
    items="".join(f'<li><time>{fmt(x,"%b %-d")}</time><span><a href="/{x}/">{fmt(x)}</a></span></li>' for x in reversed(days))
    arch=f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hive Buzz Newz · Archive</title><link rel="stylesheet" href="/style.css"></head><body>
{CHL_NAV}<header><div class="wrap"><p class="kicker">Codex Hive</p><h1>Hive Buzz <span>Newz</span></h1>
<p class="date">Archive · every day we published, newest first</p></div></header>
<main class="wrap"><section><h2>All days</h2><ul class="cal">{items}</ul>
<p class="legend"><a href="/">← Today's edition</a></p></section></main>
<footer class="wrap"><p>Hive Buzz Newz · codex-hive.com</p></footer></body></html>'''
    os.makedirs(os.path.join(OUT,"archive"),exist_ok=True)
    open(os.path.join(OUT,"archive","index.html"),"w").write(arch)
    shutil.copy(os.path.join(HERE,"style.css"),os.path.join(OUT,"style.css"))
    print("built",len(days),"day(s); latest",days[-1],"->",OUT)
main()

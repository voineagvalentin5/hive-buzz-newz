"""Render World Temperature readings and the edition’s featured signals."""

import html
import json
from datetime import date as calendar_date
from pathlib import Path

CHANNELS = {
    "conflict": "Conflict & geopolitics",
    "economy": "Economy & energy",
    "environment": "Climate & disasters",
    "institutions": "Politics & society",
    "technology": "Technology & infrastructure",
    "health": "Public health",
}
BANDS = (
    (0, "Calm", "#7ca4c8"),
    (20, "Mild", "#8ea98a"),
    (40, "Warm", "#d4b873"),
    (60, "Hot", "#e4925d"),
    (80, "Boiling", "#d86e5d"),
)
CHANNEL_ICONS = {
    "conflict": '<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="3"/><path d="M5 20v-2a7 7 0 0 1 14 0v2M3 16a4 4 0 0 1 3-4m15 4a4 4 0 0 0-3-4"/></svg>',
    "economy": '<svg viewBox="0 0 24 24"><ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v12c0 4 16 4 16 0V6M4 12c0 4 16 4 16 0"/></svg>',
    "environment": '<svg viewBox="0 0 24 24"><path d="M7 17H6a4 4 0 1 1 1.6-7.7A5 5 0 0 1 17 10a3.5 3.5 0 1 1 1 7h-1m-4-4-4 6h4l-2 4"/></svg>',
    "institutions": '<svg viewBox="0 0 24 24"><path d="m3 9 9-6 9 6H3Zm2 11h14M7 9v11m5-11v11m5-11v11M3 22h18"/></svg>',
    "technology": '<svg viewBox="0 0 24 24"><rect x="5" y="5" width="14" height="14" rx="2"/><path d="M9 9h6v6H9zM9 2v3m6-3v3m-6 14v3m6-3v3M2 9h3m-3 6h3m14-6h3m-3 6h3"/></svg>',
    "health": '<svg viewBox="0 0 24 24"><path d="M12 21 4 13A5 5 0 0 1 12 7a5 5 0 0 1 8 6Z"/><path d="M6 12h4l2-3 2 5 2-2h2"/></svg>',
}
HERE = Path(__file__).parent


def read_signals(date, headlines):
    path = HERE / "signals" / f"{date}.json"
    if not path.is_file():
        return {}
    signals = json.loads(path.read_text(encoding="utf-8"))
    for channel, entry in signals.items():
        if channel not in CHANNELS:
            raise ValueError(f"{date}: unknown Global State channel {channel}")
        if not entry.get("signal") or headlines.count(entry.get("headline")) != 1:
            raise ValueError(f"{date}: {channel} requires a signal and one matching story")
    return signals


def temperature_series(through):
    records = json.loads((HERE / "world-temperature.json").read_text(encoding="utf-8"))
    dates = []
    for entry in records:
        day = calendar_date.fromisoformat(entry["date"])
        score = entry["score"]
        if type(score) is not int or not 0 <= score <= 100 or type(entry["edition"]) is not bool:
            raise ValueError(f"Invalid World Temperature reading for {day}")
        if dates and day <= dates[-1]:
            raise ValueError(f"World Temperature dates must be unique and ordered: {day}")
        dates.append(day)
    return [entry for entry in records if entry["date"] <= through]


def story_ids(signals):
    ids = {}
    for channel, entry in signals.items():
        ids.setdefault(entry["headline"], f"signal-{channel}")
    return ids


def display_day(iso):
    day = calendar_date.fromisoformat(iso)
    return f"{day:%b} {day.day}"


def temperature_label(score):
    return next(label for minimum, label, _ in reversed(BANDS) if score >= minimum)


def reading(score):
    if score is None:
        return '<div class="state-reading"><strong>—</strong><span>Awaiting reading</span></div>'
    return (f'<div class="state-reading"><strong>{score}</strong><span> / 100</span>'
            f'<span class="state-level">{temperature_label(score)}</span></div>')


def gauge(score):
    labels = "".join(
        f'<span>{label}<small>{minimum}–{minimum + (20 if minimum == 80 else 19)}</small></span>'
        for minimum, label, _ in BANDS
    )
    marker = f'<span class="scale-marker" style="--score:{score}%"></span>' if score is not None else ""
    return f'<div class="state-scale"><div class="scale-labels">{labels}</div><div class="scale-track">{marker}</div></div>'


def date_range(records):
    if not records:
        return "No readings yet"
    first, last = (calendar_date.fromisoformat(records[i]["date"]) for i in (0, -1))
    if first == last:
        return f"{display_day(first.isoformat())}, {last.year}"
    start = f"{display_day(first.isoformat())}, {first.year}" if first.year != last.year else display_day(first.isoformat())
    return f"{start} – {display_day(last.isoformat())}, {last.year}"


def chart_svg(records):
    first, last = (calendar_date.fromisoformat(records[i]["date"]) for i in (0, -1))
    left, right, top, bottom = 47, 930, 23, 258
    height = bottom - top
    duration = max(1, (last - first).days)
    stride = max(1, (len(records) + 16) // 17)
    points, dots, dates = [], [], []
    mobile_dates = {0, len(records) // 2, len(records) - 1}
    for index, entry in enumerate(records):
        day = calendar_date.fromisoformat(entry["date"])
        score = entry["score"]
        x = left + 10 + (right - left - 20) * (day - first).days / duration
        y = bottom - height * score / 100
        points.append(f"{x:.2f},{y:.2f}")
        kind = "" if entry["edition"] else " trend-dot-open"
        dots.append(f'<circle class="trend-dot{kind}" data-point="{day}" cx="{x:.2f}" cy="{y:.2f}" r="5">'
                    f'<title>{display_day(str(day))}: {score}</title></circle>')
        if index in mobile_dates or (index % stride == 0 and index < len(records) - stride):
            milestone = " milestone" if index in mobile_dates else ""
            edge = " first-day" if index == 0 else " last-day" if index == len(records) - 1 else ""
            dates.append(f'<path d="M{x:.2f} {top}V{bottom}"/>'
                         f'<text class="day-label{milestone}{edge}" x="{x:.2f}" y="283" text-anchor="middle">{display_day(str(day))}</text>')
    bands = "".join(
        f'<rect x="{left}" y="{bottom - height * (minimum + 20) / 100:g}" '
        f'width="{right-left}" height="{height/5:g}" fill="{color}" opacity=".22"/>'
        for minimum, _, color in BANDS
    )
    grid = "".join(
        f'<path d="M{left} {bottom - height * value / 100:g}H{right}"/>'
        f'<text x="33" y="{bottom - height * value / 100 + 5:g}" text-anchor="end">{value}</text>'
        for value in range(0, 101, 20)
    )
    x, y = points[-1].split(",")
    label_offset = 56 if float(y) < 57 else 0
    callout = (f'<g class="trend-callout" transform="translate({x} {y})">'
               f'<path d="M0 {top - float(y):.2f}V{bottom - float(y):.2f}"/>'
               f'<rect x="-19" y="{-36 + label_offset}" width="38" height="24" rx="5"/>'
               f'<text x="0" y="{-19 + label_offset}" text-anchor="middle">{records[-1]["score"]}</text></g>')
    return f"""<svg class="trend-chart" viewBox="0 0 949 300" role="img"
      aria-label="World Temperature, {date_range(records)}. Exact values are in the daily readings table.">
      {bands}<g class="trend-grid">{grid}{''.join(dates)}</g>
      <polyline class="trend-line" points="{' '.join(points)}"/>
      {callout}{''.join(dots)}</svg>"""


def chart_view(records, name):
    count = sum(row["edition"] for row in records)
    return f"""<div data-chart-view="{name}" {"hidden" if name != "all" else ""}>
      <p class="trend-dates">{date_range(records)}</p>
      <div class="trend-scroll">{chart_svg(records)}</div>
      <p class="trend-legend"><span><i class="trend-point" aria-hidden="true"></i> Published edition ({count})</span>
      <span><i class="trend-point trend-point-open" aria-hidden="true"></i> Reconstructed ({len(records)-count})</span></p></div>"""


def trend_chart(records):
    if not records:
        return """<details class="dash-panel"><summary class="panel-summary">
          <span>World Temperature</span></summary><p class="panel-empty">No historical readings yet.</p></details>"""
    latest = calendar_date.fromisoformat(records[-1]["date"])
    views = [chart_view(records, "all")]
    for length in (7, 30):
        subset = [row for row in records if (latest - calendar_date.fromisoformat(row["date"])).days < length]
        views.append(f'<template data-range="{length}">{chart_view(subset, str(length))}</template>')
    rows = []
    for row in reversed(records):
        date = row["date"]
        day = display_day(date)
        day = f'<a href="/{date}/index.html">{day}</a>' if row["edition"] else day
        basis = "Published edition" if row["edition"] else "Reconstructed"
        rows.append(f'<tr id="reading-{date}"><th scope="row">{day}</th><td>{row["score"]}</td><td>{basis}</td></tr>')
    return f"""<details class="dash-panel trend-panel" id="temperature-trend">
      <summary class="panel-summary"><span><strong>World Temperature</strong><span class="panel-subtitle"> · Historical trend</span></span></summary>
      <div class="trend-body">
        <div class="trend-ranges" role="group" aria-label="History range" hidden>
          <button type="button" data-set-range="7" aria-pressed="false">7D</button>
          <button type="button" data-set-range="30" aria-pressed="false">30D</button>
          <button type="button" data-set-range="all" aria-pressed="true">All</button>
        </div>
        {''.join(views)}
        <details class="trend-details">
          <summary>View daily readings</summary>
          <table><thead><tr><th scope="col">Date</th><th scope="col">Score / 100</th><th scope="col">Basis</th></tr></thead>
          <tbody>{''.join(rows)}</tbody></table>
        </details>
      </div></details>"""


def archive_score_color(score):
    stops = (
        (0, (150, 208, 255)),
        (20, (143, 222, 184)),
        (35, (245, 211, 124)),
        (43, (255, 173, 105)),
        (50, (255, 130, 123)),
        (65, (255, 108, 117)),
        (100, (255, 113, 142)),
    )
    for (low, start), (high, end) in zip(stops, stops[1:]):
        if score <= high:
            fraction = (score - low) / (high - low)
            channels = (round(a + (b - a) * fraction) for a, b in zip(start, end))
            return "#" + "".join(f"{channel:02x}" for channel in channels)


def archive_strip(records, current):
    chips = []
    for row in records:
        iso = row["date"]
        day = calendar_date.fromisoformat(iso)
        basis = "Published edition" if row["edition"] else "Reconstructed"
        link = f"/{iso}/index.html" if row["edition"] else f"#reading-{iso}"
        active = ' aria-current="date"' if current == iso else ""
        chips.append(
            f'<li><a class="archive-chip" href="{link}" data-reading="{iso}" data-day="{display_day(iso)}" '
            f'data-basis="{basis}" data-score="{row["score"]}" data-level="{temperature_label(row["score"])}"'
            f'{active} aria-label="{display_day(iso)}, {row["score"]} out of 100, {basis}">'
            f'<time datetime="{iso}"><span>{day:%b}</span> {day.day}</time>'
            f'<strong style="--archive-score-color:{archive_score_color(row["score"])}">{row["score"]}</strong></a></li>'
        )
    dates = (f'<button type="button" class="archive-arrow" data-scroll="-1" aria-label="Show earlier dates" hidden>‹</button>'
             f'<ol class="archive-chips">{"".join(chips)}</ol>'
             f'<button type="button" class="archive-arrow" data-scroll="1" aria-label="Show later dates" hidden>›</button>') if chips else ""
    return f"""<details class="dash-panel archive-panel" id="edition-archive">
      <summary class="panel-summary"><span><strong>Archive</strong><span class="panel-subtitle"> · Daily editions</span>
      <small>{date_range(records)}</small></span></summary>
      <div class="archive-body">{dates}<a class="archive-all" href="/archive/index.html">All editions</a></div>
    </details>"""


def feature_signals(signals):
    ids = story_ids(signals)
    items = []
    for channel, label in CHANNELS.items():
        if channel not in signals:
            continue
        entry = signals[channel]
        title = html.escape(entry.get("title") or entry["signal"])
        description = html.escape(entry.get("description") or label)
        items.append(
            f'<li><a href="#{ids[entry["headline"]]}"><span class="signal-icon" aria-hidden="true">{CHANNEL_ICONS[channel]}</span>'
            f'<span><strong>{title}</strong><span class="signal-description">{description}</span></span>'
            '<span class="signal-arrow" aria-hidden="true"></span></a></li>'
        )
    body = f'<ul>{"".join(items)}</ul>' if items else '<p class="panel-empty">No featured signals for this edition.</p>'
    return f"""<details class="dash-panel state-signals" id="key-signals">
      <summary class="panel-summary"><span>Key signals</span></summary>{body}</details>"""


def render_global_state(date, signals):
    records = temperature_series(date)
    current = next((entry for entry in reversed(records)
                    if entry["date"] == date and entry["edition"]), None)
    score = current["score"] if current else None
    previous = records[-2] if current and len(records) > 1 else None
    change = ""
    if previous:
        delta = score - previous["score"]
        direction, signed = ("down", f"−{abs(delta)}") if delta < 0 else ("up", f"+{delta}") if delta else ("flat", "0")
        qualifier = " (reconstructed)" if not previous["edition"] else ""
        change = f'<p class="state-change {direction}"><strong>{signed}</strong> vs {display_day(previous["date"])}{qualifier}</p>'
    edition_link = f'/{date}/index.html'
    return f"""<section class="global-state" id="global-state" aria-labelledby="global-state-title">
    <div class="state-banner">
      <div class="state-intro"><h2 id="global-state-title">Global State</h2><p>Pressure in the world’s news.</p></div>
      <div class="state-score">{reading(score)}{change}</div>
      {gauge(score)}
      <div class="state-planet" aria-hidden="true"></div>
    </div>
    <h3 class="history-heading">History</h3>
    <div class="history-grid">
      {trend_chart(records)}
      <div class="history-side">
        <details class="dash-panel edition-reading">
          <summary class="panel-summary"><span><strong data-edition-date>{display_day(date)}</strong>
            <span data-edition-basis> · Published edition</span>
            <small data-edition-score>{f'{score} / 100 · {temperature_label(score)}' if score is not None else 'Awaiting reading'}</small></span></summary>
          <div class="edition-reading-body" aria-live="polite"><p data-edition-note>Reading for this edition.</p>
          <a data-edition-link href="{edition_link}">Open edition</a></div>
        </details>
        {feature_signals(signals)}
      </div>
    </div>
    {archive_strip(records, date)}
    <div class="dashboard-footer"><details class="state-method">
      <summary>Method v1 · AI-calculated news-pressure index</summary>
      <div><p>Scores run from 0 to 100 and describe pressure in the news. Filled chart points use published editions.
      Open chart points are reconstructions from days without editions. The change above compares the previous recorded reading.</p>
      <p>Earth imagery: NASA EPIC via Codex Hive Labs.</p></div>
    </details>
    <a class="dashboard-labs" href="https://codex-hive.com" aria-label="Codex Hive Labs"><img
      src="/chl-assets/codex-hive-mark-2x.webp" width="23" height="28" alt="" decoding="async"></a>
    </div></section>"""


def edition_masthead(date):
    day = calendar_date.fromisoformat(date)
    return f"""<header class="edition-masthead" id="edition-top"><div class="wrap masthead-inner">
      <div class="masthead-brand">
        <a class="brand-mark" href="/" aria-label="Hive Buzz Newz home"><img src="/assets/hive-buzz-icon-320.png"
          width="56" height="56" alt="" decoding="async"></a>
        <div><h1><a href="/">Hive Buzz <span>Newz</span></a></h1>
          <a class="masthead-parent" href="https://codex-hive.com">By Codex Hive Labs</a></div>
      </div>
      <nav class="edition-nav" aria-label="Edition sections">
        <a href="#global-state" aria-current="location">Global State</a><a href="#stories">Stories</a><a href="#rumors">Rumors</a>
        <a href="#watch">What to watch</a><a href="#edition-archive">Archive</a>
      </nav>
      <time class="masthead-date" datetime="{date}">{day:%B} {day.day}, {day.year}</time>
    </div></header>"""

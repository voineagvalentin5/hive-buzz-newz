"""Render World Temperature readings and the edition’s featured signals."""

import html
import json
import math
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


def dial(score):
    center_x, center_y, radius = 150, 129, 109
    path = 'M41 129 A109 109 0 0 1 259 129'
    arcs = []
    for (start, _, color), end in zip(BANDS, [20, 40, 60, 80, 100]):
        arcs.append(
            f'<path d="{path}" pathLength="100" stroke="{color}" '
            f'stroke-dasharray="0 {start} {end - start - .8} 101"/>'
        )
    ticks = []
    for mark in range(0, 101, 5):
        angle = math.pi * (1 - mark / 100)
        start_radius = radius - (18 if mark % 25 == 0 else 14)
        x1 = center_x + start_radius * math.cos(angle)
        y1 = center_y - start_radius * math.sin(angle)
        x2 = center_x + (radius - 10) * math.cos(angle)
        y2 = center_y - (radius - 10) * math.sin(angle)
        ticks.append(f'<path d="M{x1:.2f} {y1:.2f}L{x2:.2f} {y2:.2f}"/>')
    needle = ""
    if score is not None:
        angle = math.pi * (1 - score / 100)
        x = center_x + 88 * math.cos(angle)
        y = center_y - 88 * math.sin(angle)
        needle = (f'<path d="M150 129L{x:.2f} {y:.2f}" stroke="#f6e6bb" stroke-width="3" '
                  'stroke-linecap="round"/><circle cx="150" cy="129" r="7" '
                  'fill="#f6e6bb" stroke="#1c1711" stroke-width="3"/>')
    return (
        '<svg class="state-dial" viewBox="24 9 252 148" aria-hidden="true">'
        f'<g fill="none" stroke-width="7" opacity="{1 if score is not None else .36}">'
        + "".join(arcs) + '</g><g fill="none" stroke="#ae9d7b" opacity=".57">'
        + "".join(ticks) + f'</g>{needle}'
        '<g fill="#d1c5af" font-size="10" text-anchor="middle">'
        '<text x="41" y="149">0</text><text x="259" y="149">100</text></g></svg>'
    )


def story_ids(signals):
    ids = {}
    for channel, entry in signals.items():
        ids.setdefault(entry["headline"], f"signal-{channel}")
    return ids


def trend_chart(records):
    if len(records) < 2:
        return ""
    start = calendar_date.fromisoformat(records[0]["date"])
    end = calendar_date.fromisoformat(records[-1]["date"])
    points, markers, rows = [], [], []
    for entry in records:
        day = calendar_date.fromisoformat(entry["date"])
        score = entry["score"]
        x = 34 + (day - start).days / (end - start).days * 580
        y = 113 - score
        points.append(f"{x:.2f},{y}")
        fill = "#e5bd79" if entry["edition"] else "#111820"
        label = f"{day:%b} {day.day}"
        markers.append(f'<circle cx="{x:.2f}" cy="{y}" r="3.5" fill="{fill}" stroke="#e5bd79" stroke-width="1.5"><title>{label}: {score}</title></circle>')
        if entry["edition"]:
            date_label = f'<a href="/{day}/index.html">{label}</a>'
            source = "Published edition"
        else:
            date_label = label
            source = "Reconstructed"
        rows.append(f'<tr><th scope="row">{date_label}</th><td>{score}</td><td>{source}</td></tr>')
    bands = "".join(
        f'<rect x="34" y="{93 - minimum}" width="580" height="20" fill="{color}" opacity=".08"/>'
        for minimum, _, color in BANDS
    )
    grid = "".join(
        f'<path d="M34 {113 - value}H614" stroke="#59616a" stroke-opacity=".42"/>'
        f'<text x="25" y="{117 - value}" text-anchor="end">{value}</text>'
        for value in (0, 20, 40, 60, 80, 100)
    )
    labels = [
        (34, start, "start"), (324, start + (end - start) // 2, "middle"), (614, end, "end"),
    ]
    dates = "".join(f'<text x="{x}" y="133" text-anchor="{anchor}">{day:%b} {day.day}</text>'
                    for x, day, anchor in labels)
    return f"""
    <section class="state-trend" id="temperature-trend" aria-labelledby="trend-title">
      <div class="trend-heading">
        <h3 id="trend-title">Temperature trend</h3>
        <p>Method v1 · AI-calculated</p>
      </div>
      <svg class="trend-chart" viewBox="0 0 630 140" role="img" aria-labelledby="trend-summary">
        <title id="trend-summary">World Temperature from {start:%b} {start.day} to {end:%b} {end.day}. Exact readings and source types are available in the daily readings table.</title>
        {bands}
        <g fill="#bcb6ab" font-size="12">{grid}{dates}</g>
        <polyline points="{' '.join(points)}" fill="none" stroke="#e5bd79" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        {"".join(markers)}
      </svg>
      <div class="trend-foot">
        <p class="trend-legend"><span><i class="trend-point" aria-hidden="true"></i> Published edition</span>
        <span><i class="trend-point trend-point-open" aria-hidden="true"></i> Reconstructed</span></p>
        <details class="trend-details">
          <summary>View daily readings</summary>
          <table><thead><tr><th scope="col">Date</th><th scope="col">Score / 100</th><th scope="col">Basis</th></tr></thead>
          <tbody>{"".join(reversed(rows))}</tbody></table>
        </details>
      </div>
    </section>"""


def render_global_state(date, signals):
    records = temperature_series(date)
    current = next((entry for entry in reversed(records)
                    if entry["date"] == date and entry["edition"]), None)
    score = current["score"] if current else None
    score_markup = '<div class="state-reading"><strong>—</strong></div><p>Awaiting reading</p>'
    if score is not None:
        level = next(label for minimum, label, _ in reversed(BANDS) if score >= minimum)
        score_markup = (f'<div class="state-reading"><strong>{score}</strong><span> / 100</span></div>'
                        f'<p>{level}</p>')

    ids = story_ids(signals)
    items = []
    for channel, label in CHANNELS.items():
        if channel not in signals:
            continue
        entry = signals[channel]
        signal = html.escape(entry["signal"])
        anchor = ids[entry["headline"]]
        items.append(
            f'<li><a href="#{anchor}"><span class="signal-meta">{html.escape(label)}</span>'
            f'<span class="signal-headline">{signal}<span class="signal-arrow" aria-hidden="true"></span></span></a></li>'
        )
    signal_list = f'<ul>{"".join(items)}</ul>' if items else (
        '<p class="state-empty">This edition has no featured signals.</p>'
    )
    return f"""<section class="global-state" id="global-state" aria-labelledby="global-state-title">
    <div class="state-hero">
      <div class="state-intro">
        <p class="state-eyebrow"><span aria-hidden="true"></span> Global State</p>
        <h2 id="global-state-title">World<br> Temperature</h2>
        <p>How much pressure is showing up in the news?</p>
      </div>
      <div class="state-gauge">
        {dial(score)}
        {score_markup}
      </div>
    </div>
    <aside class="state-signals" aria-labelledby="state-signals-title">
      <div class="state-signals-head"><h3 id="state-signals-title">Key signals</h3></div>
      {signal_list}
    </aside>
    {trend_chart(records)}
    <details class="state-method">
      <summary>About World Temperature</summary>
      <div>
        <p>World Temperature is an AI-calculated Hive Buzz Newz index of pressure in the news.
        The chart labels method v1 readings by their basis. A filled point uses a published edition.
        An open point is a reconstruction from a day without an edition.</p>
        <p>The scale runs from 0 to 100. Bands begin at 0 (calm), 20 (mild), 40 (warm),
        60 (hot), and 80 (boiling).</p>
        <p>Key signals link to reporting in this edition. Earth artwork: Codex Hive Labs.</p>
      </div>
    </details>
    </section>"""


def edition_navigation():
    return """<nav class="edition-nav wrap" aria-label="Edition sections">
      <a href="#global-state">Global State</a>
      <a href="#stories">Stories</a>
      <a href="#rumors">Rumors</a>
      <a href="#watch">What to watch</a>
      <a href="/archive/index.html">Archive</a>
    </nav>"""
